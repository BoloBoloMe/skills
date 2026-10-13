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
        detail = {"Id": CID, "Name": "/testbox", "State": {"Status": "running"},
                  "Config": {"Labels": {common.CONTAINER_LABEL: str(common.CONTRACT),
                     common.TOKEN_LABEL: meta["creation-token"], common.DIGEST_LABEL: meta["snapshot-digest"],
                     "sandbox-worktree.repo": state["repo"], "sandbox-worktree.mother": "topic",
                     "sandbox-worktree.name": "testbox"}}}
        return state, detail


class DataTests(TemporaryCase):
    def test_deterministic_and_native_catalog_consumed(self):
        self.assertEqual(template.snapshot(self.bundle), template.snapshot(copy.deepcopy(self.bundle)))
        files = self.value["files"]
        codex = tomllib.loads(files[".codex/config.toml"])
        self.assertEqual(codex["model_catalog_json"], "/home/bolo/.codex/models.json")
        catalog = json.loads(files[".codex/models.json"])
        self.assertEqual(len(catalog["models"]), 7)
        self.assertTrue(all(m["upgrade"] is None and not m["prefer_websockets"] for m in catalog["models"]))
        kimi = tomllib.loads(files[".kimi-code/config.toml"])
        self.assertEqual(kimi["default_model"], "cliproxy-chat/glm-5.3")
        self.assertEqual(len(kimi["models"]), 11)
        self.assertEqual({p["base_url"] for p in kimi["providers"].values()}, {self.bundle["template"]["base_url"]})
        self.assertNotIn(KEY, json.dumps(self.value))
        self.assertNotIn(MANAGEMENT, json.dumps(self.value))

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
        first = template.creation(self.root / "snapshot.json", self.bundle, "testbox", "sha256:fake")
        changed = copy.deepcopy(self.bundle)
        changed["template"]["version"] = "next"
        second = template.creation(self.root / "snapshot.json", changed, "testbox", "sha256:fake")
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        self.assertNotEqual(first["creation-token"], second["creation-token"])
        self.assertEqual(template.read_snapshot(Path(first["snapshot"]))["template"]["version"], "2026-10-13.1")

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

    def test_real_entrypoint_for_each_client_uses_env_not_argv(self):
        self.installed()
        common.safe_write(self.home / common.READY_PATH, common.pretty({"contract": common.CONTRACT, "snapshot-digest": self.value["snapshot-digest"]}), mode=0o644)
        for cli in ("pi", "codex", "kimi"):
            observed = {}
            def fake_exec(binary, argv, env):
                observed.update(binary=binary, argv=argv, env=env)
            with mock.patch.object(launch, "HOME", self.home), mock.patch.object(launch.os, "execve", fake_exec):
                launch.main([cli, "--no-session"])
            self.assertEqual(observed["env"][common.KEY_ENV], KEY)
            self.assertNotIn(KEY, " ".join(observed["argv"]))
            self.assertIn(cli, observed["binary"])

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


@unittest.skipUnless(shutil.which("pi"), "没有主机 Pi, 真实解析验收留给新测试容器")
class PiParserTests(TemporaryCase):
    def test_actual_pi_parser_and_auth_resolver_in_private_home(self):
        self.installed()
        env = common.client_env({"PATH": os.environ["PATH"], "TERM": "dumb"}, KEY, home=self.home)
        flags = ["--offline", "--no-extensions", "--no-mcp", "--no-skills", "--no-prompt-templates", "--no-context-files", "--no-approve"]
        listed = subprocess.run([shutil.which("pi"), *flags, "--list-models", "cli"], cwd=self.home, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(listed.returncode, 0, "Pi 真实解析失败, 原始输出不打印")
        for model in self.bundle["catalog"]["models"]:
            self.assertIn(model["id"], listed.stdout, "Pi 未列出模板模型")
        auth = subprocess.run([shutil.which("pi"), "auth", "check", "--provider", "cli", "--json", "--offline"], cwd=self.home, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(auth.returncode, 0, "Pi 凭据解析失败, 原始输出不打印")
        self.assertNotIn(KEY, auth.stdout + auth.stderr)
        self.assertEqual(json.loads(auth.stdout)["status"], "ready")


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
                 "prepare_image": {"ref": "fake:image", "digest": "sha256:fake", "verdict": "EXPLICIT"},
                 "decision_fingerprint": {"repo": str(self.repo), "image-digest": "sha256:fake"},
                 "print_birth_state": None, "print_delivery_lines": None}
        for name, value in basic.items():
            self.stack.enter_context(mock.patch.object(self.swt, name, return_value=value))
        for name in ("create_mother_worktree", "configure_repo", "start_daemon", "create_and_start_container", "migrate_legacy_pairs", "inject_auth_json"):
            self.resources[name] = self.stack.enter_context(mock.patch.object(self.swt, name, side_effect=AssertionError("resource mutation before gate: " + name)))
        self.stack.enter_context(mock.patch.object(template, "load", return_value=self.bundle))
        self.stack.enter_context(mock.patch.object(template, "choices", return_value=[template.summary(self.bundle)]))
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

    def test_verified_birth_reentry_uses_frozen_snapshot_not_latest_template(self):
        meta = template.creation(self.root / "snapshot.json", self.bundle, "testbox", "sha256:fake")
        meta.update(status="verified", hostname="testbox")
        state = {"stage": "born", "repo": str(self.repo), "mother": {"dir": str(self.mother), "branch": "topic"},
                 "mother_dir": str(self.mother), "image": {"ref": "fake:image", "digest": "sha256:fake"},
                 "network": {"mode": "whitelist", "allow": [], "deny": []}, "agent-template": meta,
                 "containers": [{"name": "testbox", "agent-template": dict(meta)}]}
        self.swt.atomic_write_json(self.runtime_file, state)
        with mock.patch.object(template, "target"), mock.patch.object(template, "operate", return_value={"ok": True}) as operate, mock.patch.object(template, "load", side_effect=AssertionError("latest template read")), mock.patch.object(template, "credential", side_effect=AssertionError("host key read")):
            self.assertEqual(self.swt.birth(self.args(), self.repo), 0)
        self.assertFalse(operate.call_args.kwargs["install"])
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
                            swt.create_and_start_container(args, Path(state["repo"]), {"ref": "fake", "digest": "sha256:fake"}, "topic", state, file, {}, self.root, "unit")
                        refresh.assert_not_called()
                        self.assertFalse(file.exists())
                    else:
                        result = swt.create_and_start_container(args, Path(state["repo"]), {"ref": "fake", "digest": "sha256:fake"}, "topic", state, file, {}, self.root, "unit")
                        self.assertEqual(result["record"]["podman-id"], CID)
                        self.assertEqual(json.loads(file.read_text())["containers"][0]["podman-id"], CID)


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
                         "print_state": None}
                mocks = {name: stack.enter_context(mock.patch.object(self.swt, name, return_value=value)) for name, value in stubs.items()}
                stack.enter_context(mock.patch.object(self.swt, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps([self.detail]), "")))
                auth = stack.enter_context(mock.patch.object(self.swt, "inject_auth_json", side_effect=AssertionError("no OAuth update on ready resume")))
                operate = stack.enter_context(mock.patch.object(template, "operate", return_value={"ok": True}))
                stack.enter_context(mock.patch.object(template, "target"))
                self.assertEqual(self.swt.resume(self.args, Path(state["repo"])), 0)
                auth.assert_not_called()
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
