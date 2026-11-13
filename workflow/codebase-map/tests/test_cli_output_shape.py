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
import pytest
import shutil
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


def _no_podman_path(tmp_path):
    """构造不含 podman 的临时 PATH (REWORK-02 P-1): 不依赖系统 PATH 目录内容.

    之前用 PATH=/usr/bin:/bin 表达"没有 podman", 宿主 /usr/bin/podman 常见,
    会让用例红或真跑 build; 改为临时目录只软链 unshare/sh/mount 三个真实存在
    的二进制, 目录内容与系统 PATH 无关, 必然没有 podman. 缺任一二进制属环境
    前置不满足: 显式失败并说明原因, 不静默通过.
    """
    fakebin = tmp_path / "no-podman-bin"
    fakebin.mkdir()
    for name in ("unshare", "sh", "mount"):
        found = shutil.which(name)
        assert found, (
            f"环境前置不满足: 找不到 {name}, 无法构造无 podman 的 mount ns 子进程; "
            "本用例需要 unshare 与非特权 user namespace (见用例 docstring), "
            "显式失败不假通过")
        (fakebin / name).symlink_to(found)
    assert sorted(p.name for p in fakebin.iterdir()) == ["mount", "sh", "unshare"], (
        "临时 PATH 应只含 unshare/sh/mount, 不得混入其它二进制 (尤其 podman)")
    return fakebin


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
    不用替身数据冒充分析结果), unshare 的 mount ns 里挂 tmpfs 只影响子进程
    视图.

    环境前置与不满足时的表现 (REWORK-02 P-2): 需要 unshare/sh/mount 在场
    (构造临时 PATH 时软链, 缺了立即失败), 内核允许非特权 user namespace 且
    seccomp 不拦 mount (unshare -m -r 与 tmpfs 挂载要能成功). macOS /
    kernel.unprivileged_userns_clone=0 / 禁 userns 的容器运行时下子进程起
    不来, 本用例断言失败并说明原因, 不是假通过. 该用例自建 mount namespace
    却被归快层, 属分层偏移, 已在 tests/README.md 映射行与 tests/run 注释
    备案 (REWORK-02 P-3).

    PATH 构造 (REWORK-02 P-1): 临时目录只软链 unshare/sh/mount, 不依赖系统
    PATH 目录的内容; 宿主 /usr/bin/podman 常见也不会进子进程 PATH.
    """
    target = make_target(tmp_path)
    fakebin = _no_podman_path(tmp_path)
    env = os.environ.copy()
    env["PATH"] = str(fakebin)  # 只含 unshare/sh/mount, 与系统 PATH 内容无关
    env[ENV_RUNTIME_DIR] = str(tmp_path / "rt")
    cmd = [
        str(fakebin / "unshare"), "-m", "-r", str(fakebin / "sh"), "-c",
        'mount -t tmpfs tmpfs /run && exec "$1" "$2" build "$3" --json',
        "sh", sys.executable, str(CLI_SCRIPT), str(target),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    obj = stdout_json(proc)
    if obj is None:
        raise AssertionError(
            "子进程没有产出可解析的 --json 输出, 大概率是环境前置不满足 "
            "(unshare -m -r 需要非特权 user namespace, mount 需要挂载权限, "
            f"见 docstring): rc={proc.returncode} stdout={proc.stdout!r} "
            f"stderr={proc.stderr!r}")
    assert proc.returncode == 1, f"应报错退出 1: rc={proc.returncode} stderr={proc.stderr!r}"
    assert obj["success"] is False
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


@pytest.fixture
def srv(tmp_path):
    """真实 serve/stop 生命周期控制器, 收尾加强杀不残留进程."""
    from codemap_service_helpers import CodemapSrv

    controller = CodemapSrv(tmp_path)
    yield controller
    controller.cleanup()


def test_port_change_human_output_reports_stale_address_and_port(srv, tmp_path):
    """P-7 (REWORK-02): 人类可读形态的换端口断言.

    "旧地址已失效" 此前只有 --json 形态的自动断言 (test_delivery_output),
    人类可读形态只能靠 human_summary 铺开同一份结果 dict 的结构推断; 本用例
    用非 --json 形态真跑一次换端口 (record 来源首启 -> stop -> --port 换
    端口), 直接观察 stdout 含失效说明与端口信息.
    """
    from codemap_service_helpers import CONFIRMED_ADDR, free_port, use_temp_home

    use_temp_home(srv, tmp_path, confirmed=CONFIRMED_ADDR)
    srv.prime()
    first, _ = srv.serve()  # --json 首启, 留痕交付 URL
    old_url = first["url"]
    srv.stop()
    new_port = free_port()
    proc = srv.cli("serve", "--port", str(new_port))  # 不带 --json: 人类可读形态
    assert proc.returncode == 0, (
        f"换端口 serve 应成功: stdout={proc.stdout!r} stderr={proc.stderr!r}")
    assert "旧地址已失效" in proc.stdout, (
        f"人类可读输出应写明旧地址已失效: {proc.stdout!r}")
    assert f"port: {new_port}" in proc.stdout, (
        f"人类可读输出应含新端口信息: {proc.stdout!r}")
    assert old_url in proc.stdout, (
        f"人类可读输出应含旧交付 URL (previous_url 铺开): {proc.stdout!r}")
