"""非正式一次性实验: 每个进程只测一次, 看冷启动成本落在谁头上."""
import sys, time
from pathlib import Path
REPO = Path("/tmp/orchestra-19/red3-lab")
sys.path.insert(0, str(REPO / "src"))
side = sys.argv[1]
fn = __import__("index_" + side).build_index
rows = [tuple(l.rstrip("\n").split(",")) for l in open(REPO/"data"/"rows.csv", encoding="utf-8")]
s = time.perf_counter(); out = fn(rows); d = (time.perf_counter()-s)*1000
print(f"{side} 首次调用(含结果销毁) {d:.2f}ms")
