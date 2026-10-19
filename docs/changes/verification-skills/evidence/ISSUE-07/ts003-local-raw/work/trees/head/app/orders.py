"""订单读取: 把 orders.payload 里的金额解析出来."""
import json

from amountlib import parse_amount, resolve_amount


def read_orders(conn):
    rows = conn.execute("SELECT id, payload FROM orders ORDER BY id").fetchall()
    out = []
    for row in rows:
        payload = json.loads(row[1])
        amount = resolve_amount(payload)
        if amount is None:
            amount = parse_amount(payload.get("amount_str", ""))
        out.append({"id": row[0], "amount": None if amount is None else str(amount)})
    return out
