"""非正式 TC: 每轮随机决定先后, 各 20 次, 避免固定顺序偏置."""
import random, statistics, sys, time
from pathlib import Path
ROOT = Path("/tmp/orchestra-19/green-lab"); sys.path.insert(0, str(ROOT/"src"))
from index_fast import build_index as fast
from index_lite import build_index as lite

rows=[]
with open(ROOT/"data"/"rows.csv", encoding="utf-8") as h:
    for line in h:
        k,v=line.rstrip("\n").split(","); rows.append((k,v))

rng=random.Random(20251020)
t={"fast":[],"lite":[]}
fast(rows); lite(rows)  # 预热
for _ in range(20):
    order=["fast","lite"]; rng.shuffle(order)
    for name in order:
        fn=fast if name=="fast" else lite
        s=time.perf_counter(); fn(rows); t[name].append((time.perf_counter()-s)*1000)
for name in ("fast","lite"):
    v=t[name]
    print(f"{name}: n={len(v)} median={statistics.median(v):.3f}ms min={min(v):.3f} max={max(v):.3f} range={max(v)-min(v):.3f}")
mf,ml=statistics.median(t["fast"]),statistics.median(t["lite"])
print(f"gain={(ml-mf)/ml*100:.1f}%")

# exact Mann-Whitney U two-sided via DP over rank sums
a,b=sorted(t["fast"]),sorted(t["lite"])
all_v=sorted(a+b); ranks={}
# use average ranks
def avg_ranks(vals):
    r={}; i=0
    while i<len(vals):
        j=i
        while j+1<len(vals) and vals[j+1]==vals[i]: j+=1
        r[vals[i]]=(i+j)/2+1; i=j+1
    return r
rk=avg_ranks(all_v)
Ra=sum(rk[x] for x in a); n1,n2=len(a),len(b)
U=Ra-n1*(n1+1)/2
# exact null distribution of rank sums for n1=10 out of 20
from functools import lru_cache
@lru_cache(None)
def cnt(i,k,s):
    if k==0: return 1 if s==0 else 0
    if i==0: return 0
    return cnt(i-1,k,s)+cnt(i-1,k-1,s-i)
tot=cnt(20,10,0) if False else None
# simpler: DP counting subsets of size 10 from 1..20 by sum
dp={(0,0):1}
for i in range(1,21):
    nd={}
    for (k,s),c in dp.items():
        nd[(k,s)]=nd.get((k,s),0)+c
        if k<10: nd[(k+1,s+i)]=nd.get((k+1,s+i),0)+c
    dp=nd
dist={s:c for (k,s),c in dp.items() if k==10}
T=sum(dist.values())
obs=int(Ra)
p=sum(c for s,c in dist.items() if abs(s- (10*(21)/2))>=abs(obs-10*(21)/2))/T
print(f"U={U:.1f} rank_sum={Ra:.1f} exact two-sided p={p:.4f}")
