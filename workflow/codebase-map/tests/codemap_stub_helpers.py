"""codebase-map 测试共享工具: 本地 stub podman 与伪官方前端产物 (TC-02 系列).

唯一命名模块, 刻意不叫 conftest (pytest.ini 头注释: 多树 conftest 同名会
互相覆盖, 本树共享工具一律放唯一命名模块, 先例 codemap_helpers.py).

进程接缝 (m25 TECHNICAL "接缝与依赖"): stub podman 脚本由用例现场写入
tmp_path 并只通过 PATH 注入子进程环境, 不入仓库 (BR-031); 它只证明参数
构造与流程接线, 不构成"分析可用"证据.

文件接缝: 官方前端 web.zip 按 m25 EXECUTION 验证策略"本地可替换, 测试可放
伪产物并预置 sha256 期望值" -- 期望值通过 monkeypatch codemap_common 常量
注入, 生产代码路径恒用常量本身, 没有任何旁路.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

from codemap_helpers import SCRIPTS_DIR  # noqa: F401  (顺带完成 scripts 注入 sys.path)

import codemap_common as cmc  # noqa: E402

# ---------------------------------------------------------------------------
# stub podman 脚本 (写进 tmp_path, 只通过 PATH 注入)
# ---------------------------------------------------------------------------

STUB_PODMAN_BODY = '''#!/usr/bin/env python3
"""测试专用 stub podman: 只存在于测试临时目录, 不入仓库.

行为由环境变量驱动 (全部经 PATH 注入的子进程环境传递):
  CODEMAP_STUB_DIR            stub 状态目录: calls.jsonl 逐行记录每次调用的完整 argv
  CODEMAP_STUB_IMAGE_PRESENT  =1 时 image inspect 直接成功 (本地已有镜像);
                              否则 inspect 失败, 直到 pull 在状态目录留下标记
  CODEMAP_STUB_REPO_DIGESTS   JSON 数组, image inspect 打印的 RepoDigests
  CODEMAP_STUB_RUN_FAIL       =1 时 run 以退出码 1 失败 (注入失败场景)

podman run: 解析 -v <dir>:/out 挂载, 按 ccsh 子命令写入伪产物
(deps.cc.json / metrics.cc.json / cc.json), 内容带 run 序号供覆盖断言.
"""
import json
import os
import pathlib
import sys

argv = sys.argv[1:]
state = pathlib.Path(os.environ["CODEMAP_STUB_DIR"])
state.mkdir(parents=True, exist_ok=True)
calls_path = state / "calls.jsonl"
with calls_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"argv": argv}, ensure_ascii=False) + "\\n")


def fail(message):
    sys.stderr.write("stub podman: " + message + "\\n")
    raise SystemExit(1)


if argv[:2] == ["image", "inspect"]:
    marker = state / "image-present"
    if os.environ.get("CODEMAP_STUB_IMAGE_PRESENT") == "1":
        marker.write_text("1\\n")
    if not marker.exists():
        fail("image not found (stub)")
    sys.stdout.write(os.environ.get("CODEMAP_STUB_REPO_DIGESTS", "[]") + "\\n")
    raise SystemExit(0)

if argv[:1] == ["pull"]:
    (state / "image-present").write_text("1\\n")
    sys.stdout.write("stub: pulled (simulated, no network)\\n")
    raise SystemExit(0)

if argv[:1] == ["run"]:
    out_dir = None
    for i, arg in enumerate(argv):
        if arg == "-v" and i + 1 < len(argv) and argv[i + 1].endswith(":/out"):
            out_dir = pathlib.Path(argv[i + 1][: -len(":/out")])
    if out_dir is None:
        fail("run without /out mount: " + json.dumps(argv))
    out_dir.mkdir(parents=True, exist_ok=True)
    run_no = sum(
        1
        for line in calls_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line)["argv"][:1] == ["run"]
    )
    joined = " ".join(argv)
    if "dependencyparser" in joined:
        product = "deps.cc.json"
    elif "unifiedparser" in joined:
        product = "metrics.cc.json"
    elif "merge" in joined:
        product = "cc.json"
    else:
        fail("unknown ccsh step: " + joined)
    (out_dir / product).write_text(
        json.dumps({"stub": product, "run": run_no}, ensure_ascii=False), encoding="utf-8")
    if os.environ.get("CODEMAP_STUB_RUN_FAIL") == "1":
        fail("injected run failure")
    raise SystemExit(0)

fail("unexpected invocation: " + json.dumps(argv))
'''


def make_stub_podman(tmp_path: Path) -> Path:
    """写 stub podman 脚本并置可执行, 返回其所在目录 (供 PATH 前置)."""
    bin_dir = tmp_path / "stub-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    podman = bin_dir / "podman"
    podman.write_text(STUB_PODMAN_BODY, encoding="utf-8")
    podman.chmod(0o755)
    return bin_dir


def stub_env(bin_dir, state_dir, *, image_present=False, repo_digests=None, run_fail=False) -> dict:
    """stub podman 的子进程环境: PATH 前置 stub 目录 + stub 行为开关."""
    if repo_digests is None:
        repo_digests = [
            f"docker.io/codecharta/codecharta-analysis@{cmc.IMAGE_SINGLE_ARCH_DIGEST}",
            f"docker.io/codecharta/codecharta-analysis@{cmc.IMAGE_MULTI_ARCH_DIGEST}",
        ]
    env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        "CODEMAP_STUB_DIR": str(state_dir),
        "CODEMAP_STUB_REPO_DIGESTS": json.dumps(repo_digests),
    }
    if image_present:
        env["CODEMAP_STUB_IMAGE_PRESENT"] = "1"
    if run_fail:
        env["CODEMAP_STUB_RUN_FAIL"] = "1"
    return env


def stub_calls(state_dir) -> list:
    """stub podman 记录的全部调用 (含完整 argv), 供用例断言参数形状."""
    path = Path(state_dir) / "calls.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stub_run_argv(state_dir) -> list:
    """仅 podman run 调用的完整 argv, 按发生顺序."""
    return [entry["argv"] for entry in stub_calls(state_dir) if entry["argv"][:1] == ["run"]]


def ccsh_part(run_argv) -> list:
    """podman run argv 里镜像 tag 之后的 ccsh 命令部分."""
    return run_argv[run_argv.index(cmc.IMAGE_TAG) + 1:]


# ---------------------------------------------------------------------------
# 伪官方前端产物 (文件接缝: cache/frontend 本地可替换)
# ---------------------------------------------------------------------------


def pseudo_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_real_zip_bytes(entries: dict) -> bytes:
    """把 {名字: 字节} 打成真 zip (供解包路径使用)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def preset_frontend_cache(
    runtime: Path,
    *,
    zip_bytes: bytes = b"pseudo official web.zip",
    unpacked_entries: dict | None = None,
    frontend_version: str | None = None,
    populate_serve_root: bool = True,
) -> str:
    """预置"上次成功初始化留下的"前端产物: web.zip + unpacked/ + cache.json 版本记录
    (可选 serve-root/index.html). 返回 zip 字节的 sha256, 供用例把它预置为期望值.

    frontend_version 传旧版本号 (如 vis-2.8.0) 即伪造"版本升级前的残留状态".
    """
    runtime = Path(runtime)
    frontend_dir = runtime / "cache" / "frontend" / cmc.FRONTEND_VERSION
    frontend_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dir / "web.zip").write_bytes(zip_bytes)
    unpacked = frontend_dir / "unpacked"
    unpacked.mkdir(parents=True, exist_ok=True)
    for name, data in (unpacked_entries or {"index.html": b"<html>pseudo vis</html>", "app.js": b"// pseudo"}).items():
        target = unpacked / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    cache_path = runtime / "cache" / "cache.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({
        "frontend": {
            "version": frontend_version or cmc.FRONTEND_VERSION,
            "zip_sha256": pseudo_sha(zip_bytes),
            "unpacked_at": "2026-01-01T00:00:00+00:00",
        },
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    if populate_serve_root:
        serve_root = runtime / "serve-root"
        serve_root.mkdir(parents=True, exist_ok=True)
        (serve_root / "index.html").write_bytes(b"<html>pseudo serve-root</html>")
    return pseudo_sha(zip_bytes)
