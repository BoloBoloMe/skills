"""TC-01-06: CLI 输出形状与可诊断性 (m25 TECHNICAL.md CLI "输出形状", 非功能要求
"可诊断").

进程接缝: 入口脚本带连字符不能当模块名, 一律 subprocess 调真实入口.

环境感知 (m25 D016 验证分工): 容器内失败码是 container_not_supported. ISSUE-02
接线后, 宿主上前置检查全过的 build 会走真实分析流水线 (含网络初始化), 形状
用例不应触发它, 故注入不含 podman 的 PATH 让宿主分支在 podman_missing 处快速
失败 (仍是前置检查失败, 形状断言不变; ISSUE-02 接线的允许越界调整, 见交付
证据). 两种环境都必须满足同一形状: --json stdout 恰一行含
success/command/error; 非 JSON 失败 stdout 是多行摘要, stderr 说清下一步动作,
退出码 1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from codemap_helpers import (
    CLI_SCRIPT,
    ENV_RUNTIME_DIR,
    IN_CONTAINER,
    make_target,
    run_cli,
    stdout_json,
)

# 宿主上注入不含 podman 的 PATH: 形状用例在 podman_missing 快速失败, 不触真实流水线
NO_PODMAN_PATH = {"PATH": "/nonexistent"}


def test_json_failure_stdout_exactly_one_line_with_stable_fields(tmp_path):
    """--json 时 stdout 恰好一行可解析 JSON, 字段含 success/command/error."""
    target = make_target(tmp_path)
    proc = run_cli("build", str(target), "--json",
                   env_extra={ENV_RUNTIME_DIR: str(tmp_path / "rt"), **NO_PODMAN_PATH})
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
                   env_extra={ENV_RUNTIME_DIR: str(tmp_path / "rt"), **NO_PODMAN_PATH})
    assert proc.returncode == 1
    assert proc.stdout.count("\n") >= 2, "默认输出应为多行人类可读摘要"
    assert "codebase-map build" in proc.stdout
    assert "下一步" in proc.stderr, f"stderr 未说下一步动作: {proc.stderr!r}"
    assert proc.stderr.strip() != ""


def test_podman_missing_message_names_no_podman(tmp_path):
    """AC-007 场景大纲 (没有 podman): 真实 CLI 报错里必须出现"本机没有 podman",
    error.code == podman_missing, 退出码 1, 下一步动作保留.

    容器内 /run/.containerenv 在场时第一关前置检查是 container_not_supported,
    podman_missing 到不了; 用 unshare -m -r + tmpfs 盖 /run 在子进程里藏掉
    容器标记, 再用不含 podman 的 PATH, 让宿主分支前置链 (container ->
    target -> podman) 在容器内也可到达 podman 关. 这是环境级构造 (不改产物,
    不用替身数据冒充分析结果), 宿主上同样可跑 (unshare 的 mount ns 里挂
    tmpfs 只影响子进程视图).
    """
    target = make_target(tmp_path)
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"  # 不含 podman 的 PATH
    env[ENV_RUNTIME_DIR] = str(tmp_path / "rt")
    cmd = [
        "unshare", "-m", "-r", "/bin/sh", "-c",
        'mount -t tmpfs tmpfs /run && exec "$1" "$2" build "$3" --json',
        "sh", sys.executable, str(CLI_SCRIPT), str(target),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    obj = stdout_json(proc)
    assert proc.returncode == 1, f"应报错退出 1: rc={proc.returncode} stderr={proc.stderr!r}"
    assert obj is not None and obj["success"] is False
    assert obj["error"]["code"] == "podman_missing"
    assert "本机没有 podman" in obj["error"]["message"], (
        f"AC-007 要求的说法缺失: {obj['error']['message']!r}")
    assert obj["error"]["hint"], "下一步动作 hint 应保留"


def test_serve_and_stop_registered_since_issue_04(tmp_path):
    """BR-013 三子命令注册推进: ISSUE-01 时 serve/stop 未注册 (invalid choice);
    ISSUE-04 起两者进入 argparse 并走各自前置检查, 不再是 invalid choice.

    两次调用都无副作用: stop 无状态记录 -> 幂等成功; serve 无数据 ->
    no_data_keys 在起服务之前拦截, 不起空服务.
    """
    from codemap_service_helpers import free_port

    runtime = tmp_path / "rt"
    stop_proc = run_cli("stop", "--json", env_extra={ENV_RUNTIME_DIR: str(runtime)})
    stop_obj = stdout_json(stop_proc)
    assert stop_proc.returncode == 0
    assert stop_obj["success"] is True
    assert stop_obj["command"] == "stop" and stop_obj["stopped"] is False

    serve_proc = run_cli(
        "serve", "--json",
        env_extra={ENV_RUNTIME_DIR: str(runtime), "CODEMAP_PORT": str(free_port())})
    serve_obj = stdout_json(serve_proc)
    assert serve_proc.returncode == 1
    assert serve_obj["success"] is False
    assert serve_obj["error"]["code"] == "no_data_keys"
    assert "invalid choice" not in serve_proc.stderr
