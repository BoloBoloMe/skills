"""非正式一次性核查: 函数级 build_index, 预热后交替 30 轮; 可选关闭 GC 对照."""
import gc, statistics, sys, time
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
from index_lite import build_index as lite
from index_fast import build_index as fast
rows=[]
with open("/tmp/orchestra-19/red-lab/data/rows.csv", encoding="utf-8") as h:
    for line in h:
        k,v=line.rstrip("\n").split(",",1); rows.append((k,v))
if "--nogc" in sys.argv: gc.disable()
for _ in range(2): lite(rows); fast(rows)
L=[];F=[];fail=0
for i in range(30):
    t=time.perf_counter()
    try: a=lite(rows)
    except Exception: fail+=1
    L.append((time.perf_counter()-t)*1000)
    t=time.perf_counter()
    try: b=fast(rows)
    except Exception: fail+=1
    F.append((time.perf_counter()-t)*1000)
ml,mf=statistics.median(L),statistics.median(F)
print(f"{'nogc' if gc.isenabled() is False else 'gc-on'} lite p50={ml:.3f} range={min(L):.3f}-{max(L):.3f} | fast p50={mf:.3f} range={min(F):.3f}-{max(F):.3f} | diff={ml-mf:.3f}ms gain={(ml-mf)/ml*100:.1f}% fails={fail} rows={len(rows)} keys={len(a)}/{len(b)}")
