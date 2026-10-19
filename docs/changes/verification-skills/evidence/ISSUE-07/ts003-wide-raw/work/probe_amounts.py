"""证明 F4: 本次提交只改键名与外层, 金额值与解析路径不变.

用两份干净副本 (HEAD 与 HEAD~1) 各自 seed + dump 后的真实导出做断言.
"""
import json
import pathlib
import sys

WORK = pathlib.Path("/tmp/orchestra-07/out/ts003-wide-work")

# 1) 断言测到的是仓库自带 amountlib 2.4.0, 不是别处装的
sys.path.insert(0, str(WORK / "head"))
import amountlib  # noqa: E402

assert amountlib.VERSION == "2.4.0", amountlib.VERSION
assert pathlib.Path(amountlib.__file__).resolve().is_relative_to((WORK / "head").resolve()), amountlib.__file__
print(f"amountlib {amountlib.VERSION} @ {amountlib.__file__}")

base = json.loads((WORK / "base" / "var" / "orders.export.json").read_text())
head = json.loads((WORK / "head" / "var" / "orders.export.json").read_text())

# 2) 基线是顶层数组, HEAD 是对象包 rows
assert isinstance(base, list), type(base)
assert isinstance(head, dict) and head.get("schema") == "orders-export/2", head.keys()
print("envelope: base=array, head=object schema=orders-export/2")

# 3) 金额字段改名
assert all(set(r) == {"id", "amount"} for r in base), base
assert all(set(r) == {"id", "amount_value"} for r in head["rows"]), head["rows"]
print("keys: base amount -> head amount_value")

# 4) 3 行真实 seed 的金额值完全一致, 顺序与 id 一致
base_vals = [(r["id"], r["amount"]) for r in base]
head_vals = [(r["id"], r["amount_value"]) for r in head["rows"]]
assert base_vals == head_vals == [(1, "12.50"), (2, "9.99"), (3, None)], (base_vals, head_vals)
print(f"values identical: {head_vals}")

# 5) 本次提交未触碰 amountlib 与 orders.py 的解析分支: 由 git diff 另行断言
print("PASS: 金额值不变 (12.50, 9.99, null)")
