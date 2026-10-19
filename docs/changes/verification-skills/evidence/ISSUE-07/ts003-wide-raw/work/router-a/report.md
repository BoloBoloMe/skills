# payout-service e807b06 影响范围调查, A 路

**不建议按当前提交单独合入.** 已有消费者读新文件会退出 1. 只适配外层 rows, 或改读 stdout, 都会退出 0 但产出错误账本. 这两条均有第 4 级证据, 不是仅凭 diff 推测.

## 1. 做了什么

### 变更与历史

- 调查时间: 2026-10-19 UTC. 本路独立调查, 未开新会话, 未读其他调查产物.
- 本仓库: `/tmp/orchestra-07/drill-ts003-wide`.
- 消费者仓库: `/tmp/orchestra-07/orders-consumer`.
- 工作区: `/tmp/orchestra-07/out/ts003-wide-work/router-a`.
- 下文 `app/...`, `amountlib/...`, `db/...`, `scripts/...` 均相对本仓库. `orders-consumer/...` 相对消费者仓库. 证明与输出路径相对本工作区.
- HEAD: `e807b06ca2a9cb88413390a298f55b84d3ac7869`.
- HEAD~1: `04ddf931fd161baea18b0a0d315da8d41eb7cf7e`.
- 消费者 HEAD: `a47893d0dea16e39197603ee28b7b8b467efbbee`, package.json 版本 `0.9.2`.

[事实/2级] 本次确实只改两行:

1. `app/orders.py:15`: 返回行的 `amount` 改名 `amount_value`.
2. `scripts/dump_orders.py:19`: 文件由数组改为 `{"schema":"orders-export/2","rows":[...]}`.

[事实/2级] `04ddf93` 才是删除旧格式化函数/注册调用, 添加 `parse_amount` 回退的提交. 本次没有再次修改解析逻辑. `011ec25` 是基线, `amountlib/core.py` 和 `amountlib/legacy.py` 全部来自该提交. 不能把父提交的解析变更归给本次提交.

实际读取了两仓库全部产品文件: 本仓库 13 个, 消费者 5 个. 还读了任务指定的技能及 3 份参考文档. 历史命令包括:

```bash
git -C /tmp/orchestra-07/drill-ts003-wide log --oneline -20
git -C /tmp/orchestra-07/drill-ts003-wide log --format=fuller -20
git -C /tmp/orchestra-07/drill-ts003-wide show HEAD
git -C /tmp/orchestra-07/drill-ts003-wide show HEAD~1
git -C /tmp/orchestra-07/drill-ts003-wide blame -L 1,16 -- app/orders.py
git -C /tmp/orchestra-07/drill-ts003-wide blame -L 7,24 -- scripts/dump_orders.py
git -C /tmp/orchestra-07/drill-ts003-wide log --follow -p -- app/orders.py
git -C /tmp/orchestra-07/drill-ts003-wide log --follow -p -- scripts/dump_orders.py
git -C /tmp/orchestra-07/drill-ts003-wide blame -- amountlib/core.py
git -C /tmp/orchestra-07/drill-ts003-wide blame -- amountlib/legacy.py
for symbol in amount_str amount_value orders-export schema; do
  git -C /tmp/orchestra-07/drill-ts003-wide log --all --oneline -S"$symbol" --
done
git -C /tmp/orchestra-07/drill-ts003-wide remote -v
git -C /tmp/orchestra-07/orders-consumer log --oneline -20
git -C /tmp/orchestra-07/orders-consumer remote -v
```

原始记录: `evidence/history-runtime.raw.log`. 提交消息没有 PR 编号. 本仓库 origin 是允许范围外的本机路径 `/tmp/orchestra-07/payout-service`, 未进入该目录. 消费者没有 remote 输出. 未取得托管平台讨论或部署材料, 不编造这部分历史.

### 实跑与材料

[事实/4级] 使用工作区的 `repo/` 和 `base/`, 分别调用真实 `db/seed.py`, `scripts/dump_orders.py`, `app.orders.read_orders` 和消费者 `src/run.sh`/`src/ledger.js`. 未修改产品代码, 测试或配置. 仅在工作区写临时脚本, 日志, 缓存, 以及两个副本自己的 `var/`.

实跑环境: CPython `3.14.4`, SQLite `3.46.1`, uv `0.12.5`, Node `v24.19.0`. amountlib 使用各副本随附的 `2.4.0`, 不是另外安装的包. Python 入口均为 `uv run ... python -B`. 证明先检查运行环境与库版本/加载路径. 两快照全部 13 个文件逐字节对照相应 git 提交. 消费者 5 个文件也逐字节对照其 HEAD. 实跑前后再检查文件校验值与两只读仓库状态. 记录见 `evidence/source-manifest.json`.

| 材料 | 用途/结果 |
| --- | --- |
| `proofs/prove_all.py` | 总入口, 任一事实不符就非零退出 |
| `proofs/check_amounts.py` | 两个独立进程核对金额版本, 分支和回退 |
| `proofs/rows_only.mjs` | Node 真实语义证明, 包含可失败断言 |
| `proofs/search_readers.sh` | 精确检索范围, 命令, 空结果断言 |
| `proofs/repro_file_crash.py` | 最小文件失败复现, 全文见第 5 部分 |
| `evidence/proof-all.raw.log`, `evidence/proof-all.exitcode` | 最终完整原始输出, 总入口退出 0 |
| `evidence/search-readers.raw.log`, `evidence/search-readers.exitcode` | 检索全部命中和各命令退出码, 总脚本退出 0 |
| `evidence/repro.raw.log`, `evidence/repro.exitcode` | 最小复现原始输出, 证明入口退出 0 |
| `evidence/base.file.json`, `evidence/head.file.json` | 两个真实导出文件的原样副本 |
| `evidence/base.dump.stdout`, `evidence/head.dump.stdout` | 两次导出真实 stdout |

每次调用还分别保留 `evidence/<用例>.command.json`, `.stdout`, `.stderr`, `.exitcode`. 不把消费者退出码和证明脚本退出码混为一谈: 消费者按预期退出 1, 证明该事实的脚本应退出 0.

[事实] 首次证明把旧账本总额误写成精确的 `22.49`, 因现有浮点数结果 `22.490000000000002` 而断言失败. 只修正了证明的预期为 `12.5 + 9.99`, 没改产品. 首次失败原文留在 `evidence/proof-all.attempt1.raw.log`/`.exitcode`, 退出 1. 随后成功输出也留在 `evidence/proof-all.attempt2.raw.log`/`.exitcode`, 最终版本又实跑成功.

### 覆盖边界

[事实] 改动跨 app/scripts, 跨 Python/Node, 跨两个仓库, 修改下游共享的导出 JSON 外形与字段. 即使只有两行, 也属于宽影响变更.

[事实] 调用方只授权 A 路单路调查, 且禁止新会话. 缺少第二模型同题核对, 不假装已完成多路合并. [未证实] 跨模型的一致性没有核对. 这不降低已实跑事实的第 4 级证据.

[未证实] 未取得生产运行时, 任务调度, 实际输入路径, 部署顺序, 使用频率, 其他仓库/外部脚本, 历史导出存量及生产网入口. 不声称生产已经发生故障. 禁止目录与其他调查目录均未读取. 归档服务的限制见 F5.

## 2. 关键安全事实与证据级别

级别含义: 1=单独断言, 2=真实源码位置, 3=逐步走查路径, 4=真实代码及可失败证明, 5=运行中的应用复现. 本报告没有声称第 5 级. 本地离线副本/CLI 实跑停在第 4 级, 未进入运行中的生产应用.

决定本次是否安全的两条前提是: 旧消费者是否仍能遍历顶层, 是否仍能读到 `amount`. 两条前提都不成立. 金额解析本身没变不能抵消这两处破坏.

### F1. 真实消费者读新文件: 会因顶层不可遍历而失败

[事实/4级] 可在给定新文件和现有消费者代码的条件下定案"会崩". `JSON.parse` 成功, 得到普通对象. `orders-consumer/src/ledger.js:3` 没有取 `.rows`, 第 6 行直接 `for (const row of rows)`, 对该对象抛 `TypeError`. 第 7/11 行的金额处理尚未执行.

实跑命令:

```bash
bash /tmp/orchestra-07/orders-consumer/src/run.sh /tmp/orchestra-07/out/ts003-wide-work/router-a/evidence/head.file.json
```

真实退出码: `1`. stdout 为空. stderr 原文, 对应 `evidence/head.file-ledger.stderr`:

```text
file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6
for (const row of rows) {
                  ^

TypeError: rows is not iterable
    at file:///tmp/orchestra-07/orders-consumer/src/ledger.js:6:19
    at ModuleJob.run (node:internal/modules/esm/module_job:439:25)
    at async node:internal/modules/esm/loader:643:26
    at async asyncRunEntryPointWithESMLoader (node:internal/modules/run_main:101:5)

Node.js v24.19.0
```

证明: `proofs/prove_all.py`, 断言退出 1, 无 stdout, 且错误类型/位置匹配. 另有第 5 部分独立最小复现.

[推断/3级] 对未修改的这个读取入口, 新外层对象即使 `rows` 为空仍不可直接遍历. 不能把这推广成"生产一定已经崩", 因为生产是否已经切到此文件未证实. 已实跑的是任务的 3 行数据, 故停在第 4 级而非第 5 级.

### F2. 只适配 rows, 字段仍用 amount: 不崩, 静默算错

[事实/4级] 使用真实新文件, 只抽出 `.rows` 存为 `evidence/head.rows-only.json`, 再交给未改动的消费者. 退出 `0`, 原始 stdout (`evidence/head.rows-only-ledger.stdout`):

```json
{
  "total": null,
  "missing": []
}
```

`proofs/rows_only.mjs` 另用真实 Node 执行同样的循环并逐项断言:

1. 3 行都没有 `amount`, 访问结果是 `undefined`.
2. `undefined === null` 为 false, 因而不会收集缺失金额的 id.
3. `Number(undefined)` 是 `NaN`, 即不是有效数字. 累加后 total 也是 `NaN`.
4. `JSON.stringify` 把数值位置的 `NaN` 写成 `null`, 不抛错.

原始语义输出见 `evidence/head.rows-semantics.stdout`. 3 次 `amountIsUndefined`/`totalIsNaN` 均为 true, 最后 `internalTotalIsNaN` 为 true, 断言通过. 此处不是把金额按 0 算, 不是 TypeError, 也不是正常的业务缺失值. 它还把本来应报告的 `missing: [3]` 丢成 `[]`.

停在第 4 级: 假设的仅是"先修外层"这一部署状态. 数值语义和未改动消费者对抽出数组的行为已经实跑, 不是未证实的猜想.

### F3. stdout 保留裸数组, 但不能保住旧字段契约

[事实/4级] `scripts/dump_orders.py:19-20` 在同一次运行里先写文件, 再 print 数组; 不是互斥的两个命令行分支. HEAD 的真实 stdout 原文:

```json
[{"id": 1, "amount_value": "12.50"}, {"id": 2, "amount_value": "9.99"}, {"id": 3, "amount_value": null}]
```

把该原始 stdout 保存后交给相同 `src/run.sh`, 退出 `0`, 输出仍为:

```json
{
  "total": null,
  "missing": []
}
```

证明及原始材料: `proofs/prove_all.py`, `evidence/head.dump.stdout`, `evidence/head.stdout-ledger.stdout`, `.stderr`, `.exitcode`. 旧版 stdout 同样实跑, 得到总额 `22.490000000000002`, `missing: [3]`, 退出 0.

[事实/4级] 文件入口有顶层异常, stdout 数组没有该异常, 却有 F2 的静默错误. 风险不同, 不能用"stdout 还能遍历"作为兼容证据.

[事实/2级] 两仓库没有找到真正从 stdin 读此 stdout 的额外程序. 实验是把 stdout 的同一批字节保存后交给现有文件读取器, 不伪造一个生产管道. [未证实] 是否有其他生产 stdout 读取器, 以及它们怎样处理缺失字段, 仍缺代码和部署入口.

### F4. 三行金额值没有变, 解析分支与回退也没有变

[事实/4级] 两边都运行各自真实 `db/seed.py:8-12`, 再运行各自真实导出脚本. 按 id 比较, 只忽略字段改名:

| id | 真实 payload | HEAD~1 的 amount | HEAD 的 amount_value |
| --- | --- | --- | --- |
| 1 | `{"schema":"v2","amount":"12.50"}` | `"12.50"` | `"12.50"` |
| 2 | `{"schema":"v1","amount_str":"9.99"}` | `"9.99"` | `"9.99"` |
| 3 | `{"schema":"v1","amount_str":""}` | `null` | `null` |

`proofs/check_amounts.py` 在每个快照的独立进程导入真实 app/库, 仅给真实函数包一层进程内调用记录, 不替换返回值. 两次均断言 `_FORMATTERS == {}`, 记录完全相同. Decimal 是按十进制保存的小数:


- id 1: `resolve_amount` 返回 Decimal `12.50`, 不走 app 回退.
- id 2: `resolve_amount` 返回 None, app 回退 `parse_amount("9.99")` 得到 Decimal `9.99`.
- id 3: `resolve_amount` 返回 None, app 回退 `parse_amount("")` 得到 None.

源码位置: `amountlib/legacy.py:18-23`, `amountlib/core.py:7-21`, `app/orders.py:11-15`. 所谓 v1/v2 分支实际按 payload 有没有 `amount` 键区分, 不是读取 `schema` 值来分派. 证明额外断言: `{"schema":"v1","amount":"8.40"}` 仍解析 amount, `{"schema":"v2","amount_str":"7.10"}` 在未注册格式化函数时仍返回 None. None/空串/纯空格解析为 None, 带空格的合法金额会去空格, `not-an-amount` 仍抛 ValueError.

两快照的 amountlib 三个文件逐字节相同, 版本均为 2.4.0. `app/orders.py` 只在字典键处不同. `app/__init__.py` 仍为空, 导入后的 v1 注册表在两进程均为空. 本次没有改金额解析代码, 库内补丁或注册时机. 这是源码等同性加真实调用证据, 不是仅看版本号.

完整原始调用记录: `evidence/base.amounts.stdout`, `evidence/head.amounts.stdout`. 真实导出文件也已保留. 停在第 4 级: 值对比覆盖指定 3 行及列出的分支控制输入, 不声称测尽生产数据; 代码未变的判断另有逐字节证据.

### F5. 在两个允许仓库中找到哪些旧读取方

[事实/2级, 有限静态范围] 读取旧导出数组/`amount` 的实际程序只有 `orders-consumer/src/ledger.js:3,6-11`, 由 `orders-consumer/src/run.sh:4` 调用. 本仓库内没有另一个读取导出 JSON 的程序. `scripts/dump_orders.py:10,17` 是 `read_orders` 返回列表的调用方和导出方, 不是读取旧导出文件的消费者.

精确可重跑入口:

```bash
cd /tmp/orchestra-07/out/ts003-wide-work/router-a
bash proofs/search_readers.sh
```

脚本执行的检索命令如下, 不是只搜已跟踪文件. `rg` 是实际使用的递归 grep 工具:

```bash
filters=(--hidden --no-ignore -g '!**/.git/**' -g '!**/.agents/**' -g '!**/.venv/**' -g '!**/node_modules/**' -g '!**/__pycache__/**' -g '!**/var/**')
for root in /tmp/orchestra-07/drill-ts003-wide /tmp/orchestra-07/orders-consumer; do
  cd "$root" || exit 2
  rg --files "${filters[@]}" .
  rg -n "${filters[@]}" -e '\bamount\b' .
  rg -n "${filters[@]}" -e 'read_orders|resolve_amount|parse_amount|register_legacy_formatter|amount_str' .
  rg -n "${filters[@]}" -e 'orders[.]export[.]json|dump_orders|JSON[.]parse|json[.]loads|readFileSync|\brows\b|stdout|jq|stdin|process[.]argv|ARCHIVE|orders_archive' .
  rg -n "${filters[@]}" -e 'schema|orders-export|amount_value' .
done
```

排除项: `.git` 是版本元数据, `.agents` 是调查说明, `.venv`/`node_modules` 是依赖安装目录, `__pycache__` 是 Python 缓存, `var` 是生成数据而非读取方源码. 隐藏文件和被 ignore 的其他文件也纳入. 没有排除测试, 脚本或配置目录. 文件清单实际为上述 13+5 个文件, 全部人工阅读. 工作区证明脚本不算产品读取方.

完整命中和每条命令退出码见 `evidence/search-readers.raw.log`. `amount` 单词检索的全部命中如下:

| 范围 | 命中路径/行 | 含义 |
| --- | --- | --- |
| 本仓库 | `app/orders.py:12,13,14,15` | 局部 amount 变量/回退, 不是读旧导出字段 |
| 本仓库 | `amountlib/legacy.py:15,18,19` | 注释和读取数据库 payload 的 amount; 输入格式未变 |
| 本仓库 | `db/seed.py:9` | 写入测试数据的 amount, 不是导出消费方 |
| 消费者 | `src/ledger.js:7,11` | 真正读旧导出字段 |
| 消费者 | `README.md:3` | 文档描述, 不是另一程序 |

其他查询命中的真实路径关系:

- 顶层 JSON 读取: 消费者 `src/ledger.js:3` 解析整个文件, `:6` 假定可遍历. 本仓库 `app/orders.py:8,11` 读的是 SQLite payload, 不读导出 JSON.
- 导出路径/写入: `scripts/dump_orders.py:12,17,19,20`; 消费者 `README.md:4` 说明生产生成方, 不证明实际生产调度.
- 库解析/注册: `amountlib/__init__.py:1,2,4`, `core.py:7`, `legacy.py:2,7,12,15,16,19,20,23`, `app/orders.py:4,7,12,14`, `db/seed.py:10,11`. 都不是额外导出消费方.
- 归档命中: `app/legacy_sync.py:3,7,11,13,14,15`. 当前函数只查询 `orders_archive` 并返回条数, 没有调用 `read_orders`, 解析导出 JSON 或读 amount 字段.

空结果也有边界:

- 消费者查询 `read_orders|resolve_amount|parse_amount|register_legacy_formatter|amount_str`: 无命中, rg 退出 1.
- 消费者查询 `schema|orders-export|amount_value`: 无命中, rg 退出 1. 脚本还断言了这个有限范围的空结果.
- 两仓库未找到其他 stdout/stdin 读取入口或按 schema 分派的代码. 本仓库 schema 命中是 seed 的 v1/v2 标签, 读取 `schema.sql` 的文件名, 库注释, 以及新导出声明, 不是另一个分派器.

[未证实] 这不能证明整个部署只有一个消费者. 缺其他仓库和外部脚本的读取权限, 缺调度/服务配置入口, 缺生产网与数据. `app/legacy_sync.py:3,11-14` 还要求归档表与 ARCHIVE_TOKEN, 任务未提供这批数据, 令牌和服务入口; 未运行/外联归档服务. 不能把那里未验证的外部链路写成"已安全". 第 2 级仅覆盖列明的有限源码范围, 不把 grep 空结果当全局不存在证明.

### F6. 其他行为: 文件新增版本标签, 两种出口不再同形

| 状态/级别 | 结论 | 证据/停下理由 |
| --- | --- | --- |
| 事实/4级 | 顶层 `schema` 是新增, 值为 `orders-export/2`, 只在文件里出现 | `scripts/dump_orders.py:19`; 真实 `evidence/head.file.json`; 总脚本断言完整顶层键集 |
| 事实/4级 | HEAD~1 文件与 stdout 解析后相同, HEAD 不同; HEAD 文件的 `.rows` 才与 stdout 相同 | `:19-20`; 总脚本同时断言两边关系, 输出文件与 stdout 均留原文 |
| 事实/4级 | 相对输出路径仍为 `var/orders.export.json`, 数据库仍为 `var/orders.db` | `:7,12,16`; 两边真实生成到各自 ROOT/var; 两版脚本只允许第 19 行不同 |
| 事实/4级 | 订单 id/顺序, 金额字符串/null 和原数据库 payload 未因本提交改变 | `app/orders.py:8,15`; seed/库/SQL 逐字节相同, 三行真实输出对比 |
| 事实/2级 | 现有消费者不检查 schema, 不能自动选择新旧格式 | `orders-consumer/src/ledger.js:3-13` 全文; F5 的 schema 查询无命中 |
| 事实/2级 | 库不按 payload.schema 分派, 且数据库内 v1/v2 标签没被本次修改 | `amountlib/legacy.py:18-23`, `db/seed.py:9-11`; F4 另有第 4 级控制输入 |

[推断/3级] 只读 stdout 的程序无法从这个新的顶层 schema 识别版本, 因为 stdout 没有该键. 若某外部程序要求两个出口同形, 这一前提现在已不成立.

[未证实] 未发现实际按导出 schema 分派的其他下游, 因而不声称已经破坏一个未找到的分派器. 外部分派器/两出口比较器的存在和部署均未知. 本地已确认的失败仍是 F1/F2/F3.

## 3. 风险

### 风险 1. 现有文件消费者整批失败, 阻断合入

- 状态: [事实/4级] 本地真实消费者已复现.
- 位置: `scripts/dump_orders.py:19` 改外层; `orders-consumer/src/ledger.js:3,6` 仍解析后直接遍历; `src/run.sh:4` 直接返回 Node 退出结果.
- 怎么坏: 新文件能被 JSON.parse, 但不能当顶层数组遍历. 消费者在汇总前抛 TypeError, 退出 1, 没有账本 stdout.
- 概率依据: 在"现有消费者读取本次生成文件"条件下是确定失败. 指定 3 行实跑已失败; 与金额取值无关. 真实切换频率/是否同时部署兼容消费者未知, 不编造生产发生率.
- 代价: 这一批无法汇总. 对同一文件重试仍失败, 不是偶发网络问题. 是否阻断更后面的财务任务, 影响多少批, 无生产数据可量化.
- 检查: 第 5 部分一条命令; 看 `evidence/repro-ledger.exitcode` 的 1 和 `.stderr` 的 `TypeError: rows is not iterable`. 不能只检查导出进程退出 0.

### 风险 2. 只修外层或改用 stdout, 零退出却交付错误账本, 阻断合入

- 状态: [事实/4级] 两种输入均已用真实消费者复现; "只修外层"是条件性部署方案, 不是声称消费者代码已经这样修改.
- 位置: `app/orders.py:15` 去掉 amount; `scripts/dump_orders.py:20` 仍打印裸数组; `orders-consumer/src/ledger.js:7-11,13` 只认 null/旧字段, 再序列化总额.
- 怎么坏: 缺字段产生 undefined, 未进入 null 检查, 相加产生 NaN. 最终 JSON 是 `total: null, missing: []`, 退出 0. id 3 本该列入缺失列表却被漏掉.
- 概率依据: 当前导出的每行都没有 amount. 对任何非空的新行数组, 继续使用这个旧循环就会出现 NaN; 指定数据实测 3/3 行触发. 空数组不触发该字段错误. 是否有真实 stdout 生产读取方/是否只适配外层未知.
- 代价: 样本总额由旧结果 `22.490000000000002` 变为 null, 缺失标记从 `[3]` 变成 `[]`. 退出码检查发现不了. 下游可能把错误账本当成功结果, 但金额损失和后续处理入口未取得, 不擅自量化.
- 检查: 重跑 `proofs/prove_all.py`; 看 `evidence/head.rows-only-ledger.*`, `head.stdout-ledger.*`, `head.rows-semantics.stdout`. 必须同时检查 total 是有效数值, 且 missing 仍含 3, 不能仅检查进程未崩.

[推断] 合入前至少需要同时解决外层和字段兼容, 并明确/协调文件与 stdout 的版本契约. 仅加 schema, 仅改遍历 `.rows`, 或仅回退 stdout 都不足以修复现有读取链路. 可以由消费者完整适配并联合验证, 或由生产方保留旧兼容出口; 本报告未实施任何方案.

## 4. 已排除项

仅列已确认的范围, 不把未知外部链路放进来:

1. [事实/4级] 排除本次提交改变 seed 三行金额值. 两版均为 id 1=`"12.50"`, id 2=`"9.99"`, id 3=`null`. 证据是两次真实导出和独立函数跟踪, 不包含未给出的生产数据.
2. [事实/4级] 排除本次改了 amountlib 版本, 本地补丁, v1 注册状态或 app 的 parse_amount 回退. 三个库文件相同, app 只改输出键, 全新进程注册表均为空, 分支调用记录相同. 未声称祖先提交没有改变解析.
3. [事实/4级] 排除新文件因 JSON 语法损坏而失败. 真正错误在 JSON.parse 成功后的 `for...of`. 外层修好后仍有另一处独立错误.
4. [事实/4级] 排除本次改了输出文件相对路径/数据库列/SQL 排序. 两版脚本路径相同, SQL 和 schema.sql 相同, id 序列均为 1/2/3. 未检查外部搬运脚本的部署路径.
5. [事实/2级] 排除在已读两仓库源码里存在一个已经适配 schema/amount_value 的其他消费入口. 消费者全量 5 文件已读, 新符号查询无命中. 不外推到其他仓库/生产环境.
6. [事实/2级] `app/clamp.py:4-6` 只限制下单数量; `app/legacy_sync.py:10-15` 当前源码不读本次导出或 amount 字段; 两者不在本次 diff. 已排除的是本地可见的直接依赖, 不是给生产归档服务作安全背书.
7. [事实/4级] 旧消费者的 `22.490000000000002` 浮点数尾差已经存在于 HEAD~1. 不把它列为本提交新增问题, 也不把该尾差与新出现的 NaN/null 混为一谈.

## 5. 合并前最便宜的复现

在允许的工作区运行一条命令, 不安装依赖, 不碰两只读仓库. 会重建 `repo/var/orders.db` 和 `repo/var/orders.export.json`, 仅适合任务给的副本:

```bash
cd /tmp/orchestra-07/out/ts003-wide-work/router-a && UV_CACHE_DIR="$PWD/.uv-cache" PYTHONDONTWRITEBYTECODE=1 uv run --no-project --no-managed-python --no-python-downloads python -B proofs/repro_file_crash.py
```

已实跑. 原始输出在 `evidence/repro.raw.log`. 消费者退出 1, TypeError 原文与 F1 相同; 证明脚本断言通过后自身退出 0. 若不再出现该失败, 或错误类型/退出码不符, 此证明脚本会非零退出. 这是证明已观察失败, 不是"产品通过"的验收测试.

`proofs/repro_file_crash.py` 全文:

```python
"""最小复现: 真 seed + 真导出 + 未改动的消费者. 判断不符即非零退出."""
import os
import pathlib
import subprocess
import sys

work = pathlib.Path(__file__).resolve().parents[1]
root = work / "repo"
out = work / "evidence"
out.mkdir(exist_ok=True)
assert sys.implementation.name == "cpython" and sys.version_info >= (3, 11)
sys.path.insert(0, str(root))
import amountlib

assert amountlib.VERSION == "2.4.0"
assert pathlib.Path(amountlib.__file__).resolve() == root / "amountlib/__init__.py"
assert subprocess.check_output(["node", "--version"]).strip() == b"v24.19.0"
env = os.environ | {"UV_CACHE_DIR": str(work / ".uv-cache"), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""}
py = ["uv", "run", "--no-project", "--no-managed-python", "--no-python-downloads", "python", "-B"]
for script in ["db/seed.py", "scripts/dump_orders.py"]:
    run = subprocess.run([*py, str(root / script)], cwd=work, env=env, capture_output=True)
    (out / ("repro-" + pathlib.Path(script).stem + ".stdout")).write_bytes(run.stdout)
    (out / ("repro-" + pathlib.Path(script).stem + ".stderr")).write_bytes(run.stderr)
    assert run.returncode == 0, run.stderr
consumer = "/tmp/orchestra-07/orders-consumer/src/run.sh"
run = subprocess.run(["bash", consumer, str(root / "var/orders.export.json")], cwd=work, env=env, capture_output=True)
(out / "repro-ledger.stdout").write_bytes(run.stdout)
(out / "repro-ledger.stderr").write_bytes(run.stderr)
(out / "repro-ledger.exitcode").write_text(str(run.returncode) + "\n")
print(f"consumer_exit_code={run.returncode}", flush=True)
sys.stdout.buffer.write(run.stdout)
sys.stdout.buffer.write(run.stderr)
sys.stdout.buffer.flush()
assert run.returncode == 1 and run.stdout == b""
assert b"TypeError: rows is not iterable" in run.stderr
assert b"ledger.js:6" in run.stderr
print("PASS: 新文件确实使旧消费者非零退出; 证明脚本自身成功退出.")
```

全量复核另用:

```bash
cd /tmp/orchestra-07/out/ts003-wide-work/router-a && UV_CACHE_DIR="$PWD/.uv-cache" PYTHONDONTWRITEBYTECODE=1 uv run --no-project --no-managed-python --no-python-downloads python -B proofs/prove_all.py
```

它还检查 HEAD~1 对照, 两出口, 3 行值, Node 的 NaN/null 行为, 全部快照与消费者源码未变. 检索另跑 `bash proofs/search_readers.sh`. 本报告只交接材料, 未合并, 未建 PR, 未更改产品.
