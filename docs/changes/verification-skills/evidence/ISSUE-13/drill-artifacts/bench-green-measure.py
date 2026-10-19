"""非正式实验: 核查 "新索引实现让报表导出快 30%" 这一主张.

授权范围: 只读仓库代码与数据, 脚本与输出放仓库外 /tmp/idx-check.
产品源码, 既有测试, 项目配置均不改.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path("/tmp/orchestra-13/lab")
sys.path.insert(0, str(REPO))

from src import index_fast, index_lite  # noqa: E402
from src.export import export_report  # noqa: E402

rows = json.loads((REPO / "bench/rows.json").read_text())
ROUNDS = 9

sink = 0


def timed(fn):
    global sink
    t0 = time.perf_counter()
    out = fn()
    dt = (time.perf_counter() - t0) * 1000
    # 消费结果, 防止被优化掉/计时区外丢弃
    sink ^= hash(tuple(sorted(out.items())))
    return dt, out


failures = 0


def safe(fn):
    global failures
    try:
        return timed(fn)
    except Exception as exc:  # noqa: BLE001
        failures += 1
        print(f"FAIL {fn}: {exc!r}")
        return None, None


def summarize(name, xs):
    print(
        f"{name}: n={len(xs)} median={statistics.median(xs):.3f} ms "
        f"min={min(xs):.3f} max={max(xs):.3f} range={max(xs)-min(xs):.3f} "
        f"all={[round(x, 3) for x in xs]}"
    )


# ---- 1. 正确性: 两个实现是否同意, 是否覆盖全部输入行 ----
lite_out = index_lite.build_index(rows)
fast_out = index_fast.build_index(rows)
expected = {}
for r in rows:
    from src.keys import normalize_key

    k = normalize_key(r["key"])
    expected[k] = expected.get(k, 0) + int(r["qty"])

print(f"rows={len(rows)} distinct_keys={len(expected)}")
print(f"lite == 逐行累加真值: {lite_out == expected}")
print(f"fast == 逐行累加真值: {fast_out == expected}")
mismatch = {k: (expected.get(k), fast_out.get(k)) for k in expected if expected.get(k) != fast_out.get(k)}
print(f"fast 与真值不一致的 key 数: {len(mismatch)} / {len(expected)}")
print(f"fast 丢掉的数量合计: {sum(a - b for a, b in mismatch.values())}")
print(f"lite 合计数量={sum(lite_out.values())} fast 合计数量={sum(fast_out.values())}")

# ---- 2. 交替重复计时: build_index 两侧 ----
lite_t, fast_t, export_t = [], [], []
for i in range(ROUNDS):
    d, _ = safe(lambda: index_lite.build_index(rows))
    lite_t.append(d)
    d, _ = safe(lambda: index_fast.build_index(rows))
    fast_t.append(d)
    d, _ = safe(lambda: export_report(rows))
    export_t.append(d)

summarize("index_lite.build_index", lite_t)
summarize("index_fast.build_index", fast_t)
summarize("export_report (真实导出入口)", export_t)

# ---- 3. 占比与收益上限 ----
med_lite = statistics.median(lite_t)
med_export = statistics.median(export_t)
r = med_lite / med_export
upper = r / (1 - r) if r < 1 else float("inf")
print(f"被改动段(索引构建) 中位耗时 / 端到端导出中位耗时 r={r:.4f}")
print(f"若整段完全移除, 端到端收益上限={upper*100:.2f}% (仅天花板, 非结果)")
print(f"export_report 是否调用 build_index: {'build_index' in Path(REPO/'src/export.py').read_text()}")
print(f"failures={failures} sink={sink} sha={hashlib.sha256(str(sink).encode()).hexdigest()[:12]}")
