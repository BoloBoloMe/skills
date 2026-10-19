"""非正式 TC 一次性实验: export_report 在 index_lite / index_fast 两侧交替各 5 次.
不改产品代码, 只用 export_report 已有的 build 参数注入. 记录中位数/极差/输出字节/失败数."""
import statistics
import sys
import time
from pathlib import Path

REPO = Path("/tmp/orchestra-19/red-lab")
sys.path.insert(0, str(REPO / "src"))
from report import export_report  # noqa: E402
import index_lite  # noqa: E402
import index_fast  # noqa: E402

rows = []
with open(REPO / "data" / "rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))

sides = {"lite": index_lite.build_index, "fast": index_fast.build_index}
res = {"lite": [], "fast": []}
bytes_out = {}
fails = {"lite": 0, "fast": 0}
build_ms = {"lite": [], "fast": []}

for _ in range(5):
    for name in ("lite", "fast"):          # 交替 A,B,A,B...
        t0 = time.perf_counter()
        try:
            out = export_report(rows, build=sides[name])
        except Exception as exc:
            fails[name] += 1
            print("FAIL", name, exc)
            continue
        el = (time.perf_counter() - t0) * 1000
        res[name].append(el)
        bytes_out[name] = len(out)

rows_ref = rows
for name, fn in sides.items():
    for _ in range(3):
        t0 = time.perf_counter()
        fn(rows_ref)
        build_ms[name].append((time.perf_counter() - t0) * 1000)

for name in ("lite", "fast"):
    v = res[name]
    print(f"{name}: n={len(v)} median={statistics.median(v):.2f}ms range={min(v):.2f}-{max(v):.2f}ms "
          f"输出={bytes_out.get(name)}字节 fails={fails[name]}")
    b = build_ms[name]
    print(f"  仅 build_index: median={statistics.median(b):.2f}ms range={min(b):.2f}-{max(b):.2f}ms")
