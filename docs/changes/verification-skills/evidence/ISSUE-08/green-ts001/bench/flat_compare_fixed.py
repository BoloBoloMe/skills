"""任务 5 补测: 复刻 flat_compare 的批处理与限流, 但把限流等待移到计时区外.

原脚本把 500 ms 限流 sleep 算进每个请求的计时区, 9 ms 的归一化差异被稀释成约 1.5%.
本脚本保留 BATCH=5 和 0.5 s 限流, 只对 run_job 调用计时; 新旧交替, 每侧 9 个批次样本.
同时打印把限流算回去的对比, 用来解释原脚本的 1.5%.
"""

import argparse
import random
import statistics
import sys
import time

sys.path.insert(0, "src")
from pipeline import normalize, normalize_fast, parse, render, run_job  # noqa: E402

BATCH = 5
THROTTLE_S = 0.500


def payload(seed: int, rows: int) -> dict:
    return {"rows": [{"id": seed * 100000 + i, "name": f" n{i}-{seed} "} for i in range(rows)]}


def batch(fast: bool, seed_base: int, rows: int):
    """跑 BATCH 个请求; 只对 run_job 计时, 限流 sleep 在计时区外."""
    product_ms = []
    stages_last = None
    stats_last = None
    for i in range(BATCH):
        data = payload(seed_base + i, rows)
        start = time.perf_counter()
        stats, stages = run_job(data, fast_normalize=fast, dry_run=False)
        product_ms.append((time.perf_counter() - start) * 1000)
        assert "cache" not in stages, "缓存命中, 这次不算"
        assert stats["failed"] == 0, stats
        assert stats["written"] == rows, (stats, rows)
        assert all(value > 0 for value in stages.values()), stages
        stages_last = stages
        stats_last = stats
        time.sleep(THROTTLE_S)  # 限流, 不计入产品时间
    return product_ms, stages_last, stats_last


def correctness(rows: int = 50) -> None:
    data = payload(424242, rows)
    for fast, fn in ((False, normalize), (True, normalize_fast)):
        rows_out, _ = parse(data)
        rows_out, _ = fn(rows_out)
        body, _ = render(rows_out)
        expect = [f"{row['id']},{str(row['name']).strip().upper()}" for row in data["rows"]]
        assert body.splitlines() == expect, "归一化输出内容不对"
    print(f"correctness rows {rows}: 两种归一化实现的输出均与预期逐行一致")


def perm_test(a, b, perms: int = 20000, seed: int = 12345) -> float:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=200)
    parser.add_argument("--rounds", type=int, default=9)
    args = parser.parse_args()
    correctness()

    print(
        f"===== rows {args.rows} batch {BATCH} throttle {THROTTLE_S}s rounds {args.rounds} "
        f"(限流在计时区外, 新旧交替) ====="
    )
    collected = {
        "old": {"batch": [], "each": [], "with_throttle": []},
        "new": {"batch": [], "each": [], "with_throttle": []},
    }
    for r in range(args.rounds):
        sides = [("old", False), ("new", True)]
        if r % 2 == 1:
            sides.reverse()
        for name, fast in sides:
            seed_base = args.rows * 100000 + r * 10000 + (0 if not fast else 500000)
            product_ms, stages, stats = batch(fast, seed_base, args.rows)
            batch_mean = statistics.mean(product_ms)
            collected[name]["batch"].append(batch_mean)
            collected[name]["each"].extend(product_ms)
            collected[name]["with_throttle"].append(batch_mean + THROTTLE_S * 1000)
    for name in ("old", "new"):
        item = collected[name]
        print(
            f"{name} batches {len(item['batch'])} requests {len(item['each'])} "
            f"product_batch_med {statistics.median(item['batch']):.2f} ms "
            f"product_batch_range {min(item['batch']):.2f}-{max(item['batch']):.2f} "
            f"product_each_med {statistics.median(item['each']):.2f} ms "
            f"product_each_range {min(item['each']):.2f}-{max(item['each']):.2f} "
            f"with_throttle_med {statistics.median(item['with_throttle']):.2f} ms"
        )
    old_b, new_b = collected["old"]["batch"], collected["new"]["batch"]
    old_t, new_t = collected["old"]["with_throttle"], collected["new"]["with_throttle"]
    print(
        f"product_only_delta {(statistics.median(old_b) - statistics.median(new_b)) / statistics.median(old_b) * 100:.2f}% "
        f"p(median,batch) {perm_test(old_b, new_b):.4f} | "
        f"with_throttle_delta {(statistics.median(old_t) - statistics.median(new_t)) / statistics.median(old_t) * 100:.2f}% "
        f"p(median,with_throttle) {perm_test(old_t, new_t):.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
