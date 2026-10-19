"""证明: 只改了外层信封与金额键名, 金额值序列逐个相同."""
import json, pathlib

W = pathlib.Path("/tmp/orchestra-07/out/ts003-gap-work")
base = json.loads((W / "base/var/orders.export.json").read_text())
head = json.loads((W / "head/var/orders.export.json").read_text())

assert isinstance(base, list), type(base)
assert isinstance(head, dict) and head["schema"] == "orders-export/2", head.get("schema")
assert list(head) == ["schema", "rows"], list(head)

bvals = [r["amount"] for r in base]
hvals = [r["amount_value"] for r in head["rows"]]
assert bvals == hvals == ["12.50", "9.99", None], (bvals, hvals)
assert [r["id"] for r in base] == [r["id"] for r in head["rows"]] == [1, 2, 3]
print("base rows:", json.dumps(base, ensure_ascii=False))
print("head rows:", json.dumps(head["rows"], ensure_ascii=False))
print("values identical:", bvals == hvals, bvals)
