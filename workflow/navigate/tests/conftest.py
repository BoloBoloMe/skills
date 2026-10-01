"""navigate web_server 测试接缝层: 只留 pytest fixture.

共享工具在 nav_helpers.py (唯一命名, 不与根 tests/conftest.py 争抢
sys.modules 的 'conftest' 键); fixture 隐式注入不依赖模块名, 留此处即可.
fixture 收尾确保 stop + 强杀, 不残留守护进程.
"""
from __future__ import annotations

import os
import signal
import time

import pytest

from nav_helpers import NavigateServer


@pytest.fixture
def server(tmp_path):
    srv = NavigateServer(tmp_path)
    yield srv
    # 收尾: 先走 stop 正常清理, 再强杀兜底, 不残留守护进程
    try:
        srv.run_cli("stop", timeout=15)
    except Exception:
        pass
    for pid in srv.pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(0.2)
    for pid in srv.pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
