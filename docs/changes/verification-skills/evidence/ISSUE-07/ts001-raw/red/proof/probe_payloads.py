"""对比 base 与 HEAD 的 read_orders 对同一批 payload 的输出.

用法: uv run --no-project python probe_payloads.py <repo-root>
每个 payload 单独建一个内存库, 避免一行抛错遮住后面的行.
"""
import json
import sqlite3
import sys

REPO = sys.argv[1]
sys.path.insert(0, REPO)

from app.orders import read_orders  # noqa: E402

PAYLOADS = [
    (1, {"schema": "v2", "amount": "12.50"}),
    (2, {"schema": "v1", "amount_str": "9.99"}),
    (3, {"schema": "v1", "amount_str": ""}),
    (4, {"schema": "v1", "amount_str": None}),
    (5, {"schema": "v1"}),
    (6, {"schema": "v1", "amount_str": " 9.99 "}),
    (7, {"schema": "v1", "amount_str": "N/A"}),
    (8, {"schema": "v1", "amount_str": "1,234.50"}),
    (9, {"schema": "v2", "amount": None, "amount_str": "5.00"}),
    (10, {"schema": "v2", "amount": "", "amount_str": "6.00"}),
    (11, {"schema": "v2", "amount": "0"}),
    (12, {"schema": "v1", "amount_str": "0"}),
    (13, {"schema": "v1", "amount_str": "   "}),
    (14, {"schema": "v1", "amount_str": "\t\n"}),
]

print(f"repo = {REPO}")
print(f"app.orders file = {sys.modules['app.orders'].__file__}")
rows = []
for order_id, payload in PAYLOADS:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
    conn.execute("INSERT INTO orders (id, payload) VALUES (?, ?)", (order_id, json.dumps(payload)))
    try:
        result = read_orders(conn)
        outcome = {"id": order_id, "payload": payload, "result": result}
    except Exception as exc:  # noqa: BLE001 - 要记录任意异常
        outcome = {
            "id": order_id,
            "payload": payload,
            "raised": type(exc).__name__,
            "message": str(exc),
        }
    rows.append(outcome)
    print(json.dumps(outcome, ensure_ascii=False))
conn.close()
print("JSON_SUMMARY=" + json.dumps(rows, ensure_ascii=False, sort_keys=True))
