#!/usr/bin/env python3
"""codebase-map 分析与产出 (m25 TECHNICAL.md "分析与产出").

ISSUE-02 落地首次初始化与三步分析; ISSUE-03 在此之上补齐门禁判定, 统计
分母, 副本分发与 state.json 的 data_keys 写入, build 由此从"能出数据"变成
"能判断该不该交付, 并把数据放到页面能取到的地方".

责任:
  门禁 (写副本之前判定, m25 D001 / m13 D029 / m24 U001):
    - edges = len(lenses.dependency.edges.dependencies)
    - level_kinds = 文件节点 (type=File) 上 level 的取值种数
    - 通过条件 edges > 0 且 level_kinds >= 3; 不通过时仍把 merge 产物写进
      目标库 .codebase-map/cc.json 供复查, 但不复制副本, 返回 gate_failed.
  统计 (门禁失败也完整输出, BR-024/BR-025, 口径归因非功能要求):
    - 宿主侧按与分析端同一份排除集扫盘, 把每份磁盘文件归入且只归入一个
      口径桶; 分母不硬凑相等, 只要求差值逐类归因可对账 (m25 D019).
  产出与副本 (m13 D010/D023, BR-010/BR-012, BR-036):
    - 原件写 <target>/.codebase-map/cc.json; 门禁通过后复制副本到
      serve-root/<key> (先写临时文件再 os.replace), 锁内更新
      state.json.data_keys; 不删任何其它库的副本.
  首次初始化 (仅缺失时, m25 D009 / m13 D030):
    - 本地没有镜像就 `podman pull`, 然后校验 RepoDigests 含单架构清单
      digest (m25 D013/D016, 阻断项); 多架构清单 digest 只记录进
      cache/cache.json, 不阻断.
    - 本地没有官方前端 web.zip 就下载 (vis-2.9.1), sha256 校验不过
      frontend_hash_mismatch, 下载不到 frontend_unavailable; 解包到
      cache/frontend/vis-2.9.1/unpacked/ 再整体同步进 serve-root/
      (版本升级整体替换, 不叠加旧产物).
  三步分析, 每步一次 `podman run`, 各自一份日志 (m23 PROBE 6.1/6.2/6.3):
    1. ccsh dependencyparser /proj -o /out/deps.cc.json -nc -e <排除正则>
    2. ccsh unifiedparser /proj -nc -o /out/metrics.cc.json
    3. ccsh merge /out/metrics.cc.json /out/deps.cc.json -o /out/cc.json -nc
    固定参数 --rm --network=none --userns=keep-id -v <target>:/proj:ro
    -v <cache/work>:/out; 不用 --privileged, 不挂 docker socket, 不映射
    端口 (BR-017). 中间产物留 cache/work/ 供复查, 下次运行先清空再覆盖.
  产出: merge 产物逐字节写 <target>/.codebase-map/cc.json, 不改字段不注入
  自造指标; 同库重跑覆盖同一路径, 不保留历史版本.

失败出口 (不降级, m13 D003 / BR-021, 一律停下不拿旧产物冒充):
  image_unavailable      podman pull 失败或拉取后仍找不到镜像
  image_digest_mismatch  RepoDigests 不含单架构清单 digest
  frontend_unavailable   web.zip 下载失败 (含无网络)
  frontend_hash_mismatch web.zip sha256 与常量不符 (含预置/残留坏产物)
  gate_failed            门禁不通过 (依赖边为 0 或文件层号种数 < 3, m25 D001)
  internal_error         三步分析失败, merge 产物缺失或不可解析, 运行时锁超时

网络面 (BR-027): 只有初始化的 pull 与前端下载出网; serve/stop 不做网络
动作. 进程接缝: podman 命令行, 测试用本地 stub 核对参数构造, stub 不构成
"分析可用"证据 (m25 EXECUTION 验证策略).

约束: 只 import python 标准库加同目录共享模块 (BR-033, m25 D012); 对
codemap_common 的排除集/键/常量与 codemap_service 的文件锁是内部接缝, 不
另写一份常量或排除集.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import codemap_common as cmc
import codemap_service as cms  # 仅复用运行时文件锁 (_acquire_lock/_release_lock)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 官方前端 web.zip 的下载地址 (GitHub release, m25 TECHNICAL "网络接缝");
# 容器内测试不触网, 该 URL 只在宿主真实初始化时使用.
FRONTEND_ZIP_URL = (
    "https://github.com/CodeCharta/CodeCharta/releases/download/"
    f"{cmc.FRONTEND_VERSION}/web.zip"
)

WORK_REL = "cache/work"
FRONTEND_REL = "frontend"  # 相对 cache_dir 的子路径
CACHE_MANIFEST_REL = "cache.json"  # 相对 cache_dir
CC_JSON_NAME = "cc.json"
DEPS_NAME = "deps.cc.json"
METRICS_NAME = "metrics.cc.json"

INIT_NOTICE = (
    "首次初始化已执行: 拉取官方分析镜像与下载官方前端包 (vis-2.9.1) 属于首次"
    "初始化的慢操作, 只在本地缺失时进行; 本次耗时已计入 duration_seconds, "
    "之后镜像与前端产物齐备时 build 会跳过初始化."
)


class _AnalyzeError(Exception):
    """携带稳定错误码的分析失败; run_build 捕获后转 error_result, 不裸栈."""

    def __init__(self, code: str, message: str, hint: str):
        super().__init__(message)
        self.code, self.message, self.hint = code, message, hint


# ---------------------------------------------------------------------------
# 纯函数: digest 口径 (m25 D013/D016; TC-02-06)
# ---------------------------------------------------------------------------


def _digest_present(repo_digests, digest: str) -> bool:
    """RepoDigests 条目形如 `repo@sha256:...`, 兼容裸 digest 写法."""
    return any(digest in entry for entry in repo_digests or [])


def check_image_digests(repo_digests) -> tuple:
    """返回 (单架构清单 digest 是否在 RepoDigests, 多架构清单 digest 是否在).

    阻断只看单架构; 多架构只记录不阻断 (m25 D013/D016), 不信镜像内自报版本号.
    """
    single_ok = _digest_present(repo_digests, cmc.IMAGE_SINGLE_ARCH_DIGEST)
    multi_present = _digest_present(repo_digests, cmc.IMAGE_MULTI_ARCH_DIGEST)
    return single_ok, multi_present


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 镜像侧: inspect / pull / 校验
# ---------------------------------------------------------------------------


def _image_repo_digests():
    """`podman image inspect --format {{json .RepoDigests}}`; 镜像不在返回 None."""
    proc = subprocess.run(
        ["podman", "image", "inspect", "--format", "{{json .RepoDigests}}", cmc.IMAGE_TAG],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return None


def _pull_image():
    proc = subprocess.run(["podman", "pull", cmc.IMAGE_TAG], capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise _AnalyzeError(
            "image_unavailable",
            f"拉取官方分析镜像失败: {cmc.IMAGE_TAG}"
            + (f" ({detail[-1]})" if detail else ""),
            "确认宿主能访问镜像 registry 后重试; 不降级, 不用其它镜像顶替.",
        )
    digests = _image_repo_digests()
    if digests is None:
        raise _AnalyzeError(
            "image_unavailable",
            f"podman pull 已执行, 但仍 inspect 不到镜像 {cmc.IMAGE_TAG}.",
            "检查 podman 存储后重试; 不降级.",
        )
    return digests


def _ensure_image(steps: list) -> list:
    """本地没有镜像就 pull; 校验单架构 digest. 返回 RepoDigests."""
    digests = _image_repo_digests()
    if digests is None:
        steps.append(f"podman pull {cmc.IMAGE_TAG} (本地无镜像)")
        digests = _pull_image()
    single_ok, multi_present = check_image_digests(digests)
    if not single_ok:
        raise _AnalyzeError(
            "image_digest_mismatch",
            f"镜像 {cmc.IMAGE_TAG} 的 RepoDigests 不含预期的单架构清单 digest "
            f"{cmc.IMAGE_SINGLE_ARCH_DIGEST}"
            + (f" (多架构清单 digest {cmc.IMAGE_MULTI_ARCH_DIGEST} 在场, 只记录不阻断)"
               if multi_present else ""),
            "用 `podman pull` 更新到官方 2.3.0 镜像后重试; 不采信镜像内自报版本号, 不降级.",
        )
    return digests


# ---------------------------------------------------------------------------
# 前端侧: 下载 / 校验 / 解包 / 整体同步
# ---------------------------------------------------------------------------


def _frontend_zip_path(cache_dir: Path) -> Path:
    return cache_dir / FRONTEND_REL / cmc.FRONTEND_VERSION / "web.zip"


def _frontend_unpacked_path(cache_dir: Path) -> Path:
    return cache_dir / FRONTEND_REL / cmc.FRONTEND_VERSION / "unpacked"


def verify_frontend_zip(zip_path, expected_sha256=None) -> str:
    """对在场的 web.zip 做 sha256 校验, 返回实际哈希; 不符即 frontend_hash_mismatch.

    校验对象是"当前在场的产物"而不只是刚下载的文件: 残留的旧版/损坏包不得
    冒充当前版本 (m25 D009). expected 参数只供测试注入 (m25 EXECUTION 文件
    接缝: "测试可放伪产物并预置 sha256 期望值"), 生产路径恒用 codemap_common
    常量, 不提供任何旁路.
    """
    expected = expected_sha256 or cmc.FRONTEND_ZIP_SHA256
    actual = sha256_file(zip_path)
    if actual != expected:
        raise _AnalyzeError(
            "frontend_hash_mismatch",
            f"官方前端 web.zip 的 sha256 与预期不符: 期望 {expected}, 实际 {actual} ({zip_path}).",
            "删除该 cache/frontend/ 目录后重跑 build 以重新下载; 不用旧产物或本机其它前端顶替.",
        )
    return actual


def download_frontend_zip(cache_dir: Path) -> None:
    """下载官方 web.zip 到 cache/frontend/<版本>/web.zip; 下载不到即 frontend_unavailable."""
    zip_path = _frontend_zip_path(cache_dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = zip_path.with_name(zip_path.name + ".part")
    try:
        with urllib.request.urlopen(FRONTEND_ZIP_URL, timeout=60) as resp, \
                open(tmp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except (OSError, urllib.error.URLError) as exc:
        tmp.unlink(missing_ok=True)
        raise _AnalyzeError(
            "frontend_unavailable",
            f"取不到官方前端产物: 下载 {FRONTEND_ZIP_URL} 失败: {exc}",
            "确认宿主能访问 GitHub release 后重试; 缺网络就停下, 不降级, 不用本机其它前端顶替.",
        )
    try:
        verify_frontend_zip(tmp)  # 先校验再落位, 坏包不进 cache
    except _AnalyzeError:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, zip_path)


def unpack_frontend(cache_dir: Path) -> Path:
    """解包 web.zip 到 unpacked/ (先清空, 保证是本 zip 的产物)."""
    unpacked = _frontend_unpacked_path(cache_dir)
    if unpacked.exists():
        shutil.rmtree(unpacked)
    unpacked.mkdir(parents=True)
    with zipfile.ZipFile(_frontend_zip_path(cache_dir)) as zf:
        zf.extractall(unpacked)
    return unpacked


def sync_frontend_to_serve_root(unpacked: Path, serve_root: Path) -> None:
    """整体替换: 清掉 serve-root 里除 *.cc.json 数据副本外的全部内容, 再镜像解包产物.

    版本升级不留旧版本文件 (m13 D030); 其它库的数据副本是 BR-036 的保护对象,
    同步时原样保留.
    """
    serve_root.mkdir(parents=True, exist_ok=True)
    for entry in serve_root.iterdir():
        if entry.is_file() and not entry.is_symlink() and entry.name.endswith(".cc.json"):
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()
    shutil.copytree(unpacked, serve_root, dirs_exist_ok=True)


def _ensure_frontend(cache_dir: Path, serve_root: Path, steps: list) -> dict:
    """缺什么补什么; 返回 {zip_sha256, unpacked_dir, unpacked_at}.

    齐备 = web.zip 在场且 sha256 过校验 + unpacked 非空 + cache.json 记录的
    前端版本就是当前常量 + serve-root 已有 index.html. cache.json 缺失或版本
    对不上视为旧版本残留, 整体重做解包与同步 (m13 D030 整体替换).
    """
    zip_path = _frontend_zip_path(cache_dir)
    if not zip_path.is_file():
        steps.append(f"下载官方前端 web.zip ({cmc.FRONTEND_VERSION})")
        download_frontend_zip(cache_dir)
    zip_sha = verify_frontend_zip(zip_path)

    prior_cache = _load_cache_json(cache_dir)
    prior_frontend = prior_cache.get("frontend") or {}
    unpacked_at = None
    unpacked = _frontend_unpacked_path(cache_dir)
    need_unpack = not (unpacked.is_dir() and any(unpacked.iterdir()))
    if prior_frontend.get("version") != cmc.FRONTEND_VERSION:
        need_unpack = True  # 首次或版本升级: 整体重做, 不叠加旧产物
    if need_unpack:
        steps.append(f"解包官方前端到 {unpacked.relative_to(cache_dir.parent)}")
        unpacked = unpack_frontend(cache_dir)
        unpacked_at = _utc_now_iso()
    if need_unpack or not (serve_root / "index.html").is_file():
        steps.append("整体同步官方前端进 serve-root/ (替换旧版产物, 不叠加)")
        sync_frontend_to_serve_root(unpacked, serve_root)
    if unpacked_at is None:
        unpacked_at = prior_frontend.get("unpacked_at") or _mtime_iso(unpacked)
    return {"zip_sha256": zip_sha, "unpacked_dir": unpacked, "unpacked_at": unpacked_at}


# ---------------------------------------------------------------------------
# cache.json (TECHNICAL "cache/cache.json 字段")
# ---------------------------------------------------------------------------


def _cache_manifest_path(cache_dir: Path) -> Path:
    return cache_dir / CACHE_MANIFEST_REL


def _load_cache_json(cache_dir: Path) -> dict:
    try:
        data = json.loads(_cache_manifest_path(cache_dir).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_cache_json(cache_dir: Path, data: dict) -> None:
    path = _cache_manifest_path(cache_dir)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# 三步分析 (m23 PROBE 6.1/6.2/6.3)
# ---------------------------------------------------------------------------


def _podman_run_base_args(target: Path, work_dir: Path) -> list:
    """固定隔离参数 (BR-017): --rm/--network=none/--userns=keep-id, 源码 :ro,
    出目录挂 cache/work; 不用 --privileged, 不挂 docker socket, 不映射端口."""
    return [
        "podman", "run", "--rm", "--network=none", "--userns=keep-id",
        "-v", f"{target}:/proj:ro",
        "-v", f"{work_dir}:/out",
        cmc.IMAGE_TAG,
    ]


def step1_dependencyparser(exclude_regexes) -> list:
    return ["ccsh", "dependencyparser", "/proj", "-o", f"/out/{DEPS_NAME}", "-nc",
            *(item for regex in exclude_regexes for item in ("-e", regex))]


def step2_unifiedparser() -> list:
    return ["ccsh", "unifiedparser", "/proj", "-nc", "-o", f"/out/{METRICS_NAME}"]


def step3_merge() -> list:
    # 官方管道损坏的替代 (m24 F002 / m23 6.3): 先各自出文件再 merge, metrics 在前 deps 在后
    return ["ccsh", "merge", f"/out/{METRICS_NAME}", f"/out/{DEPS_NAME}",
            "-o", f"/out/{CC_JSON_NAME}", "-nc"]


ANALYSIS_STEPS = (
    (1, "dependencyparser", "analyze-step1-dependencyparser.log", step1_dependencyparser),
    (2, "unifiedparser", "analyze-step2-unifiedparser.log", lambda _re: step2_unifiedparser()),
    (3, "merge", "analyze-step3-merge.log", lambda _re: step3_merge()),
)


def _analysis_log_path(base: Path, filename: str) -> Path:
    return base / "logs" / filename


def _run_analysis_step(base_args: list, step_cmd: list, log_path: Path, no: int, name: str) -> None:
    argv = [*base_args, *step_cmd]
    proc = subprocess.run(argv, capture_output=True, text=True)
    _write_step_log(log_path, argv, proc)
    if proc.returncode != 0:
        raise _AnalyzeError(
            "internal_error",
            f"第 {no} 步 ccsh {name} 以退出码 {proc.returncode} 失败, 日志: {log_path}",
            "查看该日志定位原因; 中间产物保留在 cache/work/ 供复查, 修复后重跑 build.",
        )


def _write_step_log(log_path: Path, argv: list, proc: subprocess.CompletedProcess) -> None:
    """每步一份日志: 完整 argv + 退出码 + stdout/stderr (0600, 不含源码内容)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        f"{_utc_now_iso()} ccsh 分析步骤日志",
        "argv: " + json.dumps(argv, ensure_ascii=False),
        f"exit: {proc.returncode}",
        "--- stdout ---",
        proc.stdout or "",
        "--- stderr ---",
        proc.stderr or "",
    ]
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(body) + "\n")


def _reset_work_dir(work_dir: Path) -> None:
    """清空 cache/work/ 再分析: 下次运行覆盖, 不留历史版本文件 (m13 D030 同取向)."""
    work_dir.mkdir(parents=True, exist_ok=True)
    for entry in work_dir.iterdir():
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


# ---------------------------------------------------------------------------
# 产出: merge 产物逐字节写目标库 (BR-031: 除它之外不改目标库)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 门禁 (写副本之前判定; m25 D001, m13 D029, m24 U001)
# ---------------------------------------------------------------------------


def _dependency_lens(merge_data: dict) -> tuple:
    """取 lenses.dependency 的 (nodes 映射, 边列表).

    边列表形状按 TECHNICAL 定的 2.1 口径 `lenses.dependency.edges.dependencies`
    读取; m23 实测的 2.0 形状里 edges 直接是数组 (PROBE 6.4 的统计脚本即按它
    写), 两种都认, 只读不改 (NG-006). 其余结构一律视为空, 交给门禁判 0.
    """
    dep = (merge_data.get("lenses") or {}).get("dependency") or {}
    nodes = dep.get("nodes") or {}
    edges_raw = dep.get("edges")
    if isinstance(edges_raw, dict):
        edges = edges_raw.get("dependencies") or []
    elif isinstance(edges_raw, list):
        edges = edges_raw
    else:
        edges = []
    return nodes, edges


def _files_tree_index(merge_data: dict) -> tuple:
    """遍历 files 树: 返回 ({节点id: type}, {文件相对路径}) .

    路径 = 根节点名以下的各级 name 以 / 相接 (根名是库根的名字, m23 实测样例
    与 tools/smoke.py 都形如 root/src/Main.java, 剥掉后才是库内相对路径).
    只读 merge 产物, 不改任何字段 (NG-006).
    """
    id_types: dict = {}
    file_paths: set = set()
    for root in merge_data.get("files") or []:
        # prefix = 库内相对路径 (不含根节点名); 根节点名非空时它不属于库内路径
        stack = [(root, "")]
        while stack:
            node, prefix = stack.pop()
            node_type = node.get("type")
            if node.get("id") is not None:
                id_types[node["id"]] = node_type
            if node is not root:
                name = node.get("name") or ""
                rel = f"{prefix}/{name}" if prefix else name
            else:
                rel = ""
            if node_type == "File" and rel:
                file_paths.add(rel)
            for child in node.get("children") or []:
                stack.append((child, rel))
    return id_types, file_paths


def evaluate_gate(merge_data: dict) -> dict:
    """门禁: edges = 依赖边数, level_kinds = 文件节点 level 取值种数.

    通过条件 edges > 0 且 level_kinds >= 3 (m25 D001, m13 D029 保留项).
    不通过时 gate.reason 写明缺什么并带实际数值; 同时命中两条时都写.
    """
    id_types, _ = _files_tree_index(merge_data)
    dep_nodes, dep_edges = _dependency_lens(merge_data)
    edges = len(dep_edges)
    levels = {
        attrs.get("level")
        for node_id, attrs in dep_nodes.items()
        if id_types.get(node_id) == "File" and attrs.get("level") is not None
    }
    level_kinds = len(levels)
    reasons = []
    if edges <= 0:
        reasons.append(f"依赖边为 0 条 (门禁要求 > 0)")
    if level_kinds < 3:
        reasons.append(
            f"文件层号只有 {level_kinds} 种, 少于 3 种 (门禁要求 >= 3): "
            f"取值 {sorted(levels, key=lambda v: (v is None, v))}"
        )
    gate = {"passed": not reasons, "edges": edges, "level_kinds": level_kinds}
    if reasons:
        gate["reason"] = "; ".join(reasons)
    return gate


# ---------------------------------------------------------------------------
# 统计与分母归因 (BR-024/BR-025, m25 D019, m23 PROBE 6.4/F003)
# ---------------------------------------------------------------------------

# 测试目录名: 与分析端 TestFileDetector 的目录规则一致 (m23 PROBE 6.4:
# 目录 test/tests/__tests__/spec/specs). 名字规则 (Java 名以 Test/Tests 结尾)
# 不在宿主侧复刻, 归 tool_defaults (分析端自带规则过滤).
TEST_DIR_NAMES = frozenset({"test", "tests", "__tests__", "spec", "specs"})

ZERO_DECL_REASON = "零声明"  # 解析了但无可分析声明, 整体不入依赖树 (m23 F003)


def compute_stats(target, merge_data: dict, user_excludes=()) -> tuple:
    """宿主侧统计与分母归因; 返回 (stats dict, 磁盘文件总数).

    统计等式 (TC-03-04 固定): 每份磁盘文件按以下先后次序归入且只归入一项 --

        磁盘文件总数 (target 下全部普通文件)
          = files_in_tree               # 相对路径能在 cc.json files 树对上的文件
          + excluded.dot_codebase_map   # 路径段 .codebase-map (本工具的数据目录,
                                        #   含本次写出的原件; AC-001 二次执行不扫数据目录)
          + excluded.build_dirs         # 默认结构性排除目录命中 (node_modules/.git/
                                        #   dist/build/target/vendor; 与 ccsh -e 同一套
                                        #   转义正则, 口径同源)
          + excluded.custom             # 用户 --exclude glob 命中 (同一套 glob->正则转换,
                                        #   m25 D019)
          + excluded.tests              # 测试目录命中 (路径段属 TEST_DIR_NAMES;
                                        #   BR-024 测试目录默认不扫)
          + excluded.tool_defaults      # 宿主扫描到但被分析端自带规则过滤: 扩展名
                                        #   不受支持 (明细单列 unsupported_extensions),
                                        #   或文件名以 Test/Tests 结尾 (TestFileDetector
                                        #   名字规则); 单列不与 custom 混 (m25 D019)
          + len(zero_declaration)       # 扫描到, 扩展名受支持, 未命中上述规则,
                                        #   但不在依赖树 (零声明, m23 F003)

    归因四类口径 (BR-024): 测试目录/构建目录/自定义排除按类计数 (excluded.*),
    零声明逐文件列清单 (zero_declaration), 工具默认过滤单列 tool_defaults.
    归入次序保证不重不漏: 在依赖树里的文件优先按 files_in_tree 归因, 排除规则
    命中的不再进扫描分母, 扫描分母里受支持扩展名才计入 scanned_files.

    scanned_files 分母口径 = files_in_tree + len(zero_declaration)
                            + tool_defaults 中扩展名受支持的部分,
    即 tool_defaults - unsupported_extensions 各项计数之和.
    """
    target = Path(target)
    _, in_tree_paths = _files_tree_index(merge_data)
    dep_nodes, dep_edges = _dependency_lens(merge_data)
    cyclic_edges = sum(1 for edge in dep_edges if edge.get("isCyclic"))
    upward_edges = sum(1 for edge in dep_edges if edge.get("isPointingUpwards"))
    supported_exts = {Path(p).suffix.lower() for p in in_tree_paths}

    # 排除口径同一份数据 (cmc.collect_excludes), 与喂给 ccsh 的正则同源 (BR-015)
    default_globs = tuple(g for g in cmc.DEFAULT_EXCLUDES if g != ".codebase-map")
    user_globs = tuple(g for g in user_excludes or () )
    default_regexes = [re.compile(cmc.glob_to_ccsh_regex(g)) for g in default_globs]
    user_regexes = [re.compile(cmc.glob_to_ccsh_regex(g)) for g in user_globs]

    excluded = {"tests": 0, "build_dirs": 0, "custom": 0, "dot_codebase_map": 0,
                "tool_defaults": 0}
    zero_declaration: list = []
    unsupported: dict = {}
    files_in_tree = 0
    scanned_files = 0
    disk_total = 0
    for dirpath, _dirnames, filenames in os.walk(target, followlinks=False):
        for filename in filenames:
            disk_total += 1
            rel = Path(dirpath, filename).relative_to(target).as_posix()
            segments = rel.split("/")
            # 归入次序 (不重不漏, 见函数头等式): 数据目录 -> 默认排除 -> 自定义
            # 排除 -> 在依赖树 -> 测试目录 -> 扫描分母内的工具规则与零声明
            if ".codebase-map" in segments:
                excluded["dot_codebase_map"] += 1
                continue
            if any(rx.search(rel) for rx in default_regexes):
                excluded["build_dirs"] += 1
                continue
            if any(rx.search(rel) for rx in user_regexes):
                excluded["custom"] += 1
                continue
            if rel in in_tree_paths:
                files_in_tree += 1
                scanned_files += 1
                continue
            if any(seg in TEST_DIR_NAMES for seg in segments[:-1]):
                excluded["tests"] += 1
                continue
            ext = Path(filename).suffix.lower()
            if ext not in supported_exts:
                excluded["tool_defaults"] += 1
                unsupported[ext] = unsupported.get(ext, 0) + 1
                continue
            scanned_files += 1
            stem = filename[: -len(ext)] if ext else filename
            if stem.endswith("Test") or stem.endswith("Tests"):
                excluded["tool_defaults"] += 1  # TestFileDetector 名字规则 (m23 PROBE 6.4)
                continue
            if rel not in in_tree_paths:
                zero_declaration.append({"path": rel, "reason": ZERO_DECL_REASON})
    zero_declaration.sort(key=lambda item: item["path"])
    unsupported_extensions = [
        {"ext": ext, "count": count}
        for ext, count in sorted(unsupported.items(), key=lambda item: (-item[1], item[0]))
    ]
    stats = {
        "scanned_files": scanned_files,
        "files_in_tree": files_in_tree,
        "excluded": excluded,
        "zero_declaration": zero_declaration,
        "unsupported_extensions": unsupported_extensions,
        "cyclic_edges": cyclic_edges,
        "upward_edges": upward_edges,
    }
    return stats, disk_total


# ---------------------------------------------------------------------------
# 副本分发与 state.json (BR-010/BR-012/BR-036, m13 D023, m25 D020)
# ---------------------------------------------------------------------------


def copy_to_serve_root(original: Path, serve_root: Path, key: str) -> Path:
    """把原件复制为 serve-root/<key>: 先写临时文件再 os.replace.

    副本与 index.html 同目录 (BR-012, 前端 <base href="./"> 约束); rename
    保证页面不会读到半个文件. 不删任何其它库的副本 (BR-036).
    """
    serve_root.mkdir(parents=True, exist_ok=True)
    dest = serve_root / key
    tmp = serve_root / (key + ".tmp")
    tmp.write_bytes(original.read_bytes())
    os.replace(tmp, dest)
    return dest


def _update_data_keys(base: Path, entry: dict) -> None:
    """锁内 upsert 本库的 data_keys 条目 (run_build 持锁期间调用).

    复用 codemap_service 的 state 读写原语 (原子写, 0600), 不另写一份;
    其它库的条目原样保留 (BR-036), 同键重跑覆盖同一条目 (m13 D020).
    """
    state, err = cms._load_state(base)
    if err is not None or state is None:
        state = cms._fresh_state(base)
    keys = [item for item in (state.get("data_keys") or []) if item.get("key") != entry["key"]]
    keys.append(entry)
    state["data_keys"] = keys
    cms._atomic_write_state(base, state)


def write_cc_json(work_dir: Path, target: Path) -> Path:
    src = work_dir / CC_JSON_NAME
    if not src.is_file():
        raise _AnalyzeError(
            "internal_error",
            f"第三步结束后没有找到 merge 产物 {src}; 分析未产出数据, 目标库未写任何文件.",
            "查看第三步日志定位 merge 失败原因; 修复后重跑 build.",
        )
    dest_dir = target / ".codebase-map"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / CC_JSON_NAME
    tmp = dest_dir / (CC_JSON_NAME + ".tmp")
    tmp.write_bytes(src.read_bytes())  # 逐字节拷贝, 不解包改写, 不注入自造指标
    os.replace(tmp, dest)
    return dest


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _mtime_iso(path: Path):
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None
    return datetime.datetime.fromtimestamp(stamp, datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 编排: build 的初始化与分析两段 (门禁/统计/副本/state.json 归 ISSUE-03)
# ---------------------------------------------------------------------------


def run_build(target, user_excludes=(), runtime_base=None) -> dict:
    """初始化 (缺失时) -> 三步分析 -> 写原件 -> 门禁 -> 统计 -> 副本与 data_keys.

    不碰 stdout, 不退出进程; 返回结果 dict 交 CLI 层. 全程持有运行时文件锁
    (TECHNICAL 关键流程): 副本复制与 state.json.data_keys 更新都在同一锁内.
    """
    started = time.monotonic()
    target = Path(target).resolve()
    base = Path(runtime_base).resolve() if runtime_base is not None else cmc.runtime_dir()
    cmc.ensure_runtime_layout(base)
    lock_fd = cms._acquire_lock(base)
    if lock_fd is None:
        return cmc.error_result(
            "build", "internal_error",
            f"运行时目录锁等待超过 {cms.LOCK_WAIT_SECONDS} 秒: {base / cms.LOCK_FILENAME}",
            "确认没有其它 codebase-map 调用长时间持锁后重试.",
        )
    try:
        steps: list = []
        # -- 初始化: 镜像 (本地没有才 pull; 校验每轮都做) --
        repo_digests = _ensure_image(steps)
        _, multi_present = check_image_digests(repo_digests)
        # -- 初始化: 官方前端 --
        cache_dir = base / "cache"
        frontend = _ensure_frontend(cache_dir, base / "serve-root", steps)
        # -- cache/cache.json: 字段齐全, 整体重写 --
        now = _utc_now_iso()
        _write_cache_json(cache_dir, {
            "image": {
                "tag": cmc.IMAGE_TAG,
                "single_arch_digest": cmc.IMAGE_SINGLE_ARCH_DIGEST,
                "multi_arch_digest": cmc.IMAGE_MULTI_ARCH_DIGEST if multi_present else None,
                "verified_at": now,
            },
            "frontend": {
                "version": cmc.FRONTEND_VERSION,
                "zip_sha256": frontend["zip_sha256"],
                "unpacked_at": frontend["unpacked_at"],
            },
            "excluded_globs": list(cmc.collect_excludes(user_excludes)),
            "written_at": now,
        })
        # -- 三步分析, 每步一次 podman run, 各自一份日志 --
        work_dir = base / WORK_REL
        _reset_work_dir(work_dir)
        exclude_regexes = cmc.excluded_regexes(user_excludes)
        base_args = _podman_run_base_args(target, work_dir)
        log_paths = []
        for no, name, log_name, cmd_builder in ANALYSIS_STEPS:
            log_path = _analysis_log_path(base, log_name)
            _run_analysis_step(base_args, cmd_builder(exclude_regexes), log_path, no, name)
            log_paths.append(str(log_path))
        # -- 产出: 逐字节写原件 -> 门禁 -> 统计 -> (通过时) 副本与 data_keys --
        dest = write_cc_json(work_dir, target)
        try:
            merge_data = json.loads(dest.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise _AnalyzeError(
                "internal_error",
                f"merge 产物不是合法 JSON, 无法判定门禁与统计: {dest} ({exc})",
                "查看第三步日志与 cache/work/cc.json 定位原因; 修复后重跑 build.",
            )
        gate = evaluate_gate(merge_data)
        stats, _disk_total = compute_stats(target, merge_data, user_excludes)
        performed = bool(steps)
        initialization = {"performed": performed, "steps": steps}
        if performed:
            initialization["notice"] = INIT_NOTICE
        duration_seconds = round(time.monotonic() - started, 3)
        key = cmc.data_key(target)
        if not gate["passed"]:
            # m25 D001: 数据照写目标库供复查, 不复制进 serve-root, 退出码非 0;
            # stats 与 initialization 照常完整输出, 不因失败省掉分母
            result = cmc.error_result(
                "build", "gate_failed",
                f"{gate['reason']}. 原件已写出 {dest} 供复查, 副本未复制进 serve-root.",
                "门禁不交付 (m13 D029): 在目标库补出依赖边与分层后重跑 build; "
                "分母与零声明清单见 stats, 可先核查 ccsh 是否可信.",
            )
            result.update({
                "target": str(target),
                "key": key,
                "cc_json_path": str(dest),
                "gate": gate,
                "stats": stats,
                "initialization": initialization,
                "duration_seconds": duration_seconds,
            })
            return result
        serve_copy = copy_to_serve_root(dest, base / "serve-root", key)
        _update_data_keys(base, {
            "key": key,
            "source_cc_json": str(dest),
            "built_at": _utc_now_iso(),
            "bytes": dest.stat().st_size,
        })
        return cmc.success_result(
            "build",
            target=str(target),
            key=key,
            cc_json_path=str(dest),
            serve_copy_path=str(serve_copy),
            gate=gate,
            stats=stats,
            analysis_logs=log_paths,
            initialization=initialization,
            duration_seconds=duration_seconds,
        )
    except _AnalyzeError as exc:
        return cmc.error_result("build", exc.code, exc.message, exc.hint)
    finally:
        cms._release_lock(lock_fd)
