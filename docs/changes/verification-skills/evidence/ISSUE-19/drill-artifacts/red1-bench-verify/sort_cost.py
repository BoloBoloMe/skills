"""非正式 TC: export_report 里 sorted(index) 那几行的绝对成本.
单次结构: 建好 index 后, 把 sorted(index) 单独重复计时, 再对照整条路径."""
import json, sys, time
sys.path.insert(0, "/tmp/orchestra-19/red-lab/src")
from index_fast import build_index

rows = []
with open("/tmp/orchestra-19/red-lab/data/rows.csv", encoding="utf-8") as h:
    for line in h:
        k, v = line.rstrip("\n").split(",")
        rows.append((k, v))

index = build_index(rows)
print("key 数", len(index))

t0 = time.perf_counter(); out = json.dumps([{"key": k} for k in index]); whole = (time.perf_counter()-t0)*1000
N = 2000
t0 = time.perf_counter()
for _ in range(N):
    sorted(index)
per = (time.perf_counter()-t0)*1000/N
print(f"sorted(index) 单次约 {per*1000:.1f} 微秒 ({per:.5f} ms)")
print(f"整条 export_report 上次实测约 9.15 ms -> 占比约 {per/9.15*100:.4f}%")
