"""sandbox-worktree M04 端到端测试: rootless netns nft 双模式网络访问控制.

验证命令: uv run pytest tests/test_swt_m04.py
环境依赖: rootless podman + netavark, nft, 本地镜像 localhost/swt-m03:latest
(缺席时回落本机最新 localhost/sandbox-worktree/base:* — m04 只需要 bash/python3
与网络栈, 镜像命名随里程碑演进不应让防火墙回归探针失联).
依赖缺失时失败并打印缺失项, 不静默 skip (与 test_swt_m03 同约定).

机制见 docs/changes/use-sandbox-worktree/milestone-04/MILESTONE-04-findings.md.
关键实测事实 (findings F-M04-01..06):
- 注入通道 = podman unshare nsenter --net=<rootless-netns> nft (无 root).
- rootless netns 随最后一个容器停止而拆毁, 自有表随之消失 → restart 后须重注入.
- 静态 IP (--ip) 跨 stop/start 保持.
- 容器 → host 通道 = pasta map-guest-addr 169.254.1.2, 仅达 host 非 loopback 监听.
- 被过滤的连接特征: timeout (rc 124); 未监听端口是 refused (rc 1); 断言区分二者.
- 过滤链 = forward/input/output 三链镜像 (2026-09-14 出站链修复): bridge 夹具
  (NetFixture) 容器流量走 rootless 桥 netns 的 FORWARD/INPUT; pasta 直连拓扑
  (生产, PastaFixture) 容器流量只走自身 netns 的 OUTPUT/INPUT — 后者是
  2026-09-14 swt-firewall-outbound-bypass bug 的漏网面, 专属回归类堵住它.
"""
from __future__ import annotations

import os
import random
import re
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/net-firewall.py"
IMAGE = "localhost/swt-m03:latest"
FALLBACK_IMAGE_PREFIX = "localhost/sandbox-worktree/base"
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


_image_ref: str | None = None


def image_ref() -> str:
    """测试镜像: 首选 M03 固定名, 缺席时回落本机最新 sandbox-worktree base 层."""
    global _image_ref
    if _image_ref is None:
        if run(["podman", "image", "exists", IMAGE]).returncode == 0:
            _image_ref = IMAGE
        else:
            result = run([
                "podman", "images", "--format", "{{.Repository}}:{{.Tag}}",
                "--filter", f"reference={FALLBACK_IMAGE_PREFIX}:*",
                "--sort", "created",
            ])
            candidates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            _image_ref = candidates[0] if candidates else IMAGE
    return _image_ref


def missing_dependencies() -> list[str]:
    missing: list[str] = []
    if run(["podman", "info"]).returncode != 0:
        missing.append("rootless podman 不可用")
    if run(["nft", "--version"]).returncode != 0:
        missing.append("nft 不可用")
    image = image_ref()
    if run(["podman", "image", "exists", image]).returncode != 0:
        missing.append(
            f"镜像 {IMAGE} 不存在且无 {FALLBACK_IMAGE_PREFIX}:* 可回落 (先经 M03/base 流程构建)"
        )
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
                image_ref(), "sleep", "infinity",
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
        # 桥拓扑的 forward/input 过滤发生在共享 rootless netns (桥与 pasta 网关
        # 所在), 与 net-firewall.py default_netns() 同一路径. 不能靠 pgrep 猜:
        # 宿主机同时跑 gitea 等带端口映射的容器时, 它们各有专用 pasta netns,
        # pgrep 首匹配会指错.
        xdg = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        path = f"{xdg}/containers/networks/rootless-netns/rootless-netns"
        if Path(path).exists():
            return path
        raise AssertionError(f"共享 rootless netns 不在: {path}")

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
        # 规则集含 IPv6 兜底 DROP (forward/input/output 三链各一)
        show = run_script(["show", "--netns", fx.netns_path()])
        self.assertEqual(show.returncode, 0)
        self.assertEqual(show.stdout.count("meta nfproto ipv6 drop"), 3)

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
                image_ref(), "sleep", "infinity",
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


class FirewallExtensionTestCase(unittest.TestCase):
    """ISSUE-06 net-firewall 扩展: 每个切片独立使用真实 rootless netns."""

    @classmethod
    def setUpClass(cls) -> None:
        missing = missing_dependencies()
        if missing:
            raise AssertionError("环境依赖缺失: " + "; ".join(missing))

    def setUp(self) -> None:
        self.fx = NetFixture()
        self.fx.up()

    def tearDown(self) -> None:
        self.fx.down()

    def test_f1_conflict_guard_scans_other_chains(self) -> None:
        fx = self.fx
        netns = fx.netns_path()
        other_ip = f"10.99.{fx.subnet.split('.')[2]}.6"
        first = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--deny", "203.0.113.7", "--netns", netns,
            ]
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        # apply 现生成 forward/input/output 三链; 异己规则落 output 链也必须被守卫逮住
        added_rule = run(
            [
                "podman", "unshare", "nsenter", f"--net={netns}", "nft",
                "add", "rule", "inet", "swt", "output",
                "ip", "saddr", other_ip, "ip", "daddr", "203.0.113.8", "drop",
            ]
        )
        self.assertEqual(added_rule.returncode, 0, added_rule.stderr)

        conflict = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--netns", netns,
            ]
        )
        self.assertEqual(conflict.returncode, 1)
        self.assertTrue(conflict.stderr.startswith("APPLY-CONFLICT"), conflict.stderr)

    def test_ts105_apply_without_merge_keeps_conflict_guard(self) -> None:
        fx = self.fx
        netns = fx.netns_path()
        other_ip = f"10.99.{fx.subnet.split('.')[2]}.6"
        first = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--deny", "203.0.113.7", "--netns", netns,
            ]
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        before = run_script(["show", "--netns", netns])
        self.assertEqual(before.returncode, 0, before.stderr)

        added = run(
            [
                "podman", "unshare", "nsenter", f"--net={netns}", "nft",
                "add", "rule", "inet", "swt", "forward",
                "ip", "saddr", other_ip, "ip", "daddr", "203.0.113.8", "drop",
            ]
        )
        self.assertEqual(added.returncode, 0, added.stderr)
        conflict = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", other_ip, "--gateway", fx.gateway,
                "--netns", netns,
            ]
        )
        self.assertEqual(conflict.returncode, 1)
        self.assertTrue(conflict.stderr.startswith("APPLY-CONFLICT"), conflict.stderr)
        after = run_script(["show", "--netns", netns])
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertIn(f"ip saddr {fx.container_ip}", after.stdout)
        self.assertIn(f"ip saddr {other_ip}", after.stdout)

    def test_ts104_apply_merge_preserves_foreign_rules(self) -> None:
        fx = self.fx
        netns = fx.netns_path()
        other_ip = f"10.99.{fx.subnet.split('.')[2]}.6"

        first = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--deny", "203.0.113.7", "--netns", netns,
            ]
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        before_merge = run_script(["show", "--netns", netns])
        self.assertEqual(before_merge.returncode, 0, before_merge.stderr)
        a_rules = [
            line.split(" # handle", 1)[0]
            for line in before_merge.stdout.splitlines()
            if line.strip().startswith(f"ip saddr {fx.container_ip} ")
        ]
        self.assertTrue(a_rules)

        merged = run_script(
            [
                "apply", "--merge", "--mode", "whitelist",
                "--container-ip", other_ip, "--gateway", fx.gateway,
                "--allow", "198.51.100.8", "--netns", netns,
            ]
        )
        self.assertEqual(merged.returncode, 0, merged.stderr)
        merged_show = run_script(["show", "--netns", netns])
        self.assertEqual(merged_show.returncode, 0, merged_show.stderr)
        for rule in a_rules:
            self.assertIn(rule, merged_show.stdout)
        self.assertIn(f"ip saddr {other_ip}", merged_show.stdout)
        b_rules = [
            line.split(" # handle", 1)[0]
            for line in merged_show.stdout.splitlines()
            if line.strip().startswith(f"ip saddr {other_ip} ")
        ]
        self.assertTrue(b_rules)

        updated = run_script(
            [
                "apply", "--merge", "--mode", "blacklist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--deny", "203.0.113.8", "--netns", netns,
            ]
        )
        self.assertEqual(updated.returncode, 0, updated.stderr)
        final_show = run_script(["show", "--netns", netns])
        self.assertEqual(final_show.returncode, 0, final_show.stderr)
        for rule in b_rules:
            self.assertIn(rule, final_show.stdout)
        self.assertIn("203.0.113.8", final_show.stdout)
        self.assertNotIn("203.0.113.7 drop", final_show.stdout)

    def test_ts103_remove_absent_source_or_table_is_idempotent(self) -> None:
        fx = self.fx
        netns = fx.netns_path()
        applied = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--netns", netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)

        absent_source = run_script(
            [
                "remove", "--container-ip", "10.99.0.6",
                "--netns", netns,
            ]
        )
        self.assertEqual(absent_source.returncode, 0, absent_source.stderr)
        self.assertIn("removed=absent", absent_source.stdout)
        self.assertEqual(run_script(["show", "--netns", netns]).returncode, 0)

        removed = run_script(
            ["remove", "--container-ip", fx.container_ip, "--netns", netns]
        )
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertIn("table-removed", removed.stdout)
        absent_table = run_script(
            ["remove", "--container-ip", fx.container_ip, "--netns", netns]
        )
        self.assertEqual(absent_table.returncode, 0, absent_table.stderr)
        self.assertIn("removed=absent", absent_table.stdout)

    def test_ts102_remove_last_container_deletes_table(self) -> None:
        fx = self.fx
        netns = fx.netns_path()
        applied = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                "--deny", "203.0.113.7", "--netns", netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)

        removed = run_script(
            ["remove", "--container-ip", fx.container_ip, "--netns", netns]
        )
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertIn("removed=3", removed.stdout)  # 1 deny 条目 × 3 链
        self.assertIn("table-removed", removed.stdout)
        show = run_script(["show", "--netns", netns])
        self.assertEqual(show.returncode, 1)
        self.assertTrue(show.stderr.startswith("NO-TABLE"), show.stderr)

        absent = run_script(
            ["remove", "--container-ip", fx.container_ip, "--netns", netns]
        )
        self.assertEqual(absent.returncode, 0, absent.stderr)
        self.assertIn("removed=absent", absent.stdout)

    def test_ts101_remove_keeps_sibling_rules(self) -> None:
        fx = self.fx
        other_ip = f"10.99.{fx.subnet.split('.')[2]}.6"
        other_name = fx.token + "-b"
        other = run(
            [
                "podman", "run", "-d", "--name", other_name,
                "--network", fx.token, "--ip", other_ip,
                image_ref(), "sleep", "infinity",
            ]
        )
        self.assertEqual(other.returncode, 0, other.stderr)
        try:
            applied = run_script(
                [
                    "apply", "--mode", "whitelist",
                    "--container-ip", fx.container_ip, "--gateway", fx.gateway,
                    "--netns", fx.netns_path(),
                ]
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            netns = fx.netns_path()
            for chain in ("forward", "input"):
                added = run(
                    [
                        "podman", "unshare", "nsenter", f"--net={netns}", "nft",
                        "add", "rule", "inet", "swt", chain,
                        "ip", "saddr", other_ip, "ip", "daddr", "203.0.113.7",
                        "accept",
                    ]
                )
                self.assertEqual(added.returncode, 0, added.stderr)

            removed = run_script(
                ["remove", "--container-ip", fx.container_ip, "--netns", netns]
            )
            self.assertEqual(removed.returncode, 0, removed.stderr)
            self.assertIn("removed=9", removed.stdout)  # (2 DNS + 1 drop) × 3 链

            show = run_script(["show", "--netns", netns])
            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertNotIn(f"ip saddr {fx.container_ip}", show.stdout)
            self.assertEqual(show.stdout.count(f"ip saddr {other_ip}"), 2)
        finally:
            run(["podman", "rm", "-f", other_name])


def parse_chain_blocks(text: str) -> dict[str, str]:
    """nft list table 输出按 chain 名切块 (测试断言用的小解析器)."""
    blocks: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r"^\s*chain\s+(\S+)\s+\{", line)
        if m:
            current = m.group(1)
            blocks[current] = ""
        elif current is not None:
            if line.strip() == "}":
                current = None
            else:
                blocks[current] += line + "\n"
    return blocks


class PastaFixture:
    """pasta 直连拓扑夹具 (生产同构): 容器自带 netns, 注入点 = SandboxKey.

    bridge 夹具 (NetFixture) 的容器流量走 rootless 桥 netns 的 FORWARD/INPUT,
    永远测不到 output 链 — 2026-09-14 出站链 bug 因此漏网, 本夹具专堵该面.
    """

    def __init__(self) -> None:
        self.token = f"swt-m04-pasta-{random.randint(0x1000, 0xFFFF):x}"
        self.container: str | None = None
        self.netns: str | None = None
        self.listener: subprocess.Popen[bytes] | None = None
        self.host_port: int | None = None

    def up(self) -> None:
        result = run(
            [
                "podman", "run", "-d", "--name", self.token,
                "--network", "pasta", image_ref(), "sleep", "infinity",
            ]
        )
        assert result.returncode == 0, f"pasta 容器创建失败: {result.stderr}"
        self.container = self.token
        inspected = run(
            ["podman", "inspect", "--format",
             "{{.NetworkSettings.SandboxKey}}", self.token]
        )
        self.netns = inspected.stdout.strip()
        assert self.netns, "pasta 容器没有 SandboxKey"
        deadline = time.monotonic() + NETNS_WAIT
        while time.monotonic() < deadline:
            # netns 可达即可 (show 报 NO-TABLE 也算)
            if run_script(["show", "--netns", self.netns]).returncode != 2:
                break
            time.sleep(0.5)
        else:
            raise AssertionError(f"{NETNS_WAIT}s 内 pasta netns 不可达")
        self.start_listener()

    def container_ip(self) -> str:
        result = run(
            [
                "podman", "unshare", "nsenter", f"--net={self.netns}",
                "ip", "-o", "-4", "addr", "show",
            ]
        )
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 4 and fields[1] != "lo":
                return fields[3].split("/", 1)[0]
        raise AssertionError("pasta 容器没有 IPv4 地址")

    def container_gateway(self) -> str:
        result = run(
            ["podman", "exec", self.container, "getent", "hosts",
             "host.containers.internal"]
        )
        match = re.search(r"(?m)^([0-9.]+)\s+", result.stdout)
        assert match, "容器内解析不到 host.containers.internal"
        return match.group(1)

    def start_listener(self) -> None:
        sock = socket.socket()
        sock.bind(("0.0.0.0", 0))
        self.host_port = sock.getsockname()[1]
        sock.close()
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

    def down(self) -> None:
        if self.listener is not None:
            self.listener.terminate()
            self.listener.wait(timeout=10)
        if self.container is not None:
            run(["podman", "rm", "-f", self.container])
        # netns 随容器消失, 无需单独清理


class PastaOutboundTestCase(unittest.TestCase):
    """2026-09-14 swt-firewall-outbound-bypass 回归: whitelist 出站默认拒必须在
    pasta 直连拓扑 (生产) 成立 — 旧实现缺 output 链, 本类的 A/B 探针 (同一目的
    地, 仅规则集有无放行条目之差) 在旧代码下必失败, 是该 bug 的专属性检验.
    """

    @classmethod
    def setUpClass(cls) -> None:
        missing = missing_dependencies()
        if missing:
            raise AssertionError("环境依赖缺失: " + "; ".join(missing))
        cls.fx = PastaFixture()
        cls.fx.up()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fx.down()

    def test_01_outbound_default_deny_ab(self) -> None:
        fx = self.fx
        ip = fx.container_ip()
        gateway = fx.container_gateway()
        applied = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", ip, "--gateway", gateway,
                "--allow", gateway, "--netns", fx.netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        # 阳性: 放行条目出站可达 (经 output 链 accept)
        self.assertEqual(fx.container_tcp(gateway, fx.host_port), TCP_OPEN)
        # 阴性 (A/B): 同一目的地, 仅去掉放行条目 → 容器主动出站被 output 链默认拒
        stripped = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", ip, "--gateway", gateway, "--netns", fx.netns,
            ]
        )
        self.assertEqual(stripped.returncode, 0, stripped.stderr)
        self.assertEqual(
            fx.container_tcp(gateway, fx.host_port),
            TCP_TIMEOUT,
            "whitelist 出站默认拒未生效 (pasta 拓扑 output 链缺失 = 2026-09-14 bug 复现)",
        )

    def test_02_loopback_git_bridge_unaffected(self) -> None:
        # 容器内回环 (git 桥 127.0.0.1:9418 同形) 不得被 saddr drop 误伤
        fx = self.fx
        applied = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", fx.container_ip(), "--gateway", fx.container_gateway(),
                "--netns", fx.netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        started = run(
            ["podman", "exec", "-d", fx.container,
             "python3", "-m", "http.server", "9419", "--bind", "127.0.0.1"]
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        # 监听就绪轮询: 未 bind 完的连接是瞬时 REFUSED (重试即过), 被 saddr drop
        # 误伤则是耗满超时的 TIMEOUT — 轮询通不过即回归, 不掩盖
        for _ in range(8):
            if fx.container_tcp("127.0.0.1", 9419) == TCP_OPEN:
                break
            time.sleep(0.3)
        else:
            self.fail("容器内回环监听未就绪或被 saddr drop 误伤 (2026-09-14 回归)")

    def test_03_dns_rules_in_all_chains(self) -> None:
        # --dns 条目 (resolv.conf 对齐的真实解析器) 在三链各落 udp+tcp 两条, 逐链结构断言
        fx = self.fx
        applied = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", fx.container_ip(), "--gateway", fx.container_gateway(),
                "--dns", "192.0.2.53", "--netns", fx.netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        show = run_script(["show", "--netns", fx.netns])
        self.assertEqual(show.returncode, 0)
        chains = parse_chain_blocks(show.stdout)
        self.assertEqual(sorted(chains), ["forward", "input", "output"])
        for name, block in chains.items():
            self.assertEqual(block.count("ip daddr 192.0.2.53 udp dport 53 accept"), 1, name)
            self.assertEqual(block.count("ip daddr 192.0.2.53 tcp dport 53 accept"), 1, name)
            self.assertIn("meta nfproto ipv6 drop", block, name)
            self.assertIn("ip saddr", block, name)

    def test_04_blacklist_output_deny(self) -> None:
        # 冷审建议 4: pasta 拓扑 blacklist 的 output deny 也要有真出站对照
        fx = self.fx
        applied = run_script(
            [
                "apply", "--mode", "blacklist",
                "--container-ip", fx.container_ip(), "--gateway", fx.container_gateway(),
                "--deny", fx.container_gateway(), "--netns", fx.netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        # deny 条目出站被 output 链拦 (TIMEOUT)
        self.assertEqual(fx.container_tcp(fx.container_gateway(), fx.host_port), TCP_TIMEOUT)
        # 默认放行: 容器内回环不受影响; 连自身 IP 也通 (新连接 policy accept)
        started_loopback = run(
            ["podman", "exec", "-d", fx.container,
             "python3", "-m", "http.server", "9420", "--bind", "127.0.0.1"]
        )
        self.assertEqual(started_loopback.returncode, 0, started_loopback.stderr)
        for _ in range(8):
            if fx.container_tcp("127.0.0.1", 9420) == TCP_OPEN:
                break
            time.sleep(0.3)
        else:
            self.fail("blacklist 下容器内回环被误伤")
        started_self = run(
            ["podman", "exec", "-d", fx.container,
             "python3", "-m", "http.server", "9421", "--bind", "0.0.0.0"]
        )
        self.assertEqual(started_self.returncode, 0, started_self.stderr)
        for _ in range(8):
            if fx.container_tcp(fx.container_ip(), 9421) == TCP_OPEN:
                break
            time.sleep(0.3)
        else:
            self.fail("blacklist 下容器连自身 IP 被误拦 (默认放行未生效)")

    def test_05_stale_flow_cut_on_policy_tighten(self) -> None:
        # 冷审阻塞项 1 回归: whitelist 收紧 (去掉 allow 条目) 后, 既有容器主动连接
        # 不得因 established 继续出站
        fx = self.fx
        ip, gateway = fx.container_ip(), fx.container_gateway()
        applied = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", ip, "--gateway", gateway,
                "--allow", gateway, "--netns", fx.netns,
            ]
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        # 容器内探针: 放行期建连 → 停 12s (host 期间重 apply 去掉放行) → 再发请求
        probe = (
            "import socket,time\n"
            f"s=socket.create_connection(({gateway!r},{int(fx.host_port)}),timeout=5)\n"
            "time.sleep(12)\n"
            "s.settimeout(6)\n"
            "try:\n"
            "    s.sendall(b'GET / HTTP/1.1\\r\\nHost: x\\r\\n\\r\\n')\n"
            "    data=s.recv(100)\n"
            "    verdict='FLOW-ALIVE' if data else 'FLOW-CLOSED'\n"
            "except Exception:\n"
            "    verdict='FLOW-BLOCKED'\n"
            "open('/tmp/swt-stale-probe','w').write(verdict)\n"
        )
        cleaned = run(["podman", "exec", fx.container, "rm", "-f", "/tmp/swt-stale-probe"])
        self.assertEqual(cleaned.returncode, 0, cleaned.stderr)
        launched = run(["podman", "exec", "-d", fx.container, "python3", "-c", probe])
        self.assertEqual(launched.returncode, 0, launched.stderr)
        time.sleep(3)  # 连接在放行期建立
        stripped = run_script(
            [
                "apply", "--mode", "whitelist",
                "--container-ip", ip, "--gateway", gateway, "--netns", fx.netns,
            ]
        )
        self.assertEqual(stripped.returncode, 0, stripped.stderr)
        verdict = ""
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            out = run(["podman", "exec", fx.container, "cat", "/tmp/swt-stale-probe"])
            if out.returncode == 0 and out.stdout.strip():
                verdict = out.stdout.strip()
                break
            time.sleep(1)
        self.assertEqual(
            verdict, "FLOW-BLOCKED",
            "whitelist 收紧后既有容器主动连接仍可出站 (established 泄漏)",
        )


if __name__ == "__main__":
    unittest.main()
