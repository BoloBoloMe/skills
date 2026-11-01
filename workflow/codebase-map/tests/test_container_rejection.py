"""TC-007 (AC-007 主用例): 沙箱容器内 build 被拒, 不降级, 不产出数据.

场景 (PRODUCT @AC-007 @failure @G-001 @BR-021 "在沙箱容器里调用被拒绝"):
  在沙箱容器内执行 build -> 命令报错退出并说明本工具只在宿主机上使用,
  不尝试任何降级分析.

验证分工 (m25 D016): 本用例是容器内场景, 宿主上跳过; 宿主侧构造
target_missing/podman_missing 归 ISSUE-07, 不用 stub 顶替.
"""
from __future__ import annotations

import pytest

from codemap_helpers import (
    ENV_RUNTIME_DIR,
    IN_CONTAINER,
    make_target,
    run_cli,
    stdout_json,
)


@pytest.mark.skipif(
    not IN_CONTAINER,
    reason="容器内场景用例: 仅在 /run/.containerenv 存在的沙箱内运行 (m25 D016 验证分工)",
)
def test_tc007_build_rejected_in_container_and_produces_no_data(tmp_path):
    """TC-007: 真实入口 build --json 报 container_not_supported, 退出码非 0, 零产出."""
    target = make_target(tmp_path)
    runtime = tmp_path / "runtime"

    proc = run_cli("build", str(target), "--json",
                   env_extra={ENV_RUNTIME_DIR: str(runtime)})
    obj = stdout_json(proc)

    assert obj is not None, f"stdout 无 JSON: {proc.stdout!r}"
    assert obj["success"] is False
    assert obj["command"] == "build"
    assert obj["error"]["code"] == "container_not_supported"
    assert proc.returncode != 0

    # 不产出任何数据文件: 目标库无 .codebase-map, 运行时 serve-root 无 .cc.json
    assert not (target / ".codebase-map").exists()
    serve_root = runtime / "serve-root"
    assert not serve_root.exists() or not list(serve_root.glob("*.cc.json"))
