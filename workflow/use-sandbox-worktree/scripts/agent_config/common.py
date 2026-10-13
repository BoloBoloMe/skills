"""共享契约. 不访问主机配置, 不执行模板字符串."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path

CONTRACT = 2
CONTRACT_LABEL = "run.sandbox-worktree.agent-template-contract"
CONTAINER_LABEL = "sandbox-worktree.agent-template-contract"
TOKEN_LABEL = "sandbox-worktree.creation-token"
DIGEST_LABEL = "sandbox-worktree.agent-template-digest"
TOOL_DIR = "/opt/swt-agent-config"
HOME = Path("/home/bolo")
KEY_ENV = "SWT_AGENT_CLIENT_KEY"
KEY_PATH = ".config/swt-agent/client-key.json"
READY_PATH = ".config/swt-agent/ready.json"
SNAPSHOT_PATH = ".config/swt-agent/snapshot.json"

# 点名模型凭据/模型路由/配置路径, 不用 *_KEY 泛匹配误删业务变量.
MODEL_ENV = frozenset("""
SWT_AGENT_CLIENT_KEY CLIPROXYAPI_KEY CHANG_ZHI_AI_WORK
ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_OAUTH_TOKEN ANTHROPIC_BASE_URL
ANTHROPIC_FEDERATION_RULE_ID ANTHROPIC_ORGANIZATION_ID ANTHROPIC_IDENTITY_TOKEN_FILE
OPENAI_API_KEY OPENAI_BASE_URL OPENAI_ORG_ID OPENAI_PROJECT_ID CODEX_API_KEY CODEX_HOME
DEEPSEEK_API_KEY NVIDIA_API_KEY GEMINI_API_KEY GOOGLE_API_KEY MISTRAL_API_KEY
GROQ_API_KEY CEREBRAS_API_KEY XAI_API_KEY OPENROUTER_API_KEY AI_GATEWAY_API_KEY
ZAI_API_KEY ZAI_CODING_CN_API_KEY OPENCODE_API_KEY RADIUS_API_KEY TYPESAFE_API_KEY
HF_TOKEN FIREWORKS_API_KEY TOGETHER_API_KEY BASETEN_API_KEY KIMI_API_KEY KIMI_BASE_URL
KIMI_CODE_HOME KIMI_CONFIG_FILE META_API_KEY MINIMAX_API_KEY MINIMAX_CN_API_KEY
MOONSHOT_API_KEY QWEN_TOKEN_PLAN_API_KEY QWEN_TOKEN_PLAN_CN_API_KEY XIAOMI_API_KEY
XIAOMI_TOKEN_PLAN_CN_API_KEY XIAOMI_TOKEN_PLAN_AMS_API_KEY XIAOMI_TOKEN_PLAN_SGP_API_KEY
AZURE_OPENAI_API_KEY AZURE_OPENAI_BASE_URL AZURE_OPENAI_RESOURCE_NAME
AZURE_OPENAI_DEPLOYMENT_NAME_MAP AZURE_OPENAI_API_VERSION
CLOUDFLARE_API_KEY CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_GATEWAY_ID
COPILOT_GITHUB_TOKEN GH_TOKEN GITHUB_TOKEN
AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE
AWS_BEARER_TOKEN_BEDROCK AWS_WEB_IDENTITY_TOKEN_FILE AWS_SHARED_CREDENTIALS_FILE
GOOGLE_APPLICATION_CREDENTIALS GOOGLE_CLOUD_API_KEY GOOGLE_CLOUD_PROJECT
GCLOUD_PROJECT GOOGLE_CLOUD_LOCATION
PI_CODING_AGENT_DIR PI_PROVIDER PI_MODEL PI_THINKING PI_OFFLINE
""".split())
MODEL_ENV_PREFIXES = ("KIMI_MODEL_", "KIMI_WEB_SEARCH_", "KIMI_WEB_FETCH_",
                      "AWS_CONTAINER_CREDENTIALS_", "ANTHROPIC_SERVICE_ACCOUNT_",
                      "ANTHROPIC_WORKSPACE_", "GOOGLE_GEMINI_", "GOOGLE_VERTEX_")
# 这些名字也常用于业务, 不代替用户决定丢弃. 必须在创建前报告冲突.
SHARED_ENV = frozenset("""
GH_TOKEN GITHUB_TOKEN AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
AWS_PROFILE AWS_WEB_IDENTITY_TOKEN_FILE AWS_SHARED_CREDENTIALS_FILE
GOOGLE_APPLICATION_CREDENTIALS GOOGLE_CLOUD_API_KEY GOOGLE_CLOUD_PROJECT
GCLOUD_PROJECT GOOGLE_CLOUD_LOCATION HF_TOKEN
""".split())


class TemplateError(Exception):
    """只允许脱敏的人话, 不携带原始子进程/网关应答或凭据值."""


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def pretty(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def q(value: str) -> str:
    # JSON 字符串也是所用 ASCII 字符范围内的 TOML basic string.
    return json.dumps(value, ensure_ascii=True)


def filtered_env(env: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    if any(not isinstance(k, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) or not isinstance(v, str) or "\n" in v or "\r" in v or "\0" in v for k, v in env.items()):
        raise TemplateError("继承环境含非法名称/多行值, 须用户处理, 不写入 SSH environment")
    shared = sorted(k for k in env if k.upper() in SHARED_ENV or k.upper().startswith("AWS_CONTAINER_CREDENTIALS_"))
    if shared:
        raise TemplateError("模型/业务共用环境变量需用户决定, 不自动丢弃或继承: " + ", ".join(shared))
    removed = sorted(k for k in env if k.upper() in MODEL_ENV or
                     k.upper().startswith(MODEL_ENV_PREFIXES))
    return {k: v for k, v in env.items() if k not in removed}, removed


def client_env(env: dict[str, str], key: str, *, home: Path = HOME) -> dict[str, str]:
    result, _ = filtered_env(env)
    # 客户端直连模板入口; 业务 shell 的代理配置不作为模型路由来源.
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        result.pop(name, None)
    result.update({"HOME": str(home), KEY_ENV: key,
                   "PI_CODING_AGENT_DIR": str(home / ".pi/agent"),
                   "CODEX_HOME": str(home / ".codex"),
                   "KIMI_CODE_HOME": str(home / ".kimi-code"), "PI_OFFLINE": "1"})
    return result


def valid_key(value) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[!-~]{16,4096}", value):
        raise TemplateError("客户端 Key 缺失或格式非法")
    return value


def private_json(path: Path, *, uid: int | None = None) -> dict:
    try:
        # O_NOFOLLOW + fstat 防符号链接和检查/读取之间的替换.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            st = os.fstat(stream.fileno())
            if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600 or st.st_uid != (os.getuid() if uid is None else uid):
                raise TemplateError("凭据文件须为当前用户所有的普通文件, 权限 600")
            value = json.loads(stream.read(65537))
    except (OSError, ValueError):
        raise TemplateError("凭据文件缺失/不可读/JSON 非法") from None
    if not isinstance(value, dict):
        raise TemplateError("凭据文件须为 JSON 对象")
    return value


def safe_write(path: Path, text: str, mode: int = 0o600, owner: tuple[int, int] | None = None) -> None:
    # 所有临时文件从创建起就是 600, 不先写后 chmod.
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise TemplateError("拒绝写入符号链接")
    fd, temporary = tempfile.mkstemp(prefix=".swt-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), mode)
            if owner is not None:
                os.fchown(stream.fileno(), *owner)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
