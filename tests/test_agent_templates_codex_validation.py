"""Codex 模板验收回归, 默认仅临时目录/假 Key/模拟子进程.

真实容器用例须显式设置 SWT_AGENT_PARSER_IMAGE, 不加载 pytest 清理 hooks.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "workflow/use-sandbox-worktree/scripts"
sys.path.insert(0, str(SCRIPTS))
from agent_config import common, runtime, template

KEY = "fake-codex-validation-client-key-12345678"


class CodexValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="swt-codex-validation-")
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.owner = (os.getuid(), os.getgid())
        value = template.snapshot(template.load("cliproxyapi"))
        runtime.install_payload({"snapshot": value, "client_api_key": KEY}, self.home, self.owner)
        self.calls = []

    def run_clients(self, *, fail=False):
        def captured(cmd, **kwargs):
            self.calls.append((cmd, kwargs))
            code = 1 if fail and Path(cmd[0]).name == "codex" else 0
            return subprocess.CompletedProcess(cmd, code, KEY, KEY)
        with mock.patch.object(runtime, "HOME", self.home), \
             mock.patch.object(runtime.subprocess, "run", captured), \
             mock.patch.dict(os.environ, {}, clear=True):
            runtime.check_clients(KEY, self.owner)

    def test_codex_uses_local_configuration_and_catalog_parser_not_doctor(self):
        self.run_clients()
        commands = [cmd for cmd, _ in self.calls if Path(cmd[0]).name == "codex"]
        self.assertEqual(commands, [[str(runtime.REAL_BIN_DIR / "codex"), "features", "list"]])
        for cmd, options in self.calls:
            self.assertNotIn(KEY, " ".join(cmd))
            self.assertEqual(options["env"][common.KEY_ENV], KEY)
            self.assertEqual(options["cwd"], str(self.home))
            self.assertEqual(options["user"], self.owner[0])
            self.assertEqual(options["group"], self.owner[1])

    def test_native_parser_failure_is_not_ignored_and_diagnostics_are_hidden(self):
        with self.assertRaises(common.TemplateError) as error:
            self.run_clients(fail=True)
        self.assertEqual(str(error.exception), "codex 真实配置解析/凭据检查未通过")
        self.assertNotIn(KEY, str(error.exception))
        self.assertNotIn("kimi", [Path(cmd[0]).name for cmd, _ in self.calls])


# 在一次性断网容器内启动回环模拟网关, 真实执行三个客户端的解析入口.
# Key/快照只从 stdin 进入, 不复制任何主机配置/凭据或调用真实网关.
CONTAINER_CHECK = r'''
import contextlib
import io
import json
import os
import pwd
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0, "/opt/swt-agent-config")
from agent_config import common, runtime

payload = json.load(sys.stdin)
value = payload["snapshot"]
key = payload["client_api_key"]
user = pwd.getpwnam("bolo")
owner = (user.pw_uid, user.pw_gid)
requests = []

class Gateway(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        authorized = self.headers.get("Authorization") == "Bearer " + key
        requests.append(["GET", self.path, authorized])
        accepted = authorized and self.path == "/v1/models"
        self.send_response(200 if accepted else 403)
        self.end_headers()
        self.wfile.write(json.dumps({"data": [{"id": m["id"]} for m in value["catalog"]["models"]]}).encode())
    def do_HEAD(self):
        requests.append(["HEAD", self.path, False])
        self.send_response(405)
        self.end_headers()
    def do_POST(self):
        requests.append(["POST", self.path, False])
        self.send_response(405)
        self.end_headers()

server = ThreadingHTTPServer(("127.0.0.1", 18761), Gateway)
threading.Thread(target=server.serve_forever, daemon=True).start()

def action(command):
    original = sys.stdin
    captured = io.StringIO()
    try:
        sys.stdin = io.StringIO(common.canonical(payload))
        with contextlib.redirect_stdout(captured):
            code = runtime.main([command])
    finally:
        sys.stdin = original
    if code != 0:
        raise RuntimeError("native client acceptance failed: " + command)
    return json.loads(captured.getvalue())

try:
    installed = action("install")
    paths = [p for p in value["files"] if p != runtime.OVERLAY]
    paths += [".pi/agent/settings.json", common.KEY_PATH, common.SNAPSHOT_PATH, common.READY_PATH]
    before = {p: ((common.HOME / p).read_bytes(), (common.HOME / p).stat().st_mtime_ns) for p in paths}
    checked = action("check")
    after = {p: ((common.HOME / p).read_bytes(), (common.HOME / p).stat().st_mtime_ns) for p in paths}
    if before != after:
        raise RuntimeError("check rewrote installed configuration or credential")

    env = common.client_env({"PATH": os.environ["PATH"], "TERM": "dumb"}, key)
    def native(cli, args):
        return subprocess.run([str(runtime.REAL_BIN_DIR / cli), *args], env=env,
                              cwd=str(common.HOME), user=owner[0], group=owner[1],
                              capture_output=True, text=True, timeout=45)
    versions = {}
    for cli in ("pi", "codex", "kimi"):
        result = native(cli, ["--version"])
        if result.returncode != 0 or key in result.stdout + result.stderr:
            raise RuntimeError("invalid or unredacted client version result")
        versions[cli] = result.stdout.strip()

    config = common.HOME / ".codex/config.toml"
    catalog = common.HOME / ".codex/models.json"
    originals = {p: p.read_text() for p in (config, catalog)}
    parser_checks = []
    try:
        common.safe_write(config, 'model = ["invalid-type"]\n', owner=owner)
        if native("codex", ["features", "list"]).returncode == 0:
            raise RuntimeError("Codex accepted invalid configuration")
        parser_checks.append("invalid-config-rejected")
        common.safe_write(config, originals[config], owner=owner)
        common.safe_write(catalog, '{"models":[{"slug":"missing-native-fields"}]}', owner=owner)
        if native("codex", ["features", "list"]).returncode == 0:
            raise RuntimeError("Codex did not parse native model catalog")
        parser_checks.append("invalid-native-catalog-rejected")
    finally:
        for path, text in originals.items():
            common.safe_write(path, text, owner=owner)
    runtime.check_clients(key, owner)
    if requests != [["GET", "/v1/models", True], ["GET", "/v1/models", True]]:
        raise RuntimeError("unexpected gateway requests during local parsing")
    print(json.dumps({"ok": True, "versions": versions, "requests": requests,
                      "parser-checks": parser_checks, "reentry-unchanged": before == after,
                      "installed": installed, "checked": checked}, separators=(",", ":")))
finally:
    server.shutdown()
    server.server_close()
'''


@unittest.skipUnless(os.environ.get("SWT_AGENT_PARSER_IMAGE"), "真实容器验收须显式指定已批准的本地镜像")
class NativeContainerValidationTests(unittest.TestCase):
    def test_native_install_check_and_codex_parser_in_disposable_offline_container(self):
        image = os.environ["SWT_AGENT_PARSER_IMAGE"]
        marker = subprocess.run(["podman", "image", "inspect", image, "--format",
                                 '{{index .Labels "' + common.CONTRACT_LABEL + '"}}'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(marker.returncode, 0, "验收镜像须已存在, 不拉取/构建镜像")
        self.assertEqual(marker.stdout.strip(), str(common.CONTRACT))
        bundle = template.load("cliproxyapi")
        bundle["template"]["base_url"] = "http://127.0.0.1:18761/v1"
        value = template.snapshot(bundle)
        token = secrets.token_hex(16)
        name = "swt-parser-check-" + token[:12]
        label = "sandbox-worktree.parser-test"
        payload = {"snapshot": value, "client_api_key": KEY,
                   "binding": {"creation-token": token, "container-id": "a" * 64}}
        with tempfile.TemporaryDirectory(prefix="swt-parser-check-") as directory:
            cid_file = Path(directory) / "container-id"
            command = ["podman", "run", "--rm", "-i", "--pull", "never", "--network", "none",
                       "--user", "root", "--name", name, "--cidfile", str(cid_file),
                       "--label", label + "=" + token,
                       "--env", "PYTHONDONTWRITEBYTECODE=1", "--workdir", str(common.HOME),
                       "--mount", "type=bind,src=" + str(SCRIPTS / "agent_config") +
                       ",dst=" + common.TOOL_DIR + "/agent_config,ro",
                       "--entrypoint", "/usr/local/bin/uv", image,
                       "run", "--no-project", "--offline", "python", "-c", CONTAINER_CHECK]
            try:
                result = subprocess.run(command, input=common.canonical(payload), capture_output=True,
                                        text=True, timeout=180)
            finally:
                # --rm 正常收尾; 超时时只清理本次 cidfile + 标签共同绑定的完整 ID.
                if cid_file.is_file():
                    cid = cid_file.read_text().strip()
                    if re.fullmatch(r"[0-9a-f]{64}", cid):
                        observed = subprocess.run(["podman", "inspect", cid, "--format",
                                                   '{{index .Config.Labels "' + label + '"}}'],
                                                  capture_output=True, text=True, timeout=15)
                        if observed.returncode == 0 and observed.stdout.strip() == token:
                            subprocess.run(["podman", "rm", "-f", cid], capture_output=True, timeout=30)
        self.assertNotIn(KEY, result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, "真实客户端验收失败: " + result.stderr[:2000])
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertTrue(report["reentry-unchanged"])
        self.assertEqual(report["requests"], [["GET", "/v1/models", True]] * 2)
        self.assertEqual(report["parser-checks"], ["invalid-config-rejected", "invalid-native-catalog-rejected"])
        for cli, version in (("pi", "1.2.0"), ("codex", "0.162.1"), ("kimi", "2.1.1")):
            self.assertIn(version, report["versions"][cli])
        for action in ("installed", "checked"):
            self.assertEqual(report[action]["snapshot-digest"], value["snapshot-digest"])
        print("\n真实断网容器验收: " + common.canonical(report))


if __name__ == "__main__":
    unittest.main()
