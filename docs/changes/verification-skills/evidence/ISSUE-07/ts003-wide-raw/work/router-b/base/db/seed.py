"""建本地 SQLite 库并写入真实存在的订单行."""
import json
import pathlib
import sqlite3

DB = pathlib.Path(__file__).resolve().parent.parent / "var" / "orders.db"

ROWS = [
    (1, {"schema": "v2", "amount": "12.50"}),
    (2, {"schema": "v1", "amount_str": "9.99"}),
    (3, {"schema": "v1", "amount_str": ""}),
]


def main():
    DB.parent.mkdir(exist_ok=True)
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    conn.executescript(pathlib.Path(__file__).resolve().parent.joinpath("schema.sql").read_text())
    conn.executemany(
        "INSERT INTO orders (id, payload) VALUES (?, ?)",
        [(i, json.dumps(p)) for i, p in ROWS],
    )
    conn.commit()
    conn.close()
    print(f"seeded {DB} with {len(ROWS)} rows")


if __name__ == "__main__":
    main()
