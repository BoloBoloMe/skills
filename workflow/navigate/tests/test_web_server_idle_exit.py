"""web_server.py 空闲自退测试 (ISSUE-04: TC-011).

缩短空闲阈值触发同一代码路径: 断言进程退出与运行时文件清理;
请求刷新计时 (覆盖所有端点含判活 ping).
"""

import time

from conftest import ENV_TTL, http_get, pid_alive, wait_pid_gone


def test_idle_exit_after_shortened_threshold(server):
    """TC-011 (AC-011): 秒级空闲阈值下无新请求 -> 进程退出且运行时文件清理."""
    obj = server.start(extra_env={ENV_TTL: "2"})
    sj = server.read_server_json()
    pid = sj["pid"]
    port = obj["port"]

    # 前置: 服务真的在响应 (TTL 注入不影响正常服务)
    status, _, _ = http_get(server.base_url(port) + "/")
    assert status == 200

    # 空闲超过阈值 -> 进程自退, server.json 被清理
    assert wait_pid_gone(pid, timeout=15), f"idle ttl=2s 后 15s 内进程 {pid} 未退出"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and server.server_json_exists():
        time.sleep(0.1)
    assert not server.server_json_exists(), "空闲自退后 server.json 未清理"

    # status 报未运行
    st, code, _ = server.run_cli("status")
    assert code == 0
    assert st["alive"] is False


def test_request_resets_idle_timer(server):
    """TC-011 伴随: 阈值内持续请求 (含判活 ping) 不自退; 停止请求后仍自退."""
    obj = server.start(extra_env={ENV_TTL: "3"})
    sj = server.read_server_json()
    pid = sj["pid"]
    base = server.base_url(obj["port"])

    # 每 ~1s 请求一次, 持续 ~5s (> ttl=3s): 计时被刷新, 不自退
    for i in range(5):
        path = "/" if i % 2 == 0 else "/__control__/ping"
        status, _, _ = http_get(base + path)
        assert status == 200, f"第 {i} 次请求 -> {status}"
        assert pid_alive(pid), f"第 {i} 次请求后进程退出, 计时未被刷新"
        time.sleep(1.0)

    # 停止请求 -> 空闲超过阈值后仍自退并清理
    assert wait_pid_gone(pid, timeout=15), "停止请求后进程未空闲自退"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and server.server_json_exists():
        time.sleep(0.1)
    assert not server.server_json_exists()
