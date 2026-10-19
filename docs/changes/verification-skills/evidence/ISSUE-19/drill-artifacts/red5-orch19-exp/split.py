"""非正式一次性实验: 把 build 与结果销毁分开计时, 交替 9 轮."""
import gc, statistics, sys, time
from pathlib import Path
REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
from index_fast import build_index as fast
from index_lite import build_index as lite
rows = [tuple(l.rstrip("\n").split(",")) for l in open(REPO/"data"/"rows.csv", encoding="utf-8")]

build = {"lite": [], "fast": []}
drop = {"lite": [], "fast": []}
for i in range(9):
    order = [("lite", lite), ("fast", fast)] if i % 2 == 0 else [("fast", fast), ("lite", lite)]
    for name, fn in order:
        gc.collect(); gc.disable()
        s = time.perf_counter(); out = fn(rows); build[name].append((time.perf_counter()-s)*1000)
        s = time.perf_counter(); del out; drop[name].append((time.perf_counter()-s)*1000)
        gc.enable()

f = lambda xs: f"median={statistics.median(xs):.2f}ms min={min(xs):.2f} max={max(xs):.2f} range={max(xs)-min(xs):.2f}"
for name in ("lite", "fast"):
    print(f"{name} build  n=9 {f(build[name])}")
    print(f"{name} 销毁   n=9 {f(drop[name])}")
lb, fb = statistics.median(build["lite"]), statistics.median(build["fast"])
ld, fd = statistics.median(drop["lite"]), statistics.median(drop["fast"])
print(f"只算 build: fast 比 lite 快 {lb-fb:+.2f}ms ({(lb-fb)/lb*100:+.1f}%)")
print(f"build+销毁: fast 比 lite 快 {(lb+ld)-(fb+fd):+.2f}ms ({((lb+ld)-(fb+fd))/(lb+ld)*100:+.1f}%)")
