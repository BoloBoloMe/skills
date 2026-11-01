#!/usr/bin/env python3
"""codebase-map CLI 入口 (m25 TECHNICAL.md 模块划分).

子命令 (m13 D009, BR-013): build / serve / stop 三子命令各管一件事, 不合并.
本 issue 只注册 build 的骨架; serve 与 stop 由后续 issue 注册, 不建占位分支,
不写会静默成功的空实现.

build <目标目录> [--exclude <glob>]... [--json]:
  前置检查 (顺序固定, 命中即停并报错退出, m13 D003 / BR-021 不降级):
    1. 不在沙箱容器内 (/run/.containerenv 不存在) -> container_not_supported
    2. 目标目录存在且是目录                       -> target_missing
    3. podman 在 PATH 上可用                      -> podman_missing
  分析流水线 (初始化, 三次 podman run, 门禁, 统计, 产出) 属后续 issue;
  就位之前前置检查全过也一律 internal_error 退出, 未写任何数据.

输出形状 (两种形态字段一致, 共用同一份结果 dict):
  --json : stdout 恰好一行 JSON (success/command/error 或负载字段)
  默认   : stdout 多行人类可读摘要; 失败时 stderr 另写错误码与下一步动作
退出码: 成功 0, 失败 1 (argparse 用法错误为 2).

约束: 只 import python 标准库加同目录共享模块 (BR-033, m25 D012); 对
codemap_common 的调用是 TECHNICAL "接缝与依赖" 定义的内部接缝.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codemap_common as cmc  # noqa: E402  (脚本同目录, 保证任意 cwd 可跑)

CONTAINER_MARKER = "/run/.containerenv"  # podman/oci 容器内存在的标记文件


# ---------------------------------------------------------------------------
# 前置检查 (命中即返回错误信封, 未命中返回 None)
# ---------------------------------------------------------------------------


def _precheck_container():
    if Path(CONTAINER_MARKER).exists():
        return cmc.error_result(
            "build",
            "container_not_supported",
            f"检测到 {CONTAINER_MARKER}: 本工具只在宿主机上使用, 不在沙箱容器内运行.",
            "改在宿主机上执行本命令; 容器内不做降级分析, 也不提供调用宿主服务的接口.",
        )
    return None


def _precheck_target(target: Path):
    if not target.is_dir():
        return cmc.error_result(
            "build",
            "target_missing",
            f"目标目录不存在或不是目录: {target}",
            "确认目标库路径后重试; 数据键取该目录的 realpath.",
        )
    return None


def _precheck_podman():
    if shutil.which("podman") is None:
        return cmc.error_result(
            "build",
            "podman_missing",
            "PATH 上找不到 podman, 无法运行官方分析镜像.",
            "先安装 podman 并确认 `podman --version` 可用, 再重试.",
        )
    return None


# ---------------------------------------------------------------------------
# 子命令核心 (只返回结果 dict, 不碰 stdout 与 sys.exit)
# ---------------------------------------------------------------------------


def run_build(target, user_excludes) -> dict:
    """build 骨架: 前置检查 -> (分析流水线属后续 issue).

    user_excludes 在流水线接线时经 collect_excludes/excluded_regexes 消费
    (ISSUE-02/03); 本骨架只收下不使用, 不做任何分析动作.
    """
    failure = _precheck_container()
    if failure is None:
        failure = _precheck_target(Path(target))
    if failure is None:
        failure = _precheck_podman()
    if failure is not None:
        return failure
    return cmc.error_result(
        "build",
        "internal_error",
        "前置检查已全部通过, 但分析流水线尚未接入本骨架.",
        "本版本还不能完成分析且未写任何数据; 流水线接线后重试.",
    )


# ---------------------------------------------------------------------------
# CLI 适配层
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codebase-map.py",
        description="代码库结构地图的构建与托管 (只在宿主机使用).",
    )
    sub = parser.add_subparsers(dest="command", metavar="<子命令>", required=True)
    p_build = sub.add_parser(
        "build", help="分析目标库并产出结构数据 (.cc.json); 只在宿主机使用.")
    p_build.add_argument("target", help="被分析的目标库目录")
    p_build.add_argument(
        "--exclude", action="append", default=[], metavar="GLOB",
        help="追加排除规则 (glob 语义, 脚本负责转成分析端正则), 可多次.")
    p_build.add_argument(
        "--json", dest="as_json", action="store_true",
        help="stdout 只输出一行 JSON.")
    return parser


def _emit(result: dict, as_json: bool) -> int:
    """输出结果并给出退出码; 成功 0, 失败 1."""
    if as_json:
        sys.stdout.write(cmc.json_line(result))
    else:
        sys.stdout.write(cmc.human_summary(result))
        if not result["success"]:
            err = result["error"]
            sys.stderr.write(f"错误 {err['code']}: {err['message']}\n")
            sys.stderr.write(f"下一步: {err['hint']}\n")
    sys.stdout.flush()
    return 0 if result["success"] else 1


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = run_build(args.target, args.exclude)
        else:  # pragma: no cover - subparsers required=True 挡住其余取值
            result = cmc.error_result(
                args.command, "internal_error",
                f"未知子命令: {args.command}", "查看 --help.")
    except Exception as exc:  # 兜底: 未预期异常也落稳定错误码, 不裸栈不静默
        result = cmc.error_result(
            getattr(args, "command", "?"), "internal_error",
            f"未预期异常: {exc}", "保留 stderr 全文并报告.")
    raise SystemExit(_emit(result, getattr(args, "as_json", False)))


if __name__ == "__main__":
    main()
