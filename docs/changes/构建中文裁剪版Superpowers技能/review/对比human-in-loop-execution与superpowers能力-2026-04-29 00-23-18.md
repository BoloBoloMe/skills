# 对比 human-in-loop-execution 与 superpowers 能力

## 1. 审查结论

**结论：不相当；`human-in-loop-execution/` 是合格的 HILP 执行纪律骨架，但相较 `superpowers/` 对应技能存在明显能力劣化。**

本次按用户要求忽略 `human-in-loop-execution/` 未保留的 Superpowers 技能，只审查前者已经拥有的技能与后者对应能力是否相当。

总体判断：

- `human-in-loop-execution/` 保留了多数核心名词、阶段门、HILP asset_ref 绑定、禁止越界项和回退 HILP 的治理约束。
- 但它普遍把 Superpowers 中的操作级流程、反例、强制门、prompt 细节、严重性校准、停止条件和验证细节压缩为概括性清单。
- 因此若目标是“在 HILP 下提供最低限度执行约束”，前者可用；若目标是“达到 Superpowers 原技能的实际执行质量和抗误用能力”，前者不相当。

## 2. 分项对比

| human-in-loop-execution 能力 | Superpowers 对应能力 | 判断 | 主要差异 |
|---|---|---|---|
| `writing-plans.md` | `skills/writing-plans/SKILL.md` | 明显劣化 | 保留任务拆分、文件范围、验证命令，但缺少每步必须给实际代码、2-5 分钟粒度、完整 plan header、spec coverage / placeholder / type consistency 自检。 |
| `subagent-driven-development.md` | `skills/subagent-driven-development/SKILL.md` | 明显劣化 | 保留 fresh subagent 与两阶段审查，但缺少模型选择、状态处理、提问循环、失败重派策略、不得手工修 agent 失败、红旗清单和完整流程图。 |
| `executing-plans.md` | `skills/executing-plans/SKILL.md` | 轻到中度劣化 | 核心“读计划、先审查、逐项执行、验证失败停止”仍在；但少了 TodoWrite、main/master 禁止、与 worktree/finishing 的明确集成。 |
| `test-driven-development.md` | `skills/test-driven-development/SKILL.md` | 严重劣化 | 保留 RED-GREEN-REFACTOR，但丢失“先写生产代码必须删除重来”、无例外、常见借口、红旗、好/坏测试示例、每个函数测试、输出 pristine 等抗规避机制。 |
| `code-review.md` | `requesting-code-review` + `receiving-code-review` | 明显劣化 | 合并了请求审查和反馈处理，但丢失 SHA 范围工作流、reviewer prompt 使用方法、外部反馈怀疑规则、禁止表演式赞同、YAGNI 检查、逐项处理顺序。 |
| `finishing-branch.md` | `finishing-a-development-branch` | 明显劣化 | 保留新鲜验证和不自动合并，但缺少固定四选项、base branch 判断、PR/merge/discard 具体命令、discard typed confirmation、worktree cleanup 规则。 |
| `systematic-debugging.md` | `systematic-debugging/SKILL.md` | 严重劣化 | 保留四阶段名称，但缺少 Iron Law、逐步证据收集、多组件诊断、3 次失败后质疑架构、红旗和反借口表。 |
| `verification-before-completion.md` | `verification-before-completion/SKILL.md` | 明显劣化 | 保留“新鲜验证证据”，但缺少 gate function 的严厉语义、常见声明-所需证据矩阵、regression red-green 反转验证、agent 报告不可信检查。 |
| `dispatching-parallel-agents.md` | `dispatching-parallel-agents/SKILL.md` | 明显劣化 | 保留独立域、文件不冲突和集成验证；缺少适用/不适用校准、prompt 结构示例、错误示例、真实场景和并行收益/风险细节。 |
| `writing-skills.md` | `writing-skills/SKILL.md` | 严重劣化 | 只剩元技能摘要；原技能的 skill TDD、压力场景、CSO、frontmatter 规范、测试方法、反理性化、部署清单几乎全部缺失。 |
| `testing-anti-patterns.md` | `testing-anti-patterns.md` | 严重劣化 | 保留测试真实行为、不测 mock、不加测试专用生产方法；缺少五类反模式、gate function、示例、复杂 mock 诊断。 |
| `root-cause-tracing.md` | `root-cause-tracing.md` | 明显劣化 | 保留从症状向上追踪和源头修复；缺少栈追踪示例、污染定位脚本、完整追踪图和“绝不只修症状”的强约束展开。 |
| `defense-in-depth.md` | `defense-in-depth.md` | 中度劣化 | 保留入口、业务、环境、诊断多层验证；缺少四层示例、数据流映射、每层测试绕过验证和为什么单点验证不足。 |
| `condition-based-waiting.md` | `condition-based-waiting.md` | 中度劣化 | 保留真实条件、超时、禁止随意 sleep；缺少 waitFor 实现、场景表、何时允许固定等待、完整示例。 |
| prompt templates | 各 Superpowers prompt 模板 | 明显劣化 | HILP 资产注入更强，但实现/审查 prompt 的上下文、校准、输出格式、升级策略、自查问题和代码组织约束明显少于原版。 |

## 3. 主要劣化模式

### 3.1 从“可执行流程”退化为“纪律摘要”

Superpowers 原技能往往不只告诉 agent 做什么，还告诉 agent 如何识别错误、如何停止、如何复核、如何抵抗常见借口。`human-in-loop-execution/` 多数文件只保留了目标、输入、禁止事项和检查清单，缺少让 agent 在压力场景下稳定执行的细节。

### 3.2 抗误用和反理性化能力下降

劣化最明显的是 TDD、系统调试、完成前验证和技能编写。这些原技能都有强制语句、红旗、常见借口表、好坏示例和“违反后如何重来”的规则。前者删掉这些内容后，agent 更容易把规则解释成建议。

### 3.3 Prompt 可操作性下降

前者的 prompt 模板虽然加入 HILP asset_ref 和禁止越界项，但普遍缺少：

- 场景上下文如何组织。
- 子 agent 何时提问、何时升级、何时停止。
- 审查者如何校准严重性。
- 具体输出格式和 file:line 要求。
- 实现者自查维度。

这会降低 subagent 执行的一致性。

### 3.4 HILP 治理增强不等于原能力等价

前者在“不得越过已批准设计/蓝图/执行交接”方面强于原版，这是有价值的汉化裁剪。但这是治理边界增强，不会自动补回 Superpowers 原技能中的执行技术细节。

## 4. 可接受的保留项

以下能力在裁剪后仍保留了主骨架，可视为“方向正确但细节不足”：

- HILP 执行交接接收与执行路由。
- 执行计划必须绑定 HILP 三类 asset_ref。
- subagent 每任务新上下文与两阶段审查。
- inline 执行遇阻停止。
- TDD 的 RED-GREEN-REFACTOR 名义流程。
- 审查按 Critical / Important / Minor 分类。
- 完成前必须有新鲜验证证据。
- 调试必须先定位根因。
- 发现蓝图错误、新事实、越界需求时回到 HILP 重审。

这些说明前者不是无效技能包；问题在于它更像“压缩版执行守则”，不是 Superpowers 的等价实现。

## 5. 建议

若希望前者能力接近后者，同时保持 HILP 裁剪边界，建议优先补回以下内容：

1. **TDD：** 补回“先写生产代码则删除重来”、常见借口表、红旗、好/坏测试示例和最终验证 checklist。
2. **系统调试：** 补回 Iron Law、多组件诊断、一次一个假设、3 次失败后质疑架构、红旗和反理性化表。
3. **writing-plans：** 明确每步必须有实际代码/命令/预期输出，补自检：蓝图覆盖、占位符扫描、类型/签名一致性。
4. **subagent prompt：** 补回实现者提问、升级、BLOCKED/NEEDS_CONTEXT 处理、自查维度、review loop 细节。
5. **code review：** 拆清请求审查与接收反馈，补回 SHA 范围、外部反馈怀疑规则、禁止表演式附和、YAGNI 检查。
6. **finishing branch：** 补回固定四选项、确认丢弃、PR/merge/cleanup 的具体命令，但仍受 HILP 禁止越界项约束。
7. **writing-skills：** 若确实要保留该元技能，至少补回 skill TDD、压力场景和 CSO；否则它目前不足以承担原技能能力。

## 6. 最终回答

`human-in-loop-execution/` 中已有技能相较 `superpowers/` 对应技能**不是能力相当**。它们大多保留了核心纪律和 HILP 边界，但在操作细节、抗误用能力、prompt 精度、验证强度和流程校准上存在系统性劣化。若作为 HILP 执行层的最小中文裁剪版可以使用；若要求达到 Superpowers 原版的执行可靠性，需要补回上述关键细节。
