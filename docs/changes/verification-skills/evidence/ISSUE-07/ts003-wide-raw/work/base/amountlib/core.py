"""amountlib 2.4.0: 金额文本解析."""
from decimal import Decimal, InvalidOperation

VERSION = "2.4.0"


def parse_amount(raw):
    """把金额文本解析成 Decimal.

    空字符串和 None 表示没有金额, 返回 None; 其它非法文本抛 ValueError.
    """
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(f"无法解析金额: {raw!r}")
