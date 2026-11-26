"""模板校验/快照/精确容器绑定. 纯标准库, 不接受模板安装命令."""
from __future__ import annotations

import copy
import json
import math
import os
import re
import secrets
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from . import codex, kimi, pi
from .common import (CONTRACT, CONTRACT_LABEL, CONTAINER_LABEL, TOKEN_LABEL,
                     DIGEST_LABEL, TOOL_DIR, IMAGE_ID_RE, TemplateError, canonical,
                     digest, normalize_image_id, pretty, private_json, safe_write,
                     valid_key)

TEMPLATES = Path(__file__).resolve().parents[2] / "agent-templates"
# 测试可用环境变量覆盖模板根缺省值; 显式传 root= 的调用不受影响.
TEMPLATES_ENV = "SWT_AGENT_TEMPLATES_DIR"


def templates_root() -> Path:
    override = os.environ.get(TEMPLATES_ENV)
    return Path(override) if override else TEMPLATES


PROTOCOLS = ("openai-responses", "openai-completions")
THINKING = ("off", "minimal", "low", "medium", "high", "xhigh", "max")
PI_MODEL_KEYS = {"id", "name", "reasoning", "thinkingLevelMap", "input", "contextWindow", "maxTokens", "cost", "api", "compat"}
COMPAT_KEYS = {"supportsToolSearch", "supportsStore", "supportsDeveloperRole", "supportsReasoningEffort", "supportsUsageInStreaming", "maxTokensField", "supportsStrictMode", "thinkingFormat", "zaiToolStream", "requiresReasoningContentOnAssistantMessages"}
SNAPSHOT_KEYS = {"contract", "template", "catalog", "files", "digest", "snapshot-digest"}
CODEX_MODEL_KEYS = set("""
slug display_name description default_reasoning_level supported_reasoning_levels shell_type
visibility supported_in_api priority availability_nux support_verbosity default_verbosity
apply_patch_tool_type truncation_policy input_modalities supports_reasoning_summary_parameter
supports_reasoning_summaries base_instructions upgrade experimental_supported_tools
context_window max_context_window prefer_websockets use_responses_lite
""".split())


def fields(obj, required: set[str], optional: set[str] = frozenset()) -> None:
    if not isinstance(obj, dict) or not required <= set(obj) or set(obj) - required - optional:
        raise TemplateError("模板字段缺失/未知, 不允许安装命令或额外凭据")


def identifier(value) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,80}", value))


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        raise TemplateError("模板/快照 JSON 缺失或不可读取") from None


def validate(template, catalog) -> None:
    try:
        _validate(template, catalog)
    except TemplateError:
        raise
    except (TypeError, ValueError, KeyError, OverflowError):
        raise TemplateError("模板字段类型/值非法") from None


def _validate(template, catalog) -> None:
    fields(template, {"schema", "name", "version", "kind", "contract", "base_url", "credential", "providers", "defaults"})
    if type(template["schema"]) is not int or template["schema"] != 1 or type(template["contract"]) is not int or template["contract"] != CONTRACT or template["kind"] != "openai-gateway":
        raise TemplateError("模板协议/初始化契约不兼容")
    if not identifier(template["name"]) or not identifier(template["version"]):
        raise TemplateError("模板名称/版本非法")
    url = template["base_url"]
    if not isinstance(url, str) or any(ord(c) < 33 or ord(c) > 126 for c in url):
        raise TemplateError("网关 URL 非法")
    try:
        parts = urlsplit(url)
        _ = parts.port
    except ValueError:
        raise TemplateError("网关 URL 非法") from None
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or url.endswith("/"):
        raise TemplateError("网关 URL 须为无凭据/查询/片段的 HTTP(S) 入口, 无尾斜线")
    credential = template["credential"]
    fields(credential, {"kind", "path", "field"})
    if credential["kind"] != "json-field" or credential["field"] != "client_api_key" or not isinstance(credential["path"], str) or not Path(credential["path"]).is_absolute():
        raise TemplateError("只支持 JSON 文件中的 client_api_key 引用")
    fields(template["providers"], {"pi", "codex", "kimi_chat", "kimi_responses"})
    if not all(identifier(v) for v in template["providers"].values()) or template["providers"]["kimi_chat"] == template["providers"]["kimi_responses"]:
        raise TemplateError("provider 名称非法/两个 Kimi 协议名称重复")
    if template["providers"]["pi"] in ("openai", "anthropic") or template["providers"]["codex"] in ("openai", "ollama", "lmstudio"):
        raise TemplateError("须使用非内置 provider 名称")
    fields(catalog, {"schema", "version", "models", "codex_catalog"}, {"sources"})
    if type(catalog["schema"]) is not int or catalog["schema"] != 1 or not identifier(catalog["version"]) or not isinstance(catalog["models"], list) or not catalog["models"]:
        raise TemplateError("模型清单版本/格式非法")
    if "sources" in catalog and (not isinstance(catalog["sources"], list) or not all(isinstance(v, str) for v in catalog["sources"])):
        raise TemplateError("模型清单来源须为字符串列表")
    by_id = {}
    for model in catalog["models"]:
        fields(model, {"id", "reasoning", "input", "contextWindow", "maxTokens", "api"}, PI_MODEL_KEYS)
        mid = model["id"]
        if not isinstance(mid, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,150}", mid) or mid in by_id:
            raise TemplateError("模型 ID 非法或重复")
        if model["api"] not in PROTOCOLS or type(model["reasoning"]) is not bool:
            raise TemplateError("模型协议/推理声明非法")
        for key in ("contextWindow", "maxTokens"):
            if type(model[key]) is not int or model[key] < 1:
                raise TemplateError("模型窗口/输出限制须为正整数")
        if model["maxTokens"] > model["contextWindow"]:
            raise TemplateError("输出限制超过总窗口")
        if not isinstance(model["input"], list) or not model["input"] or set(model["input"]) - {"text", "image"}:
            raise TemplateError("模型输入类型非法")
        # cost 可选: 价格未公布的模型可省略整块; 出现时必须完整且非负有限.
        if "cost" in model:
            fields(model["cost"], {"input", "output", "cacheRead", "cacheWrite"})
            if not all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in model["cost"].values()):
                raise TemplateError("模型价格非法")
        levels = model.get("thinkingLevelMap", {})
        if not isinstance(levels, dict) or set(levels) - set(THINKING) or any(v is not None and v not in (*THINKING, "none") for v in levels.values()):
            raise TemplateError("思考等级映射非法")
        compat = model.get("compat", {})
        if not isinstance(compat, dict) or set(compat) - COMPAT_KEYS:
            raise TemplateError("未知 Pi 兼容选项")
        for key, value in compat.items():
            if key == "maxTokensField":
                ok = value in ("max_tokens", "max_completion_tokens")
            elif key == "thinkingFormat":
                ok = value in ("deepseek", "zai", "qwen", "openai")
            else:
                ok = type(value) is bool
            if not ok:
                raise TemplateError("Pi 兼容选项值非法")
        by_id[mid] = model
    fields(template["defaults"], {"pi", "codex", "kimi"})
    for agent, default in template["defaults"].items():
        fields(default, {"model", "thinking"} if agent == "pi" else {"model"})
        if default["model"] not in by_id:
            raise TemplateError("默认模型不在版本化清单中")
    default = template["defaults"]["pi"]
    if default["thinking"] not in THINKING or by_id[default["model"]].get("thinkingLevelMap", {}).get(default["thinking"], default["thinking"]) is None:
        raise TemplateError("Pi 默认思考等级不受模型支持")
    if by_id[template["defaults"]["codex"]["model"]]["api"] != "openai-responses":
        raise TemplateError("Codex 默认模型须支持 Responses")
    responses = [m for m in catalog["models"] if m["api"] == "openai-responses"]
    native = catalog["codex_catalog"]
    fields(native, {"version", "models"})
    if not identifier(native["version"]) or not isinstance(native["models"], list):
        raise TemplateError("Codex 固定清单版本/格式非法")
    native_ids = []
    for model in native["models"]:
        fields(model, CODEX_MODEL_KEYS)
        mid = model["slug"]
        if not isinstance(mid, str) or not isinstance(model["display_name"], str) or type(model["priority"]) is not int or (model["description"] is not None and not isinstance(model["description"], str)):
            raise TemplateError("Codex 模型标识/描述/排序字段非法")
        for key in ("support_verbosity", "supports_reasoning_summary_parameter", "supports_reasoning_summaries"):
            if type(model[key]) is not bool:
                raise TemplateError("Codex 能力字段须为布尔值")
        fields(model["truncation_policy"], {"mode", "limit"})
        if model["truncation_policy"]["mode"] not in ("tokens", "bytes") or type(model["truncation_policy"]["limit"]) is not int or model["truncation_policy"]["limit"] < 1:
            raise TemplateError("Codex 工具输出截断字段非法")
        native_ids.append(mid)
        if mid not in by_id or by_id[mid]["api"] != "openai-responses":
            raise TemplateError("Codex 固定清单含模板外模型/非 Responses 模型")
        if model["context_window"] != by_id[mid]["contextWindow"] or model["max_context_window"] < model["context_window"] or model["input_modalities"] != by_id[mid]["input"]:
            raise TemplateError("Codex 窗口/输入规格与共享清单不符")
        if model["prefer_websockets"] is not False or model["use_responses_lite"] is not False or model["upgrade"] is not None or model["experimental_supported_tools"]:
            raise TemplateError("Codex 固定清单不允许 WebSocket/Lite/自动升级/未验证工具")
        if not isinstance(model["base_instructions"], str) or not model["base_instructions"] or len(model["base_instructions"]) > 100000:
            raise TemplateError("Codex 原生基础指令缺失/过大")
        if model["shell_type"] not in ("shell_command", "local", "unified_exec") or model["visibility"] != "list" or model["supported_in_api"] is not True:
            raise TemplateError("Codex 固定清单客户端字段非法")
        for effort in model["supported_reasoning_levels"]:
            fields(effort, {"effort", "description"})
            if effort["effort"] not in (*THINKING, "none", "ultra"):
                raise TemplateError("Codex 思考等级非法")
    if len(native_ids) != len(set(native_ids)) or set(native_ids) != {m["id"] for m in responses}:
        raise TemplateError("Codex 固定清单与 Responses 模型集不同")


def load(name: str, root: Path | None = None) -> dict:
    root = templates_root() if root is None else root
    if not identifier(name):
        raise TemplateError("模板名称非法")
    directory = root / name
    if directory.is_symlink():
        raise TemplateError("模板目录不得是符号链接")
    template = read_json(directory / "template.json")
    catalog = read_json(directory / "models.json")
    validate(template, catalog)
    if template["name"] != name:
        raise TemplateError("模板目录名与声明不同")
    return {"template": template, "catalog": catalog}


def summary(bundle: dict) -> dict:
    template = bundle["template"]
    return {"name": template["name"], "version": template["version"],
            "digest": digest(bundle), "contract": CONTRACT,
            "models-version": bundle["catalog"]["version"]}


def choices(root: Path | None = None) -> list[dict]:
    root = templates_root() if root is None else root
    if not root.is_dir():
        raise TemplateError("模板目录缺失")
    return [summary(load(p.name, root)) for p in sorted(root.iterdir()) if p.is_dir()]


def render(bundle: dict) -> dict[str, str]:
    validate(bundle["template"], bundle["catalog"])
    result = {}
    for client in (pi, codex, kimi):
        result.update(client.render(bundle["template"], bundle["catalog"]))
    return result


def snapshot(bundle: dict) -> dict:
    value = {"contract": CONTRACT, **copy.deepcopy(bundle), "files": render(bundle), "digest": digest(bundle)}
    value["snapshot-digest"] = digest(value)
    return value


def validate_snapshot(value: dict) -> dict:
    fields(value, SNAPSHOT_KEYS)
    bundle = {"template": value["template"], "catalog": value["catalog"]}
    validate(bundle["template"], bundle["catalog"])
    core = {k: v for k, v in value.items() if k != "snapshot-digest"}
    if value["contract"] != CONTRACT or value["digest"] != digest(bundle) or value["snapshot-digest"] != digest(core) or value["files"] != render(bundle):
        raise TemplateError("固定快照摘要/生成契约不一致, 拒绝更新或重新猜配置")
    return value


def read_snapshot(path: Path, expected: str | None = None) -> dict:
    value = validate_snapshot(read_json(path))
    if expected and value["snapshot-digest"] != expected:
        raise TemplateError("固定快照已被改动")
    return value


def freeze(path: Path, bundle: dict) -> dict:
    value = snapshot(bundle)
    if path.exists():
        if read_snapshot(path) != value:
            raise TemplateError("快照已存在且内容不同, 不覆盖")
        return value
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    safe_write(path, pretty(value))
    return value


def creation(path: Path, bundle: dict, name: str, image_digest: str) -> dict:
    token = secrets.token_hex(16)
    path = path.parent / token / path.name
    value = freeze(path, bundle)
    return {**summary(bundle), "snapshot": str(path), "snapshot-digest": value["snapshot-digest"],
            "creation-token": token, "container": name,
            "image-digest": image_digest, "status": "pending"}


def credential(value: dict) -> str:
    source = value["template"]["credential"]
    key = valid_key(private_json(Path(source["path"])).get(source["field"]))
    if key in canonical(value):
        raise TemplateError("模板含客户端 Key 原文, 拒绝留档/安装")
    return key


def captured(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, text=True, capture_output=True, check=False, timeout=60, **kwargs)
    except (OSError, subprocess.TimeoutExpired):
        raise TemplateError("初始化命令不可执行或超时, 原始输出已隐藏") from None


# 容器内工具允许透传的脱敏原因: 只认固定人话, 其余一律换成通用说明.
CHECK_REASONS = frozenset({
    "pi 真实配置解析/凭据检查未通过", "codex 真实配置解析/凭据检查未通过",
    "kimi 真实配置解析/凭据检查未通过", "客户端解析/凭据检查不能执行或超时",
    "网关不可达/认证失败/模型清单非法, 不回退供应商", "网关没有模板声明的完整模型清单",
    "网关发生重定向, 不转发客户端 Key", "客户端配置/凭据权限或属主错误",
    "客户端模型配置与固定快照不同, 不自动覆盖", "目标存在 OAuth/其他认证数据, 不覆盖",
})
# 解析器 (validate_snapshot/validate) 的固定原因, 用于预检与 state 失败.
PARSER_REASONS = frozenset({
    "模板字段缺失/未知, 不允许安装命令或额外凭据", "模板字段类型/值非法",
    "模板/快照 JSON 缺失或不可读取", "模板协议/初始化契约不兼容",
    "模板名称/版本非法", "模板名称非法", "模板目录不得是符号链接",
    "模板目录名与声明不同", "模板目录缺失",
    "网关 URL 非法", "网关 URL 须为无凭据/查询/片段的 HTTP(S) 入口, 无尾斜线",
    "只支持 JSON 文件中的 client_api_key 引用",
    "provider 名称非法/两个 Kimi 协议名称重复", "须使用非内置 provider 名称",
    "模型清单版本/格式非法", "模型清单来源须为字符串列表", "模型 ID 非法或重复",
    "模型协议/推理声明非法", "模型窗口/输出限制须为正整数", "输出限制超过总窗口",
    "模型输入类型非法", "模型价格非法", "思考等级映射非法", "未知 Pi 兼容选项",
    "Pi 兼容选项值非法", "默认模型不在版本化清单中", "Pi 默认思考等级不受模型支持",
    "Codex 默认模型须支持 Responses", "Codex 固定清单版本/格式非法",
    "Codex 模型标识/描述/排序字段非法", "Codex 能力字段须为布尔值",
    "Codex 工具输出截断字段非法", "Codex 固定清单含模板外模型/非 Responses 模型",
    "Codex 窗口/输入规格与共享清单不符",
    "Codex 固定清单不允许 WebSocket/Lite/自动升级/未验证工具",
    "Codex 原生基础指令缺失/过大", "Codex 固定清单客户端字段非法",
    "Codex 思考等级非法", "Codex 固定清单与 Responses 模型集不同",
    "固定快照摘要/生成契约不一致, 拒绝更新或重新猜配置",
})
# 旧镜像没有 validate 动作; 不再用这句文案推断版本, 只用于说明工具自检失败.
LEGACY_TOOL_REASON = "初始化工具仅用于契约匹配的新容器"
PREFLIGHT_INCOMPATIBLE = (
    "镜像内模板解析器不接受本次模板快照, 该镜像不能用于本次 birth; "
    "按 image-prep 审批构建/发布含兼容解析器的新 base/display/项目镜像后, 用 --image <ref> 重跑; "
    "不手改快照, 不补假价格, 不改旧容器"
)


def stderr_reason(result: subprocess.CompletedProcess, allowed: frozenset[str]) -> str:
    """只取白名单内的固定脱敏原因; 逐行挑固定 JSON, 不透传原始输出/正文."""
    for line in (result.stderr or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        reason = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(reason, str) and reason in allowed:
            return reason
    return ""


def pin_image(image: str) -> str:
    """本地不可变引用: 已是完整镜像 ID 就原样用, 否则解析当前本地 ID (tag 会漂).

    podman 的 .Id 可能给 64 位裸 ID, 统一补 sha256: 前缀.
    """
    pinned = normalize_image_id(image)
    if pinned:
        return pinned
    result = captured(["podman", "image", "inspect", image, "--format", "{{.Id}}"])
    pinned = normalize_image_id(result.stdout.strip())
    if result.returncode != 0 or not pinned:
        raise TemplateError(f"镜像不存在或不可 inspect, 不能预检: {image}")
    return pinned


# 能力探针: 先读镜构建写入的 agent-tool-actions 标记; 老镜像没有标记时扫工具实现文件
# (镜像里 /opt/swt-agent-config/runtime.py 只是 import wrapper, 动作列表在内层包里).
# 都不符合就当无法识别 (fail closed), 不从错误文案猜版本.
PROBE_SOURCE = (
    "import pathlib,sys;"
    "root=pathlib.Path({root!r});"
    "sys.exit(2) if not root.is_dir() else None;"
    "marker=root/'agent-tool-actions';"
    "has=('validate' in marker.read_text(encoding='utf-8').split()) if marker.is_file() "
    "else any('\"validate\"' in path.read_text(encoding='utf-8', errors='ignore') "
    "for path in sorted(root.rglob('*.py')));"
    "sys.exit(0 if has else 1)"
)


def capability_probe_source(root: str = TOOL_DIR) -> str:
    return PROBE_SOURCE.format(root=root)


def tool_has_validate(pinned: str, run_tool) -> bool:
    probe = run_tool(["-c", capability_probe_source()])
    if probe.returncode == 0:
        return True
    if probe.returncode == 1:
        return False
    raise TemplateError(
        f"无法确认镜像 {pinned} 内工具是否支持只读预检, 按不兼容处理; "
        "核对镜像是否完整/可运行后重跑"
    )


def incompatible_image(pinned: str, detail: str = "") -> TemplateError:
    return TemplateError(
        PREFLIGHT_INCOMPATIBLE + f"; 目标镜像 {pinned}" + (f"; 原因: {detail}" if detail else ""))


def preflight(image: str, value: dict) -> str:
    """按选定镜像做只读模板预检: 用镜像内真实解析器校验本次快照; 返回校验用的镜像 ID.

    临时容器 --rm, --pull=never (只用宿主已有镜像, 不拉取), --http-proxy=false
    (Podman 默认会把代理变量传进容器), 无网络/无挂载/无 -e, 镜像按本地不可变 ID
    引用, 快照只经 stdin 传入; 不读主机凭据, 不写容器内客户端配置.
    旧镜像没有 validate 动作时 (先读镜像内工具源码确认) 退回同一工具的 state 只读动作.
    """
    if not isinstance(value, dict) or not isinstance(value.get("snapshot-digest"), str):
        raise TemplateError("没有本次模板快照, 不能做镜像预检")
    pinned = pin_image(image)
    base = ["podman", "run", "--rm", "--pull=never", "--network=none", "--http-proxy=false",
            "--user", "root", "-i", pinned,
            "uv", "run", "--no-project", "--offline", "python"]

    def run_tool(tail: list[str], payload: dict | None = None) -> subprocess.CompletedProcess:
        options = {"input": canonical(payload)} if payload is not None else {}
        try:
            return captured([*base, *tail], **options)
        except TemplateError as exc:
            raise TemplateError(f"镜像预检不能执行 ({exc}), 尚未创建母体/容器, 也未读主机凭据") from None

    if tool_has_validate(pinned, run_tool):
        result = run_tool([TOOL_DIR + "/runtime.py", "validate"], {"snapshot": value})
        if result.returncode == 0:
            expected = {"ok": True, "contract": CONTRACT, "snapshot-digest": value["snapshot-digest"]}
            try:
                report = json.loads(result.stdout)
            except ValueError:
                raise incompatible_image(pinned, "预检没有返回固定脱敏报告") from None
            if report != expected:
                raise incompatible_image(pinned, "预检报告结构不符, 不转发原始输出")
            return pinned
        # 新入口真实校验失败不回落 state, 避免把真实拒收误当版本兼容性.
        if stderr_reason(result, frozenset({LEGACY_TOOL_REASON})):
            raise incompatible_image(pinned, "镜像内工具自检失败, 需 root 身份且契约文件与标签一致")
        raise incompatible_image(pinned, stderr_reason(result, PARSER_REASONS))

    # 已确认是旧入口: 只用它支持的 state 只读动作校验同一份快照.
    legacy = run_tool([TOOL_DIR + "/runtime.py", "state"], {
        "snapshot": value,
        "binding": {"creation-token": secrets.token_hex(16), "container-id": secrets.token_hex(32)},
    })
    if legacy.returncode == 0:
        try:
            reported = json.loads(legacy.stdout)
        except ValueError:
            reported = None
        if reported == {"installed": False}:
            return pinned
        raise incompatible_image(pinned, "旧镜像的只读状态不是未安装, 不能完成预检")
    raise incompatible_image(pinned, stderr_reason(legacy, PARSER_REASONS))


def image_compatible(ref: str) -> None:
    result = captured(["podman", "image", "inspect", ref, "--format", '{{index .Labels "' + CONTRACT_LABEL + '"}}'])
    if result.returncode != 0 or result.stdout.strip() != str(CONTRACT):
        raise TemplateError(f"镜像缺少 agent-template 契约 {CONTRACT}, 须经审批构建新 base/display/项目镜像; 不复用旧镜像")


def guard(detail: dict, runtime: dict, record: dict) -> str:
    meta = record.get("agent-template")
    if not isinstance(meta, dict) or meta != runtime.get("agent-template"):
        raise TemplateError("容器没有本次模板创建记录, 拒绝操作旧容器")
    cid = record.get("podman-id")
    if not isinstance(cid, str) or not re.fullmatch(r"[0-9a-f]{64}", cid) or cid != detail.get("Id"):
        raise TemplateError("容器 ID 与创建记录不同, 拒绝误操作同名容器")
    config = detail.get("Config")
    labels = config.get("Labels") if isinstance(config, dict) else None
    if not isinstance(labels, dict) or not re.fullmatch(r"[0-9a-f]{32}", str(meta.get("creation-token", ""))) or not re.fullmatch(r"[0-9a-f]{64}", str(meta.get("snapshot-digest", ""))):
        raise TemplateError("创建令牌/摘要/标签格式非法")
    expected = {CONTAINER_LABEL: str(CONTRACT), TOKEN_LABEL: meta.get("creation-token"),
                DIGEST_LABEL: meta.get("snapshot-digest"), "sandbox-worktree.repo": runtime.get("repo"),
                "sandbox-worktree.mother": record.get("branch"), "sandbox-worktree.name": record.get("name")}
    if any(not v or labels.get(k) != v for k, v in expected.items()) or detail.get("Name", "").lstrip("/") != record.get("name") or meta.get("container") != record.get("name") or meta.get("image-digest") != record.get("image-digest"):
        raise TemplateError("容器标签/创建令牌/镜像记录不匹配")
    return cid


def target(runtime: dict, name: str) -> tuple[dict, dict, str]:
    if not isinstance(runtime, dict) or not isinstance(runtime.get("containers"), list):
        raise TemplateError("创建记录格式非法")
    record = next((r for r in runtime["containers"] if isinstance(r, dict) and r.get("name") == name), None)
    if not isinstance(record, dict) or record.get("retired"):
        raise TemplateError("目标不在本次有效创建记录中")
    result = captured(["podman", "inspect", name])
    try:
        detail = json.loads(result.stdout)[0] if result.returncode == 0 else {}
    except (ValueError, IndexError, TypeError):
        raise TemplateError("目标容器 inspect 不可解析") from None
    return record, detail, guard(detail, runtime, record)


def operate(runtime: dict, name: str, *, install: bool) -> dict:
    record, detail, cid = target(runtime, name)
    meta = record["agent-template"]
    if detail.get("State", {}).get("Status") != "running":
        raise TemplateError("目标新容器未运行, 初始化工具不负责启动")
    value = read_snapshot(Path(meta["snapshot"]), meta["snapshot-digest"])
    if install and meta["status"] == "verified":
        install = False  # 已验收的 birth 重入只检查, 不重装/不重新取主机密钥.
    payload = {"snapshot": value, "binding": {"creation-token": meta["creation-token"], "container-id": cid}}
    command = ["podman", "exec", "-i", "--user", "root", cid,
               "uv", "run", "--no-project", "--offline", "python", TOOL_DIR + "/runtime.py"]
    if install:
        state = captured([*command, "state"], input=canonical(payload))
        if state.returncode != 0:
            # 先看返回码: 失败时 stdout 为空, 原因在 stderr 的固定 JSON 里.
            detail = stderr_reason(state, PARSER_REASONS | CHECK_REASONS)
            raise TemplateError("新容器初始化状态不符, 不取主机凭据" + (": " + detail if detail else ""))
        try:
            installed = json.loads(state.stdout)
        except ValueError:
            raise TemplateError("新容器初始化状态无法解析, 不取主机凭据") from None
        if installed not in ({"installed": True}, {"installed": False}):
            raise TemplateError("新容器初始化状态不符, 不取主机凭据")
        if not installed["installed"]:
            payload["client_api_key"] = credential(value)
    action = "install" if install else "check"
    result = captured([*command, action], input=canonical(payload))
    # 子进程可能把 stdin/Key 反射到 stdout/stderr. 不透传, 只接收固定成功结构.
    if result.returncode != 0:
        # 只转述固定原因, 不透传子进程反射的 Key/路径/正文.
        reason = stderr_reason(result, CHECK_REASONS)
        detail = ": " + reason if reason else ""
        raise TemplateError("新容器模板安装/验收失败" + detail + "; 未交付, 同一 birth 重入或 terminate 该新容器")
    try:
        report = json.loads(result.stdout)
    except ValueError:
        raise TemplateError("模板验收没有返回固定脱敏报告") from None
    expected = {"ok": True, "contract": CONTRACT, "snapshot-digest": value["snapshot-digest"],
                "checks": ["permissions", "config", "credentials", "clients", "gateway-models"]}
    if report != expected:
        raise TemplateError("模板验收报告结构不符, 不转发原始输出")
    return report
