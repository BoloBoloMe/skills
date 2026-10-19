"""门禁: 新导出必须仍能被订单消费者读成同一份账.

期望 (基线): total 22.49, missing [3].
判断错就以非零退出, 并原样打印消费者输出与 stderr.
"""
import json, pathlib, subprocess, sys

W = pathlib.Path("/tmp/orchestra-07/out/ts003-gap-work")
LEDGER = "/tmp/orchestra-07/orders-consumer/src/ledger.js"
EXPECTED = {"total": 22.49, "missing": [3]}

def run(path):
    p = subprocess.run(["node", LEDGER, str(path)], capture_output=True, text=True)
    print(f"--- node ledger.js {path.name}  rc={p.returncode}")
    print("stdout:", p.stdout.strip() or "<空>")
    if p.stderr:
        print("stderr:", p.stderr.strip().splitlines()[0])
    return p

fails = 0
for name, path in [("基线导出", W / "base/var/orders.export.json"),
                   ("新导出  ", W / "head/var/orders.export.json")]:
    p = run(path)
    try:
        got = json.loads(p.stdout)
        assert p.returncode == 0, f"rc={p.returncode}"
        assert abs(got["total"] - EXPECTED["total"]) < 1e-9, got
        assert got["missing"] == EXPECTED["missing"], got
        print(f"    PASS {name}")
    except Exception as e:
        fails += 1
        print(f"    FAIL {name}: {e}")
sys.exit(1 if fails else 0)
