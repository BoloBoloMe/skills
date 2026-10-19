"""非正式一次性实验: 每个进程只冷跑一次 build_index, 侧别由命令行决定."""
import sys, time
from pathlib import Path
ROOT = Path("/tmp/orchestra-19/green2-lab")
sys.path.insert(0, str(ROOT / "src"))
side = sys.argv[1]
if side == "lite":
    from index_lite import build_index as build
else:
    from index_fast import build_index as build
rows = []
with open(ROOT / "data" / "rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))
t = time.perf_counter(); out = build(rows); ms = (time.perf_counter() - t) * 1000
ok = (sum(out.values()) if side == "fast" else sum(len(v) for v in out.values())) == len(rows)
print(f"{side} {ms:.3f} {ok}")
