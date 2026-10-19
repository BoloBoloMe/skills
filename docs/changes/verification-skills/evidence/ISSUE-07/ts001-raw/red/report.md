# ts001 影响范围调查报告

- 仓库: `/tmp/orchestra-07/drill-ts001-red`
- 起始提交: `011ec2536e0fcb750156fef546a90b1050ab4882`
- 变更提交: `04ddf931fd161baea18b0a0d315da8d41eb7cf7e` (HEAD)
- 下游仓库: `/tmp/orchestra-07/orders-consumer`, 起始提交 `a47893d0dea16e39197603ee28b7b8b467efbbee`
- 调查时间: 2026-10-19
- 产品代码/测试改动: 无. 原仓库 `git status --porcelain` 为空, `git diff --stat HEAD` 为空.

技能说明: 本机 `~/.agents/skills/` 下没有 `blast-radius` 技能目录. 本报告按 `/home/bolo/Workspace/skills/skills-v2/docs/changes/verification-skills/` 中 ISSUE-07 的规格执行, 使用其中规定的五段交接结构和证据阶梯.

## 0. 结论摘要

1. 对 seed 中 3 条已知真实订单, base 与 HEAD 的导出 JSON 逐字节相同, Node 消费者输出也相同. 证据级 5 (运行应用复现).
2. 关键事实 (a) 成立: 仓库内 `amountlib` 版本 2.4.0, `parse_amount("")` 返回 `None`, 不抛错. 空串订单仍然输出 `amount: null`. 证据级 5 (对已知 3 行), 脚本级 4 (对库函数本身).
3. 关键事实 (b) 未证实: 外部归档服务是否丢弃没有 amount 的旧订单, 本地没有任何可运行入口, 也没有服务端源码/配置/日志. 停在位置级, 失败路径无法走查.
4. 被删符号 `format_amount_str` 和 `LEGACY_AMOUNT_KEY` 在已知两个仓库, 全部 Git 历史, 第二个同 HEAD 检出中都没有其他调用者. 范围外系统无法排除.
5. 变更引入了 3 类已知数据形状下的行为变化, 都不在 seed 的 3 行里:
   - 非数字 `amount_str` 从"原样输出"变成抛 `ValueError`, 会让整次导出失败.
   - 纯空白 `amount_str` 从输出空串 `""` 变成 `null`, 消费者会把它记为 missing, 归档若丢弃 null 订单则可能丢单.
   - `amount` 为 null/空串且 `amount_str` 有值时, HEAD 会新增金额, 旧代码输出 null.

## 1. 做了什么

### 1.1 历史定位

命令:

```bash
cd /tmp/orchestra-07/drill-ts001-red
git log --all --oneline --decorate
git show-ref
git tag
git diff --stat 011ec25..HEAD
git diff --name-status 011ec25..HEAD
git show HEAD
```

输出摘要:

```text
04ddf93 (HEAD -> master, origin/master, origin/HEAD) 删除旧的 amount_str 格式化符号, 改用 parse_amount 回退
011ec25 订单服务基线: amountlib 2.4.0 与 orders.payload 读取
04ddf931fd161baea18b0a0d315da8d41eb7cf7e refs/heads/master
04ddf931fd161baea18b0a0d315da8d41eb7cf7e refs/remotes/origin/HEAD
04ddf931fd161baea18b0a0d315da8d41eb7cf7e refs/remotes/origin/master
(无 tag)
 app/orders.py | 19 +++++--------------
 1 file changed, 5 insertions(+), 14 deletions(-)
M	app/orders.py
```

完整 diff:

```diff
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

### 1.2 为什么用应用实际使用的库和真实入口

- `scripts/dump_orders.py:8` 把仓库根目录插入 `sys.path[0]`, 然后 `from app.orders import read_orders`.
- `app/orders.py:4` 从 `amountlib` 导入.
- 仓库内 `amountlib/core.py:4` 声明 `VERSION = "2.4.0"`.
- 在 `/tmp` 下 `importlib.util.find_spec("amountlib")` 返回 `None`, 说明环境里没有另一个已安装的 amountlib 遮蔽仓库版本.

命令:

```bash
cd /tmp && uv run --no-project python - <<'EOF'
import importlib.util, os
print("cwd:", os.getcwd())
print("find_spec:", importlib.util.find_spec("amountlib"))
EOF
```

输出:

```text
cwd: /tmp
find_spec: None
```

### 1.3 证据产物

在仓库外建立两个只读对比副本:

```bash
cd /tmp/orchestra-07/out
git clone -q /tmp/orchestra-07/drill-ts001-red repo-base
git -C repo-base checkout -q 011ec2536e0fcb750156fef546a90b1050ab4882
git clone -q /tmp/orchestra-07/drill-ts001-red repo-head
git -C repo-head checkout -q 04ddf931fd161baea18b0a0d315da8d41eb7cf7e
```

证明脚本和日志都在 `/tmp/orchestra-07/out/proof/`:

| 文件 | 作用 |
| --- | --- |
| `proof_parse_amount.py` | 导入仓库 amountlib, 断言版本与 `parse_amount("")` 行为, 带负控制 |
| `probe_payloads.py` | 对 14 种 payload 分别跑 base/HEAD 的 `read_orders` |
| `proof_registration.py` | 证明导入 `app.orders` 后全局 formatter 注册是否还在 |
| `proof_archive.py` | 尝试本地触发归档流程, 证明本地只能看到什么 |
| `scan_db.py` | 只读扫描 orders.db, 统计风险数据形状 |
| `probe-base.log`, `probe-head.log` 等 | 原始运行输出 |

真实应用入口也跑了: `db/seed.py` -> `scripts/dump_orders.py` -> `orders-consumer/src/run.sh`.

## 2. 关键事实与证据级别

证据阶梯, 从低到高:

1. 自说: 只有断言, 没有材料.
2. 位置: 给到真实 `file:line`.
3. 失败路径走查: 沿代码分支走通成功/失败路径.
4. 真实脚本或测试: 运行导入真实代码的脚本并贴输出.
5. 运行应用复现: 跑真实应用入口, 产生真实产物并对比.

### 2.1 关键事实 (a): `parse_amount("")` 的行为

事实: 仓库内 `amountlib` 2.4.0 的 `parse_amount("")` 返回 `None`, 不抛错. 因此 HEAD 对 `{"schema":"v1","amount_str":""}` 的回退仍然是 `None`, 导出仍是 `amount: null`.

证据级别: 5 (运行应用复现), 但只覆盖 seed 中的 3 条已知行. 库函数行为本身是 4 (真实脚本). 更广的生产数据形状停在未证实.

位置:

- `amountlib/core.py:7-20`: `parse_amount` 先判 `None`, 再 `raw.strip()`, `if not text: return None`, 最后 `Decimal(text)`.
- `app/orders.py:12-14`: `resolve_amount` 返回 `None` 时回退到 `parse_amount(payload.get("amount_str", ""))`.
- `amountlib/legacy.py:20-23`: HEAD 进程内没有注册 formatter 时, `resolve_amount` 对 v1 payload 返回 `None`, 正好进入上面的回退.

证明脚本 `proof_parse_amount.py` 的关键断言和运行结果:

```bash
cd /tmp/orchestra-07/out
uv run --no-project python proof/proof_parse_amount.py "$PWD/repo-head"
```

```text
repo arg      = /tmp/orchestra-07/out/repo-head
amountlib file= /tmp/orchestra-07/out/repo-head/amountlib/__init__.py
VERSION       = '2.4.0'
[PASS] VERSION 是 2.4.0: actual='2.4.0' expected='2.4.0'
[PASS] 导入的是仓库内 amountlib: actual=True expected=True
[PASS] parse_amount('') 的返回: actual=None expected=None
[PASS] parse_amount('   ') 的返回: actual=None expected=None
[PASS] parse_amount(None) 的返回: actual=None expected=None
[PASS] parse_amount('9.99') 的返回: actual=Decimal('9.99') expected=Decimal('9.99')
[PASS] parse_amount(' 9.99 ') 的返回: actual=Decimal('9.99') expected=Decimal('9.99')
[PASS] parse_amount('0') 不是 None: actual=False expected=False
[PASS] parse_amount('N/A') 的行为: actual='ValueError' expected='ValueError'

RESULT: PASS
```

可失败性证明, 故意把空串期望改成"有值":

```bash
uv run --no-project python proof/proof_parse_amount.py "$PWD/repo-head" --negative-control
```

```text
[FAIL] parse_amount('') 的返回: actual=None expected='SENTINEL'
RESULT: FAIL (1 条断言不成立): ["parse_amount('') 的返回"]
exit=1
```

应用级复现, 3 条 seed 行在 base/HEAD 下逐字节相同:

```bash
for v in base head; do
  uv run --no-project python repo-$v/db/seed.py
  uv run --no-project python repo-$v/scripts/dump_orders.py
  bash /tmp/orchestra-07/orders-consumer/src/run.sh repo-$v/var/orders.export.json
done
diff -u repo-base/var/orders.export.json repo-head/var/orders.export.json
```

base 导出:

```json
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
```

HEAD 导出:

```json
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
```

`diff` 输出为空, 脚本打印 `IDENTICAL`.

base 消费者:

```json
{
  "total": 22.490000000000002,
  "missing": [
    3
  ]
}
```

HEAD 消费者:

```json
{
  "total": 22.490000000000002,
  "missing": [
    3
  ]
}
```

结论: 对已知 3 行, 事实 (a) 成立, 变更没有改变导出和消费者结果.

### 2.2 关键事实 (b): 外部归档服务是否丢弃没有 amount 的旧订单

事实: 未证实. 本地无法观察服务端是否丢弃 `amount` 缺失或为 null 的订单.

证据级别: 本地代码可走到 3 (失败路径走查), 外部服务行为停在 2 (位置) 且未证实. 缺的是: 归档服务源码/配置/日志, 生产网可达入口, 或可核对的接口契约. 没有用猜测代替.

本地能看到的位置和代码走查:

- `app/legacy_sync.py:1-15`: 注释写明本地不可运行, 需要 `orders_archive` 表和 `ARCHIVE_TOKEN`, 且归档服务只在生产网内可达.
- `app/legacy_sync.py:7`: URL 是 `https://archive.example.invalid/orders`, `.invalid` 是保留 TLD, 本机 DNS 解析失败.
- `app/legacy_sync.py:10-15`: 函数只检查 token, 然后 `SELECT id, payload FROM orders_archive`, 返回本地行数. 代码里没有任何 HTTP 请求, 也没有任何按 amount 过滤的逻辑. 所以本地代码既不能证明服务端会丢, 也不能证明会留.
- `db/schema.sql:1-4`: 本地 schema 只有 `orders` 表, 没有 `orders_archive` 表.

本地探测命令:

```bash
cd /tmp/orchestra-07/out
uv run --no-project python proof/proof_archive.py "$PWD/repo-head"
getent hosts archive.example.invalid
grep -n "orders_archive" repo-head/db/schema.sql
```

输出:

```text
repo = /tmp/orchestra-07/out/repo-head
ARCHIVE_URL = https://archive.example.invalid/orders
ARCHIVE_TOKEN in env before = False
[无 token] raised RuntimeError: 缺 ARCHIVE_TOKEN, 本地无法推送归档
[假 token, 无 orders_archive 表] raised OperationalError: no such table: orders_archive
[假 token, 有 orders_archive 表] returned {'url': 'https://archive.example.invalid/orders', 'pushed': 1}
注意: 上面第三次只统计本地表行数, 源码没有任何 HTTP 调用,
所以它不能证明外部服务收到无 amount 的订单后会丢弃还是保留.
```

```text
(无输出, getent 退出码 2)
```

```text
(grep 退出码 1, schema.sql 里没有 orders_archive)
```

为找本地是否有归档服务源码, 检索了 `/home/bolo/Workspace` 和 `/home/bolo/.agents`:

```bash
timeout 30 grep -rl --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv \
  -e "orders_archive" -e "archive.example.invalid" /home/bolo/Workspace /home/bolo/.agents
```

只命中一个夹具搭建脚本 `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-07/docs/changes/verification-skills/evidence/ISSUE-07/setup-fixture.sh`, 里面只有生成订单服务和消费者的代码, 没有归档服务实现. 结论: 本地没有可核对的归档服务代码.

这件事为什么和本次变更有关: HEAD 新增了一条"从有值变成 null"的路径, 即 v1 payload 的 `amount_str` 只有空白字符时, base 输出空串 `""`, HEAD 输出 `null`. 如果归档服务丢弃 null 订单, 这类订单会从"保留"变成"丢弃". 因为事实 (b) 未证实, 这条路径只能列为未决风险, 不能判定为已发生回归.

### 2.3 被删符号是否还有别的调用者

被删符号: `format_amount_str`, `LEGACY_AMOUNT_KEY`. 同时删除了导入期的 `register_legacy_formatter(...)` 调用, 但库函数本身还在.

证据级别: 对"已知两个仓库内没有其他调用者"是 4 (真实检索 + 导入副作用脚本). 对"范围外系统也没有"只是 2 (只能报告检索范围), 未证实.

检索范围与命令:

```bash
cd /tmp/orchestra-07/drill-ts001-red
git grep -n -E "format_amount_str|LEGACY_AMOUNT_KEY|register_legacy_formatter" HEAD --
git grep -n -E "format_amount_str|LEGACY_AMOUNT_KEY|register_legacy_formatter" 011ec25 --
grep -rn -E "format_amount_str|LEGACY_AMOUNT_KEY|register_legacy_formatter" . \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=var
for s in format_amount_str LEGACY_AMOUNT_KEY register_legacy_formatter; do
  echo "--- $s"; git log --all --oneline -S"$s"; done

grep -rn -E "format_amount_str|LEGACY_AMOUNT_KEY|from app\.orders|import app\.orders|app\.orders" \
  /tmp/orchestra-07 --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=out
grep -rn -E "format_amount_str|LEGACY_AMOUNT_KEY|register_legacy_formatter|amount_str" \
  /tmp/orchestra-07/orders-consumer --exclude-dir=.git
```

结果:

```text
### HEAD 追踪文件
HEAD:amountlib/__init__.py:2:from .legacy import register_legacy_formatter, resolve_amount
HEAD:amountlib/__init__.py:4:__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]
HEAD:amountlib/legacy.py:7:def register_legacy_formatter(field, formatter):

### base 提交 011ec25
011ec25:amountlib/__init__.py:2:from .legacy import register_legacy_formatter, resolve_amount
011ec25:amountlib/__init__.py:4:__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]
011ec25:amountlib/legacy.py:7:def register_legacy_formatter(field, formatter):
011ec25:app/orders.py:4:from amountlib import register_legacy_formatter, resolve_amount
011ec25:app/orders.py:6:LEGACY_AMOUNT_KEY = "amount_str"
011ec25:app/orders.py:9:def format_amount_str(raw):
011ec25:app/orders.py:16:register_legacy_formatter(LEGACY_AMOUNT_KEY, format_amount_str)

### 工作树递归 grep
./amountlib/legacy.py:7:def register_legacy_formatter(field, formatter):
./amountlib/__init__.py:2:from .legacy import register_legacy_formatter, resolve_amount
./amountlib/__init__.py:4:__all__ = ["VERSION", "parse_amount", "register_legacy_formatter", "resolve_amount"]

### 全部提交 -S
--- format_amount_str
04ddf93 删除旧的 amount_str 格式化符号, 改用 parse_amount 回退
011ec25 订单服务基线: amountlib 2.4.0 与 orders.payload 读取
--- LEGACY_AMOUNT_KEY
04ddf93 删除旧的 amount_str 格式化符号, 改用 parse_amount 回退
011ec25 订单服务基线: amountlib 2.4.0 与 orders.payload 读取
--- register_legacy_formatter
04ddf93 删除旧的 amount_str 格式化符号, 改用 parse_amount 回退
011ec25 订单服务基线: amountlib 2.4.0 与 orders.payload 读取

### /tmp/orchestra-07 全域检索
/tmp/orchestra-07/drill-ts001-red/scripts/dump_orders.py:10:from app.orders import read_orders
/tmp/orchestra-07/payout-service/scripts/dump_orders.py:10:from app.orders import read_orders

### 消费仓库检索
(无输出, 退出码 1)
```

说明:

- `register_legacy_formatter` 仍然存在于 `amountlib/legacy.py:7` 并由 `amountlib/__init__.py` 导出, 只是应用侧不再调用它.
- `/tmp/orchestra-07/payout-service` 是同一个 HEAD 的第二份检出, 内容与本次仓库一致, 没有额外调用者.
- 唯一入口是 `scripts/dump_orders.py:10` 的 `read_orders`, 它不使用被删符号.
- 消费仓库只读 `row.amount`, 从不读 `amount_str`.

导入副作用证明:

```bash
cd /tmp/orchestra-07/out
uv run --no-project python proof/proof_registration.py "$PWD/repo-base"
uv run --no-project python proof/proof_registration.py "$PWD/repo-head"
```

base:

```text
repo = /tmp/orchestra-07/out/repo-base
app.orders file = /tmp/orchestra-07/out/repo-base/app/orders.py
amountlib._FORMATTERS keys = ['amount_str']
hasattr(app.orders, 'format_amount_str') = True
hasattr(app.orders, 'LEGACY_AMOUNT_KEY') = True
resolve_amount(v1 9.99) = '9.99'
resolve_amount(v1 空串) = None
```

HEAD:

```text
repo = /tmp/orchestra-07/out/repo-head
app.orders file = /tmp/orchestra-07/out/repo-head/app/orders.py
amountlib._FORMATTERS keys = []
hasattr(app.orders, 'format_amount_str') = False
hasattr(app.orders, 'LEGACY_AMOUNT_KEY') = False
resolve_amount(v1 9.99) = None
resolve_amount(v1 空串) = None
```

结论: 在已知范围内, 被删符号没有其他调用者. 但删除 import 时注册是一次全局副作用变更: 任何同进程内先 `import app.orders`, 再直接调用 `amountlib.resolve_amount(v1_payload)` 的代码, 现在会从原来的字符串变成 `None`. 这种代码不在两个仓库里, 但无法排除范围外进程.

### 2.4 附带事实: 变更对已知订单的输出稳定性

证据级别: 5 (运行应用复现). base/HEAD 的 `var/orders.export.json` 逐字节相同, 消费者 JSON 输出相同. 见 2.1 的端到端输出.

## 3. 风险

风险与已排除项分开. 每条给出真实位置, 可能性, 代价, 检查方法.

### R1. 非数字 `amount_str` 现在抛错, 整次导出会失败

- 位置: `app/orders.py:14` -> `amountlib/core.py:17-20`.
- 行为: base 的 `format_amount_str` 只做 `strip()`, 会把 `"N/A"`, `"1,234.50"`, `"$9.99"` 原样输出. HEAD 的 `parse_amount` 对它们抛 `ValueError`. `read_orders` 的循环没有逐行捕获, 所以一行坏数据会让整个 `dump_orders.py` 失败, 不是只跳过该行.
- 可能性: 生产数据未知. seed 的 3 条已知行里 0 条命中. 一旦存在, 必定触发.
- 代价: 导出任务失败, 消费者和归档拿到 0 条新数据. 比 base 输出非数字字符串更早失败, 但影响面从"一行坏"扩大到"整批不出".
- 检查方法: 对生产 orders.db 只读跑 `scan_db.py`, 或在 SQL 里筛 v1 且 `amount_str` 非空, `CAST` 失败的行.
- 原始证明: `probe-head.log` 中 id 7 `N/A` 和 id 8 `1,234.50` 都 `raised ValueError`; base 对应输出 `"N/A"` / `"1,234.50"`.

### R2. 纯空白 `amount_str` 从空串变成 null, 可能触发归档丢弃

- 位置: base `app/orders.py:9-14` (`raw == ""` 才返回 None, 其他 `raw.strip()`), HEAD `app/orders.py:14` -> `amountlib/core.py:14-16`.
- 行为: `amount_str = "   "` 或 `"\t\n"` 时, base 的 formatter 返回 `""`, `read_orders` 输出 `amount: ""`. HEAD 的 `parse_amount` 返回 `None`, 输出 `amount: null`.
- 下游影响: Node 消费者只把 `=== null` 当 missing. base 的 `""` 会被 `Number("")` 当成 0, 计入 total 且不报 missing; HEAD 的 null 会进入 missing.
- 可能性: 生产数据未知, 已知 3 行 0 条命中. 一旦存在, 必定改变导出.
- 代价: 如果外部归档服务丢弃没有 amount 的订单, 这类订单会从"保留"变成"丢弃". 事实 (b) 未证实, 所以这是未决风险.
- 检查方法: `scan_db.py` 的第三项统计; 并向归档服务方确认 null 订单处理规则.
- 原始证明: `probe-base.log` id 13/14 输出 `""`, `probe-head.log` id 13/14 输出 `null`; `consumer-ws-base.out` 为 `total 0, missing []`, `consumer-ws-head.out` 为 `total 0, missing [13]`.

### R3. `amount` 为 null/空串且 `amount_str` 有值时, HEAD 新增金额

- 位置: `app/orders.py:12-14`.
- 行为: `resolve_amount` 对带 `amount` 键的 payload 直接 `parse_amount(payload["amount"])`. 如果结果是 None, HEAD 继续回退读 `amount_str`. base 没有这个回退, 直接输出 null.
- 可能性: 生产数据未知, 已知 3 行 0 条命中. 命中时必定改变结果.
- 代价: 原本被标为 missing 的订单会重新获得金额, 可能改变账目合计; 归档侧可能从"无金额"变成"有金额", 造成重复计数或状态不一致.
- 检查方法: `scan_db.py` 的第二项统计; 或在 SQL 中筛 `json_type(payload, '$.amount')` 为 null 且 `amount_str` 非空的行.
- 原始证明: `probe-base.log` id 9/10 输出 null, `probe-head.log` id 9/10 输出 `"5.00"` / `"6.00"`.

### R4. 删除全局 formatter 注册, 影响范围外同进程调用者

- 位置: base `app/orders.py:16` 的 `register_legacy_formatter(...)`, 读取点 `amountlib/legacy.py:20-23`.
- 行为: 任何依赖 `import app.orders` 副作用的代码, 在同进程调用 `resolve_amount` 处理 v1 payload 时, 以前拿到字符串, 现在拿到 `None`.
- 可能性: 已知两个仓库内 0 个调用者. 范围外未知, 可能性低但不可排除.
- 代价: 静默变成 null, 不抛错, 难以发现.
- 检查方法: 在部署包和启动入口搜索 `import app.orders` / `from app.orders`, 或在运行时断言 `amountlib.legacy._FORMATTERS` 是否为空并对照调用方预期.
- 原始证明: 2.3 的 `registration-base.out` / `registration-head.out`.

### R5. `parse_amount` 接受 `NaN` / `Infinity`, 消费者合计可能变 null

- 位置: `amountlib/core.py:18` 的 `Decimal(text)`, 下游 `orders-consumer/src/ledger.js:11`.
- 行为: `Decimal("NaN")`, `Decimal("Infinity")` 都是合法 Decimal. `read_orders` 会输出字符串 `"NaN"` / `"Infinity"`. Node 的 `Number("NaN")` 是 `NaN`, `JSON.stringify(NaN)` 变成 `null`, 合计静默变 null.
- 可能性: 极低, 需要生产数据出现这些文本. base 也会原样输出, 所以不是本次新引入, 但 HEAD 的回退路径仍然接受它们.
- 代价: 账目合计变成 null, 不报错.
- 检查方法: 扫 `amount_str` / `amount` 是否命中 `NaN`, `Infinity`, `-Infinity`.
- 原始证明:

```text
'NaN' -> Decimal('NaN')
'sNaN' -> Decimal('sNaN')
'Infinity' -> Decimal('Infinity')
'-Infinity' -> Decimal('-Infinity')
'1e3' -> Decimal('1E+3')
'+9.99' -> Decimal('9.99')
'1_000' -> Decimal('1000')
'1 000' -> ValueError 无法解析金额: '1 000'
```

### R6. 生产环境实际库版本未核实

- 位置: `README.md:3` 声明 vendored amountlib 2.4.0, `amountlib/core.py:4` 声明版本.
- 已证明: 本地仓库和 `uv run --no-project` 环境里只有仓库内这一份 amountlib, `VERSION = "2.4.0"`.
- 未证明: 生产部署是否确实从仓库导入, 而不是从别处安装同版本或不同版本的包. 若生产装的是另一份 2.4.0, 函数行为可能不同.
- 可能性: 低. 代价: 事实 (a) 的结论失效. 检查方法: 在生产进程打印 `amountlib.__file__` 和 `amountlib.VERSION`.

## 4. 已排除项

以下项曾经怀疑, 现已用真实运行或检索排除. 与上面的风险分开.

### E1. 3 条已知真实订单的导出变化

已排除. base/HEAD 的 `orders.export.json` 逐字节相同, Node 消费者输出相同. 证据级 5. 见 2.1.

### E2. 环境里另一个 amountlib 版本遮蔽仓库版本

已排除. `/tmp` 下 `find_spec("amountlib")` 返回 `None`; 证明脚本导入的是 `repo-head/amountlib/__init__.py`, `VERSION` 是 2.4.0.

### E3. v2 正常数字金额受影响

已排除. `{"schema":"v2","amount":"12.50"}` 和 `{"schema":"v2","amount":"0"}` 在 base/HEAD 都输出 `"12.50"` / `"0"`. 位置: `amountlib/legacy.py:18-19`, 两个版本都直接走 `parse_amount`.

### E4. v1 的空串, null, 缺键, 前后带空白的数字文本

已排除.

- `amount_str: ""` -> base/HEAD 都是 null.
- `amount_str: null` -> base/HEAD 都是 null.
- 缺 `amount_str` -> base/HEAD 都是 null.
- `amount_str: " 9.99 "` -> base/HEAD 都是 `"9.99"`.
- `amount_str: "0"` -> base/HEAD 都是 `"0"`.
- 注意: 纯空白 `"   "` 不在本项, 它是 R2.

### E5. 被删符号在已知仓库内有其他调用者

已排除. HEAD/base 的 `git grep`, 工作树递归 grep, 全部提交 `git log -S`, `/tmp/orchestra-07` 全域 grep, 消费仓库 grep 均未发现 `format_amount_str` / `LEGACY_AMOUNT_KEY` 的其他调用者. 唯一入口是 `scripts/dump_orders.py:10`, 它只用 `read_orders`.

### E6. 消费仓库依赖 `amount_str` 或导出结构变化

已排除. `orders-consumer/src/ledger.js:6-12` 只读 `row.amount` 和 `row.id`; 消费仓库全文没有 `amount_str`. HEAD 仍输出 `id` + `amount` 两个键.

### E7. 数据库 schema 或 payload 被改写

已排除. 本次 diff 只有 `app/orders.py`, `db/schema.sql` 和 `db/seed.py` 未变. 变更只在读取路径, 不写库, 不迁移, 不改 `orders.payload`.

### E8. `app/clamp.py` 或 `app/legacy_sync.py` 受金额解析影响

已排除. `app/clamp.py` 只有数量夹取, 不导入 amountlib. `app/legacy_sync.py` 只查 `orders_archive` 并计行数, 不解析 amount. 但归档服务端行为本身就是未证实项 (2.2), 不能因为本地代码无关就当作已排除.

### E9. 零金额被误判为缺失

已排除. `parse_amount("0")` 返回 `Decimal("0")`, 不是 None; `read_orders` 输出 `"0"`. base 的 `format_amount_str("0")` 也返回 `"0"`. 证明脚本和 probe id 11/12 都覆盖.

## 5. 合并前最便宜复现

### 5.1 复现"已知 3 行无变化"

```bash
cd /tmp/orchestra-07
rm -rf repro-base repro-head
git clone -q drill-ts001-red repro-base
git -C repro-base checkout -q 011ec2536e0fcb750156fef546a90b1050ab4882
git clone -q drill-ts001-red repro-head
git -C repro-head checkout -q 04ddf931fd161baea18b0a0d315da8d41eb7cf7e

for v in base head; do
  uv run --no-project python repro-$v/db/seed.py
  uv run --no-project python repro-$v/scripts/dump_orders.py
  bash orders-consumer/src/run.sh repro-$v/var/orders.export.json
done

diff -u repro-base/var/orders.export.json repro-head/var/orders.export.json
```

预期: `diff` 无输出, 两份消费者输出都是 `total 22.490000000000002, missing [3]`.

### 5.2 复现三类行为变化

```bash
uv run --no-project python /tmp/orchestra-07/out/proof/probe_payloads.py /tmp/orchestra-07/repro-head
```

预期关键行:

- id 7 `N/A`: `raised ValueError`.
- id 8 `1,234.50`: `raised ValueError`.
- id 9 `amount: null, amount_str: "5.00"`: 输出 `"5.00"` (base 是 null).
- id 10 `amount: "", amount_str: "6.00"`: 输出 `"6.00"` (base 是 null).
- id 13 `"   "`: 输出 null (base 是 `""`).
- id 14 `"\t\n"`: 输出 null (base 是 `""`).

### 5.3 检查真实数据库的数据形状

只读, 不改库:

```bash
uv run --no-project python /tmp/orchestra-07/out/proof/scan_db.py \
  /tmp/orchestra-07/repro-head /path/to/orders.db
```

输出会列出:

- v1 且 `amount_str` 非空但 `parse_amount` 会抛 `ValueError` 的行 (R1).
- `amount` 为 null/空串但 `amount_str` 非空, HEAD 会新增金额的行 (R3).
- v1 且 `amount_str` 仅空白, base 输出空串而 HEAD 输出 null 的行 (R2).

本地 seed 库的结果是 3 行, 三个列表都为空. 生产库需要单独跑.

### 5.4 复现全局注册副作用

```bash
uv run --no-project python /tmp/orchestra-07/out/proof/proof_registration.py /tmp/orchestra-07/repro-base
uv run --no-project python /tmp/orchestra-07/out/proof/proof_registration.py /tmp/orchestra-07/repro-head
```

预期: base 的 `_FORMATTERS` 有 `amount_str`, HEAD 为空; base 的 `resolve_amount(v1 "9.99")` 是 `'9.99'`, HEAD 是 `None`.

## 6. 单模型说明与局限

- 本轮只运行了一款模型 `deepseek-v4.1-flash-expires-on-0910`, 没有做不同模型同题调查和合并.
- 这次变更虽然只有 19 行, 但改的是跨仓库读取的导出金额语义, 还牵涉外部归档服务, 按宽影响标准本应做多模型同题调查. 本轮未做, 这是能力/范围缺口, 不是"已确认多模型一致".
- 已有真实证明的事实保留原证据级别, 没有因为单模型就降级或改成未证实; 未证实的事实仍然是未证实.
- 没有生产数据库, 没有归档服务源码/入口/日志, 没有生产进程的 `amountlib.__file__` 观测. 因此 R1-R3 的"是否存在这类数据"和 R6 的"生产库版本"都停在本地证据.

## 附录 A: 原始命令与输出

### A.1 环境与仓库状态

```bash
cd /tmp/orchestra-07/drill-ts001-red
git rev-parse HEAD
git status --porcelain=v1
git diff --stat HEAD
git ls-files
```

```text
04ddf931fd161baea18b0a0d315da8d41eb7cf7e
(无输出)
(无输出)
.gitignore
README.md
amountlib/__init__.py
amountlib/core.py
amountlib/legacy.py
app/__init__.py
app/clamp.py
app/legacy_sync.py
app/orders.py
db/schema.sql
db/seed.py
pyproject.toml
scripts/dump_orders.py
```

### A.2 base/HEAD payload 全量 probe 输出

base:

```bash
cd /tmp/orchestra-07/out
uv run --no-project python proof/probe_payloads.py "$PWD/repo-base"
```

```text
repo = /tmp/orchestra-07/out/repo-base
app.orders file = /tmp/orchestra-07/out/repo-base/app/orders.py
{"id": 1, "payload": {"schema": "v2", "amount": "12.50"}, "result": [{"id": 1, "amount": "12.50"}]}
{"id": 2, "payload": {"schema": "v1", "amount_str": "9.99"}, "result": [{"id": 2, "amount": "9.99"}]}
{"id": 3, "payload": {"schema": "v1", "amount_str": ""}, "result": [{"id": 3, "amount": null}]}
{"id": 4, "payload": {"schema": "v1", "amount_str": null}, "result": [{"id": 4, "amount": null}]}
{"id": 5, "payload": {"schema": "v1"}, "result": [{"id": 5, "amount": null}]}
{"id": 6, "payload": {"schema": "v1", "amount_str": " 9.99 "}, "result": [{"id": 6, "amount": "9.99"}]}
{"id": 7, "payload": {"schema": "v1", "amount_str": "N/A"}, "result": [{"id": 7, "amount": "N/A"}]}
{"id": 8, "payload": {"schema": "v1", "amount_str": "1,234.50"}, "result": [{"id": 8, "amount": "1,234.50"}]}
{"id": 9, "payload": {"schema": "v2", "amount": null, "amount_str": "5.00"}, "result": [{"id": 9, "amount": null}]}
{"id": 10, "payload": {"schema": "v2", "amount": "", "amount_str": "6.00"}, "result": [{"id": 10, "amount": null}]}
{"id": 11, "payload": {"schema": "v2", "amount": "0"}, "result": [{"id": 11, "amount": "0"}]}
{"id": 12, "payload": {"schema": "v1", "amount_str": "0"}, "result": [{"id": 12, "amount": "0"}]}
{"id": 13, "payload": {"schema": "v1", "amount_str": "   "}, "result": [{"id": 13, "amount": ""}]}
{"id": 14, "payload": {"schema": "v1", "amount_str": "\t\n"}, "result": [{"id": 14, "amount": ""}]}
```

HEAD:

```bash
uv run --no-project python proof/probe_payloads.py "$PWD/repo-head"
```

```text
repo = /tmp/orchestra-07/out/repo-head
app.orders file = /tmp/orchestra-07/out/repo-head/app/orders.py
{"id": 1, "payload": {"schema": "v2", "amount": "12.50"}, "result": [{"id": 1, "amount": "12.50"}]}
{"id": 2, "payload": {"schema": "v1", "amount_str": "9.99"}, "result": [{"id": 2, "amount": "9.99"}]}
{"id": 3, "payload": {"schema": "v1", "amount_str": ""}, "result": [{"id": 3, "amount": null}]}
{"id": 4, "payload": {"schema": "v1", "amount_str": null}, "result": [{"id": 4, "amount": null}]}
{"id": 5, "payload": {"schema": "v1"}, "result": [{"id": 5, "amount": null}]}
{"id": 6, "payload": {"schema": "v1", "amount_str": " 9.99 "}, "result": [{"id": 6, "amount": "9.99"}]}
{"id": 7, "payload": {"schema": "v1", "amount_str": "N/A"}, "raised": "ValueError", "message": "无法解析金额: 'N/A'"}
{"id": 8, "payload": {"schema": "v1", "amount_str": "1,234.50"}, "raised": "ValueError", "message": "无法解析金额: '1,234.50'"}
{"id": 9, "payload": {"schema": "v2", "amount": null, "amount_str": "5.00"}, "result": [{"id": 9, "amount": "5.00"}]}
{"id": 10, "payload": {"schema": "v2", "amount": "", "amount_str": "6.00"}, "result": [{"id": 10, "amount": "6.00"}]}
{"id": 11, "payload": {"schema": "v2", "amount": "0"}, "result": [{"id": 11, "amount": "0"}]}
{"id": 12, "payload": {"schema": "v1", "amount_str": "0"}, "result": [{"id": 12, "amount": "0"}]}
{"id": 13, "payload": {"schema": "v1", "amount_str": "   "}, "result": [{"id": 13, "amount": null}]}
{"id": 14, "payload": {"schema": "v1", "amount_str": "\t\n"}, "result": [{"id": 14, "amount": null}]}
```

日志末尾还有一行 `JSON_SUMMARY=` 的机器可读汇总, 内容与上面逐行相同, 完整原文见 `/tmp/orchestra-07/out/proof/probe-base.log` 和 `probe-head.log`.

### A.3 本地 seed 库扫描

```bash
cd /tmp/orchestra-07/out
uv run --no-project python proof/scan_db.py "$PWD/repo-head" "$PWD/repo-head/var/orders.db"
```

```text
repo = /tmp/orchestra-07/out/repo-head
db   = /tmp/orchestra-07/out/repo-head/var/orders.db
rows = 3
v1 且 amount_str 非空但 parse_amount 会抛 ValueError 的行: []
amount 为 null/空串但 amount_str 非空, HEAD 会新增金额的行: []
v1 且 amount_str 仅空白, base 输出空串而 HEAD 输出 null 的行: []
```

### A.4 消费者对异常 amount 的处理

```bash
cd /tmp/orchestra-07/out
cat > proof/export-invalid-base-style.json <<'EOF'
[
  {"id": 7, "amount": "N/A"},
  {"id": 8, "amount": "1,234.50"},
  {"id": 3, "amount": null}
]
EOF
bash /tmp/orchestra-07/orders-consumer/src/run.sh proof/export-invalid-base-style.json
```

```json
{
  "total": null,
  "missing": [
    3
  ]
}
```

说明: `Number("N/A")` 是 NaN, `JSON.stringify` 把 NaN 写成 null, 所以 base 风格的非数字金额会让合计静默变成 null.

纯空白路径:

```bash
bash /tmp/orchestra-07/orders-consumer/src/run.sh proof/export-whitespace-base.json
bash /tmp/orchestra-07/orders-consumer/src/run.sh proof/export-whitespace-head.json
```

```json
{
  "total": 0,
  "missing": []
}
```

```json
{
  "total": 0,
  "missing": [
    13
  ]
}
```

### A.5 归档探测

```bash
cd /tmp/orchestra-07/out
uv run --no-project python proof/proof_archive.py "$PWD/repo-head"
getent hosts archive.example.invalid
grep -n "orders_archive" repo-head/db/schema.sql
```

```text
repo = /tmp/orchestra-07/out/repo-head
ARCHIVE_URL = https://archive.example.invalid/orders
ARCHIVE_TOKEN in env before = False
[无 token] raised RuntimeError: 缺 ARCHIVE_TOKEN, 本地无法推送归档
[假 token, 无 orders_archive 表] raised OperationalError: no such table: orders_archive
[假 token, 有 orders_archive 表] returned {'url': 'https://archive.example.invalid/orders', 'pushed': 1}
注意: 上面第三次只统计本地表行数, 源码没有任何 HTTP 调用,
所以它不能证明外部服务收到无 amount 的订单后会丢弃还是保留.
```

```text
(getent 无输出, 退出码 2)
(grep 无输出, 退出码 1)
```

### A.6 原仓库最终状态

```bash
cd /tmp/orchestra-07/drill-ts001-red
git status --porcelain=v1
git rev-parse HEAD
git diff --stat HEAD
```

```text
(无输出)
04ddf931fd161baea18b0a0d315da8d41eb7cf7e
(无输出)
```

产品代码和测试未修改. 一次误建的 `.venv/` 和 `uv.lock` 已删除, 未进入 Git.
