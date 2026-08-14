"""startup 锁: 位置, 超时与并发互斥测试."""

import os
import shutil
import threading

import pytest

from browser_agent.browser import _startup_lock
from browser_agent.config import BrowserConfig


def _make_config(tmp_path):
    return BrowserConfig(cwd=str(tmp_path), tempdir=str(tmp_path / "t"))


def test_lock_file_lives_outside_session_root(tmp_path):
    """锁文件与 session 目录平级 (<key>.lock), 不在其内部."""
    config = _make_config(tmp_path)
    assert config.startup_lock.parent == config.session_root.parent
    assert config.startup_lock.name == f"{config.session_key}.lock"


@pytest.mark.skipif(os.name == "nt", reason="Windows 无 flock")
def test_lock_acquire_times_out_instead_of_blocking(tmp_path):
    """holder 持锁不放时, waiter 超时抛 TimeoutError 而非无限阻塞."""
    config = _make_config(tmp_path)
    errors: list = []

    def waiter():
        try:
            with _startup_lock(config, timeout=1.0):
                pass
        except TimeoutError as e:
            errors.append(e)

    with _startup_lock(config, timeout=5.0):
        t = threading.Thread(target=waiter)
        t.start()
        t.join(timeout=15)

    assert not t.is_alive(), "waiter 线程未在超时后退出 (疑似无限阻塞)"
    assert len(errors) == 1
    assert "超时" in str(errors[0])


@pytest.mark.skipif(os.name == "nt", reason="Windows 无 flock")
def test_lock_mutual_exclusion(tmp_path):
    """同一路径的锁互斥: 持锁期间其他 waiter 拿不到."""
    config = _make_config(tmp_path)
    acquired: list = []

    def waiter():
        try:
            with _startup_lock(config, timeout=0.6):
                acquired.append(True)
        except TimeoutError:
            pass

    with _startup_lock(config, timeout=5.0):
        t = threading.Thread(target=waiter)
        t.start()
        t.join(timeout=10)

    assert not acquired


@pytest.mark.skipif(os.name == "nt", reason="Windows 无 flock")
def test_lock_survives_session_root_removal(tmp_path):
    """rmtree session 目录后锁文件仍在, 且重开后互斥语义不分裂 (防 split-brain)."""
    config = _make_config(tmp_path)
    config.ensure_session_dirs()
    with _startup_lock(config, timeout=5.0):
        pass

    shutil.rmtree(config.session_root)
    assert config.startup_lock.exists()

    # 重新 open 同一锁文件 (同 inode, 未因 rmtree 换锁), 互斥依然成立
    acquired: list = []

    def waiter():
        try:
            with _startup_lock(config, timeout=0.6):
                acquired.append(True)
        except TimeoutError:
            pass

    with _startup_lock(config, timeout=5.0):
        t = threading.Thread(target=waiter)
        t.start()
        t.join(timeout=10)

    assert not acquired
