"""Pi: 单个自定义 provider, 保留每个模型的协议/兼容参数."""
from .common import KEY_ENV, pretty

MODEL_SETTINGS = ("defaultProvider", "defaultModel", "defaultThinkingLevel", "enabledModels",
                  "modelThinkingLevels", "thinkingBudgets", "httpProxy")


def render(template, catalog):
    provider = template["providers"]["pi"]
    return {
        ".pi/agent/models.json": pretty({"providers": {provider: {
            "baseUrl": template["base_url"], "api": "openai-responses",
            "apiKey": "$" + KEY_ENV, "authHeader": True,
            "models": catalog["models"],
        }}}),
        ".pi/agent/settings.overlay.json": pretty({
            "defaultProvider": provider, "defaultModel": template["defaults"]["pi"]["model"],
            "defaultThinkingLevel": template["defaults"]["pi"]["thinking"],
            "enabledModels": [provider + "/*"],
        }),
    }


def merge_settings(settings, overlay):
    # 只动模型设置, 不放宽 trust/工具权限, 公共 hooks/键位设置不变.
    return {**{k: v for k, v in settings.items() if k not in MODEL_SETTINGS}, **overlay}
