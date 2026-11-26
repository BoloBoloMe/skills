"""模板安全测试. unittest 入口, 不加载 pytest 全机清理 hooks.

全部文件为独立临时目录, 全部 Key 为假的, Podman 全部替换为边界假实现.
真实 HTTP 仅本机模拟网关, 不读取真实凭据/主机 agent 配置, 不创建容器.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workflow/use-sandbox-worktree/scripts"
sys.path.insert(0, str(SCRIPTS))
from agent_config import common, launch, runtime, template

KEY = "fake-client-key-not-real-12345678"
MANAGEMENT = "fake-management-must-not-copy-99"
CID = "a" * 64
IMAGE_ID = "sha256:" + "a" * 64


def load_script(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TemporaryCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="swt-agent-isolated-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.key_file = self.root / "keys.json"
        common.safe_write(self.key_file, common.pretty({"client_api_key": KEY, "management_key": MANAGEMENT}))
        self.bundle = copy.deepcopy(template.load("cliproxyapi"))
        self.bundle["template"]["credential"]["path"] = str(self.key_file)
        self.value = template.snapshot(self.bundle)
        self.owner = (os.getuid(), os.getgid())

    def installed(self):
        runtime.install_payload({"snapshot": self.value, "client_api_key": KEY}, self.home, self.owner)

    def binding(self):
        meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", "sha256:fake")
        record = {"name": "testbox", "branch": "topic", "podman-id": CID,
                  "image-digest": "sha256:fake", "retired": False, "agent-template": dict(meta)}
        state = {"repo": str(self.root / "repo"), "agent-template": meta, "containers": [record]}
        detail = {"Id": CID, "Image": IMAGE_ID, "Name": "/testbox", "State": {"Status": "running"},
                  "Config": {"Labels": {common.CONTAINER_LABEL: str(common.CONTRACT),
                     common.TOKEN_LABEL: meta["creation-token"], common.DIGEST_LABEL: meta["snapshot-digest"],
                     "sandbox-worktree.repo": state["repo"], "sandbox-worktree.mother": "topic",
                     "sandbox-worktree.name": "testbox"}}}
        return state, detail


class DataTests(TemporaryCase):
    def test_deterministic_and_native_catalog_consumed(self):
        self.assertEqual(template.snapshot(self.bundle), template.snapshot(copy.deepcopy(self.bundle)))
        files = self.value["files"]
        expected_models = {"deepseek-flash", "glm-5.3-flash", "glm-5.4", "gpt-6-luna",
                           "gpt-6.2-astra", "gpt-6.2-sol"}
        pi = json.loads(files[".pi/agent/models.json"])
        self.assertEqual({m["id"] for m in pi["providers"]["cli"]["models"]}, expected_models)
        pi_settings = json.loads(files[".pi/agent/settings.overlay.json"])
        self.assertEqual(pi_settings["defaultModel"], "deepseek-flash")
        codex = tomllib.loads(files[".codex/config.toml"])
        self.assertEqual(codex["model"], "gpt-6-luna")
        self.assertEqual(codex["model_catalog_json"], "/home/bolo/.codex/models.json")
        catalog = json.loads(files[".codex/models.json"])
        self.assertEqual({m["slug"] for m in catalog["models"]},
                         {"gpt-6-luna", "gpt-6.2-astra", "gpt-6.2-sol"})
        self.assertTrue(all(m["upgrade"] is None and not m["prefer_websockets"] for m in catalog["models"]))
        kimi = tomllib.loads(files[".kimi-code/config.toml"])
        self.assertEqual(kimi["default_model"], "cliproxy-chat/deepseek-flash")
        self.assertEqual(set(kimi["models"]), {
            "cliproxy-chat/deepseek-flash", "cliproxy-chat/glm-5.3-flash",
            "cliproxy-chat/glm-5.4",
            "cliproxy-responses/gpt-6-luna",
            "cliproxy-responses/gpt-6.2-astra", "cliproxy-responses/gpt-6.2-sol",
        })
        self.assertEqual({p["base_url"] for p in kimi["providers"].values()}, {self.bundle["template"]["base_url"]})
        self.assertNotIn(KEY, json.dumps(self.value))
        self.assertNotIn(MANAGEMENT, json.dumps(self.value))

    def test_cost_optional_but_complete_when_present(self):
        # 价格未公布的模型 (如 glm-5.4) 可省略 cost; 出现时必须完整合法.
        data = copy.deepcopy(self.bundle)
        for model in data["catalog"]["models"]:
            model.pop("cost", None)
        template.validate(data["template"], data["catalog"])
        data["catalog"]["models"][0]["cost"] = {"input": 8, "output": 40}
        with self.assertRaises(common.TemplateError):
            template.validate(data["template"], data["catalog"])

    def test_reject_invalid_data_and_executable_fields(self):
        mutations = [
            lambda t, c: t.update(install="curl unsafe | sh"),
            lambda t, c: t["credential"].update(field="management_key"),
            lambda t, c: t.update(base_url="http://user:secret@host/v1"),
            lambda t, c: t["defaults"]["pi"].update(model="not-present"),
            lambda t, c: t["defaults"]["codex"].update(model="glm-5.3"),
            lambda t, c: c["models"].append(copy.deepcopy(c["models"][0])),
            lambda t, c: c["models"][0].update(contextWindow=-1),
            lambda t, c: c["models"][0].update(input=[{}]),
            lambda t, c: c["models"][0]["cost"].update(input=float("nan")),
            lambda t, c: c["codex_catalog"]["models"][0].update(prefer_websockets=True),
            lambda t, c: c["codex_catalog"]["models"][0].update(context_window=1),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                data = copy.deepcopy(self.bundle)
                mutate(data["template"], data["catalog"])
                with self.assertRaises(common.TemplateError):
                    template.validate(data["template"], data["catalog"])

    def test_new_birth_same_name_gets_new_snapshot_not_old_one(self):
        self.bundle["template"]["version"] = "test-v1"
        first = template.creation(self.root / "snapshot.json", self.bundle, "testbox", "sha256:fake")
        changed = copy.deepcopy(self.bundle)
        changed["template"]["version"] = "next"
        second = template.creation(self.root / "snapshot.json", changed, "testbox", "sha256:fake")
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        self.assertNotEqual(first["creation-token"], second["creation-token"])
        self.assertEqual(template.read_snapshot(Path(first["snapshot"]))["template"]["version"], "test-v1")

    def test_shared_business_credentials_require_decision(self):
        with self.assertRaises(common.TemplateError) as error:
            common.filtered_env({"GITHUB_TOKEN": KEY})
        self.assertIn("用户决定", str(error.exception))
        self.assertNotIn(KEY, str(error.exception))
        kept, _ = common.filtered_env({"STRIPE_KEY": KEY, "DATABASE_KEY": KEY})
        self.assertEqual(kept, {"STRIPE_KEY": KEY, "DATABASE_KEY": KEY})
        with self.assertRaises(common.TemplateError):
            common.filtered_env({"BUSINESS": "value\nOPENAI_API_KEY=bad"})

    def test_credential_requires_private_file_and_extracts_only_client_key(self):
        self.assertEqual(template.credential(self.value), KEY)
        self.key_file.chmod(0o644)
        with self.assertRaises(common.TemplateError):
            template.credential(self.value)
        self.key_file.chmod(0o600)
        link = self.root / "key-link"
        link.symlink_to(self.key_file)
        with self.assertRaises(common.TemplateError):
            common.private_json(link)
        common.safe_write(self.key_file, '{"management_key":"' + MANAGEMENT + '"}')
        with self.assertRaises(common.TemplateError):
            template.credential(self.value)


class InstallerTests(TemporaryCase):
    def test_reentry_does_not_rewrite_key_or_config(self):
        self.installed()
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.home.rglob("*") if p.is_file()}
        runtime.install_payload({"snapshot": self.value, "client_api_key": "different-client-key-123456789"}, self.home, self.owner)
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.home.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.home / common.READY_PATH).exists())

    def test_new_nested_config_directories_are_owned_by_client_user(self):
        made = []
        existing = self.home / ".config"
        existing.mkdir()
        real_mkdir = Path.mkdir
        def tracked_mkdir(path, *args, **kwargs):
            existed = path.exists()
            result = real_mkdir(path, *args, **kwargs)
            if not existed:
                made.append(path)
            return result
        with mock.patch.object(Path, "mkdir", tracked_mkdir), mock.patch.object(runtime.os, "chown") as chown:
            runtime.checked_path(self.home, common.KEY_PATH, create=True, owner=self.owner)
        assigned = {Path(call.args[0]) for call in chown.call_args_list}
        self.assertTrue(made)
        self.assertTrue(set(made) <= assigned, "root 创建的中间目录也须交给客户端用户, 否则 Chromium 无法写 .config")
        self.assertIn(existing, assigned, "已存在但由 root 持有的 .config 也须交给客户端用户")
        self.assertNotIn(self.home, assigned)

    def test_oauth_is_never_overwritten(self):
        auth = self.home / ".pi/agent/auth.json"
        common.safe_write(auth, '{"oauth":"do-not-touch"}')
        with self.assertRaises(common.TemplateError):
            self.installed()
        self.assertEqual(auth.read_text(), '{"oauth":"do-not-touch"}')
        self.assertFalse((self.home / common.KEY_PATH).exists())

    def test_no_symlink_target_or_permission_relaxation(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / ".codex").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(common.TemplateError):
            self.installed()
        self.assertEqual(list(outside.iterdir()), [])

    def test_public_trust_and_hooks_preserved_without_template_permission_settings(self):
        public = self.home / ".pi/agent/settings.json"
        common.safe_write(public, common.pretty({"defaultProjectTrust": "never", "defaultModel": "old",
                                               "extensions": ["public-hook.ts"]}))
        self.installed()
        settings = json.loads(public.read_text())
        self.assertEqual(settings["defaultProjectTrust"], "never")
        self.assertEqual(settings["extensions"], ["public-hook.ts"])
        for field in ("approval_policy", "sandbox_mode", "projects"):
            self.assertNotIn(field, tomllib.loads(self.value["files"][".codex/config.toml"]))

    def test_launcher_reads_key_without_shell_source(self):
        self.installed()
        common.safe_write(self.home / common.READY_PATH, common.pretty({"contract": common.CONTRACT, "snapshot-digest": self.value["snapshot-digest"]}), mode=0o644)
        env = launch.launch_env(self.home, {"CHANG_ZHI_AI_WORK": "old", "OPENAI_API_KEY": "old", "PATH": "/bin", "HTTP_PROXY": "http://bad"})
        self.assertEqual(env[common.KEY_ENV], KEY)
        self.assertEqual(env["HOME"], str(self.home))
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("CHANG_ZHI_AI_WORK", env)
        self.assertNotIn("HTTP_PROXY", env)
        (self.home / common.KEY_PATH).chmod(0o644)
        with self.assertRaises(common.TemplateError):
            launch.launch_env(self.home, {})

    def test_launcher_rejects_missing_store_instead_of_using_inherited_key(self):
        self.installed()
        common.safe_write(self.home / common.READY_PATH, common.pretty({"contract": common.CONTRACT, "snapshot-digest": self.value["snapshot-digest"]}), mode=0o644)
        (self.home / common.KEY_PATH).unlink()
        with self.assertRaises(common.TemplateError):
            launch.launch_env(self.home, {common.KEY_ENV: KEY, "CLIPROXYAPI_KEY": KEY})

    def test_real_entrypoint_for_each_client_uses_env_not_argv(self):
        self.installed()
        common.safe_write(self.home / common.READY_PATH, common.pretty({"contract": common.CONTRACT, "snapshot-digest": self.value["snapshot-digest"]}), mode=0o644)
        for entry, cli, defaults in (
            ("pi", "pi", []),
            ("codex", "codex", []),
            ("kimi", "kimi", []),
            ("codex-d", "codex", ["--dangerously-bypass-approvals-and-sandbox"]),
        ):
            observed = {}
            def fake_exec(binary, argv, env):
                observed.update(binary=binary, argv=argv, env=env)
            with mock.patch.object(launch, "HOME", self.home), mock.patch.object(launch.os, "execve", fake_exec):
                launch.main([entry, "--no-session"])
            self.assertEqual(observed["env"][common.KEY_ENV], KEY)
            self.assertNotIn(KEY, " ".join(observed["argv"]))
            self.assertIn(cli, observed["binary"])
            # codex-d 的固定参数在用户参数前, 不靠 shell 拼接
            self.assertEqual([*defaults, "--no-session"], observed["argv"][1:])

    def test_client_parsers_invoked_no_generation_and_no_secret_diagnostics(self):
        self.installed()
        calls = []
        def fake_run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(cmd, 0, KEY, KEY)
        with mock.patch.object(runtime, "HOME", self.home), mock.patch.object(runtime.subprocess, "run", fake_run), mock.patch.dict(os.environ, {}, clear=True):
            runtime.check_clients(KEY, self.owner)
        self.assertEqual(len(calls), 4)
        for cmd, kwargs in calls:
            self.assertNotIn(KEY, " ".join(cmd))
            self.assertEqual(kwargs["env"][common.KEY_ENV], KEY)
            self.assertNotIn("exec", cmd)
            self.assertNotIn("--print", cmd)


@unittest.skipUnless((Path("/opt/swt-agent-bin/pi").is_file()), "没有 Pi 原始解析器, 真实解析验收留给新测试容器")
class PiParserTests(TemporaryCase):
    def test_actual_pi_parser_and_auth_resolver_in_private_home(self):
        self.installed()
        env = common.client_env({"PATH": os.environ["PATH"], "TERM": "dumb"}, KEY, home=self.home)
        flags = ["--offline", "--no-extensions", "--no-mcp", "--no-skills", "--no-prompt-templates", "--no-context-files", "--no-approve"]
        listed = subprocess.run([str(runtime.REAL_BIN_DIR / "pi"), *flags, "--list-models", "cli"], cwd=self.home, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(listed.returncode, 0, "Pi 真实解析失败, 原始输出不打印")
        for model in self.bundle["catalog"]["models"]:
            self.assertIn(model["id"], listed.stdout, "Pi 未列出模板模型")
        auth = subprocess.run([str(runtime.REAL_BIN_DIR / "pi"), "auth", "check", "--provider", "cli", "--json", "--offline"], cwd=self.home, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(auth.returncode, 0, "Pi 凭据解析失败, 原始输出不打印")
        self.assertNotIn(KEY, auth.stdout + auth.stderr)
        self.assertEqual(json.loads(auth.stdout)["status"], "ready")

    def test_repo_pi_config_resolves_environment_and_rejects_missing_key(self):
        agent_dir = self.home / ".pi/agent"
        common.safe_write(agent_dir / "models.json", (ROOT / "pi/models.json").read_text())
        env = {"PATH": os.environ["PATH"], "HOME": str(self.home), "TERM": "dumb",
               "PI_CODING_AGENT_DIR": str(agent_dir), "PI_OFFLINE": "1"}
        command = [str(runtime.REAL_BIN_DIR / "pi"), "auth", "print-api-key",
                   "--provider", "cli", "--offline"]
        # 仅解析临时 HOME 和假 Key, 捕获输出, 不连接网关/生成内容.
        with_key = subprocess.run(command, cwd=self.home, env={**env, "CLIPROXYAPI_KEY": KEY},
                                  capture_output=True, text=True, timeout=30)
        self.assertEqual(with_key.returncode, 0, "Pi 环境变量解析失败, 原始输出不打印")
        self.assertTrue(with_key.stdout.strip() == KEY, "Pi 必须解析出环境变量的值")
        without_key = subprocess.run(command, cwd=self.home, env=env,
                                     capture_output=True, text=True, timeout=30)
        self.assertNotEqual(without_key.returncode, 0, "缺少环境变量时不得使用占位符或回退密钥")
        for path in self.home.rglob("*"):
            if path.is_file():
                self.assertNotIn(KEY, path.read_text(), "Pi 不得将环境变量 Key 写入配置/认证文件")


class HostBindingTests(TemporaryCase):
    def fake_boundary(self, state, detail, *, installed=False, failure=False):
        calls = []
        def captured(cmd, **kwargs):
            calls.append((cmd, kwargs))
            if cmd[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(cmd, 0, json.dumps([detail]), "")
            if cmd[-1] == "state":
                return subprocess.CompletedProcess(cmd, 0, json.dumps({"installed": installed}), "")
            report = {"ok": True, "contract": common.CONTRACT, "snapshot-digest": state["agent-template"]["snapshot-digest"],
                      "checks": ["permissions", "config", "credentials", "clients", "gateway-models"]}
            if failure:
                return subprocess.CompletedProcess(cmd, 1, KEY, '{"error":"' + KEY + '"}')
            return subprocess.CompletedProcess(cmd, 0, json.dumps(report), "")
        return calls, mock.patch.object(template, "captured", captured)

    def test_only_client_key_via_stdin_to_full_container_id(self):
        state, detail = self.binding()
        calls, boundary = self.fake_boundary(state, detail)
        with boundary:
            template.operate(state, "testbox", install=True)
        command, options = calls[-1]
        self.assertIn(CID, command)
        self.assertNotIn("testbox", command)
        self.assertNotIn(KEY, " ".join(command))
        self.assertNotIn(MANAGEMENT, options["input"])
        payload = json.loads(options["input"])
        self.assertEqual(payload["client_api_key"], KEY)
        self.assertNotIn("management_key", payload)

    def test_old_container_or_changed_id_never_executes(self):
        for mutation in ("legacy", "id", "token", "repo", "snapshot"):
            with self.subTest(mutation=mutation):
                state, detail = self.binding()
                if mutation == "legacy":
                    state.pop("agent-template")
                    state["containers"][0].pop("agent-template")
                elif mutation == "id":
                    detail["Id"] = "b" * 64
                else:
                    label = {"token": common.TOKEN_LABEL, "repo": "sandbox-worktree.repo", "snapshot": common.DIGEST_LABEL}[mutation]
                    detail["Config"]["Labels"][label] = "other"
                calls, boundary = self.fake_boundary(state, detail)
                with boundary, mock.patch.object(template, "credential", side_effect=AssertionError("must not read credential")):
                    with self.assertRaises(common.TemplateError):
                        template.operate(state, "testbox", install=True)
                self.assertTrue(all(cmd[:2] != ["podman", "exec"] for cmd, _ in calls))

    def test_existing_install_and_verified_resume_do_not_read_host_key(self):
        for verified in (False, True):
            state, detail = self.binding()
            if verified:
                state["agent-template"]["status"] = "verified"
                state["containers"][0]["agent-template"] = dict(state["agent-template"])
            calls, boundary = self.fake_boundary(state, detail, installed=True)
            with boundary, mock.patch.object(template, "credential", side_effect=AssertionError("host key must not be read")):
                template.operate(state, "testbox", install=True)
            self.assertNotIn("client_api_key", json.loads(calls[-1][1]["input"]))
            self.assertEqual(calls[-1][0][-1], "check" if verified else "install")

    def test_reflected_secret_is_not_in_failure(self):
        state, detail = self.binding()
        calls, boundary = self.fake_boundary(state, detail, failure=True)
        with boundary:
            with self.assertRaises(common.TemplateError) as error:
                template.operate(state, "testbox", install=True)
        self.assertNotIn(KEY, str(error.exception))
        self.assertNotIn(MANAGEMENT, str(error.exception))

    def test_state_failure_keeps_allowlisted_reason_only(self):
        # 旧镜像解析器拒收快照时 state 以非零退出; 原因在 stderr 的固定 JSON 里.
        reason = "模板字段缺失/未知, 不允许安装命令或额外凭据"
        for reported, expected in ((reason, reason), ("reflected " + KEY, "")):
            with self.subTest(reported=reported):
                state, detail = self.binding()

                def captured(cmd, **kwargs):
                    if cmd[:2] == ["podman", "inspect"]:
                        return subprocess.CompletedProcess(cmd, 0, json.dumps([detail]), "")
                    if cmd[-1] == "state":
                        return subprocess.CompletedProcess(cmd, 2, KEY, json.dumps({"error": reported}))
                    raise AssertionError("state 失败后不得继续 install/check")

                with mock.patch.object(template, "captured", captured), \
                        mock.patch.object(template, "credential", side_effect=AssertionError("must not read host key")):
                    with self.assertRaises(common.TemplateError) as error:
                        template.operate(state, "testbox", install=True)
                message = str(error.exception)
                self.assertIn("新容器初始化状态不符", message)
                self.assertNotIn(KEY, message)
                if expected:
                    self.assertIn(expected, message)
                else:
                    self.assertNotIn("reflected", message)


class GatewayTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.calls = []
        case = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                case.calls.append((self.path, self.headers.get("Authorization") == "Bearer " + KEY))
                if case.mode == "redirect":
                    self.send_response(302)
                    self.send_header("Location", case.other_url + "/stolen")
                    self.end_headers()
                    return
                self.send_response(200 if case.mode != "fail" else 503)
                self.end_headers()
                data = [{"id": m["id"]} for m in case.bundle["catalog"]["models"]] if case.mode == "ok" else []
                self.wfile.write(json.dumps({"data": data, "reflected": KEY}).encode())
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.bundle["template"]["base_url"] = f"http://127.0.0.1:{self.server.server_port}/v1"
        self.value = template.snapshot(self.bundle)
        self.mode = "ok"

    def test_only_authenticated_get_models(self):
        runtime.check_gateway(self.value, KEY)
        self.assertEqual(self.calls, [("/v1/models", True)])

    def test_failure_or_missing_models_never_deliver_ready(self):
        self.installed()
        for mode in ("fail", "missing"):
            self.mode = mode
            with self.assertRaises(common.TemplateError) as error:
                runtime.check_payload({"snapshot": self.value}, self.home, self.owner, clients=lambda *args: None)
            self.assertNotIn(KEY, str(error.exception))
            self.assertFalse((self.home / common.READY_PATH).exists())
        self.assertTrue(all(path == "/v1/models" for path, _ in self.calls))

    def test_redirect_does_not_forward_key(self):
        other_calls = []
        class Other(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                other_calls.append(True)
                self.send_response(200)
                self.end_headers()
        other = ThreadingHTTPServer(("127.0.0.1", 0), Other)
        threading.Thread(target=other.serve_forever, daemon=True).start()
        self.addCleanup(other.server_close)
        self.addCleanup(other.shutdown)
        self.other_url = f"http://127.0.0.1:{other.server_port}"
        self.mode = "redirect"
        with self.assertRaises(common.TemplateError):
            runtime.check_gateway(self.value, KEY)
        self.assertEqual(other_calls, [])


class PreflightTests(TemporaryCase):
    """birth 前置的镜像内只读模板预检: 固定镜像 ID, 无网络/挂载/凭据, 不安装, 不拉取."""

    PIN = "sha256:" + "b" * 64

    def fake(self, *, has_validate=True, capability_rc=None, validate_rc=0, validate_report="",
             state_rc=0, state_report=""):
        calls = []

        def captured(cmd, **kwargs):
            calls.append((cmd, kwargs))
            if cmd[:3] == ["podman", "image", "inspect"]:
                return subprocess.CompletedProcess(cmd, 0, self.PIN + "\n", "")
            if "-c" in cmd:
                rc = capability_rc if capability_rc is not None else (0 if has_validate else 1)
                return subprocess.CompletedProcess(cmd, rc, "", "")
            if cmd[-1] == "validate":
                if validate_rc == 0:
                    report = {"ok": True, "contract": common.CONTRACT,
                              "snapshot-digest": self.value["snapshot-digest"]}
                    return subprocess.CompletedProcess(cmd, 0, json.dumps(report), "")
                return subprocess.CompletedProcess(cmd, validate_rc, "", validate_report)
            if cmd[-1] == "state":
                if state_rc == 0:
                    return subprocess.CompletedProcess(cmd, 0, json.dumps({"installed": False}), "")
                return subprocess.CompletedProcess(cmd, state_rc, "", state_report)
            raise AssertionError("未预期的命令: " + " ".join(cmd))

        return calls, mock.patch.object(template, "captured", captured)

    def assert_offline_readonly(self, command):
        self.assertEqual(command[:2], ["podman", "run"])
        for flag in ("--rm", "--pull=never", "--network=none", "--http-proxy=false", "-i"):
            self.assertIn(flag, command)
        for flag in ("-v", "--volume", "-e", "--env", "--privileged", "--pull=always", "--pull=newer"):
            self.assertNotIn(flag, command)
        self.assertIn(self.PIN, command)

    def runs(self, calls):
        return [command for command, _ in calls if command[:2] == ["podman", "run"]]

    def test_new_image_preflight_pins_local_id_and_blocks_proxy(self):
        calls, boundary = self.fake()
        with boundary:
            pinned = template.preflight("localhost/new:1", self.value)
        self.assertEqual(pinned, self.PIN)
        commands = self.runs(calls)
        self.assertEqual(["probe" if "-c" in command else command[-1] for command in commands],
                         ["probe", "validate"])
        for command in commands:
            self.assert_offline_readonly(command)
            self.assertNotIn("localhost/new:1", command)
        payload = json.loads(calls[-1][1]["input"])
        self.assertEqual(set(payload), {"snapshot"})
        self.assertEqual(payload["snapshot"], self.value)
        self.assertNotIn(KEY, calls[-1][1]["input"])
        self.assertNotIn(MANAGEMENT, calls[-1][1]["input"])

    def test_legacy_entry_is_identified_before_any_validate_call(self):
        calls, boundary = self.fake(has_validate=False)
        with boundary:
            template.preflight("localhost/old:1", self.value)
        actions = ["probe" if "-c" in command else command[-1] for command in self.runs(calls)]
        self.assertEqual(actions, ["probe", "state"])
        binding = json.loads(calls[-1][1]["input"])["binding"]
        self.assertRegex(binding["creation-token"], r"^[0-9a-f]{32}$")
        self.assertRegex(binding["container-id"], r"^[0-9a-f]{64}$")
        self.assertNotIn(KEY, calls[-1][1]["input"])

    def test_new_entry_real_rejection_never_falls_back_to_state(self):
        reason = "模板字段缺失/未知, 不允许安装命令或额外凭据"
        calls, boundary = self.fake(validate_rc=2, validate_report=json.dumps({"error": reason}))
        with boundary:
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/new:1", self.value)
        message = str(error.exception)
        self.assertIn(reason, message)
        self.assertIn("image-prep", message)
        self.assertIn("--image", message)
        self.assertIn("不补假价格", message)
        self.assertIn(self.PIN, message)
        self.assertNotIn("state", [command[-1] for command in self.runs(calls)])

    def test_new_entry_tool_guard_failure_is_not_a_version_fallback(self):
        calls, boundary = self.fake(
            validate_rc=2, validate_report=json.dumps({"error": template.LEGACY_TOOL_REASON}))
        with boundary:
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/new:1", self.value)
        self.assertIn("自检失败", str(error.exception))
        self.assertNotIn("state", [command[-1] for command in self.runs(calls)])

    def test_unidentifiable_tool_version_fails_closed(self):
        calls, boundary = self.fake(capability_rc=2)
        with boundary:
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/new:1", self.value)
        self.assertIn("无法确认", str(error.exception))
        self.assertEqual(len(self.runs(calls)), 1)

    def test_legacy_state_must_report_not_installed(self):
        # state 报 installed=true 时不能当预检通过.
        calls = []

        def captured(cmd, **kwargs):
            calls.append(cmd)
            if cmd[:3] == ["podman", "image", "inspect"]:
                return subprocess.CompletedProcess(cmd, 0, self.PIN + "\n", "")
            if "-c" in cmd:
                return subprocess.CompletedProcess(cmd, 1, "", "")
            return subprocess.CompletedProcess(cmd, 0, json.dumps({"installed": True}), "")

        with mock.patch.object(template, "captured", captured):
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/old:1", self.value)
        self.assertIn("不是未安装", str(error.exception))

    def test_legacy_parser_rejection_reports_how_to_get_compatible_image(self):
        reason = "模板字段缺失/未知, 不允许安装命令或额外凭据"
        calls, boundary = self.fake(has_validate=False, state_rc=2,
                                    state_report=json.dumps({"error": reason}))
        with boundary:
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/old:1", self.value)
        message = str(error.exception)
        self.assertIn(reason, message)
        self.assertIn("image-prep", message)
        self.assertIn("--image", message)
        self.assertIn("不补假价格", message)

    def test_missing_or_wrong_preflight_report_is_rejected(self):
        for stdout in ('{"ok":true}', json.dumps({"ok": True, "contract": common.CONTRACT,
                                                  "snapshot-digest": "sha256:" + "c" * 64})):
            with self.subTest(stdout=stdout):
                calls = []

                def captured(cmd, **kwargs):
                    calls.append(cmd)
                    if cmd[:3] == ["podman", "image", "inspect"]:
                        return subprocess.CompletedProcess(cmd, 0, self.PIN + "\n", "")
                    if "-c" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, "", "")
                    return subprocess.CompletedProcess(cmd, 0, stdout, "")

                with mock.patch.object(template, "captured", captured):
                    with self.assertRaises(common.TemplateError):
                        template.preflight("localhost/new:1", self.value)

    def test_non_allowlisted_response_is_not_forwarded(self):
        reflected = json.dumps({"error": KEY})
        calls, boundary = self.fake(validate_rc=2, validate_report=reflected)
        with boundary:
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/new:1", self.value)
        self.assertNotIn(KEY, str(error.exception))
        self.assertNotIn(MANAGEMENT, str(error.exception))
        self.assertIn("不接受本次模板快照", str(error.exception))

    def test_image_must_exist_locally(self):
        def captured(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, "", "no such image")

        with mock.patch.object(template, "captured", captured):
            with self.assertRaises(common.TemplateError) as error:
                template.preflight("localhost/missing:1", self.value)
        self.assertIn("不能预检", str(error.exception))

    def test_cli_pin_image_normalizes_bare_local_id(self):
        calls = []

        def fake(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "a" * 64 + "\n", "")

        with mock.patch.object(template, "captured", fake):
            self.assertEqual(template.pin_image("localhost/x:1"), "sha256:" + "a" * 64)
            self.assertEqual(template.pin_image("sha256:" + "b" * 64), "sha256:" + "b" * 64)
        self.assertEqual(len(calls), 1, "--image 已是完整 ID 时不再 inspect")

    def test_in_image_validate_action_only_validates_snapshot(self):
        report = runtime.validate_only({"snapshot": self.value})
        self.assertEqual(report, {"ok": True, "contract": common.CONTRACT,
                                  "snapshot-digest": self.value["snapshot-digest"]})
        with self.assertRaises(common.TemplateError):
            runtime.validate_only({"snapshot": {}})
        with self.assertRaises(common.TemplateError):
            runtime.validate_only({})
        self.assertFalse((self.home / common.KEY_PATH).exists())
        self.assertFalse((self.home / common.SNAPSHOT_PATH).exists())


class CapabilityProbeTests(unittest.TestCase):
    """能力探针: 真实镜像里 runtime.py 只是 import wrapper, 动作列表在内层包里."""

    WRAPPER = "from agent_config.runtime import main\nraise SystemExit(main())\n"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="swt-probe-layout-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "swt-agent-config"
        self.root.mkdir()

    def probe(self) -> int:
        return subprocess.run([sys.executable, "-c", template.capability_probe_source(str(self.root))],
                              capture_output=True, text=True).returncode

    def inner(self, text: str) -> None:
        (self.root / "agent_config").mkdir(exist_ok=True)
        (self.root / "agent_config" / "runtime.py").write_text(text, encoding="utf-8")

    def test_wrapper_only_layout_has_no_validate(self):
        # 2026.10.30-1 的布局: 根目录 runtime.py 是 wrapper, 内层没有 validate.
        (self.root / "runtime.py").write_text(self.WRAPPER, encoding="utf-8")
        self.inner('ACTIONS = (["install"], ["check"], ["state"])\n')
        self.assertEqual(1, self.probe())

    def test_inner_implementation_with_validate_is_detected_without_marker(self):
        (self.root / "runtime.py").write_text(self.WRAPPER, encoding="utf-8")
        self.inner('ACTIONS = ["install", "check", "state", "validate"]\n')
        self.assertEqual(0, self.probe())

    def test_marker_is_authoritative_for_new_images(self):
        (self.root / "runtime.py").write_text(self.WRAPPER, encoding="utf-8")
        self.inner('ACTIONS = ["install", "check", "state", "validate"]\n')
        (self.root / "agent-tool-actions").write_text("install\ncheck\nstate\n", encoding="utf-8")
        # 标记说不支持就以标记为准, 不回退去扫源码.
        self.assertEqual(1, self.probe())
        (self.root / "agent-tool-actions").write_text("install check state validate\n", encoding="utf-8")
        self.assertEqual(0, self.probe())

    def test_missing_tool_directory_fails_closed(self):
        code = subprocess.run(
            [sys.executable, "-c", template.capability_probe_source(str(self.root / "absent"))],
            capture_output=True, text=True).returncode
        self.assertEqual(2, code)


class RuntimeEntryTests(TemporaryCase):
    """容器内工具 main() 入口: validate 只读预检动作 (不经 podman)."""

    def call(self, action, payload, ready=True):
        out, err = io.StringIO(), io.StringIO()
        stdin = io.StringIO(json.dumps(payload))
        with mock.patch.object(runtime, "tool_ready", return_value=ready), \
                mock.patch.object(sys, "stdin", stdin), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = runtime.main([action])
        return code, out.getvalue(), err.getvalue()

    def test_validate_entry_returns_fixed_report_and_writes_nothing(self):
        code, out, err = self.call("validate", {"snapshot": self.value})
        self.assertEqual(0, code, err)
        self.assertEqual(json.loads(out), {"ok": True, "contract": common.CONTRACT,
                                           "snapshot-digest": self.value["snapshot-digest"]})
        self.assertEqual("", err)
        self.assertFalse((self.home / common.KEY_PATH).exists())
        self.assertFalse((self.home / common.SNAPSHOT_PATH).exists())
        self.assertFalse((self.home / common.READY_PATH).exists())

    def test_validate_entry_rejects_invalid_snapshot_with_fixed_reason(self):
        for payload in ({"snapshot": {}}, {}):
            with self.subTest(payload=payload):
                code, out, err = self.call("validate", payload)
                self.assertEqual(2, code)
                self.assertEqual("", out)
                self.assertIn("模板字段缺失/未知", json.loads(err)["error"])
                self.assertFalse((self.home / common.SNAPSHOT_PATH).exists())

    def test_unknown_action_is_rejected(self):
        code, out, err = self.call("bogus", {"snapshot": self.value})
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(json.loads(err)["error"], "初始化工具仅用于契约匹配的新容器")

    def test_entry_requires_contract_and_root(self):
        code, out, err = self.call("validate", {"snapshot": self.value}, ready=False)
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(json.loads(err)["error"], "初始化工具仅用于契约匹配的新容器")


class LifecycleTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.swt = load_script("swt_agent_lifecycle_test", "swt.py")
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.mother = self.root / "mother"
        self.mother.mkdir()
        self.records = self.root / "records"
        self.runtime_file = self.records / "runtime/unit.json"
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.resources = {}
        basic = {"mother_path": self.mother, "resolve_pair_identity": "unit", "find_mother": (self.mother, False),
                 "daemon_pids_for_serve_path": [], "container_exists": False, "legacy_pair_branches": [],
                 "host_wayland_socket": None, "live_repo_containers": [], "resolve_project_slug": "unit",
                 "prepare_image": {"ref": "fake:image", "digest": "sha256:fake", "pin": IMAGE_ID,
                                   "verdict": "EXPLICIT"},
                 "decision_fingerprint": {"repo": str(self.repo), "image-digest": "sha256:fake"},
                 "print_birth_state": None, "print_delivery_lines": None}
        for name, value in basic.items():
            self.stack.enter_context(mock.patch.object(self.swt, name, return_value=value))
        for name in ("create_mother_worktree", "configure_repo", "start_daemon", "create_and_start_container", "migrate_legacy_pairs", "inject_auth_json"):
            self.resources[name] = self.stack.enter_context(mock.patch.object(self.swt, name, side_effect=AssertionError("resource mutation before gate: " + name)))
        self.stack.enter_context(mock.patch.object(template, "load", return_value=self.bundle))
        self.stack.enter_context(mock.patch.object(template, "choices", return_value=[template.summary(self.bundle)]))
        self.preflight = self.stack.enter_context(mock.patch.object(template, "preflight"))
        self.image_gate = self.stack.enter_context(mock.patch.object(template, "image_compatible"))

    def args(self, *, selected=True):
        values = ["birth", "--repo", str(self.repo), "--records-root", str(self.records), "--branch", "topic",
                  "--name", "testbox", "--image", "fake:image", "--mode", "whitelist", "--hostname", "testbox", "--lan-ip", "192.0.2.10"]
        if selected:
            values += ["--agent-template", "cliproxyapi"]
        return self.swt.parse_args(values)

    def test_missing_template_decides_before_any_resource(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(self.swt.birth(self.args(selected=False), self.repo), 1)
        self.assertIn("agent-template", out.getvalue())
        receipts = list(self.records.glob("runtime/unit/decisions/d-*.json"))
        self.assertEqual(len(receipts), 1)
        receipt = json.loads(receipts[0].read_text())
        self.assertEqual(receipt["fingerprint"]["agent-template-options"], [template.summary(self.bundle)])
        self.image_gate.assert_not_called()
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_template_drift_expires_receipt(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.swt.birth(self.args(selected=False), self.repo)
        old = set(self.records.glob("runtime/unit/decisions/d-*.json"))
        changed = copy.deepcopy(self.bundle)
        changed["template"]["version"] = "next"
        with mock.patch.object(template, "choices", return_value=[template.summary(changed)]), mock.patch.object(template, "load", return_value=changed), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(self.swt.birth(self.args(), self.repo), 1)
        self.assertIn("已变化", out.getvalue())
        self.assertTrue(all(not path.exists() for path in old))
        self.image_gate.assert_not_called()

    def test_missing_key_or_old_image_or_shared_env_rejected_before_resources(self):
        for kind in ("key", "image", "shared"):
            with self.subTest(kind=kind), contextlib.ExitStack() as stack:
                if kind == "key":
                    stack.enter_context(mock.patch.object(template, "credential", side_effect=common.TemplateError("客户端 Key 缺失")))
                elif kind == "image":
                    stack.enter_context(mock.patch.object(template, "image_compatible", side_effect=common.TemplateError("旧镜像")))
                else:
                    stack.enter_context(mock.patch.object(self.swt, "load_inherited_env", return_value={"AWS_SECRET_ACCESS_KEY": KEY}))
                with self.assertRaises(self.swt.PreconditionError) as error:
                    self.swt.birth(self.args(), self.repo)
                self.assertNotIn(KEY, str(error.exception))
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_old_runtime_rejected_without_template_or_oauth_mutation(self):
        self.swt.atomic_write_json(self.runtime_file, {"stage": "born", "containers": [{"name": "old"}]})
        with self.assertRaises(self.swt.PreconditionError):
            self.swt.birth(self.args(), self.repo)
        self.assertTrue(all(not value.called for value in self.resources.values()))
        self.preflight.assert_not_called()

    def test_preflight_runs_before_credentials_and_resources(self):
        order: list[str] = []

        def preflight(ref, value):
            order.append("preflight:" + ref)

        def credential(value):
            order.append("credential")
            raise common.TemplateError("客户端 Key 缺失")

        with mock.patch.object(template, "preflight", side_effect=preflight), \
                mock.patch.object(template, "credential", side_effect=credential):
            with self.assertRaises(self.swt.PreconditionError):
                self.swt.birth(self.args(), self.repo)
        # 镜像预检先于读主机凭据; 两者都先于母体/daemon/容器.
        self.assertEqual(order, [f"preflight:{IMAGE_ID}", "credential"])
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_preflight_and_create_share_pinned_image_id(self):
        pinned = IMAGE_ID
        image = {"ref": "fake:image", "digest": "sha256:fake", "pin": pinned,
                 "verdict": "EXPLICIT", "newer-available": False}
        seen = []
        with mock.patch.object(self.swt, "prepare_image", return_value=image), \
                mock.patch.object(template, "preflight",
                                  side_effect=lambda ref, value: seen.append(ref)), \
                mock.patch.object(template, "credential", side_effect=common.TemplateError("客户端 Key 缺失")):
            with self.assertRaises(self.swt.PreconditionError):
                self.swt.birth(self.args(), self.repo)
        # 契标签检查与镜像预检都指向同一个不可变 ID, 不用可变 tag.
        self.assertEqual(seen, [pinned])
        self.image_gate.assert_called_once_with(pinned)

    def test_preflight_failure_blocks_before_credentials_and_resources(self):
        with mock.patch.object(template, "preflight",
                               side_effect=common.TemplateError("镜像内模板解析器不接受本次模板快照")), \
                mock.patch.object(template, "credential", side_effect=AssertionError("must not read host key")), \
                mock.patch.object(template, "creation", side_effect=AssertionError("must not freeze snapshot")):
            with self.assertRaises(self.swt.PreconditionError) as error:
                self.swt.birth(self.args(), self.repo)
        self.assertIn("不接受本次模板快照", str(error.exception))
        self.assertTrue(all(not value.called for value in self.resources.values()))
        self.assertFalse((self.records / "runtime/unit").exists())

    def test_verified_birth_reentry_uses_frozen_snapshot_not_latest_template(self):
        meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", "sha256:fake")
        meta.update(status="verified", hostname="testbox")
        state = {"stage": "born", "repo": str(self.repo), "mother": {"dir": str(self.mother), "branch": "topic"},
                 "mother_dir": str(self.mother), "image": {"ref": "fake:image", "digest": "sha256:fake"},
                 "network": {"mode": "whitelist", "allow": [], "deny": []}, "agent-template": meta,
                 "containers": [{"name": "testbox", "agent-template": dict(meta)}]}
        self.swt.atomic_write_json(self.runtime_file, state)
        with mock.patch.object(template, "target"), mock.patch.object(template, "operate", return_value={"ok": True}) as operate, mock.patch.object(template, "load", side_effect=AssertionError("latest template read")), mock.patch.object(template, "credential", side_effect=AssertionError("host key read")), mock.patch.object(self.swt, "ensure_herdr_machine") as herdr:
            self.assertEqual(self.swt.birth(self.args(), self.repo), 0)
        self.assertFalse(operate.call_args.kwargs["install"])
        herdr.assert_called_once()
        self.assertEqual(herdr.call_args.args[-1]["name"], "testbox")
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_verified_reentry_skips_preflight_and_host_key(self):
        """固定快照重入不跑镜像预检, 也不重读主机 Key."""
        meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", "sha256:fake")
        meta.update(status="verified", hostname="testbox")
        state = {"stage": "born", "repo": str(self.repo), "mother": {"dir": str(self.mother), "branch": "topic"},
                 "mother_dir": str(self.mother), "image": {"ref": "fake:image", "digest": "sha256:fake"},
                 "network": {"mode": "whitelist", "allow": [], "deny": []}, "agent-template": meta,
                 "containers": [{"name": "testbox", "agent-template": dict(meta)}]}
        self.swt.atomic_write_json(self.runtime_file, state)
        with mock.patch.object(self.swt, "configure_repo"), \
                mock.patch.object(template, "target"), \
                mock.patch.object(template, "operate", return_value={"ok": True}) as operate, \
                mock.patch.object(template, "credential", side_effect=AssertionError("host key read")), \
                mock.patch.object(self.swt, "ensure_herdr_machine"):
            self.assertEqual(self.swt.birth(self.args(), self.repo), 0)
        self.assertFalse(operate.call_args.kwargs["install"])
        self.preflight.assert_not_called()
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_fixed_snapshot_reentry_preflights_only_before_container_exists(self):
        for exists in (False, True):
            with self.subTest(container_exists=exists):
                meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", IMAGE_ID)
                meta.update(status="pending", hostname="testbox")
                state = {"stage": "daemon", "repo": str(self.repo), "mother": {"dir": str(self.mother), "branch": "topic"},
                         "mother_dir": str(self.mother), "image": {"ref": "fake:image", "digest": IMAGE_ID, "pin": IMAGE_ID},
                         "network": {"mode": "whitelist", "allow": [], "deny": []}, "agent-template": meta,
                         "containers": []}
                self.swt.atomic_write_json(self.runtime_file, state)
                self.preflight.reset_mock()
                with mock.patch.object(self.swt, "container_exists", return_value=exists), \
                        mock.patch.object(self.swt, "image_identity", return_value={"digest": IMAGE_ID, "pin": IMAGE_ID}), \
                        mock.patch.object(self.swt, "configure_repo", side_effect=AssertionError("stop here")):
                    with self.assertRaises(AssertionError):
                        self.swt.birth(self.args(), self.repo)
                if exists:
                    self.preflight.assert_not_called()
                else:
                    self.preflight.assert_called_once()
                    self.assertEqual(self.preflight.call_args.args[1]["snapshot-digest"],
                                     meta["snapshot-digest"])

    def test_build_new_decides_before_resolving_missing_image(self):
        image = {"ref": None, "digest": None, "verdict": "BUILD-NEW",
                 "newer-available": False, "reason": "没有满足需求的镜像"}
        args = self.args()
        args.image = None
        args.requirements = str(self.root / "requirements.md")
        with mock.patch.object(self.swt, "prepare_image", return_value=image), \
                mock.patch.object(self.swt, "resolve_image_pin",
                                  side_effect=AssertionError("BUILD-NEW 不能先解析镜像")), \
                mock.patch.object(template, "credential",
                                  side_effect=AssertionError("不能读主机 Key")), \
                mock.patch.object(template, "preflight",
                                  side_effect=AssertionError("不能先跑镜像预检")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = self.swt.birth(args, self.repo)
        self.assertEqual(1, code)
        self.assertIn("image-build", out.getvalue())
        receipts = [json.loads(path.read_text(encoding="utf-8"))
                    for path in self.records.glob("runtime/unit/decisions/d-*.json")]
        self.assertEqual([receipt["kind"] for receipt in receipts], ["image-build"])
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_bare_historical_image_digest_does_not_block_reentry(self):
        bare = "a" * 64
        meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", bare)
        meta.update(status="pending", hostname="testbox")
        state = {"stage": "daemon", "repo": str(self.repo), "mother": {"dir": str(self.mother), "branch": "topic"},
                 "mother_dir": str(self.mother), "image": {"ref": "fake:image", "digest": bare, "pin": IMAGE_ID},
                 "network": {"mode": "whitelist", "allow": [], "deny": []}, "agent-template": meta,
                 "containers": []}
        self.swt.atomic_write_json(self.runtime_file, state)
        identity = {"digest": "sha256:" + "e" * 64, "pin": IMAGE_ID}
        with mock.patch.object(self.swt, "container_exists", return_value=True), \
                mock.patch.object(self.swt, "image_identity", return_value=identity), \
                mock.patch.object(self.swt, "configure_repo", side_effect=AssertionError("stop here")):
            with self.assertRaises(AssertionError):
                self.swt.birth(self.args(), self.repo)
        stored = json.loads(self.runtime_file.read_text(encoding="utf-8"))
        # 记录里的原始 digest 不被改写.
        self.assertEqual(stored["image"]["digest"], bare)
        self.assertEqual(stored["agent-template"]["image-digest"], bare)

    def test_unverified_container_never_persists_image_pin(self):
        # 同名容器不是本创建记录 (guard 不通过), 且 digest 本地解析不出 → 停, 记录不被改写.
        digest = "sha256:" + "d" * 64
        meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", IMAGE_ID)
        meta.update(status="pending", hostname="testbox")
        state = {"stage": "daemon", "repo": str(self.repo), "mother": {"dir": str(self.mother), "branch": "topic"},
                 "mother_dir": str(self.mother), "image": {"ref": "localhost/x:1", "digest": digest},
                 "network": {"mode": "whitelist", "allow": [], "deny": []}, "agent-template": meta,
                 "containers": [{"name": "testbox", "branch": "topic", "podman-id": CID,
                                 "image-digest": digest, "retired": False, "agent-template": dict(meta)}]}
        self.swt.atomic_write_json(self.runtime_file, state)
        foreign = {"Id": CID, "Image": "a" * 64, "ImageDigest": "",
                   "Config": {"Labels": {"sandbox-worktree.name": "testbox"}}}

        def fake_run(command, **kwargs):
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([foreign]), "")
            return subprocess.CompletedProcess(command, 1, "", "not found")

        with mock.patch.object(self.swt, "run", fake_run), \
                mock.patch.object(self.swt, "image_identity", return_value={"digest": IMAGE_ID, "pin": IMAGE_ID}):
            with self.assertRaises(self.swt.PreconditionError):
                self.swt.birth(self.args(), self.repo)
        stored = json.loads(self.runtime_file.read_text(encoding="utf-8"))
        self.assertNotIn("pin", stored["image"])
        self.assertTrue(all(not value.called for value in self.resources.values()))

    def test_initialization_failure_persists_failed_not_born(self):
        state, _ = self.binding()
        with mock.patch.object(template, "operate", side_effect=common.TemplateError("gateway failed")):
            with self.assertRaises(self.swt.SwtError) as error:
                self.swt.initialize_agent_template(state, self.runtime_file, "testbox")
        self.assertEqual(error.exception.code, 3)
        stored = json.loads(self.runtime_file.read_text())
        self.assertEqual(stored["stage"], "agent-template-failed")
        self.assertEqual(stored["agent-template"]["status"], "failed")
        self.assertNotIn(KEY, json.dumps(stored))


class CreateReentryTests(TemporaryCase):
    def test_only_current_token_container_can_be_adopted_after_interrupted_record_write(self):
        swt = load_script("swt_agent_create_test", "swt.py")
        for old in (False, True):
            with self.subTest(old=old):
                state, detail = self.binding()
                state["containers"] = []
                if old:
                    detail["Config"]["Labels"].pop(common.TOKEN_LABEL)
                file = self.root / ("old-record.json" if old else "new-record.json")
                args = swt.parse_args(["birth", "--name", "testbox", "--hostname", "testbox"])
                def refreshed(name, record, *rest):
                    return {"name": name, "record": record, "port": 2222, "detail": detail}
                with mock.patch.object(swt, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps([detail]), "")), mock.patch.object(swt, "refresh_container", side_effect=refreshed) as refresh:
                    if old:
                        with self.assertRaises(swt.PreconditionError):
                            swt.create_and_start_container(args, Path(state["repo"]), {"ref": "fake", "digest": "sha256:fake", "pin": IMAGE_ID}, "topic", state, file, {}, self.root, "unit")
                        refresh.assert_not_called()
                        self.assertFalse(file.exists())
                    else:
                        result = swt.create_and_start_container(args, Path(state["repo"]), {"ref": "fake", "digest": "sha256:fake", "pin": IMAGE_ID}, "topic", state, file, {}, self.root, "unit")
                        self.assertEqual(result["record"]["podman-id"], CID)
                        self.assertEqual(json.loads(file.read_text())["containers"][0]["podman-id"], CID)


class ImagePinTests(TemporaryCase):
    """预检与正式创建只认本地不可变镜像 ID; 旧记录用固定 digest 解析, 解析不出就停."""

    def setUp(self):
        super().setUp()
        self.swt = load_script("swt_image_pin_test", "swt.py")

    def test_image_reference_refuses_mutable_tag(self):
        self.assertEqual(self.swt.image_reference({"ref": "localhost/x:1", "pin": IMAGE_ID}), IMAGE_ID)
        with self.assertRaises(self.swt.PreconditionError) as error:
            self.swt.image_reference({"ref": "localhost/x:1"})
        self.assertIn("拒绝用可变 tag", str(error.exception))

    def test_old_record_resolves_pin_from_repo_digest_without_tag(self):
        # 真实形态: 存储 digest 不是镜像 ID, 但 repo@digest 能解析.
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            if command[:3] == ["podman", "image", "inspect"]:
                if command[3] == f"localhost/x@{IMAGE_ID}":
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                return subprocess.CompletedProcess(command, 1, "", "image not known")
            raise AssertionError("不得用可变 tag:" + " ".join(command))

        with mock.patch.object(self.swt, "run", fake_run):
            self.assertEqual(
                self.swt.resolve_image_pin({"ref": "localhost/x:1", "digest": IMAGE_ID}), IMAGE_ID)
        self.assertIn(f"localhost/x@{IMAGE_ID}", [command[3] for command in calls])
        self.assertNotIn("localhost/x:1", [command[3] for command in calls])

    def record_and_runtime(self, *, labels_ok=True, image="a" * 64, digest=IMAGE_ID):
        meta = {"name": "cliproxyapi", "container": "testbox", "creation-token": "a" * 32,
                "snapshot-digest": "b" * 64, "image-digest": IMAGE_ID}
        record = {"name": "testbox", "branch": "topic", "podman-id": CID,
                  "image-digest": IMAGE_ID, "retired": False, "agent-template": dict(meta)}
        labels = {common.CONTAINER_LABEL: str(common.CONTRACT), common.TOKEN_LABEL: "a" * 32,
                  common.DIGEST_LABEL: "b" * 64, "sandbox-worktree.repo": str(self.root / "repo"),
                  "sandbox-worktree.mother": "topic", "sandbox-worktree.name": "testbox"}
        if not labels_ok:
            labels[common.TOKEN_LABEL] = "c" * 32
        detail = {"Id": CID, "Image": image, "ImageDigest": digest, "Name": "/testbox",
                  "State": {"Status": "running"}, "Config": {"Labels": labels}}
        runtime = {"repo": str(self.root / "repo"), "agent-template": meta, "containers": [record]}
        return runtime, record, detail

    def test_bound_container_image_requires_guard_and_matching_digest(self):
        container_id = "sha256:" + "c" * 64
        for digest, ok in ((IMAGE_ID, True), ("sha256:" + "d" * 64, False)):
            with self.subTest(container_digest=digest):
                runtime, record, detail = self.record_and_runtime(image=container_id, digest=digest)
                calls = []

                def fake_run(command, **kwargs):
                    calls.append(command)
                    return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")

                image = {"ref": "localhost/x:1", "digest": IMAGE_ID}
                with mock.patch.object(self.swt, "run", fake_run):
                    binding = self.swt.verified_container_image(runtime, record, "testbox")
                    self.assertIsNotNone(binding)
                    if ok:
                        self.assertEqual(self.swt.resolve_image_pin(image, binding=binding), container_id)
                    else:
                        with self.assertRaises(self.swt.PreconditionError) as error:
                            self.swt.resolve_image_pin(image, binding=binding)
                        self.assertIn("ImageDigest", str(error.exception))

    def test_historical_bare_id_record_is_resolved_and_not_rewritten(self):
        # 旧版 image_digest 在 .Digest 缺失时保存裸 .Id: 记录值是 64 位裸 ID.
        bare = "a" * 64
        image = {"ref": "localhost/x:1", "digest": bare}
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            if command[:3] == ["podman", "image", "inspect"]:
                if command[3] == f"localhost/x@{IMAGE_ID}":
                    return subprocess.CompletedProcess(command, 1, "", "image not known")
                if command[3] == IMAGE_ID:
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                return subprocess.CompletedProcess(command, 1, "", "image not known")
            raise AssertionError("未预期的命令: " + " ".join(command))

        with mock.patch.object(self.swt, "run", fake_run):
            self.assertEqual(self.swt.resolve_image_pin(image), IMAGE_ID)
        # repo@digest 用带前缀形态; 未改动记录里的原始 digest.
        self.assertIn(f"localhost/x@{IMAGE_ID}", [command[3] for command in calls])
        self.assertEqual(image["digest"], bare)

    def test_historical_bare_id_confirmed_by_bound_container_image(self):
        bare = "a" * 64
        manifest = "sha256:" + "e" * 64
        runtime, record, detail = self.record_and_runtime(image=bare, digest=manifest)
        image = {"ref": "localhost/x:1", "digest": bare}

        def fake_run(command, **kwargs):
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
            raise AssertionError("历史 ID 已被容器 Image 确认, 不该再解析: " + " ".join(command))

        with mock.patch.object(self.swt, "run", fake_run):
            binding = self.swt.verified_container_image(runtime, record, "testbox")
            # 容器 ImageDigest 是 manifest digest, 与裸历史 ID 不同名空间; Image ID 相符即确认.
            self.assertEqual(self.swt.resolve_image_pin(image, binding=binding), "sha256:" + bare)

    def test_historical_bare_id_mismatching_container_still_rejected(self):
        bare = "a" * 64
        runtime, record, detail = self.record_and_runtime(image="b" * 64, digest="sha256:" + "e" * 64)
        image = {"ref": "localhost/x:1", "digest": bare}

        def fake_run(command, **kwargs):
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
            return subprocess.CompletedProcess(command, 1, "", "not found")

        with mock.patch.object(self.swt, "run", fake_run):
            binding = self.swt.verified_container_image(runtime, record, "testbox")
            with self.assertRaises(self.swt.PreconditionError) as error:
                self.swt.resolve_image_pin(image, binding=binding)
        self.assertIn("不接管该容器", str(error.exception))
        self.assertNotIn("b" * 64, str(error.exception).split("ImageDigest")[0])

    def test_historical_id_not_reported_as_newer_candidate(self):
        runtime = {"containers": [{"state": "running", "image-digest": "a" * 64}]}
        same = self.swt.mark_newer_available({"digest": IMAGE_ID}, runtime)
        self.assertFalse(same["newer-available"])
        other = self.swt.mark_newer_available({"digest": "sha256:" + "b" * 64}, runtime)
        self.assertTrue(other["newer-available"])

    def test_record_digest_matches_manifest_or_historical_id(self):
        identity = {"digest": "sha256:" + "e" * 64, "pin": "sha256:" + "a" * 64}
        self.assertTrue(self.swt.image_matches_record("sha256:" + "e" * 64, identity))
        self.assertTrue(self.swt.image_matches_record("a" * 64, identity))
        self.assertTrue(self.swt.image_matches_record("sha256:" + "a" * 64, identity))
        self.assertFalse(self.swt.image_matches_record("b" * 64, identity))
        self.assertFalse(self.swt.image_matches_record(None, identity))
        self.assertFalse(self.swt.image_matches_record("garbage", identity))

    def test_same_named_foreign_container_is_rejected_as_candidate(self):
        runtime, record, detail = self.record_and_runtime(labels_ok=False)
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
            if command[:3] == ["podman", "image", "inspect"]:
                if command[3] == f"localhost/x@{IMAGE_ID}":
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                return subprocess.CompletedProcess(command, 1, "", "image not known")
            raise AssertionError("未预期的命令: " + " ".join(command))

        with mock.patch.object(self.swt, "run", fake_run):
            self.assertIsNone(self.swt.verified_container_image(runtime, record, "testbox"))
            resolved = self.swt.resolve_image_pin({"ref": "localhost/x:1", "digest": IMAGE_ID})
        self.assertEqual(resolved, IMAGE_ID)
        # 用了 repo@digest, 没有采用同名容器的 Image.
        self.assertIn(f"localhost/x@{IMAGE_ID}", [command[3] for command in calls if command[:3] == ["podman", "image", "inspect"]])

    def test_bound_container_without_imagedigest_needs_cross_check(self):
        container_id = "sha256:" + "c" * 64
        # a) 按 ID 读到的 digest 与记录吻合 → 可用.
        runtime, record, detail = self.record_and_runtime(image=container_id, digest="")
        image = {"ref": "localhost/x:1", "digest": IMAGE_ID}

        def fake_run(command, **kwargs):
            if command[:2] == ["podman", "inspect"] and "--format" in command:
                # 按镜像 ID 单次读: digest 与记录吻合.
                return subprocess.CompletedProcess(command, 0, IMAGE_ID + "@@" + container_id + "\n", "")
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
            return subprocess.CompletedProcess(command, 1, "", "image not known")

        with mock.patch.object(self.swt, "run", fake_run):
            binding = self.swt.verified_container_image(runtime, record, "testbox")
            self.assertEqual(self.swt.resolve_image_pin(image, binding=binding), container_id)

        # b) 交叉核对都不成立 → 不采用容器 Image, 改走 repo@digest.
        resolved_calls = []

        def fake_run_b(command, **kwargs):
            resolved_calls.append(command)
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
            if command[:3] == ["podman", "image", "inspect"]:
                if command[3] == f"localhost/x@{IMAGE_ID}":
                    return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
                return subprocess.CompletedProcess(command, 1, "", "image not known")
            return subprocess.CompletedProcess(command, 1, "", "not found")

        with mock.patch.object(self.swt, "run", fake_run_b):
            binding = self.swt.verified_container_image(runtime, record, "testbox")
            self.assertEqual(self.swt.resolve_image_pin(image, binding=binding), IMAGE_ID)
        self.assertFalse(any(container_id in command for command in resolved_calls if command[:3] == ["podman", "image", "inspect"]))

        # c) 交叉核对不成立且 digest 也解析不出 → 停 (不用未验证的容器 Image).
        def fake_run_c(command, **kwargs):
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
            return subprocess.CompletedProcess(command, 1, "", "not found")

        with mock.patch.object(self.swt, "run", fake_run_c):
            binding = self.swt.verified_container_image(runtime, record, "testbox")
            with self.assertRaises(self.swt.PreconditionError):
                self.swt.resolve_image_pin(image, binding=binding)

    def test_tag_read_used_only_when_digest_matches_exactly(self):
        for current in (IMAGE_ID, "sha256:" + "e" * 64):
            with self.subTest(current_tag_digest=current):
                def fake_run(command, **kwargs):
                    if command[:3] == ["podman", "image", "inspect"]:
                        return subprocess.CompletedProcess(command, 1, "", "image not known")
                    if command[:2] == ["podman", "inspect"] and "--format" in command:
                        return subprocess.CompletedProcess(command, 0, f"{current}@@{IMAGE_ID}\n", "")
                    raise AssertionError("未预期的命令: " + " ".join(command))

                image = {"ref": "localhost/x:1", "digest": IMAGE_ID}
                with mock.patch.object(self.swt, "run", fake_run):
                    if current == IMAGE_ID:
                        self.assertEqual(self.swt.resolve_image_pin(image), IMAGE_ID)
                    else:
                        with self.assertRaises(self.swt.PreconditionError) as error:
                            self.swt.resolve_image_pin(image)
                        self.assertIn("不用可变 tag 代替", str(error.exception))

    def test_old_record_with_unresolvable_digest_stops_instead_of_using_tag(self):
        cases = ({"ref": "localhost/x:1", "digest": "sha256:" + "b" * 64}, {"ref": "localhost/x:1"})
        for image in cases:
            with self.subTest(image=image):
                def fake_run(command, **kwargs):
                    return subprocess.CompletedProcess(command, 1, "", "no such image")

                with mock.patch.object(self.swt, "run", fake_run):
                    with self.assertRaises(self.swt.PreconditionError) as error:
                        self.swt.resolve_image_pin(image)
                self.assertNotIn("localhost/x:1", str(error.exception))

    def test_single_inspect_reads_digest_and_id_together(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "sha256:digest@@" + IMAGE_ID + "\n", "")

        tag = "localhost/x:1"
        with mock.patch.object(self.swt, "run", fake_run):
            image = self.swt.prepare_image(
                self.swt.parse_args(["birth", "--repo", str(self.root), "--records-root",
                                     str(self.root / "records"), "--image", tag]),
                self.root, self.root / "records")
        self.assertEqual(len(calls), 1, "同一次选择只读一次镜像, 避免 digest 与 ID 对到不同镜像")
        self.assertEqual(image, {"ref": tag, "digest": "sha256:digest", "pin": IMAGE_ID,
                                 "verdict": "EXPLICIT", "newer-available": False})

    def test_reuse_match_digest_must_equal_current_read(self):
        tag = "localhost/x:1"
        for reported in ("sha256:digest", "sha256:" + "c" * 64):
            with self.subTest(reported=reported):
                def fake_run(command, **kwargs):
                    if command[:3] == ["podman", "inspect", tag]:
                        return subprocess.CompletedProcess(command, 0, "sha256:digest@@" + IMAGE_ID + "\n", "")
                    if command[:2] == ["uv", "run"]:
                        return subprocess.CompletedProcess(
                            command, 0, f"verdict=REUSE\nimage={tag}\ndigest={reported}\n", "")
                    raise AssertionError("未预期的命令: " + " ".join(command))

                requirements = self.root / "requirements.md"
                requirements.write_text("python3\n", encoding="utf-8")
                args = self.swt.parse_args(["birth", "--repo", str(self.root), "--records-root",
                                            str(self.root / "records"), "--requirements", str(requirements)])
                with mock.patch.object(self.swt, "run", fake_run):
                    if reported == "sha256:digest":
                        image = self.swt.prepare_image(args, self.root, self.root / "records")
                        self.assertEqual(image["pin"], IMAGE_ID)
                    else:
                        with self.assertRaises(self.swt.PreconditionError) as error:
                            self.swt.prepare_image(args, self.root, self.root / "records")
                        self.assertIn("重指", str(error.exception))

    def test_create_uses_pinned_image_id_not_mutable_tag(self):
        tag = "localhost/x:1"
        commands = []
        image = {"ref": tag, "digest": IMAGE_ID, "pin": IMAGE_ID, "verdict": "EXPLICIT"}

        def fake_run(command, **kwargs):
            commands.append(command)
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 1, "", "no such container")
            return subprocess.CompletedProcess(command, 0, "", "")

        args = self.swt.parse_args(["birth", "--name", "testbox", "--hostname", "testbox"])
        runtime = {"containers": [], "agent-template": None}
        runtime_file = self.root / "records/runtime/unit.json"
        with mock.patch.object(self.swt, "run", fake_run), \
                mock.patch.object(self.swt, "host_port_free", return_value=False), \
                mock.patch.object(self.swt, "host_wayland_socket", return_value=None), \
                mock.patch.object(self.swt, "stage_agent_prompts", return_value=self.root / "prompts"), \
                mock.patch.object(self.swt, "assert_skills_mountable", return_value=[]), \
                mock.patch.object(self.swt, "assert_llm_select_mountable", return_value=False), \
                mock.patch.object(self.swt, "stage_maven_settings", return_value=None), \
                mock.patch.object(self.swt, "inspect_container", return_value={"Id": CID}), \
                mock.patch.object(self.swt, "refresh_container", return_value={"name": "testbox", "record": {}}):
            self.swt.create_and_start_container(
                args, self.root / "repo", image, "topic", runtime, runtime_file, {}, self.root, "unit")
        create = next(command for command in commands if command[:2] == ["podman", "create"])
        self.assertEqual(create[-1], IMAGE_ID)
        self.assertNotIn(tag, create)

    def test_old_record_create_resolves_digest_instead_of_tag(self):
        tag = "localhost/x:1"
        commands = []
        image = {"ref": tag, "digest": IMAGE_ID}

        def fake_run(command, **kwargs):
            commands.append(command)
            if command[:3] == ["podman", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
            if command[:2] == ["podman", "inspect"]:
                return subprocess.CompletedProcess(command, 1, "", "no such container")
            return subprocess.CompletedProcess(command, 0, "", "")

        args = self.swt.parse_args(["birth", "--name", "testbox", "--hostname", "testbox"])
        runtime = {"containers": [], "agent-template": None}
        with mock.patch.object(self.swt, "run", fake_run), \
                mock.patch.object(self.swt, "inspect_container", return_value={"Id": CID}), \
                mock.patch.object(self.swt, "refresh_container", return_value={"name": "testbox", "record": {}}):
            self.swt.create_and_start_container(
                args, self.root / "repo", image, "topic", runtime,
                self.root / "records/runtime/unit.json", {}, self.root, "unit")
        create = next(command for command in commands if command[:2] == ["podman", "create"])
        self.assertEqual(create[-1], IMAGE_ID)
        self.assertNotIn(tag, create)
        self.assertTrue(any(command[:3] == ["podman", "image", "inspect"] for command in commands))

    def test_existing_container_image_binding_is_verified_not_by_tag(self):
        image = {"ref": "localhost/x:1", "digest": IMAGE_ID, "pin": IMAGE_ID}
        for container_image in ("a" * 64, "d" * 64):
            with self.subTest(container_image=container_image):
                detail = {"Id": CID, "Image": container_image, "Name": "/testbox",
                          "State": {"Status": "running"},
                          "Config": {"Labels": {common.CONTAINER_LABEL: str(common.CONTRACT),
                             common.TOKEN_LABEL: "a" * 32, common.DIGEST_LABEL: "b" * 64,
                             "sandbox-worktree.repo": str(self.root / "repo"),
                             "sandbox-worktree.mother": "topic",
                             "sandbox-worktree.name": "testbox"}}}
                meta = {"name": "cliproxyapi", "container": "testbox", "creation-token": "a" * 32,
                        "snapshot-digest": "b" * 64, "image-digest": IMAGE_ID}
                record = {"name": "testbox", "branch": "topic", "podman-id": CID,
                          "image-digest": IMAGE_ID, "retired": False, "agent-template": dict(meta)}
                runtime = {"repo": str(self.root / "repo"), "agent-template": meta, "containers": [record]}

                def fake_run(command, **kwargs):
                    if command[:2] == ["podman", "inspect"]:
                        return subprocess.CompletedProcess(command, 0, json.dumps([detail]), "")
                    return subprocess.CompletedProcess(command, 0, "", "")

                args = self.swt.parse_args(["birth", "--name", "testbox", "--hostname", "testbox"])
                with mock.patch.object(self.swt, "run", fake_run), \
                        mock.patch.object(self.swt, "refresh_container", return_value={"name": "testbox"}):
                    if container_image == "a" * 64:
                        self.swt.create_and_start_container(
                            args, self.root / "repo", image, "topic", runtime,
                            self.root / "records/runtime/unit.json", {}, self.root, "unit")
                    else:
                        with self.assertRaises(self.swt.PreconditionError) as error:
                            self.swt.create_and_start_container(
                                args, self.root / "repo", image, "topic", runtime,
                                self.root / "records/runtime/unit.json", {}, self.root, "unit")
                        self.assertIn("实际镜像与本次创建记录不同", str(error.exception))


class ResumeTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.swt = load_script("swt_agent_resume_test", "swt.py")
        self.state, self.detail = self.binding()
        self.state["mother"] = {"branch": "topic", "dir": str(self.root / "mother")}
        self.state["stage"] = "born"
        self.state["agent-template"]["status"] = "verified"
        self.state["containers"][0]["agent-template"] = dict(self.state["agent-template"])
        self.state["containers"][0]["state"] = "running"
        self.records = self.root / "records"
        self.file = self.records / "runtime/unit.json"
        self.args = self.swt.parse_args(["resume", "--records-root", str(self.records), "--name", "testbox"])

    def test_uninitialized_resume_never_installs_or_reads_host_auth(self):
        self.state["agent-template"]["status"] = "failed"
        with mock.patch.object(self.swt, "locate_pair_runtime", return_value=(self.file, self.state)), mock.patch.object(template, "operate", side_effect=AssertionError("must not install")), mock.patch.object(self.swt, "inject_auth_json", side_effect=AssertionError("must not copy OAuth")):
            with self.assertRaises(self.swt.PreconditionError):
                self.swt.resume(self.args, Path(self.state["repo"]))

    def test_new_and_old_ready_resume_are_separate(self):
        for legacy in (False, True):
            state = copy.deepcopy(self.state)
            if legacy:
                state.pop("agent-template")
                state["containers"][0].pop("agent-template")
            with self.subTest(legacy=legacy), contextlib.ExitStack() as stack:
                stubs = {"locate_pair_runtime": (self.file, state), "legacy_pair_branches": [],
                         "load_repo_runtimes": [(self.file, state)], "podman_container_state": state["containers"],
                         "daemon_state": {}, "resume_daemon_stale": False, "git_bridge_ready": True,
                         "resume_network_status": (True, ""), "resume_git_ready": True,
                         "resume_decision_fingerprint": {}, "ensure_display_after_resume": "absent",
                         "ensure_host_display": "absent", "build_state": {}, "print_delivery_lines": None,
                         "print_state": None, "ensure_herdr_machine": None}
                mocks = {name: stack.enter_context(mock.patch.object(self.swt, name, return_value=value)) for name, value in stubs.items()}
                stack.enter_context(mock.patch.object(self.swt, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps([self.detail]), "")))
                auth = stack.enter_context(mock.patch.object(self.swt, "inject_auth_json", side_effect=AssertionError("no OAuth update on ready resume")))
                operate = stack.enter_context(mock.patch.object(template, "operate", return_value={"ok": True}))
                stack.enter_context(mock.patch.object(template, "target"))
                self.assertEqual(self.swt.resume(self.args, Path(state["repo"])), 0)
                auth.assert_not_called()
                mocks["ensure_herdr_machine"].assert_called_once()
                self.assertEqual(mocks["ensure_herdr_machine"].call_args.args[-1]["name"], "testbox")
                if legacy:
                    operate.assert_not_called()
                    self.assertIsNone(mocks["podman_container_state"].call_args.kwargs["only_name"])
                else:
                    self.assertFalse(operate.call_args.kwargs["install"])
                    self.assertEqual(mocks["podman_container_state"].call_args.kwargs["only_name"], "testbox")


class ObservationTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.swt = load_script("swt_agent_observation_test", "swt.py")

    def test_template_network_status_queries_only_current_target_netns(self):
        state, detail = self.binding()
        detail["NetworkSettings"] = {"SandboxKey": "/run/netns/new-target"}
        state["network"] = {"mode": "whitelist", "gateway": "192.0.2.1", "allow": [], "deny": []}
        with mock.patch.object(template, "target", return_value=(state["containers"][0], detail, CID)) as target, \
             mock.patch.object(self.swt, "run", return_value=subprocess.CompletedProcess([], 0, "table inet swt {}", "")) as run:
            observed = self.swt.network_state(state)
        target.assert_called_once_with(state, "testbox")
        self.assertTrue(observed["table-present"])
        self.assertEqual(run.call_args.args[0][-2:], ["--netns", "/run/netns/new-target"])

    def test_display_verifier_detects_the_actual_wayland_mount_path(self):
        display = load_script("swt_agent_display_observation_test", "swt-display.py")
        args = type("Args", (), {"name": "testbox"})()
        with mock.patch.object(display, "_podman", side_effect=RuntimeError("stop after mount query")) as podman:
            with self.assertRaisesRegex(RuntimeError, "stop after mount query"):
                display.cmd_verify(args)
        self.assertEqual(podman.call_args.args[0], ["exec", "testbox", "test", "-e", "/run/swt-wayland/wayland-0"])

    def test_already_connected_host_display_is_rechecked_not_reported_absent(self):
        for status in ("ok", "degraded"):
            state, _ = self.binding()
            record = state["containers"][0]
            record["host-display"] = status
            with mock.patch.object(self.swt, "host_wayland_socket", return_value=None), \
                 mock.patch.object(self.swt, "host_display_probe", return_value=(True, "connect-ok")) as probe, \
                 mock.patch.object(self.swt, "relax_host_wayland_perms", side_effect=AssertionError("must not chmod host")):
                result = self.swt.ensure_host_display(state, self.root / "runtime.json", record)
            self.assertEqual(result, "ok")
            probe.assert_called_once_with("testbox")


class ImageTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.image = load_script("swt_agent_image_test", "image-prep.py")

    def test_public_staging_excludes_credentials_routes_trust_and_template_data(self):
        skills = self.root / "skills"
        (skills / "use-sandbox-worktree/agent-templates/cliproxyapi").mkdir(parents=True)
        (skills / "use-sandbox-worktree/agent-templates/cliproxyapi/template.json").write_text("route-data")
        pi_dir = self.root / "pi"
        pi_dir.mkdir()
        for name in ("auth.json", "models.json", "trust.json", "unknown-secret.json"):
            (pi_dir / name).write_text(KEY)
        (pi_dir / "settings.json").write_text(json.dumps({"defaultProvider": "old", "defaultModel": "old", "defaultProjectTrust": "always", "httpProxy": KEY, "theme": "system"}))
        context = self.root / "context"
        self.image.stage_context(context, skills, pi_dir)
        staged = context / "pi-agent"
        self.assertEqual(json.loads((staged / "settings.json").read_text()), {"theme": "system"})
        self.assertFalse((context / "skills/use-sandbox-worktree/agent-templates").exists())
        for path in staged.rglob("*"):
            if path.is_file():
                self.assertNotIn(KEY, path.read_text())

    def test_child_cannot_relabel_old_parent_as_compatible(self):
        with mock.patch.object(self.image, "image_inspect", return_value="1"), mock.patch.object(self.image, "podman_build", side_effect=AssertionError("must not build")):
            with self.assertRaises(self.image.EnvError):
                self.image._build_child_layer(kind="display", slug="display", project_id="display", parent_ref="old", parent_digest="sha256:old", parent_build_id="old", parent_image_id="old", requirements_text="", entries=[], records_root=self.root, image_ref_prefix="test")


if __name__ == "__main__":
    unittest.main()
