"""web_server.py 生命周期测试 (ISSUE-03: TC-008, TC-009, TC-010 + milestone-17 R1-R4, R7).

milestone-17 起测试与生产不再在真实 39271 上互斥: 除 TC-010 (保留的真实
默认端口漂移回归) 外, 一律用 free_port() + NAVIGATE_WEB_PORT 固定端口.
"""

import os
import shutil
import signal
import socket

from nav_helpers import (
    ENV_PORT,
    SCRIPT,
    http_get,
    pid_alive,
    wait_pid_gone,
)


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _fixed_port_start(server, port):
    return server.start(extra_env={ENV_PORT: str(port)})


def test_start_status_stop_cycle(server):
    """TC-008 (AC-008): start 就绪返回可访问 URL -> status 报存活 -> stop 清理."""
    expected = _free_port()
    obj = _fixed_port_start(server, expected)
    assert obj["command"] == "start"
    assert "url" in obj
    assert obj["port"] == expected
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
    expected = _free_port()
    obj1 = _fixed_port_start(server, expected)
    sj1 = server.read_server_json()
    baseline = server.count_serve_processes()

    obj2, code, proc = server.run_cli("start", extra_env={ENV_PORT: str(expected)})
    assert code == 0, f"stdout={proc.stdout} stderr={proc.stderr}"
    assert obj2["success"] is True
    assert obj2["reused"] is True
    assert obj2["port"] == obj1["port"]
    assert obj2["pid"] == sj1["pid"]

    # 运行时文件不变, 未起第二个实例 (与生产实例并存时按差值计, 见 R6)
    sj2 = server.read_server_json()
    assert sj2["pid"] == sj1["pid"]
    assert sj2["port"] == sj1["port"]
    assert server.count_serve_processes() == baseline


def test_port_conflict_falls_back(server):
    """TC-010 (AC-010): 真实默认端口 39271 被占 -> 自动换端口, status 一致, 服务可用.

    milestone-17 保留的真实默认端口漂移回归. 占位者绑不上 (真实实例已占
    39271) 时直接在既有占用上验证漂移, 不与生产互斥.
    """
    occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        we_bound = True
        try:
            occupant.bind(("0.0.0.0", 39271))
            occupant.listen(1)
        except OSError:
            we_bound = False  # 39271 已被 (真实) 实例占用, 借用该占用
        try:
            obj = server.start()
            assert obj["port"] != 39271
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
            if we_bound:
                occupant.close()
    finally:
        if not we_bound:
            occupant.close()


def test_fixed_port_reuse_and_rebuild_same_port(server):
    """R1: NAVIGATE_WEB_PORT 固定端口 start -> port 相符; stop 后重建仍同端口."""
    expected = _free_port()
    obj1 = _fixed_port_start(server, expected)
    assert obj1["port"] == expected and obj1["reused"] is False

    obj2, code, _ = server.run_cli("start", extra_env={ENV_PORT: str(expected)})
    assert code == 0
    assert obj2["reused"] is True and obj2["port"] == expected

    sp, code, _ = server.run_cli("stop")
    assert code == 0 and sp["success"] is True

    obj3 = _fixed_port_start(server, expected)
    assert obj3["port"] == expected and obj3["reused"] is False
    status, _, _ = http_get(server.base_url(expected) + "/")
    assert status == 200


def test_fixed_port_refuses_foreign_occupant(server):
    """R2: 固定端口被陌生进程占 -> start 报 port_in_use, 不漂移, 不产生实例."""
    expected = _free_port()
    stranger = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    stranger.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    stranger.bind(("0.0.0.0", expected))
    stranger.listen(1)
    baseline = server.count_serve_processes()
    try:
        obj, code, proc = server.run_cli("start", extra_env={ENV_PORT: str(expected)})
        assert code == 1, f"stdout={proc.stdout} stderr={proc.stderr}"
        assert obj["success"] is False
        assert obj["code"] == "port_in_use"
        assert "refusing to drift" in obj["error"]
        # 未产生任何实例: server.json 不在, 未新起 __serve__ 守护, 未漂移到随机端口
        assert not server.server_json_exists()
        assert server.count_serve_processes() == baseline
    finally:
        stranger.close()


def test_fixed_port_rebuild_after_sigkill(server):
    """R3: SIGKILL 后 server.json 残留, status 报死, start 重建回同端口."""
    expected = _free_port()
    obj = _fixed_port_start(server, expected)
    pid = obj["pid"]
    os.kill(pid, signal.SIGKILL)
    assert wait_pid_gone(pid, timeout=5)
    assert server.server_json_exists(), "SIGKILL 应残留 server.json"

    st, code, _ = server.run_cli("status")
    assert code == 0
    assert st["alive"] is False, "ping 探活兜底: 残留文件不骗 status"

    obj2 = _fixed_port_start(server, expected)
    assert obj2["port"] == expected and obj2["reused"] is False
    status, _, _ = http_get(server.base_url(expected) + "/")
    assert status == 200


def test_stop_refuses_foreign_script_copy(server, tmp_path):
    """R4: 跨脚本路径 stop 被拒 (防误杀), 本路径 stop 正常."""
    expected = _free_port()
    obj = _fixed_port_start(server, expected)
    pid = obj["pid"]

    copy_dir = tmp_path / "copyA"
    copy_dir.mkdir()
    copy_script = copy_dir / "web_server.py"
    shutil.copyfile(SCRIPT, copy_script)

    out, code, proc = server.run_cli("stop", script=copy_script)
    assert code == 1, f"stdout={proc.stdout} stderr={proc.stderr}"
    assert out["success"] is False
    assert "refuse to stop" in out["error"]
    assert pid_alive(pid), "被拒后实例必须仍存活"

    sp, code, _ = server.run_cli("stop")
    assert code == 0 and sp["success"] is True
    assert wait_pid_gone(pid, timeout=5)


def test_log_rotates_during_run(server):
    """R7: 运行中日志超 10MB 在下次写入时截断, 不再只靠重启截断."""
    expected = _free_port()
    _fixed_port_start(server, expected)
    log_path = server.runtime_dir / "server.log"
    log_path.write_text("x" * (11 * 1024 * 1024), encoding="utf-8")
    assert log_path.stat().st_size > 10 * 1024 * 1024

    status, _, _ = http_get(server.base_url(expected) + "/")
    assert status == 200  # 该请求触发一条访问日志 -> 滚动检查生效
    assert log_path.stat().st_size < 1024 * 1024, "运行中滚动未生效"
