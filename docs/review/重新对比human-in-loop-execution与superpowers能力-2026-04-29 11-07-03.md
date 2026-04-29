# 重新对比 human-in-loop-execution 与 superpowers 能力

## 1. 审查结论

**结论：补强有效；`human-in-loop-execution/` 已从“纪律摘要版”提升为“可执行的 HILP 裁剪版”。但它仍不是 Superpowers 原版的完整等价实现。**

按用户要求，本次仍只比较 `human-in-loop-execution/` 已拥有的技能，忽略它未保留的 Superpowers 技能。

当前判断：

- 对执行主链路而言，前者已基本补回 Superpowers 对应能力的核心行为门：TDD 铁律、系统调试根因优先、完成前验证证据门、subagent 状态处理、审查反馈处理、分支收尾选项和技能编写压力场景。
- 对 HILP 场景而言，前者在资产绑定、禁止越界、执行交接和重审回退方面强于原 Superpowers。
- 对原 Superpowers 的“抗压说服力、示例密度、反理性化完整性、流程图和真实案例”而言，前者仍明显更薄，尤其是 `writing-skills`、`test-driven-development`、`systematic-debugging`、`subagent-driven-development` 和 `testing-anti-patterns`。

因此：

> 如果评价标准是“在 HILP 执行交接后，能否安全约束计划、实现、测试、审查、调试与收尾”，现在基本相当。  
> 如果评价标准是“是否完整保留 Superpowers 原技能的训练强度、示例、反借口库和流程细节”，仍不相当，但差距已从结构性劣化降为可接受的裁剪差异。

## 2. 与上次审查相比的变化

补强后新增或恢复的关键能力包括：

- `SKILL.md` 明确“补回执行强制门和抗误用细节，不接管 HILP 规划审批”。
- `test-driven-development.md` 已补入铁律、删除并从测试重来、RED/GREEN/REFACTOR、好坏测试对照和常见借口表。
- `systematic-debugging.md` 已补入根因调查铁律、四阶段、单假设验证、三次失败后停止、红旗和常见借口。
- `verification-before-completion.md` 已补入 gate function、声明与证据矩阵、退出码和 agent 独立验证。
- `subagent-driven-development.md` 已补入 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED、提问循环、审查顺序、复审循环和失败处理。
- `code-review.md` 已补入 BASE_SHA / HEAD_SHA、外部反馈怀疑性验证、禁止表演式附和和 YAGNI 检查。
- `finishing-branch.md` 已补入四个后续选项、精确确认、验证失败阻断和 HILP 执行结果回写。
- `writing-skills.md` 已补入文档 TDD、压力场景、RED / GREEN / REFACTOR 和 description 规则。

关键词抽查结果显示核心补强点已落入目标文件：

| 文件 | 命中情况 |
|---|---:|
| TDD：删除重来 / 常见借口 / RED-GREEN-REFACTOR | 5 |
| 调试：根因 / 假设 / 三次失败 / 红旗 | 13 |
| 验证：退出码 / 新鲜验证 / agent 完成 / 证据矩阵 | 10 |
| subagent：DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED / 规格审查 | 7 |
| code review：BASE_SHA / HEAD_SHA / YAGNI / 外部反馈 / 表演式 | 9 |
| finishing：本地合并 / 创建 PR / 保留分支 / 丢弃 / 确认 | 7 |
| writing-skills：文档 TDD / 压力场景 / RED / GREEN / REFACTOR | 11 |

## 3. 分项对比

| human-in-loop-execution 能力 | Superpowers 对应能力 | 当前判断 | 说明 |
|---|---|---|---|
| `writing-plans.md` | `skills/writing-plans/SKILL.md` | 接近相当 | 已补固定计划头、文件职责、2-5 分钟任务、No placeholders、自检。仍少原版完整示例代码和 plan document header 细节，但 HILP 场景下可用。 |
| `subagent-driven-development.md` | `skills/subagent-driven-development/SKILL.md` | 核心相当，细节较弱 | 已补状态处理、提问循环、审查顺序、复审和失败处理。仍少模型选择、完整流程图、真实示例、成本/优势分析和大量红旗。 |
| `executing-plans.md` | `skills/executing-plans/SKILL.md` | 基本相当 | 已补先审计划、任务状态、验证失败停止、主分支风险、完成后审查与验证。相较原版少 TodoWrite 和 worktree 集成，但后者属裁剪边界。 |
| `test-driven-development.md` | `skills/test-driven-development/SKILL.md` | 核心相当，抗压弱于原版 | 铁律、删除重来、RED/GREEN/REFACTOR、借口表已补回。仍少原版大量好坏代码示例、红旗清单、验证 checklist 和详细心理防线。 |
| `code-review.md` | `requesting-code-review` + `receiving-code-review` | 接近相当 | 已补 SHA 范围、外部反馈怀疑、禁止表演式附和、YAGNI、Critical/Important 处理。仍比原版少 GitHub thread 回复细节和更完整的反馈场景。 |
| `finishing-branch.md` | `finishing-a-development-branch` | 接近相当 | 已补四选项、确认丢弃、验证失败阻断、worktree cleanup 约束和 HILP 结果回写。仍少具体 git / gh 命令模板。 |
| `systematic-debugging.md` | `systematic-debugging/SKILL.md` | 核心相当，示例弱于原版 | 已补根因优先、四阶段、单假设、三次失败后质疑架构。仍少多组件诊断的大段示例、真实案例和完整 rationalization 表。 |
| `verification-before-completion.md` | `verification-before-completion/SKILL.md` | 基本相当 | 已补 gate function、证据矩阵、退出码、agent 独立验证和禁止措辞。仍少原版关于 regression red-green 的展开和大量失败记忆说明。 |
| `dispatching-parallel-agents.md` | `dispatching-parallel-agents/SKILL.md` | 接近相当 | 已补独立域、prompt 结构、不适用场景、集成检查和 spot check。仍少原版具体 agent prompt 示例和真实案例。 |
| `writing-skills.md` | `writing-skills/SKILL.md` | 明显改善但仍弱 | 已补文档 TDD、压力场景、RED/GREEN/REFACTOR、description 规则。原版 655 行中关于 CSO、flowchart、文件组织、测试类型、反理性化和部署清单仍大量压缩。 |
| `testing-anti-patterns.md` | `testing-anti-patterns.md` | 中度接近 | 已补五类反模式和 gate function。仍少原版代码示例、每类详细解释和复杂 mock 诊断展开。 |
| `root-cause-tracing.md` | `root-cause-tracing.md` | 接近相当 | 已补固定追踪链和诊断格式。仍少 find-polluter 脚本、完整示例和流程图。 |
| `defense-in-depth.md` | `defense-in-depth.md` | 接近相当 | 已补四层验证模型和每层证据要求。仍少原版代码示例和真实案例。 |
| `condition-based-waiting.md` | `condition-based-waiting.md` | 接近相当 | 已补 waitFor 伪代码、场景表、固定等待条件和常见错误。仍少 TypeScript 完整实现和真实案例。 |
| prompt templates | 各 Superpowers prompt 模板 | 接近相当 | 已补 HILP asset_ref、开始前提问、升级条件、自查、file:line、严重性校准。仍比原版简短，但执行关键点已覆盖。 |

## 4. 仍存在的主要差距

### 4.1 示例和压力场景密度仍显著低于 Superpowers

原 Superpowers 的强项不是只有规则，而是大量示例、反例、常见借口、红旗和真实案例。这些内容会在 agent 处于压力、疲劳、赶时间或想绕规则时提供额外约束。当前 `human-in-loop-execution/` 已补回规则骨架，但示例密度仍低。

### 4.2 `writing-skills.md` 仍是最大短板

当前文件已从不可用摘要变成可用元纪律，但相较原版仍缺：

- 完整 CSO 规则。
- 技能类型测试方法。
- 反理性化技巧。
- flowchart 使用规则。
- 详细部署 checklist。
- subagent 压力测试方法引用。

如果未来要频繁维护 skill，建议继续扩展该文件。

### 4.3 subagent 工作流仍少模型选择和长流程校准

当前已覆盖核心状态和 review loop，但原版还包括：

- 不同任务使用不同模型能力的选择策略。
- 复杂示例工作流。
- 成本 / 收益说明。
- 大量 Never / Red Flags。

这不影响基本执行，但会影响复杂任务下的调度质量。

### 4.4 分支收尾缺少具体命令模板

`finishing-branch.md` 已恢复四选项和确认纪律，但原版提供更直接的 git / gh 命令模板。当前版本更偏原则和输出契约，实际执行时需要 agent 自行选择命令。

## 5. HILP 裁剪版的增强项

相较 Superpowers 原版，`human-in-loop-execution/` 有以下 HILP 场景优势：

- 所有执行入口都绑定已批准设计、已批准蓝图和执行交接 asset_ref。
- 所有计划、prompt、审查和完成声明都要求保留禁止越界项。
- 发现蓝图错误、新事实、越界需求或审批缺失时统一回到 HILP 变更重审。
- 明确不接管需求、设计、审批和蓝图职责，避免双审批系统。
- 对蓝图外审查建议和调试修复要求更严格，不允许执行层自行扩大范围。

这意味着前者不是单纯弱化版；它在治理边界上更适合 HILP 流程。

## 6. 最终判断

当前补强后的 `human-in-loop-execution/`：

- **执行主链路能力：接近 Superpowers 对应技能。**
- **HILP 边界治理能力：强于 Superpowers 原版。**
- **示例、反理性化、训练强度和复杂 subagent 调度细节：仍弱于 Superpowers 原版。**

建议后续只针对三个短板继续补：

1. 扩展 `writing-skills.md` 的 CSO、压力测试和部署 checklist。
2. 扩展 `subagent-driven-development.md` 的模型选择、失败重派和红旗清单。
3. 为 TDD、调试、测试反模式增加少量高质量代码示例，而不是全文翻译原版。

在当前状态下，可以把它视为**能力基本达标的 HILP 中文裁剪执行版**，而不是此前那种明显劣化版。
