"""任务 2 复核: noop_claim.py 的 40% 是否可比.

原脚本: old 侧 dry_run=False, new 侧 dry_run=True, 各 5 次, 先 old 后 new.
本脚本: 同一真实入口 run_job, 三臂交替:
  old_full  慢归一化 + 真写出
  new_full  快归一化 + 真写出   <- 与 old_full 唯一差别是归一化实现
  new_dry   快归一化 + dry_run   <- 原脚本 new 侧的条件, 不写出
同时核对 written 条数, failed 数, cache 命中, 以及输出内容.
"""

import argparse
import random
import statistics
import sys
import time

sys.path.insert(0, "src")
from pipeline import normalize, normalize_fast, parse, render, run_job  # noqa: E402

ARMS = ["old_full", "new_full", "new_dry"]


def payload(seed: int, rows: int) -> dict:
    return {"rows": [{"id": seed * 100000 + i, "name": f" n{i}-{seed} "} for i in range(rows)]}


def one(arm: str, seed: int, rows: int):
    data = payload(seed, rows)  # 计时区内构造, 与原脚本一致
    start = time.perf_counter()
    fast = arm != "old_full"
    dry = arm == "new_dry"
    stats, stages = run_job(data, fast_normalize=fast, dry_run=dry)
    total_ms = (time.perf_counter() - start) * 1000
    hit = "cache" in stages
    return total_ms, stages, stats, hit


def correctness(rows: int = 50) -> None:
    data = payload(888888, rows)
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

    print(f"===== rows {args.rows} rounds {args.rounds} 三臂交替 (每轮轮换起跑顺序) =====")
    samples = {arm: [] for arm in ARMS}
    for r in range(args.rounds):
        order = ARMS[r % len(ARMS) :] + ARMS[: r % len(ARMS)]
        for arm in order:
            seed = args.rows * 10000 + r * 100 + ARMS.index(arm)
            total_ms, stages, stats, hit = one(arm, seed, args.rows)
            assert not hit, f"{arm} 缓存命中"
            if arm == "new_dry":
                assert stats["written"] == 0 and stats["failed"] == 0, (arm, stats)
                assert stages["write"] == 0.0, (arm, stages)
            else:
                assert stats["written"] == args.rows, (arm, stats)
                assert stats["failed"] == 0, (arm, stats)
                assert stages["write"] > 0, (arm, stages)
            samples[arm].append((total_ms, stages, stats))

    totals = {}
    for arm in ARMS:
        values = [item[0] for item in samples[arm]]
        totals[arm] = values
        stages = samples[arm][-1][1]
        stage_text = " ".join(f"{k}={v:.2f}" for k, v in stages.items())
        non_success = sum(
            1 for item in samples[arm] if item[2]["failed"] > 0 or item[2]["written"] != args.rows
        )
        print(
            f"{arm} n {len(values)} median {statistics.median(values):.2f} ms "
            f"range {min(values):.2f}-{max(values):.2f} "
            f"non_success {non_success}/{len(values)} "
            f"written_last {samples[arm][-1][2]['written']} failed_last {samples[arm][-1][2]['failed']}"
        )
        print(f"  last_stages {stage_text}")

    for label, base, candidate in (
        ("原脚本口径 old_full vs new_dry", "old_full", "new_dry"),
        ("同条件 old_full vs new_full", "old_full", "new_full"),
    ):
        old, new = totals[base], totals[candidate]
        print(
            f"{label}: {statistics.median(old):.2f} -> {statistics.median(new):.2f} ms "
            f"change {(statistics.median(old) - statistics.median(new)) / statistics.median(old) * 100:.2f}% "
            f"p(median) {perm_test(old, new):.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
