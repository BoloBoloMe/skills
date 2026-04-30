asset_id: hilp-execution-capability-restoration-design-choice
artifact_name: stage-3/design-choice
version: v2
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-design-approval
created_from: stage-reapproval/reapproval-decision@v1 [state=archived｜中文状态=已归档]
last_event: new-fact-original-examples-confirmed
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 方案设计与审批阶段：human-in-loop-execution 最新补强方案 v2

## 这个阶段要做什么

在旧版补强已完成的基础上，针对复审报告中剩余三个短板制定最新版补强方案，并明确第 3 项纳入依据。

## 已保存资产

- 文件路径：`docs/changes/补回human-in-loop-execution能力/planning/assets/02-方案设计_needs-approval_design-choice@v2.md`
- asset_ref：`stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]`
- 当前状态：待审批（`ready-for-approval`）
- 当前是否需要审批：需审批。批准后才能进入实施蓝图阶段。

## 事实基础

- 复审报告：`docs/changes/补回human-in-loop-execution能力/review/重新对比human-in-loop-execution与superpowers能力-2026-04-29 11-07-03.md`。
- 原版代码示例核查报告：`docs/changes/补回human-in-loop-execution能力/review/核查Superpowers原版代码示例-2026-04-29 11-13-23.md`。
- 核查结论：Superpowers 原版在 TDD、系统化调试主文件、测试反模式，以及 root-cause-tracing / defense-in-depth / condition-based-waiting 配套文件中均存在代码示例。因此第 3 项属于原版能力的选择性补回，不是新增设计偏好。

## 推荐方案

### 名称

**二次精准补强：补元技能、补 subagent 调度、补原版已有代码示例。**

### 核心思路

只补复审后剩余的高价值差距，不再重写已达标的主执行链路：

1. `writing-skills.md`：补齐 CSO、技能测试类型、压力测试、反理性化、部署 checklist。
2. `subagent-driven-development.md`：补齐模型选择、失败重派、红旗清单、复杂任务调度校准。
3. TDD / 调试 / 测试反模式相关文件：基于原版已有示例，补入少量高信号代码示例，而不是全文翻译原版。

### 为什么推荐

- 该方案直接对应复审报告剩余短板。
- 第 3 项已有事实支持：原版确实有代码示例。
- 改动范围小于全文复刻，能保持 HILP 中文裁剪版定位。
- 能显著提升 agent 在压力、复杂 subagent 调度和测试设计误用场景下的稳定性。

## 备选方案

### 方案 A：只补第 1 和第 2 项

- 核心思路：仅补 `writing-skills.md` 与 `subagent-driven-development.md`。
- 优点：改动更小。
- 代价：TDD / 调试 / 测试反模式仍缺少原版已有的示例支撑。
- 不选原因：原版事实已确认第 3 项存在代码示例，继续排除会保留不必要差距。

### 方案 B：全文翻译三类原版示例与说明

- 核心思路：完整翻译相关原版章节。
- 优点：遗漏风险最低。
- 代价：文档膨胀，裁剪版定位变弱，维护成本高。
- 不选原因：当前只需补高信号示例，不需要恢复原版完整篇幅。

## 具体补强范围

### 补强包 A：`writing-skills.md`

目标：把当前元技能从“可用摘要”提升为“足以指导后续技能维护”的执行版。

补入内容：

- CSO 规则：
  - description 只写触发条件，不写流程摘要。
  - 使用具体触发症状、关键词、错误信号和场景词。
  - 避免 `@` 强制加载大型参考；用技能名和 required marker。
- 技能测试类型：
  - 纪律型：压力场景、反借口、红旗。
  - 技术型：应用场景、边界场景、缺信息场景。
  - 参考型：检索场景、应用场景、缺口测试。
  - pattern 型：识别场景、应用场景、反例场景。
- 压力测试流程：
  - RED：旧行为或无技能基线失败。
  - GREEN：最小规则让场景通过。
  - REFACTOR：补漏洞并复测。
- 反理性化模板：
  - 常见借口表。
  - 红旗清单。
  - “文档小改也要压力场景”的明确约束。
- 部署 checklist：
  - frontmatter、description、压力场景、验证证据、禁止越界项、安装边界。

不补内容：

- 不复制 Superpowers 插件、hooks、commands、测试工程或贡献流程。
- 不引入完整 Anthropic best practices 长文。

### 补强包 B：`subagent-driven-development.md`

目标：把当前 subagent 编排从“核心流程可用”提升为“复杂任务下更稳定”。

补入内容：

- 模型选择规则：
  - 机械任务使用较轻模型。
  - 多文件集成和调试使用标准模型。
  - 架构、设计判断、最终审查使用最强可用模型。
- 失败重派策略：
  - `NEEDS_CONTEXT`：补上下文后重派。
  - `BLOCKED`：判断是上下文不足、模型能力不足、任务过大还是蓝图错误。
  - 能力不足：换更强模型。
  - 任务过大：拆小任务。
  - 蓝图错误：回到 HILP 变更重审。
- 红旗清单：
  - 让 subagent 自己读整份计划。
  - 跳过规格审查或质量审查。
  - 规格审查未通过就做质量审查。
  - 多个实现 subagent 并行编辑同一文件。
  - reviewer 有问题但不复审。
  - 实现者自查替代真正审查。
  - 控制者手工修 subagent 失败以绕过流程。
- 复杂任务调度校准：
  - 每个任务给完整任务文本和局部上下文。
  - subagent 可以开始前或过程中提问。
  - 任务完成后先 spec compliance，再 code quality。

不补内容：

- 不引入平台专用 Task API 语法作为唯一方式。
- 不恢复 Superpowers worktree 入口。

### 补强包 C：TDD / 调试 / 测试反模式代码示例

目标：补回原版已有的示例能力，但保持少量高信号。

目标文件：

- `human-in-loop-execution/references/test-driven-development.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/testing-anti-patterns.md`
- 可选：`root-cause-tracing.md`、`defense-in-depth.md`、`condition-based-waiting.md`，只在篇幅仍可控时补一段伪代码或短示例。

补入内容：

- TDD：
  - 一个好测试 / 坏测试 TypeScript 或伪代码对照。
  - 一个最小 GREEN / 过度实现对照。
  - 示例必须强调 HILP 蓝图外能力不得加入。
- 系统调试：
  - 一个多组件边界诊断 bash 示例，展示输入、输出、环境和配置传播。
  - 一个“一次一个假设”的最小诊断例。
- 测试反模式：
  - mock 行为测试 before/after。
  - 测试专用生产方法 before/after。
- 条件式等待可选示例：
  - `waitFor` 简短伪代码或 TypeScript 片段。

示例约束：

- 每个文件最多补 1-2 个短示例。
- 示例只服务规则理解，不引入特定项目 API。
- 示例不能扩大 HILP 执行范围。
- 不全文翻译原版示例。

## 文件范围

允许修改：

- `human-in-loop-execution/references/writing-skills.md`
- `human-in-loop-execution/references/subagent-driven-development.md`
- `human-in-loop-execution/references/test-driven-development.md`
- `human-in-loop-execution/references/systematic-debugging.md`
- `human-in-loop-execution/references/testing-anti-patterns.md`
- 可选修改：
  - `human-in-loop-execution/references/root-cause-tracing.md`
  - `human-in-loop-execution/references/defense-in-depth.md`
  - `human-in-loop-execution/references/condition-based-waiting.md`

禁止修改：

- `superpowers/**`
- 插件、hooks、commands、assets、历史 plans/specs、测试工程。
- HILP 规划协议文件，除本变更目录内规划资产外。
- `human-in-loop-execution/` 下未列文件，除非后续蓝图明确新增。

## 成功标准

1. `writing-skills.md` 能回答：如何写 description、如何做压力场景、如何做 skill TDD、如何部署前自检。
2. `subagent-driven-development.md` 能回答：选什么模型、BLOCKED / NEEDS_CONTEXT 如何重派、哪些红旗必须停止。
3. TDD / 调试 / 测试反模式相关文件至少包含少量原版同类代码示例或伪代码示例。
4. 所有新增内容仍保持 HILP asset_ref、禁止越界项和回退 HILP 的边界。
5. 文件仍保持既有六段结构，不引入蓝图外入口。

## 验证建议

后续实施蓝图应将以下检查转成确定性命令：

```bash
grep -n "CSO\|搜索优化\|description" human-in-loop-execution/references/writing-skills.md
grep -n "压力场景\|RED\|GREEN\|REFACTOR" human-in-loop-execution/references/writing-skills.md
grep -n "模型选择\|NEEDS_CONTEXT\|BLOCKED\|红旗" human-in-loop-execution/references/subagent-driven-development.md
grep -n "```" human-in-loop-execution/references/test-driven-development.md
grep -n "```" human-in-loop-execution/references/systematic-debugging.md
grep -n "```" human-in-loop-execution/references/testing-anti-patterns.md
git diff --name-only -- superpowers | grep . && exit 1 || true
```

## 关键取舍

- 正确性 / 安全性：优先补规则触发和停止条件，不用长示例覆盖核心纪律。
- 可维护性：每个文件只补少量高信号内容，避免全文翻译。
- 未来扩展性：若压力测试发现新漏洞，再按 writing-skills 的文档 TDD 继续补。
- HILP 边界：任何示例或 subagent 策略都不得让执行者补做规划判断。

## 需要用户决定什么

- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项；但未批准前不得进入实施蓝图。
- 问题描述：是否批准本 v2 最新补强方案。
- 可选项：
  1. 批准推荐方案：补强包 A、B、C 全部纳入。
  2. 只批准补强包 A、B，不纳入代码示例。
  3. 要求调整补强范围或文件范围。
- 建议：批准选项 1。
- 默认路径：未获明确批准则保持待审批，不进入蓝图。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：不得把补强包 A/B/C 当作已批准执行范围；不得开始修改目标文件。

## 当前状态

- 中文状态名：待审批
- 内部状态值：`ready-for-approval`
- 进入该状态的理由：事实基础已建立，补强范围确定，不存在必须人工裁决阻断，可提交审批。

## 下一步

- 下一阶段：等待用户批准；批准后进入实施蓝图阶段。
- 继续前提：用户明确批准 `stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]` 的推荐方案，或指定修订方向。
- 当前阻断项：无阻断项，但缺少人工批准。
