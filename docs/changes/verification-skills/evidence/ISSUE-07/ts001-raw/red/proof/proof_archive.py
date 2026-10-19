"""证明本地能否观察"外部归档服务是否丢弃没有 amount 的旧订单".

用法: uv run --no-project python proof_archive.py <repo-root>
分三种情况: 无 token / 有 token 但缺 orders_archive 表 / 有 token 且有表.
"""
import os
import sqlite3
import sys

REPO = sys.argv[1]
sys.path.insert(0, REPO)

from app.legacy_sync import ARCHIVE_URL, push_to_archive  # noqa: E402

print(f"repo = {REPO}")
print(f"ARCHIVE_URL = {ARCHIVE_URL}")
print(f"ARCHIVE_TOKEN in env before = {'ARCHIVE_TOKEN' in os.environ}")


def attempt(label, conn):
    try:
        result = push_to_archive(conn)
        print(f"[{label}] returned {result!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"[{label}] raised {type(exc).__name__}: {exc}")


conn = sqlite3.connect(":memory:")
attempt("无 token", conn)

os.environ["ARCHIVE_TOKEN"] = "fake-token-for-local-probe"
attempt("假 token, 无 orders_archive 表", conn)

conn.execute("CREATE TABLE orders_archive (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
conn.execute("INSERT INTO orders_archive VALUES (3, '{\"schema\":\"v1\",\"amount_str\":\"\"}')")
attempt("假 token, 有 orders_archive 表", conn)

print("注意: 上面第三次只统计本地表行数, 源码没有任何 HTTP 调用,")
print("所以它不能证明外部服务收到无 amount 的订单后会丢弃还是保留.")
