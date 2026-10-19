# ts003-wide 多模型同题调查合并记录

调查对象: payout-service HEAD `e807b06` (orders-export/2, amount -> amount_value).
合并人: cli/deepseek-v4.1-flash-expires-on-0910, thinking high, 本会话 `br-wide`.
两路互不可见, 各自跑证明, 报告落在不同目录. 合并时逐条事实对齐, 不按整篇投票.

## 1. 会话, 模型与产物

| 路 | 会话名 / tab | 模型全名 | thinking | kind | 起止 (本地时间, 按文件 mtime) | 报告 | 脚本与原始输出 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | `wide-a` / `S-wide-a-1` (`w1J:t2Q`) | `cli/gpt-6.1-sol` | xhigh | pi | 约 18:05 - 18:15 | `/tmp/orchestra-07/out/ts003-wide-work/router-a/report.md` | `router-a/proofs/`, `router-a/evidence/` |
| B | `wide-b` / `S-wide-b-1` (`w1J:t2R`) | `cli/glm-5.3-flash` | xhigh | pi | 约 18:05 - 18:14 | `/tmp/orchestra-07/out/ts003-wide-work/router-b/report.md` | `router-b/work/` |
| 合并 | 本会话 | `cli/deepseek-v4.1-flash-expires-on-0910` | high | pi | - | 本文件与 `ts003-wide-report.md` | `ts003-wide-work/probe_*`, `consumer_*`, `head/`, `base/`, `repro.sh` |

选型依据 (llm-select `score.py` 输出):

- `cli/gpt-6.1-sol`: coding 1.13, knowledge 1.24, review 0.993. 知识与编码高于基准, 适合复核跨语言线格式; 价格分 0.0297, 速度 0.7, 慢且贵, 只跑一路.
- `cli/glm-5.3-flash`: 各维与基准持平, 便宜, 适合独立跑第二套证明.
- thinking 都取 xhigh: 两款都支持 high/xhigh/max, xhigh 是第二深档; 本次失败代价高 (下游账本), 按 llm-select 规则优先深档, 但不取最贵的 max.
- kind 都用 pi: 两款模型只配置在 pi 的 `cli` provider 里, 换 codex 等 CLI 拿不到这两个模型. 启动后用真实 ping 确认可调用, 实际界面确认显示 `gpt-6.1-sol * xhigh` 与 `glm-5.3-flash * xhigh`.
- 两路完成后已按 use-herdr 收尾规则关闭 tab, `agent list` 不再有 `wide-a` / `wide-b`.

输入一致性: 两路拿到逐字相同的任务书 (`router-a/TASK.md`, `router-b/TASK.md`, 仅工作目录和输出路径不同), 各自有同 commit 的 HEAD 副本与 HEAD~1 副本, 读同一份技能, 同一批问题 F1-F6. 两路都在完成后才写报告, 没有读对方目录.

合并人复核: 重跑了 A 的 `proofs/prove_all.py` (exit 0, `ALL ASSERTIONS PASSED`), B 的 `work/f2-rows-amount.mjs`, `work/f3-stdout-consumer.mjs`, `work/f4-values.py` (三者 exit 0, 输出与报告一致), 并用合并人自己的 `repro.sh` 独立跑崩溃与静默两条链路. 关键原始输出一致.

## 2. 逐条事实对齐

| 事实 | A 路结论 / 级别 | B 路结论 / 级别 | 合并级别 | 合并结论与依据 |
| --- | --- | --- | --- | --- |
| F1 新文件让现有消费者崩 | 会崩, TypeError `rows is not iterable`, exit 1 / 4 | 同, 定位 `ledger.js:6`, exit 1 / 4 | 4 | 一致. 两路都用未改动的消费者读真实导出. 合并人重跑 A 总脚本与 B 产物, 并用自己的 `repro.sh` 再证一次. 不到 5 级: 未在运行中的生产应用复现. |
| F2 只适配外层, 仍读 `amount` | 不崩, total NaN 序列化为 null, missing 丢 id 3, exit 0 / 4 | 同, 逐项断言 undefined/NaN/null / 4 | 4 | 一致. A 用真实消费者读抽出的 `.rows`, B 用等价循环脚本; 合并人重跑 B 脚本. 结论是静默错账, 不是崩溃. |
| F3 读 stdout 的旧消费者 | 不崩, 同样静默错账; 文件与 stdout 不再同构 / 4 | 同, 明确 stdout 是裸数组, 文件是对象 / 4 | 4 | 一致. `dump_orders.py:19-20` 同一次运行写文件并 print, 不是两个互斥分支; stdout 仍数组但字段已改名. |
| F4 金额值与解析行为 | 三行值 12.50/9.99/null 不变, 解析路径未改 / 4 | 同 / 4 | 4 | 一致. 两路都在独立进程导入各自副本的 amountlib 2.4.0, 断言 `_FORMATTERS == {}`, v1 走 `parse_amount` 回退; 合并人 `probe_amounts.py` 再证. 只覆盖给定 3 行, 不覆盖生产数据. |
| F5 本地旧格式读取方 | 只找到 `ledger.js`, 检索级别 2 | 同, 检索级别 3 | 2 | 事实一致, 级别有分歧 (见第 3 节). 合并取 2: 静态零命中只说明列明范围内没有别的读者, 没有逐步走查失败路径, 够不上 3. 覆盖边界: 本机两个仓库, 不含生产调度和其他仓库. |
| F6a schema 键与两出口关系 | schema 只在文件里, 值 `orders-export/2` / 4 | 同 / 4 | 4 | 一致. 真实导出文件与 stdout 均已留原文; stdout 没有 schema 键. |
| F6b 输出路径, DB 列, 行序 | 未变 / 4 | 未变 / 4 | 4 | 一致. 两版 `OUT` 都是 `var/orders.export.json`, SQL 与 schema.sql 逐字节相同. |
| F7 HEAD 未推送 | 未查 `ls-remote`, 只说 origin 在授权范围外 | `git ls-remote origin` = `04ddf93` (HEAD~1) / 2 | 2 | 新增项, 合并人用 `git ls-remote origin` 与 `git rev-parse origin/master` 复核: origin/master = `04ddf93`, HEAD 未推送. 只说明推送状态, 不证明部署状态. |
| F8 schema 命名冲突 | 未提 | 推断: 与 payload 内 `schema: v1/v2` 同名不同义, 当前无读者 / 2 | 2 | 新增项, 保留为低优先级可读性风险. 本地检索无任何代码读导出 `schema`, 当前无害. |

## 3. 分歧与处理

1. F5 的证据级别. A 标 2, B 标 3. 事实相同, 都是本机两个仓库内只有 `src/ledger.js` 读旧字段, 其余命中是写入方, 文档或 payload 内部字段. 合并取 2, 理由: 技能把 3 定义为逐步走查失败路径, 静态枚举加零命中属于 2 级源码定位. 要升到 3, 需要拿到部署配置或运行时入口, 证明没有其他调用路径; 当前缺这类入口.
2. R1 的概率措辞. B 写"必然, 每次", A 写"在消费者读取本次生成文件的条件下确定失败". 合并取 A 的条件式: 单次读取是确定的, 但生产是否已切到该文件, 调度频率, 是否同时部署消费者都未证实. 不把条件确定写成生产必然已发生.
3. stdout 读取方的概率. B 给"中", 依据是若生产存在管道消费者则必然触发; A 标未证实. 合并: 本地两仓库未找到 stdout 读取方, 概率未证实; 条件成立时后果与 F3 相同, 是确定的静默错账.
4. README 的解释. B 说 `orders-consumer/README.md:2-3` 写明这就是生产读法; A 更严格, 只说生产 JSON 由 `dump_orders.py` 生成. 合并取 A: README 证明生成方与读取意图, 不证明生产调度与调用频率.
5. 调查范围的松紧. A 完全没进 origin; B 跑了 `git ls-remote origin` 只读 ref, 没读文件内容. 合并记录 F7 采纳 B 的 ref 信息, 同时明确 origin 目录内容未审计, 两路都没有越界读产品文件.

## 4. 合并结论

- 不建议按当前形态单独合入. 金额计算本身安全, 坏的全部在共享线格式: 现有文件消费者 100% 崩溃; 只修外层或改用 stdout 的消费者会在 exit 0 下交付 `total: null, missing: []` 的错账.
- 要合入, 至少同时做两件事: 消费者同步适配 `{schema, rows}` 外层与 `amount_value` 字段; 明确 stdout 与文件的版本契约, 或保留旧兼容出口. 只改其中一处会从显式崩溃变成静默错账.
- 金额值与 `amountlib` 2.4.0 解析行为未受本次提交影响, 有 4 级证据.
- 旧格式读取方只在本机两个仓库范围内查清; 生产和其他仓库的读者未证实, 这是合入前最大的未知.
- 未自动合并, 未创建 PR, 未改任何产品代码, 测试或配置.
