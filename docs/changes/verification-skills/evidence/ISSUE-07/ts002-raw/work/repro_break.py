"""最小复现: HEAD 的两处行为变化, 一条命令跑完.

运行:
  cd /tmp/orchestra-07/out/ts002-work
  PYTHONPATH=/tmp/orchestra-07/drill-ts002 uv run --no-project python repro_break.py

复现 1: v1 行 amount_str='abc', HEAD 让整次导出抛 ValueError, 基线版本导出 'abc'.
复现 2: v2 行 amount=null 且残留 amount_str='9.99', HEAD 凭空多出金额 9.99.
"""
import json
import sqlite3
import sys

sys.path.insert(0, "/tmp/orchestra-07/drill-ts002")
from app.orders import read_orders  # noqa: E402

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
conn.execute("INSERT INTO orders VALUES (1, ?)", (json.dumps({"schema": "v1", "amount_str": "abc"}),))
try:
    read_orders(conn)
    print("1) 没抛异常, 与预期不符")
except ValueError as exc:
    print("1) HEAD 整次导出失败:", exc)

conn2 = sqlite3.connect(":memory:")
conn2.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
conn2.execute(
    "INSERT INTO orders VALUES (1, ?)",
    (json.dumps({"schema": "v2", "amount": None, "amount_str": "9.99"}),),
)
print("2) HEAD 导出的金额:", read_orders(conn2)[0]["amount"], "(基线版本为 None)")
