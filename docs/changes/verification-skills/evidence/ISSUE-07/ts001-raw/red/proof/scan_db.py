"""扫描一个 orders.db, 统计 HEAD 回退逻辑下行为可能变化的行形状.

用法: uv run --no-project python scan_db.py <repo-root> <sqlite-path>
只读, 不写库.
"""
import json
import sqlite3
import sys

REPO, DB = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO)

from amountlib import parse_amount  # noqa: E402

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = conn.execute("SELECT id, payload FROM orders ORDER BY id").fetchall()
print(f"repo = {REPO}")
print(f"db   = {DB}")
print(f"rows = {len(rows)}")

non_numeric_v1 = []
fallback_gain = []
new_null_whitespace = []
for order_id, raw in rows:
    payload = json.loads(raw)
    has_amount = "amount" in payload
    amount_value = payload.get("amount")
    amount_blank = amount_value is None or (isinstance(amount_value, str) and not amount_value.strip())
    amount_str = payload.get("amount_str")
    if has_amount and amount_blank and isinstance(amount_str, str) and amount_str.strip():
        fallback_gain.append(order_id)
    if not has_amount and isinstance(amount_str, str) and amount_str.strip():
        try:
            parse_amount(amount_str)
        except ValueError:
            non_numeric_v1.append(order_id)
    if not has_amount and isinstance(amount_str, str) and amount_str != "" and not amount_str.strip():
        new_null_whitespace.append(order_id)

print(f"v1 且 amount_str 非空但 parse_amount 会抛 ValueError 的行: {non_numeric_v1}")
print(f"amount 为 null/空串但 amount_str 非空, HEAD 会新增金额的行: {fallback_gain}")
print(f"v1 且 amount_str 仅空白, base 输出空串而 HEAD 输出 null 的行: {new_null_whitespace}")
conn.close()
