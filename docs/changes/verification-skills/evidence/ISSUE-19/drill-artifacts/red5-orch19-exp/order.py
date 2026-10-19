"""非正式一次性实验: 复现 bench/micro.py 的顺序偏差 (先测者承担预热)."""
import sys, time
from pathlib import Path
REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
from index_fast import build_index as fast
from index_lite import build_index as lite
rows = [tuple(l.rstrip("\n").split(",")) for l in open(REPO/"data"/"rows.csv", encoding="utf-8")]

def t(fn):
    s = time.perf_counter(); fn(rows); return (time.perf_counter()-s)*1000

print("== 1) 预热后按 micro.py 顺序 (lite 先) 各 5 轮")
t(lite); t(fast)
L=[];F=[]
for _ in range(5):
    L.append(t(lite)); F.append(t(fast))
print("lite", [f"{x:.3f}" for x in L]); print("fast", [f"{x:.3f}" for x in F])

print("== 2) 冷启动, 让 fast 先测 (与 micro.py 相反的顺序) 各 1 轮")
print(f"fast {t(fast):.3f}ms  lite {t(lite):.3f}ms")
