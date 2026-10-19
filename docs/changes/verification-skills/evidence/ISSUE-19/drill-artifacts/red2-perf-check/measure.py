"""非正式一次性核查 (benchmark-checklist): 交替测 build_index 与 export_report 端到端.
不改仓库内任何文件. 输出: 每次耗时, 失败数, 工作量, 输出校验."""
import json, statistics, sys, time, traceback
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
from report import export_report
from index_lite import build_index as lite
from index_fast import build_index as fast

rows = []
with open("/tmp/orchestra-19/red-lab/data/rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",", 1)
        rows.append((k, v))

failures = {"lite_build": 0, "fast_build": 0, "lite_e2e": 0, "fast_e2e": 0}
N = 6
res = {"lite_build": [], "fast_build": [], "lite_e2e": [], "fast_e2e": []}
work = {"lite_build": 0, "fast_build": 0}

def timed(fn, tag):
    t = time.perf_counter()
    try:
        out = fn()
    except Exception:
        failures[tag] += 1
        traceback.print_exc()
        return None
    res[tag].append((time.perf_counter() - t) * 1000)
    return out

# 预热一次 (不计入)
lite(rows); fast(rows)

for i in range(N):
    il = timed(lambda: lite(rows), "lite_build")
    if il is not None:
        work["lite_build"] += len(il)
    i_f = timed(lambda: fast(rows), "fast_build")
    if i_f is not None:
        work["fast_build"] += len(i_f)
    ol = timed(lambda: export_report(rows, build=lite), "lite_e2e")
    of = timed(lambda: export_report(rows, build=fast), "fast_e2e")

# 正确性: fast 的计数应等于 lite 每个 key 的值个数, 且键集相同
ic_l, ic_f = lite(rows), fast(rows)
ok_counts = set(ic_l) == set(ic_f) and all(ic_f[k] == len(ic_l[k]) for k in ic_l)
# 端到端输出: 两版 payload 的实际差异
pl, pf = export_report(rows, build=lite), export_report(rows, build=fast)
jl, jf = json.loads(pl), json.loads(pf)
ok_same_report = pl == pf

def stats(xs):
    return f"n={len(xs)} median={statistics.median(xs):.3f}ms min={min(xs):.3f}ms max={max(xs):.3f}ms spread={max(xs)-min(xs):.3f}ms all={[round(x,3) for x in xs]}"

for k in ("lite_build", "fast_build", "lite_e2e", "fast_e2e"):
    print(f"{k}: {stats(res[k])} failures={failures[k]}")
print(f"work: lite index keys={work['lite_build']//N if N else 0} fast index keys={work['fast_build']//N if N else 0} rows={len(rows)}")
print(f"counts consistent with lite list lengths: {ok_counts}; lite/fast report identical: {ok_same_report}")
print(f"payload bytes lite={len(pl)} fast={len(pf)}; entries lite={len(jl)} fast={len(jf)}; fast report entries value type={type(jf[0]['count']).__name__}")
lb, fb = statistics.median(res['lite_build']), statistics.median(res['fast_build'])
le, fe = statistics.median(res['lite_e2e']), statistics.median(res['fast_e2e'])
print(f"build median gain: {(lb-fb)/lb*100:.1f}%")
print(f"e2e median gain: {(le-fe)/le*100:.1f}%")
r = lb / le
print(f"build share of lite e2e: {r*100:.1f}%  upper bound if removed entirely: {r/(1-r)*100:.1f}%")
