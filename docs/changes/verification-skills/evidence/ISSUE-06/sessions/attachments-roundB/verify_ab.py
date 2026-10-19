"""核验用: 新旧两版交替测量, 不加随机扰动, 记录成功行数.

run_export.py 的 measure() 会给每次样本叠加 +/-2ms (clear) 或 +/-4ms (close)
的人工随机数, 且两条 --profile 分支跑的是同一份代码; 本脚本只测真实耗时,
并按 A/B/A/B 交替取对, 让两侧吃到同样的机器噪声.
"""

import argparse
import statistics
import sys
import time

sys.path.insert(0, "src")
from exporter import export  # noqa: E402

ROWS = [1000 + i for i in range(5)]


def run(side: str) -> tuple[float, int]:
    start = time.perf_counter()
    results = export(ROWS, side)
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, sum(1 for r in results if r["ok"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=2)
    args = parser.parse_args()

    for _ in range(args.warmup):
        run("a")
        run("b")

    a_ms: list[float] = []
    b_ms: list[float] = []
    diffs: list[float] = []
    ok_counts: dict[str, set[int]] = {"a": set(), "b": set()}
    for _ in range(args.pairs):
        ta, oka = run("a")
        tb, okb = run("b")
        a_ms.append(ta)
        b_ms.append(tb)
        diffs.append(tb - ta)
        ok_counts["a"].add(oka)
        ok_counts["b"].add(okb)

    for name, xs in (("a", a_ms), ("b", b_ms)):
        print(
            f"{name}: p50 {statistics.median(xs):.1f} ms  "
            f"min {min(xs):.1f}  max {max(xs):.1f}  "
            f"ok_rows {sorted(ok_counts[name])} / {len(ROWS)}"
        )
    print(
        f"b-a 配对差: p50 {statistics.median(diffs):+.1f} ms  "
        f"min {min(diffs):+.1f}  max {max(diffs):+.1f}  "
        f"b 更慢的配对 {sum(d > 0 for d in diffs)}/{len(diffs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
