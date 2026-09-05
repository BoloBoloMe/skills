"""sandbox-worktree M04 端到端测试: rootless netns nft 双模式网络访问控制.

验证命令: uv run pytest tests/test_swt_m04.py
环境依赖: rootless podman + netavark, nft, 本地镜像 localhost/swt-m03:latest.
依赖缺失时失败并打印缺失项, 不静默 skip (与 test_swt_m03 同约定).

机制见 docs/changes/use-sandbox-worktree/milestone-04/MILESTONE-04-findings.md.
关键实测事实 (findings F-M04-01..06):
- 注入通道 = podman unshare nsenter --net=<rootless-netns> nft (无 root).
- rootless netns 随最后一个容器停止而拆毁, 自有表随之消失 → restart 后须重注入.
- 静态 IP (--ip) 跨 stop/start 保持.
- 容器 → host 通道 = pasta map-guest-addr 169.254.1.2, 仅达 host 非 loopback 监听.
- 被过滤的连接特征: timeout (rc 124); 未监听端口是 refused (rc 1); 断言区分二者.
"""
from __future__ import annotations

import random
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/net-firewall.py"
IMAGE = "localhost/swt-m03:latest"
PROBE_TIMEOUT = 4  # 单次容器内连通探测的上限秒数
NETNS_WAIT = 20  # 等 rootless netns 建立的上限秒数

# 容器内探测返回码语义 (bash /dev/tcp + timeout)
TCP_OPEN = 0
TCP_REFUSED = 1
TCP_TIMEOUT = 124


def run(
    command: list[str], input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, capture_output=True, text=True, input=input_text, check=False
    )


def run_script(args: list[str]) -> subprocess.CompletedProcess[str]:
    return run(["uv", "run", "python", str(SCRIPT)] + args)


def missing_dependencies() -> list[str]:
    missing: list[str] = []
    if run(["podman", "info"]).returncode != 0:
        missing.append("rootless podman 不可用")
    if run(["nft", "--version"]).returncode != 0:
        missing.append("nft 不可用")
    if run(["podman", "image", "exists", IMAGE]).returncode != 0:
        missing.append(f"镜像 {IMAGE} 不存在 (先经 M03 流程构建)")
    return missing


class NetFixture:
    """每个测试用例一套: 专用网络 + 静态 IP 容器 + host 监听, 用毕全回收."""

    def __init__(self) -> None:
        self.token = f"swt-m04-test-{random.randint(0x1000, 0xFFFF):x}"
        third_octet = random.randint(2, 254)
        self.subnet = f"10.99.{third_octet}.0/24"
        self.gateway = f"10.99.{third_octet}.1"
        self.container_ip = f"10.99.{third_octet}.5"
        self.network: str | None = None
        self.container: str | None = None
        self.listener: subprocess.Popen[bytes] | None = None
        self.host_port: int | None = None
        self.forbidden_port: int | None = None  # host 无监听端口, 供 TIMEOUT/REFUSED 区分断言

    # ── 搭建 ──
    def up(self) -> None:
        result = run(["podman", "network", "create", "--subnet", self.subnet, self.token])
        assert result.returncode == 0, f"network create 失败: {result.stderr}"
        self.network = self.token
        result = run(
            [
                "podman", "run", "-d", "--name", self.token,
                "--network", self.token, "--ip", self.container_ip,
                IMAGE, "sleep", "infinity",
            ]
        )
        assert result.returncode == 0, f"容器创建失败: {result.stderr}"
        self.container = self.token
        deadline = time.monotonic() + NETNS_WAIT
        while time.monotonic() < deadline:
            if run_script(["show"]).returncode != 2:  # netns 已可达 (show 报 NO-TABLE 也算)
                break
            time.sleep(0.5)
        else:
            raise AssertionError(f"{NETNS_WAIT}s 内 rootless netns 未建立")
        self.start_listener()

    def start_listener(self) -> None:
        for role in ("host", "forbidden"):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            value = sock.getsockname()[1]
            sock.close()
            if role == "host":
                self.host_port = value
            else:
                self.forbidden_port = value
        self.listener = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(self.host_port), "--bind", "0.0.0.0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", self.host_port)) == 0:
                    return
            time.sleep(0.2)
        raise AssertionError("host 监听未就绪")

    # ── 观测 ──
    def container_tcp(self, host: str, port: int) -> int:
        """容器内对 host:port 发起 TCP, 返回 0=open / 1=refused / 124=timeout."""
        assert self.container is not None
        result = run(
            [
                "podman", "exec", self.container, "bash", "-c",
                f'timeout {PROBE_TIMEOUT} bash -c "echo > /dev/tcp/{host}/{port}"'
                " 2>/dev/null",
            ]
        )
        return result.returncode

    def netns_path(self) -> str:
        result = run(["pgrep", "-af", "pasta --config-net"])
        for line in result.stdout.splitlines():
            if "--netns " in line:
                return line.split("--netns ")[1].split()[0]
        raise AssertionError("未发现 pasta --netns 路径 (rootless netns 不在)")

    # ── 拆除 ──
    def down(self) -> None:
        if self.listener is not None:
            self.listener.terminate()
            self.listener.wait(timeout=10)
        if self.container is not None:
            run(["podman", "rm", "-f", self.container])
        if self.network is not None:
            run(["podman", "network", "rm", self.network])


class NetworkModeTestCase(unittest.TestCase):
    fixture: NetFixture

    @classmethod
    def setUpClass(cls) -> None:
        missing = missing_dependencies()
        if missing:
            raise AssertionError("环境依赖缺失: " + "; ".join(missing))
        cls.fixture = NetFixture()
        cls.fixture.up()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.down()

    def test_01_whitelist_default_deny(self) -> None:
        fx = self.fixture
        result = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--allow", "169.254.1.2",
                "--netns", fx.netns_path(),
            ]
        )
        self.assertEqual(result.returncode, 0, f"apply 失败: {result.stderr}")
        self.assertIn("mode=whitelist", result.stdout)

        # 放行条目 (git daemon 通道) 可达
        self.assertEqual(fx.container_tcp("169.254.1.2", fx.host_port), TCP_OPEN)
        # 网关 DNS 放行
        self.assertEqual(fx.container_tcp(fx.gateway, 53), TCP_OPEN)
        # 非放行 IP 的非监听端口被默认拒 → TIMEOUT (不是 REFUSED, 否则说明没经过滤);
        # 过滤为 IP 级: 放行条目 (169.254.1.2) 全端口可达, 默认拒作用在其余 IP
        self.assertEqual(
            fx.container_tcp(fx.gateway, 9999),
            TCP_TIMEOUT,
            "白名单默认拒未生效 (应超时而非拒绝)",
        )
        # 规则集含 IPv6 兜底 DROP
        show = run_script(["show", "--netns", fx.netns_path()])
        self.assertEqual(show.returncode, 0)
        self.assertEqual(show.stdout.count("meta nfproto ipv6 drop"), 2)

    def test_02_restart_loses_rules_then_reinject(self) -> None:
        fx = self.fixture
        run(["podman", "stop", fx.container])
        # 规则丢失不变量: netns 拆毁 (rc 2) 或 netns 幸存仅表灭 (rc 1, 本机另有容器时)
        self.assertIn(
            run_script(["show"]).returncode, (1, 2),
            "容器停止后规则应已不存在",
        )
        run(["podman", "start", fx.container])
        # 静态 IP 保持
        hostname = run(["podman", "exec", fx.container, "hostname", "-I"])
        self.assertIn(fx.container_ip, hostname.stdout, "stop/start 后静态 IP 不保持")
        # 表已随 netns 重建消失
        self.assertEqual(
            run_script(["show", "--netns", fx.netns_path()]).returncode, 1,
            "netns 重建后旧表应不存在",
        )
        # 重注入后过滤恢复
        result = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--allow", "169.254.1.2",
                "--netns", fx.netns_path(),
            ]
        )
        self.assertEqual(result.returncode, 0, f"重注入失败: {result.stderr}")
        self.assertEqual(fx.container_tcp("169.254.1.2", fx.host_port), TCP_OPEN)
        self.assertEqual(
            fx.container_tcp(fx.gateway, 9999),
            TCP_TIMEOUT,
        )

    def test_03_blacklist_default_allow(self) -> None:
        fx = self.fixture
        result = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--deny", "169.254.1.2",
                "--netns", fx.netns_path(),
            ]
        )
        self.assertEqual(result.returncode, 0, f"apply 失败: {result.stderr}")
        self.assertIn("mode=blacklist", result.stdout)
        # 拒绝条目 IP 级全端口不可达 (TIMEOUT, 非 REFUSED)
        self.assertEqual(
            fx.container_tcp("169.254.1.2", fx.host_port), TCP_TIMEOUT,
            "黑名单拒绝条目未生效",
        )
        # 默认放行: 网关 DNS 可达; 网关无监听端口 REFUSED (穿透到 netns 栈, 未被滤)
        self.assertEqual(fx.container_tcp(fx.gateway, 53), TCP_OPEN)
        self.assertEqual(
            fx.container_tcp(fx.gateway, 9999),
            TCP_REFUSED,
            "黑名单默认放行未生效 (应拒绝而非超时)",
        )

    def test_04_clear_idempotent(self) -> None:
        fx = self.fixture
        self.assertEqual(run_script(["clear", "--netns", fx.netns_path()]).returncode, 0)
        self.assertEqual(run_script(["clear", "--netns", fx.netns_path()]).returncode, 0)
        self.assertEqual(run_script(["show", "--netns", fx.netns_path()]).returncode, 1)

    def test_05_foreign_container_conflict(self) -> None:
        # D010 允许多容器共存; 表按容器源地址过滤, 表级替换会清掉异己规则 → 必须拒绝
        fx = self.fixture
        other_ip = f"10.99.{self.fixture.subnet.split('.')[2]}.6"
        other = run(
            [
                "podman", "run", "-d", "--name", fx.token + "-b",
                "--network", fx.token, "--ip", other_ip,
                IMAGE, "sleep", "infinity",
            ]
        )
        self.assertEqual(other.returncode, 0, other.stderr)
        try:
            base = run_script(
                [
                    "apply", "--mode", "whitelist",
                    "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                    "--netns", fx.netns_path(),
                ]
            )
            self.assertEqual(base.returncode, 0, base.stderr)
            conflict = run_script(
                [
                    "apply", "--mode", "whitelist",
                    "--container-ip", other_ip, "--gateway", fx.gateway,
                    "--netns", fx.netns_path(),
                ]
            )
            self.assertEqual(conflict.returncode, 1, "异己容器 saddr 未被拒绝")
            self.assertTrue(conflict.stderr.startswith("APPLY-CONFLICT"), conflict.stderr)
        finally:
            run(["podman", "rm", "-f", fx.token + "-b"])


class ArgumentGuardTestCase(unittest.TestCase):
    """参数与状态守卫, 不依赖存活 netns."""

    def test_hostname_entry_rejected(self) -> None:
        result = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", "10.99.0.5", "--gateway", "10.99.0.1",
                "--allow", "github.com", "--netns", "/nonexistent",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("INVALID-ENTRY"))

    def test_mode_entry_mismatch_rejected(self) -> None:
        result = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", "10.99.0.5", "--gateway", "10.99.0.1",
                "--deny", "1.1.1.1", "--netns", "/nonexistent",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("INVALID-ARGUMENT"))

    def test_unreachable_netns_reported(self) -> None:
        result = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", "10.99.0.5", "--gateway", "10.99.0.1",
                "--netns", "/nonexistent",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("NETNS-UNREACHABLE"))


if __name__ == "__main__":
    unittest.main()
