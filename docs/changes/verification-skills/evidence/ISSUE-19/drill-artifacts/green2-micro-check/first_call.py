"""非正式 TC 续: 复现 micro.py 的固定顺序, 区分首调用开销与稳定差距; 并做秩和检验."""
import statistics
import sys
import time
from pathlib import Path

ROOT = Path("/tmp/orchestra-19/green-lab")
sys.path.insert(0, str(ROOT / "src"))
from index_fast import build_index as fast  # noqa: E402
from index_lite import build_index as lite  # noqa: E402


def load_rows():
    rows = []
    with open(ROOT / "data" / "rows.csv", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.rstrip("\n").split(",")
            rows.append((key, value))
    return rows


rows = load_rows()
mode = sys.argv[1]

if mode == "first":
    start = time.perf_counter()
    (lite if sys.argv[2] == "lite" else fast)(rows)
    print(f"first-call {sys.argv[2]}: {(time.perf_counter()-start)*1000:.3f}ms")
else:
    # 预热两侧后, 按 micro.py 的固定顺序 lite, fast 反复测
    fast(rows); lite(rows)
    tl, tf = [], []
    for _ in range(10):
        s = time.perf_counter(); lite(rows); tl.append((time.perf_counter() - s) * 1000)
        s = time.perf_counter(); fast(rows); tf.append((time.perf_counter() - s) * 1000)
    print(f"warm fixed-order lite median={statistics.median(tl):.3f} "
          f"range={max(tl)-min(tl):.3f}; fast median={statistics.median(tf):.3f} "
          f"range={max(tf)-min(tf):.3f}; gain={(statistics.median(tl)-statistics.median(tf))/statistics.median(tl)*100:.1f}%")
