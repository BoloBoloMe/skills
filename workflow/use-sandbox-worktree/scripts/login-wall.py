"""login-wall: M09 登录墙编排器 (ISSUE-04).

TS-001 切片: RFB 3.8 客户端纯逻辑 — 握手, 消息发送, raw 帧解码,
PPM 写出, 非黑占比判定.
TS-003 切片: up / down 子命令 — 容器生命周期与宿主端口动态发现.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import socket
import struct
import subprocess
import sys
import tempfile
from collections import namedtuple
from pathlib import Path

RFB_BANNER = b"RFB 003.008\n"
SECURITY_NONE = 1
ENCODING_RAW = 0

# 32bpp little-endian true-colour, depth 24, shifts r16 g8 b0 (3x pad)
# 字段本身按 RFC 6143 大端; "little-endian" 只约束像素数据 (big-endian-flag=0)
PIXEL_FORMAT_32BPP_LE = struct.pack(
    ">BBBBHHHBBB3x", 32, 24, 0, 1, 255, 255, 255, 16, 8, 0
)

ServerInfo = namedtuple("ServerInfo", "width height name")
FrameRect = namedtuple("FrameRect", "x y w h rgb")


def raw32_to_rgb(raw: bytes) -> bytes:
    """32bpp LE (r16 g8 b0, depth 24) 像素串 -> RGB888 像素串."""
    out = bytearray(len(raw) // 4 * 3)
    for i in range(len(raw) // 4):
        (v,) = struct.unpack_from("<I", raw, i * 4)
        out[i * 3] = (v >> 16) & 0xFF
        out[i * 3 + 1] = (v >> 8) & 0xFF
        out[i * 3 + 2] = v & 0xFF
    return bytes(out)


def ppm_bytes(width: int, height: int, rgb: bytes) -> bytes:
    """RGB888 像素串 -> PPM P6 文件字节."""
    return b"P6\n%d %d\n255\n" % (width, height) + rgb


def non_black_ratio(rgb: bytes) -> float:
    """非黑像素 (任一通道非 0) 占比."""
    total = len(rgb) // 3
    if total == 0:
        return 0.0
    non_black = sum(
        1 for i in range(0, len(rgb), 3) if rgb[i : i + 3] != b"\x00\x00\x00"
    )
    return non_black / total


def frame_has_content(rgb: bytes, min_ratio: float) -> bool:
    """非黑占比达到阈值即判定画面有内容."""
    return non_black_ratio(rgb) >= min_ratio


def ws_read_frame(recv_fn, prepend: bytes = b"") -> tuple[int, bytes]:
    """读一个 websocket 帧 (RFC 6455 §5.2, 服务端->客户端方向).

    recv_fn(n) 拉取 n 字节 (可注入, 供手写字节单测); prepend 为同包
    预读缓冲 (101 响应后 banner 可能同包到达). 服务端帧不带掩码,
    带掩码即违协议报错; 长度三档: 7 位 / 16 位 / 64 位.
    """
    buf = bytearray(prepend)

    def need(n: int) -> bytes:
        while len(buf) < n:
            chunk = recv_fn(n - len(buf))
            if not chunk:
                raise ConnectionError("ws stream closed mid-frame")
            buf.extend(chunk)
        out = bytes(buf[:n])
        del buf[:n]
        return out

    b1, b2 = need(2)
    opcode = b1 & 0x0F
    masked = b2 >> 7
    length = b2 & 0x7F
    if masked:
        raise ValueError("server-to-client ws frames must not be masked")
    if length == 126:
        (length,) = struct.unpack(">H", need(2))
    elif length == 127:
        (length,) = struct.unpack(">Q", need(8))
    return opcode, need(length)


def compose_framebuffer(width: int, height: int,
                        rects: list[FrameRect]) -> bytes:
    """把 update rects 逐行填入全帧 RGB 画布 (未覆盖处保持黑).

    数据契约: rect 越界或 rgb 尺寸与 w*h*3 不符即抛 ValueError —
    切片赋值在长度不匹配时会静默 resize/错位, 必须前置拦截.
    """
    for rect in rects:
        if not (0 <= rect.x and 0 <= rect.y
                and rect.w >= 0 and rect.h >= 0
                and rect.x + rect.w <= width and rect.y + rect.h <= height):
            raise ValueError(f"rect out of bounds: {rect} for {width}x{height}")
        if len(rect.rgb) != rect.w * rect.h * 3:
            raise ValueError(
                f"rgb size mismatch: {len(rect.rgb)} != {rect.w}*{rect.h}*3")
    frame = bytearray(width * height * 3)
    for rect in rects:
        for row in range(rect.h):
            dst = ((rect.y + row) * width + rect.x) * 3
            src = row * rect.w * 3
            frame[dst:dst + rect.w * 3] = rect.rgb[src:src + rect.w * 3]
    return bytes(frame)


# ------------------------------------------------- verify: host 侧通道检查

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _http_get(host: str, port: int, path: str,
              timeout: float = 10.0) -> tuple[int, bytes]:
    """stdlib HTTP/1.1 GET (Connection: close), 返回 (状态码, body)."""
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(
            f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
            "Connection: close\r\n\r\n".encode()
        )
        buf = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
    head, _, body = buf.partition(b"\r\n\r\n")
    status_line = head.split(b"\r\n")[0]
    status = int(status_line.split()[1])
    return status, body


def _ws_handshake(host: str, port: int,
                  timeout: float = 10.0) -> tuple[socket.socket, bytes]:
    """raw websocket 升级握手, 校验 Sec-WebSocket-Accept;
    返回 (socket, 101 响应后同包预读字节)."""
    key = base64.b64encode(secrets.token_bytes(16)).decode()
    request = (
        f"GET /websockify HTTP/1.1\r\nHost: {host}:{port}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    )
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.sendall(request.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = sock.recv(4096)
        if not chunk:
            sock.close()
            raise ConnectionError("ws handshake: connection closed")
        resp += chunk
    head, _, rest = resp.partition(b"\r\n\r\n")
    status_line = head.split(b"\r\n")[0]
    if b" 101 " not in status_line + b" ":
        sock.close()
        raise ConnectionError(f"ws handshake failed: {status_line!r}")
    accept = base64.b64encode(
        hashlib.sha1((key + WS_GUID).encode()).digest()
    ).decode()
    if accept.encode() not in head:
        sock.close()
        raise ConnectionError("ws handshake: Sec-WebSocket-Accept mismatch")
    return sock, rest


def _baseline_probe_script() -> str:
    """容器内执行: RFB 全帧读取 -> 非黑占比 -> PPM 落容器 /tmp."""
    return (
        "import importlib.util, socket;"
        "spec = importlib.util.spec_from_file_location('lw', '/tmp/lw.py');"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "s = socket.create_connection(('127.0.0.1', 5900), 10);"
        "c = m.RfbClient(s);"
        "info = c.handshake();"
        "c.set_pixel_format(); c.set_encodings_raw(); c.request_full_update();"
        "rects = c.read_framebuffer_update();"
        "frame = m.compose_framebuffer(info.width, info.height, rects);"
        "ratio = m.non_black_ratio(frame);"
        "open('/tmp/baseline.ppm', 'wb').write("
        "m.ppm_bytes(info.width, info.height, frame));"
        "print(info.width, info.height, f'{ratio:.6f}')"
    )


BROWSE_DIR = "/home/agent/.agents/skills/access-web/browse"

# image-prep 与缺省清单的仓库内位置 (本脚本在 scripts/ 下)
IMAGE_PREP_SCRIPT = Path(__file__).resolve().parent / "image-prep.py"
DEFAULT_REQUIREMENTS = (
    Path(__file__).resolve().parents[1] / "image/requirements-browser.md"
)

# 高对比页: 全屏白底 + 中央 40vh 黑条. 白窗本身即非黑, 窗口 1280x720
# 占屏 44%, 加黑条后非黑占比远超空白基线 (~0%), 但不达全屏白的 >50%.
DATA_PAGE = (
    "data:text/html,<body style='background:%23ffffff;margin:0'>"
    "<div style='position:fixed;top:30vh;left:0;width:100vw;height:40vh;"
    "background:%23000000'></div></body>"
)


def _navigate_script() -> str:
    """headed/headless 共用: navigate 高对比页, 打印 success 与 error."""
    return (
        "from browser_agent import navigate\n"
        f"r = navigate({DATA_PAGE!r})\n"
        "print(r.success, r.error)\n"
    )


def _render_poll_script() -> str:
    """容器内轮询 (<=30s): RFB 全帧非黑占比超阈值即写 rendering.ppm 退 0.

    阈值 0.2 的实测几何: chromium 窗口固定 1280x720 (browser.py
    --window-size), 屏 1920x1080 -> 窗口占 44%; 窗口内 UI 栏 (~90px) 与
    白区 (扣除 40vh 黑条) 全部非黑, 实测占比 ~29-31%; 0.2 留健康余量,
    仍远超空白基线 (<1%).
    """
    return (
        "import importlib.util, socket, time\n"
        "spec = importlib.util.spec_from_file_location('lw', '/tmp/lw.py')\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "best = 0.0\n"
        "for i in range(15):\n"
        "    try:\n"
        "        s = socket.create_connection(('127.0.0.1', 5900), 10)\n"
        "        c = m.RfbClient(s)\n"
        "        info = c.handshake()\n"
        "        c.set_pixel_format(); c.set_encodings_raw()\n"
        "        c.request_full_update()\n"
        "        rects = c.read_framebuffer_update()\n"
        "        s.close()\n"
        "        frame = m.compose_framebuffer(info.width, info.height, rects)\n"
        "        ratio = m.non_black_ratio(frame)\n"
        "        best = max(best, ratio)\n"
        "        if ratio > 0.2:\n"
        "            open('/tmp/rendering.ppm', 'wb').write("
        "m.ppm_bytes(info.width, info.height, frame))\n"
        "            print('ratio', ratio)\n"
        "            raise SystemExit(0)\n"
        "    except SystemExit:\n"
        "        raise\n"
        "    except Exception:\n"
        "        time.sleep(2)\n"
        "print('ratio', best)\n"
        "raise SystemExit(1)\n"
    )


def cmd_verify(args: argparse.Namespace) -> int:
    """TS-004 通道检查: (1) noVNC HTTP 200 (2) ws 握手 101 + accept
    (3) ws 帧内 RFB banner (4) 容器内空白 framebuffer 基线 (<1% 非黑)
    + PPM 证据回宿主. 全过 rc 0, 检查失败 rc 1; podman 传输层失败
    (cp/exec/超时) 上抛经 main 封装 rc 2, 不与检查结果混淆."""
    results: list[bool] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append(ok)
        suffix = f" ({detail})" if detail else ""
        print(f"check {name}: {'OK' if ok else 'FAIL'}{suffix}")

    ports = discover_ports(args.name)
    host_port = ports.get("6080/tcp")
    if not host_port:
        check("discover_ports", False, "no 6080/tcp mapping")
        return 1

    # (1) noVNC HTTP
    try:
        status, body = _http_get("127.0.0.1", int(host_port), "/vnc.html")
        ok = status == 200 and b"noVNC" in body
        check("http_vnc_html_200", ok, f"status={status}")
    except (OSError, ValueError, IndexError) as error:
        check("http_vnc_html_200", False, str(error))

    # (2) ws 握手
    sock, rest = None, b""
    try:
        sock, rest = _ws_handshake("127.0.0.1", int(host_port))
        check("ws_handshake_101", True)
    except (OSError, ValueError, ConnectionError) as error:
        check("ws_handshake_101", False, str(error))

    # (3) ws 帧 RFB banner (独立记项, 失败必记自身 False)
    if sock is not None:
        try:
            opcode, payload = ws_read_frame(sock.recv, prepend=rest)
            ok_banner = opcode in (0x1, 0x2) and payload.startswith(b"RFB ")
            check("ws_rfb_banner", ok_banner,
                  f"opcode={opcode} payload={payload[:16]!r}")
        except (OSError, ValueError, ConnectionError) as error:
            check("ws_rfb_banner", False, str(error))
        finally:
            sock.close()
    else:
        check("ws_rfb_banner", False, "handshake failed")

    # (4) 空白基线 (容器内 RFB 全帧) + PPM 证据回宿主
    evidence_dir = args.evidence_dir or tempfile.mkdtemp(prefix="swt-m09-evidence-")
    Path(evidence_dir).mkdir(parents=True, exist_ok=True)  # 用户传入可能不存在
    print(f"evidence-dir: {evidence_dir}")
    _podman(["cp", str(Path(__file__).resolve()),
             f"{args.name}:/tmp/lw.py"], timeout=120)
    probe = _podman(["exec", args.name, "python3", "-c",
                     _baseline_probe_script()], check=False, timeout=300)
    if probe.returncode != 0:
        check("blank_frame_baseline", False, probe.stderr.strip()[-160:])
    else:
        width, height, ratio = probe.stdout.split()[-3:]
        check("blank_frame_baseline", float(ratio) < 0.01,
              f"{width}x{height} non_black={float(ratio):.4%}")
    _podman(["cp", f"{args.name}:/tmp/baseline.ppm",
             str(Path(evidence_dir) / "baseline.ppm")],
            check=False, timeout=120)
    if (Path(evidence_dir) / "baseline.ppm").is_file():
        print(f"evidence: {Path(evidence_dir) / 'baseline.ppm'}")
    else:
        print("evidence: unavailable (baseline probe failed)")

    # (5) headed chromium 渲染 -> framebuffer 非黑超阈值 + PPM 证据
    # HOME=/home/agent: chromium 由项目层装在该处缓存; root 直跑会找错
    try:
        _podman(["exec", args.name, "mkdir", "-p", "/tmp/headless-session"],
                timeout=60)
        headed = _podman([
            "exec", "-w", BROWSE_DIR,
            "-e", "HOME=/home/agent",
            "-e", "BROWSER_HEADED=true", "-e", "DISPLAY=:99",
            args.name, "uv", "run", "python", "-c",
            _navigate_script(),
        ], check=False, timeout=300)
        if headed.returncode != 0 or \
                not headed.stdout.strip().startswith("True"):
            check("headed_render_nonblack", False,
                  headed.stdout.strip()[:80] or headed.stderr.strip()[-160:])
        else:
            poll = _podman(["exec", args.name, "python3", "-c",
                            _render_poll_script()], check=False, timeout=300)
            if poll.returncode != 0:
                check("headed_render_nonblack", False,
                      poll.stdout.strip() or poll.stderr.strip()[-160:])
            else:
                ratio = float(poll.stdout.split()[-1])
                check("headed_render_nonblack", True,
                      f"non_black={ratio:.4%}")
        _podman(["cp", f"{args.name}:/tmp/rendering.ppm",
                 str(Path(evidence_dir) / "rendering.ppm")],
                check=False, timeout=120)
        if (Path(evidence_dir) / "rendering.ppm").is_file():
            print(f"evidence: {Path(evidence_dir) / 'rendering.ppm'}")
        else:
            print("evidence: unavailable (render probe failed)")
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        check("headed_render_nonblack", False, f"infra: {error}")
        print("evidence: unavailable (render probe failed)")

    # (6) headless 回切: 换 cwd (同 cwd 会复用 headed 会话), 无 DISPLAY /
    # BROWSER_HEADED; headless 不依赖 X, 成功即证明环境变量回切生效
    try:
        headless = _podman([
            "exec", "-w", "/tmp/headless-session",
            "-e", "HOME=/home/agent",
            args.name, "uv", "run", "--project", BROWSE_DIR,
            "python", "-c", _navigate_script(),
        ], check=False, timeout=300)
        ok = headless.returncode == 0 and \
            headless.stdout.strip().startswith("True")
        check("headless_fallback_ok", ok,
              headless.stdout.strip()[:80] or headless.stderr.strip()[-160:])
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        check("headless_fallback_ok", False, f"infra: {error}")
    finally:
        # 收尾杀干净两棵 chromium 树 (cmdline 均含 chrome-linux 路径);
        # headless 段任何异常路径都不得漏杀. 收尾尽力, 不遮主结果.
        try:
            _podman(["exec", args.name, "pkill", "-f", "chrome-linux"],
                    check=False, timeout=60)
        except (RuntimeError, subprocess.TimeoutExpired):
            pass

    return 0 if all(results) else 1


# --------------------------------------------------------------- 编排命令


def _podman(args: list[str], check: bool = True,
            timeout: int = 600) -> subprocess.CompletedProcess:
    """timeout 600s 依据: run -d / port / rm 秒级; exec swt-vnc start
    最坏三环资源等待 ~30s + X 冷启动余量, 600s 约 20 倍裕度."""
    result = subprocess.run(
        ["podman", *args], capture_output=True, text=True, timeout=timeout,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"podman {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result


def discover_ports(name: str) -> dict[str, str]:
    """podman port 输出 -> {容器端口/协议: 宿主端口}.

    优先 0.0.0.0/[::] 表项; 缺省回退任一表项 (消费方经 127.0.0.1 连接,
    宿主侧网络栈对 lo 目标同样命中动态映射).
    """
    preferred: dict[str, str] = {}
    fallback: dict[str, str] = {}
    for line in _podman(["port", name]).stdout.splitlines():
        if "->" not in line:
            continue
        proto_port, host = (part.strip() for part in line.split("->", 1))
        host_ip, _, host_port = host.rpartition(":")
        if host_ip in ("0.0.0.0", "[::]"):
            preferred.setdefault(proto_port, host_port)
        else:
            fallback.setdefault(proto_port, host_port)
    return {**fallback, **preferred}


def cmd_up(args: argparse.Namespace) -> int:
    name = args.name or f"swt-m09-{secrets.token_hex(4)}"
    hint = (f"container {name} may be left behind; "
            f"run 'login-wall.py down --name {name}' to clean up")
    try:
        _podman([
            "run", "-d", "--shm-size", "1g", "--name", name,
            "-p", "22", "-p", "6080", args.image,
        ])
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"up failed: {error}", file=sys.stderr)
        print(hint, file=sys.stderr)
        return 1
    exec_args = ["exec"]
    if args.geom:
        exec_args += ["-e", f"GEOM={args.geom}"]
    exec_args += [name, "swt-vnc", "start"]
    started = _podman(exec_args, check=False, timeout=300)
    if started.returncode != 0:
        print(started.stderr.strip(), file=sys.stderr)
        print(hint, file=sys.stderr)
        return 1
    ports = discover_ports(name)
    if "6080/tcp" not in ports:
        print("up failed: no host port mapped for 6080/tcp", file=sys.stderr)
        print(hint, file=sys.stderr)
        return 1
    state = {
        "container": name,
        "image": args.image,
        "ports": ports,
        "url": f"http://127.0.0.1:{ports['6080/tcp']}/vnc.html?resize=scale",
        "geom": args.geom,
    }
    print(json.dumps(state))
    return 0


def cmd_down(args: argparse.Namespace) -> int:
    result = _podman(["rm", "-f", args.name], check=False)
    if result.returncode == 0:
        print(f"container {args.name} removed")
        return 0
    if "no such" in result.stderr.lower():
        print(f"container {args.name} already gone")
        return 0
    print(result.stderr.strip(), file=sys.stderr)
    return 1


def cmd_build(args: argparse.Namespace) -> int:
    """ISSUE-04 #3 build: image-prep build 的薄封装.

    --requirements 缺省指向仓库内 image/requirements-browser.md;
    --prefix/--records-root 必传 (测试隔离用, 不落真实存储);
    退出码与输出原样透传, 无额外逻辑.
    """
    result = subprocess.run(
        [sys.executable, str(IMAGE_PREP_SCRIPT), "build",
         "--repo", args.repo,
         "--requirements", args.requirements or str(DEFAULT_REQUIREMENTS),
         "--prefix", args.prefix,
         "--records-root", args.records_root],
        capture_output=True, text=True, check=False,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.returncode != 0 and result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M09 登录墙编排器")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_up = subparsers.add_parser("up", help="起容器并启动 VNC 栈, 输出状态 json")
    p_up.add_argument("--image", required=True, help="项目层镜像引用")
    p_up.add_argument("--name", default=None, help="容器名, 缺省随机")
    p_up.add_argument("--geom", default=None, help="Xvfb 分辨率 WxH[xD], 缺省 1920x1080x24")
    p_up.set_defaults(handler=cmd_up)

    p_down = subparsers.add_parser("down", help="删容器 (幂等)")
    p_down.add_argument("--name", required=True)
    p_down.set_defaults(handler=cmd_down)

    p_verify = subparsers.add_parser(
        "verify", help="通道检查: noVNC HTTP/ws/RFB banner/空白基线")
    p_verify.add_argument("--name", required=True, help="up 起的容器名")
    p_verify.add_argument("--evidence-dir", default=None,
                          help="PPM 证据目录, 缺省临时目录")
    p_verify.set_defaults(handler=cmd_verify)

    p_build = subparsers.add_parser(
        "build", help="调 image-prep build 项目层镜像 (薄封装)")
    p_build.add_argument("--repo", required=True, help="项目仓库路径 (slug 推导)")
    p_build.add_argument("--requirements", default=None,
                         help="缺省 image/requirements-browser.md")
    p_build.add_argument("--prefix", required=True)
    p_build.add_argument("--records-root", required=True)
    p_build.set_defaults(handler=cmd_build)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except RuntimeError as error:
        print(f"PODMAN-FAIL {error}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as error:
        print(f"PODMAN-TIMEOUT {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("RFB server closed connection early")
        buf += chunk
    return buf


class RfbClient:
    """RFB 3.8 客户端, 经既有 socket (duck-typed) 收发."""

    def __init__(self, sock: socket.socket, timeout: float = 5.0):
        self.sock = sock
        sock.settimeout(timeout)
        # 握手后由 ServerInit 填充; 未握手前请求全量更新无尺寸可用
        self.frame_width: int | None = None
        self.frame_height: int | None = None

    def handshake(self, shared: bool = True) -> ServerInfo:
        banner = _recv_exact(self.sock, len(RFB_BANNER))
        if banner != RFB_BANNER:
            raise ValueError(f"unexpected RFB banner: {banner!r}")
        self.sock.sendall(RFB_BANNER)

        (count,) = struct.unpack(">B", _recv_exact(self.sock, 1))
        types = _recv_exact(self.sock, count)
        if SECURITY_NONE not in types:
            raise ValueError("server offers no None security type")
        self.sock.sendall(struct.pack(">B", SECURITY_NONE))

        (result,) = struct.unpack(">I", _recv_exact(self.sock, 4))
        if result != 0:
            raise ValueError(f"security handshake failed: {result}")

        self.sock.sendall(struct.pack(">B", 1 if shared else 0))

        width, height = struct.unpack(">HH", _recv_exact(self.sock, 4))
        _recv_exact(self.sock, 16)  # pixel format (unused; we pin our own)
        (name_len,) = struct.unpack(">I", _recv_exact(self.sock, 4))
        name = _recv_exact(self.sock, name_len).decode("utf-8", "replace")
        self.frame_width = width
        self.frame_height = height
        return ServerInfo(width=width, height=height, name=name)

    def set_pixel_format(self) -> None:
        # type 0, 3 pad, 16-byte pixel format
        self.sock.sendall(struct.pack(">B3x", 0) + PIXEL_FORMAT_32BPP_LE)

    def set_encodings_raw(self) -> None:
        # type 2, pad, u16 count, s32 encodings
        self.sock.sendall(
            struct.pack(">BxH", 2, 1) + struct.pack(">i", ENCODING_RAW)
        )

    def request_full_update(self) -> None:
        if self.frame_width is None or self.frame_height is None:
            raise RuntimeError(
                "request_full_update 需先调用 handshake 获取帧尺寸"
            )
        # type 3, incremental=0, rect x y w h (w/h filled at call time
        # from the negotiated ServerInit dimensions)
        self.sock.sendall(
            struct.pack(">BB", 3, 0)
            + struct.pack(">HHHH", 0, 0, self.frame_width, self.frame_height)
        )

    def read_framebuffer_update(self) -> list[FrameRect]:
        msg_type, _pad = struct.unpack(">BB", _recv_exact(self.sock, 2))
        if msg_type != 0:
            raise ValueError(f"expected FramebufferUpdate, got type {msg_type}")
        (nrects,) = struct.unpack(">H", _recv_exact(self.sock, 2))
        rects = []
        for _ in range(nrects):
            x, y, w, h = struct.unpack(">HHHH", _recv_exact(self.sock, 8))
            (encoding,) = struct.unpack(">i", _recv_exact(self.sock, 4))
            if encoding != ENCODING_RAW:
                raise ValueError(f"unsupported encoding: {encoding}")
            raw = _recv_exact(self.sock, w * h * 4)
            rects.append(FrameRect(x, y, w, h, raw32_to_rgb(raw)))
        return rects
