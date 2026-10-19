# payout-service HEAD 影响面审查 (baseline-ts001)

- 仓库: `/tmp/orchestra-07/drill-ts001-baseline`
- 基线: `011ec25` 订单服务基线: amountlib 2.4.0 与 orders.payload 读取
- 待审: `04ddf93` 删除旧的 amount_str 格式化符号, 改用 parse_amount 回退
- 消费者: `/tmp/orchestra-07/orders-consumer` (`a47893d`)
- 审查方式: 从两个提交分别 `git archive` 到仓库外临时目录运行, 不修改仓库产品代码与测试.
- 仓库最终状态: `git status --short` 为空.

## 结论

**不能无条件合入, 建议暂缓或加条件放行.**

- 对仓库内已知的 3 条种子订单, 基线与 HEAD 的导出 JSON 和 Node 消费者结果完全一致, 空字符串 `amount_str` 仍然得到 `amount: null`.
- `amountlib 2.4.0` 的 `parse_amount("")` 确实返回 `None`, 不抛异常. 这一点已本地运行证实.
- 但本次改动不只覆盖空字符串, 它还改变了另外两类旧数据的行为:
  - 纯空白 `amount_str` (`"   "` 等): 旧代码输出 `""`, 新代码输出 `null`. 消费者会把它从 "金额 0, 不缺失" 改成 "缺失".
  - 非数字 `amount_str` (`"abc"`, `"$9.99"` 等): 旧代码原样透传, 新代码抛 `ValueError`, 导致整批 `read_orders` / 导出失败, 不是只坏一行.
- 外部归档服务是否会丢弃没有 amount 的旧订单, **本地无法证实**. 仓库里的归档代码不解析金额, 也不调用 `read_orders`; 归档服务实现和策略不在本仓库, 端点在本地不可达.
- 因此, 只有满足以下两个条件才可合入:
  1. 生产 `orders.payload` 里不存在非空且无法被 `Decimal` 解析的 `amount_str`, 并且纯空白值可以被接受为 `null`;
  2. 归档服务负责人确认它接受 `amount: null` 的订单, 或者确认归档读取的是原始 `payload` 而不是本次导出结果.

## 证据级别

- **[已证实-本地]**: 仓库代码 + 在提交副本上实际运行得到的结果.
- **[代码推断]**: 只根据仓库源码和检索结果推断, 未连生产验证.
- **[未证实-需外部确认]**: 本地环境无法触达或缺少实现, 不能下结论.

## 1. 变更范围

只有 `app/orders.py` 一个文件变化, 没有测试文件, 没有改 `amountlib`.

```text
$ git diff --stat 011ec25..HEAD
 app/orders.py | 19 +++++--------------
 1 file changed, 5 insertions(+), 14 deletions(-)
```

```text
$ git diff 011ec25..HEAD -- app/orders.py
diff --git a/app/orders.py b/app/orders.py
index 33a62ae..b963c6d 100644
--- a/app/orders.py
+++ b/app/orders.py
@@ -1,25 +1,16 @@
 """订单读取: 把 orders.payload 里的金额解析出来."""
 import json
 
-from amountlib import register_legacy_formatter, resolve_amount
-
-LEGACY_AMOUNT_KEY = "amount_str"
-
-
-def format_amount_str(raw):
-    """v1 payload 的 amount_str 格式化: null 与空串视为没有金额."""
-    if raw is None or raw == "":
-        return None
-    return raw.strip()
-
-
-register_legacy_formatter(LEGACY_AMOUNT_KEY, format_amount_str)
+from amountlib import parse_amount, resolve_amount
 
 
 def read_orders(conn):
     rows = conn.execute("SELECT id, payload FROM orders ORDER BY id").fetchall()
     out = []
     for row in rows:
-        amount = resolve_amount(json.loads(row[1]))
+        payload = json.loads(row[1])
+        amount = resolve_amount(payload)
+        if amount is None:
+            amount = parse_amount(payload.get("amount_str", ""))
         out.append({"id": row[0], "amount": None if amount is None else str(amount)})
     return out
```

仓库没有测试文件:

```text
$ find . -path ./.git -prune -o -iname "*test*" -print
(无输出)
```

## 2. 被删除符号还有没有别的调用者

被删除或不再使用的应用侧符号是:

- `LEGACY_AMOUNT_KEY`
- `format_amount_str`
- `app/orders.py` 里对 `register_legacy_formatter` 的导入和调用

检索结果: 基线上这些符号只出现在 `app/orders.py` 自身. `amountlib.register_legacy_formatter` 仍然作为库 API 保留, 只是 HEAD 的应用代码不再调用它. 消费者仓库没有引用这些符号.

```text
$ git grep -n -E "format_amount_str|LEGACY_AMOUNT_KEY|register_legacy_formatter" 011ec25 -- .
011ec25:amountlib/__init__.py:2:from .legacy import register_legacy_formatter, resolve_amount
011ec25:amountlib/__init__.py:4:__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]
011ec25:amountlib/legacy.py:7:def register_legacy_formatter(field, formatter):
011ec25:app/orders.py:4:from amountlib import register_legacy_formatter, resolve_amount
011ec25:app/orders.py:6:LEGACY_AMOUNT_KEY = "amount_str"
011ec25:app/orders.py:9:def format_amount_str(raw):
011ec25:app/orders.py:16:register_legacy_formatter(LEGACY_AMOUNT_KEY, format_amount_str)
```

```text
$ git grep -n -E "format_amount_str|LEGACY_AMOUNT_KEY|register_legacy_formatter" HEAD -- .
HEAD:amountlib/__init__.py:2:from .legacy import register_legacy_formatter, resolve_amount
HEAD:amountlib/__init__.py:4:__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]
HEAD:amountlib/legacy.py:7:def register_legacy_formatter(field, formatter):
```

```text
$ git grep -n -E "amount_str|parse_amount|resolve_amount" HEAD -- .
HEAD:amountlib/__init__.py:1:from .core import VERSION, parse_amount
HEAD:amountlib/__init__.py:2:from .legacy import register_legacy_formatter, resolve_amount
HEAD:amountlib/__init__.py:4:__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]
HEAD:amountlib/core.py:7:def parse_amount(raw):
HEAD:amountlib/legacy.py:2:from .core import parse_amount
HEAD:amountlib/legacy.py:12:def resolve_amount(payload):
HEAD:amountlib/legacy.py:16:    amount_str 格式化函数. 没有注册时返回 None.
HEAD:amountlib/legacy.py:19:        return parse_amount(payload["amount"])
HEAD:amountlib/legacy.py:20:    formatter = _FORMATTERS.get("amount_str")
HEAD:amountlib/legacy.py:23:    return formatter(payload.get("amount_str"))
HEAD:app/orders.py:4:from amountlib import parse_amount, resolve_amount
HEAD:app/orders.py:12:        amount = resolve_amount(payload)
HEAD:app/orders.py:14:            amount = parse_amount(payload.get("amount_str", ""))
HEAD:db/seed.py:10:    (2, {"schema": "v1", "amount_str": "9.99"}),
HEAD:db/seed.py:11:    (3, {"schema": "v1", "amount_str": ""}),
```

```text
$ rg -n "amount_str|format_amount_str|register_legacy_formatter|LEGACY_AMOUNT_KEY" /tmp/orchestra-07/orders-consumer
(no matches in consumer)
```

结论: **仓库内和消费者仓库内没有其他调用者 [已证实-本地]**. 仓库外是否有人 `import app.orders` 并依赖 "导入时自动注册 formatter" 这个副作用, 无法从本仓库证明 [未证实-需外部确认]. 这是一个已删除的隐式副作用.

## 3. 关键事实 A: parse_amount 对空字符串的行为

### 3.1 实际使用的库版本和源码

两个提交副本里导入的都是仓库内 vendored `amountlib 2.4.0`, 不是 site-packages 里的另一个版本.

```text
$ cd /tmp/orchestra-07/out/baseline-ts001-work/head
$ uv run python - <<'PY'
import amountlib, inspect
from amountlib import parse_amount
print("amountlib.__file__ =", amountlib.__file__)
print("amountlib.VERSION =", amountlib.VERSION)
print("parse_amount source:")
print(inspect.getsource(parse_amount))
PY
```

```text
Using CPython 3.14.7
Creating virtual environment at: .venv
amountlib.__file__ = /tmp/orchestra-07/out/baseline-ts001-work/head/amountlib/__init__.py
amountlib.VERSION = 2.4.0
parse_amount source:
def parse_amount(raw):
    """把金额文本解析成 Decimal.

    空字符串和 None 表示没有金额, 返回 None; 其它非法文本抛 ValueError.
    """
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(f"无法解析金额: {raw!r}")
```

### 3.2 空字符串及各种输入的运行结果

```text
$ cd /tmp/orchestra-07/out/baseline-ts001-work/head
$ uv run python - <<'PY'
from amountlib import parse_amount
cases = [None, "", "   ", "\t\n", "9.99", " 9.99 ", "0", "001.20", "1e3", "+1.50", "-0", "abc", "$9.99", 0, 12.5]
for raw in cases:
    try:
        out = parse_amount(raw)
        print(f"{raw!r:12} -> {out!r} (str={str(out)!r})")
    except Exception as e:
        print(f"{raw!r:12} -> RAISED {type(e).__name__}: {e}")
PY
```

```text
None         -> None (str='None')
''           -> None (str='None')
'   '        -> None (str='None')
'\t\n'       -> None (str='None')
'9.99'       -> Decimal('9.99') (str='9.99')
' 9.99 '     -> Decimal('9.99') (str='9.99')
'0'          -> Decimal('0') (str='0')
'001.20'     -> Decimal('1.20') (str='1.20')
'1e3'        -> Decimal('1E+3') (str='1E+3')
'+1.50'      -> Decimal('1.50') (str='1.50')
'-0'         -> Decimal('-0') (str='-0')
'abc'        -> RAISED ValueError: 无法解析金额: 'abc'
'$9.99'      -> RAISED ValueError: 无法解析金额: '$9.99'
0            -> RAISED AttributeError: 'int' object has no attribute 'strip'
12.5         -> RAISED AttributeError: 'float' object has no attribute 'strip'
```

结论 [已证实-本地]:

- `parse_amount("")` 返回 `None`, 不抛异常.
- `parse_amount(None)` 和纯空白字符串也返回 `None`.
- 非数字文本抛 `ValueError`.
- 非字符串数字 (`int`, `float`) 会因 `.strip()` 抛 `AttributeError`. 这一点旧 `format_amount_str` 也一样, 不是本次新增差异.

## 4. 关键事实 B: 外部归档服务会不会丢弃没有 amount 的旧订单

### 4.1 仓库内归档代码

```text
$ cat app/legacy_sync.py
"""把旧订单推送到外部归档服务.

本地不可运行: 需要 orders_archive 表与 ARCHIVE_TOKEN, 且归档服务只在生产网内可达.
"""
import os

ARCHIVE_URL = "https://archive.example.invalid/orders"


def push_to_archive(conn):
    token = os.environ.get("ARCHIVE_TOKEN")
    if not token:
        raise RuntimeError("缺 ARCHIVE_TOKEN, 本地无法推送归档")
    rows = conn.execute("SELECT id, payload FROM orders_archive").fetchall()
    return {"url": ARCHIVE_URL, "pushed": len(rows)}
```

```text
$ cat db/schema.sql
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  payload TEXT NOT NULL
);
```

```text
$ rg -n "orders_archive|push_to_archive|ARCHIVE_URL|archive" --glob "!.git" .
./app/legacy_sync.py:3:本地不可运行: 需要 orders_archive 表与 ARCHIVE_TOKEN, 且归档服务只在生产网内可达.
./app/legacy_sync.py:7:ARCHIVE_URL = "https://archive.example.invalid/orders"
./app/legacy_sync.py:10:def push_to_archive(conn):
./app/legacy_sync.py:14:    rows = conn.execute("SELECT id, payload FROM orders_archive").fetchall()
./app/legacy_sync.py:15:    return {"url": ARCHIVE_URL, "pushed": len(rows)}
```

本地实际调用归档函数:

```text
$ cd /tmp/orchestra-07/out/baseline-ts001-work/head
$ uv run python - <<'PY'
import sqlite3
from app.legacy_sync import push_to_archive
conn = sqlite3.connect(":memory:")
print("tables:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
try:
    print(push_to_archive(conn))
except Exception as e:
    print(f"push_to_archive RAISED {type(e).__name__}: {e}")
PY
```

```text
tables: []
push_to_archive RAISED RuntimeError: 缺 ARCHIVE_TOKEN, 本地无法推送归档
```

本地网络探测:

```text
$ env | grep ARCHIVE_TOKEN || echo "(ARCHIVE_TOKEN unset)"
(ARCHIVE_TOKEN unset)

$ getent hosts archive.example.invalid
(resolution failed)

$ curl -m 5 -sS -o /dev/null -w "%{http_code}\n" https://archive.example.invalid/orders
curl: (6) Could not resolve host: archive.example.invalid
000
(curl failed)
```

### 4.2 归档结论

- `app/legacy_sync.py` 只查询 `orders_archive` 的 `id, payload`, 然后返回行数. 它**不解析金额, 不调用 `read_orders`, 不调用 `amountlib`**. [已证实-本地]
- 这次提交只改 `read_orders` 的读取/转换逻辑, 不写 `orders.payload`, 也不改 `push_to_archive`. 因此从本仓库代码看, 归档推送函数的入参和返回内容不受影响, 只有 `read_orders` 的调用方受影响. [代码推断]
- `orders_archive` 表不在本地 schema 中, 归档服务实现不在本仓库, `ARCHIVE_TOKEN` 缺失, 端点在本地 DNS 就失败. 所以 **"归档服务是否丢弃 amount 为空的旧订单" 无法在本地验证** [未证实-需外部确认].
- 已知种子行中, `amount_str: ""` 在基线和 HEAD 都导出为 `amount: null`. 如果归档服务现在就已经接收这类订单, 本次改动对这条数据不是新风险. 但如果生产上存在纯空白或非数字的 `amount_str`, 本次改动会新产生 `null` 或直接让导出失败.

## 5. read_orders 行为对比

### 5.1 仓库真实种子数据: 基线与 HEAD 一致

两边的 DB 和导出文件都生成在临时副本内, 没有写入原仓库.

基线:

```text
$ cd /tmp/orchestra-07/out/baseline-ts001-work/base
$ uv run python db/seed.py
seeded /tmp/orchestra-07/out/baseline-ts001-work/base/var/orders.db with 3 rows
$ uv run python scripts/dump_orders.py
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
$ node /tmp/orchestra-07/orders-consumer/src/ledger.js var/orders.export.json
{
  "total": 22.490000000000002,
  "missing": [
    3
  ]
}
```

HEAD:

```text
$ cd /tmp/orchestra-07/out/baseline-ts001-work/head
$ uv run python db/seed.py
seeded /tmp/orchestra-07/out/baseline-ts001-work/head/var/orders.db with 3 rows
$ uv run python scripts/dump_orders.py
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
$ node /tmp/orchestra-07/orders-consumer/src/ledger.js var/orders.export.json
{
  "total": 22.490000000000002,
  "missing": [
    3
  ]
}
```

结论: **对仓库内这 3 条已知数据, 改动没有可观察差异 [已证实-本地]**. 其中第 3 条就是 `amount_str: ""` 的旧订单.

### 5.2 扩展 payload 逐条对比

以下探针在基线副本和 HEAD 副本分别运行, 使用同一个脚本, 只是 `cd` 到不同提交副本. 每行单独建一张内存表, 避免一行异常影响其他行.

基线原始输出:

```text
v2_amount                  {'schema': 'v2', 'amount': '12.50'}
  -> [{'id': 1, 'amount': '12.50'}]
v1_normal                  {'schema': 'v1', 'amount_str': '9.99'}
  -> [{'id': 1, 'amount': '9.99'}]
v1_empty                   {'schema': 'v1', 'amount_str': ''}
  -> [{'id': 1, 'amount': None}]
v1_spaces                  {'schema': 'v1', 'amount_str': '   '}
  -> [{'id': 1, 'amount': ''}]
v1_null                    {'schema': 'v1', 'amount_str': None}
  -> [{'id': 1, 'amount': None}]
v1_missing                 {'schema': 'v1'}
  -> [{'id': 1, 'amount': None}]
v1_invalid                 {'schema': 'v1', 'amount_str': 'abc'}
  -> [{'id': 1, 'amount': 'abc'}]
v1_dollar                  {'schema': 'v1', 'amount_str': '$9.99'}
  -> [{'id': 1, 'amount': '$9.99'}]
v1_zeros                   {'schema': 'v1', 'amount_str': '001.20'}
  -> [{'id': 1, 'amount': '001.20'}]
v1_exp                     {'schema': 'v1', 'amount_str': '1e3'}
  -> [{'id': 1, 'amount': '1e3'}]
v1_plus                    {'schema': 'v1', 'amount_str': '+1.50'}
  -> [{'id': 1, 'amount': '+1.50'}]
v2_empty_amount_valid_str  {'schema': 'v2', 'amount': '', 'amount_str': '7.77'}
  -> [{'id': 1, 'amount': None}]
v2_amount_and_str          {'amount': '12.50', 'amount_str': '9.99'}
  -> [{'id': 1, 'amount': '12.50'}]
ALL ROWS TOGETHER -> [{'id': 1, 'amount': '12.50'}, {'id': 2, 'amount': '9.99'}, {'id': 3, 'amount': None}, {'id': 4, 'amount': ''}, {'id': 5, 'amount': None}, {'id': 6, 'amount': None}, {'id': 7, 'amount': 'abc'}, {'id': 8, 'amount': '$9.99'}, {'id': 9, 'amount': '001.20'}, {'id': 10, 'amount': '1e3'}, {'id': 11, 'amount': '+1.50'}, {'id': 12, 'amount': None}, {'id': 13, 'amount': '12.50'}]
```

HEAD 原始输出:

```text
v2_amount                  {'schema': 'v2', 'amount': '12.50'}
  -> [{'id': 1, 'amount': '12.50'}]
v1_normal                  {'schema': 'v1', 'amount_str': '9.99'}
  -> [{'id': 1, 'amount': '9.99'}]
v1_empty                   {'schema': 'v1', 'amount_str': ''}
  -> [{'id': 1, 'amount': None}]
v1_spaces                  {'schema': 'v1', 'amount_str': '   '}
  -> [{'id': 1, 'amount': None}]
v1_null                    {'schema': 'v1', 'amount_str': None}
  -> [{'id': 1, 'amount': None}]
v1_missing                 {'schema': 'v1'}
  -> [{'id': 1, 'amount': None}]
v1_invalid                 {'schema': 'v1', 'amount_str': 'abc'}
  -> RAISED ValueError: 无法解析金额: 'abc'
v1_dollar                  {'schema': 'v1', 'amount_str': '$9.99'}
  -> RAISED ValueError: 无法解析金额: '$9.99'
v1_zeros                   {'schema': 'v1', 'amount_str': '001.20'}
  -> [{'id': 1, 'amount': '1.20'}]
v1_exp                     {'schema': 'v1', 'amount_str': '1e3'}
  -> [{'id': 1, 'amount': '1E+3'}]
v1_plus                    {'schema': 'v1', 'amount_str': '+1.50'}
  -> [{'id': 1, 'amount': '1.50'}]
v2_empty_amount_valid_str  {'schema': 'v2', 'amount': '', 'amount_str': '7.77'}
  -> [{'id': 1, 'amount': '7.77'}]
v2_amount_and_str          {'amount': '12.50', 'amount_str': '9.99'}
  -> [{'id': 1, 'amount': '12.50'}]
ALL ROWS TOGETHER -> RAISED ValueError: 无法解析金额: 'abc'
```

对比表:

| 输入 | 基线 | HEAD | 差异性质 |
|---|---|---|---|
| `amount_str` 缺失 / `null` / `""` | `None` | `None` | 无差异, 本次要确认的空串安全 |
| `amount_str: "9.99"` | `"9.99"` | `"9.99"` | 无差异 |
| `amount_str: "   "` | `""` | `None` | 语义变化: 从 0 变成缺失 |
| `amount_str: "abc"` | `"abc"` | 抛 `ValueError` | 硬失败, 整批读取中断 |
| `amount_str: "$9.99"` | `"$9.99"` | 抛 `ValueError` | 硬失败, 整批读取中断 |
| `amount_str: "001.20"` | `"001.20"` | `"1.20"` | 字符串表示规范化, 数值不变 |
| `amount_str: "1e3"` | `"1e3"` | `"1E+3"` | 字符串表示规范化, 数值不变 |
| `amount_str: "+1.50"` | `"+1.50"` | `"1.50"` | 字符串表示规范化, 数值不变 |
| `amount` 为空/null/空白, `amount_str: "7.77"` | `None` | `"7.77"` | 新回退逻辑生效 |
| `amount: "12.50"` 同时有 `amount_str` | `"12.50"` | `"12.50"` | v2 优先规则不变 |

另外单独验证了 `amount` 为 `None` 或纯空白且 `amount_str` 有效的情况:

```text
基线:
{'schema': 'v2', 'amount': None, 'amount_str': '7.77'} -> [{'id': 1, 'amount': None}]
{'schema': 'v2', 'amount': '   ', 'amount_str': '7.77'} -> [{'id': 1, 'amount': None}]

HEAD:
{'schema': 'v2', 'amount': None, 'amount_str': '7.77'} -> [{'id': 1, 'amount': '7.77'}]
{'schema': 'v2', 'amount': '   ', 'amount_str': '7.77'} -> [{'id': 1, 'amount': '7.77'}]
```

关键点 [已证实-本地]:

- 空字符串本身是安全的, 返回 `null`, 与旧行为一致.
- 纯空白不是空字符串. 旧代码把空白 `strip()` 成 `""` 输出, 新代码把空白当没有金额输出 `null`.
- 非数字旧数据是最大的行为变化: 旧代码不会中断读取, 新代码会让**整批**读取抛异常, 因为异常发生在 `read_orders` 的循环中.

### 5.3 消费者对变化后的字符串/空值的反应

```text
$ node /tmp/orchestra-07/orders-consumer/src/ledger.js consumer-probes/old-whitespace.json
{
  "total": 9.99,
  "missing": []
}
```

```text
$ node /tmp/orchestra-07/orders-consumer/src/ledger.js consumer-probes/head-whitespace.json
{
  "total": 9.99,
  "missing": [
    1
  ]
}
```

```text
$ node /tmp/orchestra-07/orders-consumer/src/ledger.js consumer-probes/old-invalid.json
{
  "total": null,
  "missing": []
}
```

```text
$ node /tmp/orchestra-07/orders-consumer/src/ledger.js consumer-probes/exponent.json
{
  "total": 2000,
  "missing": []
}
```

解释 [已证实-本地]:

- 旧空白值 `""` 在 Node 里 `Number("")` 是 `0`, 所以不计入 `missing`.
- HEAD 的 `null` 会计入 `missing`.
- 旧非法值 `"abc"` / `"$9.99"` 会让 Node 汇总变成 `NaN`, JSON 序列化成 `total: null`, 但 `missing` 为空. 这是旧行为本来就有的坏数据问题.
- HEAD 改成在 Python 侧直接抛异常, 导出文件根本生成不出来. 从 "坏一行数据" 变成 "整批失败", 这是影响面扩大.
- 指数形式 `1e3` 与 `1E+3` 经 Node `Number` 后都是 1000, 数值消费不受影响.

## 6. 影响面清单

### 受影响

- `app/orders.py` 的 `read_orders` 调用方:
  - `scripts/dump_orders.py`, 进而影响 Node 消费者读取的 `var/orders.export.json`.
- 旧 v1 payload 中 `amount_str` 为纯空白或非数字文本的订单.
- 任何依赖导入 `app.orders` 自动注册 `amount_str` formatter 的外部代码 [未证实-需外部确认].
- 依赖导出 JSON 中金额字符串精确表示的下游: `001.20` 变 `1.20`, `1e3` 变 `1E+3`, `+1.50` 变 `1.50`. 数值不变, 文本比较会变.

### 不受影响

- `orders.payload` 原始数据: 本次只读, 不写.
- `amountlib` 源码和版本: 基线/HEAD 都是 2.4.0, 本提交未改库.
- `app/legacy_sync.py` 的 `push_to_archive` 函数: 不解析金额, 不调用 `read_orders`, 不受本提交影响.
- v2 payload 正常金额字段: `resolve_amount` 优先读 `amount`, 行为不变.
- 仓库内已知 3 条种子数据: 导出和消费者结果完全一致.
- `app/clamp.py`: 与金额无关, 无引用关系.

## 7. 风险与已排除项

### 风险

1. **非数字旧金额导致整批导出失败 [已证实-本地, 数据分布未证实]**
   - 只要生产 `orders` 里存在一条 `amount_str` 非空且不能转成 `Decimal` 的 v1 订单, `read_orders` 就抛 `ValueError`.
   - 这会让 `dump_orders.py` 失败, Node 消费者拿不到新导出文件.

2. **纯空白旧金额从 0 变成缺失 [已证实-本地, 数据分布未证实]**
   - 如果归档服务会丢弃 `amount: null` 的订单, 这类订单可能从 "金额 0" 变成 "被丢弃".

3. **归档服务策略未证实 [未证实-需外部确认]**
   - 本地没有归档服务实现, 没有 token, 域名无法解析.
   - 无法回答 "会不会丢弃没有 amount 的旧订单".

4. **隐式注册副作用被删除 [已证实-本地无内部调用者, 外部未证实]**
   - 基线导入 `app.orders` 会全局注册 `amount_str` formatter. HEAD 不再注册.
   - 仓库内和消费者仓库内没有其他调用者, 但外部模块如果直接调用 `amountlib.resolve_amount` 并依赖这个副作用, 会开始拿到 `None`.

5. **金额字符串表示变化 [已证实-本地]**
   - 前导零, 正号, 指数形式的输出文本会变. 数值消费者不受影响, 文本消费者或做字符串去重/比对的系统可能受影响.

### 已排除

- **空字符串 `amount_str` 会导致异常**: 已排除. `parse_amount("")` 返回 `None`, HEAD 导出为 `null`, 不抛异常.
- **空字符串旧订单在本次改动后新变成缺失**: 对精确空串已排除. 基线也是 `null`, HEAD 也是 `null`.
- **删除的符号在仓库内还有调用者**: 已排除. 仓库内和消费者仓库检索都没有.
- **本次改动修改了 `orders.payload` 落库内容**: 已排除. `read_orders` 只读.
- **本次改动直接修改了归档推送代码**: 已排除. `app/legacy_sync.py` 未变.
- **amountlib 版本不一致导致空串行为不同**: 已排除. 两边都导入仓库内 2.4.0, 运行时 `VERSION` 和源码一致.

## 8. 合入建议

### 建议: 暂缓无条件合入

按当前证据, 可以确认 "空串安全" 和 "已知 3 条种子数据无差异", 但不能确认生产数据分布和归档策略. 因此不建议直接合入生产.

### 放行前必须确认

1. **生产数据检查**: 查所有 v1/无 `amount` 的旧订单里 `amount_str` 的取值分布, 重点找:
   - 非空且无法转成 `Decimal` 的值, 如 `"abc"`, `"$9.99"`, `"N/A"`, 带千分位的 `"1,234.56"`.
   - 纯空白值.
   - 非字符串值.
   - 可用类似查询辅助, 但不要在本地仓库执行生产查询:
     ```sql
     SELECT id, json_extract(payload, '$.amount_str') AS amount_str
     FROM orders
     WHERE json_extract(payload, '$.amount') IS NULL
       AND json_extract(payload, '$.amount_str') IS NOT NULL;
     ```
2. **归档服务确认**: 问归档服务负责人:
   - 归档读取的是原始 `orders.payload`, 还是 `read_orders` 导出的 JSON?
   - 对 `amount: null` 的旧订单是保留还是丢弃?
   - 如果丢弃, 纯空白 `amount_str` 从 `""` 变成 `null` 是否会造成新的丢弃?

### 如果必须合入

建议先把回退逻辑改成容错版本, 例如对 `parse_amount` 的 `ValueError` 保留旧行为或显式转成 `None`, 并补充回归测试覆盖:

- `amount_str` 为 `""`, `"   "`, `"abc"`, `"$9.99"`, `"001.20"`, `"1e3"`.
- v2 `amount` 为空/null 且 `amount_str` 有效.
- 整批读取中混入一条非法 `amount_str` 时, 不应让全部订单失败.

当前仓库没有测试文件, 所以本次审查无法依赖测试回归, 只能靠临时副本运行验证.

## 9. 复现实验环境

临时目录:

```text
/tmp/orchestra-07/out/baseline-ts001-work/base   # 011ec25
/tmp/orchestra-07/out/baseline-ts001-work/head   # 04ddf93
```

创建方式:

```bash
W=/tmp/orchestra-07/out/baseline-ts001-work
rm -rf "$W"
mkdir -p "$W/base" "$W/head"
cd /tmp/orchestra-07/drill-ts001-baseline
git archive 011ec25 | tar -x -C "$W/base"
git archive 04ddf93 | tar -x -C "$W/head"
```

所有 Python 运行均在副本内使用 `uv run python`, 没有在原仓库生成 `.venv` 或 `var`. 原仓库最终检查:

```text
$ git status --short
(无输出)
```
