"""非正式一次性实验: 与 bench/micro.py 相同跑法, 但把 fast 放在第一次, 看顺序效应."""
import sys, time
from pathlib import Path
ROOT = Path("/tmp/orchestra-19/green2-lab")
sys.path.insert(0, str(ROOT / "src"))
from index_fast import build_index as fast
from index_lite import build_index as lite

rows = []
with open(ROOT / "data" / "rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))

def once(fn):
    t = time.perf_counter(); out = fn(rows); return (time.perf_counter() - t) * 1000, out

f_ms, f_out = once(fast)
l_ms, l_out = once(lite)
print(f"顺序 fast, lite: fast {f_ms:.3f}ms lite {l_ms:.3f}ms -> fast 相对 lite {(l_ms-f_ms)/l_ms*100:+.1f}%")
# 再来一轮 (都在热态)
f2, _ = once(fast); l2, _ = once(lite)
print(f"热态第二轮: fast {f2:.3f}ms lite {l2:.3f}ms -> fast 相对 lite {(l2-f2)/l2*100:+.1f}%")
print("计数和一致:", sum(v for v in f_out.values()) == sum(len(v) for v in l_out.values()) == len(rows))
