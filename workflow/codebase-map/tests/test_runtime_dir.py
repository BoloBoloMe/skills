"""TC-01-02: 运行时目录解析 (CODEMAP_RUNTIME_DIR 覆盖, 默认 ~/.agents/codebase-map,
子目录 serve-root/cache/logs 按需创建, 目录 0700).

纯函数接缝 (内部): 直接 import codemap_common; 默认值用例只解析不创建,
不触碰真实 ~/.agents/codebase-map.
"""
from __future__ import annotations

import os
import stat
import unittest.mock as mock
from pathlib import Path

from codemap_helpers import ENV_RUNTIME_DIR, codemap_common as cmc


def test_default_runtime_dir_value():
    """env 未设时默认 ~/.agents/codebase-map (TECHNICAL 运行时目录)."""
    with mock.patch.dict(os.environ):
        os.environ.pop(ENV_RUNTIME_DIR, None)
        assert cmc.runtime_dir() == Path.home() / ".agents" / "codebase-map"


def test_env_override_takes_precedence(tmp_path):
    """CODEMAP_RUNTIME_DIR 覆盖生效; 解析本身无副作用, 未调用创建前不存在."""
    override = tmp_path / "custom-runtime"
    with mock.patch.dict(os.environ, {ENV_RUNTIME_DIR: str(override)}):
        assert cmc.runtime_dir() == override
        assert not override.exists()


def test_ensure_layout_creates_base_and_three_subdirs_0700(tmp_path):
    """按需创建基目录与三个子目录, 全部 0700 (TECHNICAL: 目录 0700)."""
    base = tmp_path / "rt"
    assert cmc.ensure_runtime_layout(base) == base
    assert stat.S_IMODE(base.stat().st_mode) == 0o700
    for sub in ("serve-root", "cache", "logs"):
        d = base / sub
        assert d.is_dir(), f"缺子目录 {sub}"
        assert stat.S_IMODE(d.stat().st_mode) == 0o700


def test_ensure_layout_honors_env_override(tmp_path):
    """不传参时按 runtime_dir() 解析 (env 覆盖路径) 落盘."""
    base = tmp_path / "via-env"
    with mock.patch.dict(os.environ, {ENV_RUNTIME_DIR: str(base)}):
        cmc.ensure_runtime_layout()
    for sub in ("serve-root", "cache", "logs"):
        assert (base / sub).is_dir()
