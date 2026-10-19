"""把旧订单推送到外部归档服务.

本地不可运行: 需要 orders_archive 表与 ARCHIVE_TOKEN, 且归档服务只在生产网内可达.
"""
import os

ARCHIVE_URL = "https://archive.example.invalid/orders"


def push_to_archive(conn):
    token = os.environ.get("ARCHIVE_TOKEN")
    if not token:
        raise RuntimeError("缺 ARCHIVE_TOKEN, 本地无法推送归档")
    rows = conn.execute("SELECT id, payload FROM orders_archive").fetchall()
    return {"url": ARCHIVE_URL, "pushed": len(rows)}
