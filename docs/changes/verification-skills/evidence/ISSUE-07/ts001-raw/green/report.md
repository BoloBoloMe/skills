# blast-radius 交接: 04ddf93 删除 amount_str 格式化符号, 改用 parse_amount 回退

仓库: /tmp/orchestra-07/drill-ts001-green (HEAD 04ddf93, 父提交 011ec25)
执行者: green-ts001 会话
只读范围: 本仓库 + 仓库内 .agents/skills/blast-radius/SKILL.md; 未读 /home/bolo/Workspace, 未读 orders-consumer 仓库.
仓库状态: 调查结束后 `git status --porcelain` 为空 (调查中 uv 生成的 .venv/uv.lock 已删除), 未改产品代码与测试.

## 1. 做了什么

1. 读 HEAD diff, 父提交版本, 全部相关源码 (amountlib, app, db, scripts).
2. 用 git log/blame 定位两个符号的来历, 确认仓库只有 2 个提交, 没有 PR 材料可查 (来源限制).
3. 确认运行环境实际加载的是仓库内 amountlib 2.4.0, 不存在 site-packages 里的同名包抢先.
4. 写两个证据脚本 (放仓库外), 逐条断言关键事实, 并对 base/head 两棵树逐行对比 read_orders 输出.
5. 用真实入口 db/seed.py + scripts/dump_orders.py 跑正常种子数据和一条非法金额数据, 对比导出 JSON.
6. 尝试本地运行归档推送, 证明本地不可达.
7. 全仓 grep 被删符号, 确认调用者.

## 2. 关键安全事实与证据级别

### 事实 A: parse_amount 对空字符串返回 None (等级 4, 实际跑过)

源码位置: amountlib/core.py:12-16

```python
if raw is None:
    return None
text = raw.strip()
if not text:
    return None
```

证据: 在 HEAD 树里导入实际使用的库并断言, 失败会 assert 报错并非零退出:

```
python: 3.14.7
amountlib.__file__: /tmp/orchestra-07/out/green-ts001/head-tree/amountlib/__init__.py
amountlib.VERSION: 2.4.0
parse_amount('') -> None
parse_amount(None) -> None
parse_amount('   ') -> None
parse_amount('\t\n') -> None
parse_amount('9.99') -> Decimal('9.99') ; str() -> '9.99'
parse_amount(' 9.99 ') -> Decimal('9.99') ; str() -> '9.99'
parse_amount('0012.50') -> Decimal('12.50') ; str() -> '12.50'
parse_amount('1e3') -> Decimal('1E+3') ; str() -> '1E+3'
parse_amount('1,234.50') -> ValueError: 无法解析金额: '1,234.50'
OK: 版本与空串行为断言全部通过
EXIT=0
```

为什么它决定安全: 旧代码的空串分支返回 None, 新代码 parse_amount("") 也返回 None, 所以种子数据里 id=3 的 `amount_str: ""` 不会变成 0 或抛错, 导出的 JSON 不变. 这是本次"大多数旧订单安全"的核心.

停在这一级的理由: 已到 4 级; 没有生产应用可跑, 所以不是 5 级.

### 事实 B: 三条已知种子订单的导出结果完全一致 (等级 4, 真实入口实跑)

对 base 树 (011ec25) 和 head 树 (04ddf93) 各跑 db/seed.py + scripts/dump_orders.py:

```
base:
seeded /tmp/orchestra-07/out/green-ts001/base-tree/var/orders.db with 3 rows
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
head:
seeded /tmp/orchestra-07/out/green-ts001/head-tree/var/orders.db with 3 rows
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
diff: IDENTICAL
```

停下的理由: 种子数据只有 3 行, 不代表生产数据分布; 生产库 var/orders.db 不在仓库里.

### 事实 C: 外部归档服务行为本地不可证实 (等级 1-2, 明确未证实)

源码: app/legacy_sync.py:10-15 要求 ARCHIVE_TOKEN 且读 orders_archive 表; schema.sql 只有 orders 表; 域名 archive.example.invalid 不可解析.

实跑:

```
无 token -> EXIT=1
RuntimeError: 缺 ARCHIVE_TOKEN, 本地无法推送归档
假 token -> EXIT=1
sqlite3.OperationalError: no such table: orders_archive
getent hosts archive.example.invalid -> 无法解析
```

未证实的内容: 归档服务收到 `amount: null` 的旧订单时是否丢弃. 缺口是: 缺生产凭据 (ARCHIVE_TOKEN), 缺 orders_archive 表和数据, 缺生产网络可达性. 不是权限问题能补的, 是环境本身不在本地.

为什么它决定安全: 本 diff 唯一可能把某条旧订单的 amount 从 `""` 变成 `null` (纯空白金额, 见风险 R2). 如果归档侧把 null 当"没有金额"而丢弃, 这些订单会静默消失; 如果归档侧保留 null, 最坏只是金额字段从空串变 null. 这一条不验证, R2 就只能标未证实.

### 事实 D: 被删符号没有其他调用者 (等级 4)

```
git grep @HEAD:
format_amount_str        -> 无命中
LEGACY_AMOUNT_KEY        -> 无命中
register_legacy_formatter -> 只剩 amountlib/__init__.py:2,4 与 amountlib/legacy.py:7 的定义/导出
read_orders              -> app/orders.py:7 定义, scripts/dump_orders.py:10,17 使用
```

全仓文本 grep (排除 .git/.agents) 同样只命中 db/seed.py 的数据字符串和 amountlib 自身. 唯一入口是 scripts/dump_orders.py.

含义: 删掉的两个符号 (format_amount_str, LEGACY_AMOUNT_KEY) 是纯死代码; register_legacy_formatter 仍被导出但已无调用者, 属于遗留 API, 不会造成导入错误.

## 3. 风险

按严重度排序, 每条都有实跑证据 (除非标未证实).

### R1 (高, 可用性): 非规范金额文本会让整次导出失败

旧代码只做 strip, 原样透传; 新代码 parse_amount 对非法文本抛 ValueError. read_orders 不捕获, dump_orders 也不捕获, 于是一行坏数据导致整批失败, 不再产出 JSON.

真实入口实跑 (head 树, 追加 id=4, amount_str="1,234.50"):

```
Traceback (most recent call last):
  File ".../head-tree/scripts/dump_orders.py", line 24, in <module>
    main()
  File ".../head-tree/scripts/dump_orders.py", line 17, in main
    rows = read_orders(conn)
  File ".../head-tree/app/orders.py", line 14, in read_orders
    amount = parse_amount(payload.get("amount_str", ""))
  File ".../head-tree/amountlib/core.py", line 20, in parse_amount
    raise ValueError(f"无法解析金额: {raw!r}")
ValueError: 无法解析金额: '1,234.50'
EXIT=1
dump 后导出文件: No such file or directory
```

同一条数据在 base 树正常导出为 `"1,234.50"`, EXIT=0.

触发面: 千分位, 货币符号, "N/A", 中文数字, 全角数字等任何非 Decimal 可解析文本. 生产 v1 数据里是否存在这类值, 本地无数据可查 (缺口: 缺生产 orders.payload 样本).

### R2 (中, 静默值变化 + 未证实下游): 纯空白 amount_str 从 "" 变成 null

base: `""` -> `''`; head: `""` -> `None`. 实跑对比:

```
id=4 {"schema": "v1", "amount_str": "   "}
  base -> ''
  head -> None
```

旧函数只判 `raw is None or raw == ""`, 纯空白不会被拦截, 返回 `""`; 新路径 strip 后为空, 返回 None.

危害取决于两件本地无法确认的事: (1) 归档服务是否丢弃 amount 为 null 的订单 (事实 C 未证实); (2) Node 消费者对 `""` 与 `null` 是否同样处理 (本次按你的只读限制未读该仓库, 未证实). 如果任何一方把 null 当"无金额订单"丢弃, 这类订单会静默丢失. 生产数据里纯空白金额有多少, 同样无样本可查.

### R3 (中, 语义变化): v2 行 amount 为 null/空时, 新代码会回退读 amount_str

```
id=9  {"schema": "v2", "amount": null, "amount_str": "9.99"}  base -> None, head -> '9.99'
id=10 {"schema": "v2", "amount": "",   "amount_str": "9.99"}  base -> None, head -> '9.99'
```

旧逻辑对 v2 只看 amount, 为空就是没有金额; 新逻辑把 amount 为空也当"解析失败"去回退 amount_str. 若 v2 数据里存在 amount 显式置空但 amount_str 是历史残留, 会复活过期金额. 是否有这种行, 无生产样本, 未证实.

### R4 (低, 线格式): 同一数值的文本表示被规范化

```
id=5 "0012.50" base -> '0012.50'  head -> '12.50'
id=6 "1e3"     base -> '1e3'      head -> '1E+3'
```

数值相等, 但导出 JSON 的字符串变了. 若消费者按字符串比对/去重, 会看到差异. 未读消费者, 无法判断.

### R5 (低, 死代码): register_legacy_formatter 现在无调用者

不影响运行; 只是 amountlib 里留着一个再也没人注册的扩展点. 不是破坏, 但可在后续清理.

## 4. 已排除项

- v2 且 amount 有值: 两版都走 resolve_amount 的 `"amount" in payload` 分支, 行为完全相同 (id=1: 12.50).
- v1 空串: 两版都得 None (事实 A, id=3), 不会变 0, 不会抛错.
- v1 缺 amount_str 字段: 两版都得 None (id=8).
- 普通十进制文本 "9.99": 输出字符串一致 (id=2).
- 被删符号的外部调用者: 无 (事实 D), 删了不会 ImportError.
- 导入顺序/注册时机副作用: 旧代码在 import app.orders 时全局注册 formatter, 但仓库内只有 scripts/dump_orders.py 导入 app.orders, 且它只用 read_orders; 没有别的模块依赖这个注册副作用.
- 库版本被环境覆盖: 实测 `amountlib.__file__` 指向仓库内 vendored 副本, VERSION 2.4.0; 全盘查找无 site-packages 版同名包 (只找到同批练习目录).
- 归档推送路径: 本地跑不起来 (事实 C), 不会因为本次改动在本地产生副作用.

## 5. 合并前最便宜的复现

一条命令复现 R1 (整批导出失败):

```bash
D=/tmp/orchestra-07/out/green-ts001/head-tree
uv run --no-project python -c "import sqlite3,json;c=sqlite3.connect('$D/var/orders.db');c.execute('INSERT INTO orders (id,payload) VALUES (?,?)',(99,json.dumps({'schema':'v1','amount_str':'1,234.50'})));c.commit()"
cd $D && uv run --no-project python scripts/dump_orders.py; echo EXIT=$?
```

期望: ValueError, EXIT=1, var/orders.export.json 不生成. 换 base 树跑同一条则 EXIT=0 并导出 `"1,234.50"`.

复现 R2/R3/R4: 跑 /tmp/orchestra-07/out/green-ts001/proof_read.py 对两棵树, 对比其输出 (见下).

## 6. 实际执行的命令与原始输出

### 6.1 变更与历史

```bash
cd /tmp/orchestra-07/drill-ts001-green
git show HEAD
git log --oneline --all
git log --all --oneline -S"format_amount_str"
git log --all --oneline -S"parse_amount"
git blame -L 1,16 -- app/orders.py
git show 011ec25:app/orders.py
```

关键输出:

```
04ddf93 删除旧的 amount_str 格式化符号, 改用 parse_amount 回退
011ec25 订单服务基线: amountlib 2.4.0 与 orders.payload 读取

diff --git a/app/orders.py b/app/orders.py
@@ -1,25 +1,16 @@
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
@@
-        amount = resolve_amount(json.loads(row[1]))
+        payload = json.loads(row[1])
+        amount = resolve_amount(payload)
+        if amount is None:
+            amount = parse_amount(payload.get("amount_str", ""))
```

git blame 显示这些行只来自 011ec25 与 04ddf93 两个提交; 仓库无 PR 分支/远端材料, 提交消息里也没有 PR 编号, 所以拿不到评审讨论 (来源限制).

### 6.2 环境与版本

```bash
uv run python -c "import sys, amountlib; print(sys.version); print(amountlib.__file__); print(amountlib.VERSION)"
find / -maxdepth 8 -name "amountlib*" -not -path "*/drill-ts001-green/*"
```

```
3.14.7 (main, Aug 14 2026, 15:35:28) [Clang 22.1.3 ]
/tmp/orchestra-07/drill-ts001-green/amountlib/__init__.py
2.4.0
(全盘结果只有同批练习目录, 无 site-packages 安装副本)
```

注: 这次 uv 调用在仓库里生成了 .venv 与 uv.lock, 已在调查结束前删除, 仓库恢复干净.

### 6.3 证据脚本 1 (parse_amount 空串行为)

文件: /tmp/orchestra-07/out/green-ts001/proof_parse.py (全文见附录 A)

```bash
cd /tmp && PYTHONPATH=/tmp/orchestra-07/out/green-ts001/head-tree \
  uv run --no-project python /tmp/orchestra-07/out/green-ts001/proof_parse.py
```

输出见事实 A, EXIT=0.

### 6.4 证据脚本 2 (base vs head 逐行对比)

文件: /tmp/orchestra-07/out/green-ts001/proof_read.py (全文见附录 B). 脚本先断言导入的是指定树的 amountlib 2.4.0, 再逐行建独立内存库调用 read_orders, 捕获每行异常.

```bash
cd /tmp
for t in base head; do
  PYTHONPATH=/tmp/orchestra-07/out/green-ts001/$t-tree \
    uv run --no-project python /tmp/orchestra-07/out/green-ts001/proof_read.py \
    /tmp/orchestra-07/out/green-ts001/$t-tree
done
```

base 输出 (EXIT=0):

```
tree: /tmp/orchestra-07/out/green-ts001/base-tree
amountlib.__file__: /tmp/orchestra-07/out/green-ts001/base-tree/amountlib/__init__.py
amountlib.VERSION: 2.4.0
id=1 payload={"schema": "v2", "amount": "12.50"} -> '12.50'
id=2 payload={"schema": "v1", "amount_str": "9.99"} -> '9.99'
id=3 payload={"schema": "v1", "amount_str": ""} -> None
id=4 payload={"schema": "v1", "amount_str": "   "} -> ''
id=5 payload={"schema": "v1", "amount_str": "0012.50"} -> '0012.50'
id=6 payload={"schema": "v1", "amount_str": "1e3"} -> '1e3'
id=7 payload={"schema": "v1", "amount_str": "1,234.50"} -> '1,234.50'
id=8 payload={"schema": "v1"} -> None
id=9 payload={"schema": "v2", "amount": null, "amount_str": "9.99"} -> None
id=10 payload={"schema": "v2", "amount": "", "amount_str": "9.99"} -> None
```

head 输出 (EXIT=0):

```
tree: /tmp/orchestra-07/out/green-ts001/head-tree
amountlib.__file__: /tmp/orchestra-07/out/green-ts001/head-tree/amountlib/__init__.py
amountlib.VERSION: 2.4.0
id=1 payload={"schema": "v2", "amount": "12.50"} -> '12.50'
id=2 payload={"schema": "v1", "amount_str": "9.99"} -> '9.99'
id=3 payload={"schema": "v1", "amount_str": ""} -> None
id=4 payload={"schema": "v1", "amount_str": "   "} -> None
id=5 payload={"schema": "v1", "amount_str": "0012.50"} -> '12.50'
id=6 payload={"schema": "v1", "amount_str": "1e3"} -> '1E+3'
id=7 payload={"schema": "v1", "amount_str": "1,234.50"} -> EXCEPTION ValueError: 无法解析金额: '1,234.50'
id=8 payload={"schema": "v1"} -> None
id=9 payload={"schema": "v2", "amount": null, "amount_str": "9.99"} -> '9.99'
id=10 payload={"schema": "v2", "amount": "", "amount_str": "9.99"} -> '9.99'
```

diff (去掉 tree 路径行):

```
-id=4 ... -> ''
+id=4 ... -> None
-id=5 ... -> '0012.50'
+id=5 ... -> '12.50'
-id=6 ... -> '1e3'
+id=6 ... -> '1E+3'
-id=7 ... -> '1,234.50'
+id=7 ... -> EXCEPTION ValueError: 无法解析金额: '1,234.50'
-id=9 ... -> None
+id=9 ... -> '9.99'
-id=10 ... -> None
+id=10 ... -> '9.99'
```

第一次跑该脚本时用了整批一个连接, id=7 的异常直接中断整次调用, 看不到 8-10 行; 这本身就说明一行坏数据会打断整批. 后来改成逐行隔离才拿到上表.

### 6.5 真实入口: 种子数据导出

```bash
cd /tmp
for t in base head; do
  ( cd /tmp/orchestra-07/out/green-ts001/$t-tree \
    && uv run --no-project python db/seed.py \
    && uv run --no-project python scripts/dump_orders.py )
done
diff -u base-tree/var/orders.export.json head-tree/var/orders.export.json
```

```
base: seeded .../base-tree/var/orders.db with 3 rows
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
head: seeded .../head-tree/var/orders.db with 3 rows
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
IDENTICAL
```

### 6.6 真实入口: 一行非法金额

```bash
D=.../head-tree
uv run --no-project python -c "import sqlite3,json;c=sqlite3.connect('$D/var/orders.db');c.execute('INSERT INTO orders (id,payload) VALUES (?,?)',(4,json.dumps({'schema':'v1','amount_str':'1,234.50'})));c.commit()"
cd $D && uv run --no-project python scripts/dump_orders.py
```

head 结果见风险 R1 (EXIT=1, 无导出文件); base 同数据 EXIT=0, 导出含 `{"id": 4, "amount": "1,234.50"}`.

### 6.7 归档服务可达性

```bash
cd .../head-tree
env -u ARCHIVE_TOKEN uv run --no-project python -c "import sqlite3; from app.legacy_sync import push_to_archive; push_to_archive(sqlite3.connect(':memory:'))"
ARCHIVE_TOKEN=fake uv run --no-project python -c "import sqlite3; from app.legacy_sync import push_to_archive; push_to_archive(sqlite3.connect(':memory:'))"
grep -n orders_archive db/schema.sql
getent hosts archive.example.invalid
```

```
无 token -> EXIT=1, RuntimeError: 缺 ARCHIVE_TOKEN, 本地无法推送归档
假 token -> EXIT=1, sqlite3.OperationalError: no such table: orders_archive
schema.sql 中不存在 orders_archive
archive.example.invalid 无法解析
```

### 6.8 被删符号调用者

```bash
git grep -n format_amount_str HEAD
git grep -n LEGACY_AMOUNT_KEY HEAD
git grep -n register_legacy_formatter HEAD
git grep -n read_orders HEAD
```

```
format_amount_str -> 无命中
LEGACY_AMOUNT_KEY -> 无命中
register_legacy_formatter -> amountlib/__init__.py:2,4; amountlib/legacy.py:7
read_orders -> app/orders.py:7; scripts/dump_orders.py:10,17
```

## 7. 结论

对仓库里已知的 3 条订单, 本次改动导出结果逐字节相同 (事实 A/B), 被删符号无外部调用者 (事实 D), 库版本无污染. 这部分是安全的.

真正的风险不在我们能看到的数据上: 生产 v1 数据只要有一条非规范金额文本 ("1,234.50", "N/A", 货币符号等), 整次导出会从"原样透传"变成"直接崩溃且不产出 JSON" (R1, 已用真实入口复现). 其次, 纯空白金额从 "" 静默变成 null (R2), 而归档服务是否因此丢弃订单 (事实 C) 与消费者如何对待 null 都无法本地证实, 需要生产凭据/网络或该仓库的访问权限才能补齐.

## 8. 未证实项与缺口

1. 归档服务对 amount=null 旧订单的处理策略: 缺 ARCHIVE_TOKEN, 缺 orders_archive 表与数据, 缺生产网络. 事实 C 停在 2 级.
2. Node 消费者对 "" / null / 规范化字符串的处理: 按只读限制未读 orders-consumer 仓库, 停在 0 级 (未观察).
3. 生产 orders.payload 里是否存在非法文本, 纯空白金额, 以及 v2 行 amount 置空但 amount_str 有残留: 无生产数据样本, 缺数据.
4. 未在生产运行中的应用里复现 (5 级): 缺可运行环境.

## 附录 A: proof_parse.py 全文

```python
"""证据脚本 1: 断言应用实际加载的 amountlib 版本与 parse_amount 的空串行为.

判断错时 assert 触发, 进程非零退出.
"""
import sys
from decimal import Decimal

import amountlib
from amountlib import parse_amount

print("python:", sys.version.split()[0])
print("amountlib.__file__:", amountlib.__file__)
print("amountlib.VERSION:", amountlib.VERSION)

assert amountlib.VERSION == "2.4.0", "版本不符, 测到的不是应用使用的那份代码"

# (a) 关键事实: 空串/None/纯空白都表示没有金额.
for raw in ("", None, "   ", "\t\n"):
    got = parse_amount(raw)
    print(f"parse_amount({raw!r}) -> {got!r}")
    assert got is None, f"parse_amount({raw!r}) 应为 None, 实际 {got!r}"

# 正常文本仍然解析成 Decimal, 且格式与原文本可能不同.
for raw in ("9.99", " 9.99 ", "0012.50", "1e3"):
    got = parse_amount(raw)
    print(f"parse_amount({raw!r}) -> {got!r} ; str() -> {str(got)!r}")
assert parse_amount("9.99") == Decimal("9.99")

# 非数字文本抛 ValueError, 不会返回原文.
try:
    parse_amount("1,234.50")
except ValueError as exc:
    print("parse_amount('1,234.50') -> ValueError:", exc)
else:
    raise AssertionError("非法金额没有抛 ValueError")

print("OK: 版本与空串行为断言全部通过")
```

## 附录 B: proof_read.py 全文

```python
"""证据脚本 2: 对任意一棵代码树逐行跑 read_orders, 打印结果或该行触发的异常.

用法: python proof_read.py <tree>
逐行隔离, 避免一行非法金额掩盖后面的行. 版本/tree 断言失败时非零退出.
"""
import json
import sqlite3
import sys

tree = sys.argv[1]
import amountlib  # noqa: E402

print("tree:", tree)
print("amountlib.__file__:", amountlib.__file__)
print("amountlib.VERSION:", amountlib.VERSION)
assert amountlib.VERSION == "2.4.0"
assert amountlib.__file__.startswith(tree), "导入的不是指定树的 amountlib"

from app.orders import read_orders  # noqa: E402

CASES = [
    (1, {"schema": "v2", "amount": "12.50"}),                 # seed
    (2, {"schema": "v1", "amount_str": "9.99"}),              # seed
    (3, {"schema": "v1", "amount_str": ""}),                  # seed
    (4, {"schema": "v1", "amount_str": "   "}),               # 纯空白
    (5, {"schema": "v1", "amount_str": "0012.50"}),           # 前导零
    (6, {"schema": "v1", "amount_str": "1e3"}),               # 科学计数
    (7, {"schema": "v1", "amount_str": "1,234.50"}),          # 带千分位
    (8, {"schema": "v1"}),                                    # 缺字段
    (9, {"schema": "v2", "amount": None, "amount_str": "9.99"}),   # v2 显式 null
    (10, {"schema": "v2", "amount": "", "amount_str": "9.99"}),    # v2 空串
]

for i, p in CASES:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
    conn.execute("INSERT INTO orders (id, payload) VALUES (?, ?)", (i, json.dumps(p)))
    try:
        got = read_orders(conn)[0]["amount"]
        print(f"id={i} payload={json.dumps(p, ensure_ascii=False)} -> {got!r}")
    except Exception as exc:
        print(f"id={i} payload={json.dumps(p, ensure_ascii=False)} -> EXCEPTION {type(exc).__name__}: {exc}")
    finally:
        conn.close()
```

## 附录 C: 证据文件位置

- /tmp/orchestra-07/out/green-ts001/proof_parse.py
- /tmp/orchestra-07/out/green-ts001/proof_read.py
- /tmp/orchestra-07/out/green-ts001/base-tree (011ec25 的 git archive 副本)
- /tmp/orchestra-07/out/green-ts001/head-tree (04ddf93 的 git archive 副本)
- /tmp/orchestra-07/out/green-ts001/read-base.log, read-head.log
- /tmp/orchestra-07/out/green-ts001/archive-no-token.log, archive-fake-token.log
