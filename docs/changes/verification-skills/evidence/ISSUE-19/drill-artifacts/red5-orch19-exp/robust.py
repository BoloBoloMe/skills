"""非正式一次性实验: 交替 AB 测 build_index, 分别在 GC 开启/关闭下各 9 轮."""
import gc, statistics, sys, time
from pathlib import Path
REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
from index_fast import build_index as fast
from index_lite import build_index as lite
rows = [tuple(l.rstrip("\n").split(",")) for l in open(REPO/"data"/"rows.csv", encoding="utf-8")]

def run(mode, rounds=9):
    L, F = [], []
    for i in range(rounds):
        a, b = (lite, fast) if i % 2 == 0 else (fast, lite)
        for fn in (a, b):
            if mode == "off":
                gc.collect(); gc.disable()
            s = time.perf_counter(); fn(rows); d = (time.perf_counter() - s) * 1000
            if mode == "off":
                gc.enable()
            (L if fn is lite else F).append(d)
    return L, F

def show(tag, L, F):
    fmt = lambda xs: f"n={len(xs)} median={statistics.median(xs):.2f}ms min={min(xs):.2f} max={max(xs):.2f} range={max(xs)-min(xs):.2f}"
    print(tag); print("  lite", fmt(L)); print("  fast", fmt(F))
    print(f"  中位数差 {(statistics.median(L)-statistics.median(F)):+.2f}ms "
          f"({(statistics.median(L)-statistics.median(F))/statistics.median(L)*100:+.1f}%)")

lite(rows); fast(rows)  # 预热
show("GC 开启 (脚本默认状态) 9 轮交替", *run("on"))
show("计时区内关闭 GC 9 轮交替", *run("off"))

# 正确性: 两次构建的 key->条数 是否与原始数据统计一致, 且两侧是否一致
exp = {}
for k, _ in rows: exp[k] = exp.get(k, 0) + 1
conv = lambda idx: {k: (v if isinstance(v, int) else len(v)) for k, v in idx.items()}
print("lite 条数正确:", conv(lite(rows)) == exp, "| fast 条数正确:", conv(fast(rows)) == exp,
      "| 两侧折算结果一致:", conv(lite(rows)) == conv(fast(rows)))
print("索引值类型 lite:", type(next(iter(lite(rows).values()))).__name__,
      "fast:", type(next(iter(fast(rows).values()))).__name__)
print("数据: data/rows.csv", len(rows), "行, 37 个不同 key")
