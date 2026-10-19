"""非正式一次性核查: 复刻 bench/micro.py 的单次测法, 但反转两侧顺序, 看首次冷启动偏差."""
import sys, time
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
from index_lite import build_index as lite
from index_fast import build_index as fast
rows=[]
with open("/tmp/orchestra-19/red-lab/data/rows.csv", encoding="utf-8") as h:
    for line in h:
        k,v=line.rstrip("\n").split(",",1); rows.append((k,v))
# 与 micro.py 同样的顺序: lite 先, fast 后, 各一次
t=time.perf_counter(); lite(rows); l1=(time.perf_counter()-t)*1000
t=time.perf_counter(); fast(rows); f1=(time.perf_counter()-t)*1000
print(f"顺序 lite->fast 单次: lite {l1:.3f}ms fast {f1:.3f}ms 快 {(l1-f1)/l1*100:.1f}%")
