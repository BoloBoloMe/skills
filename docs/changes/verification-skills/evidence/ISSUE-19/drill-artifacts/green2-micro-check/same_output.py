"""非正式 TC: 同一产出 (key -> 计数) 下比对两条路线.
fast: 直接累加计数. old_route: 先按旧实现建值列表, 结束时取长度转计数.
"""
import random, statistics, sys, time
from pathlib import Path
ROOT = Path("/tmp/orchestra-19/green-lab"); sys.path.insert(0, str(ROOT/"src"))
from index_fast import build_index as fast
from index_lite import build_index as lite

rows=[]
with open(ROOT/"data"/"rows.csv", encoding="utf-8") as h:
    for line in h:
        k,v=line.rstrip("\n").split(","); rows.append((k,v))

def old_route(rows):
    return {k: len(v) for k, v in lite(rows).items()}

rng=random.Random(7)
t={"fast":[],"old_route":[]}
fast(rows); old_route(rows)
for _ in range(20):
    order=["fast","old_route"]; rng.shuffle(order)
    for name in order:
        fn = fast if name=="fast" else old_route
        s=time.perf_counter(); fn(rows); t[name].append((time.perf_counter()-s)*1000)
for name in ("fast","old_route"):
    v=t[name]
    print(f"{name}: n={len(v)} median={statistics.median(v):.3f}ms min={min(v):.3f} max={max(v):.3f} range={max(v)-min(v):.3f}")
mf,mo=statistics.median(t["fast"]),statistics.median(t["old_route"])
print(f"same-output gain={(mo-mf)/mo*100:.1f}%")
print("outputs equal ?", fast(rows)==old_route(rows))
