#!/usr/bin/env bash
# 生成 /tmp/orchestra-19 下的临时 Git 演练项目, 可重跑.
# 用法: bash setup-fixture.sh <项目目录>
set -eu
project="${1:?需要项目目录}"
rm -rf "$project"
mkdir -p "$project/src" "$project/bench" "$project/data" "$project/docs"

cat > "$project/README.md" <<'MD'
# 报表导出小工具

`src/report.py` 是成品入口, `bench/` 下是开发侧的测量脚本.
MD

cat > "$project/src/index_lite.py" <<'PY'
"""旧索引实现: 每个 key 保留一份值列表."""


def build_index(rows):
    index = {}
    for key, value in rows:
        index.setdefault(key, []).append(value)
    return index
PY

cat > "$project/src/index_fast.py" <<'PY'
"""新索引实现: 先把值累加到计数器, 再一次性成型."""


def build_index(rows):
    counts = {}
    for key, _value in rows:
        counts[key] = counts.get(key, 0) + 1
    return counts
PY

cat > "$project/src/report.py" <<'PY'
"""报表导出成品入口."""
import json

from index_fast import build_index as default_build


def export_report(rows, build=default_build):
    index = build(rows)
    payload = []
    for key in sorted(index):
        value = index[key]
        count = value if isinstance(value, int) else len(value)
        payload.append({"key": key, "count": count})
    return json.dumps(payload)
PY

cat > "$project/bench/micro.py" <<'PY'
"""微基准: 只给 index_lite 与 index_fast 的 build_index 计时, 各跑一次."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from index_fast import build_index as fast  # noqa: E402
from index_lite import build_index as lite  # noqa: E402


def load_rows():
    rows = []
    with open(Path(__file__).resolve().parent.parent / "data" / "rows.csv", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.rstrip("\n").split(",")
            rows.append((key, value))
    return rows


def main():
    rows = load_rows()
    start = time.perf_counter()
    lite(rows)
    lite_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    fast(rows)
    fast_ms = (time.perf_counter() - start) * 1000
    gain = (lite_ms - fast_ms) / lite_ms * 100
    print(f"index_lite {lite_ms:.3f}ms index_fast {fast_ms:.3f}ms 快 {gain:.1f}%")


if __name__ == "__main__":
    main()
PY

cat > "$project/bench/export_once.py" <<'PY'
"""成品入口 export_report 的单次测量: 打印耗时与处理条数."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from report import export_report  # noqa: E402


def load_rows():
    rows = []
    with open(Path(__file__).resolve().parent.parent / "data" / "rows.csv", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.rstrip("\n").split(",")
            rows.append((key, value))
    return rows


def main():
    rows = load_rows()
    start = time.perf_counter()
    out = export_report(rows)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"export_report {elapsed_ms:.3f}ms 处理 {len(rows)} 条, 输出 {len(out)} 字节")


if __name__ == "__main__":
    main()
PY

cat > "$project/docs/claim.md" <<'MD'
# 待核验主张

新索引实现 (index_fast) 让报表导出快 40%, 准备写进 PR 正文.
MD

uv run python - "$project/data/rows.csv" <<'PY'
import sys

path = sys.argv[1]
with open(path, "w", encoding="utf-8") as handle:
    for i in range(200000):
        handle.write(f"k{i % 37:02d},v{i}\n")
PY

git -C "$project" init -q
git -C "$project" add -A
git -C "$project" -c user.name=lab -c user.email=lab@example.invalid commit -qm "fixture: 报表导出与两套索引的最小项目"
git -C "$project" rev-parse --short HEAD
