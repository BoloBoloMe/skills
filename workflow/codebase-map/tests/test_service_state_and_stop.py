"""ISSUE-04 状态真实性与 stop 语义用例.

覆盖: TC-004 (AC-004 主用例: state.json 字段齐全与权限), TC-04-06 (残留
记录判死重起), TC-04-07 (两种不一致都 state_mismatch), TC-04-08 (stop 语义
与重复 stop), TC-04-10 (两类 no_data_keys).

隔离纪律: 每个用例独立运行时目录与独立高位端口, 不占 8090; 收尾 fixture
stop 加强杀, 不残留进程.
"""
from __future__ import annotations

import datetime
import os
import signal
import stat

import pytest

from codemap_service_helpers import (
    SERVICE_SCRIPT,
    CodemapSrv,
    free_port,
    http_status,
    port_connectable,
    stdout_json,
    use_temp_home,
)


@pytest.fixture
def srv(tmp_path):
    controller = CodemapSrv(tmp_path)
    # 空 HOME (无 lan-address): serve 恒走 address_missing 形态, 不受宿主记录影响
    use_temp_home(controller, tmp_path)
    yield controller
    controller.cleanup()


def _assert_state_fields_complete(state, srv, pid):
    """TC-004 的逐字段核对 (TECHNICAL "state.json 字段")."""
    assert state["version"] == 1
    assert state["port"] == srv.port
    assert state["last_port"] == srv.port
    assert state["last_url"] == f"http://127.0.0.1:{srv.port}/"
    assert state["pid"] == pid
    assert state["bind"] == "0.0.0.0"
    started = datetime.datetime.fromisoformat(state["started_at"])
    assert started.utcoffset() == datetime.timedelta(0), "started_at 应为 UTC ISO8601"
    assert state["stopped_at"] is None
    assert state["command_path"] == str(SERVICE_SCRIPT)
    assert state["serve_root"] == str(srv.serve_root)
    assert state["log_path"] == str(srv.base / "logs" / "service.log")
    assert state["runtime_dir"] == str(srv.base)
    assert state["data_keys"] and state["data_keys"][0]["key"].endswith(".cc.json")
    for entry in state["data_keys"]:
        assert set(entry) == {"key", "source_cc_json", "built_at", "bytes"}


def test_tc004_state_json_complete_and_permissions(srv):
    """TC-004: 首次 serve 成功后 state.json 字段齐全 (逐字段核对), 文件 0600,
    目录 0700, bind == 0.0.0.0."""
    srv.prime()
    obj, _ = srv.serve()
    assert obj["bind"] == "0.0.0.0"
    state = srv.read_state()
    _assert_state_fields_complete(state, srv, obj["pid"])
    # 权限: 目录 0700, 文件 0600
    assert stat.S_IMODE(srv.base.stat().st_mode) == 0o700
    for sub in ("serve-root", "cache", "logs"):
        assert stat.S_IMODE((srv.base / sub).stat().st_mode) == 0o700
    assert stat.S_IMODE(srv.state_path.stat().st_mode) == 0o600
    assert stat.S_IMODE((srv.base / "lock").stat().st_mode) == 0o600
    assert stat.S_IMODE((srv.base / "logs" / "service.log").stat().st_mode) == 0o600


def test_tc_04_06_stale_pid_restarted_on_recorded_port(srv):
    """TC-04-06: 手工把 state.json 的 pid 改成不存在的值, serve 说明旧实例已死
    并按记录端口重起, 新 pid 与端口可用."""
    srv.prime(last_port=srv.port, stopped_at="2026-01-01T00:00:00+00:00")
    stale_pid = srv.dead_pid()
    srv.write_state(pid=stale_pid)

    obj, proc = srv.serve()
    assert obj["success"] is True and obj["reused"] is False
    assert obj["port"] == srv.port, "应按记录端口重起"
    assert "旧实例已死" in obj["note"], f"输出应说明旧实例已死: {obj}"
    assert obj["pid"] != stale_pid
    status, _ = http_status(srv.port)
    assert status == 200
    state = srv.read_state()
    assert state["pid"] == obj["pid"], "state.json 应更新为新 pid"


def test_tc_04_07_both_mismatches_report_state_mismatch(srv):
    """TC-04-07: 两种不一致各一次, 都返回 state_mismatch, 退出码非 0, 不接管
    端口, 不重起:
    a) pid 活着但端口无人应答 (SIGSTOP 真守护, 探活第三步超时);
    b) 端口被别的 HTTP 程序占着, state 记着那个外来 pid (探活三步会误判活,
       但监听者不是本服务, 必须拦下)."""
    # --- a) pid 活着但端口无人应答 ---
    srv.prime()
    first, _ = srv.serve()
    daemon_pid = first["pid"]

    os.kill(daemon_pid, signal.SIGSTOP)
    srv.paused_pids.add(daemon_pid)  # 收尾先 SIGCONT, 否则 stop 会等满 10 秒
    obj, proc = srv.serve(expect_success=False, timeout=30)
    assert proc.returncode != 0
    assert obj["error"]["code"] == "state_mismatch"
    state = srv.read_state()
    assert state["pid"] == daemon_pid, "不一致时报错不重起, 状态不动"
    assert srv.daemon_pids_for_port() == [daemon_pid], "不接管: 原守护未被替换"

    # --- b) 端口被别的程序占着, state 记着外来 pid ---
    port_b = free_port()
    foreign = srv.foreign_http_server(port_b)
    other = CodemapSrv(srv.base.parent / "mismatch-b")
    try:
        other.port = port_b
        other.prime(pid=foreign.pid, last_port=port_b)
        obj_b, proc_b = other.serve(expect_success=False)
        assert proc_b.returncode != 0
        assert obj_b["error"]["code"] == "state_mismatch"
        # 不接管端口: 外来服务仍应答, 本工具没有新起守护
        status, _ = http_status(port_b)
        assert status == 200, "外来服务应原样还在"
        assert other.daemon_pids_for_port() == []
        assert other.read_state()["pid"] == foreign.pid, "状态未被改动"
    finally:
        other.cleanup()


def test_tc_04_08_stop_semantics_and_idempotent_repeat(srv):
    """TC-04-08: stop 后 GET / 失败, state.json pid 为 null 且 stopped_at 有值,
    port/last_port/last_url 保留; 重复 stop 退出码 0 且说明当前没有在跑的服务."""
    srv.prime()
    srv.serve()
    before = srv.read_state()
    assert before["pid"] is not None

    stop_proc = srv.stop()
    obj = stdout_json(stop_proc)
    assert stop_proc.returncode == 0
    assert obj["success"] is True and obj["stopped"] is True
    assert obj["pid"] == before["pid"] and obj["port"] == srv.port

    status, _ = http_status(srv.port)
    assert status is None and not port_connectable(srv.port), "旧地址应立即失效"
    after = srv.read_state()
    assert after["pid"] is None
    assert after["stopped_at"], "stopped_at 应有值"
    assert after["port"] == before["port"]
    assert after["last_port"] == before["last_port"]
    assert after["last_url"] == before["last_url"], "端口留痕应保留 (m25 D018)"

    again_proc = srv.stop()
    again = stdout_json(again_proc)
    assert again_proc.returncode == 0, f"重复 stop 应幂等成功: {again}"
    assert again["success"] is True and again["stopped"] is False
    assert "没有在跑" in again["note"], f"输出应说明没有在跑的服务: {again}"


def test_tc_04_10_no_data_keys_two_messages(srv):
    """TC-04-10: 两类 no_data_keys: 清单与磁盘都空 -> 还没 build; 清单有条目但
    副本全缺 -> 副本已删建议重新 build. 两次都不起服务 (端口无监听)."""
    # 类别 1: 清单与磁盘都空
    srv.prime(key=None)
    obj, proc = srv.serve(expect_success=False)
    assert proc.returncode != 0
    assert obj["error"]["code"] == "no_data_keys"
    assert "build" in obj["error"]["message"], f"文案应说明还没 build: {obj}"
    assert "重新" not in obj["error"]["message"], "还没 build 过不应建议重新 build"
    assert not port_connectable(srv.port), "不应起空服务"

    # 类别 2: 清单有条目但副本全缺
    other = CodemapSrv(srv.base.parent / "no-data-b")
    try:
        other.prime(with_copy=False)
        obj2, proc2 = other.serve(expect_success=False)
        assert proc2.returncode != 0
        assert obj2["error"]["code"] == "no_data_keys"
        message = obj2["error"]["message"]
        assert "已删" in message and "重新" in message, f"文案应说明副本已删并建议重新 build: {obj2}"
        assert not port_connectable(other.port), "不应起空服务"
        assert other.daemon_pids_for_port() == []
    finally:
        other.cleanup()
