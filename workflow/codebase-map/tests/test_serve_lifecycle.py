"""ISSUE-04 serve 生命周期用例: 单例复用, 并发, 端口占用与换端口, 常驻性.

覆盖: TC-003 (AC-003 主用例), TC-04-01 (并发单例), TC-04-02 (端口被占),
TC-04-03 (显式换端口), TC-04-04 (换端口后沿用), TC-04-05 (存活实例换端口
报 instance_running), TC-04-11 (常驻性短时验证).

隔离纪律: 每个用例独立运行时目录 (CODEMAP_RUNTIME_DIR -> tmp_path) 与独立
高位端口 (free_port), 不占 8090; 收尾 fixture stop 加强杀, 不残留进程.
ISSUE-04 的 serve 不输出 url/base_url (归 ISSUE-05), "URL 一致"口径在本树
以 state.json 的 last_url 一致断言. srv fixture 默认用空 HOME 隔离地址来源
(无 lan-address -> address_missing 形态), 需要 record 来源的用例单独覆盖.
"""
from __future__ import annotations

import json
import time

import pytest

from codemap_service_helpers import (
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
    # 空 HOME (无 lan-address): serve 恒走 address_missing 形态, 不受宿主记录影响;
    # 需要 confirmed_record 来源的用例再调 use_temp_home(srv, tmp_path, confirmed=...)
    use_temp_home(controller, tmp_path)
    yield controller
    controller.cleanup()


def _last_json_line(text):
    lines = [line for line in text.splitlines() if line.strip()]
    return json.loads(lines[-1])


def test_tc003_alive_instance_reused_not_restarted(srv):
    """TC-003: 起服务后再次 serve 复用, 两次 port 相同, 第二次 reused=true,
    pid 不变, 进程数不变."""
    srv.prime()
    first, _ = srv.serve()
    assert first["reused"] is False
    assert first["port"] == srv.port
    pids_before = srv.daemon_pids_for_port()

    second, _ = srv.serve()
    assert second["success"] is True
    assert second["reused"] is True, f"第二次 serve 应复用: {second}"
    assert second["port"] == first["port"]
    assert second["pid"] == first["pid"], "复用时 pid 不得变"
    assert srv.daemon_pids_for_port() == pids_before, "进程数不应变化"
    # 两次输出同 URL 的 ISSUE-04 口径: state 记录的 last_url 同端口同值
    state = srv.read_state()
    assert state["last_url"] == f"http://127.0.0.1:{srv.port}/"


def test_tc_04_01_concurrent_serve_leaves_single_instance(srv):
    """TC-04-01: 两进程同时对同一运行时目录 serve, 结束时 state.json 只有一个
    pid, 两次输出同 port, reused 一次 false 一次 true."""
    srv.prime()
    p1 = srv.popen_serve()
    p2 = srv.popen_serve()
    out1, _ = p1.communicate(timeout=60)
    out2, _ = p2.communicate(timeout=60)
    assert p1.returncode == 0, f"serve #1 失败: {out1}"
    assert p2.returncode == 0, f"serve #2 失败: {out2}"
    obj1, obj2 = _last_json_line(out1), _last_json_line(out2)

    assert sorted([obj1["reused"], obj2["reused"]]) == [False, True], (
        f"reused 应一 false 一 true: {obj1} {obj2}")
    assert obj1["port"] == obj2["port"] == srv.port, "两次输出应同端口"
    starter, reuser = (obj1, obj2) if not obj1["reused"] else (obj2, obj1)
    state = srv.read_state()
    assert state["pid"] == starter["pid"], "state.json 应只留一个 pid (先起者)"
    assert reuser["pid"] == starter["pid"], "后到会话拿到的是同一实例"
    assert len(srv.daemon_pids_for_port()) == 1, "端口上应只有一个守护进程"


def test_tc_04_02_occupied_target_port_errors_without_drift(srv):
    """TC-04-02: 一次性 socket 占住目标端口且无生效实例, serve 返回 port_in_use,
    退出码非 0, 端口仍被原程序持有, 不去试其它端口."""
    import socket

    srv.prime(last_port=srv.port, stopped_at="2026-01-01T00:00:00+00:00")
    occupier = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupier.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    occupier.bind(("127.0.0.1", srv.port))
    occupier.listen(1)
    try:
        obj, proc = srv.serve(expect_success=False)
        assert proc.returncode != 0, f"端口被占时 serve 不应成功: {obj}"
        assert obj["success"] is False
        assert obj["error"]["code"] == "port_in_use"
        assert str(srv.port) in obj["error"]["message"], "错误应指明被占端口"
        # 端口仍被原程序持有 (测试内 socket 还在听), 未被接管
        assert port_connectable(srv.port), "占用者应仍持有端口"
        # 不去试其它端口: 状态记录未被动过, 端口上没有本工具守护
        state = srv.read_state()
        assert state["last_port"] == srv.port and state["pid"] is None
        assert srv.daemon_pids_for_port() == []
    finally:
        occupier.close()


def test_tc_04_03_explicit_port_change_reports_old_url(srv):
    """TC-04-03: 起服务 -> stop -> serve --port <新端口>: 新端口 GET / 200,
    port_changed=true; 缺已确认地址 (address_missing 形态) 时解析不出旧
    地址, previous_url 省略, 但输出仍写明旧地址已失效; 旧端口不再响应."""
    srv.prime()
    first, _ = srv.serve()
    assert srv.read_state()["last_url"] == f"http://127.0.0.1:{srv.port}/", (
        "缺地址时 last_url 保持回环留痕")

    stop_proc = srv.stop()
    stop_obj = stdout_json(stop_proc)
    assert stop_proc.returncode == 0 and stop_obj["stopped"] is True

    new_port = free_port()
    second, _ = srv.serve("--port", str(new_port))
    assert second["success"] is True
    assert second["port"] == new_port
    assert second["port_changed"] is True
    assert "previous_url" not in second, (
        "本次也解析不出地址时应省略 previous_url, 不用回环地址拼旧地址")
    assert "旧地址已失效" in second["note"], "换端口输出必须写明旧地址已失效"
    status, _ = http_status(new_port)
    assert status == 200, "新端口应能打开"
    assert not port_connectable(srv.port), "旧端口不应再有监听"
    state = srv.read_state()
    assert state["port"] == new_port and state["last_port"] == new_port
    assert state["last_url"] == f"http://127.0.0.1:{new_port}/", "缺地址时 last_url 保持回环留痕"


def test_tc_04_04_serve_without_port_keeps_last_port(srv):
    """TC-04-04 (承 TC-04-03 场景自建): 曾用 serve --port 起过并已 stop, 之后不带
    --port 的 serve 起在上一回端口, 不回到 8090, 也不算换端口."""
    srv.prime()
    srv.serve()
    srv.stop()  # 换端口必须在停机状态 (存活实例上换端口是 instance_running)
    changed_port = free_port()
    srv.serve("--port", str(changed_port))
    srv.stop()

    obj, proc = srv.serve()
    assert obj["success"] is True
    assert obj["port"] == changed_port, "应沿用 last_port"
    assert obj["port"] != 8090, "不得悄悄退回首选端口 8090"
    assert obj["reused"] is False
    assert "port_changed" not in obj, "沿用 last_port 不算换端口"
    status, _ = http_status(changed_port)
    assert status == 200


def test_tc_04_05_port_change_with_alive_instance_rejected(srv):
    """TC-04-05: 存活实例上用 --port 指定别的端口: instance_running, 存活实例
    仍在原端口 200, 新端口无人监听."""
    srv.prime()
    first, _ = srv.serve()
    other_port = free_port()
    obj, proc = srv.serve("--port", str(other_port), expect_success=False)
    assert proc.returncode != 0
    assert obj["success"] is False
    assert obj["error"]["code"] == "instance_running"
    assert "stop" in obj["error"]["hint"], "应提示先 stop"
    status, _ = http_status(srv.port)
    assert status == 200, "存活实例应仍在原端口服务"
    assert not port_connectable(other_port), "新端口不应有人监听"
    state = srv.read_state()
    assert state["port"] == first["port"] and state["pid"] == first["pid"]


def test_tc_04_11_service_survives_real_wait_and_reuse(srv):
    """TC-04-11: 常驻性短时验证, serve 成功后隔真实等待 (>= 2 秒) 并跨另一次
    CLI 调用, GET / 仍 200 且再 serve 复用同一 pid."""
    srv.prime()
    first, _ = srv.serve()
    time.sleep(2.2)  # 真实等待, 不少于 2 秒
    status, _ = http_status(srv.port)
    assert status == 200, "隔真实等待后服务应仍在"
    second, _ = srv.serve()
    assert second["reused"] is True
    assert second["pid"] == first["pid"], "应复用同一实例而非新起"
