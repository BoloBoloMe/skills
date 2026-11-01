"""codebase-map 测试共享工具 (唯一命名模块, 刻意不叫 conftest).

pytest.ini testpaths 收多棵测试树, 各树 conftest.py 同名, 预载时后者覆盖
sys.modules['conftest'], 显式 `from conftest import ...` 会拿错对象
(pytest.ini 文件头注释; 先例 workflow/navigate/tests/nav_helpers.py).
本模块名全仓库唯一, 导入永远命中自身; 本树不设 conftest.py,
共享工具只放这里.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
CLI_SCRIPT = SCRIPTS_DIR / "codebase-map.py"
ENV_RUNTIME_DIR = "CODEMAP_RUNTIME_DIR"

# 容器判定与 CLI 前置检查同口径: podman/oci 容器内的标记文件
IN_CONTAINER = Path("/run/.containerenv").exists()

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import codemap_common  # noqa: E402  (注入 scripts 目录后导入被测共享模块)


def run_cli(*argv, env_extra=None, timeout=60):
    """真实子进程跑 CLI (入口脚本带连字符, 不能当模块导入, 一律 subprocess).

    默认剥离 CODEMAP_RUNTIME_DIR 防串台, env_extra 可按用例覆盖 (隔离运行时
    目录一律指向 tmp_path, 不占用真实 ~/.agents/codebase-map, 不用 8090).
    """
    env = os.environ.copy()
    env.pop(ENV_RUNTIME_DIR, None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT), *[str(a) for a in argv]],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def stdout_json(proc):
    """取 stdout 最后一个非空行解析为 JSON (--json 模式应恰一行)."""
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else None


def make_target(tmp_path, name="demo-lib"):
    """造一个被分析目标目录 (只用于前置检查, 不放源码)."""
    target = tmp_path / name
    target.mkdir(parents=True)
    return target
