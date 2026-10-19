# F4 证明: HEAD 与 HEAD~1 导出的金额值是否变化; 本次提交是否改变金额解析行为.
# 判定错则以非零退出. 用两份副本各自树内的真实代码 (vendored amountlib + app.orders) 跑.
import decimal
import json
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD = ROOT / "repo"
BASE = ROOT / "base"


def load_tree(tree: pathlib.Path):
    """把指定副本的树放到 sys.path 最前, 导入它自己的 amountlib 与 app.orders."""
    for name in ("amountlib", "app"):
        sys.modules.pop(name, None)
        sys.modules.pop(name + ".core", None)
        sys.modules.pop(name + ".legacy", None)
        sys.modules.pop(name + ".orders", None)
    sys.path.insert(0, str(tree))
    import amountlib
    from app import orders as orders_mod

    return amountlib, orders_mod


def read_db(tree: pathlib.Path):
    conn = sqlite3.connect(tree / "var" / "orders.db")
    try:
        return conn.execute("SELECT id, payload FROM orders ORDER BY id").fetchall()
    finally:
        conn.close()


results = {}
for label, tree in (("HEAD", HEAD), ("HEAD~1", BASE)):
    amountlib, orders_mod = load_tree(tree)
    # 断言运行环境: 各树用的都是 vendored amountlib 2.4.0
    assert amountlib.VERSION == "2.4.0", f"{label}: amountlib 版本应为 2.4.0, 实际 {amountlib.VERSION}"
    assert amountlib.__file__ is not None and str(tree) in amountlib.__file__, (
        f"{label}: 导入的不是该树的 amountlib: {amountlib.__file__}"
    )
    # 断言: 没有任何地方注册过 v1 格式化函数, v1 分支只能走 parse_amount 回退
    from amountlib import legacy as legacy_mod

    assert legacy_mod._FORMATTERS == {}, f"{label}: _FORMATTERS 应为空, 实际 {legacy_mod._FORMATTERS}"
    # v1/v2 分支与回退的真实行为
    assert amountlib.resolve_amount({"schema": "v2", "amount": "12.50"}) == decimal.Decimal("12.50")
    assert amountlib.resolve_amount({"schema": "v1", "amount_str": "9.99"}) is None
    assert amountlib.parse_amount("") is None
    assert amountlib.parse_amount(None) is None
    assert amountlib.parse_amount("9.99") == decimal.Decimal("9.99")
    try:
        amountlib.parse_amount("abc")
        raise AssertionError("parse_amount('abc') 应抛 ValueError")
    except ValueError:
        pass
    # 用该树自己的 read_orders 读该树自己的 DB
    rows = orders_mod.read_orders(sqlite3.connect(tree / "var" / "orders.db"))
    results[label] = rows
    print(f"{label}: read_orders -> {rows}")

# 断言: 逐 id 金额值完全一致 (只比金额值, 不比键名)
head_by_id = {r["id"]: r["amount_value"] for r in results["HEAD"]}
base_by_id = {r["id"]: r["amount"] for r in results["HEAD~1"]}
assert set(head_by_id) == {1, 2, 3}, f"应有 id 1/2/3, 实际 {sorted(head_by_id)}"
assert head_by_id == base_by_id, f"金额值发生变化! HEAD={head_by_id} HEAD~1={base_by_id}"
assert head_by_id == {1: "12.50", 2: "9.99", 3: None}, f"金额值与种子数据预期不符: {head_by_id}"

# 再核对 DB 里的原始 payload 与 seed.py 的种子一致 (两份副本同一份 db/seed.py)
seed_src = (HEAD / "db" / "seed.py").read_text()
assert seed_src == (BASE / "db" / "seed.py").read_text(), "两份副本的 db/seed.py 应相同"
for tree in (HEAD, BASE):
    rows = read_db(tree)
    payloads = [json.loads(r[1]) for r in rows]
    assert payloads == [
        {"schema": "v2", "amount": "12.50"},
        {"schema": "v1", "amount_str": "9.99"},
        {"schema": "v1", "amount_str": ""},
    ], f"{tree}: DB payload 与种子不符: {payloads}"

print("F4 证实: id 1/2/3 金额值 HEAD 与 HEAD~1 完全一致: '12.50', '9.99', None.")
print("  v1 payload (id 2/3) 因无人注册格式化函数, resolve_amount 返回 None, 走 parse_amount 回退.")
print("  本次提交只改导出键名与文件外层, 未改 amountlib 与解析路径.")
