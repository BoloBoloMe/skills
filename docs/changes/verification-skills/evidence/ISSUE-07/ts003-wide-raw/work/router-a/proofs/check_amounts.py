"""在独立进程里调用每个快照的真实金额代码. 不改产品文件."""
import json
import pathlib
import sqlite3
import sys
from decimal import Decimal

assert sys.implementation.name == "cpython"
assert sys.version_info >= (3, 11)
root = pathlib.Path(sys.argv[1]).resolve()
assert root.parent == pathlib.Path(__file__).resolve().parents[1]
assert root.name in {"repo", "base"}
sys.path.insert(0, str(root))

import amountlib
import amountlib.legacy as legacy
from app import orders
from db import seed

assert amountlib.VERSION == "2.4.0"
assert pathlib.Path(amountlib.__file__).resolve() == root / "amountlib/__init__.py"
assert pathlib.Path(orders.__file__).resolve() == root / "app/orders.py"
assert legacy._FORMATTERS == {}, "应用导入后不应存在 v1 注册函数"
assert seed.ROWS == [
    (1, {"schema": "v2", "amount": "12.50"}),
    (2, {"schema": "v1", "amount_str": "9.99"}),
    (3, {"schema": "v1", "amount_str": ""}),
]

def text(value):
    return None if value is None else str(value)

resolve_calls = []
fallback_calls = []
real_resolve = orders.resolve_amount
real_parse = orders.parse_amount

def traced_resolve(payload):
    value = real_resolve(payload)
    resolve_calls.append({"payload": payload, "result": text(value)})
    return value

def traced_parse(raw):
    value = real_parse(raw)
    fallback_calls.append({"input": raw, "result": text(value)})
    return value

# 只在本证明进程内包一层记录, 两个函数仍调用真正实现.
orders.resolve_amount = traced_resolve
orders.parse_amount = traced_parse
with sqlite3.connect(f"file:{root / 'var/orders.db'}?mode=ro", uri=True) as conn:
    db_rows = [(i, json.loads(payload)) for i, payload in conn.execute(
        "SELECT id, payload FROM orders ORDER BY id"
    )]
    assert db_rows == seed.ROWS
    actual = orders.read_orders(conn)
orders.resolve_amount = real_resolve
orders.parse_amount = real_parse

key = "amount_value" if root.name == "repo" else "amount"
expected = [{"id": 1, key: "12.50"}, {"id": 2, key: "9.99"}, {"id": 3, key: None}]
assert actual == expected, (actual, expected)
assert resolve_calls == [
    {"payload": seed.ROWS[0][1], "result": "12.50"},
    {"payload": seed.ROWS[1][1], "result": None},
    {"payload": seed.ROWS[2][1], "result": None},
]
assert fallback_calls == [
    {"input": "9.99", "result": "9.99"},
    {"input": "", "result": None},
]
assert legacy._FORMATTERS == {}

# 分支按 amount 键是否存在, 不按 payload.schema 字符串分派.
assert real_resolve({"schema": "v1", "amount": "8.40"}) == Decimal("8.40")
assert real_resolve({"schema": "v2", "amount_str": "7.10"}) is None
assert real_resolve({"amount": None}) is None
for raw, expected_value in [(None, None), ("", None), ("   ", None), (" 9.99 ", Decimal("9.99"))]:
    assert real_parse(raw) == expected_value
try:
    real_parse("not-an-amount")
except ValueError as error:
    invalid_error = str(error)
else:
    raise AssertionError("非法金额应抛 ValueError")

print(json.dumps({
    "snapshot": root.name,
    "python": sys.version,
    "sqlite": sqlite3.sqlite_version,
    "amountlib_version": amountlib.VERSION,
    "amountlib_path": amountlib.__file__,
    "read_orders": actual,
    "resolve_calls": resolve_calls,
    "fallback_calls": fallback_calls,
    "formatters": legacy._FORMATTERS,
    "schema_key_dispatch": False,
    "invalid_error": invalid_error,
    "assertions": "PASS",
}, ensure_ascii=False, indent=2))
