"""MILESTONE-08 ISSUE-06 + ISSUE-07: enroll-device-key 子命令与窗口直飞交付行.

接缝 (公开行为, 不测内部实现):
- enroll-device-key: 公钥校验 (单行/非注释/>=2 字段) + podman exec -i 单次调用
  (stdin 传公钥, 容器内 sh 完成 install -d/touch/grep -qxF 去重/chmod 600, N4)
  + 确认与设备侧测试提示; 容器不在/exec 失败走既有错误通道.
- headed_delivery_lines / print_delivery_lines: 窗口直飞交付 (ISSUE-07, UD-09):
  有实例脚本 → 前置行 + waypipe 模板行; lan 未确认 → 未附发 reason (F3);
  无实例脚本 → 一行 reason.
- status 接线: print_status_headed_lines 只对 running 且有 ssh-port 的容器产行.

测试约定沿 test_swt_birth_mailbox.py / test_swt_m08_headed.py: importlib 加载
swt.py, fake run 替换 podman 边界, tmpdir, 不依赖 podman.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import sys
import unittest
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"

CONTAINER_SCRIPT_PATH = "/home/bolo/.local/bin/swt-headed-browser.sh"
VALID_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeFakeFakeFakeFakeFakeFakeFakeFakeFake00 device@host"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class M08Case(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-m08-delivery-"))
        self.addCleanup(rmtree, self.root, True)


class _FakePodman:
    """podman 边界: exec -i 记录命令与 stdin, port 22 回定向映射."""

    def __init__(self, exec_rc: int = 0, exec_stderr: str = ""):
        self.commands: list[list[str]] = []
        self.inputs: list[str | None] = []
        self.exec_rc = exec_rc
        self.exec_stderr = exec_stderr

    def __call__(self, command, *, cwd=None, timeout=None, input=None):
        self.commands.append([str(part) for part in command])
        self.inputs.append(input)
        if command[:2] == ["podman", "port"]:
            if "22" in command:
                return _cp(command, 0, "0.0.0.0:49153\n", "")
            return _cp(command, 1, "", "no mapping")
        if command[:3] == ["podman", "exec", "-i"]:
            return _cp(command, self.exec_rc, "", self.exec_stderr)
        raise AssertionError(f"fake run 未预期命令: {command}")

    def exec_calls(self) -> list[list[str]]:
        return [c for c in self.commands if c[:3] == ["podman", "exec", "-i"]]


def _cp(command, rc, stdout, stderr):
    import subprocess
    return subprocess.CompletedProcess(command, rc, stdout, stderr)


class TestEnrollDeviceKey(M08Case):
    """ISSUE-06: swt enroll-device-key <容器名> [--pubkey-file <路径>|-]."""

    def _cmd(self, fake, *, container="swt-demo", pubkey_file=None, key=VALID_KEY):
        import argparse
        m = self.m
        original_run = m.run
        m.run = fake
        try:
            args = argparse.Namespace(container=container, pubkey_file=pubkey_file)
            stdout = io.StringIO()
            if pubkey_file in (None, "-"):
                original_stdin = sys.stdin
                sys.stdin = io.StringIO(key + "\n")
                try:
                    with contextlib.redirect_stdout(stdout):
                        rc = m.cmd_enroll_device_key(args)
                finally:
                    sys.stdin = original_stdin
            else:
                with contextlib.redirect_stdout(stdout):
                    rc = m.cmd_enroll_device_key(args)
            return rc, stdout.getvalue()
        finally:
            m.run = original_run

    def test_valid_key_from_file_single_exec_with_stdin(self):
        key_file = self.root / "device.pub"
        key_file.write_text(VALID_KEY + "\n", encoding="utf-8")
        fake = _FakePodman()
        rc, output = self._cmd(fake, pubkey_file=str(key_file))
        self.assertEqual(rc, 0)
        exec_calls = fake.exec_calls()
        # 单次 exec, stdin 传公钥 (命令行不嵌 key); exec 后还有 port 查询, 按序定位
        self.assertEqual(len(exec_calls), 1)
        exec_index = next(i for i, c in enumerate(fake.commands) if c[:3] == ["podman", "exec", "-i"])
        self.assertEqual(fake.inputs[exec_index], VALID_KEY + "\n")
        self.assertNotIn(VALID_KEY, " ".join(exec_calls[0]))
        command = exec_calls[0]
        self.assertEqual(command[:4], ["podman", "exec", "-i", "swt-demo"])
        self.assertEqual(command[4:6], ["sh", "-c"])
        script = command[6]
        self.assertIn("install -d -m 700 -o bolo -g bolo /home/bolo/.ssh", script)
        self.assertIn("touch /home/bolo/.ssh/authorized_keys", script)
        self.assertIn("chown bolo:bolo /home/bolo/.ssh/authorized_keys", script)
        self.assertIn("chmod 600", script)
        # grep -qxF 精确行去重, 未命中才追加
        self.assertIn('grep -qxF "$key" /home/bolo/.ssh/authorized_keys', script)
        self.assertIn(">> /home/bolo/.ssh/authorized_keys", script)
        # 确认 + 设备侧测试提示 (端口来自 podman port)
        self.assertIn("swt-demo", output)
        self.assertIn("authorized_keys", output)
        self.assertIn("ssh -p 49153 bolo@127.0.0.1", output)

    def test_valid_key_from_stdin_by_default(self):
        fake = _FakePodman()
        rc, _output = self._cmd(fake, pubkey_file=None)
        self.assertEqual(rc, 0)
        self.assertEqual(len(fake.exec_calls()), 1)
        exec_index = next(i for i, c in enumerate(fake.commands) if c[:3] == ["podman", "exec", "-i"])
        self.assertEqual(fake.inputs[exec_index], VALID_KEY + "\n")

    def test_pubkey_file_dash_reads_stdin(self):
        fake = _FakePodman()
        rc, _output = self._cmd(fake, pubkey_file="-")
        self.assertEqual(rc, 0)
        exec_index = next(i for i, c in enumerate(fake.commands) if c[:3] == ["podman", "exec", "-i"])
        self.assertEqual(fake.inputs[exec_index], VALID_KEY + "\n")

    def test_multiline_key_rejected_before_exec(self):
        fake = _FakePodman()
        with self.assertRaises(self.m.PreconditionError):
            self._cmd(fake, key=VALID_KEY + "\nsecond line")
        self.assertEqual(fake.exec_calls(), [])

    def test_comment_key_rejected(self):
        fake = _FakePodman()
        with self.assertRaises(self.m.PreconditionError):
            self._cmd(fake, key="# just a comment")
        self.assertEqual(fake.exec_calls(), [])

    def test_single_field_key_rejected(self):
        fake = _FakePodman()
        with self.assertRaises(self.m.PreconditionError):
            self._cmd(fake, key="just-one-giant-base64-blob")
        self.assertEqual(fake.exec_calls(), [])

    def test_empty_key_rejected(self):
        fake = _FakePodman()
        with self.assertRaises(self.m.PreconditionError):
            self._cmd(fake, key="   \n")
        self.assertEqual(fake.exec_calls(), [])

    def test_exec_failure_raises_with_container_name(self):
        fake = _FakePodman(exec_rc=1, exec_stderr="no such container")
        with self.assertRaises(self.m.PreconditionError) as ctx:
            self._cmd(fake, container="gone")
        self.assertIn("gone", str(ctx.exception))
        self.assertEqual(len(fake.exec_calls()), 1)

    def test_missing_pubkey_file_raises(self):
        fake = _FakePodman()
        with self.assertRaises(self.m.PreconditionError):
            self._cmd(fake, pubkey_file=str(self.root / "absent.pub"))
        self.assertEqual(fake.exec_calls(), [])

    def test_subcommand_registered(self):
        args = self.m.parse_args(["enroll-device-key", "c1", "--pubkey-file", "-"])
        self.assertEqual(args.command, "enroll-device-key")
        self.assertEqual(args.container, "c1")
        self.assertEqual(args.pubkey_file, "-")
        default = self.m.parse_args(["enroll-device-key", "c2"])
        self.assertIsNone(default.pubkey_file)


class TestHeadedDeliveryLines(M08Case):
    """ISSUE-07: headed_delivery_lines 三态 (模板+前提 / lan 缺 reason / 无脚本 reason)."""

    def test_template_and_preamble_with_lan(self):
        lines = self.m.headed_delivery_lines(
            49153, "192.168.1.10", "/records/runtime/x/swt-headed-browser.sh")
        self.assertEqual(len(lines), 2)
        template = lines[0]
        # UD-09: -R 远端路径用 $(id -u) 由设备 shell 展开
        self.assertIn(
            "waypipe ssh -p 49153 -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native"
            f" bolo@192.168.1.10 {CONTAINER_SCRIPT_PATH}", template)
        preamble = lines[1]
        self.assertIn("waypipe", preamble)
        self.assertIn("enroll-device-key", preamble)

    def test_unconfirmed_lan_reason_carries_assembled_template(self):
        lines = self.m.headed_delivery_lines(49153, None, "/records/runtime/x/swt-headed-browser.sh")
        self.assertEqual(len(lines), 1)
        self.assertIn("未附发", lines[0])
        self.assertIn("<host-LAN-IP>", lines[0])
        self.assertIn(
            "waypipe ssh -p 49153 -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native"
            f" bolo@<host-LAN-IP> {CONTAINER_SCRIPT_PATH}", lines[0])

    def test_absent_script_single_reason_line(self):
        lines = self.m.headed_delivery_lines(49153, "192.168.1.10", None)
        self.assertEqual(len(lines), 1)
        self.assertIn("未附发", lines[0])
        self.assertNotIn("waypipe ssh -p", lines[0])

    def test_no_lines_without_ssh_port(self):
        self.assertEqual(self.m.headed_delivery_lines(None, "192.168.1.10", "/x.sh"), [])


class TestPrintDeliveryWiring(M08Case):
    """print_delivery_lines 接线 + status 侧产行 + 调用点守卫."""

    def _delivery_output(self, **kwargs) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.m.print_delivery_lines(
                "birth: 已完成", 49153, None, "absent", None, "192.168.1.10", **kwargs)
        return buffer.getvalue()

    def test_delivery_prints_headed_lines_when_script_present(self):
        output = self._delivery_output(headed_script="/records/runtime/x/swt-headed-browser.sh")
        self.assertIn("waypipe ssh -p 49153", output)
        self.assertIn("enroll-device-key", output)

    def test_delivery_prints_reason_when_script_absent(self):
        output = self._delivery_output(headed_script=None)
        self.assertIn("窗口直飞未附发", output)
        self.assertNotIn("waypipe ssh -p", output)

    def test_status_headed_lines_per_running_container(self):
        entries = [
            {"name": "swt-new", "state": "running", "ssh-port": 49153,
             "headed-script": "/records/runtime/x/swt-headed-browser.sh"},
            {"name": "swt-old", "state": "running", "ssh-port": 49154,
             "headed-script": None},
            {"name": "swt-stop", "state": "exited", "ssh-port": 49155,
             "headed-script": "/records/runtime/x/swt-headed-browser.sh"},
            {"name": "swt-noport", "state": "running", "ssh-port": None,
             "headed-script": None},
        ]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.m.print_status_headed_lines(entries, "192.168.1.10")
        output = buffer.getvalue()
        self.assertIn("waypipe ssh -p 49153", output)
        # swt-old 无实例脚本 → reason 行 (F3), 不出模板行
        self.assertIn("窗口直飞未附发", output)
        self.assertNotIn("waypipe ssh -p 49154", output)
        self.assertNotIn("waypipe ssh -p 49155", output)  # 停止容器不附 (UD-11 同语义)
        self.assertNotIn("49156", output)

    def test_status_hooked_after_web_lines(self):
        source = SCRIPT.read_text(encoding="utf-8")
        segment = source[source.index("def status("):]
        self.assertIn("print_status_headed_lines(containers,", segment)

    @staticmethod
    def _extract_call(source: str, start: int) -> str:
        depth = 0
        for index in range(source.index("(", start), len(source)):
            char = source[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return source[start:index + 1]
        raise AssertionError("print_delivery_lines 调用括号不平衡, 源码已变化, 守卫需复核")

    def test_all_delivery_call_sites_pass_headed_script(self):
        """ISSUE-07 接缝守卫: birth/resume 全部 print_delivery_lines 调用点
        (5 处: birth 主交付 + 显示门禁重交付 x2 + resume 两路径) 都传 headed_script."""
        source = SCRIPT.read_text(encoding="utf-8")
        segments = [self._extract_call(source, match.start())
                    for match in re.finditer(r"(?<!def )print_delivery_lines\(", source)]
        self.assertEqual(len(segments), 5, f"调用点数量变化, 守卫需同步复核: {len(segments)}")
        for segment in segments:
            self.assertIn("headed_script=", segment,
                          f"交付调用点未接线窗口直飞行: {segment[:120]}")


if __name__ == "__main__":
    unittest.main()
