"""web_server.py 生命周期测试 (ISSUE-03: TC-008, TC-009, TC-010)."""

import json
import socket

from nav_helpers import DEFAULT_PORT, http_get, pid_alive, wait_pid_gone


def test_start_status_stop_cycle(server):
    """TC-008 (AC-008): start 就绪返回可访问 URL -> status 报存活 -> stop 清理."""
    obj = server.start()
    assert obj["command"] == "start"
    assert "url" in obj
    assert obj["port"] == DEFAULT_PORT
    assert obj["bind"] == "0.0.0.0"
    assert obj["reused"] is False

    sj = server.read_server_json()
    assert sj["pid"] > 0
    assert sj["port"] == obj["port"]
    assert sj["bind"] == "0.0.0.0"
    assert "started_at" in sj

    # URL 可访问: 服务真实在响应
    status, headers, body = http_get(server.base_url(obj["port"]) + "/")
    assert status == 200

    # status 报存活与实际端口
    st, code, proc = server.run_cli("status")
    assert code == 0, f"stdout={proc.stdout} stderr={proc.stderr}"
    assert st["success"] is True
    assert st["alive"] is True
    assert st["pid"] == sj["pid"]
    assert st["port"] == obj["port"]
    assert st["bind"] == "0.0.0.0"

    # stop 停止并清理运行时文件
    sp, code, proc = server.run_cli("stop")
    assert code == 0, f"stdout={proc.stdout} stderr={proc.stderr}"
    assert sp["success"] is True
    assert wait_pid_gone(sj["pid"], timeout=5), "stop 后进程仍存活"
    assert not server.server_json_exists(), "stop 后 server.json 未清理"

    # 再 status 报未运行
    st2, code, _ = server.run_cli("status")
    assert code == 0
    assert st2["success"] is True
    assert st2["alive"] is False


def test_start_reuses_alive_instance(server):
    """TC-009 (AC-009): 重复 start 复用既有进程, 同 pid/端口, 无第二实例."""
    obj1 = server.start()
    sj1 = server.read_server_json()

    obj2, code, proc = server.run_cli("start")
    assert code == 0, f"stdout={proc.stdout} stderr={proc.stderr}"
    assert obj2["success"] is True
    assert obj2["reused"] is True
    assert obj2["port"] == obj1["port"]
    assert obj2["pid"] == sj1["pid"]

    # 运行时文件不变, 未起第二个实例
    sj2 = server.read_server_json()
    assert sj2["pid"] == sj1["pid"]
    assert sj2["port"] == sj1["port"]
    assert server.count_serve_processes() == 1


def test_port_conflict_falls_back(server):
    """TC-010 (AC-010): 39271 被占 -> 自动换端口, status 报告一致, 服务可用."""
    occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    occupant.bind(("0.0.0.0", DEFAULT_PORT))
    occupant.listen(1)
    try:
        obj = server.start()
        assert obj["port"] != DEFAULT_PORT
        assert obj["reused"] is False

        sj = server.read_server_json()
        assert sj["port"] == obj["port"]

        st, code, proc = server.run_cli("status")
        assert code == 0, f"stdout={proc.stdout} stderr={proc.stderr}"
        assert st["alive"] is True
        assert st["port"] == obj["port"]

        status, _, _ = http_get(server.base_url(obj["port"]) + "/")
        assert status == 200
    finally:
        occupant.close()
