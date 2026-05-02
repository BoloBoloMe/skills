# 完成前验证

## 适用时机

准备声明完成、修复成功、测试通过、构建通过、提交、合并或交付前使用。

## 输入契约

- HILP execution handoff asset_ref。
- 需要证明的声明。
- 对应完整验证命令。
- 预期输出或通过标准。
- 禁止越界项。
- 当前 execution ledger 路径和对应 unit summary 路径。
- 当前 execution_unit 的 Failure Note 状态。
- 并行组或全包的 conflict check、integration verification、spot check 和 execution ledger 更新结果。

## 执行规则

铁律：没有新鲜验证证据，不得声明完成。

Gate function：
1. 识别声明：测试通过、构建通过、bug fixed、agent 完成或需求满足。
2. 运行完整命令，不用旧结果或片段输出替代。
3. 读取退出码、完整输出和失败数量。
4. 核对输出是否证明声明。
5. 核对 execution ledger 与 unit summary：当前 execution_unit 的 summary 已落盘，ledger 状态、summary 路径、验证命令、退出码、parallel_group、conflict check、integration verification、spot check 和重审标记与实际证据一致。
6. 核对 Failure Note：确认不存在未关闭 Failure Note；若存在未关闭 Failure Note，则不得声明完成，只能报告阻断、证据、分类和 HILP 回退出口。
7. 再声明；如果不一致，只报告实际状态。

声明与证据矩阵：

| 声明 | 必需证据 |
|---|---|
| 测试通过 | 测试命令退出码为 0，输出无失败。 |
| 构建通过 | 构建命令退出码为 0。 |
| bug fixed | 复现用例先失败后通过，相关回归通过。 |
| agent 完成 | 独立检查文件 diff，并运行验证命令。 |
| 需求满足 | 对照 HILP 蓝图和执行交接逐项核验。 |

## Must-haves Verification Ladder

完成前必须从执行交接读取已批准蓝图摘录的 `must_haves`，不得在执行阶段临场定义验收口径。

must_haves 对照：

| must_have_id | Truths | Artifacts | Key Links | 验证层级 | 证据 | 结论 |
|---|---|---|---|---|---|---|
| MH-001 | 已批准设计或蓝图中的必须满足项 | 文件、测试、命令输出或人工记录 | Truth 与 Artifact 的对应关系 | 静态检查 / 命令执行 / 行为测试 / 人工检查 | 命令、退出码、输出摘要或检查记录 | pass / fail / blocked |

核验规则：
- Truths：只接受已批准设计、已批准蓝图和有效执行交接中的绑定承诺；不得引用待审批、草稿、待修订或已归档资产作为绑定性设计或蓝图输入。
- Artifacts：只记录本 execution_unit 允许修改文件、验证输出、summary 或交接允许的证据，不得扩大文件范围。
- Key Links：逐条说明 Artifact 如何证明 Truth；若只能证明“文件存在”而不能证明承诺满足，必须标记未覆盖风险。

验证梯度：
1. 静态检查：检查字段、路径、diff、文档段落、禁止项和证据链是否存在。
2. 命令执行：运行交接指定命令，记录命令、退出码和输出摘要。
3. 行为测试：用测试或复现路径证明用户可观察行为或治理行为满足 Truth。
4. 人工检查：记录自动化无法覆盖的审批语义、风险边界或证据链完整性；人工检查不得替代已指定命令。

完成门槛：所有 `must_haves` 均为 pass，验证命令退出码与预期一致，未覆盖风险和重审结论已写入 unit summary，execution ledger 已指向该 summary 且状态、退出码、parallel_group、conflict check、integration verification、spot check 和重审标记一致；不存在未关闭 Failure Note；任一项 blocked、存在未关闭 Failure Note 或需要 HILE 补做蓝图判断时，不得声明完成。

## 禁止事项

- 不得使用“应该”“看起来”“大概”“agent 说完成”表达完成。
- 不得用部分验证推断整体通过。
- 不得相信 agent 报告而不检查实际产物。
- 不得在失败命令后继续宣称成功。
- 不得省略退出码和输出摘要。
- 不得跳过并行组返回后的 conflict check、integration verification、spot check、unit summary 和 execution ledger 更新。
- 不得在缺少 execution ledger 或 unit summary 核对时声明 execution_unit 完成。
- 不得在存在未关闭 Failure Note 时声明完成。

## 输出契约

输出验证命令、退出码、关键输出摘要、结论和未覆盖风险。失败时输出失败原因、影响、当前阻断项和下一步处理。

## 检查清单

- [ ] 命令刚刚运行。
- [ ] 已读取退出码。
- [ ] 已读取完整输出。
- [ ] 结论与证据一致。
- [ ] agent 委派结果已独立验证。
- [ ] execution ledger 与 unit summary 已核对，状态、路径、验证命令、退出码、parallel_group、conflict check、integration verification、spot check 和重审标记一致。
- [ ] 已确认不存在未关闭 Failure Note；如存在，已停止完成声明并回到 Failure Forensics 输出。
