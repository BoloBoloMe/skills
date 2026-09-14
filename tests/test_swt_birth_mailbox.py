"""ISSUE-06: swt.py birth 信箱接线单元测试.

接缝 (公开函数, 不测内部实现):
- probe_base_server: 状态文件免扫描 (D002(3)), 缺席扫区间 __identity__ 兜底 (D002(2)).
- claim_container_key: 经 admin 口申领容器 key (D006 作用域声明).
- wire_container_mailbox: 探测→申领→注入 env→登记段, 失败告警跳过不阻断 birth.
- create_and_start_container: mailbox env 经 podman -e 烘入 (注入点).
- apply_network: whitelist 模式 auto-allow 含 gateway/32 (UD-04 守卫, 防未来回归).

假服务 = 本机回环 http.server; podman 边界用 scripted fake run. 不依赖真 podman.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"

ADMIN_TOKEN = "test-admin-token"
CONTAINER_KEY = "sk-testcontainerkey0123456789"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class _LoopbackServer:
    """回环假服务基座: handler 类由子类给, 起后台线程, 用完 close."""

    handler: type[BaseHTTPRequestHandler] = NotImplemented

    def __init__(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self.handler)
        self.httpd.daemon_threads = True
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()


def _quiet_json(handler: BaseHTTPRequestHandler, code: int, obj: dict) -> None:
    body = json.dumps(obj).encode()
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class _IdentityHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/__identity__":
            _quiet_json(self, 200, {"service": "swt-base-server", "version": "test",
                                    "capabilities": ["llm-relay", "mailbox"]})
        else:
            _quiet_json(self, 404, {"error": "not found"})


class _AlienHandler(BaseHTTPRequestHandler):
    """同名端口上的异构服务: __identity__ 应答但不是 swt-base-server."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        _quiet_json(self, 200, {"service": "something-else"})


class _AdminHandler(BaseHTTPRequestHandler):
    """假 admin: 记录 container-keys 请求, token 错回 401, 可配置申领失败."""

    fail_status: int | None = None
    received: list[dict] = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.headers.get("X-Admin-Token", "") != ADMIN_TOKEN:
            return _quiet_json(self, 401, {"error": "admin token 无效"})
        if self.path != "/admin/container-keys":
            return _quiet_json(self, 404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        type(self).received.append(body)
        if type(self).fail_status is not None:
            return _quiet_json(self, type(self).fail_status, {"error": "forced failure"})
        _quiet_json(self, 200, {"key": CONTAINER_KEY, "container": body.get("container"),
                                "allow_types": body.get("allow_types"),
                                "allow_targets": body.get("allow_targets")})


class _IdentityServer(_LoopbackServer):
    handler = _IdentityHandler


class _AlienServer(_LoopbackServer):
    handler = _AlienHandler


class _AdminServer(_LoopbackServer):
    handler = _AdminHandler

    def __init__(self):
        _AdminHandler.fail_status = None
        _AdminHandler.received = []
        super().__init__()


def _write_state(directory: Path, **fields) -> Path:
    path = directory / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"service": "swt-base-server", "version": "test",
                                "started_at": "2026-09-14", **fields}), encoding="utf-8")
    return path


class SwtCase(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-birth-mailbox-"))
        self.addCleanup(rmtree, self.root, True)
        self.servers: list[_LoopbackServer] = []

    def _spawn(self, cls):
        server = cls()
        self.servers.append(server)
        self.addCleanup(server.close)
        return server


class TestProbeBaseServer(SwtCase):
    def test_state_file_hit_no_scan(self):
        identity = self._spawn(_IdentityServer)
        state = _write_state(self.root, port=identity.port,
                             admin_port=38416, admin_token=ADMIN_TOKEN)
        # ports=() 证明状态文件命中时零扫描 (D002(3))
        found = self.m.probe_base_server(state, ports=())
        self.assertEqual(found, {"port": identity.port,
                                 "admin_port": 38416, "admin_token": ADMIN_TOKEN})

    def test_state_file_stale_falls_back_to_scan(self):
        stale = self._spawn(_IdentityServer)
        state = _write_state(self.root, port=stale.port,
                             admin_port=38416, admin_token=ADMIN_TOKEN)
        stale.close()  # 状态文件记录的端口已死 (崩溃残留)
        live = self._spawn(_IdentityServer)
        found = self.m.probe_base_server(state, ports=(live.port,))
        # 扫描命中但拿不到 admin 凭证: admin 字段 None, 失配文件的凭证不可信
        self.assertEqual(found, {"port": live.port, "admin_port": None,
                                 "admin_token": None})

    def test_missing_state_file_scan_hit(self):
        live = self._spawn(_IdentityServer)
        found = self.m.probe_base_server(self.root / "absent.json", ports=(live.port,))
        self.assertEqual(found, {"port": live.port, "admin_port": None,
                                 "admin_token": None})

    def test_malformed_state_file_treated_absent(self):
        bad = self.root / "state.json"
        bad.write_text("{not json", encoding="utf-8")
        live = self._spawn(_IdentityServer)
        found = self.m.probe_base_server(bad, ports=(live.port,))
        self.assertEqual(found["port"], live.port)

    def test_alien_service_not_accepted(self):
        alien = self._spawn(_AlienServer)
        found = self.m.probe_base_server(self.root / "absent.json",
                                         ports=(alien.port,))
        self.assertIsNone(found)

    def test_nothing_anywhere_returns_none(self):
        found = self.m.probe_base_server(self.root / "absent.json", ports=())
        self.assertIsNone(found)


class TestClaimContainerKey(SwtCase):
    def test_posts_scope_and_returns_key(self):
        admin = self._spawn(_AdminServer)
        key = self.m.claim_container_key(admin.port, ADMIN_TOKEN, "swt-demo")
        self.assertEqual(key, CONTAINER_KEY)
        self.assertEqual(len(_AdminHandler.received), 1)
        body = _AdminHandler.received[0]
        self.assertEqual(body["container"], "swt-demo")
        # D006 作用域: 全 4 类型 (exec 由服务端指令集兜底降级, UD-03), 缺省路由覆盖
        self.assertEqual(sorted(body["allow_types"]),
                         ["exec", "notify", "open_url", "request"])
        self.assertEqual(body["allow_targets"], ["*"])

    def test_rejected_raises(self):
        admin = self._spawn(_AdminServer)
        with self.assertRaises(self.m.MailboxWireError):
            self.m.claim_container_key(admin.port, "wrong-token", "swt-demo")

    def test_unreachable_raises(self):
        dead = self._spawn(_AdminServer)
        port = dead.port
        dead.close()
        with self.assertRaises(self.m.MailboxWireError):
            self.m.claim_container_key(port, ADMIN_TOKEN, "swt-demo")


class TestWireContainerMailbox(SwtCase):
    def test_connected_full_path(self):
        identity = self._spawn(_IdentityServer)
        admin = self._spawn(_AdminServer)
        state = _write_state(self.root, port=identity.port,
                             admin_port=admin.port, admin_token=ADMIN_TOKEN)
        env: dict[str, str] = {}
        record = self.m.wire_container_mailbox(env, "swt-demo", state_path=state)
        # 注入: D002(5) 容器内地址恒 host.containers.internal + 探测端口
        self.assertEqual(env["SWT_BASE_URL"],
                         f"http://host.containers.internal:{identity.port}")
        self.assertEqual(env["SWT_MAILBOX_KEY"], CONTAINER_KEY)
        self.assertEqual(env["SWT_CONTAINER_NAME"], "swt-demo")
        # 登记: status/key 前缀/容器名/服务地址; 完整 key 不落登记
        self.assertEqual(record["status"], "connected")
        self.assertEqual(record["container"], "swt-demo")
        self.assertEqual(record["base_url"], env["SWT_BASE_URL"])
        self.assertEqual(record["key_prefix"], CONTAINER_KEY[:8])
        self.assertNotIn(CONTAINER_KEY, json.dumps(record))
        self.assertEqual(_AdminHandler.received[0]["container"], "swt-demo")

    def test_no_service_skips_without_touching_env(self):
        env = {"KEEP": "1"}
        record = self.m.wire_container_mailbox(
            env, "swt-demo", state_path=self.root / "absent.json")
        self.assertEqual(record["status"], "skipped")
        self.assertIn("reason", record)
        self.assertEqual(record["container"], "swt-demo")
        self.assertEqual(env, {"KEEP": "1"})

    def test_scan_only_without_admin_creds_skips(self):
        live = self._spawn(_IdentityServer)
        # 状态文件缺席, 只扫描命中: 服务在线但申领不了 key
        env: dict[str, str] = {}
        record = self.m.wire_container_mailbox(
            env, "swt-demo", state_path=self.root / "absent.json",
            ports=(live.port,))
        self.assertEqual(record["status"], "skipped")
        self.assertIn("admin", record["reason"])
        self.assertNotIn("SWT_MAILBOX_KEY", env)

    def test_claim_failure_skips(self):
        identity = self._spawn(_IdentityServer)
        admin = self._spawn(_AdminServer)
        _AdminHandler.fail_status = 500
        state = _write_state(self.root, port=identity.port,
                             admin_port=admin.port, admin_token=ADMIN_TOKEN)
        env: dict[str, str] = {}
        record = self.m.wire_container_mailbox(env, "swt-demo", state_path=state)
        self.assertEqual(record["status"], "skipped")
        self.assertIn("申领", record["reason"])
        self.assertEqual(env, {})


class _FakeRun:
    """scripted podman 边界: 前两次 inspect 是存在性检查 (调用方只看 returncode),
    之后的 inspect 回运行中容器 JSON; exists=True 模拟重入 (容器已在, 不走 create)."""

    def __init__(self, container_name: str, exists: bool = False):
        self.container_name = container_name
        self.exists = exists
        self.calls: list[list[str]] = []
        self.create_command: list[str] | None = None
        self._existence_checks = 0

    def __call__(self, command, *, cwd=None, timeout=None):
        self.calls.append(command)
        head = " ".join(str(part) for part in command[:2])
        if head == "podman inspect" and self._existence_checks < 2:
            self._existence_checks += 1
            code = 0 if self.exists else 1
            stdout = "" if code == 0 else "no such container"
            return subprocess.CompletedProcess(command, code, "", stdout)
        if head == "podman create":
            self.create_command = [str(part) for part in command]
            return subprocess.CompletedProcess(command, 0, "created\n", "")
        if head == "podman inspect":
            detail = [{
                "Id": "fakepodmanid123",
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}, "IPAddress": "10.88.0.10"},
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(detail), "")
        if command[:3] == ["podman", "port", self.container_name]:
            if command[3] == "22":
                return subprocess.CompletedProcess(command, 0, "0.0.0.0:49153\n", "")
            return subprocess.CompletedProcess(command, 1, "", "no mapping")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestBirthWiringSeam(SwtCase):
    """birth 执行的接线序列原样重放 (wire → create → 登记): env 流进 podman -e,
    mailbox 段落 runtime, 完整 key 不出现在 runtime 文件."""

    def _run_seam(self, state_path: Path, *, exists: bool = False,
                  runtime: dict | None = None):
        import argparse
        m = self.m
        records_root = self.root / "records"
        identity = "testid"
        runtime_file = records_root / "runtime" / f"{identity}.json"
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        if runtime is None:
            runtime = {"schema": m.SCHEMA, "containers": [], "stage": "daemon"}
        image = {"ref": "localhost/test:latest", "digest": "sha256:fake"}
        args = argparse.Namespace(name="swt-demo", hostname="swt-demo")
        fake = _FakeRun("swt-demo", exists=exists)
        original_run = m.run
        original_wayland = m.host_wayland_socket
        m.run = fake
        m.host_wayland_socket = lambda: None
        try:
            # 与 birth 主流程逐行同构 (test_birth_source_calls_wire_before_create 绑定二者)
            env_map: dict[str, str] = {}
            args.name = args.name or m.container_default_name("feat-x")
            mailbox_record = (
                None if m.container_exists(args.name)
                else m.wire_container_mailbox(env_map, args.name, state_path=state_path)
            )
            container = m.create_and_start_container(
                args, repo, image, "feat-x", runtime, runtime_file, env_map,
                records_root, identity)
            if mailbox_record is not None:
                container["record"]["mailbox"] = mailbox_record
                m.upsert_container_record(runtime, container["record"], runtime_file)
            elif "mailbox" not in container["record"]:
                container["record"]["mailbox"] = {
                    "status": "skipped", "container": args.name,
                    "reason": "container-exists: 重入不重复申领 key (env 不重烘)",
                }
                m.upsert_container_record(runtime, container["record"], runtime_file)
        finally:
            m.run = original_run
            m.host_wayland_socket = original_wayland
        return fake, runtime_file

    def _create_env(self, fake: _FakeRun) -> dict[str, str]:
        self.assertIsNotNone(fake.create_command)
        pairs = {}
        command = fake.create_command
        for index, part in enumerate(command):
            if part == "-e":
                name, _, value = command[index + 1].partition("=")
                pairs[name] = value
        return pairs

    def test_connected_env_baked_and_recorded(self):
        identity = self._spawn(_IdentityServer)
        admin = self._spawn(_AdminServer)
        state = _write_state(self.root / "state", port=identity.port,
                             admin_port=admin.port, admin_token=ADMIN_TOKEN)
        fake, runtime_file = self._run_seam(state)
        env = self._create_env(fake)
        self.assertEqual(env["SWT_MAILBOX_KEY"], CONTAINER_KEY)
        self.assertEqual(env["SWT_BASE_URL"],
                         f"http://host.containers.internal:{identity.port}")
        self.assertEqual(env["SWT_CONTAINER_NAME"], "swt-demo")
        # 名单源 (评审修复 2): wire 申领名与 create 采用名一致
        name_at = fake.create_command.index("--name")
        self.assertEqual(fake.create_command[name_at + 1], "swt-demo")
        self.assertEqual(_AdminHandler.received[0]["container"], "swt-demo")
        on_disk = json.loads(runtime_file.read_text(encoding="utf-8"))
        mailbox = on_disk["containers"][0]["mailbox"]
        self.assertEqual(mailbox["status"], "connected")
        self.assertEqual(mailbox["key_prefix"], CONTAINER_KEY[:8])
        # 完整 key 不落 runtime 明文
        self.assertNotIn(CONTAINER_KEY, runtime_file.read_text(encoding="utf-8"))

    def test_reentry_skips_wire_and_preserves_record(self):
        """评审修复 1: 容器已存在 (重入, create 走 refresh 早退, env 不重烘)
        → 零新 key, 不登记 connected, 既有 mailbox 记录原样保留."""
        identity = self._spawn(_IdentityServer)
        admin = self._spawn(_AdminServer)
        state = _write_state(self.root / "state", port=identity.port,
                             admin_port=admin.port, admin_token=ADMIN_TOKEN)
        existing_mailbox = {
            "status": "connected", "container": "swt-demo",
            "base_url": "http://host.containers.internal:38417",
            "key_prefix": "sk-old00",
        }
        runtime = {"schema": self.m.SCHEMA, "stage": "daemon",
                   "containers": [{"name": "swt-demo", "branch": "feat-x",
                                   "mailbox": existing_mailbox}]}
        fake, runtime_file = self._run_seam(state, exists=True, runtime=runtime)
        self.assertEqual(_AdminHandler.received, [])      # 未申领新 key
        self.assertIsNone(fake.create_command)            # 未重建容器
        on_disk = json.loads(runtime_file.read_text(encoding="utf-8"))
        # 既有 mailbox 登记不被覆盖
        self.assertEqual(on_disk["containers"][0]["mailbox"], existing_mailbox)

    def test_reentry_legacy_record_gets_skip_note(self):
        """重入且老记录无 mailbox 段 (ISSUE-06 前的 runtime): 补 skipped 说明, 不申领."""
        runtime = {"schema": self.m.SCHEMA, "stage": "daemon",
                   "containers": [{"name": "swt-demo", "branch": "feat-x"}]}
        fake, runtime_file = self._run_seam(self.root / "absent.json",
                                            exists=True, runtime=runtime)
        self.assertIsNone(fake.create_command)
        on_disk = json.loads(runtime_file.read_text(encoding="utf-8"))
        mailbox = on_disk["containers"][0]["mailbox"]
        self.assertEqual(mailbox["status"], "skipped")
        self.assertIn("container-exists", mailbox["reason"])

    def test_no_service_skips_and_create_proceeds(self):
        fake, runtime_file = self._run_seam(self.root / "absent.json")
        env = self._create_env(fake)
        self.assertNotIn("SWT_MAILBOX_KEY", env)
        on_disk = json.loads(runtime_file.read_text(encoding="utf-8"))
        mailbox = on_disk["containers"][0]["mailbox"]
        self.assertEqual(mailbox["status"], "skipped")
        self.assertIn("reason", mailbox)

    def test_birth_source_calls_wire_before_create(self):
        """birth 主流程接缝守卫: 接线在 env 装载之后、容器创建之前."""
        source = SCRIPT.read_text(encoding="utf-8")
        birth_start = source.index("def birth(")
        segment = source[birth_start:]
        load_at = segment.index("env_map = load_inherited_env(")
        wire_at = segment.index("wire_container_mailbox(")
        create_at = segment.index("container = create_and_start_container(")
        self.assertLess(load_at, wire_at)
        self.assertLess(wire_at, create_at)
        # 评审修复 1: 重入判定 (container_exists) 在 wire 之前
        exists_at = segment.index("container_exists(")
        self.assertLess(load_at, exists_at)
        self.assertLess(exists_at, wire_at)
        # 登记紧随创建
        self.assertIn('container["record"]["mailbox"]', segment)


class TestApplyNetworkAutoAllow(SwtCase):
    """UD-04 守卫: whitelist 模式 auto-allow 恒含 gateway/32 (防未来回归)."""

    def _apply(self, plan):
        captured: list[list[str]] = []

        def fake_run(command, *, cwd=None, timeout=None):
            captured.append([str(part) for part in command])
            return subprocess.CompletedProcess(command, 0, "", "")

        original = self.m.run
        self.m.run = fake_run
        try:
            result = self.m.apply_network(plan)
        finally:
            self.m.run = original
        return captured[0], result

    @staticmethod
    def _allow_entries(command: list[str]) -> list[str]:
        return [command[i + 1] for i, part in enumerate(command) if part == "--allow"]

    def test_whitelist_auto_allows_gateway(self):
        plan = self.m.NetworkPlan("whitelist", (), (), "169.254.1.2", "10.88.0.10",
                                  None, "10.88.0.1")
        command, result = self._apply(plan)
        entries = self._allow_entries(command)
        self.assertIn("169.254.1.2/32", entries)
        self.assertIn("169.254.1.2", result["auto-allow"])

    def test_whitelist_auto_allows_route_gateway_and_container_ip(self):
        plan = self.m.NetworkPlan("whitelist", (), (), "169.254.1.2", "10.88.0.10",
                                  None, "10.88.0.1")
        command, result = self._apply(plan)
        entries = self._allow_entries(command)
        self.assertIn("10.88.0.1/32", entries)
        self.assertIn("10.88.0.10/32", entries)
        self.assertEqual(result["auto-allow"],
                         ["169.254.1.2", "10.88.0.1", "10.88.0.10"])

    def test_blacklist_never_auto_allows(self):
        plan = self.m.NetworkPlan("blacklist", (), ("1.2.3.4/32",),
                                  "169.254.1.2", "10.88.0.10", None, None)
        command, result = self._apply(plan)
        self.assertEqual(self._allow_entries(command), [])
        self.assertEqual(result["auto-allow"], [])
        self.assertIn("--deny", command)


if __name__ == "__main__":
    unittest.main()
