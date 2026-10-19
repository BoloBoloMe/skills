"""任务 3 探针: 真实入口 run_job 的新旧交替端到端测量, 覆盖数据规模与并发.

- 每轮两侧各跑一批, 批大小 = 并发数; 偶数轮 old 先, 奇数轮 new 先, 抵消顺序漂移.
- 每个样本独立 payload, 断言 cache miss, written == rows, failed == 0, 各阶段耗时 > 0.
- 报每侧 n / 中位数 / 极差 / 阶段中位数 / 归一化占比与上限 / 置换检验 p.
- 计时区只包 run_job 调用 (不含测试端构造 payload, 与原 e2e_path 不同); 另报只含产品阶段的 stage_sum.
"""

import argparse
import concurrent.futures
import random
import statistics
import sys
import time

sys.path.insert(0, "src")
import pipeline  # noqa: E402
from pipeline import normalize, normalize_fast, parse, render, run_job  # noqa: E402


def payload(seed: int, rows: int) -> dict:
    return {"rows": [{"id": seed * 100000 + i, "name": f" n{i}-{seed} "} for i in range(rows)]}


def one(seed: int, rows: int, fast: bool):
    data = payload(seed, rows)  # 测试端造数据, 不计入产品路径
    start = time.perf_counter()
    stats, stages = run_job(data, fast_normalize=fast, dry_run=False)
    run_ms = (time.perf_counter() - start) * 1000
    return run_ms, stages, stats


def run_batch(fast: bool, seeds: list[int], rows: int, concurrency: int):
    if concurrency == 1:
        return [one(seed, rows, fast) for seed in seeds]
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(one, seed, rows, fast) for seed in seeds]
        return [future.result() for future in futures]


def correctness(rows: int = 50) -> None:
    data = payload(777777, rows)
    for fast, fn in ((False, normalize), (True, normalize_fast)):
        rows_out, _ = parse(data)
        rows_out, _ = fn(rows_out)
        body, _ = render(rows_out)
        expect = [f"{row['id']},{str(row['name']).strip().upper()}" for row in data["rows"]]
        assert body.splitlines() == expect, "归一化输出内容不对"
    print(f"correctness rows {rows}: 两种归一化实现的输出均与预期逐行一致")


def perm_test(a, b, perms: int = 10000, seed: int = 12345) -> float:
    obs = abs(statistics.median(a) - statistics.median(b))
    pooled = list(a) + list(b)
    rng = random.Random(seed)
    count = 0
    for _ in range(perms):
        rng.shuffle(pooled)
        got = abs(statistics.median(pooled[: len(a)]) - statistics.median(pooled[len(a) :]))
        if got >= obs - 1e-12:
            count += 1
    return (count + 1) / (perms + 1)


def summarize(samples):
    totals = [item[0] for item in samples]
    stage_sums = [sum(item[1].values()) for item in samples]
    keys = sorted({key for item in samples for key in item[1]})
    stage_med = {key: statistics.median([item[1].get(key, 0.0) for item in samples]) for key in keys}
    r = [item[1]["normalize"] / sum(item[1].values()) for item in samples]
    med_r = statistics.median(r)
    return {
        "run": totals,
        "stage_sum": stage_sums,
        "stage_med": stage_med,
        "r_med": med_r,
        "upper": med_r / (1 - med_r),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, nargs="+", default=[200, 5000, 60000])
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 4])
    parser.add_argument("--rounds", type=int, default=9)
    args = parser.parse_args()
    correctness()

    for rows in args.rows:
        for concurrency in args.concurrency:
            # 不同配置的 seed 可能重合; 清空产品缓存, 确保本配置每个样本都真做工作
            pipeline._CACHE.clear()
            print(
                f"===== rows {rows} concurrency {concurrency} rounds {args.rounds} "
                f"(每轮每侧 {concurrency} 个请求, 双数轮 old 先, 单数轮 new 先) ====="
            )
            collected = {"old": [], "new": []}
            wall = {"old": 0.0, "new": 0.0}
            for r in range(args.rounds):
                sides = [("old", False), ("new", True)]
                if r % 2 == 1:
                    sides.reverse()
                for name, fast in sides:
                    seeds = [
                        rows * 100000 + r * 1000 + (0 if not fast else 500000) + i
                        for i in range(concurrency)
                    ]
                    start = time.perf_counter()
                    batch = run_batch(fast, seeds, rows, concurrency)
                    wall[name] += time.perf_counter() - start
                    for run_ms, stages, stats in batch:
                        assert "cache" not in stages, "缓存命中, 这次不算"
                        assert stats["failed"] == 0, stats
                        assert stats["written"] == rows, (stats, rows)
                        assert all(value > 0 for value in stages.values()), stages
                        collected[name].append((run_ms, stages, stats))
            info = {}
            for name in ("old", "new"):
                item = summarize(collected[name])
                info[name] = item
                stage_text = " ".join(
                    f"{key}={value:.2f}" for key, value in sorted(item["stage_med"].items())
                )
                n = len(item["run"])
                print(
                    f"{name} n {n} run_med {statistics.median(item['run']):.2f} ms "
                    f"run_range {min(item['run']):.2f}-{max(item['run']):.2f} "
                    f"stage_sum_med {statistics.median(item['stage_sum']):.2f} ms "
                    f"stage_sum_range {min(item['stage_sum']):.2f}-{max(item['stage_sum']):.2f} "
                    f"r_med {item['r_med'] * 100:.2f}% upper {item['upper'] * 100:.2f}% "
                    f"jobs_per_sec {n / wall[name]:.2f}"
                )
                print(f"  stage_med {stage_text}")
            old_t, new_t = info["old"]["run"], info["new"]["run"]
            old_s, new_s = info["old"]["stage_sum"], info["new"]["stage_sum"]
            print(
                f"delta_run {(statistics.median(old_t) - statistics.median(new_t)) / statistics.median(old_t) * 100:.2f}% "
                f"p_run {perm_test(old_t, new_t):.4f} | "
                f"delta_stage_sum {(statistics.median(old_s) - statistics.median(new_s)) / statistics.median(old_s) * 100:.2f}% "
                f"p_stage_sum {perm_test(old_s, new_s):.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
