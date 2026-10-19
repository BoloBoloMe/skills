"""公平对比: 同一批行, 交替跑 a 默认 / b 默认 / b 调优 / legacy, 不加随机扰动.

计时范围: 只包住 export/export_tuned/export_legacy 调用本身, 含结果构造.
计数项: 返回条数, ok 条数, 错误条数, legacy 写入条数.
校验项: a 与 b 都成功的同一行 payload 是否相等, 确认 b 的成功行做了同样的计算.
"""

import statistics
import sys
import time

sys.path.insert(0, "src")
from exporter import export, export_legacy, export_tuned  # noqa: E402

ROWS = [1000 + i for i in range(5)]
SIDES = ["a", "b", "tuned", "legacy"]


def run(side: str):
    start = time.perf_counter()
    if side == "a":
        out = export(ROWS, "a")
    elif side == "b":
        out = export(ROWS, "b")
    elif side == "tuned":
        out = export_tuned(ROWS, "clear")
    else:
        written = export_legacy(ROWS)
        out = None
    elapsed = (time.perf_counter() - start) * 1000
    if out is None:
        return elapsed, {"written": written}
    return elapsed, {
        "returned": len(out),
        "ok": sum(1 for r in out if r["ok"]),
        "err": sum(1 for r in out if not r["ok"]),
        "out": out,
    }


def main() -> int:
    rounds = 6
    samples = {s: [] for s in SIDES}
    meta = {}
    for r in range(rounds):
        order = SIDES if r % 2 == 0 else list(reversed(SIDES))
        for side in order:
            elapsed, info = run(side)
            samples[side].append(elapsed)
            meta.setdefault(side, info)
        print("round", r + 1, " ".join(f"{s}={samples[s][-1]:.1f}" for s in SIDES))

    print()
    for side in SIDES:
        xs = samples[side]
        info = meta[side]
        counts = {k: v for k, v in info.items() if k != "out"}
        print(
            f"{side:7s} n={len(xs)} min={min(xs):.1f} p50={statistics.median(xs):.1f} "
            f"max={max(xs):.1f} {counts}"
        )

    a_ok = {i: r["payload"] for i, r in enumerate(meta["a"]["out"]) if r["ok"]}
    b_ok = {i: r["payload"] for i, r in enumerate(meta["b"]["out"]) if r["ok"]}
    common = sorted(set(a_ok) & set(b_ok))
    same = all(a_ok[i] == b_ok[i] for i in common)
    print(f"payload 一致行 {common} 全部相等={same}; b 缺的行 {sorted(set(a_ok) - set(b_ok))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
