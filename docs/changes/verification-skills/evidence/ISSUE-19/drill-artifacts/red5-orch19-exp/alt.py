"""非正式一次性实验: 交替测 build_index, 带正确性核对与失败计数."""
import statistics
import sys
import time
from pathlib import Path

REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
from index_fast import build_index as fast  # noqa: E402
from index_lite import build_index as lite  # noqa: E402

rows = []
with open(REPO / "data" / "rows.csv", encoding="utf-8") as fh:
    for line in fh:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))

def counts(idx):
    return {k: (v if isinstance(v, int) else len(v)) for k, v in idx.items()}

errors = 0
def timed(fn):
    global errors
    t = time.perf_counter()
    try:
        out = fn(rows)
    except Exception as exc:  # noqa: BLE001
        errors += 1
        print("ERROR", exc)
        return None, float("nan")
    return out, (time.perf_counter() - t) * 1000

# 正确性: 两侧索引折算成 key->条数 后与原始数据独立统计比对
expected = {}
for k, _v in rows:
    expected[k] = expected.get(k, 0) + 1
lite_idx, _ = timed(lite)
fast_idx, _ = timed(fast)
print("lite 结果正确:", counts(lite_idx) == expected, "| fast 结果正确:", counts(fast_idx) == expected)
print("lite 索引值类型:", type(next(iter(lite_idx.values()))).__name__,
      "| fast 索引值类型:", type(next(iter(fast_idx.values()))).__name__)

lite_ms, fast_ms = [], []
for r in range(7):
    _, a = timed(lite); lite_ms.append(a)
    _, b = timed(fast); fast_ms.append(b)
    print(f"round {r+1}: lite {a:.3f} fast {b:.3f}")

def stat(xs):
    return f"n={len(xs)} median={statistics.median(xs):.3f} min={min(xs):.3f} max={max(xs):.3f} range={max(xs)-min(xs):.3f}"

print("lite", stat(lite_ms))
print("fast", stat(fast_ms))
print(f"中位数降幅 {(statistics.median(lite_ms)-statistics.median(fast_ms))/statistics.median(lite_ms)*100:.1f}%")
print("运行失败数:", errors, "| 处理条数每侧 7 次 x", len(rows))
