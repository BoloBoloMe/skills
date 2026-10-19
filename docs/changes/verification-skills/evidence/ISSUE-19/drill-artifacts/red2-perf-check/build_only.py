"""非正式一次性核查: 只测 build_index, 预热后交替 10 轮, 每侧 10 次."""
import statistics, sys, time
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
from index_lite import build_index as lite
from index_fast import build_index as fast
rows=[]
with open("/tmp/orchestra-19/red-lab/data/rows.csv", encoding="utf-8") as h:
    for line in h:
        k,v=line.rstrip("\n").split(",",1); rows.append((k,v))
# 预热两侧各 2 次
for _ in range(2): lite(rows); fast(rows)
L=[];F=[];fail=0
for i in range(20):
    t=time.perf_counter()
    try: a=lite(rows)
    except Exception: fail+=1
    L.append((time.perf_counter()-t)*1000)
    t=time.perf_counter()
    try: b=fast(rows)
    except Exception: fail+=1
    F.append((time.perf_counter()-t)*1000)
print("lite", [round(x,3) for x in L])
print("fast", [round(x,3) for x in F])
for name,xs in (("lite",L),("fast",F)):
    print(f"{name} n={len(xs)} median={statistics.median(xs):.3f} min={min(xs):.3f} max={max(xs):.3f} spread={max(xs)-min(xs):.3f}")
print("failures",fail,"rows",len(rows),"keys",len(a),len(b))
try:
    from scipy.stats import mannwhitneyu
    print("mannwhitneyu", mannwhitneyu(L,F,alternative="two-sided"))
except Exception as e:
    print("no scipy:",e)
