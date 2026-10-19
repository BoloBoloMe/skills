"""非正式一次性实验: 交替 9 轮, 两种计时范围各测一遍. GC 保持默认, 无手动 collect."""
import statistics, sys, time
from pathlib import Path
REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
from index_fast import build_index as fast
from index_lite import build_index as lite
rows = [tuple(l.rstrip("\n").split(",")) for l in open(REPO/"data"/"rows.csv", encoding="utf-8")]
sides = [("lite", lite), ("fast", fast)]
lite(rows); fast(rows)  # 预热各一次, 结果丢弃

def bench(keep_alive, rounds=9):
    res = {"lite": [], "fast": []}
    holder = {}
    for i in range(rounds):
        order = sides if i % 2 == 0 else sides[::-1]
        for name, fn in order:
            s = time.perf_counter()
            if keep_alive:
                holder[name] = fn(rows)
            else:
                fn(rows)
            res[name].append((time.perf_counter()-s)*1000)
    return res

def show(tag, res):
    print(tag)
    for n in ("lite", "fast"):
        xs = res[n]
        print(f"  {n} n={len(xs)} median={statistics.median(xs):.2f}ms min={min(xs):.2f} max={max(xs):.2f} range={max(xs)-min(xs):.2f}")
    a, b = statistics.median(res["lite"]), statistics.median(res["fast"])
    print(f"  中位数差 {a-b:+.2f}ms ({(a-b)/a*100:+.1f}%)")

show("A 计时区只含 build, 结果销毁在计时区外", bench(True))
show("B 计时区含 build 与结果销毁", bench(False))
show("A 复测", bench(True))
show("B 复测", bench(False))
