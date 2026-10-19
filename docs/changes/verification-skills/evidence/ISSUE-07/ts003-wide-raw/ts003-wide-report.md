# payout-service e807b06 blast-radius 交接报告 (多模型同题合并)

调查对象: HEAD `e807b06ca2a9cb88413390a298f55b84d3ac7869`, "导出线格式改为 orders-export/2, 金额字段改名 amount_value".
结论: 不建议按当前形态单独合入. 金额计算本身没坏, 坏的是跨仓库共享的导出 JSON: 现有消费者读新文件 100% 崩溃; 若只适配外层或改读 stdout, 消费者会以退出码 0 交付错误账本. 两条都有第 4 级证据.
建议: 与消费者同批修改 `{schema, rows}` 外层和 `amount_value` 字段, 并明确 stdout 与文件谁是规范出口; 或者保留旧兼容出口. 不要只改一处.
多模型合并记录: `/tmp/orchestra-07/out/ts003-wide-merge.md`.

## 1. 做了什么

变更 (事实/2 级): 本次只改 2 个文件各 1 行.

- `app/orders.py:15`: 输出字典键 `amount` -> `amount_value`.
- `scripts/dump_orders.py:19`: 文件从裸数组改为 `{"schema": "orders-export/2", "rows": [...]}`.
- `scripts/dump_orders.py:20` 未改: 同一次运行仍 `print` 裸数组, 但数组元素的键已改名.

历史 (事实/2 级):

- `git log --oneline`: `e807b06` (HEAD), `04ddf93` (HEAD~1, 删旧 amount_str 格式化符号并加 parse_amount 回退), `011ec25` (基线).
- `git blame` 确认两处改动都来自 `e807b06`; amountlib 三个文件来自基线, 本次未动.
- `git ls-remote origin` / `git rev-parse origin/master`: origin/master = `04ddf93` = HEAD~1, 本次提交尚未推送. remote 指向本机 `/tmp/orchestra-07/payout-service`, 该目录内容未读.
- 提交消息没有 PR 或分支编号, 没有可读的评审讨论. 这是来源限制, 不编造 PR 内容.

读过的位置 (事实): 本仓库全部 13 个文件, 消费者仓库全部 5 个文件 (`package.json`, `README.md`, `src/ledger.js`, `src/run.sh`, `.gitignore`), 两仓库 git 历史, 以及技能目录 4 份文档.

跑过的命令 (事实/4 级):

- 用 `git archive` 在仓库外做 HEAD 与 HEAD~1 两份干净副本, 各自跑真实 `db/seed.py` 与 `scripts/dump_orders.py`.
- 用未改动的 `/tmp/orchestra-07/orders-consumer/src/run.sh` 与 `src/ledger.js` 读两版导出文件和 HEAD 的 stdout.
- 两路不同模型的会话按同一份任务书独立调查: A 路 `cli/gpt-6.1-sol` / xhigh, B 路 `cli/glm-5.3-flash` / xhigh. 各自跑自己的可失败脚本, 输出分别留在 `router-a/` 与 `router-b/`.
- 合并人重跑了 A 的 `proofs/prove_all.py`, B 的 `f2/f3/f4` 三个脚本, 以及自己写的 `repro.sh`; 输出与两路报告一致.
- 未改任何产品代码, 测试或配置. 调查后两仓库 `git status --short` 均为空.

覆盖边界 (未证实): 没有生产运行时, 调度配置, 部署顺序, 生产数据或其他仓库的读取权限. 因此不声称生产已经发生故障, 也不声称生产只有这一个消费者. 别的本机目录, origin 仓库内容, 外部脚本均未审计.

## 2. 关键安全事实与证据级别

级别: 1 单独断言, 2 真实 file:line 或库源码, 3 逐步走查失败路径, 4 实跑且判断错会失败的脚本, 5 运行中的应用复现. 本报告最高 4 级, 没有 5 级.

### K1. 现有消费者读新导出文件会显式崩溃 (4 级)

`src/ledger.js:3` 把整个文件 `JSON.parse` 成对象, `:6` 直接 `for (const row of rows)`. 新文件顶层是普通对象, 不可迭代, Node 在进入金额逻辑前抛 TypeError. 真实执行结果:

```text
file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6
for (const row of rows) {
                  ^

TypeError: rows is not iterable
    at file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6:19
...
Node.js v24.19.0
file_consumer_exit=1
```

HEAD~1 旧文件同一消费者正常: `{"total": 22.490000000000002, "missing": [3]}`, exit 0.
停在第 4 级: 真实代码, 真实文件, 真实退出码; 没有在长期运行的生产应用里复现.

### K2. 只适配外层, 字段仍读 amount: 不崩, 静默算错 (4 级)

假设消费者已改成遍历 `.rows`, 但 `ledger.js:7,11` 仍读 `row.amount`. 新行没有该键, 结果是 `undefined`; `undefined === null` 为假, 所以金额缺失行不会被记入 missing; `Number(undefined)` 是 NaN, 累加后 total 也是 NaN; `JSON.stringify` 把 NaN 写成 `null`. 真实 Node 输出:

```json
{
  "total": null,
  "missing": []
}
stdout_consumer_exit=0
```

对照组: 旧格式输出 total `22.490000000000002`, missing `[3]`; id 3 是金额为 null 的行, 现在从缺失列表里消失.
停在第 4 级: "只适配外层"是条件性的消费者修改, 不是声称消费者已经这样改; 循环语义和序列化结果是用真实 Node 与真实数据跑的.

### K3. stdout 仍是裸数组, 但旧字段契约已破 (4 级)

`scripts/dump_orders.py:19-20` 在同一次运行里先写文件再 print, 不是两个互斥分支. HEAD 真实 stdout:

```json
[{"id": 1, "amount_value": "12.50"}, {"id": 2, "amount_value": "9.99"}, {"id": 3, "amount_value": null}]
```

把这段 stdout 原样交给未改动的消费者: exit 0, 输出 `total: null, missing: []`, 与 K2 相同. 文件消费者崩溃且显式, stdout 消费者不崩且静默, 两者风险不同. 不能用"stdout 还能遍历"证明兼容.
停在第 4 级: 真实 stdout 字节与真实消费者; 但本地未找到真实的生产 stdout 管道, 频率未证实.

### K4. 金额值与解析行为没有变化 (4 级)

| id | payload | HEAD~1 | HEAD |
| --- | --- | --- | --- |
| 1 | `{"schema":"v2","amount":"12.50"}` | `"12.50"` | `"12.50"` |
| 2 | `{"schema":"v1","amount_str":"9.99"}` | `"9.99"` | `"9.99"` |
| 3 | `{"schema":"v1","amount_str":""}` | `null` | `null` |

两版都在独立进程导入各自副本的 amountlib, 断言 `VERSION == "2.4.0"` 且导入路径在本副本内; `_FORMATTERS == {}`, 所以 v1 行走 `app/orders.py:13-14` 的 `parse_amount` 回退; v2 行走 `amountlib/legacy.py:18-19`. 分支控制输入 (v1 带 amount, v2 带 amount_str, 空串, 空格, 非法文本) 也断言过.
停在第 4 级: 代码逐字节相同, 三行真实值相同; 不覆盖生产数据分布.

### K5. 本地旧格式读取方只有消费者 ledger.js (2 级)

实际检索命令与结果:

```bash
cd /tmp/orchestra-07/drill-ts003-wide
grep -rn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=var \
  -E 'amount_value|amount_str|orders\.export\.json|"amount"|dump_orders' .
# 命中: app/orders.py:14,15; scripts/dump_orders.py:12,19;
#       amountlib/legacy.py:16,18,19,20,23; db/seed.py:9,10,11

cd /tmp/orchestra-07/orders-consumer
grep -rn --exclude-dir=.git --exclude-dir=node_modules \
  -E 'amount|rows|orders\.export|schema' .
# 代码命中只有 src/ledger.js:3,6,7,11; README.md:3 是文档描述
git log --all --name-only --pretty=format: | sort -u
# 消费者历史上只有 5 个文件, 没有第二个读取入口
```

本仓库没有读导出 JSON 的程序, 只有写方 (`dump_orders.py:12,17,19,20`). `app/legacy_sync.py:10-15` 只查 `orders_archive` 表并返回条数, 不读导出文件或 amount 字段. 消费者没有 remote, 只有 1 个提交.
停在第 2 级: 静态枚举能说明列明两个仓库内没有别的读者, 但没有部署配置或运行时入口, 不能外推到生产或其他仓库. 这是合入前最大的未知.

### K6. schema 只在新文件里, 没有本地消费者读它 (观察 4 级, 缺失 2 级)

新文件顶层是 `{schema, rows}`, stdout 仍是裸数组且没有 schema. 消费者 `ledger.js:3-13` 不检查 schema; 消费者仓库检索 `schema` 零命中. 因而现有消费者不会自动识别新旧格式, 也不会因为 schema 字段得到保护.
文件与 stdout 不再同构这一条是 4 级 (两版真实输出对比). "本地没有 schema 分派器" 是 2 级 (有限静态范围).

## 3. 风险

### R1. 文件消费者整批失败 (条件确定, 高)

- 位置: 根源 `scripts/dump_orders.py:19`, 触发点 `orders-consumer/src/ledger.js:3,6`, 入口 `src/run.sh:4`.
- 怎么坏: JSON 解析成功, 但顶层对象不能当数组遍历, 汇总前抛 TypeError, exit 1, 没有账本输出.
- 概率: 在"消费者读取本次生成的文件"条件下是确定的, 与金额取值和行数无关. 生产切换频率, 是否与消费者同批部署未证实, 不写成生产必然已发生.
- 代价: 这一批无法汇总, 重试同一文件仍然失败. 若外层调度只看生成方 exit 0 而忽略消费者 exit 1, 会变成"没有账本"的静默中断.
- 检查: 跑第 5 节复现脚本, 看 `file_consumer_exit=1` 与 `TypeError: rows is not iterable`.

### R2. 部分适配或读 stdout 时静默错账 (条件确定, 代价更高)

- 位置: `app/orders.py:15` 去掉 amount, `scripts/dump_orders.py:20` 仍打印裸数组, 消费者 `ledger.js:7,11` 仍读 amount.
- 怎么坏: 缺失字段变 undefined, 绕过 null 检查, 求和变 NaN, 序列化成 `total: null`; 金额缺失行从 `missing` 消失. 退出码 0, 无告警.
- 概率: 修 R1 的最小改法就是只改遍历目标, 字段读取分散在两处, 漏一处就触发; 若生产有 stdout 消费者, 当前提交直接触发. 本地没有找到 stdout 读取方, 频率未证实.
- 代价: 样本总额从 `22.490000000000002` 变 `null`, missing 从 `[3]` 变 `[]`. 下游若把 null 当 0 或只检查进程成功, 会得到错误账本. 金额损失的后续影响未取得生产数据, 不量化.
- 检查: 复现脚本第 2 段, 必须同时确认 total 是有效数值且 missing 含 3, 不能只看进程未崩.

### R3. 范围外还有旧读者 (概率未知, 代价同 R1/R2)

- 位置: 任何读 `var/orders.export.json` 或 `dump_orders.py` stdout 的本机其他仓库, 外部脚本, 生产任务.
- 概率与代价: 本地两个仓库查不到; 若存在, 读文件者按 R1 崩, 读 stdout 者按 R2 静默错. 没有权限枚举生产, 未证实.
- 检查: 在其他仓库和调度配置里检索 `orders.export.json`, `dump_orders`, `amount_str`, `row.amount`, `for (const row of rows)`. 当前缺这些入口.

### R4. 两出口不同构与 schema 同名不同义 (低, 当前无读者)

- 位置: `scripts/dump_orders.py:19-20`; 新 `schema` 键与订单 payload 内 `db/seed.py:9-11` 的 `schema: v1/v2` 同名不同义.
- 怎么坏: 未来若有人按导出 schema 分派, 或要求 stdout 与文件同形, 容易写错兼容分支; 今天本地没有代码读导出 schema, 当前无害.
- 概率与代价: 低, 属于后续维护风险; 检查方法是在下游检索 `schema`, 命中即人工复核语义.

### R5. 仓库没有测试或 CI 拦住这类回归 (事实, 2 级)

- 位置: 本仓库只有 `pyproject.toml` 与 9 个 py 文件, 没有 tests 目录或 CI 配置; 消费者也没有测试.
- 怎么坏: 本次改的是跨仓库契约, 单仓库测试即使存在也未必覆盖消费者; 这次没有任何自动检查会在合入前报错.
- 检查: 把第 5 节复现脚本作为合并门槛, 或加跨仓库契约测试.

## 4. 已排除项

1. 排除本次改变金额值与解析行为. 两版三行值相同; amountlib 三文件逐字节相同, 版本 2.4.0; 解析分支和回退调用记录相同. (4 级)
2. 排除本次改变 amountlib 版本, 本地补丁或 v1 格式化注册状态. 全新进程 `_FORMATTERS` 均为空, 全仓库无 `register_legacy_formatter` 调用. (4 级)
3. 排除新文件是 JSON 语法损坏. `JSON.parse` 成功, 失败发生在之后的 `for...of`. (4 级)
4. 排除输出路径, 数据库 schema, 行序变化. `OUT` 仍是 `var/orders.export.json`, `schema.sql` 与 SQL 未变, id 顺序仍 1/2/3. (4 级)
5. 排除两个已读仓库内存在已适配 `amount_value` 或按 schema 分派的第二个消费者. 消费者全部 5 个文件已读, 新符号检索零命中. 不外推到其他仓库. (2 级)
6. 排除 `app/clamp.py` 与本次有关. 它只限制下单数量, 不读写导出. (2 级)
7. 排除 `app/legacy_sync.py` 是本次导出文件的直接依赖. 当前源码不调用 `read_orders`, 不解析导出 JSON; 它要求归档表和 ARCHIVE_TOKEN, 本地未运行, 不据此为外部归档链路作安全背书. (2 级)
8. 排除把旧版浮点尾差 `22.490000000000002` 算成本次新增问题. 旧版就存在, 本次金额字符串未变. (4 级)

## 5. 合并前最便宜的复现

脚本: `/tmp/orchestra-07/out/ts003-wide-work/repro.sh`. 已实跑, 输出如下 (截取关键行):

```text
amountlib 2.4.0 /tmp/orchestra-07/out/ts003-wide-work/head/amountlib/__init__.py
=== 1) 消费者读导出文件 ===
TypeError: rows is not iterable
    at file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6:19
file_consumer_exit=1
=== 2) 消费者读导出脚本 stdout (裸数组, 旧字段名) ===
{
  "total": null,
  "missing": []
}
stdout_consumer_exit=0
PASS: 文件消费者崩 (exit 1), stdout 消费者静默错账 (exit 0, total:null, missing:[]).
```

脚本全文:

```bash
#!/usr/bin/env bash
# payout-service e807b06 合并前最便宜复现: 真 seed + 真导出 + 未改动的消费者.
# 两条链路都检查: 读文件应崩溃; 读 stdout 应静默给出 total:null.
# 任一预期不符, 本脚本非零退出.
set -uo pipefail
W=/tmp/orchestra-07/out/ts003-wide-work/head
CONS=/tmp/orchestra-07/orders-consumer/src/run.sh
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cd "$W" || exit 2
uv run python -B db/seed.py >"$TMP/seed.out" 2>&1 || { cat "$TMP/seed.out"; exit 2; }
uv run python -B -c 'import amountlib,pathlib,sys; assert amountlib.VERSION=="2.4.0"; p=pathlib.Path(amountlib.__file__).resolve(); assert str(p).startswith("/tmp/orchestra-07/out/ts003-wide-work/head/"); print("amountlib", amountlib.VERSION, p)' || exit 2
uv run python -B scripts/dump_orders.py >"$TMP/stdout.json" 2>"$TMP/dump.err" || { cat "$TMP/dump.err"; exit 2; }

echo "=== 1) 消费者读导出文件 ==="
bash "$CONS" "$W/var/orders.export.json" >"$TMP/file.out" 2>"$TMP/file.err"
file_rc=$?
cat "$TMP/file.err"
echo "file_consumer_exit=$file_rc"
[ "$file_rc" -eq 1 ] || { echo "FAIL: 期望退出 1"; exit 1; }
grep -q "TypeError: rows is not iterable" "$TMP/file.err" || { echo "FAIL: 缺 TypeError"; exit 1; }
grep -q "ledger.js:6" "$TMP/file.err" || { echo "FAIL: 报错行不符"; exit 1; }

echo "=== 2) 消费者读导出脚本 stdout (裸数组, 旧字段名) ==="
bash "$CONS" "$TMP/stdout.json" >"$TMP/stdout.out" 2>"$TMP/stdout.err"
stdout_rc=$?
cat "$TMP/stdout.out"
echo "stdout_consumer_exit=$stdout_rc"
[ "$stdout_rc" -eq 0 ] || { echo "FAIL: 期望退出 0"; exit 1; }
grep -q '"total": null' "$TMP/stdout.out" || { echo "FAIL: 期望 total:null"; exit 1; }
grep -q '"missing": \[\]' "$TMP/stdout.out" || { echo "FAIL: 期望 missing:[]"; exit 1; }

echo "PASS: 文件消费者崩 (exit 1), stdout 消费者静默错账 (exit 0, total:null, missing:[])."
```

完整证明材料:

- A 路: `router-a/proofs/prove_all.py`, `router-a/proofs/repro_file_crash.py`, `router-a/evidence/`.
- B 路: `router-b/work/f1-new.out`, `f2-rows-amount.mjs`, `f3-stdout-consumer.mjs`, `f4-values.py`.
- 合并人: `probe_amounts.py`, `probe_rows_old_field.mjs`, `consumer_head_file.*`, `consumer_head_stdout.*`, `consumer_base_file.stdout`, `head/`, `base/`.

本报告只交接材料, 未合并, 未创建 PR.
