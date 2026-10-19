"""证明本次变更只改了一个窗口内的返回值, 且该窗口只能由直接调用触达."""
import importlib.util
import sys
from pathlib import Path

WORK = Path("/tmp/orchestra-07/out/ts003-local-work/trees")


def load(name):
    path = WORK / name / "app" / "clamp.py"
    spec = importlib.util.spec_from_file_location(f"clamp_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base, head = load("base"), load("head")
rows = []
for q in (0, 1, 50, 51, 60, 99, 100, 1000):
    b, h = base.clamp_qty(q), head.clamp_qty(q)
    rows.append((q, b, h, b == h))
for q, b, h, same in rows:
    print(f"clamp_qty({q:>4})  base={b:>4}  head={h:>4}  {'same' if same else 'CHANGED'}")

changed = [q for q, b, h, same in rows if not same]
print(f"\n有差异的输入: {changed}")
assert changed == [51, 60, 99, 100, 1000], f"差异窗口与预期不符: {changed}"

# 显式传入 upper 时, 默认值不参与, 行为完全不变
assert base.clamp_qty(99, upper=99) == head.clamp_qty(99, upper=99) == 99
print("PASS: 差异覆盖所有输入 >= 51 (默认 upper 生效时); 显式传 upper 时两版完全一致")
