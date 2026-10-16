"""AC-001..017: network 模块/CLI/存储/进程接缝, 不访问真实部署/Podman.

真实网络与隔离另见 test_swt_network_e2e.py. 独立运行时可 --confcutdir=/tmp,
避免旧 conftest 的全机卷/孤儿清理钩子; 本文件仅使用自身临时目录.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "workflow/use-sandbox-worktree/scripts"
sys.path.insert(0, str(SCRIPTS))
import network_update as net
import swt

spec = importlib.util.spec_from_file_location("network_test_firewall", SCRIPTS / "net-firewall.py")
firewall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(firewall)


class Host:
    """测试替换外部目标/规则/通道, 不替换被测的审批/事务/持久化行为."""
    def __init__(self, tmp_path):
        self.path = tmp_path / "records/runtime/fixture.json"
        self.context = {"container-ip": "10.77.0.2", "gateway": "10.77.0.1", "route-gateway": "10.77.0.1", "dns": ["10.77.0.53"]}
        self.identity = {"path": "/fixture/netns", "device": 7, "inode": 8}
        self.full_id = "a" * 64
        self.running = True
        self.stopped_absent = True
        self.writes = []
        self.failures = []
        self.check_failures = []
        self.observe_failures = []
        self.other = {"rules": "未变化", "record": "第二容器"}
        network = net.policy_for_context({"mode": "whitelist", "allow": ["203.0.113.10/32"], "deny": [],
                                          "allow-reasons": {"203.0.113.10/32": "下载构建依赖"}}, self.context)
        record = {"name": "fixture-a", "podman-id": self.full_id, "network-ip": "10.77.0.2", "retired": False}
        self.runtime = {"schema": 2, "repo": str(tmp_path), "mother": {"branch": "feat/fixture", "dir": str(tmp_path / "mother")},
                        "stage": "born", "containers": [record], "network": network, "unrelated": {"keep": True}}
        net.FileStore().write(self.path, self.runtime)
        self.rules = self.expected(network, self.context)

    def locate(self, request):
        runtime = net.FileStore().read(self.path)
        record = runtime["containers"][0]
        if record["podman-id"] != self.full_id:
            raise net.NetworkError("完整容器 ID 不一致")
        return net.Target(self.path, runtime, record, self.full_id, self.running,
                          self.identity if self.running else None, self.context if self.running else None,
                          {"identity": "fixture", "mother": runtime["mother"]})

    def revalidate(self, target):
        if target.id != self.full_id:
            raise net.NetworkError("目标被替换")

    def expected(self, network, context):
        return firewall.expected_snapshot(network, context)

    def observe(self, target):
        if self.observe_failures:
            exc = self.observe_failures.pop(0)
            if exc:
                raise exc
        return copy.deepcopy(self.rules)

    def apply(self, target, network, context, actual):
        assert actual == self.rules, "被测接口必须冻结并核对当前规则"
        self.writes.append(copy.deepcopy(network))
        if self.failures:
            exc = self.failures.pop(0)
            if exc:
                raise exc
        self.rules = self.expected(network, context)

    def checks(self, target):
        for name in ("ssh", "git"):
            failed = self.check_failures and self.check_failures[0] == name
            if failed:
                self.check_failures.pop(0)
            yield name, {"status": "失败" if failed else "通过"}

    def stopped_rules_absent(self, target, change):
        return self.stopped_absent


@pytest.fixture
def env(tmp_path):
    host = Host(tmp_path)
    request = net.Request("update", tmp_path, tmp_path / "records", "fixture-a",
                          add=[("198.51.100.20", "查询接口文档")])
    return host, request


def approve(host, request, store=None):
    service = net.Maintenance(host, store)
    code, result = service.execute(request)
    assert code == 1, result
    assert result["stage"] == "decision-required"
    request.confirm = result["decision-id"]
    return service.execute(request)


def runtime(host):
    return net.FileStore().read(host.path)


@pytest.mark.parametrize("entries,expected", [
    ([("203.0.113.10", " 构建依赖 ")], {"203.0.113.10/32": " 构建依赖 "}),
    ([("203.0.113.99/24", "依赖"), ("203.0.113.0/24", "依赖")], {"203.0.113.0/24": "依赖"}),
    ([("0.0.0.0/0", "网络实验")], {"0.0.0.0/0": "网络实验"}),
])
def test_entry_normalization(entries, expected):
    assert net.normalize_entries(entries) == expected


@pytest.mark.parametrize("entries", [[("example.test", "依赖")], [("2001:db8::1", "依赖")],
                                       [("203.0.113.10", "  ")], [("203.0.113.10", "a"), ("203.0.113.10/32", "b")]])
def test_invalid_entries(entries):
    with pytest.raises(net.NetworkError):
        net.normalize_entries(entries)


def test_preview_and_confirm_only_target(env):
    host, request = env
    before = host.path.read_bytes()
    other = copy.deepcopy(host.other)
    code, result = net.Maintenance(host).execute(request)
    assert code == 1
    assert host.path.read_bytes() == before and not host.writes
    assert result["container"]["id"] == "a" * 64
    assert result["diff"]["add"][0]["reason"] == "查询接口文档"
    request.confirm = result["decision-id"]
    code, result = net.Maintenance(host).execute(request)
    assert (code, result["stage"]) == (0, "updated")
    assert runtime(host)["network"]["allow"] == ["198.51.100.20/32", "203.0.113.10/32"]
    assert runtime(host)["network"]["allow-reasons"]["198.51.100.20/32"] == "查询接口文档"
    assert "network-change" not in runtime(host)
    assert runtime(host)["unrelated"] == {"keep": True}
    assert host.other == other
    assert result["checks"]["dns-rules"]["status"] == "通过"
    assert result["checks"]["ssh"]["status"] == "通过"
    assert result["checks"]["git"]["status"] == "通过"
    code, result = net.Maintenance(host).execute(request)
    assert (code, result["stage"]) == (0, "noop") and len(host.writes) == 1


def test_delete_keeps_untouched_and_auto(env):
    host, request = env
    approve(host, request)
    before_auto = runtime(host)["network"]["auto-allow"]
    request.add, request.remove, request.confirm = [], ["198.51.100.20"], None
    code, result = approve(host, request)
    assert code == 0
    assert runtime(host)["network"]["allow"] == ["203.0.113.10/32"]
    assert runtime(host)["network"]["auto-allow"] == before_auto


@pytest.mark.parametrize("changes", [
    {"add": [("example.test", "依赖")]}, {"add": [("198.51.100.20", "")]},
    {"add": [], "reasons": [("198.51.100.20", "历史用途")]},
    {"remove": ["198.51.100.20/32"]},
    {"add": [("203.0.113.10", "不同用途")]},
    {"add": [], "remove": ["10.77.0.53"]},
])
def test_invalid_whole_request_is_readonly(env, changes):
    host, request = env
    for key, value in changes.items():
        setattr(request, key, value)
    before = host.path.read_bytes()
    code, result = net.Maintenance(host).execute(request)
    assert code == 2, result
    assert host.path.read_bytes() == before and not host.writes


@pytest.mark.parametrize("changes", [
    {"add": [("203.0.113.10", "下载构建依赖")]},
    {"add": [], "remove": ["198.51.100.99"]},
    {"add": [], "reasons": [("203.0.113.10", "下载构建依赖")]}, {"add": []},
])
def test_noops_dont_rebuild_or_create_receipt(env, changes):
    host, request = env
    for key, value in changes.items():
        setattr(request, key, value)
    before = host.path.read_bytes()
    code, result = net.Maintenance(host).execute(request)
    assert (code, result["stage"]) == (0, "noop")
    assert not list(request.records_root.glob("runtime/*/decisions/*.json"))
    assert not host.writes and before == host.path.read_bytes()


def test_exact_receipt_id_and_kind(env):
    host, request = env
    service = net.Maintenance(host)
    request.confirm = "d-nonexistent"
    assert service.execute(request)[0] == 2
    request.confirm = None
    first = service.execute(request)[1]["decision-id"]
    second = service.execute(request)[1]["decision-id"]
    assert first != second
    request.confirm = second
    assert service.execute(request)[0] == 0
    directory = request.records_root / "runtime/fixture/decisions"
    assert (directory / f"{first}.json").exists()
    assert not (directory / f"{second}.json").exists()
    # 已消费的 ID 不能拿来批准另一个有差异的请求.
    request.add = [("198.51.100.21", "另一个地址")]
    assert service.execute(request)[0] == 2


@pytest.mark.parametrize("drift", ["request", "policy", "identity", "netns", "dns", "reason"])
def test_related_drift_needs_new_receipt(env, drift):
    host, request = env
    service = net.Maintenance(host)
    request.confirm = service.execute(request)[1]["decision-id"]
    if drift == "request":
        request.add = [("198.51.100.21", "查询接口文档")]
    elif drift == "policy":
        value = runtime(host)
        value["network"]["allow"].append("198.51.100.30/32")
        net.FileStore().write(host.path, value)
        host.rules = host.expected(value["network"], host.context)
    elif drift == "identity":
        host.full_id = "b" * 64
        value = runtime(host)
        value["containers"][0]["podman-id"] = host.full_id
        net.FileStore().write(host.path, value)
    elif drift == "netns":
        host.identity["inode"] += 1
    elif drift == "dns":
        host.context["dns"] = ["10.77.0.54"]
    else:
        request.add = [("198.51.100.20", "更改用途")]
    code, result = service.execute(request)
    assert (code, result["stage"]) == (1, "decision-required"), result
    assert result["decision-id"] != request.confirm and not host.writes


@pytest.mark.parametrize("condition", ["stopped", "shared", "blacklist", "unknown", "replacement", "pending"])
def test_preconditions_never_self_repair(env, condition):
    host, request = env
    value = runtime(host)
    if condition == "stopped":
        host.running = False
    elif condition == "shared":
        value["containers"].append({"name": "fixture-b", "state": "stopped"})
    elif condition == "blacklist":
        value["network"]["mode"] = "blacklist"
    elif condition == "unknown":
        host.rules["output"]["rules"].insert(-1, "ip saddr 10.77.0.2/32 ip daddr 198.51.100.99/32 accept")
    elif condition == "replacement":
        host.full_id = "b" * 64
    else:
        value["network-change"] = {"id": "unfinished", "phase": "prepared"}
    net.FileStore().write(host.path, value)
    before = host.path.read_bytes()
    code, result = net.Maintenance(host).execute(request)
    assert code == 2, result
    assert not host.writes and before == host.path.read_bytes()


def test_overlap_and_zero_range_are_explicit(env):
    host, request = env
    request.add = [("203.0.113.99/24", "依赖网段")]
    assert approve(host, request)[0] == 0
    request.add, request.remove, request.confirm = [], ["203.0.113.10"], None
    code, result = net.Maintenance(host).execute(request)
    assert code == 1
    assert result["diff"]["coverage"][0]["covered-by"] == ["203.0.113.0/24"]
    assert "仍被" in result["diff"]["coverage"][0]["effect"]
    request.remove, request.add = [], [("0.0.0.0/0", "受控网络实验")]
    code, result = net.Maintenance(host).execute(request)
    assert code == 1 and "全部 IPv4 地址的全部端口" in result["diff"]["warnings"][0]


def test_historical_reasons_show_and_reason_only_commit(env):
    host, request = env
    value = runtime(host)
    value["network"].pop("allow-reasons")
    value["network"]["allow-reasons"] = {"198.51.100.255/32": "孤立理由不是授权"}
    net.FileStore().write(host.path, value)
    request.action = "show"
    code, result = net.Maintenance(host).execute(request)
    assert code == 0
    assert result["diff"]["entries"] == [{"address": "203.0.113.10/32", "reason": "历史未记录理由", "ports": "全部端口"}]
    assert any(e["ports"] == "仅 udp/tcp 53" for e in result["diff"]["automatic"])
    request.action, request.add = "update", []
    request.reasons = [("203.0.113.10", "继承自旧任务,用途未核实")]
    code, result = approve(host, request)
    assert code == 0 and not host.writes and "network-change" not in runtime(host)
    assert runtime(host)["network"]["allow-reasons"]["203.0.113.10/32"] == "继承自旧任务,用途未核实"


def test_reason_only_preserves_legacy_rule_representation(env):
    host, request = env
    value = runtime(host)
    value["network"]["allow"] = ["203.0.113.10", "203.0.113.10/32"]
    value["network"]["auto-allow"].append("10.77.0.1")
    net.FileStore().write(host.path, value)
    host.rules = host.expected(value["network"], host.context)
    request.add, request.reasons = [], [("203.0.113.10", "更正理由")]
    code, result = approve(host, request)
    assert code == 0, result
    assert runtime(host)["network"]["allow"] == value["network"]["allow"]
    assert runtime(host)["network"]["auto-allow"] == value["network"]["auto-allow"]
    assert not host.writes
    request.action = "show"
    code, result = net.Maintenance(host).execute(request)
    assert code == 0 and result["checks"]["rules"]["status"] == "通过"


def test_removing_user_entry_still_covered_by_identical_auto_address(env):
    host, request = env
    request.add = [("10.77.0.1", "显式网关用户条目")]
    code, preview = net.Maintenance(host).execute(request)
    assert code == 1 and preview["diff"]["coverage"][0]["already-allowed-by"] == ["10.77.0.1/32"]
    request.confirm = preview["decision-id"]
    assert net.Maintenance(host).execute(request)[0] == 0
    request.add, request.remove, request.confirm = [], ["10.77.0.1"], None
    code, result = net.Maintenance(host).execute(request)
    assert code == 1
    assert result["diff"]["coverage"][0]["covered-by"] == ["10.77.0.1/32"]
    assert "仍被" in result["diff"]["coverage"][0]["effect"]


def test_reason_only_cannot_smuggle_dns_sync(env):
    host, request = env
    host.context["dns"] = ["10.77.0.54"]
    request.add, request.reasons = [], [("203.0.113.10", "更正理由")]
    before = host.path.read_bytes()
    assert net.Maintenance(host).execute(request)[0] == 2
    assert before == host.path.read_bytes() and not host.writes
    request.reasons = []
    assert approve(host, request)[0] == 0
    assert runtime(host)["network"]["auto-dns"] == ["10.77.0.54"]
    request.confirm, request.reasons = None, [("203.0.113.10", "更正理由")]
    assert approve(host, request)[0] == 0 and len(host.writes) == 1


def test_dns_and_user_change_approved_together(env):
    host, request = env
    host.context["dns"] = ["10.77.0.54"]
    assert approve(host, request)[0] == 0
    assert runtime(host)["network"]["auto-dns"] == ["10.77.0.54"]
    assert runtime(host)["network"]["allow"] == ["198.51.100.20/32", "203.0.113.10/32"]


class FailingStore(net.FileStore):
    def __init__(self, failure):
        self.failure = failure
        self.failed = False

    def write(self, path, value):
        phase = value.get("network-change", {}).get("phase")
        should_fail = ((self.failure == "prepared" and phase == "prepared") or
                       (self.failure == "applied" and phase == "applied") or
                       (self.failure == "commit" and "198.51.100.20/32" in value.get("network", {}).get("allow", []) and not phase))
        if should_fail and not self.failed:
            self.failed = True
            # 模拟 replace 已发生但目录同步失败, 不能假设旧文件仍在.
            super().write(path, value)
            raise OSError("注入持久化失败")
        return super().write(path, value)


@pytest.mark.parametrize("failure", ["apply", "rules", "ssh", "git", "prepared", "applied", "commit"])
def test_failure_restores_old_verified_state(env, failure):
    host, request = env
    old = runtime(host)
    store = FailingStore(failure)
    if failure == "apply":
        host.failures = [net.NetworkError("注入应用失败", 3)]
    if failure in ("ssh", "git"):
        host.check_failures = [failure]
    if failure == "rules":
        # 基线观察成功, 写后观察失败, 随后读取已知新规则允许回退.
        host.observe_failures = [None, None, net.NetworkError("写后观察失败", 3)]
    code, result = approve(host, request, store)
    assert code == (2 if failure == "prepared" else 3), result
    assert runtime(host) == old
    assert host.rules == host.expected(old["network"], host.context)
    assert result["pending"] is None
    if failure == "prepared":
        assert not host.writes
    else:
        assert result["stage"] == "rolled-back"


@pytest.mark.parametrize("unsettled", [False, True])
def test_failed_rollback_or_unsettled_writer_retains_evidence(env, unsettled):
    host, request = env
    host.failures = [net.NetworkError("应用失败", 3, settled=not unsettled), net.NetworkError("回退也失败", 3)]
    code, result = approve(host, request)
    assert (code, result["stage"]) == (3, "recovery-required")
    assert runtime(host)["network-change"]["phase"] == "recovery-required"
    assert len(host.writes) == (1 if unsettled else 2)
    assert net.Maintenance(host).execute(request)[0] == 2
    assert host.running
    if unsettled:
        request.action, request.add, request.confirm = "recover", [], None
        assert net.Maintenance(host).execute(request)[0] == 2


@pytest.mark.parametrize("phase", ["prepared", "applied"])
def test_interruption_then_finite_recovery(env, phase):
    host, request = env
    class InterruptHost(Host):
        def apply(self, target, network, context, actual):
            if phase == "applied":
                self.rules = self.expected(network, context)
            raise KeyboardInterrupt()
    host.__class__ = InterruptHost
    service = net.Maintenance(host)
    request.confirm = service.execute(request)[1]["decision-id"]
    with pytest.raises(KeyboardInterrupt):
        service.execute(request)
    assert "network-change" in runtime(host)
    assert service.execute(request)[0] == 2
    host.__class__ = Host
    request.action, request.add, request.confirm = "recover", [], None
    before = host.path.read_bytes()
    code, result = service.execute(request)
    assert (code, result["stage"]) == (1, "decision-required")
    assert host.path.read_bytes() == before
    request.confirm = result["decision-id"]
    code, result = service.execute(request)
    assert (code, result["stage"]) == (0, "recovered")
    assert "network-change" not in runtime(host)


def make_pending(host, request):
    host.failures = [net.NetworkError("应用失败", 3), net.NetworkError("回退失败", 3)]
    assert approve(host, request)[0] == 3
    request.action, request.add, request.confirm = "recover", [], None


@pytest.mark.parametrize("condition", ["stopped", "unknown", "replacement", "failure", "stopped-present"])
def test_recover_branches(env, condition):
    host, request = env
    make_pending(host, request)
    if condition.startswith("stopped"):
        host.running = False
        host.stopped_absent = condition != "stopped-present"
    if condition == "unknown":
        host.rules["output"]["rules"].append("未知规则")
    if condition == "replacement":
        value = runtime(host)
        host.full_id = value["containers"][0]["podman-id"] = "b" * 64
        net.FileStore().write(host.path, value)
    before = host.path.read_bytes()
    code, result = net.Maintenance(host).execute(request)
    if condition in ("unknown", "replacement", "stopped-present"):
        assert code == 2 and before == host.path.read_bytes()
    else:
        assert code == 1
        request.confirm = result["decision-id"]
        if condition == "failure":
            host.failures = [net.NetworkError("恢复失败", 3)]
        writes = len(host.writes)
        code, result = net.Maintenance(host).execute(request)
        if condition == "stopped":
            assert (code, result["stage"]) == (0, "recovered")
            assert not host.running and len(host.writes) == writes
        else:
            assert (code, result["stage"]) == (3, "recovery-required")
            assert "network-change" in runtime(host)


def test_recover_no_pending_is_noop(env):
    host, request = env
    request.action = "recover"
    assert net.Maintenance(host).execute(request)[1]["stage"] == "noop"
    assert not host.writes and not list(request.records_root.glob("runtime/*/decisions/*.json"))


def test_stopped_show_is_not_health_claim(env):
    host, request = env
    host.running, request.action = False, "show"
    code, result = net.Maintenance(host).execute(request)
    assert code == 0 and result["checks"]["rules"]["status"] == "未检查"
    assert "不可取得" in result["checks"]["rules"]["detail"]


def test_store_permissions_and_file_and_directory_sync(tmp_path, monkeypatch):
    path = tmp_path / "private.json"
    calls = []
    real = os.fsync
    def track(fd):
        calls.append(os.fstat(fd).st_mode)
        real(fd)
    monkeypatch.setattr(os, "fsync", track)
    net.FileStore().write(path, {"v": 1})
    assert len(calls) == 2 and path.stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.glob(".*.tmp"))


def test_real_process_exit_codes_are_preserved():
    runner = net.BoundedRunner()
    result = runner.checked([sys.executable, "-c", "import sys; print('evidence'); sys.exit(128)"])
    assert result.returncode == 128 and result.stdout == "evidence\n"
    assert result.settled and not result.timed_out


def test_real_process_group_kills_late_writer(tmp_path):
    marker = tmp_path / "late"
    code = ("import os,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
            "pid=os.fork(); time.sleep(4); "
            f"open({str(marker)!r},'w').write('late')")
    result = net.BoundedRunner().run([sys.executable, "-c", code], timeout=0.1)
    assert result.timed_out and result.settled
    time.sleep(1.9)
    assert not marker.exists()


def test_unsettled_process_contract(monkeypatch):
    monkeypatch.setattr(net.BoundedRunner, "group_alive", staticmethod(lambda pgid: True))
    # 不用真实等 30 秒, 同一接口缩短单次预算; 2+2 收尾仍按合同执行.
    result = net.BoundedRunner().run([sys.executable, "-c", "pass"], timeout=0.1)
    assert result.timed_out and not result.settled


def nft_json_fixture():
    data = [{"table": {"family": "inet", "name": "swt", "handle": 1}}]
    def match(left, right, op="=="):
        return {"match": {"op": op, "left": left, "right": right}}
    for name in ("forward", "input", "output"):
        data.append({"chain": {"family": "inet", "table": "swt", "name": name, "type": "filter", "hook": name, "prio": 10, "policy": "accept"}})
        common = [match({"ct": {"key": "state"}}, ["established", "related"], "in")]
        if name == "output":
            common.append(match({"ct": {"key": "direction"}}, "reply"))
        bodies = [[match({"meta": {"key": "nfproto"}}, "ipv6"), {"drop": None}],
                  [*common, {"accept": None}],
                  [match({"payload": {"protocol": "ip", "field": "saddr"}}, "10.77.0.2"), {"drop": None}]]
        for expr in bodies:
            data.append({"rule": {"family": "inet", "table": "swt", "chain": name, "handle": len(data), "expr": expr}})
    return {"nftables": data}


def test_nft_observation_ignores_only_handles_and_counters():
    data = nft_json_fixture()
    before = firewall.snapshot_json(data, "10.77.0.2")
    for item in data["nftables"]:
        if "rule" in item:
            item["rule"]["handle"] += 100
            item["rule"]["expr"].insert(0, {"counter": {"packets": 123, "bytes": 456}})
    assert firewall.snapshot_json(data, "10.77.0.2") == before


@pytest.mark.parametrize("change", ["unknown", "extra-chain", "policy", "late-ipv6", "late-reply", "broad-established"])
def test_nft_unknown_structure_is_not_silently_accepted(change):
    data = nft_json_fixture()
    items = data["nftables"]
    if change == "unknown":
        items.append({"set": {"family": "inet", "table": "swt", "name": "unknown"}})
    elif change == "extra-chain":
        items.append({"chain": {"name": "unknown"}})
    elif change == "policy":
        items[1]["chain"]["policy"] = "drop"
    elif change == "late-ipv6":
        items[2], items[3] = items[3], items[2]
    elif change == "late-reply":
        items[3], items[4] = items[4], items[3]
    else:
        # 新白名单实际比预期更宽, 即使是已知 blacklist 回程形式也不等于匹配.
        output = [i["rule"] for i in items if i.get("rule", {}).get("chain") == "output"]
        output[1]["expr"].pop(1)
        assert firewall.snapshot_json(data, "10.77.0.2") != firewall.snapshot_json(nft_json_fixture(), "10.77.0.2")
        return
    with pytest.raises(ValueError):
        firewall.snapshot_json(data, "10.77.0.2")


def test_lock_identity_is_shared_across_directories_and_is_private(tmp_path, monkeypatch):
    namespace = tmp_path / "netns"
    namespace.touch()
    alias = tmp_path / "other-records-root" / "netns"
    alias.parent.mkdir()
    os.link(namespace, alias)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "run"))
    with firewall.write_lock(str(namespace)):
        with pytest.raises(ValueError, match="写锁忙"):
            with firewall.write_lock(str(alias), timeout=0.05):
                pytest.fail("同一 namespace 不应取得第二把写锁")
    stat = namespace.stat()
    lock = tmp_path / "run/swt-net-locks" / f"{stat.st_dev}-{stat.st_ino}.lock"
    assert lock.stat().st_mode & 0o777 == 0o600
    assert lock.parent.stat().st_mode & 0o777 == 0o700
    with pytest.raises(ValueError, match="身份变化"):
        with firewall.write_lock(str(namespace), expected="0:0"):
            pytest.fail("不应锁定替换 namespace")


def test_network_cli_syntax_errors_still_have_protocol(capsys):
    assert swt.main(["network", "update", "--add", "198.51.100.20"]) == 2
    result = json.loads(capsys.readouterr().out.splitlines()[-1].removeprefix("NETWORK "))
    assert result["stage"] == "rejected" and result["error"]["name"] == "ArgumentError"


def test_cli_network_contract_and_missing_tools(tmp_path, monkeypatch, capsys):
    args = ["network", "update", "--repo", str(tmp_path), "--records-root", str(tmp_path / "records"), "--name", "fixture-a"]
    def require(name):
        if name == "nft":
            raise swt.SwtEnvError("缺少环境命令: nft")
    monkeypatch.setattr(swt, "require_command", require)
    assert swt.main(args) == 4
    result = json.loads(capsys.readouterr().out.splitlines()[-1].removeprefix("NETWORK "))
    assert result["stage"] == "unsupported" and "nft" in result["error"]["message"]
    assert not (tmp_path / "records").exists()


def test_cli_uses_module_and_last_line_network(env, monkeypatch, capsys):
    host, request = env
    monkeypatch.setattr(swt, "require_command", lambda name: None)
    monkeypatch.setattr(swt, "resolve_repo", lambda value: request.repo)
    monkeypatch.setattr(swt, "acquire_lock", lambda *args: open(os.devnull))
    monkeypatch.setattr(swt, "NetworkHost", lambda req: host)
    args = ["network", "update", "--name", request.name, "--records-root", str(request.records_root),
            "--add", "198.51.100.20", "查询接口文档"]
    assert swt.main(args) == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("DECIDE ") and lines[-1].startswith("NETWORK ")
    result = json.loads(lines[-1].removeprefix("NETWORK "))
    assert swt.main([*args, "--confirm", result["decision-id"]]) == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1].removeprefix("NETWORK "))["stage"] == "updated"


def test_resume_and_birth_block_pending_before_any_resources(env, monkeypatch):
    host, request = env
    value = runtime(host)
    value["network-change"] = {"id": "pending", "phase": "applied"}
    monkeypatch.setattr(swt, "locate_pair_runtime", lambda *a, **kw: (host.path, value))
    with pytest.raises(swt.PreconditionError, match="未完成网络变更"):
        swt.resume(swt.parse_args(["resume", "--name", "fixture-a"]), request.repo)
    monkeypatch.setattr(swt, "find_mother", lambda *a: (request.repo / "mother", False))
    monkeypatch.setattr(swt, "resolve_pair_identity", lambda *a: "fixture")
    net.FileStore().write(host.path, value)
    args = swt.parse_args(["birth", "--branch", "feat/fixture", "--records-root", str(request.records_root)])
    with pytest.raises(swt.PreconditionError, match="未完成网络变更"):
        swt.birth(args, request.repo)


@pytest.mark.parametrize("flags", [["--allow", "203.0.113.10"], ["--allow-entry", "203.0.113.10", ""],
                                   ["--allow-entry", "2001:db8::1", "依赖"]])
def test_birth_rejects_invalid_before_container_create(tmp_path, monkeypatch, flags):
    monkeypatch.setattr(swt, "find_mother", lambda *a: (tmp_path / "mother", False))
    monkeypatch.setattr(swt, "resolve_pair_identity", lambda *a: "fixture")
    args = swt.parse_args(["birth", "--branch", "feat/fixture", "--records-root", str(tmp_path / "records"), *flags])
    with pytest.raises(swt.PreconditionError):
        swt.birth(args, tmp_path)
    assert not (tmp_path / "records").exists()
