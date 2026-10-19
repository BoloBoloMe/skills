"""证明 2: 逐条比较 HEAD~1 与 HEAD 的 read_orders 输出 (同一 amountlib, 真实 SQLite 行).

每个用例单独一个子进程: 旧版 import 时会向 amountlib 的全局 _FORMATTERS 注册
formatter, 同进程跑新版会被污染.

运行:
  cd /tmp/orchestra-07/out/ts002-work
  PYTHONPATH=/tmp/orchestra-07/drill-ts002 uv run --no-project python proof_orders_compare.py

判断错时 assert 失败, 退出码非 0. 只读仓库: 数据库建在内存里.
"""
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts002")
WORK = pathlib.Path("/tmp/orchestra-07/out/ts002-work")

# 1-3 是 db/seed.py:8-12 的三条真实行, 其余是新旧分支会走出差异的形状
CASES = {
    1: {"schema": "v2", "amount": "12.50"},
    2: {"schema": "v1", "amount_str": "9.99"},
    3: {"schema": "v1", "amount_str": ""},
    4: {"schema": "v1"},
    5: {"schema": "v1", "amount_str": None},
    6: {"schema": "v1", "amount_str": "   "},
    7: {"schema": "v1", "amount_str": " 012.50 "},
    8: {"schema": "v1", "amount_str": "abc"},
    9: {"schema": "v1", "amount_str": "9,99"},
    10: {"schema": "v2", "amount": None, "amount_str": "9.99"},
    11: {"schema": "v2", "amount": "", "amount_str": ""},
    12: {"schema": "v2", "amount": "abc"},
    13: {"schema": "v1", "amount_str": 12.5},
    14: {"schema": "v2", "amount": 12.5},
}
SEED_IDS = (1, 2, 3)


def load_impl(impl):
    if impl == "old":
        import old_orders  # 由 `git show HEAD~1:app/orders.py` 生成

        return old_orders
    from app.orders import read_orders  # noqa: PLC0415

    return sys.modules["app.orders"]


def run(impl, ids):
    mod = load_impl(impl)
    conn = sqlite3.connect(":memory:")
    conn.executescript((REPO / "db" / "schema.sql").read_text())
    conn.executemany(
        "INSERT INTO orders (id, payload) VALUES (?, ?)",
        [(i, json.dumps(CASES[i])) for i in ids],
    )
    try:
        return {"rows": mod.read_orders(conn)}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def child(impl, ids):
    out = subprocess.run(
        [sys.executable, __file__, "--impl", impl, "--ids", ",".join(map(str, ids))],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO) + os.pathsep + str(WORK)},
    )
    if out.returncode != 0:
        raise SystemExit(f"{impl} 子进程失败:\n{out.stdout}\n{out.stderr}")
    return json.loads(out.stdout)


def result_of(res):
    if "error" in res:
        return "ERROR " + res["error"].split(":")[0]
    return res["rows"][0]["amount"]


def main():
    if "--impl" in sys.argv:
        impl = sys.argv[sys.argv.index("--impl") + 1]
        ids = [int(x) for x in sys.argv[sys.argv.index("--ids") + 1].split(",")]
        print(json.dumps(run(impl, ids), ensure_ascii=False))
        return

    print("id  payload                                          old -> new")
    table = {}
    for i, payload in CASES.items():
        o = result_of(child("old", [i]))
        n = result_of(child("new", [i]))
        table[i] = (o, n)
        flag = "" if o == n else "   <== 变化"
        print(f"{i:>2}  {json.dumps(payload, ensure_ascii=False):<48} {o!r} -> {n!r}{flag}")

    # 三条真实种子行: 新旧必须一致 (本条是合入判断的核心)
    for i in SEED_IDS:
        assert table[i][0] == table[i][1], (i, table[i])
    assert table[1] == ("12.50", "12.50"), table[1]
    assert table[2] == ("9.99", "9.99"), table[2]
    assert table[3] == (None, None), table[3]

    # 已证明的差异: 旧版把非数字文本原样透出, 新版抛 ValueError
    assert table[8] == ("abc", "ERROR ValueError"), table[8]
    assert table[9] == ("9,99", "ERROR ValueError"), table[9]
    # 空白串: 旧版导出空串, 新版导出 null
    assert table[6] == ("", None), table[6]
    # v2 amount 缺失/为空时, 新版会退回去读 amount_str
    assert table[10] == (None, "9.99"), table[10]
    # 纯数字文本只差前导 0
    assert table[7] == ("012.50", "12.50"), table[7]
    # 两边都会抛的情形
    assert table[12] == ("ERROR ValueError", "ERROR ValueError"), table[12]
    # 非字符串 amount: 新旧都在 .strip() 上炸, 不是本次变更引起
    assert table[13] == table[14] == ("ERROR AttributeError", "ERROR AttributeError"), (table[13], table[14])

    # 整批语义: 一条坏数据让整次导出失败, 旧版不会.
    # 12-14 号新旧都炸, 与本次变更无关, 只看 1-11.
    batch_ids = list(range(1, 12))
    old_all = child("old", batch_ids)
    new_all = child("new", batch_ids)
    print("\n整批 11 行 (排除新旧都炸的 12 号):")
    print("  old:", json.dumps(old_all, ensure_ascii=False)[:220])
    print("  new:", json.dumps(new_all, ensure_ascii=False)[:220])
    assert "rows" in old_all, old_all
    assert new_all.get("error", "").startswith("ValueError"), new_all

    print("\nOK: 比较完成, 上面的差异项全部成立")


if __name__ == "__main__":
    main()
