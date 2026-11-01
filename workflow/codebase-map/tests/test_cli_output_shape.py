"""TC-01-06: CLI 输出形状与可诊断性 (m25 TECHNICAL.md CLI "输出形状", 非功能要求
"可诊断").

进程接缝: 入口脚本带连字符不能当模块名, 一律 subprocess 调真实入口.

环境感知 (m25 D016 验证分工): 容器内失败码是 container_not_supported; 宿主
(有 podman) 前置检查全过后落 "流水线未接线" 的 internal_error. 两种环境都必须
满足同一形状: --json stdout 恰一行含 success/command/error; 非 JSON 失败
stdout 是多行摘要, stderr 说清下一步动作, 退出码 1.
"""
from __future__ import annotations

import json

from codemap_helpers import (
    ENV_RUNTIME_DIR,
    IN_CONTAINER,
    make_target,
    run_cli,
    stdout_json,
)


def test_json_failure_stdout_exactly_one_line_with_stable_fields(tmp_path):
    """--json 时 stdout 恰好一行可解析 JSON, 字段含 success/command/error."""
    target = make_target(tmp_path)
    proc = run_cli("build", str(target), "--json",
                   env_extra={ENV_RUNTIME_DIR: str(tmp_path / "rt")})
    assert proc.returncode == 1
    lines = proc.stdout.splitlines()
    assert len(lines) == 1, f"--json 模式 stdout 必须恰一行: {proc.stdout!r}"
    obj = json.loads(lines[0])
    assert obj["success"] is False
    assert obj["command"] == "build"
    assert set(obj) >= {"success", "command", "error"}
    assert obj["error"]["code"], "缺稳定错误码"
    assert obj["error"]["message"] and obj["error"]["hint"]
    if IN_CONTAINER:
        assert obj["error"]["code"] == "container_not_supported"


def test_human_failure_stderr_has_next_step_and_exit_1(tmp_path):
    """非 JSON 失败: stdout 多行人类摘要, stderr 说清下一步动作, 退出码 1."""
    target = make_target(tmp_path)
    proc = run_cli("build", str(target),
                   env_extra={ENV_RUNTIME_DIR: str(tmp_path / "rt")})
    assert proc.returncode == 1
    assert proc.stdout.count("\n") >= 2, "默认输出应为多行人类可读摘要"
    assert "codebase-map build" in proc.stdout
    assert "下一步" in proc.stderr, f"stderr 未说下一步动作: {proc.stderr!r}"
    assert proc.stderr.strip() != ""


def test_serve_and_stop_not_registered_in_this_issue(tmp_path):
    """BR-013 三子命令由各自 issue 注册: 本期无占位分支, serve/stop 走不到."""
    for command in ("serve", "stop"):
        proc = run_cli(command, env_extra={ENV_RUNTIME_DIR: str(tmp_path / "rt")})
        assert proc.returncode != 0
        assert "invalid choice" in proc.stderr
