# 交接: payout-service HEAD e807b06 对导出线格式的影响

结论: 不要单独合入. 现版消费者会直接崩 (退出码 1); 更麻烦的是金额改名在下游是静默失败, 一旦有人只解包不换键, 账目算成 `total: null`, `missing: []`, 退出码 0. 必须与消费者同一发布窗口一起改, 且要同时改两个键 (信封 `rows` 与金额 `amount_value`).

## 1. 做了什么

变更: `e807b06` 只改 2 个文件 2 行.

- `app/orders.py:15`: 行内键名 `amount` 改为 `amount_value`.
- `scripts/dump_orders.py:19`: 写文件从裸数组改为 `{"schema": "orders-export/2", "rows": [...]}`.
- `scripts/dump_orders.py:20`: 打印到 stdout 仍是裸数组 (这行没改, 但里面的键已经被上一行上游改了).

历史定位:

```bash
git log --oneline -20              # 011ec25 基线, 04ddf93 v1 回退解析, e807b06 本次
git show e807b06                   # 2 文件 2 行的完整 diff
git log --all --oneline -S"amount_value"   # 只有 e807b06
git log --all --oneline -S"orders-export"  # 只有 e807b06
git blame -L 15,15 -- app/orders.py        # e807b06
```

读过的文件: `app/orders.py`, `scripts/dump_orders.py`, `amountlib/{__init__,core,legacy}.py`, `db/{schema.sql,seed.py}`, `app/{clamp,legacy_sync}.py`, `README.md`, `pyproject.toml`; 消费者仓库 `README.md`, `package.json`, `src/run.sh`, `src/ledger.js` (全文 13 行).

实际跑过的: 在 `/tmp/orchestra-07/out/ts003-gap-work/{base,head}` 两个 `git archive` 副本里跑真实入口 `db/seed.py` + `scripts/dump_orders.py`, 再跑真实消费者 `orders-consumer/src/ledger.js`. 仓库本身零写入 (跑完 `git status --porcelain --ignored` 只剩原有的 `!! .agents/`).

检索范围: 两个仓库全树 (排除 `.git`), 加上同机 `/tmp/orchestra-07` 全目录 (排除 `.git`, `node_modules`, 本任务工作目录). 关键词 `amount`, `amount_value`, `read_orders`, `orders.export`, `orders-export`, `dump_orders`, `ledger.js`.

来源限制:

- 两个仓库都没有可读的 PR 或评审记录. payout 的 `origin` 指向本机 `/tmp/orchestra-07/drill-ts003-wide`, 历史与本地完全相同; 消费者仓库没有 remote. 提交消息里没有 PR 编号. 所以没有讨论材料可引, 也没看到别的分支做过下游适配.
- 技能加载: `~/.agents/skills/blast-radius/SKILL.md` 不存在; 本仓库内有 `.agents/skills/blast-radius/SKILL.md` 及其 `reference/`, 本次按该副本执行.
- 能力缺口: 按要求只授权一款模型, 没有第二路同题调查. 下面 4 级事实是实跑证明的, 保留 4 级; 只是少了交叉核对这一层.

未覆盖范围: 生产怎么把这份 JSON 交给消费者 (共享目录 / 管道 / 拷贝), 生产 `orders` 表的数据分布, 这两个仓库之外是否还有读者. 三处都没有配置或部署文件可查, 见第 3 节 R3 与第 4 节末.

## 2. 关键安全事实与证据级别

### F1. 现版消费者读到新导出会崩, 是响亮失败 (4 级)

`src/ledger.js:3` 把整个文件 `JSON.parse` 成 `rows`, `:6` 直接 `for (const row of rows)` 迭代. 新导出顶层是对象, 不是数组.

原始输出 (真实消费者, 真实新导出):

```
TypeError: rows is not iterable
    at file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6:19
Node.js v24.19.0
consumer exit=1
```

同一份消费者读基线导出正常: `{"total": 22.490000000000002, "missing": [3]}`, 退出码 0. 证明脚本 `proof_consumer_compat.py` 对两边都断言 `total≈22.49` 且 `missing==[3]`, 基线 PASS, 新导出 FAIL, 脚本退出码 1.

停在这里的理由: 这就是真实消费者代码 + 真实导出文件, 不需要再往上走. 没做的是在生产环境复现 (5 级), 因为没有生产数据和部署入口.

### F2. 金额改名本身是静默失败, 比崩溃更危险 (4 级)

`src/ledger.js:7` 用 `row.amount === null` 判"没有金额", `:11` 用 `Number(row.amount)` 累加. 键不存在时: `undefined === null` 为假, `Number(undefined)` 是 `NaN`, 累加后 `total` 变 `NaN`, `JSON.stringify` 把 `NaN` 输出成 `null`, `missing` 保持空, 退出码 0.

原始输出 (模拟"已适配信封, 只读 `.rows`, 没换键名"的消费者, 跑 HEAD 导出):

```
--- HEAD 导出 rc=0 {"total":null,"missing":[]}
--- HEAD stdout rc=0 {"total":null,"missing":[]}
confirmed: 退出码 0, total=null, missing=[]  -> 静默算错账
```

证明脚本 `proof_silent_nan.py`, 它断言这个静默结果确实出现 (看到 `total` 是数字或 `missing` 非空就失败).

停在这里的理由: 消费者代码是固定的 13 行, 行为可复现. 为什么危险: 崩溃会被退出码和日志抓住, 静默错账不会; 账目总额变成 `null`, 却没有任何一条订单进 `missing`.

### F3. 只有键名和外层变了, 金额值逐个相同 (4 级)

`proof_wire_diff.py` 逐项断言: 基线 `[{"id":1,"amount":"12.50"},{"id":2,"amount":"9.99"},{"id":3,"amount":null}]`, 新导出 `{"schema":"orders-export/2","rows":[... "amount_value" ...]}`, 值序列都是 `["12.50","9.99",null]`, id 都是 `[1,2,3]`. 脚本退出码 0.

意义: 解析逻辑没退化, 风险全在线上格式, 不在数值.

### F4. 导出侧自己仍然正常 (4 级)

`db/seed.py` + `scripts/dump_orders.py` 退出码 0, 生成 219 字节文件 (基线 130 字节). 原始内容见第 5 节复现输出. 所以 payout 侧不会因为这次改动报错, 问题只在下游.

### F5. 文件是信封, stdout 还是裸数组, 但数组里已经换了键名 (事实 4 级, 是否有人用 stdout 未证实)

`scripts/dump_orders.py:19` 写 `{"schema": ..., "rows": rows}`, `:20` 打印 `json.dumps(rows)`. 实测:

```
文件: {"schema": "orders-export/2", "rows": [{"id": 1, "amount_value": "12.50"}, ...]}
stdout: [{"id": 1, "amount_value": "12.50"}, {"id": 2, "amount_value": "9.99"}, {"id": 3, "amount_value": null}]
```

含义: 走 stdout 的通道看起来还是"数组", 形状像兼容, 实际键名已变. 把这个 stdout 喂给现版消费者: `{"total":null,"missing":[]}`, 退出码 0, 不崩也不错账地静默.

### F6. 仓库内没有第二个调用者 (3 级)

`read_orders` 唯一 import 是 `scripts/dump_orders.py:10`, 唯一使用是 `:17`. `orders.export.json` 在仓库里只出现在 `scripts/dump_orders.py:12`. `app/clamp.py` 和 `app/legacy_sync.py` 不碰金额也不碰这个文件. 检索命令见第 1 节, 范围是两仓库全树.

覆盖不到: Python 仓库之外的读者 (Node 消费者已单独查过), 以及生产里可能是另一份消费者版本.

## 3. 风险

### R1. 现版消费者读取新导出直接失败

- 位置: `src/ledger.js:3,6` + `scripts/dump_orders.py:19`.
- 概率: 生产跑的就是这份消费者代码时, 必然 (100%).
- 代价: 账目输出中断, 退出码 1. 会被发现, 但下游整条账目链路停摆直到修好.
- 检查: `bash /tmp/orchestra-07/out/ts003-gap-work/repro.sh`, 看最后 `consumer exit=1`.

### R2. 下游改成"只解包不改键"后静默错账

- 位置: `scripts/dump_orders.py:19` 换形状 + `app/orders.py:15` 换键名, 对端 `src/ledger.js:7,11` 仍在读 `amount`.
- 概率: 未证实. 取决于下游怎么改, 以及生产走文件还是走 stdout. 只要有人"顺手"只处理顶层 `rows`, 就是 100% 触发.
- 代价: `total` 变成 `null`, `missing` 空, 退出码 0. 没有报错, 没有缺失清单, 对账时才会发现, 且很难倒查是哪天开始的.
- 检查: `proof_silent_nan.py`, 看 `{"total":null,"missing":[]}`.

### R3. 两个仓库之外还有按 `amount` 取值的读者

- 位置: 未知.
- 概率: 未证实, 缺生产下游清单.
- 代价: 同 R2, 静默取到 `undefined`.
- 检查: 拿生产的消费者清单逐个 grep `amount`; 或看导出文件的所有读取方.

### R4. 两个仓库发布不同步

- 位置: 跨仓库约定, 无版本协商.
- 概率: 只要不是同一窗口发布就必然出现. 消费者 `src/ledger.js` 完全不读 `schema` 字段 (全文 13 行只有 `amount` 与 `id`), 所以 `"orders-export/2"` 这个版本标记现在拦不住任何旧读者.
- 代价: 发布窗口内按 R1 或 R2 坏.
- 检查: 看两边发布记录的时间差; 或者先在消费者加版本判断再上导出.

### R5. 父提交 `04ddf93` 带来的导出失败 (不属本次 HEAD, 但可能和本次一起上线)

- 位置: `app/orders.py:14` 调用 `parse_amount`, 非数字文本抛 `ValueError`; `scripts/dump_orders.py:17` 在 `:19` 写文件之前, 所以导出失败时旧文件原封不动.
- 实测: 插一条 `{"schema":"v1","amount_str":"1,234.50"}` 后跑导出, 退出码 1, 堆栈 `ValueError: 无法解析金额: '1,234.50'`; 已有导出文件 md5 前后相同 (`4e6d3dad...`), 消费者继续读陈旧数据.
- 概率: 未证实, 缺生产数据. 带千分位逗号或货币符号的历史 `amount_str` 都会命中.
- 代价: 导出静默停更, 消费者读到旧账, 且不报错.
- 检查: 对生产库副本跑一次导出; 或先跑 `SELECT id, payload FROM orders WHERE payload NOT LIKE '%"amount":%' AND payload LIKE '%"amount_str"%'` 看候选.

## 4. 已排除项

- 金额数值没变: `proof_wire_diff.py` 逐项比对, 退出码 0 (4 级).
- 仓库内没有别的 `read_orders` 调用者, 也没有别的代码读导出文件: 检索命令与范围见第 1 节, 命中只有 `scripts/dump_orders.py:10,12,17` (3 级, 边界见 F6).
- amountlib 就是仓库内 2.4.0: `proof_env.py` 断言 `VERSION=="2.4.0"`, `amountlib.__file__` 落在副本目录内, Python 3.14.7 (满足 `>=3.11`); `scripts/dump_orders.py:8` 把仓库根插到 `sys.path` 最前, 实跑通过 (4 级).
- 空金额行为保持: payload `{"schema":"v1","amount_str":""}` 仍导出 `null`, 消费者仍记 `missing: [3]` (4 级).
- `app/clamp.py`, `app/legacy_sync.py` 与本次无关: 前者只做数量裁剪, 后者读 `orders_archive` 且本地不可运行 (缺表与 token), 都不碰 `read_orders` 或导出文件 (3 级, 只读代码).
- 编码与导入方式没变: `ensure_ascii=False` 仍在, 输出路径仍是 `var/orders.export.json` (3 级, 读代码).
- "schema 字段能保护旧消费者": 不成立. 消费者不读 `schema`, 版本标记目前只是元数据 (3 级, `src/ledger.js` 全文).

## 5. 合并前最便宜的复现

脚本落在 `/tmp/orchestra-07/out/ts003-gap-work/repro.sh`, 全文:

```bash
#!/usr/bin/env bash
# 最便宜的复现: 在临时副本里跑真实入口, 不写两个仓库.
# 用法: bash repro.sh   需要 git, tar, uv, node.
set -u
SRC=/tmp/orchestra-07/drill-ts003-gap
CONS=/tmp/orchestra-07/orders-consumer
T=$(mktemp -d)
git -C "$SRC" archive HEAD | tar -x -C "$T"
(
  cd "$T" || exit 1
  uv run --no-project python db/seed.py >/dev/null
  uv run --no-project python scripts/dump_orders.py >/dev/null
) || exit 1
echo "== 导出文件 =="
cat "$T/var/orders.export.json"; echo

echo "== 现版消费者读新导出 =="
node "$CONS/src/ledger.js" "$T/var/orders.export.json"
echo "consumer exit=$?"

echo "== 只解包 .rows, 仍读旧键 amount 的消费者 =="
cat > "$T/peek.mjs" <<'JS'
import fs from "node:fs";
const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const rows = payload.rows ?? payload;
let total = 0; const missing = [];
for (const row of rows) {
  if (row.amount === null) { missing.push(row.id); continue; }
  total += Number(row.amount);
}
console.log(JSON.stringify({ total, missing }));
JS
node "$T/peek.mjs" "$T/var/orders.export.json"
echo "peek exit=$?"
rm -rf "$T"
```

实际运行尾部输出:

```
== 现版消费者读新导出 ==
TypeError: rows is not iterable
    at file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6:19
consumer exit=1
== 只解包 .rows, 仍读旧键 amount 的消费者 ==
{"total":null,"missing":[]}
peek exit=0
```

两行就是判断依据: 崩溃 (可见) 与静默错账 (不可见). 合入条件由你定: 要么消费者同窗口改成读 `payload.rows` 且读 `row.amount_value`, 要么在消费者侧按 `schema` 做版本判断后再上线.

## 附: 工作文件

- `/tmp/orchestra-07/out/ts003-gap-work/base/` 父提交 `04ddf93` 的完整副本 (含跑出来的 `var/`).
- `/tmp/orchestra-07/out/ts003-gap-work/head/` HEAD `e807b06` 的完整副本.
- `proof_env.py`, `proof_wire_diff.py`, `proof_consumer_compat.py`, `proof_silent_nan.py`, `repro.sh`.
- `base.stdout.json`, `head.stdout.json` 是两边导出脚本的 stdout 原文; `base.stderr.txt`, `head.stderr.txt` 是空.
