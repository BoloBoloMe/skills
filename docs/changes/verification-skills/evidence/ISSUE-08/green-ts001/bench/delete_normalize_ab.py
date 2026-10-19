"""任务 1 探针: 删除整段归一化的端到端对照.

产品源码冻结, 不能真的删 normalize 调用. 本脚本在 bench 内按 run_job 的同一顺序
复刻路径 (cache key / cache 查 / parse / [normalize] / render / write / 回填 cache),
用真实 src 函数取数, 并同时跑真实 run_job 作为基准校准复刻件.
复刻件只用于评估 "若删除归一化" 的耗时; 是否允许改变输出语义由产品决定.
"""

import argparse
import random
import statistics
import sys
import time

sys.path.insert(0, "src")
import pipeline  # noqa: E402
from pipeline import (  # noqa: E402
    _CACHE,
    _key,
    normalize,
    normalize_fast,
    parse,
    render,
    run_job,
    write,
)


def payload(seed: int, rows: int) -> dict:
    return {"rows": [{"id": seed * 100000 + i, "name": f" n{i}-{seed} "} for i in range(rows)]}


def timed_payload(seed: int, rows: int) -> dict:
    # 测试端造数据, 不计入产品路径
    return payload(seed, rows)


def replica(data: dict, fast: bool, delete: bool):
    """按 run_job 的顺序复刻; delete=True 时整段跳过归一化."""
    key = _key(data, fast, delete)
    stages = {}
    hit = _CACHE.get(key)
    if hit is not None:  # 正常不该发生: 每个样本 seed 唯一
        start = time.perf_counter()
        time.sleep(0.002)
        stages["cache"] = (time.perf_counter() - start) * 1000
        return hit, stages, True
    rows, elapsed = parse(data)
    stages["parse"] = elapsed * 1000
    if not delete:
        if fast:
            rows, elapsed = normalize_fast(rows)
        else:
            rows, elapsed = normalize(rows)
        stages["normalize"] = elapsed * 1000
    body, elapsed = render(rows)
    stages["render"] = elapsed * 1000
    stats, elapsed = write(body)
    stages["write"] = elapsed * 1000
    _CACHE[key] = stats
    return stats, stages, False


def one(arm: str, seed: int, rows: int):
    data = timed_payload(seed, rows)
    start = time.perf_counter()
    if arm == "real_old":
        stats, stages = run_job(data, fast_normalize=False, dry_run=False)
        hit = "cache" in stages
    elif arm == "rep_old":
        stats, stages, hit = replica(data, fast=False, delete=False)
    elif arm == "rep_del_old":
        stats, stages, hit = replica(data, fast=False, delete=True)
    elif arm == "rep_fast":
        stats, stages, hit = replica(data, fast=True, delete=False)
    elif arm == "rep_del_fast":
        stats, stages, hit = replica(data, fast=True, delete=True)
    else:
        raise ValueError(arm)
    run_ms = (time.perf_counter() - start) * 1000
    return run_ms, stages, stats, hit


def correctness(rows: int = 50) -> None:
    """在计时区外核对两种输出的内容: 归一化后的名字 vs 原样名字."""
    data = payload(999999, rows)
    raw = [str(row["name"]) for row in data["rows"]]

    def body_for(delete: bool, fast: bool) -> list[str]:
        rows_out, _ = parse(data)
        if not delete:
            rows_out, _ = (normalize_fast if fast else normalize)(rows_out)
        body, _ = render(rows_out)
        return body.splitlines()

    for fast in (False, True):
        with_norm = body_for(False, fast)
        deleted = body_for(True, fast)
        expect_norm = [f"{row['id']},{name.strip().upper()}" for row, name in zip(data["rows"], raw)]
        expect_raw = [f"{row['id']},{name}" for row, name in zip(data["rows"], raw)]
        assert with_norm == expect_norm, "归一化输出内容不对"
        assert deleted == expect_raw, "删除归一化后的输出内容不对"
    print(f"correctness rows {rows}: with_norm 与 deleted 两种输出均与各自预期逐行一致")


def perm_test(a, b, perms: int = 20000, seed: int = 12345) -> float:
    """双侧置换检验, 统计量为中位数差的绝对值. 纯标准库实现."""
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


def summarize(name: str, samples):
    totals = [item[0] for item in samples]
    stage_sums = [sum(item[1].values()) for item in samples]
    normals = [item[1].get("normalize", 0.0) for item in samples]
    r_run = [item[1].get("normalize", 0.0) / item[0] for item in samples]
    r_stage = [item[1].get("normalize", 0.0) / sum(item[1].values()) for item in samples]
    med_r_run = statistics.median(r_run)
    med_r_stage = statistics.median(r_stage)
    print(
        f"{name} n {len(samples)} "
        f"run_med {statistics.median(totals):.2f} ms "
        f"run_range {min(totals):.2f}-{max(totals):.2f} "
        f"stage_sum_med {statistics.median(stage_sums):.2f} ms "
        f"normalize_med {statistics.median(normals):.2f} ms "
        f"r_run {med_r_run * 100:.2f}% upper_run {med_r_run / (1 - med_r_run) * 100:.2f}% "
        f"r_stage {med_r_stage * 100:.2f}% upper_stage {med_r_stage / (1 - med_r_stage) * 100:.2f}%"
    )
    return totals, stage_sums


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, nargs="+", default=[200, 60000])
    parser.add_argument("--rounds", type=int, default=9)
    args = parser.parse_args()

    correctness()
    arms = ["real_old", "rep_old", "rep_del_old", "rep_fast", "rep_del_fast"]
    for rows in args.rows:
        print(f"===== rows {rows} rounds {args.rounds} 交替 (每轮轮换起跑顺序) =====")
        collected = {arm: [] for arm in arms}
        for r in range(args.rounds):
            order = arms[r % len(arms) :] + arms[: r % len(arms)]
            for pos, arm in enumerate(order):
                # seed 每臂唯一, 保证 cache miss
                seed = rows * 10000 + r * 100 + arms.index(arm)
                total_ms, stages, stats, hit = one(arm, seed, rows)
                assert not hit, f"{arm} 缓存命中"
                assert stats["failed"] == 0, (arm, stats)
                assert stats["written"] == rows, (arm, stats, rows)
                assert all(value > 0 for value in stages.values()), (arm, stages)
                collected[arm].append((total_ms, stages, stats))
        totals_by_arm = {}
        spans_by_arm = {}
        for arm in arms:
            totals, sums = summarize(arm, collected[arm])
            totals_by_arm[arm] = totals
            spans_by_arm[arm] = sums
        print(
            f"校准 real_old vs rep_old: run_delta "
            f"{(statistics.median(totals_by_arm['real_old']) - statistics.median(totals_by_arm['rep_old'])) / statistics.median(totals_by_arm['real_old']) * 100:+.2f}% "
            f"stage_sum_delta "
            f"{(statistics.median(spans_by_arm['real_old']) - statistics.median(spans_by_arm['rep_old'])) / statistics.median(spans_by_arm['real_old']) * 100:+.2f}%"
        )
        for deleted, base in (("rep_del_old", "rep_old"), ("rep_del_fast", "rep_fast")):
            old_t, new_t = totals_by_arm[base], totals_by_arm[deleted]
            old_s, new_s = spans_by_arm[base], spans_by_arm[deleted]
            print(
                f"{deleted} vs {base}: run_med {statistics.median(old_t):.2f} -> {statistics.median(new_t):.2f} ms "
                f"gain {(statistics.median(old_t) - statistics.median(new_t)) / statistics.median(old_t) * 100:.2f}% "
                f"p(median,run) {perm_test(old_t, new_t):.4f} | "
                f"stage_sum_med {statistics.median(old_s):.2f} -> {statistics.median(new_s):.2f} ms "
                f"gain {(statistics.median(old_s) - statistics.median(new_s)) / statistics.median(old_s) * 100:.2f}% "
                f"p(median,stage_sum) {perm_test(old_s, new_s):.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
