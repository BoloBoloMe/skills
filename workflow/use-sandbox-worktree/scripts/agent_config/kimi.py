"""Kimi Code: 两个 provider 仅区分协议, 都走同一个入口."""
from .common import KEY_ENV, q


def provider_for(template, model):
    key = "kimi_responses" if model["api"] == "openai-responses" else "kimi_chat"
    return template["providers"][key]


def render(template, catalog):
    default = next(m for m in catalog["models"] if m["id"] == template["defaults"]["kimi"]["model"])
    lines = ["default_model = " + q(provider_for(template, default) + "/" + default["id"])]
    for name, kind in (("kimi_chat", "openai"), ("kimi_responses", "openai_responses")):
        lines += ["", "[providers." + q(template["providers"][name]) + "]",
                  "type = " + q(kind), "base_url = " + q(template["base_url"]),
                  "api_key_env = " + q(KEY_ENV)]
    for model in catalog["models"]:
        provider = provider_for(template, model)
        # max_output_size 目前仅 anthropic 使用, 此处不伪造 OpenAI 输出限制支持.
        capabilities = ["tool_use"]
        if model["reasoning"]:
            capabilities.append("thinking")
        if "image" in model["input"]:
            capabilities.append("image_in")
        lines += ["", "[models." + q(provider + "/" + model["id"]) + "]",
                  "provider = " + q(provider), "model = " + q(model["id"]),
                  f"max_context_size = {model['contextWindow']}",
                  "capabilities = [" + ", ".join(q(v) for v in capabilities) + "]"]
    return {".kimi-code/config.toml": "\n".join(lines) + "\n"}
