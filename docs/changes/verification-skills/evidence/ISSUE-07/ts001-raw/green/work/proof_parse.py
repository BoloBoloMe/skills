"""证据脚本 1: 断言应用实际加载的 amountlib 版本与 parse_amount 的空串行为.

判断错时 assert 触发, 进程非零退出.
"""
import sys
from decimal import Decimal

import amountlib
from amountlib import parse_amount

print("python:", sys.version.split()[0])
print("amountlib.__file__:", amountlib.__file__)
print("amountlib.VERSION:", amountlib.VERSION)

assert amountlib.VERSION == "2.4.0", "版本不符, 测到的不是应用使用的那份代码"

# (a) 关键事实: 空串/None/纯空白都表示没有金额.
for raw in ("", None, "   ", "\t\n"):
    got = parse_amount(raw)
    print(f"parse_amount({raw!r}) -> {got!r}")
    assert got is None, f"parse_amount({raw!r}) 应为 None, 实际 {got!r}"

# 正常文本仍然解析成 Decimal, 且格式与原文本可能不同.
for raw in ("9.99", " 9.99 ", "0012.50", "1e3"):
    got = parse_amount(raw)
    print(f"parse_amount({raw!r}) -> {got!r} ; str() -> {str(got)!r}")
assert parse_amount("9.99") == Decimal("9.99")

# 非数字文本抛 ValueError, 不会返回原文.
try:
    parse_amount("1,234.50")
except ValueError as exc:
    print("parse_amount('1,234.50') -> ValueError:", exc)
else:
    raise AssertionError("非法金额没有抛 ValueError")

print("OK: 版本与空串行为断言全部通过")
