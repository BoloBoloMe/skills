"""Herdr 接线边界测试, HOME/XDG_STATE_HOME 全隔离, 不触真实连接配置."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "workflow/use-sandbox-worktree/scripts"
sys.path.insert(0, str(SCRIPTS))
import herdr_machine as machine


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    key = tmp_path / "key with space"
    key.write_text("fake private key, not used for a connection")
    record = {"name": "swt-demo", "podman-id": "container-1", "ssh-port": 49201,
              "ssh_private_key": str(key)}
    reserved = machine.reservation(tmp_path / "records with space", "pair", record)
    profiles = []
    calls = []

    def cli(*args):
        calls.append(args)
        if args == ("list", "--json"):
            return json.dumps(profiles)
        if args[0] == "add":
            profiles.append({"id": "a" * 32, "label": args[3], "target": args[1],
                             "session": args[5], "enabled": True})
            return "added"
        if args[0] == "remove":
            profiles[:] = [p for p in profiles if p["id"] != args[1]]
            return "removed"
        raise AssertionError(args)

    monkeypatch.setattr(machine, "_cli", cli)
    return record, reserved, profiles, calls


def test_connect_is_idempotent_and_openssh_resolves_private_alias(sandbox):
    record, reserved, profiles, calls = sandbox
    original = "Host *\n    ServerAliveInterval 45\n"
    config = Path.home() / ".ssh/config"
    config.parent.mkdir(parents=True)
    config.write_text(original)
    connected = machine.connect(reserved, record)
    assert connected["status"] == "registered"
    assert connected["id"] == profiles[0]["id"]
    machine.connect(connected, record)
    assert len([c for c in calls if c[0] == "add"]) == 1
    assert config.read_text().endswith(original)
    assert config.read_text().count("Include ") == 1
    assert Path(reserved["ssh-config"]).stat().st_mode & 0o777 == 0o600
    # 真 OpenSSH 解析 Include/带空格的路径/独立凭据, 不连接任何服务.
    result = subprocess.run(["ssh", "-G", "-F", str(config), reserved["target"]],
                            capture_output=True, text=True, check=True)
    assert "hostname 127.0.0.1\n" in result.stdout
    assert "port 49201\n" in result.stdout
    assert "identitiesonly yes\n" in result.stdout
    assert "identityagent none\n" in result.stdout
    assert f"identityfile {record['ssh_private_key']}\n" in result.stdout
    machine.disconnect(connected)
    assert profiles == []
    assert config.read_text() == original
    assert not Path(reserved["ssh-config"]).exists()
    assert Path(record["ssh_private_key"]).is_file()  # 由生命周期稍后清理
    machine.disconnect(connected)  # 幂等重入


def test_crash_after_add_recovers_by_target_without_duplicate(sandbox):
    record, reserved, profiles, calls = sandbox
    first = machine.connect(reserved, record)
    # 模拟 add 成功但 id 未写入 runtime 就中断, 仅持有原 reservation.
    second = machine.connect(reserved, record)
    assert first["id"] == second["id"]
    assert len([c for c in calls if c[0] == "add"]) == 1


def test_cleanup_only_owns_its_profile_and_preserves_other_ssh_config(sandbox):
    record, reserved, profiles, calls = sandbox
    connected = machine.connect(reserved, record)
    profiles.append({"id": "b" * 32, "label": record["name"], "target": "other-host",
                     "session": "default", "enabled": True})
    config = Path.home() / ".ssh/config"
    config.write_text(config.read_text() + "Host personal\n    HostName personal.invalid\n")
    machine.disconnect(connected)
    assert len(profiles) == 1 and profiles[0]["target"] == "other-host"
    assert "personal.invalid" in config.read_text()
    assert [c for c in calls if c[0] == "remove"] == [("remove", "a" * 32)]


def test_retargeted_owned_machine_is_not_deleted(sandbox):
    record, reserved, profiles, calls = sandbox
    connected = machine.connect(reserved, record)
    profiles[0]["target"] = "someone-else"
    with pytest.raises(machine.MachineError, match="改向"):
        machine.disconnect(connected)
    assert not [c for c in calls if c[0] == "remove"]
    assert Path(reserved["ssh-config"]).exists()


def test_remove_failure_keeps_ssh_material_for_retry(sandbox, monkeypatch):
    record, reserved, profiles, calls = sandbox
    connected = machine.connect(reserved, record)
    cli = machine._cli

    def fail(*args):
        if args[0] == "remove":
            raise machine.MachineError("test failure")
        return cli(*args)

    monkeypatch.setattr(machine, "_cli", fail)
    with pytest.raises(machine.MachineError):
        machine.disconnect(connected)
    assert Path(reserved["ssh-config"]).exists()
    assert "Include " in (Path.home() / ".ssh/config").read_text()


def test_container_recreation_and_other_record_roots_get_unique_alias(sandbox, tmp_path):
    record, reserved, profiles, calls = sandbox
    assert machine.reservation(tmp_path / "elsewhere", "pair", record)["target"] != reserved["target"]
    other = {**record, "podman-id": "new-container-id"}
    assert machine.reservation(tmp_path / "records with space", "pair", other)["target"] != reserved["target"]


def test_cli_never_prompts_for_authentication_or_approves_server_replacement(monkeypatch):
    seen = {}

    class Process:
        returncode = 0
        def communicate(self, timeout=None):
            return "[]", ""

    def popen(command, **kwargs):
        seen.update(command=command, **kwargs)
        return Process()

    monkeypatch.setattr(subprocess, "Popen", popen)
    assert machine._cli("list", "--json") == "[]"
    assert seen["stdin"] == subprocess.DEVNULL
    assert seen["env"]["SSH_ASKPASS_REQUIRE"] == "never"
    assert seen["command"] == ["herdr", "machine", "list", "--json"]
    assert seen["start_new_session"] is True


def test_cli_timeout_kills_ssh_process_group(monkeypatch):
    killed = []

    class Process:
        pid = 12345
        def communicate(self, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired("herdr", timeout)
            return "", ""

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: Process())
    monkeypatch.setattr(os, "killpg", lambda pid, sig: killed.append(pid))
    with pytest.raises(machine.MachineError, match="子进程组已停止"):
        machine._cli("add", "fixture.invalid")
    assert killed == [12345]


def test_real_herdr_list_and_remove_are_compatible_in_isolated_state(tmp_path, monkeypatch):
    if not shutil.which("herdr"):
        pytest.skip("本机没有 Herdr")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    catalog = tmp_path / "herdr/client/endpoints.json"
    catalog.parent.mkdir(parents=True)
    profile = {"id": "a" * 32, "label": "fixture", "target": "fixture.invalid",
               "session": "default", "enabled": True}
    catalog.write_text(json.dumps({"version": 1, "ssh": [profile]}))
    listed = machine._profiles()
    assert listed[0]["id"] == profile["id"]
    machine._cli("remove", profile["id"])
    assert machine._profiles() == []


def load_swt():
    spec = importlib.util.spec_from_file_location("swt_herdr_test", SCRIPTS / "swt.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_lifecycle_persists_intent_before_add_and_failure_can_retry(sandbox, tmp_path):
    record, reserved, profiles, calls = sandbox
    swt = load_swt()
    runtime = {"containers": [record], "stage": "ssh-ready"}
    path = tmp_path / "runtime.json"

    def fail(machine_record, target):
        saved = json.loads(path.read_text())["containers"][0]["herdr-machine"]
        assert saved["status"] == "pending"
        raise machine.MachineError("cannot connect")

    with patch.object(machine, "connect", fail):
        with pytest.raises(swt.SwtError) as error:
            swt.ensure_herdr_machine(tmp_path / "records", "pair", runtime, path, record)
    assert error.value.code == 3
    assert json.loads(path.read_text())["containers"][0]["herdr-machine"]["status"] == "failed"
    swt.ensure_herdr_machine(tmp_path / "records", "pair", runtime, path, record)
    assert record["herdr-machine"]["status"] == "registered"
    assert runtime["stage"] == "ssh-ready"


@pytest.mark.parametrize("fail_remove", [False, True])
def test_terminate_removes_machine_before_credentials_and_keeps_failed_cleanup_retryable(sandbox, tmp_path, monkeypatch, fail_remove):
    record, reserved, profiles, calls = sandbox
    connected = machine.connect(reserved, record)
    record["herdr-machine"] = connected
    record["dirty"] = {"reachable": True, "uncommitted": 0, "unpushed": 0}
    swt = load_swt()
    runtime = {"containers": [record], "stage": "born", "mother": {"branch": "feature/x", "dir": str(tmp_path)}}
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(runtime))
    target = {**record, "_runtime-file": path}
    monkeypatch.setattr(swt, "load_repo_runtimes", lambda *a: [(path, runtime)])
    monkeypatch.setattr(swt, "terminate_container_candidates", lambda *a: ([target], [{"name": record["name"]}]))
    monkeypatch.setattr(swt, "handle_dirty_decision", lambda *a: (False, None))
    monkeypatch.setattr(swt, "terminate_decision_fingerprint", lambda *a: {})
    monkeypatch.setattr(swt, "live_container_netns", lambda *a: None)
    monkeypatch.setattr(swt, "stop_pair_daemons", lambda *a: None)
    monkeypatch.setattr(swt, "stop_git_bridge", lambda *a: None)
    monkeypatch.setattr(swt, "revoke_container_session", lambda *a: None)
    monkeypatch.setattr(swt, "terminate_state", lambda *a: None)
    events = []

    def run(command, **kwargs):
        assert command[:2] == ["podman", "rm"]
        events.append("container-removed")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(swt, "run", run)
    real_disconnect = machine.disconnect

    def disconnect(value):
        assert events == ["container-removed"]
        assert Path(record["ssh_private_key"]).exists()
        if fail_remove:
            raise machine.MachineError("fixture removal failure")
        real_disconnect(value)

    monkeypatch.setattr(machine, "disconnect", disconnect)
    args = type("Args", (), {"records_root": tmp_path, "branch": None, "name": record["name"], "force": False})()
    if fail_remove:
        with pytest.raises(swt.SwtError, match="Herdr machine 尚未移除"):
            swt.terminate(args, tmp_path)
        assert Path(record["ssh_private_key"]).exists()
        assert json.loads(path.read_text())["containers"]
        assert profiles
    else:
        assert swt.terminate(args, tmp_path) == 0
        assert not profiles
        assert not Path(record["ssh_private_key"]).exists()
        assert json.loads(path.read_text())["stage"] == "idle"


def test_status_observation_preserves_herdr_registration(sandbox, tmp_path, monkeypatch):
    swt = load_swt()
    record, reserved, profiles, calls = sandbox
    record.update({"branch": "feature/x", "network-ip": "10.0.2.100", "herdr-machine": {"id": "owned-profile", "status": "registered"}})
    row = {"Names": [record["name"]]}
    detail = {"Id": record["podman-id"], "State": {"Status": "running"}}
    monkeypatch.setattr(swt, "podman_json", lambda command: [row] if command[1] == "ps" else [detail])
    monkeypatch.setattr(swt, "run", lambda command, **kw: subprocess.CompletedProcess(command, 0, "22/tcp -> 0.0.0.0:49201\n", ""))
    monkeypatch.setattr(swt, "ref_tip", lambda *a: None)
    monkeypatch.setattr(swt, "ssh_container_git_status", lambda *a: None)
    observed = swt.podman_container_state(tmp_path, {"containers": [record]})
    assert observed[0]["herdr-machine"]["id"] == "owned-profile"


@pytest.mark.parametrize("malformed", [False, True])
def test_list_delivery_metadata_stays_with_its_container(sandbox, tmp_path, monkeypatch, capsys, malformed):
    swt = load_swt()
    rows, details, runtimes = [], {}, []
    for index in (1, 2):
        name = f"swt-{index}"
        record = {"name": name, "branch": f"feature/{index}", "clone_dir": f"/code/{index}",
                  "display": "absent", "host-display": "absent", "ssh_private_key": f"/key/{index}",
                  "herdr-machine": ["broken"] if malformed else {"status": "registered", "label": name, "id": str(index)}}
        rows.append({"Names": [name], "Labels": {"sandbox-worktree.repo": f"/repo/{index}"}})
        details[name] = {"Name": name, "State": {"Status": "running"}, "Id": str(index) * 64}
        runtimes.append({"containers": [record], "mother_dir": f"/mother/{index}",
                         "host-session-id": f"host-{index}"})
    monkeypatch.setattr(swt, "require_command", lambda *a: None)
    monkeypatch.setattr(swt, "podman_json", lambda *a: rows)
    monkeypatch.setattr(swt, "scan_all_runtime_records", lambda *a: (runtimes, []))
    monkeypatch.setattr(swt, "inspect_containers_bulk", lambda *a: (details, ""))
    monkeypatch.setattr(swt, "list_lan_groups", lambda *a: ([], None))
    monkeypatch.setattr(swt, "run", lambda command, **kw: subprocess.CompletedProcess(
        command, 0, "22/tcp -> 0.0.0.0:49201\n8800/tcp -> 0.0.0.0:49202\n", ""))
    args = type("Args", (), {"records_root": tmp_path})()
    assert swt.list_sandbox(args) == 0
    payload = json.loads(capsys.readouterr().out.splitlines()[-1][5:])
    for index, entry in enumerate(payload["containers"], 1):
        text = "\n".join(entry["access-entries"])
        assert f"host 会话 sessionId: host-{index}" in text
        assert f"容器代码路径: /code/{index}" in text
        assert f"母体路径: /mother/{index}" in text
        assert "登录密码: sandbox" in text
        assert f"host-{3-index}" not in text
        assert ("Herdr machine: 未接线/失败" if malformed else "宿主登记记录") in text


def test_host_session_facts_are_creation_snapshot_not_current_environment(sandbox, monkeypatch, tmp_path):
    swt = load_swt()
    monkeypatch.setenv("PI_SESSION_ID", "another-session")
    runtime = {"host-session-id": "creator-session", "mother_dir": "/tmp/mother"}
    facts = swt.agent_env_facts(type("Args", (), {"mode": "blacklist"})(),
                               tmp_path, "feature/x", runtime, tmp_path)
    assert facts["host_session_id"] == "creator-session"
    target = swt.stage_agent_prompts(tmp_path, "pair", "swt-demo", net_facts=facts)
    for name, _ in swt.AGENT_PROMPT_MOUNTS:
        text = (target / name).read_text()
        assert "host 会话 sessionId: creator-session" in text
        assert "another-session" not in text
    assert "host 会话 sessionId: creator-session" in (target / "docs/identity.md").read_text()
