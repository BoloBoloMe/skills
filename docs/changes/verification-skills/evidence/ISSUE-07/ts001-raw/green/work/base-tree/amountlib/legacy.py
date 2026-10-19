"""amountlib 2.4.0: schema v1 payload 的兼容分支."""
from .core import parse_amount

_FORMATTERS = {}


def register_legacy_formatter(field, formatter):
    """应用启动时注册 v1 payload 字段的格式化函数."""
    _FORMATTERS[field] = formatter


def resolve_amount(payload):
    """返回 payload 中的金额.

    v2 payload 直接读 amount 字段; v1 payload 没有 amount, 改查已注册的
    amount_str 格式化函数. 没有注册时返回 None.
    """
    if "amount" in payload:
        return parse_amount(payload["amount"])
    formatter = _FORMATTERS.get("amount_str")
    if formatter is None:
        return None
    return formatter(payload.get("amount_str"))
