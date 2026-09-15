"""ISSUE-01: swt birth 发布容器 web 端口 8800 (D001/F001) + web-port 登记 (D003).

接缝: 公开函数 create_and_start_container, fake `run` 替换 podman 边界,
断言 podman create 参数含 `-p 8800` (宿主 0.0.0.0 动态, 与 `-p 22` 同款)
且不绑回环地址; 持久化容器记录的 `web-port` 等于 `podman port <名> 8800`
回读的宿主端口, 旧容器无 8800 映射时回读为 None 不报错.
另覆盖 podman_container_state 的 status 重建条目 (D003 交付一致):
有 8800 映射的容器条目 web-port 等于实际宿主端口, 无映射的旧容器为 None.

约定沿用 test_swt_birth_mailbox.py: importlib 按路径加载 swt.py,
模块级 `m.run` 换成 scripted fake, tmpdir 当 records_root, 不依赖真 podman.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


class _FakeRun:
    """scripted podman 边界: 存在性 inspect 回 1 (新容器, 走 create 分支);
    create 记录命令; 后续 inspect 回运行中容器 JSON; port 回读仿真实映射."""

    def __init__(self, container_name: str, web_mapping: str | None = "0.0.0.0:49155"):
        self.container_name = container_name
        self.web_mapping = web_mapping
        self.calls: list[list[str]] = []
        self.create_command: list[str] | None = None

    def __call__(self, command, *, cwd=None, timeout=None):
        command = [str(part) for part in command]
        self.calls.append(command)
        head = " ".join(command[:2])
        if head == "podman create":
            self.create_command = command
            return subprocess.CompletedProcess(command, 0, "created\n", "")
        if head == "podman inspect":
            if self.create_command is None:
                return subprocess.CompletedProcess(command, 1, "", "no such container")
            detail = [{
                "Id": "fakepodmanid123",
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}, "IPAddress": "10.88.0.10"},
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(detail), "")
        if head == "podman start":
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:3] == ["podman", "port", self.container_name]:
            if command[3] == "22":
                return subprocess.CompletedProcess(command, 0, "0.0.0.0:49153\n", "")
            if command[3] == "8800" and self.web_mapping is not None:
                return subprocess.CompletedProcess(command, 0, self.web_mapping + "\n", "")
            return subprocess.CompletedProcess(command, 1, "", "no mapping")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestBirthPublishesWebPort(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-web-access-"))
        self.addCleanup(rmtree, self.root, True)

    def _run_create(self, web_mapping: str | None = "0.0.0.0:49155") -> _FakeRun:
        m = self.m
        records_root = self.root / "records"
        identity = "testid"
        runtime_file = records_root / "runtime" / f"{identity}.json"
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        runtime = {"schema": m.SCHEMA, "containers": [], "stage": "daemon"}
        image = {"ref": "localhost/test:latest", "digest": "sha256:fake"}
        args = argparse.Namespace(name="swt-demo", hostname="swt-demo")
        fake = _FakeRun("swt-demo", web_mapping=web_mapping)
        original_run = m.run
        original_wayland = m.host_wayland_socket
        original_port_free = m.host_port_free
        m.run = fake
        m.host_wayland_socket = lambda: None
        m.host_port_free = lambda port: True
        try:
            m.create_and_start_container(
                args, repo, image, "feat-x", runtime, runtime_file, {},
                records_root, identity)
        finally:
            m.run = original_run
            m.host_wayland_socket = original_wayland
            m.host_port_free = original_port_free
        return fake

    def _persisted_record(self) -> dict:
        runtime_file = self.root / "records" / "runtime" / "testid.json"
        runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
        matches = [c for c in runtime["containers"] if c["name"] == "swt-demo"]
        self.assertEqual(len(matches), 1)
        return matches[0]

    @staticmethod
    def _publish_args(command: list[str]) -> list[str]:
        return [command[i + 1] for i, part in enumerate(command) if part == "-p"]

    def test_create_publishes_8800_on_all_host_interfaces(self):
        """D001: create 参数含 `-p 8800` (宿主 0.0.0.0 动态分配), 不绑回环."""
        fake = self._run_create()
        self.assertIsNotNone(fake.create_command)
        published = self._publish_args(fake.create_command)
        web = [spec for spec in published if spec.rpartition(":")[2] == "8800"]
        self.assertEqual(web, ["8800"], f"8800 应与 22 同款裸发布, 实际 -p 集合: {published}")

    def test_create_does_not_bind_8800_to_loopback(self):
        """F001 守卫: 8800 禁止像 6080 那样绑 127.0.0.1 (局域网直达是 D001 目标)."""
        fake = self._run_create()
        self.assertIsNotNone(fake.create_command)
        published = self._publish_args(fake.create_command)
        loopback_web = [spec for spec in published
                        if spec.startswith("127.0.0.1") and spec.rpartition(":")[2] == "8800"]
        self.assertEqual(loopback_web, [])

    def test_record_web_port_matches_podman_port_8800_readback(self):
        """D003: 新容器记录 web-port 等于 `podman port <名> 8800` 回读的宿主端口."""
        self._run_create(web_mapping="0.0.0.0:49155")
        record = self._persisted_record()
        self.assertEqual(record["web-port"], 49155)

    def test_record_web_port_none_when_no_8800_mapping(self):
        """D009: 旧容器无 8800 映射时 web-port 回读为 None, birth 不报错."""
        self._run_create(web_mapping=None)
        record = self._persisted_record()
        self.assertIsNone(record["web-port"])


class _FakeStatusRun:
    """status 重建边界: podman ps 回一行容器, inspect 回 detail,
    `podman port <名>` (无端口参数) 全量回读, 8800 映射有无由 web_mapping 控制."""

    def __init__(self, container_name: str, web_mapping: str | None = "0.0.0.0:49155"):
        self.container_name = container_name
        self.web_mapping = web_mapping
        self.calls: list[list[str]] = []

    def __call__(self, command, *, cwd=None, timeout=None):
        command = [str(part) for part in command]
        self.calls.append(command)
        head = " ".join(command[:2])
        if head == "podman ps":
            rows = [{
                "Names": [self.container_name],
                "Id": "fakepodmanid123",
                "State": "running",
                "Image": "localhost/test:latest",
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(rows), "")
        if head == "podman inspect":
            detail = [{
                "Id": "fakepodmanid123",
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}, "IPAddress": "10.88.0.10"},
            }]
            return subprocess.CompletedProcess(command, 0, json.dumps(detail), "")
        if command == ["podman", "port", self.container_name]:
            lines = ["22/tcp -> 0.0.0.0:49153"]
            if self.web_mapping is not None:
                lines.append(f"8800/tcp -> {self.web_mapping}")
            return subprocess.CompletedProcess(command, 0, "\n".join(lines) + "\n", "")
        raise AssertionError(f"fake run 未预期命令: {command}")


class TestStatusRebuildsWebPort(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-web-access-status-"))
        self.addCleanup(rmtree, self.root, True)

    def _rebuild_entries(self, web_mapping: str | None) -> list[dict]:
        m = self.m
        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)
        runtime = {"schema": m.SCHEMA, "containers": [],
                   "mother": {"branch": "feat-x", "dir": str(repo)}}
        fake = _FakeStatusRun("swt-demo", web_mapping=web_mapping)
        original_run = m.run
        m.run = fake
        try:
            return m.podman_container_state(repo, runtime, mother_tip="faketip")
        finally:
            m.run = original_run

    def test_status_entry_web_port_matches_8800_mapping(self):
        """D003: status 重建条目 web-port 等于 8800 实际宿主端口, 与 record 登记一致."""
        entries = self._rebuild_entries(web_mapping="0.0.0.0:49155")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["web-port"], 49155)

    def test_status_entry_web_port_none_when_no_8800_mapping(self):
        """D009: 旧容器无 8800 映射时 status 重建条目 web-port 为 None, 不报错."""
        entries = self._rebuild_entries(web_mapping=None)
        self.assertEqual(len(entries), 1)
        self.assertIsNone(entries[0]["web-port"])


class TestConfirmedLanAddress(unittest.TestCase):
    """ISSUE-02 切片: --lan-ip 确认值持久化与读取 (D010/UD-03).

    持久文件 = <records_root>/lan-address (根级, host 级, 纯文本一行);
    lan_ip() 现算值保持原样只作候选提示, 不作已确认值."""

    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-lan-address-"))
        self.addCleanup(rmtree, self.root, True)
        self.records_root = self.root / "records"

    def test_birth_lan_ip_flag_persists_confirmed_address(self):
        """切片 1: birth 带 --lan-ip 时, 地址写入 records_root 根级持久文件."""
        args = self.m.parse_args(["birth", "--records-root", str(self.records_root),
                                  "--lan-ip", "192.168.1.10"])
        self.assertEqual(args.lan_ip, "192.168.1.10")
        # birth 主流程接缝守卫 (同 test_swt_birth_mailbox 约定): flag 消费接写持久化
        source = SCRIPT.read_text(encoding="utf-8")
        birth_segment = source[source.index("def birth("):]
        self.assertIn("write_confirmed_lan_address(records_root, require_valid_lan_ip(args.lan_ip))", birth_segment)
        # 写函数行为: 与 birth 内调用同款实参
        self.m.write_confirmed_lan_address(self.records_root, args.lan_ip)
        persisted = self.records_root / "lan-address"
        self.assertTrue(persisted.is_file())
        self.assertEqual(persisted.read_text(encoding="utf-8").strip(), "192.168.1.10")

    def test_read_confirmed_address_returns_persisted_value(self):
        """切片 2: 持久文件已有值时, 读取已确认地址返回该值 (不再需要 --lan-ip)."""
        self.m.write_confirmed_lan_address(self.records_root, "192.168.1.10")
        self.assertEqual(self.m.read_confirmed_lan_address(self.records_root), "192.168.1.10")

    def test_read_confirmed_address_none_when_absent(self):
        """切片 3: 持久文件不存在且未给 flag 时, 读取返回 None (无值, 不是猜测)."""
        args = self.m.parse_args(["birth", "--records-root", str(self.records_root)])
        self.assertIsNone(args.lan_ip)
        self.assertIsNone(self.m.read_confirmed_lan_address(self.records_root))


class TestBirthLanAddressDecide(unittest.TestCase):
    """ISSUE-02 末切片: birth 无已确认地址且未给 --lan-ip → kind lan-address 的
    DECIDE 行 + exit 1 (D010/UD-03); lan_ip() 现算值仅作候选提示 (标注未确认),
    不落确认值; 已有确认值 (或带 flag) 时不再为该 kind 打 DECIDE.
    收据闭环 (评审修复): 走 decision_pending 既有机制 — 指纹漂移废票重问,
    答案匹配即消费旧收据, 不残留; "lan-address" 入 birth 的 stale 清理名单.

    接缝: lan_address_decision 小函数单测 (真实 create_receipt/decision_line/
    expire_receipts 走收据路径) + birth 主流程源码接缝守卫
    (同 TestConfirmedLanAddress 与 test_swt_birth_mailbox.py:438 约定)."""

    IDENTITY = "testid"
    OPTIONS = ["--lan-ip <addr>"]

    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-lan-decide-"))
        self.addCleanup(rmtree, self.root, True)
        self.records_root = self.root / "records"
        original_lan_ip = self.m.lan_ip
        self.m.lan_ip = lambda: "10.0.0.5"
        self.addCleanup(setattr, self.m, "lan_ip", original_lan_ip)

    def _decide(self, lan_ip_arg, fingerprint, stale=False):
        return self.m.lan_address_decision(
            self.records_root, self.IDENTITY, fingerprint, lan_ip_arg, stale)

    def test_pending_decide_line_exit1_when_unconfirmed(self):
        """切片 1: 无确认值且无 flag → lan-address 待决; DECIDE 行含候选提示
        (明确标注未确认) 与 --lan-ip 选项; 候选不落确认文件; birth 接法 exit 1."""
        fingerprint = {"repo": str(self.root / "repo"), "image-digest": "sha256:fake"}
        decision = self._decide(None, fingerprint)
        self.assertIsNotNone(decision)
        kind, question, options = decision
        self.assertEqual(kind, "lan-address")
        # 候选提示在问题里, 且明确标注未确认 (F006: 猜测值不冒充确认值)
        self.assertIn("10.0.0.5", question)
        self.assertIn("未确认", question)
        self.assertTrue(any("--lan-ip" in option for option in options))
        # 候选只是提示: 确认文件仍为空 (未把候选当确认值交付)
        self.assertIsNone(self.m.read_confirmed_lan_address(self.records_root))
        # DECIDE 行走真实收据路径 (与 birth pending 汇总段同一对调用)
        receipt = self.m.create_receipt(self.records_root, self.IDENTITY, kind,
                                        fingerprint, options)
        line = self.m.decision_line(receipt, kind, question, options)
        self.assertTrue(line.startswith("DECIDE "), line)
        self.assertIn(" lan-address ", line)
        self.assertIn(question, line)
        self.assertIn("--lan-ip", line)
        # 接缝守卫: birth pending 段接入 lan-address 并过 decision_pending 闭环;
        # flag 写入 (顶部) 在判定之前, 保证带 --lan-ip 重跑先持久化再判定;
        # pending 块 exit 1 在任何容器创建之前 (DECIDE 一次列全, 不动资源)
        source = SCRIPT.read_text(encoding="utf-8")
        birth_segment = source[source.index("def birth("):]
        write_at = birth_segment.index("write_confirmed_lan_address(records_root,")
        decide_at = birth_segment.index("lan_address_decision(records_root, identity,")
        pending_at = birth_segment.index("if pending:")
        self.assertLess(write_at, decide_at)
        self.assertLess(decide_at, pending_at)
        self.assertIn("pending.append(lan_address)", birth_segment)
        pending_return = birth_segment.index("return 1", pending_at)
        create_at = birth_segment.index("container = create_and_start_container(")
        self.assertLess(pending_return, create_at)
        # "lan-address" 入 stale_receipts 清理名单 (与其他 kind 同一份名单)
        loop_at = birth_segment.index("for decision_kind in (")
        loop_line = birth_segment[loop_at:birth_segment.index("\n", loop_at)]
        self.assertIn('"lan-address"', loop_line)

    def test_no_decide_when_confirmed_address_exists(self):
        """切片 2: 持久文件已有确认值 → 不打 lan-address DECIDE (D010 优先沿用);
        候选算法根本不被调用 (确认值优先, 无需现算猜测)."""
        self.m.write_confirmed_lan_address(self.records_root, "192.168.1.10")

        def _explode():
            raise AssertionError("已有确认值时不应再调用 lan_ip() 现算候选")

        self.m.lan_ip = _explode
        fingerprint = {"repo": "r", "image-digest": "d"}
        self.assertIsNone(self._decide(None, fingerprint))
        # 带 --lan-ip 时同样不待决 (顶部写入已消费)
        self.assertIsNone(self._decide("192.168.1.11", fingerprint))

    def test_fingerprint_drift_reasks_even_with_flag(self):
        """收据闭环: DECIDE 开出后指纹漂移, 用户带 --lan-ip 重跑 →
        废票重问 (drift), 不直接接受; 旧收据已被 expire 清除."""
        f_before = {"repo": "r", "image-digest": "sha256:old"}
        f_after = {"repo": "r", "image-digest": "sha256:new"}
        # 首轮 DECIDE: birth pending 汇总段开收据 (绑定当时指纹)
        receipt = self.m.create_receipt(self.records_root, self.IDENTITY,
                                        "lan-address", f_before, self.OPTIONS)
        self.assertTrue(receipt.is_file())
        # 指纹漂移: birth stale 清理段 expire 旧票
        stale = self.m.expire_receipts(self.records_root, self.IDENTITY,
                                       "lan-address", f_after)
        self.assertTrue(stale)
        self.assertFalse(receipt.exists(), "失配旧收据应被废掉")
        # 用户带 --lan-ip 重跑: 已答但票已废 → drift 重问, 不放行
        decision = self._decide("192.168.1.10", f_after, stale=stale)
        self.assertIsNotNone(decision, "指纹漂移后带 flag 重跑仍须重问, 不得直接接受")
        kind, question, _ = decision
        self.assertEqual(kind, "lan-address")
        self.assertIn("重新确认", question)

    def test_matching_answer_consumes_receipt(self):
        """收据闭环: 指纹未变, 用户带 --lan-ip 重跑 → 不待决, 旧收据被消费不残留."""
        fingerprint = {"repo": "r", "image-digest": "sha256:same"}
        receipt = self.m.create_receipt(self.records_root, self.IDENTITY,
                                        "lan-address", fingerprint, self.OPTIONS)
        decision = self._decide("192.168.1.10", fingerprint, stale=False)
        self.assertIsNone(decision)
        self.assertFalse(receipt.exists(), "答案匹配后旧收据介绍消费, 不得残留")
        self.assertEqual(self.m.receipt_files(self.records_root, self.IDENTITY,
                                              "lan-address"), [])


class TestLanIpFormatValidation(unittest.TestCase):
    """评审修复: --lan-ip IPv4 格式校验 (仿 --hostname RFC1123 先例):
    非法值 PreconditionError, 不持久化."""

    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-lan-ip-validate-"))
        self.addCleanup(rmtree, self.root, True)
        self.records_root = self.root / "records"

    def test_invalid_lan_ip_rejected_and_not_persisted(self):
        for bad in ("not-an-ip", "999.1.2.3", "10.0.0", "1.2.3.4.5", ""):
            with self.assertRaises(self.m.PreconditionError, msg=bad):
                self.m.require_valid_lan_ip(bad)
        # 校验先于写入 (birth 顶部写调用内嵌校验), 非法值不落持久文件
        self.assertIsNone(self.m.read_confirmed_lan_address(self.records_root))
        source = SCRIPT.read_text(encoding="utf-8")
        birth_segment = source[source.index("def birth("):]
        self.assertIn(
            "write_confirmed_lan_address(records_root, require_valid_lan_ip(args.lan_ip))",
            birth_segment)

    def test_valid_lan_ip_passes(self):
        self.assertEqual(self.m.require_valid_lan_ip("192.168.1.10"), "192.168.1.10")


class TestWebDeliveryUrls(unittest.TestCase):
    """ISSUE-03 切片 1-3: print_delivery_lines 的 web 双 URL (D003/D007).

    仅当容器有 web-port 才出现 web URL 行; 本机 = 127.0.0.1:<web-port>,
    局域网 = 已确认地址:<web-port>; 无已确认值不拼猜测地址 (D010/UD-03)."""

    def setUp(self):
        self.m = _load_swt()

    def _delivery_output(self, web_port, lan) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.m.print_delivery_lines(
                "birth: 已完成", 49153, None, "absent", None, lan,
                web_port=web_port)
        return buffer.getvalue()

    def test_dual_web_urls_when_web_port(self):
        """切片 1: 有 web-port → 本机 URL (127.0.0.1:web-port) + 局域网 URL
        (已确认地址:web-port) 双行齐发."""
        output = self._delivery_output(web_port=49155, lan="192.168.1.10")
        self.assertIn("web 入口 (本机):   http://127.0.0.1:49155", output)
        self.assertIn("web 入口 (局域网): http://192.168.1.10:49155", output)

    def test_no_web_lines_without_web_port(self):
        """切片 2: 无 web-port (旧容器) → 无 web URL 行, 其余交付行不变 (D009)."""
        output = self._delivery_output(web_port=None, lan="192.168.1.10")
        self.assertNotIn("web 入口", output)
        self.assertNotIn("http://127.0.0.1:49155", output)
        # 既有行不变
        self.assertIn("ssh 入口 (本机):   ssh -p 49153 bolo@127.0.0.1", output)
        self.assertIn("ssh 入口 (局域网): ssh -p 49153 bolo@192.168.1.10", output)
        self.assertIn("herdr remote (host):    herdr --remote ssh://bolo@127.0.0.1:49153", output)

    def test_no_guessed_lan_url_when_address_unconfirmed(self):
        """切片 3: 局域网地址无已确认值 → 本机 URL 照打, 不拼猜测地址,
        显式打未附发原因 (F3 同款, 不静默丢失)."""
        output = self._delivery_output(web_port=49155, lan=None)
        self.assertIn("web 入口 (本机):   http://127.0.0.1:49155", output)
        self.assertNotIn("web 入口 (局域网): http", output)
        self.assertIn("web 入口 (局域网) 未附发", output)


class TestStatusWebUrls(unittest.TestCase):
    """ISSUE-03 切片 4 (UD-04): status 对有 web-port 的容器在 STATE 之外附双 URL 行,
    与 birth/resume 同源组装; 无 web-port 的旧容器不附."""

    def setUp(self):
        self.m = _load_swt()

    def test_status_attaches_dual_urls_only_for_web_port_containers(self):
        entries = [
            {"name": "swt-new", "web-port": 49155, "state": "running"},
            {"name": "swt-old", "web-port": None, "state": "running"},
        ]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.m.print_status_web_lines(entries, "192.168.1.10")
        output = buffer.getvalue()
        # 有 web-port 的容器: 双 URL 行, 带容器名标识 (只列当前母体自身容器, D003)
        self.assertIn("web 入口 (swt-new) (本机):   http://127.0.0.1:49155", output)
        self.assertIn("web 入口 (swt-new) (局域网): http://192.168.1.10:49155", output)
        # 无 web-port 的旧容器: 不附
        self.assertNotIn("swt-old", output)
        self.assertEqual(output.count("http://"), 2)

    def test_status_skips_web_urls_for_non_running_containers(self):
        """UD-11: 停止容器 (有 web-port) 不附 web URL 行 (不交付不可达链接);
        running 容器照附."""
        entries = [
            {"name": "swt-run", "web-port": 49155, "state": "running"},
            {"name": "swt-stop", "web-port": 49156, "state": "exited"},
        ]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.m.print_status_web_lines(entries, "192.168.1.10")
        output = buffer.getvalue()
        self.assertIn("web 入口 (swt-run) (本机):   http://127.0.0.1:49155", output)
        self.assertIn("web 入口 (swt-run) (局域网): http://192.168.1.10:49155", output)
        self.assertNotIn("swt-stop", output)
        self.assertNotIn("49156", output)
        self.assertEqual(output.count("http://"), 2)

    def test_status_hooked_in_status_command(self):
        """接缝守卫: status 命令在 STATE 之后接入 print_status_web_lines,
        局域网用址取已确认值 (不现算猜测)."""
        source = SCRIPT.read_text(encoding="utf-8")
        segment = source[source.index("def status("):]
        self.assertIn("print_status_web_lines(", segment)
        self.assertIn("read_confirmed_lan_address(records_root)", segment)
        self.assertNotIn("lan_ip()", segment)


class TestDeliveryCallSitesUseConfirmedAddress(unittest.TestCase):
    """ISSUE-03 切片 5 (D010/UD-03): birth/resume 全部 print_delivery_lines 调用点
    不再用 lan_ip() 现算值拼局域网交付, 一律取已确认值; 同时接入 web-port
    (birth/resume 交付 web 双 URL 的接缝)."""

    @staticmethod
    def _extract_call(source: str, start: int) -> str:
        """从调用名起点做括号平衡扫描, 精确切到该次调用的右括号 (不吃后续代码,
        也不截断在调用内部 — assertNotIn("lan_ip()") 的窗口必须覆盖整个调用点)."""
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

    def _call_segments(self) -> list[str]:
        source = SCRIPT.read_text(encoding="utf-8")
        return [self._extract_call(source, match.start())
                for match in re.finditer(r"(?<!def )print_delivery_lines\(", source)]

    def test_call_sites_use_confirmed_address_and_web_port(self):
        segments = self._call_segments()
        # birth 主交付 + 显示门禁重交付 x2 + resume 两路径 = 5 处
        self.assertEqual(len(segments), 5, f"调用点数量变化, 守卫需同步复核: {len(segments)}")
        for segment in segments:
            # 窗口精确性自证: 恰覆盖单次调用 (一个调用名, 右括号收尾)
            self.assertEqual(segment.count("print_delivery_lines("), 1)
            self.assertTrue(segment.endswith(")"), f"窗口未切在调用终点: {segment[-80:]}")
            self.assertNotIn("lan_ip()", segment,
                             f"交付调用点仍用 lan_ip() 现算猜测值: {segment[:120]}")
            self.assertIn("read_confirmed_lan_address(records_root)", segment,
                          f"交付调用点未取已确认地址: {segment[:120]}")
            self.assertIn('get("web-port")', segment,
                          f"交付调用点未接入 web-port: {segment[:120]}")


class TestBirthSingleActiveContainer(unittest.TestCase):
    """ISSUE-04: 一母体一活跃容器 (D003/F004) — birth 时同母体已有活跃容器
    (异名) → 拒绝并指明旧容器名与 terminate 指引; 同名重入 (失败重试) 仍允许;
    retired 容器不算活跃; 别的母体容器不影响本检查.

    活跃语义以 is_active_container 为准 (记录未 retired; 停止但未终结仍算活跃,
    同样拒绝 — 不放行双活). 不追溯处置既有容器 (D009), 只拒绝本次新建.

    接缝: 模块级小函数 birth_active_container_conflict 单测 (输入 runtime 记录
    + podman live 实况, 输出拒绝原因或 None) + birth 主流程源码接缝守卫
    (同 TestBirthLanAddressDecide 约定)."""

    def setUp(self):
        self.m = _load_swt()

    @staticmethod
    def _runtime(*records: dict) -> dict:
        return {"schema": "test", "stage": "born", "containers": list(records)}

    @staticmethod
    def _record(name: str, retired: bool = False, state: str = "running") -> dict:
        return {"name": name, "retired": retired, "state": state}

    @staticmethod
    def _live_row(name: str, branch: str) -> dict:
        return {"Names": [name], "State": "running",
                "Labels": {"sandbox-worktree.repo": "/repo",
                           "sandbox-worktree.mother": branch,
                           "sandbox-worktree.branch": branch}}

    def _conflict(self, runtime, live_rows, branch="feat-x", new_name="swt-new"):
        return self.m.birth_active_container_conflict(runtime, live_rows, branch, new_name)

    def test_active_container_different_name_rejected(self):
        """切片 1a: 母体已有一个活跃容器 (异名, runtime 记录) → 拒绝,
        原因含旧容器名与 terminate 指引."""
        runtime = self._runtime(self._record("swt-old"))
        reason = self._conflict(runtime, [], new_name="swt-new")
        self.assertIsNotNone(reason)
        self.assertIn("swt-old", reason)
        self.assertIn("terminate", reason)

    def test_active_container_from_live_rows_rejected(self):
        """切片 1b: runtime 记录缺失但 podman live 实况有本母体运行中容器
        (异名) → 同样拒绝 (live 行兜底)."""
        reason = self._conflict(None, [self._live_row("swt-old", "feat-x")],
                                new_name="swt-new")
        self.assertIsNotNone(reason)
        self.assertIn("swt-old", reason)
        self.assertIn("terminate", reason)

    def test_retired_container_not_rejected(self):
        """切片 2: 已有容器已 retired (D033, 非活跃) → 不因此拒绝.
        retired 记录与 live 行交叉: 记录标 retired 的同名 live 行也不算活跃."""
        runtime = self._runtime(self._record("swt-old", retired=True, state="exited"))
        self.assertIsNone(self._conflict(runtime, [], new_name="swt-new"))
        self.assertIsNone(
            self._conflict(runtime, [self._live_row("swt-old", "feat-x")],
                           new_name="swt-new"))

    def test_stopped_but_not_retired_still_rejected(self):
        """is_active_container 语义锁定: 停止 (state=exited) 但未终结
        (未 retired) 的容器仍算活跃 → 拒绝, 不放行双活."""
        runtime = self._runtime(self._record("swt-old", retired=False, state="exited"))
        reason = self._conflict(runtime, [], new_name="swt-new")
        self.assertIsNotNone(reason)
        self.assertIn("swt-old", reason)

    def test_same_name_reentry_allowed(self):
        """切片 3: 同名重入 (失败重试, 已有活跃记录同名) → 不冲突, 仍允许."""
        runtime = self._runtime(self._record("swt-same"))
        self.assertIsNone(self._conflict(runtime, [self._live_row("swt-same", "feat-x")],
                                         new_name="swt-same"))

    def test_other_mother_containers_ignored(self):
        """切片 4: 不同母体各有容器互不影响 — live 实况里别的分支的容器
        不计入本母体冲突; 本母体无记录 → 放行."""
        live = [self._live_row("swt-other", "feat-other"),
                self._live_row("swt-yet-another", "bugfix-y")]
        self.assertIsNone(self._conflict(None, live, new_name="swt-new"))

    def test_birth_seam_guard(self):
        """接缝守卫: birth 主流程接入 birth_active_container_conflict —
        在显示门禁重入之后 (不重伤 display 重入流), 在容器创建之前拒绝;
        冲突抛 PreconditionError; live 实况取 live_repo_containers(repo)."""
        source = SCRIPT.read_text(encoding="utf-8")
        birth_segment = source[source.index("def birth("):]
        reentry_at = birth_segment.index("birth_display_gate_reentry(")
        check_at = birth_segment.index("birth_active_container_conflict(")
        create_at = birth_segment.index("container = create_and_start_container(")
        self.assertLess(reentry_at, check_at)
        self.assertLess(check_at, create_at)
        self.assertIn("live_repo_containers(repo)", birth_segment)
        raise_at = birth_segment.index("raise PreconditionError", check_at)
        self.assertLess(raise_at, create_at)

    def test_name_writeback_single_source_before_conflict_check(self):
        """评审修复守卫: 容器名推导一次写回 args.name, 位置在冲突检查之前
        (冲突检查/hostname 候选/wire/create 复用同一值, 不再各自 fork slug
        子进程); born 重入守卫改用写回前捕获的 name_explicit, 不受缺省回填
        影响 (同母体重入仍必须显式 --name)."""
        source = SCRIPT.read_text(encoding="utf-8")
        birth_segment = source[source.index("def birth("):]
        writeback_at = birth_segment.index(
            "args.name = args.name or container_default_name(branch)")
        check_at = birth_segment.index("birth_active_container_conflict(")
        self.assertLess(writeback_at, check_at,
                        "名字写回必须先于冲突检查, 检查直接用 args.name")
        # 写回唯一: birth 内其余处不再重复推导 (create_and_start_container 自身
        # 的防御性回退不算 birth 内推导点)
        self.assertEqual(
            birth_segment.count("args.name or container_default_name(branch)"), 1,
            "birth 内只允许一处名字推导 (写回点), 其余复用 args.name")
        capture_at = birth_segment.index("name_explicit = bool(args.name)")
        self.assertLess(capture_at, writeback_at,
                        "name_explicit 必须在写回之前捕获, 否则 born 重入守卫失效")
        born_at = birth_segment.index('runtime_existing.get("stage") == "born"')
        born_segment = birth_segment[born_at:born_at + 400]
        self.assertIn("not name_explicit", born_segment)
        self.assertNotIn("not args.name", born_segment)


if __name__ == "__main__":
    unittest.main()
