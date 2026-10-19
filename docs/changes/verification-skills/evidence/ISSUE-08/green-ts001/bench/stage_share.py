"""阶段占比探针: 走真实 run_job, 每次新数据, 打印各阶段中位数与归一化占比.

用途: 算 "删掉归一化整段" 的收益上限 r/(1-r).
不改产品源码; 只读取 run_job 自己返回的 stages.
"""

import argparse
import statistics
import sys
import time

sys.path.insert(0, "src")
from pipeline import run_job  # noqa: E402


def payload(seed: int, rows: int) -> dict:
    return {"rows": [{"id": seed * 100000 + i, "name": f" n{i}-{seed} "} for i in range(rows)]}


def one(seed: int, rows: int, fast: bool):
    data = payload(seed, rows)  # 测试端造数据, 不计入产品路径
    start = time.perf_counter()
    stats, stages = run_job(data, fast_normalize=fast)
    run_ms = (time.perf_counter() - start) * 1000
    return run_ms, stages, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, nargs="+", default=[200, 5000, 60000])
    parser.add_argument("--repeat", type=int, default=9)
    args = parser.parse_args()

    for rows in args.rows:
        for fast in (False, True):
            version = "new(fast)" if fast else "old(slow)"
            totals, normals, stage_sums, r_stage, r_total = [], [], [], [], []
            for i in range(args.repeat):
                # 每侧每轮独立 seed, 保证缓存必然 miss
                seed = rows * 1000 + i + (500000 if fast else 0)
                run_ms, stages, stats = one(seed, rows, fast)
                assert "cache" not in stages, "缓存命中, 这次不算"
                assert stats["failed"] == 0, stats
                assert stats["written"] == rows, (stats, rows)
                stage_sum = sum(stages.values())
                totals.append(run_ms)
                normals.append(stages["normalize"])
                stage_sums.append(stage_sum)
                r_stage.append(stages["normalize"] / stage_sum)
                r_total.append(stages["normalize"] / run_ms)
            med_r = statistics.median(r_stage)
            med_r_total = statistics.median(r_total)
            print(
                f"rows {rows} version {version} n {args.repeat} "
                f"run_med {statistics.median(totals):.2f} ms "
                f"run_range {min(totals):.2f}-{max(totals):.2f} "
                f"stage_sum_med {statistics.median(stage_sums):.2f} "
                f"normalize_med {statistics.median(normals):.2f} "
                f"normalize_range {min(normals):.2f}-{max(normals):.2f} "
                f"r_stage_med {med_r * 100:.2f}% "
                f"r_stage_range {min(r_stage) * 100:.2f}-{max(r_stage) * 100:.2f}% "
                f"r_run_med {med_r_total * 100:.2f}% "
                f"r_run_range {min(r_total) * 100:.2f}-{max(r_total) * 100:.2f}% "
                f"upper_bound_run {med_r_total / (1 - med_r_total) * 100:.2f}% "
                f"upper_bound_stage {med_r / (1 - med_r) * 100:.2f}%"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
