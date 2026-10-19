"""订单读取: 把 orders.payload 里的金额解析出来."""
import json

from amountlib import register_legacy_formatter, resolve_amount

LEGACY_AMOUNT_KEY = "amount_str"


def format_amount_str(raw):
    """v1 payload 的 amount_str 格式化: null 与空串视为没有金额."""
    if raw is None or raw == "":
        return None
    return raw.strip()


register_legacy_formatter(LEGACY_AMOUNT_KEY, format_amount_str)


def read_orders(conn):
    rows = conn.execute("SELECT id, payload FROM orders ORDER BY id").fetchall()
    out = []
    for row in rows:
        amount = resolve_amount(json.loads(row[1]))
        out.append({"id": row[0], "amount": None if amount is None else str(amount)})
    return out
