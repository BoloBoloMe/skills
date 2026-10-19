"""同一批 8 行数据上对比三个候选侧, 并核对成功数与返回值正确性.

不是新增正式用例, 只为核查 "export_flow 132ms 对旧版 73ms 说明新版变慢".
export_flow.py 跑的是 export(ROWS, "b") 默认档; 旧版 73ms 来自
run_export.py 的 5 行批次. 本脚本把两侧放回同一批 8 行, 并加上
成功/失败计数与 payload 校验.

用法:
  uv run python bench/same_batch_compare.py --side legacy
  uv run python bench/same_batch_compare.py --side new-default
  uv run python bench/same_batch_compare.py --side new-tuned
"""

import argparse
import sys
import time

sys.path.insert(0, "src")
from exporter import _work, export, export_tuned  # noqa: E402

# 与 bench/export_flow.py 完全相同的批次
ROWS = [120, 640, 810, 340, 990, 450, 700, 260]

# 期望: 每行成功时应有的 payload. 与实现无关地按公式算一遍, 只用于校验.
EXPECTED = [_work(i + 1) + row for i, row in enumerate(ROWS)]


def run(side: str):
    if side == "legacy":
        return export(ROWS, "a")
    if side == "new-default":
        return export(ROWS, "b")
    if side == "new-tuned":
        return export_tuned(ROWS, "clear")
    raise ValueError(side)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=["legacy", "new-default", "new-tuned"], required=True)
    args = parser.parse_args()

    start = time.perf_counter()
    results = run(args.side)
    elapsed = (time.perf_counter() - start) * 1000

    ok = sum(1 for r in results if r["ok"])
    failed = len(results) - ok
    payload_ok = sum(
        1 for r, want in zip(results, EXPECTED) if r["ok"] and r["payload"] == want
    )
    # 失败行没有 payload, 不参与 payload 校验; 它们本身就是 "没做这项工作".
    correctness = "ok" if payload_ok == ok == len(EXPECTED) - failed else "MISMATCH"

    print(
        f"side {args.side} total {elapsed:.1f} ms "
        f"rows {len(ROWS)} ok {ok} failed {failed} payload_ok {payload_ok} "
        f"correctness {correctness}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
