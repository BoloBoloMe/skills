"""非正式一次性实验: 只计 build 本身 (结果留在计时区外销毁), 交替 15 轮."""
import gc, statistics, sys, time
from pathlib import Path
REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
from index_fast import build_index as fast
from index_lite import build_index as lite
rows = [tuple(l.rstrip("\n").split(",")) for l in open(REPO/"data"/"rows.csv", encoding="utf-8")]
res = {"lite": [], "fast": []}
keep = {}
gc.disable()
for i in range(15):
    for name, fn in ([("lite", lite), ("fast", fast)] if i % 2 == 0 else [("fast", fast), ("lite", lite)]):
        s = time.perf_counter(); keep[name] = fn(rows); res[name].append((time.perf_counter()-s)*1000)
gc.enable()
f = lambda xs: f"n={len(xs)} median={statistics.median(xs):.2f}ms min={min(xs):.2f} max={max(xs):.2f} range={max(xs)-min(xs):.2f}"
for n in ("lite", "fast"): print(n, "build", f(res[n]))
print(f"中位数差 {statistics.median(res['lite'])-statistics.median(res['fast']):+.2f}ms")
