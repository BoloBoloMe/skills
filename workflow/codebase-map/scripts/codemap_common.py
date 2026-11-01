"""codebase-map 共享常量与纯函数 (m25 TECHNICAL.md 模块划分).

责任: 数据键命名 (库名清洗 + 路径哈希), 运行时目录解析, 排除规则集合与
glob -> ccsh 正则转换, 版本与校验常量, 两种输出形态 (人类可读多行摘要 /
单行 JSON) 的编码辅助. 这些规则被三个模块共用, 收拢在一处避免调用点
各抄一份漂移 (m25 D005/D019, m13 D023/D017).

藏住: 命名与输出规则的全部细节.

约束: 只 import python 标准库 (m25 D012, BR-033); 只在宿主使用, 容器内
不做降级分析 (m13 D003), 本模块不触碰 podman 与网络.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# 版本与校验常量 (m25 TECHNICAL.md "版本常量"; m25 D013/D016)
# ---------------------------------------------------------------------------

# 分析端镜像 tag: 纯数字版本号, 不信镜像内 ccsh --version 自报 (m25 D013)
IMAGE_TAG = "docker.io/codecharta/codecharta-analysis:2.3.0"
# 单架构清单 digest: 硬校验阻断项 (linux/amd64 实际内容, m25 D013)
IMAGE_SINGLE_ARCH_DIGEST = (
    "sha256:286b0a54f947c412b7c290a57312ac2c4327352531e046ad4ab834c13b2ddc36"
)
# 多架构清单 digest: 只记录进 cache/cache.json, 不阻断 (m25 D016)
IMAGE_MULTI_ARCH_DIGEST = (
    "sha256:6402a87f6823c8123de6c8706ffc7b68ae75ce2c2c58aa8b3fcab59e97d1f7a4"
)
# 官方前端静态包: 取官方现成产物, 不自建前端 (NG-001)
FRONTEND_VERSION = "vis-2.9.1"
FRONTEND_ZIP_SHA256 = (
    "18b6377f9f482c3e34dd9a3ab8a716d6a7171ad68fa2d6670a516761b0be3682"
)
DEFAULT_PORT = 8090
BIND = "0.0.0.0"

# ---------------------------------------------------------------------------
# 数据键 (m25 D005, m13 D023; BR-011/BR-032)
# ---------------------------------------------------------------------------

_KEY_FORBIDDEN = re.compile(r"[^A-Za-z0-9._-]")


def clean_name(raw: str) -> str:
    """库名清洗: 空白与非法字符逐个换成 -, 连续 - 折叠, 首尾 - 去掉, 空则 repo."""
    cleaned = _KEY_FORBIDDEN.sub("-", raw)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "repo"


def data_key(target_dir) -> str:
    """数据键 = <清洗后的库名>-<realpath 的 sha256 前 8 位>.cc.json.

    不变式 (m25 D005): 同一 realpath 恒得同一键 (软链进同一目录必须同键,
    所以取 realpath 而非 abspath); 不同 realpath 键不同 (同名不同库靠哈希
    区分); 键只含 [A-Za-z0-9._-].
    """
    real = str(Path(target_dir).resolve())
    digest = hashlib.sha256(real.encode("utf-8")).hexdigest()[:8]
    return f"{clean_name(Path(real).name)}-{digest}.cc.json"


# ---------------------------------------------------------------------------
# 运行时目录 (m25 TECHNICAL.md "运行时目录")
# ---------------------------------------------------------------------------

ENV_RUNTIME_DIR = "CODEMAP_RUNTIME_DIR"
RUNTIME_SUBDIRS = ("serve-root", "cache", "logs")


def runtime_dir() -> Path:
    """运行时基目录: $CODEMAP_RUNTIME_DIR 覆盖, 默认 ~/.agents/codebase-map.

    纯解析, 无副作用 (不创建目录); 创建走 ensure_runtime_layout.
    """
    override = os.environ.get(ENV_RUNTIME_DIR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".agents" / "codebase-map"


def ensure_runtime_layout(base=None) -> Path:
    """按需创建基目录与三个子目录, 目录一律 0700; 返回基目录."""
    base = Path(base) if base is not None else runtime_dir()
    for path in (base, *(base / sub for sub in RUNTIME_SUBDIRS)):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path, 0o700)
    return base


# ---------------------------------------------------------------------------
# 排除集合与 glob -> ccsh 正则 (m25 D019, m13 D017; BR-015)
# ---------------------------------------------------------------------------

DEFAULT_EXCLUDES = (
    "node_modules",
    ".git",
    "dist",
    "build",
    "target",
    "vendor",
    ".codebase-map",
)


def collect_excludes(user_excludes) -> tuple:
    """默认排除集在前, 用户 --exclude 追加, 保序去重.

    这是排除口径的唯一来源: 分析侧 (ccsh -e 正则) 与宿主侧目录树扫描都从
    这里取同一份数据, 两处口径不得各写一套 (BR-015).
    """
    seen = set()
    out = []
    for pattern in [*DEFAULT_EXCLUDES, *user_excludes]:
        if pattern not in seen:
            seen.add(pattern)
            out.append(pattern)
    return tuple(out)


def glob_to_ccsh_regex(glob: str) -> str:
    """单个 glob -> ccsh -e 正则: 元字符逐字转义, 不把 glob 原样当正则 (m25 D019)."""
    return re.escape(glob)


def excluded_regexes(user_excludes=()) -> tuple:
    """collect_excludes 的正则形态: 逐条转义, 供分析侧与扫描侧共用同一份."""
    return tuple(glob_to_ccsh_regex(g) for g in collect_excludes(user_excludes))


# ---------------------------------------------------------------------------
# 输出编码辅助 (m25 TECHNICAL.md CLI "输出形状")
# ---------------------------------------------------------------------------


def json_line(obj) -> str:
    """单行 UTF-8 JSON (含结尾换行); --json 模式的 stdout 恰好这一行."""
    return json.dumps(obj, ensure_ascii=False) + "\n"


def success_result(command: str, **payload) -> dict:
    """成功信封: success/command 加负载字段, 供各子命令组装结果."""
    return {"success": True, "command": command, **payload}


def error_result(command: str, code: str, message: str, hint: str) -> dict:
    """错误信封: 稳定错误码 + 白话说明 + 下一步动作 (非功能要求 "可诊断")."""
    return {
        "success": False,
        "command": command,
        "error": {"code": code, "message": message, "hint": hint},
    }


def human_summary(result: dict) -> str:
    """结果 dict -> 多行人类可读摘要; 与 JSON 形态字段一致, 不另造第二份数据."""
    head = "成功" if result.get("success") else "失败"
    lines = [f"codebase-map {result.get('command', '?')}: {head}"]
    for key, value in result.items():
        if key in ("success", "command"):
            continue
        if key == "error" and isinstance(value, dict):
            lines.append(f"错误码: {value.get('code', '')}")
            lines.append(f"说明: {value.get('message', '')}")
            continue
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"
