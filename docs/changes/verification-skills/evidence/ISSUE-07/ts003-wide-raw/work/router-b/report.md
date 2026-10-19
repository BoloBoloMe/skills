# payout-service e807b06 blast-radius 调查报告 (B 路, 单路)

结论: 不建议以当前形态直接合入. 消费者读新导出文件必然崩溃 (F1, 证据级别 4, 已实跑定案); 金额值本身不变 (F4, 级别 4), 所以坏法只在线格式. 若决定合入, 必须同一批改消费者 (结构与字段名两处一起), 否则就算不崩也是静默错账.

## 1. 做了什么

读到的变更与历史:

- `git show e807b06`: 改 2 个文件各 1 行. `app/orders.py:15` 导出行字段 `amount` 改名 `amount_value`; `scripts/dump_orders.py:19` 文件输出从裸数组改成 `{"schema": "orders-export/2", "rows": [...]}`. `dump_orders.py:20` 的 stdout 仍是裸数组, 未包外层.
- `git log --oneline -20`: 共 3 个提交. 邻居 `04ddf93` 删了 amount_str 格式化符号, 改用 parse_amount 回退; `011ec25` 是基线.
- `git blame -L 15,15 -- app/orders.py` 与 `git blame -L 19,20 -- scripts/dump_orders.py`: 两处改动都归 e807b06; stdout 行 (`dump_orders.py:20`) 自基线 `011ec25` 未动.
- `git log --all -S"amount_value"`: 只有 e807b06 引入过这个符号.
- 提交消息没有分支号或 PR 号. `git ls-remote origin` 显示 origin/master 停在 `04ddf93` (即 HEAD~1), 本次提交尚未推送. 没有可读的 PR 或讨论材料, 这是来源限制; origin 指向本机 `/tmp/orchestra-07/payout-service`, 在授权范围外, 未读其内容.

查过的位置: 两仓库全部源码文件 (见第 5 节检索), amountlib 三个模块的源码, 消费者 `src/ledger.js` 全部 13 行与 `src/run.sh`, 两仓库 README.

跑过的命令与脚本 (全部留原始输出, 在 `router-b/work/`):

- 在 `repo/` (HEAD 副本) 与 `base/` (HEAD~1 副本) 各跑 `uv run python db/seed.py` 和 `uv run python scripts/dump_orders.py`, 退出码全 0. 输出: `seed-head.out`, `seed-base.out`, `dump-head-stdout.txt`, `dump-base-stdout.txt`, 以及两棵树各自的 `var/orders.export.json`.
- F1: 用消费者自己的代码 `node /tmp/orchestra-07/orders-consumer/src/ledger.js <导出文件>` 分别读新/旧文件. 输出: `f1-new.out`, `f1-old.out`.
- F2: `work/f2-rows-amount.mjs` (全文见下), 读 HEAD 真实导出文件, 模拟 "只适配外层仍读 amount". 输出: `f2.out`.
- F3: `work/f3-stdout-consumer.mjs`, 消费 HEAD 真实 stdout, 模拟旧 stdout 消费者. 输出: `f3.out`.
- F4: `work/f4-values.py`, 分别导入两棵树自己的 amountlib 与 app.orders 对比金额值. 输出: `f4.out`.

没覆盖到的范围: 生产环境与两个仓库之外的任何读者 (无授权, 查不了); origin 仓库内容; 未在长期运行的应用里复现 (所有实跑都是本机一次性运行, 到证据级别 4, 不到 5).

本次为单路调查 (B 路), 未读另一路结论, 未开新会话. 按技能 multimodel.md, 改共享线格式属宽变更, 本应多模型同题交叉核对; 这里缺第二路, 已真实证明的事实保留原证据级别, 不改标未证实. 后续可加查.

## 2. 关键安全事实与证据级别

事实 1 (事实, 级别 4): 消费者读到新导出文件必然崩, 且是显式崩.

- 用消费者仓库原封不动的 `src/ledger.js` 读 HEAD 导出文件: `TypeError: rows is not iterable` (报错指向 `ledger.js:6` 的 `for (const row of rows)`), 退出码 1. 读 HEAD~1 旧文件则正常: `{"total": 22.490000000000002, "missing": [3]}`, 退出码 0. 原始输出见 `work/f1-new.out`, `work/f1-old.out`.
- 原理: `ledger.js:3` 把整个文件 `JSON.parse` 后直接 `for...of` (`ledger.js:6`), 普通对象不可迭代, Node 抛 TypeError. 能定案 "会崩": 真实代码, 真实文件, 判定依据是退出码与原始报错.
- 停在级别 4 的理由: 没有在长期运行的应用环境里复现 (级别 5).

事实 2 (事实, 级别 4): 金额解析与金额值完全没被本次提交改变.

- `work/f4-values.py` 分别导入两棵树自己的代码, 先断言 `amountlib.VERSION == "2.4.0"` 且导入路径确在该树内, 再逐 id 对比 `read_orders` 的金额值: id 1 = "12.50", id 2 = "9.99", id 3 = None, HEAD 与 HEAD~1 完全相等, 判定错会非零退出.
- v1/v2 分支与回退: `amountlib/legacy.py:18-23` 的 `resolve_amount` 见到 payload 里有 `amount` 键走 v2 分支, 否则查 `_FORMATTERS`; `work/f4-values.py` 断言 `_FORMATTERS == {}` (全仓库无任何 `register_legacy_formatter` 调用, 检索见 `app/orders.py:14` 只有 parse_amount 回退), 所以 v1 行 (id 2/3) 返回 None, 由 `app/orders.py:13-14` 的 `parse_amount` 回退接住. 空串与 None 返回 None (`amountlib/core.py:12-16`), 非法文本抛 ValueError (`core.py:17-20`), 这些行为在脚本里全部断言过.
- 本次提交没碰 amountlib, 没碰解析路径, 值逐 id 相等. 事实 2 成立.

事实 3 (事实, 级别 4): 字段改名后, 只修外层不修字段名的读者会静默算错, 不崩.

- `work/f2-rows-amount.mjs` 读 HEAD 真实导出文件, 复用 `ledger.js:5-12` 的原循环语义, 只把遍历目标改成 `.rows`. 结果: 循环正常走完, `row.amount` 全是 `undefined` (键已叫 `amount_value`); `undefined === null` 为假, 所以 `ledger.js:7` 的缺失判断永远不命中, id 3 (金额为 null) 的 missing 标记丢失; `total += Number(undefined)` 使 total 变 NaN, `JSON.stringify` 把 NaN 序列化成 null, 消费者将打印 `{"total": null, "missing": []}`, 退出码 0. 脚本逐条断言以上判断, 判错即非零退出. 原始输出见 `work/f2.out`.
- 与事实 1 合起来是本次变更的完整坏法图谱: 结构变了会显式崩, 字段名变了会静默错.

事实 4 (事实, 级别 4): stdout 与文件不再同构.

- `work/f3-stdout-consumer.mjs` 断言: HEAD 的 stdout 解析出来是裸数组, 文件解析出来是 `{schema, rows}` 对象, 两者不再相等; 内容上 stdout 数组与文件 `rows` 一致. 原始输出见 `work/f3.out`.
- 读 stdout 的旧消费者: 不崩 (数组可迭代, `f3.out` 显示循环走完退出码 0), 但字段名已改, 与事实 3 同样的静默 NaN. 和读文件的消费者风险不同: 文件读者崩溃且显式, stdout 读者不崩且静默.

## 3. 风险

R1. 文件消费者立即崩溃. 位置: `orders-consumer/src/ledger.js:6` (触发点), 根源 `payout-service/scripts/dump_orders.py:19`. 概率: 必然, 消费者每次汇总都要读这个文件, README (`orders-consumer/README.md:2-3`) 写明这就是生产读法. 代价: 汇总不可用, 管道中断; 好在显式报错, 能立刻定位, 无数据损坏. 检查方法: `node /tmp/orchestra-07/orders-consumer/src/ledger.js var/orders.export.json; echo $?`, 预期 TypeError 与退出码 1; 或直接看 `work/f1-new.out`.

R2. 消费者只修结构不修字段名, 静默错账. 位置: `orders-consumer/src/ledger.js:7` 和 `:11` (两处读 `row.amount`). 概率: 中. 依据: 修 R1 的最小改动就是 `ledger.js:6` 附近改成遍历 `.rows`, 而字段名分散在 `:7` 与 `:11` 两处, 漏一处即触发; 失败完全静默, 退出码 0, 无任何告警, 这是比崩溃更贵的失败. 代价: total 变 null, missing 丢掉金额缺失的行 (当前数据是 id 3), 账目错误且无人发现. 检查方法: 用 `work/f2-rows-amount.mjs` 的断言对着改后的消费者跑, 期望 total 非空, missing 恰好含金额缺失的 id.

R3. stdout 旧消费者静默错账. 位置: 根源 `payout-service/scripts/dump_orders.py:20` (stdout 仍裸数组但字段已改名). 概率: 本机两仓库内未找到 stdout 消费者 (检索见第 5 节), 若生产存在管道消费者则必然触发; 范围外无法核实, 此半句是未证实. 代价: 同 R2, 静默. 检查方法: `work/f3-stdout-consumer.mjs` 同款断言对着真实的 stdout 跑.

R4. (推断, 级别 2) 导出文件新增 `schema` 键, 与订单 payload 内部的 `schema: "v1"/"v2"` (`db/seed.py:9-11`) 同名不同义, 未来若下游按 schema 分派或有人混淆两者, 兼容分支容易写错. 今天无任何代码读这个键 (见已排除项 3), 所以当前无害. 检查方法: 在消费者与下游 `grep -n schema`, 命中即复核语义.

## 4. 已排除项

1. amountlib 解析行为变化. 查了什么: `work/f4-values.py` 断言两棵树均为 vendored 2.4.0, v2 分支直读, v1 分支因 `_FORMATTERS` 为空返回 None, `parse_amount` 对 "" / None / 合法 / 非法文本四种输入的行为. 凭什么: 脚本对两棵树各自真实代码逐条断言, 判错非零退出, 全部通过 (`work/f4.out`). 级别 4.
2. 金额值本身变化. 查了什么: HEAD 与 HEAD~1 对同一份种子数据 (id 1/2/3) 的逐 id 金额值. 凭什么: `f4.out` 显示两树输出仅键名不同, 值完全相等. 级别 4.
3. 下游按 schema 分派. 查了什么: `rg -n 'schema' /tmp/orchestra-07/orders-consumer -g '!.git' -g '!node_modules'`, 退出码 1, 零命中; 消费者仓库全部文件只有 `package.json`, `README.md`, `src/ledger.js`, `src/run.sh` (find 全量枚举), 无其他入口. 凭什么: 全文件枚举 + 零命中. 级别 3. 覆盖边界: 只覆盖本机消费者仓库.
4. 输出路径变化. 查了什么: `diff -r --exclude=.git --exclude=var repo base`, 仅 `app/orders.py:15` 与 `dump_orders.py:19` 两行不同, `OUT = ROOT / "var" / "orders.export.json"` (`dump_orders.py:12`) 未动. 级别 4.
5. `read_orders` 的其他调用方. 查了什么: `rg -n 'read_orders'` 在 payout 四个目录, 命中仅定义处 `app/orders.py:7` 与唯一调用 `scripts/dump_orders.py:10,17`. 检索空结果说明没有别的调用者. 级别 3. 覆盖边界: 静态检索, 不覆盖运行时动态导入; 本仓库无此类代码.
6. `run.sh` 是否解析格式. 查了什么: 全文 2 行有效内容, `node "$(dirname "$0")/ledger.js" "$1"`, 只传文件名不碰 JSON. 级别 2 (指到真实 file:line, 未实跑 run.sh 本身, 语义等价于 f1 已实跑的直调).
7. 消费者 float 求和误差 (`22.490000000000002`, `f1-old.out`). 事实: 旧格式下就存在, 本次提交未改变 (导出值仍是字符串, `Number()` 转换逻辑未动). 级别 4 (两树实跑对比).

## 5. 合并前最便宜的复现

一条命令, 抓最要紧的问题 (R1), 判断错会以非零退出可见:

```bash
cd /tmp/orchestra-07/out/ts003-wide-work/router-b/repo \
  && uv run python db/seed.py \
  && uv run python scripts/dump_orders.py \
  && node /tmp/orchestra-07/orders-consumer/src/ledger.js var/orders.export.json; echo "exit=$?"
```

预期: 打印 `TypeError: rows is not iterable` (指向 `ledger.js:6`), `exit=1`. 已实跑, 原始输出在 `work/f1-new.out`.

证明脚本全文 (与 `work/` 下文件一致):

`work/f2-rows-amount.mjs`:

```js
// F2 证明: 消费者先适配外层 (只遍历 rows), 但仍读 row.amount, 会发生什么.
// 判定错则以非零退出. 数据来自本任务 repo/ (HEAD) 的真实导出文件.
import fs from "node:fs";
import assert from "node:assert";

const EXPORT = process.argv[2];
const raw = JSON.parse(fs.readFileSync(EXPORT, "utf8"));

// 断言环境: 读的确实是 HEAD 的新格式文件
assert.deepStrictEqual(Object.keys(raw), ["schema", "rows"], "外层应是 {schema, rows}");
assert.strictEqual(raw.schema, "orders-export/2", "schema 应为 orders-export/2");

// 假设消费者已适配外层, 复用 ledger.js 原有的循环语义 (src/ledger.js:5-12):
// for (const row of rows) { if (row.amount === null) {...} total += Number(row.amount); }
const rows = raw.rows;
let total = 0;
const missing = [];
for (const row of rows) {
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
}

// 断言判断: 不崩, 但静默算错
for (const row of rows) {
  assert.ok(!("amount" in row), `row ${row.id} 不应有 amount 字段, 实际字段: ${Object.keys(row).join(",")}`);
  assert.strictEqual(row.amount, undefined, `row ${row.id}.amount 应为 undefined`);
}
assert.ok(Number.isNaN(Number(undefined)), "Number(undefined) 应为 NaN");
assert.ok(Number.isNaN(total), `total 应为 NaN, 实际 ${total}`);
assert.deepStrictEqual(missing, [], "id 3 的缺失标记应丢掉: missing 应为空数组");
assert.strictEqual(
  JSON.stringify({ total, missing }, null, 2),
  `{
  "total": null,
  "missing": []
}`,
  "console.log(JSON.stringify(...)) 的真实输出应为 total:null, missing:[] (NaN 序列化成 null)"
);

console.log("F2 证实: 遍历 rows 不崩, row.amount 全是 undefined,");
console.log("  total 变 NaN (JSON 输出成 null), id 3 的 missing 标记丢失. 静默算错, 无任何报错.");
console.log("消费者代码将打印:", JSON.stringify({ total, missing }));
```

`work/f3-stdout-consumer.mjs`:

```js
// F3 证明: 读 dump_orders.py stdout (裸数组, 字段已改名 amount_value) 的旧消费者会怎样.
// 判定错则以非零退出. stdout 原文来自 work/dump-head-stdout.txt (真实运行 HEAD 的 dump_orders.py 所得).
import fs from "node:fs";
import assert from "node:assert";

const stdoutText = fs.readFileSync("dump-head-stdout.txt", "utf8").trim();
const fileText = fs.readFileSync("../repo/var/orders.export.json", "utf8");

const stdoutRows = JSON.parse(stdoutText);
const fileObj = JSON.parse(fileText);

// 断言: stdout 与文件不再同构
assert.ok(Array.isArray(stdoutRows), "stdout 解析出来应是裸数组");
assert.ok(!Array.isArray(fileObj) && typeof fileObj === "object", "文件解析出来应是包裹对象");
assert.deepStrictEqual(Object.keys(fileObj), ["schema", "rows"], "文件外层应是 {schema, rows}");
assert.deepStrictEqual(stdoutRows, fileObj.rows, "stdout 数组与文件 rows 内容应一致");

// 旧 stdout 消费者的循环语义 (与 ledger.js:5-12 相同): 期待数组与 amount 字段
let total = 0;
const missing = [];
for (const row of stdoutRows) {
  if (row.amount === null) {
    missing.push(row.id);
    continue;
  }
  total += Number(row.amount);
}

assert.ok(Number.isNaN(total), `total 应为 NaN, 实际 ${total}`);
assert.deepStrictEqual(missing, [], "missing 应为空数组 (id 3 的 null 标记丢失)");

console.log("F3 证实: stdout 仍是裸数组, for...of 不崩, 循环正常走完 (退出码 0).");
console.log("  但 row.amount 是 undefined, total=NaN, missing 丢掉 id 3. 与文件消费者不同: 不崩, 改为静默算错.");
```

`work/f4-values.py`: 全文见 `router-b/work/f4-values.py` (80 行, 判错即 `assert` 非零退出; 核心步骤: 对 repo/ 与 base/ 各自 `sys.path` 导入其 amountlib 与 app.orders, 断言版本 2.4.0 / 导入路径 / `_FORMATTERS == {}` / v1v2 分支与回退 / 四种 parse_amount 输入, 再逐 id 对比两树 `read_orders` 金额值并核对 DB payload 与 `db/seed.py` 种子一致).

## 附: F5 精确检索记录

旧格式 (`amount` 字段 / 顶层数组) 的读取方, 在授权的两个仓库内:

```
rg -n 'amount|JSON\.parse|readFileSync|for \(const' /tmp/orchestra-07/orders-consumer -g '!.git' -g '!node_modules'
```

命中 5 行: `src/ledger.js:3,6,7,11` (唯一的代码读取方) 与 `README.md:3` (文档). `run.sh`, `package.json` 无命中; `node_modules` 目录不存在.

```
rg -n 'amount_value|"amount"|amount_str|orders-export|orders\.export' /tmp/orchestra-07/drill-ts003-wide -g '!.git' -g '!.agents' -g '!var'
```

命中: `app/orders.py:14,15`, `scripts/dump_orders.py:12,19`, `amountlib/legacy.py:16,18,19,20,23`, `db/seed.py:9,10,11`. 其中写入旧格式的只有 `app/orders.py:15` (本次已改); `amountlib/legacy.py` 与 `db/seed.py` 里的 `amount` 是订单 payload 内部字段, 不是导出线格式. 顶层数组除 `ledger.js` 外无人读: `rg -n 'read_orders|orders\.export'` 在 payout 仓库仅命中 `dump_orders.py`.

覆盖边界 (空结果也写边界): 只覆盖本机这两个仓库. 生产环境与更多仓库的读者在授权范围外, 查不到; payout 的 origin (`/tmp/orchestra-07/payout-service`) 内容未读, 只知其 master 停在 `04ddf93` (`git ls-remote origin`); `var/` 下是生成物未纳入检索, 但两份导出文件本体已人工比对并全文贴在本报告中.

## 附: 关键原始输出

`work/f1-new.out` (F1, 消费者读新文件):

```
### node ledger.js HEAD(var/orders.export.json, 新格式)
file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6
for (const row of rows) {
                  ^

TypeError: rows is not iterable
    at file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6:19
    at ModuleJob.run (node:internal/modules/esm/module_job:439:25)
    at async asyncRunEntryPointWithESMLoader (node:internal/modules/run_main:101:5)

Node.js v24.19.0
exit=1
```

`work/f1-old.out` (基线, 消费者读旧文件):

```
### node ledger.js HEAD~1(旧格式, 基线)
{
  "total": 22.490000000000002,
  "missing": [
    3
  ]
}
exit=0
```

`work/f2.out`:

```
### node f2-rows-amount.mjs ../repo/var/orders.export.json
F2 证实: 遍历 rows 不崩, row.amount 全是 undefined,
  total 变 NaN (JSON 输出成 null), id 3 的 missing 标记丢失. 静默算错, 无任何报错.
消费者代码将打印: {"total":null,"missing":[]}
exit=0
```

`work/f3.out`:

```
### node f3-stdout-consumer.mjs
F3 证实: stdout 仍是裸数组, for...of 不崩, 循环正常走完 (退出码 0).
  但 row.amount 是 undefined, total=NaN, missing 丢掉 id 3. 与文件消费者不同: 不崩, 改为静默算错.
exit=0
```

`work/f4.out`:

```
Using CPython 3.14.7
Creating virtual environment at: .venv
HEAD: read_orders -> [{'id': 1, 'amount_value': '12.50'}, {'id': 2, 'amount_value': '9.99'}, {'id': 3, 'amount_value': None}]
HEAD~1: read_orders -> [{'id': 1, 'amount': '12.50'}, {'id': 2, 'amount': '9.99'}, {'id': 3, 'amount': None}]
F4 证实: id 1/2/3 金额值 HEAD 与 HEAD~1 完全一致: '12.50', '9.99', None.
  v1 payload (id 2/3) 因无人注册格式化函数, resolve_amount 返回 None, 走 parse_amount 回退.
  本次提交只改导出键名与文件外层, 未改 amountlib 与解析路径.
exit=0
```

两份导出文件全文:

HEAD (`repo/var/orders.export.json`):

```json
{
  "schema": "orders-export/2",
  "rows": [
    {
      "id": 1,
      "amount_value": "12.50"
    },
    {
      "id": 2,
      "amount_value": "9.99"
    },
    {
      "id": 3,
      "amount_value": null
    }
  ]
}
```

HEAD~1 (`base/var/orders.export.json`):

```json
[
  {
    "id": 1,
    "amount": "12.50"
  },
  {
    "id": 2,
    "amount": "9.99"
  },
  {
    "id": 3,
    "amount": null
  }
]
```
