"""browser_agent.config 单元测试."""

import os
import sys
import tempfile

import socket
from pathlib import Path

import pytest

from browser_agent.config import (
    BrowserConfig,
    allocate_cdp_port,
    compute_session_key,
    get_runtime_info,
    get_session_paths,
    read_metadata,
    write_metadata,
)


def test_compute_session_key_is_stable_for_same_cwd():
    cwd = "/tmp/my/project"
    assert compute_session_key(cwd) == compute_session_key(cwd)


def test_compute_session_key_differs_for_different_cwd():
    assert compute_session_key("/tmp/a") != compute_session_key("/tmp/b")


def test_canonicalize_case_sensitive_on_posix(tmp_path):
    """POSIX 下 normcase 不统一大小写: 大小写不同的目录不共享 session key."""
    if os.name == "nt":
        pytest.skip("Windows normcase 会统一大小写")
    upper = tmp_path / "ProjA"
    lower = tmp_path / "proja"
    upper.mkdir()
    lower.mkdir()
    assert compute_session_key(str(upper)) != compute_session_key(str(lower))


def test_ensure_session_dirs_creates_artifacts_and_chmod_700(tmp_path):
    """ensure_session_dirs 创建 artifacts 子目录, POSIX 下 session 根目录修正为 700."""
    config = BrowserConfig(cwd=str(tmp_path))
    # 模拟已存在且权限过宽的旧目录, 验证权限会被修正
    config.session_root.mkdir(parents=True)
    if os.name != "nt":
        os.chmod(config.session_root, 0o755)

    config.ensure_session_dirs()

    assert config.artifacts_dir.is_dir()
    assert config.screenshots_dir.is_dir()
    assert config.downloads_dir.is_dir()
    assert config.logs_dir.is_dir()
    if os.name != "nt":
        mode = config.session_root.stat().st_mode & 0o777
        assert mode == 0o700, f"session_root mode {mode:o} != 700"


def test_get_runtime_info():
    info = get_runtime_info()
    assert info["os"] == os.name
    assert info["python_executable"] == sys.executable
    assert info["tempdir"] == tempfile.gettempdir()


def test_get_session_paths_under_tempdir():
    paths = get_session_paths(tempdir="/tmp/test", session_key="abc123")
    root = Path("/tmp/test/access-web/abc123")
    assert paths["session_root"] == root
    assert paths["browser_json"] == root / "browser.json"
    assert paths["profile_dir"] == root / "profile"
    assert paths["artifacts_dir"] == root / "artifacts"
    assert paths["screenshots_dir"] == root / "artifacts" / "screenshots"
    assert paths["downloads_dir"] == root / "artifacts" / "downloads"
    assert paths["logs_dir"] == root / "artifacts" / "logs"


def test_allocate_cdp_port_returns_bindable_port():
    port = allocate_cdp_port()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", port))
    s.close()


def test_metadata_roundtrip(tmp_path):
    path = tmp_path / "browser.json"
    data = {
        "pid": 1234,
        "port": 9222,
        "profile_dir": str(tmp_path / "profile"),
        "created_at": 1710000000.0,
        "status": "running",
    }
    write_metadata(path, data)
    assert read_metadata(path) == data


def test_locate_chromium_binary_returns_existing_path(tmp_path):
    config = BrowserConfig(cwd=str(tmp_path))
    binary = config.locate_chromium_binary()
    assert Path(binary).exists()


def test_locate_chromium_binary_caches_to_metadata(tmp_path):
    config = BrowserConfig(cwd=str(tmp_path))
    binary = config.locate_chromium_binary()
    metadata = config.read_metadata()
    assert metadata["chromium_binary"] == str(binary)


def test_browser_config_paths_are_under_tempdir():
    config = BrowserConfig(cwd="/tmp/project")
    assert str(config.session_root).startswith(tempfile.gettempdir())
    assert config.browser_json.parent == config.session_root
    assert config.profile_dir.parent == config.session_root
    assert config.artifacts_dir.parent == config.session_root


def test_chromium_not_installed_error_message_contains_command():
    from browser_agent.config import ChromiumNotInstalledError

    err = ChromiumNotInstalledError()
    assert "playwright install chromium" in str(err)
