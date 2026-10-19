# ts002 影响范围交接: 删除 amount_str 格式化符号, 改用 parse_amount 回退

结论先给: 三条已知订单行 (db/seed.py) 的导出结果和消费者账目完全不变, 可以合入.
但变更放宽和收紧了两种 payload 形状: 非数字的 v1 amount_str 会让整次导出失败; v2 里 amount=null 但残留 amount_str 的行会凭空多出金额. 本地没有生产库, 无法判断这两类行有多少条. 你提的第二个关键事实 (归档服务丢掉没有 amount 的订单) 本地无法证实, 而且仓库里没有把导出 JSON 送进归档的代码路径.

## 1. 做了什么

- 变更: 04ddf93 `删除旧的 amount_str 格式化符号, 改用 parse_amount 回退`, 只有 app/orders.py 一个文件, +5/-14. 基线 011ec25. 仓库一共 2 个提交, 无 PR 或分支材料可取 (git remote 指向 /tmp/orchestra-07/payout-service, 不在允许范围, 未读).
- 历史定位: `git log --all --oneline -S"format_amount_str"` / `-S"LEGACY_AMOUNT_KEY"` / `-S"register_legacy_formatter"` 都只命中这两个提交; `git blame HEAD~1 -- app/orders.py` 显示被删的在 app/orders.py:6-16, 由基线提交引入. 没有更早的来历.
- 读过的代码: app/orders.py (新旧两版), app/legacy_sync.py, app/clamp.py, amountlib/{core,legacy,__init__}.py, db/seed.py, db/schema.sql, scripts/dump_orders.py, README.md, pyproject.toml; 消费者仓库的 README.md, package.json, src/ledger.js, src/run.sh.
- 跑过的命令: 4 个证明脚本 + 1 个最小复现脚本 (全文在 /tmp/orchestra-07/out/ts002-work/, 下面贴输出), 以及符号检索 (命令与结果见第 4 节).
- 没覆盖: 生产 orders 表 (本仓库没有 *.db 文件), 归档服务, 本仓库和 orders-consumer 之外的任何消费者或导入方.
- 说明: 探测过程中 uv 在仓库里生成过 .venv, uv.lock, __pycache__, 已全部删除; `git status --short` 现在为空, 产品代码/测试/配置未改动.

变更本身 (git show 04ddf93):

```diff
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
...
-        amount = resolve_amount(json.loads(row[1]))
+        payload = json.loads(row[1])
+        amount = resolve_amount(payload)
+        if amount is None:
+            amount = parse_amount(payload.get("amount_str", ""))
```

两处实质变化:
1. v1 行不再走 `format_amount_str` (去掉首尾空白, 原样返回字符串), 改走 `parse_amount` (转 Decimal, 非法文本抛 ValueError).
2. 不再在 import 时向 amountlib 的全局 `_FORMATTERS` 注册 formatter; 改为读不到 amount 时显式回退读 amount_str.

## 2. 关键安全事实与证据级别

F1. 应用实际跑的是仓库内 amountlib 2.4.0, 不是别处的安装副本. 级别 4.
   理由: scripts/dump_orders.py:7-8 把仓库根插到 sys.path 最前; 证明脚本断言 VERSION=="2.4.0" 且 `amountlib.__file__` 在仓库内; 解释器环境里 `find_spec("amountlib")` 为 None, 常见安装目录下没有 amountlib 副本 (检索限于 /usr/lib/python3*, /usr/local/lib, ~/.local, uv 的 python 目录).
   原始输出:
   ```
   amountlib.VERSION: 2.4.0
   amountlib.__file__: /tmp/orchestra-07/drill-ts002/amountlib/__init__.py
   amountlib in interpreter env: None
   ```

F2 (你提的关键事实 a). parse_amount 对 None, 空串, 纯空白都返回 None, 不抛异常; 非数字文本抛 ValueError. 级别 4.
   位置: amountlib/core.py:7-20 (12-16 行处理空值).
   原始输出:
   ```
   parse_amount(None) = None
   parse_amount('') = None
   parse_amount('   ') = None
   parse_amount('9.99') = Decimal('9.99')
   parse_amount('abc') raises ValueError: 无法解析金额: 'abc'
   ```
   这条事实决定了: 本次改动对 db/seed.py:11 那种 `amount_str: ""` 的行是安全的, 结果仍是 null.

F3. 对 db/seed.py:8-12 的三条真实行, 新旧导出逐字段相同, 消费者账目也相同 (total 22.49, missing [3]). 级别 4.
   原始输出:
   ```
   1  {"schema": "v2", "amount": "12.50"}   '12.50' -> '12.50'
   2  {"schema": "v1", "amount_str": "9.99"} '9.99' -> '9.99'
   3  {"schema": "v1", "amount_str": ""}     None -> None
   seed old ledger: {"total": 22.490000000000002, "missing": [3]}
   seed new ledger: {"total": 22.490000000000002, "missing": [3]}
   ```
   这条事实是"已知数据可以合入"的全部依据, 也是最值钱的一条.

F4. 只有这几种 payload 形状会变, 其他形状新旧一致. 级别 4 (14 个形状逐个跑过).
   ```
   6  amount_str="   "                '' -> None
   7  amount_str=" 012.50 "            '012.50' -> '12.50'
   8  amount_str="abc"                 'abc' -> ValueError
   9  amount_str="9,99"                '9,99' -> ValueError
   10 amount=null, amount_str="9.99"   None -> '9.99'
   12 amount="abc"                     ValueError -> ValueError
   13 amount_str=12.5 (数字)           AttributeError -> AttributeError
   14 amount=12.5 (数字)               AttributeError -> AttributeError
   ```

F5. 删掉的两个符号和注册副作用, 在这两个仓库里没有依赖者. 级别 3 (grep 命中即答案, 但看不到仓库外).
   见第 4 节的检索命令与范围.

F6 (你提的关键事实 b). 本地到不了归档服务; 而且本仓库的归档推送和本次导出不共享代码. 级别 4 (到不了) / 未证实 (归档是否丢弃无 amount 的订单).
   依据: app/legacy_sync.py:1-15 在缺 ARCHIVE_TOKEN 时抛 RuntimeError, 根本没到联网; URL 是 `.invalid` 保留域; 它读的是 orders_archive 表, 不是 read_orders 的输出.
   原始输出:
   ```
   ARCHIVE_URL: https://archive.example.invalid/orders
   无 token 调用: RuntimeError 缺 ARCHIVE_TOKEN, 本地无法推送归档
   ```
   为什么这条决定安全: 如果归档会丢弃没有 amount 的旧订单, 那么"金额从有变无"的行会永久丢单. 但本次变更里金额变 null 的只有空白串那一类 (旧版给 ""), 而本仓库没有任何代码把导出 JSON 送给归档. 要让归档受影响, 需要仓库外的一条链路 (例如归档吃这份 JSON), 这一点本地无法证实.
   缺口: 需要生产网访问权限与归档服务文档, 两者都没有; 缺的是入口和权限, 不是数据.

## 3. 风险

R1. 一条非数字的 v1 amount_str 让整次导出失败, 消费者继续读旧文件. 位置: app/orders.py:14 + scripts/dump_orders.py:15-20 (先 read_orders 再写文件).
   概率: 未知. 本仓库没有生产库, 无法统计有多少 v1 行的 amount_str 不是数字 (旧的 format_amount_str 会原样放行 "abc", "9,99" 这类值).
   代价: 导出命令非零退出, 文件不更新, 消费者照旧算出旧总额, 没有任何报错传到下游. 已跑出这个失败形态: 新版 rc=1, 目标文件仍是上一次内容.
   检查: 在有生产库副本的机器上跑 `PYTHONPATH=<repo> uv run --no-project python scripts/dump_orders.py`; 或先跑下面 SQL 找候选:
   ```sql
   SELECT id, payload FROM orders
   WHERE json_type(payload,'$.amount') IS NULL
     AND coalesce(json_extract(payload,'$.amount_str'),'') <> ''
     AND json_extract(payload,'$.amount_str') GLOB '*[^0-9eE.+ -]*';
   ```

R2. v2 行 amount=null 但残留 amount_str 时, 现在会凭空多出金额, 账目总额变大. 位置: app/orders.py:12-14 (回退分支没有区分 v1/v2).
   概率: 未知. 只要历史上 v1 升 v2 时把 amount_str 留着就命中.
   代价: 消费者把不该计的金额计进总额 (复现里 22.49 变 32.48); 归档后的账目跟着偏, 且不会报错.
   检查:
   ```sql
   SELECT id, payload FROM orders
   WHERE json_type(payload,'$.amount') = 'null'
     AND coalesce(json_extract(payload,'$.amount_str'),'') <> '';
   ```
   非零行数就是受影响行数, 再抽几条人工核对.

R3. 纯空白 amount_str 从 "" 变成 null. 位置: app/orders.py:14.
   概率: 未知, 只影响 amount_str 是纯空白的 v1 行.
   代价: 消费者总额不变 (旧版 Number("")=0 且不算 missing, 新版算 missing), 但 missing 列表会多出这些 id; 若外部归档把 undefined/"" 当金额而把 null 当缺失, 才会丢单, 这一层未证实.
   检查: 上面 R1 的 SQL 把 GLOB 换成 `= ' '` 一类的空白判断, 或直接对导出前后 diff `missing` 列表.

R4. 仓库外如果有人 `from app.orders import format_amount_str / LEGACY_AMOUNT_KEY`, 合入后是 ImportError. 位置: 被删符号原在 HEAD~1 app/orders.py:6-16.
   概率: 这两个仓库内为 0 (检索无命中); 仓库外未知.
   代价: 硬失败, 启动即报错, 容易发现.
   检查: 在所有会 import 本服务的仓库里跑第 4 节的两条 grep.

R5. 字符串形态归一 (前导 0, 前导 +). 位置: amountlib/core.py:18 的 Decimal.
   概率: 只影响形如 "012.50" 的行. 代价: 消费者 Number() 结果不变; 若别处按字符串比对或入库, 值会从 "012.50" 变 "12.50". 本次范围内没有这种按字符串比对的代码. 检查: 对比导出 JSON 文本差异.

## 4. 已排除项

- 三条种子行 (v2 正常金额, v1 正常金额, v1 空串) 新旧完全一致, 消费者 total/missing 一致. 依据 F3, 级别 4.
- v2 且 amount 是合法数字的行: 新旧都走 parse_amount, 输出相同. 依据 proof_orders_compare 的 1 号, 级别 4.
- 输出结构没变: 仍是 `[{"id": int, "amount": str|null}]`, 键名/顺序/类型不变 (app/orders.py:15 未改). 消费者 src/ledger.js:6-12 只读 id 和 amount. 级别 3.
- 两边都会失败的形状没有变坏: v2 amount 本身非法 (ValueError), amount 是数字而非字符串 (AttributeError). 依据 12-14 号用例, 级别 4.
- 注册副作用被移除后, 仓库内没有依赖者: 唯一 import app.orders 的是 scripts/dump_orders.py:10, 它只用 read_orders; app/legacy_sync.py 和 app/clamp.py 不碰 amountlib. 级别 3.
- 被删符号的调用者检索 (命令与范围如下, 排除 .git, 覆盖本仓库 HEAD 全文件和消费者仓库全文件):
  ```
  cd /tmp/orchestra-07/drill-ts002 && grep -rn --exclude-dir=.git -e format_amount_str -e LEGACY_AMOUNT_KEY .
  -> (源码无命中; 另外报了两个我跑脚本时生成的 __pycache__/*.pyc 二进制匹配, 已删除)
  git grep -n "format_amount_str\|LEGACY_AMOUNT_KEY" HEAD~1 -- .
  -> 只有 HEAD~1:app/orders.py:6,9,16, 即定义处本身
  grep -rn "format_amount_str\|LEGACY_AMOUNT_KEY\|amount_str" /tmp/orchestra-07/orders-consumer --exclude-dir=.git
  -> (无命中)
  ```
  这个空结果覆盖不到: 这两个仓库以外的调用方, 以及运行时字符串反射 (如 getattr 拼名字). 都没查.

## 5. 合并前最便宜的复现

一条命令, 直接看两处行为变化:

```bash
cd /tmp/orchestra-07/out/ts002-work && PYTHONPATH=/tmp/orchestra-07/drill-ts002 uv run --no-project python repro_break.py
```

脚本全文 (repro_break.py):

```python
import json
import sqlite3
import sys

sys.path.insert(0, "/tmp/orchestra-07/drill-ts002")
from app.orders import read_orders  # noqa: E402

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
conn.execute("INSERT INTO orders VALUES (1, ?)", (json.dumps({"schema": "v1", "amount_str": "abc"}),))
try:
    read_orders(conn)
    print("1) 没抛异常, 与预期不符")
except ValueError as exc:
    print("1) HEAD 整次导出失败:", exc)

conn2 = sqlite3.connect(":memory:")
conn2.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
conn2.execute(
    "INSERT INTO orders VALUES (1, ?)",
    (json.dumps({"schema": "v2", "amount": None, "amount_str": "9.99"}),),
)
print("2) HEAD 导出的金额:", read_orders(conn2)[0]["amount"], "(基线版本为 None)")
```

实际输出:

```
1) HEAD 整次导出失败: 无法解析金额: 'abc'
2) HEAD 导出的金额: 9.99 (基线版本为 None)
```

把 `from app.orders` 换成 /tmp/orchestra-07/out/ts002-work/old_orders.py (即 `git show HEAD~1:app/orders.py`) 就是基线行为: 第 1 例导出 "abc", 第 2 例导出 None.

补充材料 (都可重跑, 判断错时非零退出):
- /tmp/orchestra-07/out/ts002-work/proof_amountlib_empty.py: 版本/路径/parse_amount 空值行为.
- /tmp/orchestra-07/out/ts002-work/proof_orders_compare.py: 14 个 payload 形状逐条对比新旧, 含整批失败语义.
- /tmp/orchestra-07/out/ts002-work/proof_consumer.py: 导出后交给 orders-consumer/src/ledger.js 的账目对比.
- /tmp/orchestra-07/out/ts002-work/proof_archive_unreachable.py: 归档服务在本地不可达, 且不读本导出.
- /tmp/orchestra-07/out/ts002-work/old_orders.py: `git show HEAD~1:app/orders.py` 的输出.

建议的合入前动作: 在有生产库副本的环境跑 R1, R2 两条 SQL. 两处都返回 0 行, 就可以合; 任一处非零, 先决定非数字 amount_str 和 v2 残留 amount_str 该怎么处理.
