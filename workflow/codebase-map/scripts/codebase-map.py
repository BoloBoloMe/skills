#!/usr/bin/env python3
"""codebase-map CLI 入口 (m25 TECHNICAL.md 模块划分).

子命令 (m13 D009, BR-013): build / serve / stop 三子命令各管一件事, 不合并.
build 由 ISSUE-02/03 接线; serve 与 stop 自 ISSUE-04 起注册, 编排
`codemap_service` 模块; serve 的地址解析与交付字段 (url/base_url/keys/
delivery_notes/address_missing 等) 归 ISSUE-05, 本版 serve 只保证端口,
状态, 复用与监听.

build <目标目录> [--exclude <glob>]... [--json]:
  前置检查 (顺序固定, 命中即停并报错退出, m13 D003 / BR-021 不降级):
    1. 不在沙箱容器内 (/run/.containerenv 不存在) -> container_not_supported
    2. 目标目录存在且是目录                       -> target_missing
    3. podman 在 PATH 上可用                      -> podman_missing
  分析流水线 (ISSUE-02 接线, 编排 codemap_analyze.run_build): 首次初始化
  (缺镜像拉镜像并校验单架构 digest, 缺官方前端下载 web.zip 并校验 sha256)
  + 三步 ccsh 分析 (dependencyparser/unifiedparser/merge), merge 产物逐字节
  写目标库 .codebase-map/cc.json; 门禁判定, 统计分母, 副本复制与 state.json
  更新归 ISSUE-03, 本版 result 不含这些字段也不写假值.

serve [--port <N>] [--address <IP>] [--json]:
  起或复用常驻服务并交付 URL; 判定分支与端口决策全部在
  codemap_service.run_serve. 有存活实例时传不同 --port 返回
  instance_running; 状态与探活对不上返回 state_mismatch; 目标端口被别的
  程序占用返回 port_in_use, 不静默顺延.
  --address 把用户确认过的局域网地址传入本次调用, 只影响本次 URL 组装与
  交付文案, 不落盘 (ISSUE-05 接线, m25 D017); 未传时按顺序取已确认地址
  记录文件, 再取候选枚举; 解析不出且未传时服务照常起, 输出
  address_missing + candidates, 退出码仍为 0.
  交付字段 (url/base_url/keys/delivery_notes/address_missing 等) 由
  codemap_service 的交付输出层组装, 调用会话只原样转述 (BR-037).
  serve/stop 不做网络动作 (BR-027), 容器内不作 build 式拒绝.

stop [--json]:
  停整个服务并归一化 state.json (pid 置空, 写 stopped_at, 保留
  port/last_port/last_url, m25 D018); 没有实例时幂等成功. 输出
  {success, command, stopped, pid?, port?}.

输出形状 (两种形态字段一致, 共用同一份结果 dict):
  --json : stdout 恰好一行 JSON (success/command/error 或负载字段)
  默认   : stdout 多行人类可读摘要; 失败时 stderr 另写错误码与下一步动作
退出码: 成功 0, 失败 1 (argparse 用法错误为 2).

约束: 只 import python 标准库加同目录共享模块 (BR-033, m25 D012); 对
codemap_common / codemap_service 的调用是 TECHNICAL "接缝与依赖" 定义的
内部接缝.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codemap_common as cmc  # noqa: E402  (脚本同目录, 保证任意 cwd 可跑)
import codemap_service as cms  # noqa: E402  (serve/stop 的编排目标, ISSUE-04 注册)
import codemap_analyze as cma  # noqa: E402  (build 的初始化与分析流水线, ISSUE-02 接线)

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


def run_build(target, user_excludes, runtime_base=None) -> dict:
    """build: 前置检查 -> 初始化与分析流水线 (codemap_analyze.run_build).

    runtime_base 只供测试注入隔离运行时目录; CLI 路径不传, 走
    CODEMAP_RUNTIME_DIR / 默认运行时目录.
    """
    failure = _precheck_container()
    if failure is None:
        failure = _precheck_target(Path(target))
    if failure is None:
        failure = _precheck_podman()
    if failure is not None:
        return failure
    return cma.run_build(Path(target), user_excludes, runtime_base=runtime_base)


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
    p_serve = sub.add_parser(
        "serve", help="起或复用常驻服务并交付 URL 与交付说明.")
    p_serve.add_argument(
        "--port", type=int, default=None, metavar="N",
        help="指定本次端口: 无存活实例时生效; 有存活实例时返回 instance_running.")
    p_serve.add_argument(
        "--address", default=None, metavar="IP",
        help="用户确认过的局域网地址, 只作用于本次调用, 不落盘 (m25 D017).")
    p_serve.add_argument(
        "--json", dest="as_json", action="store_true",
        help="stdout 只输出一行 JSON.")
    p_stop = sub.add_parser(
        "stop", help="停整个服务并归一化状态; 没有实例时幂等成功.")
    p_stop.add_argument(
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
        elif args.command == "serve":
            result = cms.run_serve(args.port, args.address)
        elif args.command == "stop":
            result = cms.run_stop()
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
