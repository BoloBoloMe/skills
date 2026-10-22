"""web_server.py 持续运行测试."""

import time

from nav_helpers import ENV_TTL, http_get, pid_alive, wait_pid_gone


def test_idle_server_stays_available_until_stop(server):
    """旧版超时设置仍存在时, 无请求的服务也持续运行直到 stop."""
    obj = server.start(extra_env={ENV_TTL: "0.2"})
    sj = server.read_server_json()
    pid = sj["pid"]
    port = obj["port"]

    time.sleep(1.0)
    assert pid_alive(pid), "服务闲置后意外退出"
    assert server.server_json_exists()
    status, _, _ = http_get(server.base_url(port) + "/")
    assert status == 200
    st, code, _ = server.run_cli("status")
    assert code == 0
    assert st["alive"] is True
    assert st["pid"] == pid

    stopped, code, _ = server.run_cli("stop")
    assert code == 0
    assert stopped["success"] is True
    assert wait_pid_gone(pid, timeout=5)
    assert not server.server_json_exists()
