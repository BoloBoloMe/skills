"""关键事实 (a) 证明: 应用实际使用的 amountlib 在空字符串下返回什么.

用法:
  uv run --no-project python proof_parse_amount.py <repo-root> [--negative-control]

退出码 0 = 断言全部成立; 1 = 至少一条断言失败 (判断错时明确失败).
--negative-control 故意把空串的期望改成"有值", 用来演示脚本真的会失败.
"""
import sys
from decimal import Decimal

REPO = sys.argv[1]
NEGATIVE = "--negative-control" in sys.argv[2:]
sys.path.insert(0, REPO)

import amountlib  # noqa: E402

failures = []


def check(label, actual, expected):
    ok = actual == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {label}: actual={actual!r} expected={expected!r}")
    if not ok:
        failures.append(label)


print(f"repo arg      = {REPO}")
print(f"amountlib file= {amountlib.__file__}")
print(f"VERSION       = {amountlib.VERSION!r}")
check("VERSION 是 2.4.0", amountlib.VERSION, "2.4.0")
check(
    "导入的是仓库内 amountlib",
    amountlib.__file__.startswith(REPO.rstrip("/") + "/"),
    True,
)

# 空串是本次变更的安全性核心: 旧格式化函数把 "" 当成没有金额,
# 新代码回退到 parse_amount(""), 所以必须确认它同样返回 None.
empty_expected = "SENTINEL" if NEGATIVE else None
check("parse_amount('') 的返回", amountlib.parse_amount(""), empty_expected)
check("parse_amount('   ') 的返回", amountlib.parse_amount("   "), None)
check("parse_amount(None) 的返回", amountlib.parse_amount(None), None)
check("parse_amount('9.99') 的返回", amountlib.parse_amount("9.99"), Decimal("9.99"))
check("parse_amount(' 9.99 ') 的返回", amountlib.parse_amount(" 9.99 "), Decimal("9.99"))
check("parse_amount('0') 不是 None", amountlib.parse_amount("0") is None, False)

try:
    amountlib.parse_amount("N/A")
    invalid = "no-raise"
except ValueError:
    invalid = "ValueError"
check("parse_amount('N/A') 的行为", invalid, "ValueError")

print()
if failures:
    print(f"RESULT: FAIL ({len(failures)} 条断言不成立): {failures}")
    sys.exit(1)
print("RESULT: PASS")
