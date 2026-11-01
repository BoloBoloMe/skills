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
import subprocess
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
# 已确认局域网地址与候选探测 (m25 D011/D017, m14 D011; BR-019/BR-020)
# ---------------------------------------------------------------------------

# 隧道/虚拟接口前缀: 这些接口上的全局地址局域网够不着, 不得作局域网入口交付
# (与 swt.py 同一份前缀口径, m14 M14 发现 4)
TUNNEL_INTERFACE_PREFIXES = (
    "tun", "tap", "wg", "ppp", "utun", "ts", "tailscale",
    "docker", "veth", "br-", "virbr", "zt", "podman",
)

# address_source 取值: 标明本次交付地址取自哪个来源 (m25 D017)
ADDRESS_SOURCE_RECORD = "confirmed_record"  # 取自 swt 已确认地址记录文件
ADDRESS_SOURCE_ARGUMENT = "explicit_argument"  # 取自本次 --address 实参

def _default_records_root() -> Path:
    """swt records_root 默认值: ~/.agents/sandbox-worktree (随运行时 HOME 解析,
    测试用临时 HOME 隔离, 不新增配置源, m14 D011)."""
    return Path.home() / ".agents" / "sandbox-worktree"


def confirmed_lan_address_path(records_root=None) -> Path:
    """swt 已确认局域网地址文件路径 (只读); 默认 records_root 按运行时 HOME 解析."""
    root = Path(records_root) if records_root is not None else _default_records_root()
    return root / "lan-address"


def read_confirmed_lan_address(records_root=None) -> str | None:
    """读已确认局域网地址; 无文件或内容为空返回 None (无值, 不猜测, m14 D011)."""
    path = confirmed_lan_address_path(records_root)
    try:
        if not path.is_file():
            return None
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def candidate_lan_addresses() -> tuple:
    """枚举非隧道网卡的全局 IPv4 字面量作候选地址 (只候选, 不自动交付, m25 D011).

    口径与 swt.py 同源: `ip -o -4 addr show scope global`, 过滤隧道/虚拟接口
    前缀, 保留枚举序并去重; 只取点分 IPv4, 天然不含回环/IPv6/主机名.
    """
    try:
        proc = subprocess.run(
            ["ip", "-o", "-4", "addr", "show", "scope", "global"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        output = proc.stdout
    except (OSError, subprocess.SubprocessError):
        return ()
    candidates = []
    for line in output.splitlines():
        match = re.match(r"\d+: (\S+)\s+inet (\d+\.\d+\.\d+\.\d+)/", line)
        if not match:
            continue
        iface, addr = match.group(1), match.group(2)
        if iface.startswith(TUNNEL_INTERFACE_PREFIXES):
            continue
        if addr not in candidates:
            candidates.append(addr)
    return tuple(candidates)


def resolve_delivery_address(explicit_address=None, records_root=None) -> dict:
    """交付地址解析 (m25 D011/D017, m14 D011): 单一入口, 只读不落盘.

    顺序: --address 实参 (本次显式传入的确认值) -> 已确认地址记录文件有值就用
    -> 否则枚举非隧道全局 IPv4 作 candidates 并给
    address_missing.code = no_confirmed_address.
    解析成功: {"url_host": <addr>, "address_source": confirmed_record|explicit_argument}
    解析失败: {"address_missing": {code, message}, "candidates": [...]}
    明确不采 SSH_CONNECTION, 主机名, localhost, 服务自报地址 (m25 D011);
    --address 只属于本次调用, 由调用方保证不写 state.json/配置文件/记录文件.
    """
    explicit = (explicit_address or "").strip()
    if explicit:
        return {"url_host": explicit, "address_source": ADDRESS_SOURCE_ARGUMENT}
    confirmed = read_confirmed_lan_address(records_root)
    if confirmed:
        return {"url_host": confirmed, "address_source": ADDRESS_SOURCE_RECORD}
    return {
        "address_missing": {
            "code": "no_confirmed_address",
            "message": (
                "缺已确认的局域网地址: 请用户确认一个候选地址, "
                "然后用 serve --address <已确认地址> 重新交付; "
                "不用回环地址, 主机名或文件路径顶替 (BR-019/BR-020)."
            ),
        },
        "candidates": list(candidate_lan_addresses()),
    }


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
    """结果 dict -> 多行人类可读摘要; 与 JSON 形态字段一致, 不另造第二份数据.

    地址缺口 (m25 D017, AC-008): serve 成功但缺已确认地址时, 交付被阻断而
    服务已起, 首行改写 BLOCKED, 其余字段照常铺开, 不另造第二份数据.
    """
    head = "成功" if result.get("success") else "失败"
    if result.get("success") and "address_missing" in result and "url" not in result:
        lines = ["BLOCKED: 缺已确认局域网地址"]
    else:
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
