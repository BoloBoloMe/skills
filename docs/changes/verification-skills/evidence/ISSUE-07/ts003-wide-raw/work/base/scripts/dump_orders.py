"""把订单导出成另一个仓库的 Node 消费者读取的 JSON."""
import json
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.orders import read_orders  # noqa: E402

OUT = ROOT / "var" / "orders.export.json"


def main():
    conn = sqlite3.connect(ROOT / "var" / "orders.db")
    rows = read_orders(conn)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(json.dumps(rows, ensure_ascii=False))


if __name__ == "__main__":
    main()
