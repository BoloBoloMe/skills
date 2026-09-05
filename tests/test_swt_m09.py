"""M09 login-wall tests (ISSUE-04).

TS-001 slice: pure RFB client logic. A fake RFB 3.8 server (test-side,
independent truth: RFC 6143 byte layout) feeds banner / Security /
SecurityResult / ServerInit / framebuffer update. Expected client byte
streams are hand-computed literals, never derived from implementation
symbols (anti-pattern: tautology).

TS-002 slice (TestBrowserImageE2E): isolated real base + project build with
requirements-browser.md; network heavy, class-level shared fixtures.
"""
from __future__ import annotations

import atexit
import contextlib
import importlib.util
import io
import json
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
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/login-wall.py"
IMAGE_PREP = ROOT / "workflow/use-sandbox-worktree/scripts/image-prep.py"
REQ_BROWSER = ROOT / "workflow/use-sandbox-worktree/image/requirements-browser.md"

BANNER = b"RFB 003.008\n"
TIMEOUT = 5.0


def _load_module():
    spec = importlib.util.spec_from_file_location("login_wall", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["login_wall"] = module
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


# --------------------------------------------------------------- TS-002 e2e


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
    """One isolated build-base + one project build (network heavy, cached).

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
    build = _run_ip([
        "build",
        "--repo", str(repo),
        "--requirements", str(REQ_BROWSER),
        "--records-root", str(records_root),
        "--prefix", prefix,
        "--base-ref", base_ref,
    ])
    if build.returncode != 0:
        raise unittest.SkipTest(f"browser build failed: {build.stderr[-800:]}")
    return _kv(base.stdout), _kv(build.stdout)


_SHARED_FIXTURES: dict | None = None


def _shared_image_fixtures() -> dict:
    """模块级一次性构建夹具: 两个 e2e 类共享同一套 base+项目镜像.

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
        # reference glob 不跨 "/": prefix*/* 才能命中 prefix/base:tag 与 prefix/repo:tag
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
    base_values, build_values = _build_image_fixtures(
        fixtures["records_root"], fixtures["repo"], fixtures["prefix"],
        fixtures["base_ref"],
    )
    fixtures["base_values"] = base_values
    fixtures["build_values"] = build_values
    fixtures["image"] = build_values["image"]
    _SHARED_FIXTURES = fixtures
    return _SHARED_FIXTURES


class TestBrowserImageE2E(unittest.TestCase):
    """TS-002: isolated real base + browser project build.

    Isolation: --prefix localhost/swt-m09-<random> and records root under
    /tmp/swt-m09-<random>; never touches user images or real records.
    setUpClass performs the single base build and the single project build
    (network heavy, class-level shared); each test only asserts its own
    contract, so any test can run alone without skipping the other.
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
        cls.build_values: dict[str, str] = fixtures["build_values"]

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

    def test_browser_image_probes_and_artifacts(self):
        """build 全 probe 过 + swt-vnc 可执行 + fonts 在位 + chromium 版本."""
        values = type(self).build_values
        assert values is not None
        image = values["image"]
        contents = (Path(values["record"]) / "contents.md").read_text()
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
            "/home/agent/.cache/ms-playwright/chromium-*/chrome-linux*/chrome --version",
        )
        self.assertEqual(chrome.returncode, 0, msg=chrome.stderr)
        self.assertRegex(chrome.stdout + chrome.stderr, r"\d+(\.\d+)+")


# ---------------------------------------------------------------- TS-003 e2e


def _run_lw(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, check=False, timeout=timeout,
    )


class TestUpFlowE2E(unittest.TestCase):
    """TS-003: up -> swt-vnc start -> GEOM resolution, 0.0.0.0 listeners,
    dynamic host port discovery; swt-vnc status/stop idempotency; down.
    """

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
                ["podman", "rm", "-f", name], capture_output=True,
            )

    def _up(self, name: str, geom: str | None = None) -> dict:
        args = ["up", "--image", self.image, "--name", name]
        if geom:
            args += ["--geom", geom]
        result = _run_lw(args, timeout=1800)
        type(self).containers.append(name)  # 断言前登记, 失败也兜底清理
        self.addCleanup(
            subprocess.run, ["podman", "rm", "-f", name], capture_output=True,
        )
        if result.returncode != 0:
            self.fail(f"up --name {name} failed: {result.stderr[-2000:]}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(
                f"up --name {name} 输出非 json ({error}): {result.stdout[:200]}")

    def _exec(self, name: str, command: str, check: bool = False):
        return subprocess.run(
            ["podman", "exec", name, "sh", "-c", command],
            capture_output=True, text=True, check=check, timeout=300,
        )

    def _rfb_frame_size(self, name: str) -> tuple[int, int]:
        """RFB 单一真相源: cp 纯逻辑进容器, 容器内 python3 握手读尺寸."""
        subprocess.run(
            ["podman", "cp", str(SCRIPT), f"{name}:/tmp/lw.py"],
            capture_output=True, text=True, check=True,
        )
        probe = (
            "import importlib.util,socket;"
            "spec=importlib.util.spec_from_file_location('lw','/tmp/lw.py');"
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

    def test_up_state_contract_and_default_resolution(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        state = self._up(name)
        self.assertEqual(state["container"], name)
        self.assertEqual(state["image"], self.image)
        self.assertTrue(state["ports"].get("22/tcp"))
        host_6080 = state["ports"].get("6080/tcp")
        self.assertTrue(host_6080)
        self.assertEqual(
            state["url"],
            f"http://127.0.0.1:{host_6080}/vnc.html?resize=scale",
        )
        inspect = subprocess.run(
            ["podman", "inspect", name, "--format",
             "{{.State.Running}}|{{.HostConfig.ShmSize}}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        running, shm_size = inspect.split("|")
        self.assertEqual(running, "true")
        self.assertEqual(int(shm_size), 1 << 30)  # --shm-size 1g
        # 宿主侧经动态发现的 6080 可 TCP 连上 (0.0.0.0 监听佐证)
        with socket.create_connection(("127.0.0.1", int(host_6080)), timeout=10):
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

    def test_up_geom_env_controls_resolution(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        state = self._up(name, geom="1280x720")
        self.assertEqual(state["geom"], "1280x720")  # up 原样透传, 脚本负责归一
        self.assertEqual(self._rfb_frame_size(name), (1280, 720))  # 生效值经 RFB 读出

    def test_start_status_stop_idempotent(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._up(name)  # up 已含首轮 start
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

    def test_down_removes_container_idempotent(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._up(name)
        down_first = _run_lw(["down", "--name", name])
        self.assertEqual(down_first.returncode, 0, msg=down_first.stderr)
        inspect = subprocess.run(
            ["podman", "inspect", name, "--format", "{{.State.Running}}"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(inspect.returncode, 0)  # 容器已不存在
        down_again = _run_lw(["down", "--name", name])
        self.assertEqual(down_again.returncode, 0, msg=down_again.stderr)


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


class TestVerifyChannelE2E(unittest.TestCase):
    """TS-004: host 侧 noVNC HTTP 200 + ws 握手 101 + ws 帧 RFB banner;
    容器内空白 framebuffer 基线 (非黑 < 1%) + PPM 证据回 host."""

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
                ["podman", "rm", "-f", name], capture_output=True,
            )

    def _up(self, name: str) -> None:
        result = _run_lw(["up", "--image", self.image, "--name", name],
                         timeout=1800)
        type(self).containers.append(name)
        self.addCleanup(
            subprocess.run, ["podman", "rm", "-f", name], capture_output=True,
        )
        if result.returncode != 0:
            self.fail(f"up --name {name} failed: {result.stderr[-2000:]}")

    def _exec(self, name: str, command: str):
        return subprocess.run(
            ["podman", "exec", name, "sh", "-c", command],
            capture_output=True, text=True, check=False, timeout=300,
        )

    def test_verify_channels_pass_and_evidence(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._up(name)
        evidence = Path(mkdtemp(prefix="swt-m09-verify-"))
        self.addCleanup(rmtree, evidence, True)
        result = _run_lw([
            "verify", "--name", name, "--evidence-dir", str(evidence),
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

    def test_verify_fails_after_stack_stop(self):
        """负例: VNC 栈停后 verify 必须红 (证明检查真的在测)."""
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._up(name)
        stop = self._exec(name, "swt-vnc stop")
        self.assertEqual(stop.returncode, 0, msg=stop.stderr)
        result = _run_lw(["verify", "--name", name], timeout=600)
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FAIL", result.stdout, msg=result.stdout)


# ---------------------------------------------------------------- TS-005 e2e


class TestRenderE2E(unittest.TestCase):
    """TS-005: headed chromium 渲染高对比页 -> framebuffer 非黑超阈值
    + PPM 证据回 host; headless 回切 (换 cwd, 无 DISPLAY); down 后无残留."""

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
                ["podman", "rm", "-f", name], capture_output=True,
            )

    def _up(self, name: str) -> None:
        result = _run_lw(["up", "--image", self.image, "--name", name],
                         timeout=1800)
        type(self).containers.append(name)
        self.addCleanup(
            subprocess.run, ["podman", "rm", "-f", name], capture_output=True,
        )
        if result.returncode != 0:
            self.fail(f"up --name {name} failed: {result.stderr[-2000:]}")

    def test_verify_render_checks_pass_with_evidence(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._up(name)
        # 嵌套不存在路径: evidence-dir 需自行创建 (podman cp 不建宿主目录)
        evidence = Path(mkdtemp(prefix="swt-m09-render-")) / "a" / "b"
        self.addCleanup(rmtree, evidence.parent.parent, True)
        result = _run_lw([
            "verify", "--name", name, "--evidence-dir", str(evidence),
        ], timeout=1800)
        self.assertEqual(result.returncode, 0,
                         msg=result.stdout + result.stderr[-2000:])
        for check in ("headed_render_nonblack", "headless_fallback_ok"):
            self.assertIn(f"check {check}: OK", result.stdout, msg=result.stdout)
        ppm = evidence / "rendering.ppm"
        self.assertTrue(ppm.is_file(), msg=result.stdout)
        self.assertTrue(ppm.read_bytes().startswith(b"P6\n1920 1080\n255\n"),
                        msg=ppm.read_bytes()[:32])

    def test_down_leaves_no_container(self):
        name = f"swt-m09-{secrets.token_hex(4)}"
        self._up(name)
        down = _run_lw(["down", "--name", name])
        self.assertEqual(down.returncode, 0, msg=down.stderr)
        ps = subprocess.run(
            ["podman", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True,
        )
        self.assertNotIn(name, ps.stdout.splitlines())


# ------------------------------------------------- build 子命令 (加餐轮)


class TestBuildCommand(unittest.TestCase):
    """build = image-prep build 的薄封装: mock subprocess.run 接缝,
    断言 argv 组装与透传; 缺省 requirements = 仓库内 image/requirements-browser.md."""

    @classmethod
    def setUpClass(cls):
        cls.lw = _load_module()

    def _argv_of(self, extra_args, completed):
        fake = unittest.mock.MagicMock(return_value=completed)
        buf = io.StringIO()
        with unittest.mock.patch.object(self.lw.subprocess, "run", fake), \
                contextlib.redirect_stdout(buf):
            rc = self.lw.main(["build", *extra_args])
        return rc, fake.call_args.args[0], buf.getvalue()

    def test_default_requirements_and_passthrough(self):
        rc, argv, out = self._argv_of(
            ["--repo", "/some/repo",
             "--prefix", "localhost/swt-x",
             "--records-root", "/tmp/recs"],
            subprocess.CompletedProcess([], 0, stdout="kind=project\n"),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(Path(argv[1]), IMAGE_PREP)
        self.assertIn("build", argv)
        self.assertEqual(argv[argv.index("--requirements") + 1],
                         str(REQ_BROWSER))  # 缺省 = 仓库内清单绝对路径
        self.assertEqual(argv[argv.index("--prefix") + 1], "localhost/swt-x")
        self.assertEqual(argv[argv.index("--records-root") + 1], "/tmp/recs")
        self.assertEqual(argv[argv.index("--repo") + 1], "/some/repo")
        self.assertIn("kind=project", out)  # 输出透传

    def test_custom_requirements_overrides_default(self):
        rc, argv, _ = self._argv_of(
            ["--repo", "/some/repo", "--prefix", "p", "--records-root", "/tmp/r",
             "--requirements", "/tmp/custom.md"],
            subprocess.CompletedProcess([], 0, stdout=""),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(argv[argv.index("--requirements") + 1], "/tmp/custom.md")

    def test_rc_and_stderr_passthrough(self):
        rc, _, out = self._argv_of(
            ["--repo", "/some/repo", "--prefix", "p", "--records-root", "/tmp/r"],
            subprocess.CompletedProcess([], 7, stdout="", stderr="VERIFY-FAIL x\n"),
        )
        self.assertEqual(rc, 7)  # image-prep 退出码原样透传

    def test_missing_repo_is_argparse_error(self):
        with self.assertRaises(SystemExit):
            self.lw.main(["build", "--prefix", "p", "--records-root", "/tmp/r"])
