"""noVNC 本机/局域网直连: URL, 发布范围, 旧回环容器, SSH 缺席与降级.

这里只验证脚本行为与真实 socket 占用检测, 不冒充 Podman/跨设备连通验收.
创建发布参数与映射回读另见 test_swt_web_access.py.
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import socket
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "workflow/use-sandbox-worktree/scripts/swt.py"


def load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestNoVncAccess(unittest.TestCase):
    def setUp(self):
        self.m = load_swt()

    def delivery(self, **overrides):
        args = dict(heading="birth: 已完成", ssh_port=49153, vnc_port=49254,
                    display_status="ok", key_path=None, lan="192.168.1.10",
                    vnc_lan_port=49254)
        args.update(overrides)
        out = io.StringIO()
        with redirect_stdout(out):
            self.m.print_delivery_lines(**args)
        return out.getvalue()

    def test_delivery_has_only_two_direct_novnc_urls_even_without_ssh(self):
        for ssh_port in (49153, None):
            with self.subTest(ssh_port=ssh_port):
                output = self.delivery(ssh_port=ssh_port)
                entries = [line for line in output.splitlines() if line.startswith("[SWT] noVNC")]
                self.assertEqual(entries, [
                    "[SWT] noVNC (本机):   http://127.0.0.1:49254/vnc.html?resize=scale",
                    "[SWT] noVNC (局域网): http://192.168.1.10:49254/vnc.html?resize=scale",
                ])
                self.assertNotIn("-L ", output)
                self.assertNotIn("隧道", output)
                self.assertIn("noVNC 局域网直连无认证", output)
                self.assertNotIn("SSH 为门槛", output)

    def test_unconfirmed_lan_only_local_url_and_reason(self):
        output = self.delivery(lan=None)
        self.assertIn("http://127.0.0.1:49254/vnc.html?resize=scale", output)
        self.assertIn("noVNC (局域网) 未附发: host 局域网地址无已确认值", output)
        self.assertNotIn("http://192.168.", output)
        self.assertNotIn("http://<host-LAN-IP>", output)
        self.assertNotIn("-L ", output)

    def test_legacy_loopback_delivers_local_url_and_rebuild_reason(self):
        output = self.delivery(vnc_lan_port=None)
        self.assertIn("http://127.0.0.1:49254/vnc.html?resize=scale", output)
        self.assertNotIn("http://192.168.1.10:49254", output)
        self.assertIn("旧容器需经确认后重建", output)
        self.assertNotIn("-L ", output)

    def test_no_urls_for_bad_or_absent_display(self):
        for display in ("degraded", "fail", "absent", None):
            with self.subTest(display=display):
                output = self.delivery(display_status=display)
                self.assertNotIn("vnc.html", output)
                self.assertNotIn("隧道", output)
                self.assertNotIn("-L ", output)

    def test_no_urls_without_vnc_mapping(self):
        output = self.delivery(vnc_port=None, vnc_lan_port=None)
        self.assertIn("显示栈 ok 但容器无 6080 映射", output)
        self.assertNotIn("vnc.html", output)

    def test_lan_port_parsing_excludes_loopback_and_ipv6_only_mappings(self):
        for binding in ("127.0.0.1:49254", "[::1]:49254", "[::]:49254"):
            with self.subTest(binding=binding):
                text = f"6080/tcp -> {binding}\n"
                self.assertEqual(self.m.parse_podman_ports(text)["6080"], 49254)
                self.assertNotIn("6080", self.m.parse_podman_ports(text, lan_only=True))
        text = ("6080/tcp -> 127.0.0.1:49000\n"
                "6080/tcp -> 0.0.0.0:49254\n"
                "22/tcp -> 0.0.0.0:49153\n")
        self.assertEqual(self.m.parse_podman_ports(text, lan_only=True)["6080"], 49254)

    def test_host_port_probe_detects_conflict_off_primary_loopback(self):
        # 旧版只试绑 127.0.0.1, 会漏掉其他接口占用, 随后 0.0.0.0 发布失败.
        with socket.socket() as listener:
            listener.bind(("127.0.0.2", 0))
            listener.listen()
            self.assertFalse(self.m.host_port_free(listener.getsockname()[1]))

    def test_resume_refreshes_lan_mapping_instead_of_reusing_stale_record(self):
        for binding, expected in (("0.0.0.0:49254", 49254), ("127.0.0.1:49254", None)):
            with self.subTest(binding=binding), TemporaryDirectory() as root:
                record = {"name": "swt-demo", "vnc-lan-port": 49999}
                runtime = {"containers": [record]}
                runtime_file = Path(root) / "runtime.json"

                def run(command, **kwargs):
                    if command == ["podman", "port", "swt-demo"]:
                        return subprocess.CompletedProcess(command, 0, f"6080/tcp -> {binding}\n", "")
                    if command[:3] == ["podman", "exec", "swt-demo"]:
                        return subprocess.CompletedProcess(command, 0, "ok", "")
                    raise AssertionError(f"意外命令: {command}")

                with patch.object(self.m, "run", side_effect=run):
                    self.assertEqual(self.m.ensure_display_after_resume(runtime, runtime_file, record), "ok")
                saved = json.loads(runtime_file.read_text(encoding="utf-8"))["containers"][0]
                self.assertEqual(saved["vnc-port"], 49254)
                self.assertEqual(saved["vnc-lan-port"], expected)

    def test_all_birth_resume_delivery_calls_pass_lan_mapping(self):
        source = SCRIPT.read_text(encoding="utf-8")
        calls = []
        for match in re.finditer(r"(?<!def )print_delivery_lines\(", source):
            depth = 0
            for index in range(source.index("(", match.start()), len(source)):
                if source[index] == "(":
                    depth += 1
                elif source[index] == ")":
                    depth -= 1
                    if depth == 0:
                        calls.append(source[match.start():index + 1])
                        break
        self.assertEqual(len(calls), 6)
        for call in calls:
            self.assertIn("vnc_lan_port=", call)


if __name__ == "__main__":
    unittest.main()
