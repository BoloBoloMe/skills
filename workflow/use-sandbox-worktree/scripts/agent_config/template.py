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
                     DIGEST_LABEL, TOOL_DIR, TemplateError, canonical, digest,
                     pretty, private_json, safe_write, valid_key)

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
        fields(model, {"id", "reasoning", "input", "contextWindow", "maxTokens", "cost", "api"}, PI_MODEL_KEYS)
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
        try:
            installed = json.loads(state.stdout)
        except ValueError:
            raise TemplateError("新容器初始化状态无法解析, 不取主机凭据") from None
        if state.returncode != 0 or installed not in ({"installed": True}, {"installed": False}):
            raise TemplateError("新容器初始化状态不符, 不取主机凭据")
        if not installed["installed"]:
            payload["client_api_key"] = credential(value)
    action = "install" if install else "check"
    result = captured([*command, action], input=canonical(payload))
    # 子进程可能把 stdin/Key 反射到 stdout/stderr. 不透传, 只接收固定成功结构.
    if result.returncode != 0:
        # 只转述固定原因, 不透传子进程反射的 Key/路径/正文.
        reasons = {"pi 真实配置解析/凭据检查未通过", "codex 真实配置解析/凭据检查未通过",
                   "kimi 真实配置解析/凭据检查未通过", "客户端解析/凭据检查不能执行或超时",
                   "网关不可达/认证失败/模型清单非法, 不回退供应商", "网关没有模板声明的完整模型清单",
                   "网关发生重定向, 不转发客户端 Key", "客户端配置/凭据权限或属主错误",
                   "客户端模型配置与固定快照不同, 不自动覆盖", "目标存在 OAuth/其他认证数据, 不覆盖"}
        try:
            reason = json.loads(result.stderr).get("error")
        except (ValueError, AttributeError):
            reason = None
        detail = ": " + reason if isinstance(reason, str) and reason in reasons else ""
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
