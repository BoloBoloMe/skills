"""web_server.py 长跑回归 (milestone-17 R5, 对应 milestone-16 H3).

2000 请求压测后 fd/线程回落基线, 0 个 5xx, 0 次连接错误.
milestone-16 E4 (5000 请求) 已实证无泄漏, 本用例作回归保护.
"""
import os
import time
import urllib.parse

from nav_helpers import ENV_PORT, http_get


def _proc_metrics(pid):
    """读 /proc/<pid>: (fd 数, 线程数)."""
    fds = len(os.listdir(f"/proc/{pid}/fd"))
    threads = None
    with open(f"/proc/{pid}/status", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Threads:"):
                threads = int(line.split()[1])
                break
    return fds, threads


def test_soak_fds_and_threads_settle_no_5xx(server):
    expected = _free_port()
    obj = server.start(extra_env={ENV_PORT: str(expected)})
    pid = obj["pid"]
    base = server.base_url(expected)
    missing = str(server.runtime_base.parent / "absent-soak.json")
    api_url = base + "/api/roadmap?path=" + urllib.parse.quote(missing)

    baseline = _proc_metrics(pid)
    errors = []
    codes = {}
    for i in range(2000):
        url = base + "/" if i % 2 == 0 else api_url
        try:
            status, _, _ = http_get(url, timeout=5)
        except Exception as e:  # 连接错误即失败, 不吞
            errors.append(f"request {i}: {e!r}")
            break
        codes[status] = codes.get(status, 0) + 1
        if status >= 500:
            errors.append(f"request {i}: 5xx status={status}")
            break

    assert not errors, errors[:5]
    assert codes.get(200, 0) == 1000, codes
    assert codes.get(404, 0) == 1000, codes  # 缺失 .json 的预期错误响应

    time.sleep(1.0)  # 等 daemon 线程收尾
    final = _proc_metrics(pid)
    assert final[0] <= baseline[0] + 5, f"fd 未回落: baseline={baseline} final={final}"
    assert final[1] <= baseline[1] + 2, f"线程未回落: baseline={baseline} final={final}"


def _free_port():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
