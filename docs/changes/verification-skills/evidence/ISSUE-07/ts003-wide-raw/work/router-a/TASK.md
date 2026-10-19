# 任务: payout-service HEAD 提交的 blast-radius 独立调查 (A 路)

你是独立调查员. 这是一次单路调查: 不要用 herdr 或任何方式开新会话, 不要读另一路调查目录的结论. 自己跑证明, 自己写报告.

## 必读技能

- `/tmp/orchestra-07/drill-ts003-wide/.agents/skills/blast-radius/SKILL.md`
- 同目录 `reference/multimodel.md`, `reference/report-style-zh.md`, `reference/source-record.md`

严格按该技能执行: 读变更与历史, 找关键安全事实, 标 1-5 证据级别, 写判断错会非零退出的证明脚本并保留原始输出, 风险与已排除项分开, 最后按五部分交接并用中文整理规则成文.

## 可读范围 (严格)

- 本仓库: `/tmp/orchestra-07/drill-ts003-wide` (只读参考, 不要修改)
- 消费者仓库: `/tmp/orchestra-07/orders-consumer` (只读, 不要修改)
- 技能目录: `/tmp/orchestra-07/drill-ts003-wide/.agents/skills/blast-radius/`
- 你的工作区: `/tmp/orchestra-07/out/ts003-wide-work/router-a/`
  - `repo/` 是 HEAD 的干净副本 (可运行, 会写自己的 `var/`)
  - `base/` 是 HEAD~1 的干净副本
- 禁止读: `/tmp/orchestra-07/tasks`, `/tmp/orchestra-07/fixture-facts.txt`, `/tmp/orchestra-07/drill-*` 里除 `drill-ts003-wide` 外的目录, `router-b/`, 以及任何别的调查产物.
- 不要修改任何产品代码, 测试, 配置. 所有临时脚本与输出只写 `router-a/` 下.

## 变更背景

payout-service HEAD 提交 `e807b06` 把导出线格式改成 `orders-export/2`, 并把金额字段 `amount` 改名 `amount_value`. 改动 2 个文件, 各 1 行:
- `app/orders.py` 输出字典的键
- `scripts/dump_orders.py` 写文件的外层结构

仓库自带 vendored `amountlib` 2.4.0. 导出的 JSON 被另一仓库的 Node 消费者 `/tmp/orchestra-07/orders-consumer` 读取. 本次改动横跨 app 与 scripts, 改的是下游共享的线格式.

## 必须回答的关键事实 (每条都要证据级别)

F1. 新导出文件的外层从数组变成 `{"schema": "...", "rows": [...]}`. 消费者 `src/ledger.js` 的真实代码读到新文件会怎样? 用消费者自己的代码跑, 记录退出码与原始报错. 能否定案"会崩"?
F2. 假设消费者先适配外层, 只遍历 `rows`, 但字段仍是 `amount`. 会发生什么? 是崩溃还是静默算错? 用真实 Node 语义跑一个小脚本证明 (不要改消费者仓库).
F3. `scripts/dump_orders.py` 的 stdout 分支仍 `print` 裸数组, 但字段名已变. 读 stdout 的旧消费者会怎样? 与读文件的消费者风险是否不同?
F4. HEAD 与 HEAD~1 导出的金额值本身是否变化? 用 `db/seed.py` 的 3 行真实数据对比 id 1/2/3 的值. 本次提交是否改变了金额解析行为 (含 amountlib 2.4.0 的 v1/v2 分支与 `parse_amount` 回退)?
F5. 在本仓库与消费者仓库范围内, 旧格式 (`amount` 字段 / 顶层数组) 的读取方还有哪些? 给出精确 grep 命令, 路径, 排除项, 命中结果. 空结果也要写清覆盖边界 (哪些地方查不到, 缺什么权限或入口).
F6. 本次提交是否还改变了别处依赖的行为 (例如 schema 键, 输出路径, stdout 与文件不再同构, 下游按 `schema` 分派)? 有就取证, 没有就写已排除.

## 交付

- 报告: `/tmp/orchestra-07/out/ts003-wide-work/router-a/report.md`
- 证明脚本与原始输出: 留在 `router-a/` 下, 报告里给路径或全文.
- 报告必须含: 五部分 (做了什么 / 关键安全事实与证据级别 / 风险 / 已排除项 / 合并前最便宜的复现), 以及一句明确的"是否建议合入"及依据.
- 事实, 推断, 未证实三种状态分开标.
- 风险每条写位置 file:line, 概率依据, 代价, 检查方法.

完成后回复: 报告路径 + 5 行以内摘要 (是否建议合入, 最要紧的坏法, 证据级别).
