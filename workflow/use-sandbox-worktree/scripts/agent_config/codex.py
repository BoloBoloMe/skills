"""Codex: 单个 Responses provider和固定原生模型清单. 不设置审批/沙盒/信任."""
from .common import HOME, KEY_ENV, pretty, q


def render(template, catalog):
    provider = template["providers"]["codex"]
    default = template["defaults"]["codex"]["model"]
    config = (
        f"model = {q(default)}\nmodel_provider = {q(provider)}\n"
        f"model_catalog_json = {q(str(HOME / '.codex/models.json'))}\n\n"
        f"[model_providers.{q(provider)}]\nname = {q(template['name'])}\n"
        f"base_url = {q(template['base_url'])}\nenv_key = {q(KEY_ENV)}\n"
        'wire_api = "responses"\nrequires_openai_auth = false\nsupports_websockets = false\n'
    )
    # 原生清单是版本化模板数据, 包括 Codex 解析器必需的官方基础指令.
    # 不从主机读取, 不在启动时下载/猜测, 不替代公共 AGENTS.md.
    return {".codex/config.toml": config,
            ".codex/models.json": pretty({"models": catalog["codex_catalog"]["models"]})}
