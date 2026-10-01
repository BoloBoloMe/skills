"""swt-list-sandbox ISSUE-01: `swt list` 只读清单子命令单元测试 (快层).

接缝 B (podman 执行器 fake-run, 仿 test_swt_m08_headed.py 注入形状):
ps 聚合枚举 / inspect / port 全部由 FakePodman 伪造, 按真实 podman 语义建模:
- `podman ps -a --filter label=<key>` 键存在匹配 (任意值命中, 不限仓);
- `podman inspect <名...>` 可多名: 找得到的进 stdout, 缺名报 stderr 且退出码非 0;
- `podman port <名>` 活取端口映射 (输出行 "容器端口/tcp -> 宿主绑定").
records-root 用 tmp 目录, 不依赖 podman 本体.

TDD 切片见 docs/changes/swt-list-sandbox/issues/ISSUE-01-list-skeleton.md (TS-001..TS-005).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from shutil import rmtree, which
from tempfile import mkdtemp
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workflow/use-sandbox-worktree/scripts/swt.py"


def _load_swt():
    spec = importlib.util.spec_from_file_location("swt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["swt"] = module
    spec.loader.exec_module(module)
    return module


def ps_row(name: str, repo: str, mother: str, state: str = "running") -> dict:
    """podman ps --format json 行 (Names/State/Labels 对齐真实输出形状)."""
    return {
        "Id": f"ps-{name}",
        "Names": [name],
        "State": state,
        "Labels": {"sandbox-worktree.repo": repo, "sandbox-worktree.mother": mother},
    }


def inspect_detail(name: str, state: str, podman_id: str | None = None) -> dict:
    """podman inspect 条目 (Name 带前导斜杠, State.Status 为状态字符串)."""
    return {
        "Name": "/" + name,
        "Id": podman_id or f"id-{name}".ljust(64, "0"),
        "State": {"Status": state},
    }


class FakePodman:
    """scripted podman 边界: 记录全部调用, 未预期命令 AssertionError."""

    def __init__(self, ps_rows, inspect_details=None, ports=None):
        self.ps_rows = list(ps_rows)
        self.inspect_details = dict(inspect_details or {})
        self.ports = dict(ports or {})
        self.calls: list[list[str]] = []

    def __call__(self, command, *, cwd=None, timeout=None, input=None):
        parts = [str(part) for part in command]
        self.calls.append(parts)
        if parts[:2] == ["podman", "ps"]:
            return subprocess.CompletedProcess(command, 0, json.dumps(self.ps_rows), "")
        if parts[:2] == ["podman", "inspect"]:
            names = parts[2:]
            found = [self.inspect_details[name] for name in names if name in self.inspect_details]
            missing = [name for name in names if name not in self.inspect_details]
            stderr = "".join(f"Error: no such container or container is stopped: {name}\n"
                             for name in missing)
            return subprocess.CompletedProcess(
                command, 1 if missing else 0, json.dumps(found) if found else "", stderr)
        if parts[:2] == ["podman", "port"]:
            name = parts[2]
            if name in self.ports:
                # 在 ports 表 = 查询成功 (值可为空串 = 无映射); 缺席 = 非零退出失败
                return subprocess.CompletedProcess(command, 0, self.ports[name], "")
            return subprocess.CompletedProcess(command, 1, "", "no port mappings")
        if parts[0] == "nft":
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(f"fake run 未预期命令: {command}")

    def podman_calls(self) -> list[list[str]]:
        return [call for call in self.calls if call[0] == "podman"]

    def nft_calls(self) -> list[list[str]]:
        return [call for call in self.calls if call[0] == "nft"]


class ListCase(unittest.TestCase):
    def setUp(self):
        self.m = _load_swt()
        self.root = Path(mkdtemp(prefix="swt-list-"))
        self.addCleanup(rmtree, self.root, True)
        self.records = self.root / "records"
        # 测试自含 (评审 G): 快层全 fake, 不依赖环境 PATH 里有 podman —
        # require_command("podman") 由本进程内的 which 假值放行; 缺失行为专项
        # (TC-005 末段) 用自己的 which 补丁覆盖此层, 断言的正是缺失行为本身
        real_which = which

        def fake_which(name, path=None):
            if name == "podman":
                return "/nonexistent-test-bin/podman"
            return real_which(name)

        which_patcher = mock.patch("shutil.which", side_effect=fake_which)
        which_patcher.start()
        self.addCleanup(which_patcher.stop)

    def run_list(self, fake):
        stdout, stderr = io.StringIO(), io.StringIO()
        original = self.m.run
        self.m.run = fake
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = self.m.main(["list", "--records-root", str(self.records)])
        finally:
            self.m.run = original
        return code, stdout.getvalue(), stderr.getvalue()

    def parse_list(self, stdout) -> dict:
        lines = [line for line in stdout.splitlines() if line.strip()]
        self.assertTrue(lines, "stdout 无输出")
        last = lines[-1]
        self.assertTrue(last.startswith("LIST "), f"末行不是 LIST 行: {last!r}")
        # 输出协议: 人话行禁含 LIST 前缀, 仅末行为数据行 (D005)
        self.assertEqual([line for line in lines if line.startswith("LIST ")], [last])
        payload = json.loads(last.removeprefix("LIST "))
        self.assertNotIn("\n", last)
        return payload


class TestListThreeContainers(ListCase):
    """TS-001 / TC-001: 跨仓三容器枚举 + LIST 末行核心字段."""

    def test_list_three_containers_two_repos(self):
        self.records.mkdir()
        fake = FakePodman(
            ps_rows=[
                ps_row("swt-feature-a", "/repos/alpha", "feat-x", state="running"),
                ps_row("swt-hotfix-b", "/repos/alpha", "hotfix", state="exited"),
                ps_row("swt-legacy-c", "/repos/beta", "legacy", state="exited"),
            ],
            inspect_details={
                "swt-feature-a": inspect_detail("swt-feature-a", "running"),
                "swt-hotfix-b": inspect_detail("swt-hotfix-b", "exited"),
                "swt-legacy-c": inspect_detail("swt-legacy-c", "exited"),
            },
            ports={
                "swt-feature-a": (
                    "22/tcp -> 0.0.0.0:49153\n"
                    "6080/tcp -> 0.0.0.0:49154\n"
                    "8800/tcp -> 0.0.0.0:49155\n"
                ),
            },
        )
        code, out, err = self.run_list(fake)
        self.assertEqual(code, 0, err)
        payload = self.parse_list(out)
        self.assertEqual(payload["schema"], 1)
        self.assertEqual(payload["scope"]["records-root"], str(self.records.resolve()))
        self.assertEqual(payload["scope"]["completeness"], "podman-all,records-root-one")
        containers = payload["containers"]
        self.assertEqual(len(containers), 3)
        by_name = {entry["name"]: entry for entry in containers}
        self.assertEqual(set(by_name), {"swt-feature-a", "swt-hotfix-b", "swt-legacy-c"})
        feature = by_name["swt-feature-a"]
        hotfix = by_name["swt-hotfix-b"]
        legacy = by_name["swt-legacy-c"]
        self.assertEqual(feature["repo"], "/repos/alpha")
        self.assertEqual(feature["branch"], "feat-x")
        self.assertEqual(feature["podman-state"], "running")
        self.assertEqual(hotfix["repo"], "/repos/alpha")
        self.assertEqual(hotfix["branch"], "hotfix")
        self.assertEqual(hotfix["podman-state"], "exited")
        self.assertEqual(legacy["repo"], "/repos/beta")
        self.assertEqual(legacy["branch"], "legacy")
        self.assertEqual(legacy["podman-state"], "exited")


class TestListEmpty(ListCase):
    """TS-002 / TC-002: 空清单分支 (exit 0 + 空清单 + 人话提示)."""

    def test_list_empty_no_containers(self):
        self.records.mkdir()
        fake = FakePodman(ps_rows=[])
        code, out, err = self.run_list(fake)
        self.assertEqual(code, 0, err)
        payload = self.parse_list(out)
        self.assertEqual(payload["containers"], [])
        human_lines = [line for line in out.splitlines() if not line.startswith("LIST ")]
        self.assertTrue(any("无在用沙盒容器" in line for line in human_lines), out)


class TestListRecordState(ListCase):
    """TS-003 / TC-003: 跨仓 runtime 记录合并 — record-state 与 lifecycle 双轴 (D003/D006)."""

    def test_list_record_state_and_lifecycle(self):
        self.records.mkdir()
        (self.records / "runtime").mkdir()
        match_id = "id-swt-match-a".ljust(64, "0")
        retired_id = "id-swt-retired-d".ljust(64, "0")
        (self.records / "runtime" / "alpha.json").write_text(json.dumps({
            "schema": 2,
            "repo": "/repos/alpha",
            "containers": [
                {"name": "swt-match-a", "branch": "feat-a", "podman-id": match_id,
                 "host-display": "ok", "retired": False},
                {"name": "swt-retired-d", "branch": "old-d", "podman-id": retired_id,
                 "retired": True},
            ],
        }), encoding="utf-8")
        # 截断的 runtime 文件 (不可解析): swt-broken-c 的记录在位但读不出
        (self.records / "runtime" / "beta-broken.json").write_text(
            '{"schema": 2, "repo": "/repos/beta", "containers": '
            '[{"name": "swt-broken-c", "branch": "feat-c"', encoding="utf-8")
        # 引号 JSON 串匹配防误配 (评审 C): 本文件提到 swt-prefix-p-old,
        # 不得把 swt-prefix-p 归属为 corrupt; 且它不属任何在场容器 → warnings
        (self.records / "runtime" / "gamma-prefix.json").write_text(
            '{"schema": 2, "repo": "/repos/beta", "containers": '
            '[{"name": "swt-prefix-p-old", ', encoding="utf-8")
        # 无法归属任何容器的损坏文件 → 顶层 warnings (评审 C)
        (self.records / "runtime" / "orphan-corrupt.json").write_text(
            '{"schema": 2, "containers": [{"name": "swt-nobody', encoding="utf-8")
        fake = FakePodman(
            ps_rows=[
                ps_row("swt-match-a", "/repos/alpha", "mother-label-a", state="running"),
                ps_row("swt-retired-d", "/repos/alpha", "old-d", state="exited"),
                ps_row("swt-miss-b", "/repos/beta", "mother-label-b", state="exited"),
                ps_row("swt-broken-c", "/repos/beta", "mother-label-c", state="running"),
                ps_row("swt-prefix-p", "/repos/beta", "mother-label-p", state="exited"),
            ],
            inspect_details={
                "swt-match-a": inspect_detail("swt-match-a", "running", podman_id=match_id),
                "swt-retired-d": inspect_detail("swt-retired-d", "exited", podman_id=retired_id),
                "swt-miss-b": inspect_detail("swt-miss-b", "exited"),
                "swt-broken-c": inspect_detail("swt-broken-c", "running"),
                "swt-prefix-p": inspect_detail("swt-prefix-p", "exited"),
            },
        )
        code, out, err = self.run_list(fake)
        self.assertEqual(code, 0, err)
        by_name = {entry["name"]: entry for entry in self.parse_list(out)["containers"]}
        self.assertEqual(by_name["swt-match-a"]["record-state"], "matched")
        self.assertEqual(by_name["swt-match-a"]["lifecycle"], "active")
        # 匹配后记录优先于 label (branch 取自 runtime 记录)
        self.assertEqual(by_name["swt-match-a"]["branch"], "feat-a")
        self.assertEqual(by_name["swt-retired-d"]["record-state"], "matched")
        self.assertEqual(by_name["swt-retired-d"]["lifecycle"], "retired")
        self.assertEqual(by_name["swt-miss-b"]["record-state"], "missing")
        self.assertEqual(by_name["swt-miss-b"]["lifecycle"], "unknown")
        self.assertEqual(by_name["swt-broken-c"]["record-state"], "corrupt")
        self.assertEqual(by_name["swt-broken-c"]["lifecycle"], "unknown")
        # 裸子串会误配 (swt-prefix-p 是 swt-prefix-p-old 的前缀): 必须按引号内
        # JSON 字符串匹配, 未命中 = missing
        self.assertEqual(by_name["swt-prefix-p"]["record-state"], "missing")
        # 无法归属任何容器的损坏文件 → 顶层 warnings 提及文件名
        payload = self.parse_list(out)
        warnings = payload["warnings"]
        self.assertTrue(any("orphan-corrupt.json" in warning for warning in warnings), warnings)
        self.assertTrue(any("gamma-prefix.json" in warning for warning in warnings), warnings)


class TestListSubprocessBudget(ListCase):
    """TS-004 / TC-004: 非功能 — N 容器时 podman 子进程 ≤ 2+N, 不做多余轮询."""

    def test_list_subprocess_budget(self):
        self.records.mkdir()
        rows, details, ports = [], {}, {}
        for index in range(3):
            name = f"swt-budget-{index}"
            state = "running" if index == 0 else "exited"
            rows.append(ps_row(name, "/repos/alpha", f"b-{index}", state=state))
            details[name] = inspect_detail(name, state)
            if state == "running":
                ports[name] = "22/tcp -> 0.0.0.0:49200\n"
        fake = FakePodman(ps_rows=rows, inspect_details=details, ports=ports)
        code, out, err = self.run_list(fake)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.parse_list(out)["containers"]), 3)
        self.assertLessEqual(
            len(fake.podman_calls()), 2 + 3,
            f"podman 子进程超预算: {fake.podman_calls()}")


class TestListReadonlyAndErrors(ListCase):
    """TS-005 / TC-005: 只读纪律 / 单容器采集失败容错 / podman 缺失 ENV 出口 (AC-007b/c/d)."""

    def test_list_readonly_and_collection_errors_and_env(self):
        self.records.mkdir()
        (self.records / "runtime").mkdir()
        runtime_file = self.records / "runtime" / "alpha.json"
        runtime_bytes = json.dumps({
            "schema": 2,
            "repo": "/repos/alpha",
            "containers": [{"name": "swt-keep-a", "branch": "feat-a",
                            "podman-id": "id-swt-keep-a".ljust(64, "0"), "retired": False}],
        }).encode("utf-8")
        runtime_file.write_bytes(runtime_bytes)
        fake = FakePodman(
            ps_rows=[
                ps_row("swt-keep-a", "/repos/alpha", "feat-a", state="running"),
                ps_row("swt-gone-y", "/repos/alpha", "gone-y", state="running"),
                ps_row("swt-idle-z", "/repos/alpha", "idle-z", state="exited"),
                ps_row("swt-quiet-w", "/repos/alpha", "quiet-w", state="running"),
            ],
            # swt-gone-y 不在 inspect 结果中: 枚举后消失 → 单容器采集失败
            inspect_details={
                "swt-keep-a": inspect_detail("swt-keep-a", "running"),
                "swt-idle-z": inspect_detail("swt-idle-z", "exited"),
                "swt-quiet-w": inspect_detail("swt-quiet-w", "running"),
            },
            ports={
                "swt-keep-a": "22/tcp -> 0.0.0.0:49300\n",
                # 退出 0 且输出为空 = 无映射, 不算错误 (swt-quiet-w)
                "swt-quiet-w": "",
                # swt-idle-z 缺席: port 非零退出, 非 running 也要记采集错误
            },
        )
        code, out, err = self.run_list(fake)
        # 只读 (AC-007b): runtime 记录文件内容执行前后不变, 无任何 nft 调用
        self.assertEqual(runtime_file.read_bytes(), runtime_bytes)
        self.assertEqual(fake.nft_calls(), [])
        # 单容器采集失败 (AC-007c): 该条目含 collection-errors 且整体 exit 0
        self.assertEqual(code, 0, err)
        by_name = {entry["name"]: entry for entry in self.parse_list(out)["containers"]}
        gone_errors = by_name["swt-gone-y"]["collection-errors"]
        self.assertTrue(gone_errors)
        # 归属需附 stderr 摘要 (评审 A): 批量 inspect 的缺名错误要可追溯
        self.assertTrue(any("no such container" in error for error in gone_errors), gone_errors)
        self.assertEqual(by_name["swt-keep-a"]["collection-errors"], [])
        # port 错误归属 (评审 B): 非零退出无论 running 与否都记错; 空输出不算错
        idle_errors = by_name["swt-idle-z"]["collection-errors"]
        self.assertTrue(any("podman port" in error for error in idle_errors), idle_errors)
        self.assertEqual(by_name["swt-quiet-w"]["collection-errors"], [])
        # podman 缺失 (AC-007d): exit 4 且 stderr 首行为 ENV 标签行
        real_which = which

        def missing_podman(name, path=None):
            return None if name == "podman" else real_which(name)

        with mock.patch("shutil.which", side_effect=missing_podman):
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                env_code = self.m.main(["list", "--records-root", str(self.records)])
        self.assertEqual(env_code, 4)
        first_line = stderr.getvalue().splitlines()[0]
        self.assertTrue(first_line.startswith("ENV"), stderr.getvalue())
        # OSError 出口 (评审 D): records-root 扫描不可读 → ENV + exit 4, 不出现 2
        runtime_dir = self.records / "runtime"
        runtime_dir.chmod(0o000)
        self.addCleanup(runtime_dir.chmod, 0o755)
        blocked_code, _blocked_out, blocked_err = self.run_list(fake)
        self.assertEqual(blocked_code, 4)
        self.assertTrue(blocked_err.splitlines()[0].startswith("ENV"), blocked_err)


if __name__ == "__main__":
    unittest.main()
