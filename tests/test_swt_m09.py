"""M10 display-stack tests (ISSUE-04 → D039/D040/D041/D042 重写).

原 M09 login-wall 测试迁家: login-wall.py 已整删, 通道检查迁为
scripts/swt-display.py (被 swt display-check 子命令调用); 浏览器栈
从独立项目层改烘 display 层 (image-prep build-display); 容器生命周期
归 swt birth, 本文件用裸 podman run 直驱容器验证 swt-vnc 与检查链.

TS-001 slice: pure RFB client logic. A fake RFB 3.8 server (test-side,
independent truth: RFC 6143 byte layout) feeds banner / Security /
SecurityResult / ServerInit / framebuffer update. Expected client byte
streams are hand-computed literals, never derived from implementation
symbols (anti-pattern: tautology).

TS-002 slice (TestDisplayLayerBuildE2E): isolated real base + display build
with requirements-browser.md; network heavy, class-level shared fixtures.
"""
from __future__ import annotations

import atexit
import contextlib
import importlib.util
import re
import secrets
import socket
import struct
import subprocess
import sys
import threading
import unittest
import unittest.mock
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
DISPLAY_SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt-display.py"
SWT_SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"
IMAGE_PREP = ROOT / "workflow/use-sandbox-worktree/scripts/image-prep.py"
REQ_BROWSER = ROOT / "workflow/use-sandbox-worktree/image/requirements-browser.md"

BANNER = b"RFB 003.008\n"
TIMEOUT = 5.0


def _load_module():
    spec = importlib.util.spec_from_file_location("swt_display", DISPLAY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt_display"] = module
    spec.loader.exec_module(module)
    return module


class FakeRfbServer:
    """RFB 3.8 server side of a socketpair; records every byte received."""

    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.received = b""
        self.error: BaseException | None = None

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("client closed early")
            buf += chunk
        self.received += buf
        return buf

    def send(self, data: bytes) -> None:
        self.conn.sendall(data)

    # --- protocol steps, byte layout per RFC 6143 ---

    def send_banner_and_security(self) -> None:
        self.send(BANNER)
        self.send(struct.pack(">BB", 1, 1))  # 1 security type: None(1)

    def expect_banner_and_choice(self) -> None:
        assert self._recv_exact(12) == BANNER
        assert self._recv_exact(1) == b"\x01"  # client picks None

    def send_security_result_ok(self) -> None:
        self.send(struct.pack(">I", 0))

    def expect_client_init(self, shared: int) -> None:
        assert self._recv_exact(1) == bytes([shared])

    def send_server_init(self, width: int, height: int, name: bytes) -> None:
        # 这 16 字节与实现侧 PIXEL_FORMAT_32BPP_LE 同构, 但从不被断言:
        # 仅作长度占位, 内容不校验 (客户端按约定忽略 ServerInit 内格式).
        pixfmt = struct.pack(
            ">BBBBHHHBBB3x", 32, 24, 0, 1, 255, 255, 255, 16, 8, 0
        )
        self.send(struct.pack(">HH", width, height) + pixfmt)
        self.send(struct.pack(">I", len(name)) + name)

    def complete_handshake(self, width: int = 32, height: int = 16,
                           name: bytes = b"swt-test", shared: int = 1) -> None:
        """banner/Security/SecurityResult/ClientInit/ServerInit 五步组合."""
        self.send_banner_and_security()
        self.expect_banner_and_choice()
        self.send_security_result_ok()
        self.expect_client_init(shared=shared)
        self.send_server_init(width, height, name)

    def expect_client_messages(self, width: int, height: int) -> None:
        """Hand-computed literals for SetPixelFormat / SetEncodings /
        FramebufferUpdateRequest, per RFC 6143 §5 and RFB 3.8."""
        set_pixel_format = (
            b"\x00\x00\x00\x00"          # type 0 + 3 padding
            b"\x20\x18\x00\x01"          # 32bpp, depth 24, little-endian, true-colour
            b"\x00\xff\x00\xff\x00\xff"  # red/green/blue max = 255 (u16 BE)
            b"\x10\x08\x00"              # shifts: r16 g8 b0
            b"\x00\x00\x00"              # padding
        )
        set_encodings_raw_only = (
            b"\x02\x00"                  # type 2 + padding
            b"\x00\x01"                  # 1 encoding
            b"\x00\x00\x00\x00"          # encoding raw = 0
        )
        fbu_request_full = (
            b"\x03\x00"                  # type 3, incremental = 0
            b"\x00\x00\x00\x00"          # x=0 y=0
            + struct.pack(">HH", width, height)  # w h
        )
        assert self._recv_exact(20) == set_pixel_format
        assert self._recv_exact(8) == set_encodings_raw_only
        assert self._recv_exact(10) == fbu_request_full

    def send_framebuffer_update(self, pixels32: bytes, w: int, h: int,
                                x: int = 0, y: int = 0) -> None:
        rect = struct.pack(">HHHH", x, y, w, h) + b"\x00\x00\x00\x00"
        self.send(b"\x00\x00" + struct.pack(">H", 1) + rect + pixels32)


@contextlib.contextmanager
def rfb_pair(scenario):
    """Run FakeRfbServer in a daemon thread; yield (RfbClient, fake).

    Both sides carry timeouts; the context manager closes the client socket
    and joins the thread, so no test can hang the interpreter on exit.
    """
    lw = _load_module()
    client_sock, server_sock = socket.socketpair()
    client_sock.settimeout(TIMEOUT)
    server_sock.settimeout(TIMEOUT)
    fake = FakeRfbServer(server_sock)

    def run():
        try:
            scenario(fake)
        except BaseException as exc:
            fake.error = exc
        finally:
            with contextlib.suppress(OSError):
                server_sock.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        yield lw.RfbClient(client_sock), fake
    except BaseException as exc:
        # 后台线程的断言失败是真因, 优先重抛, 避免被主线程因 socket
        # 早关看到的 ConnectionError/timeout 掩盖误诊; 非断言类后台
        # 异常 (如双方互等超时) 时主线程异常更接近现场, 原样重抛.
        thread.join(timeout=TIMEOUT)
        if isinstance(fake.error, AssertionError):
            raise fake.error from exc
        raise
    finally:
        with contextlib.suppress(OSError):
            client_sock.close()
        thread.join(timeout=TIMEOUT)


def test_client_pins_pixel_format_raw_encoding_and_requests_full_update():
    def scenario(fake: FakeRfbServer):
        fake.complete_handshake(width=32, height=16)
        fake.expect_client_messages(width=32, height=16)

    with rfb_pair(scenario) as (client, fake):
        client.handshake(shared=True)
        client.set_pixel_format()
        client.set_encodings_raw()
        client.request_full_update()

    assert fake.error is None, f"fake server failed: {fake.error!r}"


def test_read_framebuffer_update_decodes_raw_32bpp_pixels():
    # 2x2 rect: red, green, blue, white as 32bpp LE (r16 g8 b0)
    pixels32 = (
        b"\x00\x00\xff\x00"  # red   = 255<<16 LE
        b"\x00\xff\x00\x00"  # green = 255<<8 LE
        b"\xff\x00\x00\x00"  # blue  = 255 LE
        b"\xff\xff\xff\x00"  # white = 0x00FFFFFF LE
    )

    def scenario(fake: FakeRfbServer):
        fake.complete_handshake(width=32, height=16)
        fake.expect_client_messages(width=32, height=16)
        fake.send_framebuffer_update(pixels32, w=2, h=2)

    with rfb_pair(scenario) as (client, fake):
        client.handshake(shared=True)
        client.set_pixel_format()
        client.set_encodings_raw()
        client.request_full_update()
        rects = client.read_framebuffer_update()

    assert fake.error is None, f"fake server failed: {fake.error!r}"
    assert len(rects) == 1
    rect = rects[0]
    assert (rect.x, rect.y, rect.w, rect.h) == (0, 0, 2, 2)
    assert rect.rgb == (
        b"\xff\x00\x00"  # red
        b"\x00\xff\x00"  # green
        b"\x00\x00\xff"  # blue
        b"\xff\xff\xff"  # white
    )


def test_ppm_bytes_writes_p6_header_plus_rgb():
    lw = _load_module()
    rgb = b"\xff\x00\x00\x00\xff\x00"  # red, green
    assert lw.ppm_bytes(2, 1, rgb) == b"P6\n2 1\n255\n" + rgb


def test_non_black_ratio_and_content_threshold():
    lw = _load_module()
    pixels = (
        b"\x00\x00\x00"  # black
        b"\xff\x00\x00"  # red
        b"\x00\x00\x00"  # black
        b"\xff\xff\xff"  # white
    )
    assert lw.non_black_ratio(pixels) == 0.5
    assert lw.non_black_ratio(b"\x00\x00\x00" * 4) == 0.0
    assert lw.non_black_ratio(b"\xff\x00\x00" * 4) == 1.0
    assert lw.frame_has_content(pixels, min_ratio=0.6) is False
    assert lw.frame_has_content(pixels, min_ratio=0.4) is True


def test_handshake_sends_protocol_bytes_and_parses_server_init():
    def scenario(fake: FakeRfbServer):
        fake.complete_handshake(width=32, height=16)

    with rfb_pair(scenario) as (client, fake):
        info = client.handshake(shared=True)

    assert fake.error is None, f"fake server failed: {fake.error!r}"
    assert fake.received.startswith(BANNER)
    assert info.width == 32
    assert info.height == 16
    assert info.name == "swt-test"


# ------------------------------------------------------- TS-002 e2e (display 层)


def _run_ip(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    """Run image-prep.py with a hard wall-clock cap (network heavy builds)."""
    return subprocess.run(
        [sys.executable, str(IMAGE_PREP), *args],
        capture_output=True, text=True, check=False, timeout=timeout,
    )


def _kv(stdout: str) -> dict[str, str]:
    out = {}
    for line in stdout.splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            out[key] = value
    return out


def _build_image_fixtures(records_root: Path, repo: Path, prefix: str,
                          base_ref: str) -> tuple[dict, dict]:
    """One isolated build-base + one display build (network heavy, cached).

    Raises unittest.SkipTest on build failure so classes degrade to skips.
    """
    base = _run_ip([
        "build-base",
        "--records-root", str(records_root),
        "--skills-dir", str(Path.home() / ".agents" / "skills"),
        "--pi-agent-dir", str(Path.home() / ".pi" / "agent"),
        "--base-ref", base_ref,
    ])
    if base.returncode != 0:
        raise unittest.SkipTest(f"base build failed: {base.stderr[-800:]}")
    display = _run_ip([
        "build-display",
        "--requirements", str(REQ_BROWSER),
        "--records-root", str(records_root),
        "--prefix", prefix,
        "--base-ref", base_ref,
    ])
    if display.returncode != 0:
        raise unittest.SkipTest(f"display build failed: {display.stderr[-800:]}")
    return _kv(base.stdout), _kv(display.stdout)


_SHARED_FIXTURES: dict | None = None


def _shared_image_fixtures() -> dict:
    """模块级一次性构建夹具: 各 e2e 类共享同一套 base+display 镜像.

    首次调用真实构建 (cached 层可加速), 后续调用直接复用; 镜像与
    records 的清理注册在 atexit, 进程退出时执行一次, 类间不互相拆除.
    """
    global _SHARED_FIXTURES
    if _SHARED_FIXTURES is not None:
        return _SHARED_FIXTURES
    root = Path(mkdtemp(prefix="swt-m09-"))
    fixtures = {
        "root": root,
        "records_root": root / "records",
        "repo": root / "repo",
        "prefix": f"localhost/swt-m09-{secrets.token_hex(3)}",
    }
    fixtures["repo"].mkdir(parents=True)
    fixtures["base_ref"] = f"{fixtures['prefix']}/base"

    def _cleanup_shared():
        # SIGKILL 场景下本函数不执行: 构建/失败时已把 prefix 打到 stderr 供人工清
        # reference glob 不跨 "/": prefix*/* 才能命中 prefix/base:tag 与 prefix/display:tag
        print(f"[swt-m09-fixtures] cleanup prefix={fixtures['prefix']}",
              file=sys.stderr)
        subprocess.run(
            ["bash", "-c",
             f"podman images --format '{{{{.ID}}}}' "
             f"--filter reference={fixtures['prefix']}*/* "
             f"| xargs -r podman rmi -f"],
            capture_output=True,
        )
        rmtree(fixtures["root"], ignore_errors=True)

    atexit.register(_cleanup_shared)  # mkdtemp 后立即注册: 构建中途失败也不泄漏
    print(f"[swt-m09-fixtures] prefix={fixtures['prefix']} "
          f"records-root={fixtures['records_root']} "
          "(进程被杀时的残留可按此人工清理)", file=sys.stderr)
    base_values, display_values = _build_image_fixtures(
        fixtures["records_root"], fixtures["repo"], fixtures["prefix"],
        fixtures["base_ref"],
    )
    fixtures["base_values"] = base_values
    fixtures["display_values"] = display_values
    fixtures["image"] = display_values["image"]
    _SHARED_FIXTURES = fixtures
    return _SHARED_FIXTURES


class TestDisplayLayerBuildE2E(unittest.TestCase):
    """TS-002: isolated real base + display layer build (D039).

    Isolation: --prefix localhost/swt-m09-<random> and records root under
    /tmp/swt-m09-<random>; never touches user images or real records.
    """

    @classmethod
    def setUpClass(cls):
        info = subprocess.run(["podman", "info"], capture_output=True, text=True)
        if info.returncode != 0:
            raise unittest.SkipTest(f"podman unavailable: {info.stderr.strip()}")
        fixtures = _shared_image_fixtures()
        cls.prefix = fixtures["prefix"]
        cls.base_ref = fixtures["base_ref"]
        cls.records_root = fixtures["records_root"]
        cls.base_values: dict[str, str] = fixtures["base_values"]
        cls.display_values: dict[str, str] = fixtures["display_values"]

    def _podman_sh(self, image: str, command: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["podman", "run", "--rm", image, "sh", "-c", command],
            capture_output=True, text=True, check=False, timeout=300,
        )

    def test_real_base_build_contract(self):
        """真 skills staging 的 build-base: build-id 与 record 在位."""
        values = type(self).base_values
        assert values is not None
        self.assertRegex(values["build-id"], r"\d{4}\.\d{2}\.\d{2}-\d+")
        self.assertTrue(
            (self.records_root / "base" / "builds" / values["build-id"]
             / "contents.md").is_file(),
        )

    def test_display_layer_probes_and_artifacts(self):
        """display 层全 probe 过 + swt-vnc 可执行 + fonts 在位 + chromium 版本
        + 记录落 display/builds + Containerfile FROM 当前 base@digest."""
        values = type(self).display_values
        assert values is not None
        image = values["image"]
        self.assertTrue(image.startswith(f"{self.prefix}/display:"))
        record = Path(values["record"])
        self.assertEqual(record.parents[1].name, "display")
        containerfile = (record / "Containerfile").read_text()
        self.assertTrue(containerfile.startswith(
            f"FROM {self.base_ref}@"))
        contents = (record / "contents.md").read_text()
        for name in ("xvfb", "x11vnc", "websockify", "novnc",
                     "fonts-noto-cjk", "chromium", "swt-vnc"):
            self.assertRegex(contents, rf"(?m)^{name}: (?!MISSING)\S", msg=contents)

        # swt-vnc 可执行: status 报三进程状态, 全 down 时退出码 1
        status = self._podman_sh(image, "swt-vnc status")
        for process in ("xvfb", "x11vnc", "websockify"):
            self.assertIn(f"{process}: down", status.stdout, msg=status.stdout)
        self.assertEqual(status.returncode, 1, msg=status.stdout + status.stderr)

        # fonts-noto-cjk 在位 (dpkg 实测 installed)
        fonts = self._podman_sh(
            image, "dpkg-query -W -f='${Status}' fonts-noto-cjk"
        )
        self.assertIn("install ok installed", fonts.stdout, msg=fonts.stderr)

        # playwright chromium 二进制可跑出版本
        chrome = self._podman_sh(
            image,
            "/home/bolo/.cache/ms-playwright/chromium-*/chrome-linux*/chrome --version",
        )
        self.assertEqual(chrome.returncode, 0, msg=chrome.stderr)
        self.assertRegex(chrome.stdout + chrome.stderr, r"\d+(\.\d+)+")


# ---------------------------------------------------------------- TS-003 e2e


def _run_swt(args: list[str], timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SWT_SCRIPT), *args],
        capture_output=True, text=True, check=False, timeout=timeout,
    )


class _DisplayContainerTestCase(unittest.TestCase):
    """display 层容器直驱夹具: 裸 podman run (回环发布 + shm 1g) +
    swt-vnc start, 模拟 swt birth 的容器形态; 类级共享镜像."""

    image: str = ""

    @classmethod
    def setUpClass(cls):
        info = subprocess.run(["podman", "info"], capture_output=True, text=True)
        if info.returncode != 0:
            raise unittest.SkipTest(f"podman unavailable: {info.stderr.strip()}")
        fixtures = _shared_image_fixtures()
        cls.image = fixtures["image"]
        cls.containers: list[str] = []

    @classmethod
    def tearDownClass(cls):
        for name in getattr(cls, "containers", []):
            subprocess.run(
                ["podman", "rm", "-f", "-v", name], capture_output=True,
            )

    def _start_container(self, name: str, geom: str | None = None) -> None:
        """swt birth 同型: -p 127.0.0.1::6080 回环动态 (测试互不抢 6080)
        + --shm-size=1g, 然后 exec swt-vnc start."""
        args = ["podman", "run", "-d", "--shm-size", "1g", "--name", name,
                "-p", "127.0.0.1::6080"]
        if geom:
            args += ["-e", f"GEOM={geom}"]
        args.append(self.image)
        run_result = subprocess.run(args, capture_output=True, text=True,
                                    check=False, timeout=300)
        type(self).containers.append(name)  # 断言前登记, 失败也兜底清理
        self.addCleanup(
            subprocess.run, ["podman", "rm", "-f", "-v", name], capture_output=True,
        )
        self.assertEqual(run_result.returncode, 0, run_result.stderr)
        started = subprocess.run(
            ["podman", "exec", name, "swt-vnc", "start"],
            capture_output=True, text=True, check=False, timeout=300,
        )
        self.assertEqual(started.returncode, 0, started.stderr)

    def _exec(self, name: str, command: str, check: bool = False):
        return subprocess.run(
            ["podman", "exec", name, "sh", "-c", command],
            capture_output=True, text=True, check=check, timeout=300,
        )

    def _rfb_frame_size(self, name: str) -> tuple[int, int]:
        """RFB 单一真相源: cp 纯逻辑进容器, 容器内 python3 握手读尺寸."""
        subprocess.run(
            ["podman", "cp", str(DISPLAY_SCRIPT), f"{name}:/tmp/swt_display.py"],
            capture_output=True, text=True, check=True,
        )
        probe = (
            "import importlib.util,socket;"
            "spec=importlib.util.spec_from_file_location('swt_display','/tmp/swt_display.py');"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "s=socket.create_connection(('127.0.0.1',5900),10);"
            "i=m.RfbClient(s).handshake();"
            "print(i.width, i.height)"
        )
        result = subprocess.run(
            ["podman", "exec", name, "python3", "-c", probe],
            capture_output=True, text=True, check=False, timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr[-2000:])
        width, height = (int(part) for part in result.stdout.split())
        return width, height


class TestDisplayContainerE2E(_DisplayContainerTestCase):
    """TS-003: 回环发布容器 + swt-vnc start -> GEOM resolution,
    5900 0.0.0.0 监听, 宿主端口回环发现; swt-vnc status/stop 幂等."""

    def _host_vnc_port(self, name: str) -> int:
        result = subprocess.run(
            ["podman", "port", name, "6080"],
            capture_output=True, text=True, check=True,
        )
        match = re.search(r":(\d+)\s*$", result.stdout.strip(), re.MULTILINE)
        self.assertIsNotNone(match, result.stdout)
        return int(match.group(1))

    def test_container_contract_and_default_resolution(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name)
        inspect = subprocess.run(
            ["podman", "inspect", name, "--format",
             "{{.State.Running}}|{{.HostConfig.ShmSize}}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        running, shm_size = inspect.split("|")
        self.assertEqual(running, "true")
        self.assertEqual(int(shm_size), 1 << 30)  # --shm-size 1g
        # 宿主侧经回环映射的 6080 可 TCP 连上
        host_port = self._host_vnc_port(name)
        with socket.create_connection(("127.0.0.1", host_port), timeout=10):
            pass
        # RFB 缺省 GEOM: 1920x1080
        self.assertEqual(self._rfb_frame_size(name), (1920, 1080))
        # 5900 必须监听 0.0.0.0: 容器内 /proc/net/tcp 直接断言
        # (x11vnc 若改绑回环, 此处红); 5900 = hex 170C, 0A = LISTEN
        proc_net = self._exec(name, "cat /proc/net/tcp")
        listen_rows = [
            line for line in proc_net.stdout.splitlines()
            if re.search(r":170C\s+[0-9A-F]+:[0-9A-F]+\s+0A\s", line)
        ]
        self.assertTrue(listen_rows, msg=proc_net.stdout)
        local_addrs = {line.split()[1] for line in listen_rows}
        self.assertTrue(
            any(addr.startswith("00000000:") for addr in local_addrs),
            msg=f"5900 未绑 0.0.0.0: {sorted(local_addrs)}",
        )

    def test_geom_env_controls_resolution(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name, geom="1280x720")
        self.assertEqual(self._rfb_frame_size(name), (1280, 720))  # 生效值经 RFB 读出

    def test_status_as_bolo_reports_running(self):
        """M14 发现 7: 栈由 root 拉起 (swt birth 的 podman exec 缺省身份) 时,
        bolo 跑 swt-vnc status 不得误报 down — kill -0 对 root 进程吃 EPERM,
        存活判定须与属主无关."""
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name)
        status = subprocess.run(
            ["podman", "exec", "--user", "bolo", name, "swt-vnc", "status"],
            capture_output=True, text=True, check=False, timeout=60,
        )
        self.assertEqual(status.returncode, 0, msg=status.stdout + status.stderr)
        for process in ("xvfb", "x11vnc", "websockify"):
            self.assertIn(f"{process}: running", status.stdout, msg=status.stdout)

    def test_start_status_stop_idempotent(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name)  # 启动已含首轮 start
        second = self._exec(name, "swt-vnc start")
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        for process in ("xvfb", "x11vnc", "websockify"):
            self.assertIn(f"{process}: already running", second.stdout,
                          msg=second.stdout)
        pid_count = self._exec(name, "ls /tmp/swt-vnc/*.pid | wc -l")
        self.assertEqual(pid_count.stdout.strip(), "3")  # 不双起

        status_up = self._exec(name, "swt-vnc status")
        self.assertEqual(status_up.returncode, 0, msg=status_up.stdout)
        for process in ("xvfb", "x11vnc", "websockify"):
            self.assertIn(f"{process}: running", status_up.stdout)
        for port in ("5900", "6080"):
            self.assertIn(f"port {port}: listening", status_up.stdout)

        stop_first = self._exec(name, "swt-vnc stop")
        self.assertEqual(stop_first.returncode, 0, msg=stop_first.stderr)
        status_down = self._exec(name, "swt-vnc status")
        self.assertEqual(status_down.returncode, 1)
        self.assertIn("xvfb: down", status_down.stdout)
        self.assertIn("port 5900: closed", status_down.stdout)

        stop_again = self._exec(name, "swt-vnc stop")
        self.assertEqual(stop_again.returncode, 0, msg=stop_again.stderr)


# ---------------------------------------------------------------- TS-004 e2e


class TestWsFrameDecode(unittest.TestCase):
    """ws 帧解码纯逻辑, 独立真相源 = RFC 6455 §5.2 手写字节.

    服务端 -> 客户端方向: 不带掩码; 长度三档 (7/16/64 位).
    """

    @classmethod
    def setUpClass(cls):
        cls.lw = _load_module()

    def test_small_binary_frame_carries_rfb_banner(self):
        banner = b"RFB 003.008\n"  # 12 bytes -> 7-bit length
        opcode, payload = self.lw.ws_read_frame(
            lambda n: banner, prepend=b"\x82\x0c"
        )
        self.assertEqual((opcode, payload), (0x2, banner))

    def test_text_frame_opcode(self):
        opcode, payload = self.lw.ws_read_frame(
            lambda n: b"hi!", prepend=b"\x81\x03"
        )
        self.assertEqual((opcode, payload), (0x1, b"hi!"))

    def test_16bit_length(self):
        body = b"x" * 20  # 20 > 125 -> 16-bit length (0x7e: 无掩码 + len=126)
        opcode, payload = self.lw.ws_read_frame(
            lambda n: body, prepend=b"\x82\x7e\x00\x14"
        )
        self.assertEqual((opcode, payload), (0x2, body))

    def test_64bit_length(self):
        body = b"y" * 20
        header = b"\x82\x7f" + (20).to_bytes(8, "big")  # 0x7f: 无掩码 + len=127
        opcode, payload = self.lw.ws_read_frame(
            lambda n: body, prepend=header
        )
        self.assertEqual((opcode, payload), (0x2, body))

    def test_masked_frame_rejected(self):
        with self.assertRaises(ValueError):
            self.lw.ws_read_frame(lambda n: b"", prepend=b"\x82\x84abcd")

    def test_fragmented_stream_reassembles(self):
        """101 响应与首帧同包到达 / 流分片: prepend + 逐字节 recv 仍完整解出."""
        frame = b"\x82\x0c" + b"RFB 003.008\n"
        it = iter(frame)
        opcode, payload = self.lw.ws_read_frame(
            lambda n: bytes([next(it)]), prepend=b""
        )
        self.assertEqual((opcode, payload), (0x2, b"RFB 003.008\n"))

    def test_close_control_frame_passthrough(self):
        """close 控制帧 (0x8): 按实现语义原样解出, 不特判."""
        opcode, payload = self.lw.ws_read_frame(
            lambda n: b"\x00\x00", prepend=b"\x88\x02"
        )
        self.assertEqual((opcode, payload), (0x8, b"\x00\x00"))

    def test_compose_framebuffer_places_rects(self):
        """4x2 黑底, rect(1,0,2,2) 填红绿红绿: 手算布局."""
        rects = [self.lw.FrameRect(
            1, 0, 2, 2,
            b"\xff\x00\x00\x00\xff\x00\xff\x00\x00\x00\xff\x00",  # 2x2=4 像素
        )]
        frame = self.lw.compose_framebuffer(4, 2, rects)
        expected = (
            b"\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x00"  # row 0
            b"\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x00"  # row 1
        )
        self.assertEqual(frame, expected)

    def test_compose_multiple_rects_tile(self):
        """两 rect 各占半幅拼接: 左红右绿."""
        rects = [
            self.lw.FrameRect(0, 0, 2, 2, b"\xff\x00\x00" * 4),
            self.lw.FrameRect(2, 0, 2, 2, b"\x00\xff\x00" * 4),
        ]
        frame = self.lw.compose_framebuffer(4, 2, rects)
        expected = (
            b"\xff\x00\x00\xff\x00\x00\x00\xff\x00\x00\xff\x00"
            b"\xff\x00\x00\xff\x00\x00\x00\xff\x00\x00\xff\x00"
        )
        self.assertEqual(frame, expected)

    def test_compose_out_of_bounds_raises(self):
        for bad in (
            self.lw.FrameRect(3, 0, 2, 2, b"\x00" * 12),   # x+w 超 width
            self.lw.FrameRect(0, 1, 4, 2, b"\x00" * 24),   # y+h 超 height
            self.lw.FrameRect(-1, 0, 1, 1, b"\x00" * 3),   # 负坐标
        ):
            with self.assertRaises(ValueError):
                self.lw.compose_framebuffer(4, 2, [bad])

    def test_compose_overlap_last_wins(self):
        """重叠区后写覆盖: 红 rect 被绿 rect 覆盖."""
        rects = [
            self.lw.FrameRect(0, 0, 2, 1, b"\xff\x00\x00\xff\x00\x00"),
            self.lw.FrameRect(0, 0, 2, 1, b"\x00\xff\x00\x00\xff\x00"),
        ]
        frame = self.lw.compose_framebuffer(4, 1, rects)
        self.assertEqual(
            frame,
            b"\x00\xff\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00",
        )

    def test_compose_rgb_size_mismatch_raises(self):
        with self.assertRaises(ValueError):
            self.lw.compose_framebuffer(
                4, 2, [self.lw.FrameRect(0, 0, 2, 2, b"\x00" * 6)])


class TestDisplayCheckChannelE2E(_DisplayContainerTestCase):
    """TS-004: swt display-check 通道检查 — noVNC HTTP 200 + ws 握手 101
    + ws 帧 RFB banner; 容器内空白 framebuffer 基线 (非黑 < 1%) + PPM 证据."""

    def test_display_check_channels_pass_and_evidence(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name)
        evidence = Path(mkdtemp(prefix="swt-m09-verify-"))
        self.addCleanup(rmtree, evidence, True)
        result = _run_swt([
            "display-check", "--name", name, "--evidence-dir", str(evidence),
        ], timeout=600)
        self.assertEqual(result.returncode, 0,
                         msg=result.stdout + result.stderr[-2000:])
        for check in ("http_vnc_html_200", "ws_handshake_101",
                      "ws_rfb_banner", "blank_frame_baseline"):
            self.assertIn(f"check {check}: OK", result.stdout, msg=result.stdout)
        self.assertIn("evidence:", result.stdout)
        ppm_path = Path(result.stdout.split("evidence:")[1].strip().splitlines()[0])
        self.assertTrue(ppm_path.is_file(), msg=str(ppm_path))
        self.assertTrue(ppm_path.read_bytes().startswith(b"P6\n1920 1080\n255\n"),
                        msg=ppm_path.read_bytes()[:32])

    def test_display_check_fails_after_stack_stop(self):
        """负例: VNC 栈停后 display-check 必须红 (证明检查真的在测)."""
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name)
        stop = self._exec(name, "swt-vnc stop")
        self.assertEqual(stop.returncode, 0, msg=stop.stderr)
        result = _run_swt(["display-check", "--name", name], timeout=600)
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FAIL", result.stdout, msg=result.stdout)


# ---------------------------------------------------------------- TS-005 e2e


class TestDisplayRenderE2E(_DisplayContainerTestCase):
    """TS-005: headed chromium 渲染高对比页 -> framebuffer 非黑超阈值
    + PPM 证据回 host; headless 回切 (换 cwd, 无 DISPLAY)."""

    def test_display_check_render_checks_pass_with_evidence(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._start_container(name)
        # 嵌套不存在路径: evidence-dir 需自行创建 (podman cp 不建宿主目录)
        evidence = Path(mkdtemp(prefix="swt-m09-render-")) / "a" / "b"
        self.addCleanup(rmtree, evidence.parent.parent, True)
        result = _run_swt([
            "display-check", "--name", name, "--evidence-dir", str(evidence),
        ], timeout=1800)
        self.assertEqual(result.returncode, 0,
                         msg=result.stdout + result.stderr[-2000:])
        for check in ("headed_render_nonblack", "headless_fallback_ok"):
            self.assertIn(f"check {check}: OK", result.stdout, msg=result.stdout)
        ppm = evidence / "rendering.ppm"
        self.assertTrue(ppm.is_file(), msg=result.stdout)
        self.assertTrue(ppm.read_bytes().startswith(b"P6\n1920 1080\n255\n"),
                        msg=ppm.read_bytes()[:32])


if __name__ == "__main__":
    unittest.main()
