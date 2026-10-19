"""非正式一次性实验 (不进仓库): 交替重复, 计错误数, 核输出一致性.

只调 src/ 里的 build_index 与 report.export_report, 不改任何产品代码.
"""
import statistics
import sys
import time
from pathlib import Path

ROOT = Path("/tmp/orchestra-19/green2-lab")
sys.path.insert(0, str(ROOT / "src"))
from index_fast import build_index as fast  # noqa: E402
from index_lite import build_index as lite  # noqa: E402
from report import export_report  # noqa: E402


def load_rows():
    rows = []
    with open(ROOT / "data" / "rows.csv", encoding="utf-8") as h:
        for line in h:
            k, v = line.rstrip("\n").split(",")
            rows.append((k, v))
    return rows


def timeit(fn, arg):
    t = time.perf_counter()
    out = fn(arg)
    return (time.perf_counter() - t) * 1000, out


def check(rows, idx_lite, idx_fast):
    """返回 (期望条数, lite 条数, fast 条数, 键一致, 计数一致)."""
    n = len(rows)
    total_lite = sum(len(v) for v in idx_lite.values())
    total_fast = sum(idx_fast.values())
    same_keys = set(idx_lite) == set(idx_fast)
    counts_equal = same_keys and all(
        len(idx_lite[k]) == idx_fast[k] for k in idx_fast
    )
    return n, total_lite, total_fast, same_keys, counts_equal


def main():
    rows = load_rows()
    # 正确性: 两侧索引逐 key 计数是否一致, 条数是否等于输入行数
    _, a = timeit(lite, rows)
    _, b = timeit(fast, rows)
    n, tl, tf, same_keys, counts_equal = check(rows, a, b)
    print(f"正确性: 输入 {n} 行, lite 计数和 {tl}, fast 计数和 {tf}, "
          f"键一致 {same_keys}, 逐 key 计数一致 {counts_equal}")

    # 交替重复, 两侧各 7 次
    tl_ms, tf_ms, failures = [], [], 0
    for i in range(7):
        for name, fn, store in (("lite", lite, tl_ms), ("fast", fast, tf_ms)):
            try:
                ms, _out = timeit(fn, rows)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  第{i + 1}轮 {name} 抛错: {exc!r}")
                continue
            store.append(ms)
    print(f"失败数 {failures}")
    for name, xs in (("index_lite", tl_ms), ("index_fast", tf_ms)):
        if not xs:
            continue
        print(f"{name} 次数 {len(xs)} 中位数 {statistics.median(xs):.3f}ms "
              f"极差 {min(xs):.3f}..{max(xs):.3f}ms 全部 {[round(x, 2) for x in xs]}")

    # 收益上限所需占比: build_index 在 export_report 里占多少 (单次, 仅算占比)
    total_ms, out = timeit(export_report, rows)
    build_fast_ms, _ = timeit(fast, rows)
    build_lite_ms, _ = timeit(lite, rows)
    print(f"export_report 单次 {total_ms:.3f}ms, 输出 {len(out)} 字节; "
          f"其中 build_index 约 {build_fast_ms:.3f}ms (fast) / {build_lite_ms:.3f}ms (lite)")
    r_lite = build_lite_ms / total_ms
    r_fast = build_fast_ms / total_ms
    print(f"占比 r = build/总: lite 侧 {r_lite:.2f}, fast 侧 {r_fast:.2f}; "
          f"整段删掉的上限 r/(1-r): lite 侧 {r_lite / (1 - r_lite):.2f}, fast 侧 {r_fast / (1 - r_fast):.2f}")


if __name__ == "__main__":
    main()
