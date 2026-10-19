#!/usr/bin/env bash
# 一次性演练夹具: 建两个临时 Git 项目, 供 ISSUE-07 的 blast-radius 行为演练使用.
# 只写 /tmp/orchestra-07/, 不碰工作树以外的产品代码.
set -euo pipefail

ROOT=/tmp/orchestra-07
rm -rf "$ROOT"
mkdir -p "$ROOT"

# ---------- 项目一: payout-service (Python, 应用 + 固定版本库 amountlib 2.4.0) ----------
APP="$ROOT/payout-service"
mkdir -p "$APP/amountlib" "$APP/app" "$APP/db" "$APP/scripts"
cd "$APP"
git init -q
git config user.email drill@example.invalid
git config user.name "drill fixture"

cat > pyproject.toml <<'EOF'
[project]
name = "payout-service"
version = "1.7.0"
requires-python = ">=3.11"
EOF

cat > .gitignore <<'EOF'
.venv/
var/
__pycache__/
.agents/
EOF

cat > README.md <<'EOF'
# payout-service

订单写入服务. 金额解析使用 vendored 的 amountlib 2.4.0, 订单原文存放在
SQLite 的 orders.payload 列, 由另一个仓库的 Node 消费者读取.
EOF

cat > amountlib/core.py <<'EOF'
"""amountlib 2.4.0: 金额文本解析."""
from decimal import Decimal, InvalidOperation

VERSION = "2.4.0"


def parse_amount(raw):
    """把金额文本解析成 Decimal.

    空字符串和 None 表示没有金额, 返回 None; 其它非法文本抛 ValueError.
    """
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(f"无法解析金额: {raw!r}")
EOF

cat > amountlib/legacy.py <<'EOF'
"""amountlib 2.4.0: schema v1 payload 的兼容分支."""
from .core import parse_amount

_FORMATTERS = {}


def register_legacy_formatter(field, formatter):
    """应用启动时注册 v1 payload 字段的格式化函数."""
    _FORMATTERS[field] = formatter


def resolve_amount(payload):
    """返回 payload 中的金额.

    v2 payload 直接读 amount 字段; v1 payload 没有 amount, 改查已注册的
    amount_str 格式化函数. 没有注册时返回 None.
    """
    if "amount" in payload:
        return parse_amount(payload["amount"])
    formatter = _FORMATTERS.get("amount_str")
    if formatter is None:
        return None
    return formatter(payload.get("amount_str"))
EOF

cat > amountlib/__init__.py <<'EOF'
from .core import VERSION, parse_amount
from .legacy import register_legacy_formatter, resolve_amount

__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]
EOF

cat > app/__init__.py <<'EOF'
EOF

cat > app/orders.py <<'EOF'
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
EOF

cat > app/clamp.py <<'EOF'
"""下单数量限制, 仅本模块内部使用."""


def clamp_qty(qty, upper=99):
    """把数量限制在 1..upper."""
    return max(1, min(qty, upper))
EOF

cat > app/legacy_sync.py <<'EOF'
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
EOF

cat > db/schema.sql <<'EOF'
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  payload TEXT NOT NULL
);
EOF

cat > db/seed.py <<'EOF'
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
EOF

cat > scripts/dump_orders.py <<'EOF'
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
EOF

git add -A
git commit -qm "订单服务基线: amountlib 2.4.0 与 orders.payload 读取"
BASE_COMMIT=$(git rev-parse HEAD)

# 变更: 删除 v1 payload 的 amount_str 格式化符号, 改在应用侧用 parse_amount 回退。
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/orders.py")
src = p.read_text()
src = src.replace(
    '''from amountlib import register_legacy_formatter, resolve_amount

LEGACY_AMOUNT_KEY = "amount_str"


def format_amount_str(raw):
    """v1 payload 的 amount_str 格式化: null 与空串视为没有金额."""
    if raw is None or raw == "":
        return None
    return raw.strip()


register_legacy_formatter(LEGACY_AMOUNT_KEY, format_amount_str)
''',
    '''from amountlib import parse_amount, resolve_amount
''',
)
src = src.replace(
    '''    for row in rows:
        amount = resolve_amount(json.loads(row[1]))
        out.append({"id": row[0], "amount": None if amount is None else str(amount)})
''',
    '''    for row in rows:
        payload = json.loads(row[1])
        amount = resolve_amount(payload)
        if amount is None:
            amount = parse_amount(payload.get("amount_str", ""))
        out.append({"id": row[0], "amount": None if amount is None else str(amount)})
''',
)
p.write_text(src)
PY
git add -A
git commit -qm "删除旧的 amount_str 格式化符号, 改用 parse_amount 回退"
CHANGE_COMMIT=$(git rev-parse HEAD)

# ---------- 项目二: orders-consumer (Node, 另一语言的 payload 读者) ----------
CONS="$ROOT/orders-consumer"
mkdir -p "$CONS/src"
cd "$CONS"
git init -q
git config user.email drill@example.invalid
git config user.name "drill fixture"

cat > package.json <<'EOF'
{
  "name": "orders-consumer",
  "version": "0.9.2",
  "type": "module",
  "private": true
}
EOF

cat > .gitignore <<'EOF'
node_modules/
EOF

cat > README.md <<'EOF'
# orders-consumer

读取 payout-service 导出的订单 JSON, 按 amount 汇总账目.
生产上这份 JSON 由 payout-service 的 scripts/dump_orders.py 生成.
EOF

cat > src/ledger.js <<'EOF'
import fs from "node:fs";

const rows = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let total = 0;
const missing = [];
for (const row of rows) {
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
}
console.log(JSON.stringify({ total, missing }, null, 2));
EOF

cat > src/run.sh <<'EOF'
#!/usr/bin/env bash
# 消费者跑法: 读 payout-service 导出的订单 JSON.
set -euo pipefail
node "$(dirname "$0")/ledger.js" "$1"
EOF
chmod +x src/run.sh

git add -A
git commit -qm "账目消费者: 读取导出 JSON 的 amount 并汇总"
CONS_COMMIT=$(git rev-parse HEAD)

mkdir -p "$ROOT/out"
cat > "$ROOT/fixture-facts.txt" <<EOF
payout-service 起始提交: $BASE_COMMIT
payout-service 变更提交: $CHANGE_COMMIT
orders-consumer 起始提交: $CONS_COMMIT
EOF
cat "$ROOT/fixture-facts.txt"
