"""证明 3: 导出的 JSON 交给 Node 消费者 (orders-consumer/src/ledger.js) 后, 账目怎么变.

运行:
  cd /tmp/orchestra-07/out/ts002-work
  PYTHONPATH=/tmp/orchestra-07/drill-ts002 uv run --no-project python proof_consumer.py

判断错时 assert 失败. 只读两个仓库: 只在 out/ts002-work 写导出文件.
"""
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts002")
WORK = pathlib.Path("/tmp/orchestra-07/out/ts002-work")
LEDGER = pathlib.Path("/tmp/orchestra-07/orders-consumer/src/ledger.js")

CASES = {
    1: {"schema": "v2", "amount": "12.50"},
    2: {"schema": "v1", "amount_str": "9.99"},
    3: {"schema": "v1", "amount_str": ""},
    6: {"schema": "v1", "amount_str": "   "},
    10: {"schema": "v2", "amount": None, "amount_str": "9.99"},
    8: {"schema": "v1", "amount_str": "abc"},
}


def export(impl, ids, out_path):
    if impl == "old":
        import old_orders as mod
    else:
        from app.orders import read_orders  # noqa: PLC0415

        mod = sys.modules["app.orders"]
    conn = sqlite3.connect(":memory:")
    conn.executescript((REPO / "db" / "schema.sql").read_text())
    conn.executemany(
        "INSERT INTO orders (id, payload) VALUES (?, ?)",
        [(i, json.dumps(CASES[i])) for i in ids],
    )
    rows = mod.read_orders(conn)
    pathlib.Path(out_path).write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    return rows


def run_export(impl, ids, out_path):
    proc = subprocess.run(
        [sys.executable, __file__, "--impl", impl, "--ids", ",".join(map(str, ids)), "--out", str(out_path)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO) + os.pathsep + str(WORK)},
    )
    return proc


def run_ledger(path):
    proc = subprocess.run(["node", str(LEDGER), str(path)], capture_output=True, text=True)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    return json.loads(proc.stdout)


def main():
    if "--impl" in sys.argv:
        impl = sys.argv[sys.argv.index("--impl") + 1]
        ids = [int(x) for x in sys.argv[sys.argv.index("--ids") + 1].split(",")]
        out = sys.argv[sys.argv.index("--out") + 1]
        print(json.dumps(export(impl, ids, out), ensure_ascii=False))
        return

    # 1) 真实种子行: 消费者看到的账目必须一样
    for impl in ("old", "new"):
        p = WORK / f"export_seed_{impl}.json"
        run_export(impl, [1, 2, 3], p)
        print(f"seed {impl} ledger:", json.dumps(run_ledger(p), ensure_ascii=False))
    old_seed = run_ledger(WORK / "export_seed_old.json")
    new_seed = run_ledger(WORK / "export_seed_new.json")
    assert old_seed == new_seed, (old_seed, new_seed)
    assert abs(old_seed["total"] - 22.49) < 1e-9 and old_seed["missing"] == [3], old_seed

    # 2) 空白串与 v2 amount=null 的行
    ids = [1, 2, 3, 6, 10]
    for impl in ("old", "new"):
        p = WORK / f"export_edge_{impl}.json"
        run_export(impl, ids, p)
        print(f"edge {impl} rows:", p.read_text().replace("\n", " "))
        print(f"edge {impl} ledger:", json.dumps(run_ledger(p), ensure_ascii=False))
    old_edge = run_ledger(WORK / "export_edge_old.json")
    new_edge = run_ledger(WORK / "export_edge_new.json")
    print("edge diff:", {"old": old_edge, "new": new_edge})
    # id=10 (v2 amount=null + amount_str='9.99'): 旧版算缺失, 新版把它算进总额
    assert abs(old_edge["total"] - 22.49) < 1e-9, old_edge
    assert abs(new_edge["total"] - 32.48) < 1e-9, new_edge
    assert 6 not in old_edge["missing"] and 6 in new_edge["missing"], (old_edge, new_edge)
    assert 10 in old_edge["missing"] and 10 not in new_edge["missing"], (old_edge, new_edge)
    # 3) v1 坏文本: 旧版导出 'abc' -> 消费者 total 变 null; 新版导出直接失败, 文件不更新
    stale = WORK / "export_stale.json"
    stale.write_text(json.dumps([{"id": 1, "amount": "12.50"}], ensure_ascii=False))
    print("stale before:", stale.read_text())
    old_bad = run_export("old", [1, 2, 3, 6, 10, 8], WORK / "export_bad_old.json")
    new_bad = run_export("new", [1, 2, 3, 6, 10, 8], stale)
    print("old bad export rc:", old_bad.returncode)
    print("old bad ledger:", json.dumps(run_ledger(WORK / "export_bad_old.json"), ensure_ascii=False))
    print("new bad export rc:", new_bad.returncode)
    print("new bad export stderr tail:", new_bad.stderr.strip().splitlines()[-1:] )
    print("stale after (new 失败, 文件没动):", stale.read_text())

    assert old_bad.returncode == 0
    assert run_ledger(WORK / "export_bad_old.json")["total"] is None  # NaN -> JSON null
    assert new_bad.returncode != 0
    assert "ValueError" in new_bad.stderr
    assert json.loads(stale.read_text()) == [{"id": 1, "amount": "12.50"}]

    print("\nOK: 消费者侧账目变化已复现")


if __name__ == "__main__":
    main()
