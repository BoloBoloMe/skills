"""非正式 TC: 核查 bench/micro.py 的 26% 主张. 只读原项目, 不改产品代码与既有脚本.

测: index_fast / index_lite 的 build_index 单函数耗时 (交替 10 轮),
并核对两者的返回值是否等价, 以及能否互换喂给 report.export_report.
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path("/tmp/orchestra-19/green-lab")
sys.path.insert(0, str(ROOT / "src"))
from index_fast import build_index as fast  # noqa: E402
from index_lite import build_index as lite  # noqa: E402
from report import export_report  # noqa: E402

import time


def load_rows():
    rows = []
    with open(ROOT / "data" / "rows.csv", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.rstrip("\n").split(",")
            rows.append((key, value))
    return rows


def main():
    rows = load_rows()
    t_fast, t_lite = [], []
    a = b = None
    for i in range(10):
        s = time.perf_counter(); a = fast(rows); t_fast.append((time.perf_counter() - s) * 1000)
        s = time.perf_counter(); b = lite(rows); t_lite.append((time.perf_counter() - s) * 1000)
        print(f"rep{i+1:02d} fast={t_fast[-1]:.3f}ms lite={t_lite[-1]:.3f}ms")

    for name, t in (("fast", t_fast), ("lite", t_lite)):
        print(f"{name}: n={len(t)} median={statistics.median(t):.3f}ms "
              f"min={min(t):.3f}ms max={max(t):.3f}ms range={max(t)-min(t):.3f}ms")

    mf, ml = statistics.median(t_fast), statistics.median(t_lite)
    print(f"median gain = {(ml - mf) / ml * 100:.1f}%")

    # 正确性: 两个返回值是否等价
    print("fast value type:", type(next(iter(a.values()))).__name__,
          "lite value type:", type(next(iter(b.values()))).__name__)
    print("a == b ?", a == b)
    same_keys = set(a) == set(b)
    counts_match = all(a[k] == len(b[k]) for k in b) if same_keys else False
    print("same key set:", same_keys, "| fast[k] == len(lite[k]) for all k:", counts_match)
    print("sum(fast.values()) =", sum(a.values()), "len(rows) =", len(rows))
    print("keys =", len(a), "| total values kept by lite =", sum(len(v) for v in b.values()))

    # 成品入口能否两边互换
    out_fast = export_report(rows)
    out_lite = export_report(rows, build=lite)
    print("export fast bytes =", len(out_fast.encode()), "| export lite bytes =", len(out_lite.encode()))
    print("export outputs equal ?", out_fast == out_lite)
    print("export lite head:", out_lite[:90])
    print("export fast head:", out_fast[:90])
    print("export lite parses to ints ?",
          all(isinstance(item["count"], int) for item in json.loads(out_lite)))

    # 端到端: 成品入口两边的单次耗时 (只为量级, 不进正式比较)
    for name, kw in (("fast", {}), ("lite", {"build": lite})):
        s = time.perf_counter(); export_report(rows, **kw); e = (time.perf_counter() - s) * 1000
        print(f"export_once {name}: {e:.3f}ms")


if __name__ == "__main__":
    main()
