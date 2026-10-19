"""非正式 TC 一次性校验: 不进仓库, 只核对 export_report 输出正确性与工作量."""
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("/tmp/orchestra-19/red-lab")
sys.path.insert(0, str(REPO / "src"))
from report import export_report  # noqa: E402

rows = []
with open(REPO / "data" / "rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))

out = export_report(rows)
payload = json.loads(out)
ref = Counter(k for k, _ in rows)
got = {d["key"]: d["count"] for d in payload}

print("输入条数", len(rows))
print("输出条目", len(payload), "参考 distinct", len(ref))
print("计数总和", sum(got.values()), "应等于输入", sum(got.values()) == len(rows))
print("计数完全匹配", got == dict(ref))
print("键有序", [d["key"] for d in payload] == sorted(ref))
print("失败/非成功响应: 无异常抛出, exit=0, 无错误日志")
