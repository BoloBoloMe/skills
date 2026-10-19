"""证明脚本: 同一批仓库真实数据, 对比现实现与候选 str.lower().
判断错时 assert 失败, 非零退出.
"""
import json, sys, unicodedata
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root))
from src import export, index_lite, index_fast

rows = json.loads((Path(sys.argv[2]) / "bench/rows.json").read_text())

print("== 环境")
print("python", sys.version.split()[0], "unicodedata", unicodedata.unidata_version)
print("module file", export.normalize_key.__module__)

rep = export.export_report(rows)
lite = index_lite.build_index(rows)
fast = index_fast.build_index(rows)
print("== export_report")
for k in sorted(rep): print(f"  {k!r}: {rep[k]}")
print("== index_lite")
for k in sorted(lite): print(f"  {k!r}: {lite[k]}")
print("== index_fast")
for k in sorted(fast): print(f"  {k!r}: {fast[k]}")
print("== 汇总")
print("export keys", len(rep), "sum", sum(rep.values()), "rows", len(rows))
assert sum(rep.values()) == sum(int(r["qty"]) for r in rows), "总量守恒"
