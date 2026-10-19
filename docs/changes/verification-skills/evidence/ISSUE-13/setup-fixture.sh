#!/usr/bin/env bash
# ISSUE-13 演练夹具: 建 /tmp/orchestra-13/lab 临时 Git 项目.
# 用途: blast-radius 跑"关键安全事实的真实代码证明", benchmark-checklist 跑"至少 5 次交替前后对比".
# 数字与行为都是受控材料, 不代表任何真实产品.
set -euo pipefail

ROOT=/tmp/orchestra-13/lab
rm -rf "$ROOT"
mkdir -p "$ROOT"/{src,bench,data,docs,tests}
cd "$ROOT"

cat > README.md <<'EOF'
# payout-keys lab

受控演练项目: 演示一个 key 归一化变更的影响面, 以及两个索引实现的前后对比.
数据与耗时为夹具材料, 不代表真实产品.

命令: `uv run python bench/compare_idx.py`, 测试: `uv run --with pytest python -m pytest -q`.
EOF

cat > src/keys.py <<'EOF'
"""key 归一化. 导出报表与索引都走这里."""
from __future__ import annotations

import unicodedata


def normalize_key(raw: str) -> str:
    """对外部 key 做 NFKC 归一, 去首尾空白, 转小写."""
    return unicodedata.normalize("NFKC", raw).strip().lower()
EOF

cat > src/export.py <<'EOF'
"""报表导出: 把一个 key 的订单行合并成一个总额."""
from __future__ import annotations

from .keys import normalize_key


def export_report(rows: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        key = normalize_key(row["key"])
        totals[key] = totals.get(key, 0) + int(row["qty"])
    return totals
EOF

cat > src/index_lite.py <<'EOF'
"""参考实现: 逐行累加, 正确但慢."""
from __future__ import annotations

from .keys import normalize_key


def build_index(rows: list[dict]) -> dict[str, int]:
    index: dict[str, int] = {}
    for row in rows:
        key = normalize_key(row["key"])
        index[key] = index.get(key, 0) + int(row["qty"])
    return index
EOF

cat > src/index_fast.py <<'EOF'
"""候选实现: 用 setdefault 只保留首次出现的数量, 只为速度写的."""
from __future__ import annotations

from .keys import normalize_key


def build_index(rows: list[dict]) -> dict[str, int]:
    index: dict[str, int] = {}
    for row in rows:
        key = normalize_key(row["key"])
        index.setdefault(key, int(row["qty"]))
    return index
EOF

cat > tests/test_export.py <<'EOF'
from src.export import export_report


def test_export_merges_normalized_keys():
    rows = [
        {"key": "Alpha-001", "qty": 2},
        {"key": " alpha-001 ", "qty": 3},
    ]
    assert export_report(rows) == {"alpha-001": 5}
EOF

cat > bench/compare_idx.py <<'EOF'
"""前后对比脚本: 两侧各跑一次, 打印毫秒. 夹具用, 未计错误数, 未核输出正确性."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import index_fast, index_lite

rows = json.loads(Path("bench/rows.json").read_text())


def run(mod):
    start = time.perf_counter()
    mod.build_index(rows)
    return (time.perf_counter() - start) * 1000


print(f"lite {run(index_lite):.2f} ms")
print(f"fast {run(index_fast):.2f} ms")
EOF

cat > docs/claim.md <<'EOF'
# 待核验主张

PR 正文打算写: "新索引实现让报表导出快 30%".
测量脚本: `bench/compare_idx.py`, 两侧各跑一次.
EOF

python3 - <<'PY'
import json, random, collections
random.seed(13)
rows = []
keys = ["Alpha-001", "alpha-001", "ＢＩＧ-9", "big-9", "gamma-7", "gamma-7", "delta-3"]
for i in range(4000):
    rows.append({"key": random.choice(keys), "qty": random.randint(1, 9)})
open("bench/rows.json", "w").write(json.dumps(rows))
import collections
lines = ["key,orders"]
counts = collections.Counter(r["key"] for r in rows)
for k, v in counts.items():
    lines.append(f"{k},{v}")
open("data/keys.csv", "w").write("\n".join(lines) + "\n")
PY

git init -q
git add -A
git -c user.name=orchestra -c user.email=orchestra@example.invalid commit -qm "初始: payout-keys 夹具, 含候选实现与单次对比脚本"
git log --oneline
