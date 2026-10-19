"""证明 1: 应用实际加载的 amountlib 版本, 以及 parse_amount 对空串/None 的行为.

运行:
  cd /tmp/orchestra-07/out/ts002-work
  PYTHONPATH=/tmp/orchestra-07/drill-ts002 uv run --no-project python proof_amountlib_empty.py

判断错时 assert 失败, 退出码 1. 只读: 不写仓库.
"""
import pathlib
import sys
from decimal import Decimal

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts002")
# 与 scripts/dump_orders.py:7-8 相同的导入方式: 仓库根排在最前
sys.path.insert(0, str(REPO))

import amountlib
from amountlib import parse_amount, resolve_amount

print("python:", sys.version.split()[0])
print("amountlib.VERSION:", amountlib.VERSION)
print("amountlib.__file__:", amountlib.__file__)

# 环境断言: 测到的必须是仓库内 vendored 的那份代码, 否则本脚本结论无效
assert amountlib.VERSION == "2.4.0", amountlib.VERSION
assert pathlib.Path(amountlib.__file__).resolve().is_relative_to(REPO), amountlib.__file__

# 关键安全事实 (a): 空串与 None 返回 None, 不抛异常
cases = [None, "", "   ", "\t\n", "0", " 12.50 ", "9.99", "abc", "9,99"]
for raw in cases:
    try:
        got = parse_amount(raw)
        print(f"parse_amount({raw!r}) = {got!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"parse_amount({raw!r}) raises {type(exc).__name__}: {exc}")

assert parse_amount(None) is None
assert parse_amount("") is None
assert parse_amount("   ") is None
assert parse_amount("\t\n") is None
assert parse_amount("9.99") == Decimal("9.99")

try:
    parse_amount("abc")
except ValueError as exc:
    print("parse_amount('abc') ValueError ok:", exc)
else:
    raise AssertionError("parse_amount('abc') 没有抛 ValueError, 与非数字文本预期不符")

# v1 路径: 没有任何 formatter 注册时 resolve_amount 返回 None
print("resolve_amount({'amount_str': '9.99'}) =", resolve_amount({"amount_str": "9.99"}))
assert resolve_amount({"amount_str": "9.99"}) is None

print("OK: 关键安全事实 (a) 成立")
