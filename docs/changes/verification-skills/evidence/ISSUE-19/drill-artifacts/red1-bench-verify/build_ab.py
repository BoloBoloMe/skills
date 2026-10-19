"""非正式 TC: 只对 build_index 交替各 5 次, 排除 JSON 输出体积干扰."""
import statistics, sys
from pathlib import Path
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
import time
import index_lite, index_fast

REPO = Path("/tmp/orchestra-19/red-lab")
rows = []
with open(REPO / "data" / "rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))

res = {"lite": [], "fast": []}
fails = {"lite": 0, "fast": 0}
for _ in range(5):
    for name, fn in (("lite", index_lite.build_index), ("fast", index_fast.build_index)):
        t0 = time.perf_counter()
        try:
            fn(rows)
        except Exception as exc:
            fails[name] += 1
            print("FAIL", name, exc)
            continue
        res[name].append((time.perf_counter() - t0) * 1000)

for name in ("lite", "fast"):
    v = res[name]
    print(f"{name}: n={len(v)} median={statistics.median(v):.2f}ms range={min(v):.2f}-{max(v):.2f}ms fails={fails[name]}")
print("差值中位数", round(statistics.median(res['lite']) - statistics.median(res['fast']), 2), "ms")
print("相对", round((statistics.median(res['lite'])-statistics.median(res['fast']))/statistics.median(res['lite'])*100, 1), "%")
