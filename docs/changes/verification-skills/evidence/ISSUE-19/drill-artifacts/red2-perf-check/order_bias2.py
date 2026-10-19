"""同一进程内反转顺序: fast 先, lite 后, 各一次 (新进程, 冷启动)."""
import sys, time
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
from index_lite import build_index as lite
from index_fast import build_index as fast
rows=[]
with open("/tmp/orchestra-19/red-lab/data/rows.csv", encoding="utf-8") as h:
    for line in h:
        k,v=line.rstrip("\n").split(",",1); rows.append((k,v))
t=time.perf_counter(); fast(rows); f1=(time.perf_counter()-t)*1000
t=time.perf_counter(); lite(rows); l1=(time.perf_counter()-t)*1000
print(f"顺序 fast->lite 单次: fast {f1:.3f}ms lite {l1:.3f}ms fast 快 {(l1-f1)/l1*100:.1f}%")
