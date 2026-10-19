"""证据脚本 2: 对任意一棵代码树逐行跑 read_orders, 打印结果或该行触发的异常.

用法: python proof_read.py <tree>
逐行隔离, 避免一行非法金额掩盖后面的行. 版本/tree 断言失败时非零退出.
"""
import json
import sqlite3
import sys

tree = sys.argv[1]
import amountlib  # noqa: E402

print("tree:", tree)
print("amountlib.__file__:", amountlib.__file__)
print("amountlib.VERSION:", amountlib.VERSION)
assert amountlib.VERSION == "2.4.0"
assert amountlib.__file__.startswith(tree), "导入的不是指定树的 amountlib"

from app.orders import read_orders  # noqa: E402

CASES = [
    (1, {"schema": "v2", "amount": "12.50"}),                 # seed
    (2, {"schema": "v1", "amount_str": "9.99"}),              # seed
    (3, {"schema": "v1", "amount_str": ""}),                  # seed
    (4, {"schema": "v1", "amount_str": "   "}),               # 纯空白
    (5, {"schema": "v1", "amount_str": "0012.50"}),           # 前导零
    (6, {"schema": "v1", "amount_str": "1e3"}),               # 科学计数
    (7, {"schema": "v1", "amount_str": "1,234.50"}),          # 带千分位
    (8, {"schema": "v1"}),                                    # 缺字段
    (9, {"schema": "v2", "amount": None, "amount_str": "9.99"}),   # v2 显式 null
    (10, {"schema": "v2", "amount": "", "amount_str": "9.99"}),    # v2 空串
]

for i, p in CASES:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
    conn.execute("INSERT INTO orders (id, payload) VALUES (?, ?)", (i, json.dumps(p)))
    try:
        got = read_orders(conn)[0]["amount"]
        print(f"id={i} payload={json.dumps(p, ensure_ascii=False)} -> {got!r}")
    except Exception as exc:
        print(f"id={i} payload={json.dumps(p, ensure_ascii=False)} -> EXCEPTION {type(exc).__name__}: {exc}")
    finally:
        conn.close()
