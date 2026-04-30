asset_id: hilp-execution-capability-restoration-design-choice
artifact_name: stage-3/design-choice
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: human-in-loop-planning
created_from: docs/changes/构建中文裁剪版Superpowers技能/review/对比human-in-loop-execution与superpowers能力-2026-04-29 00-23-18.md
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 方案设计与审批阶段：补回 human-in-loop-execution 相较 Superpowers 的执行能力

## 这个阶段要做什么

比较可行的补回路径，给出推荐方案，并把审核报告中的“能力劣化项”转化为可审批的修复方案。当前资产为待审批设计，不是已批准蓝图；未经明确批准，不应进入文件级实施。

## 已保存资产

- 文件路径：`docs/changes/补回human-in-loop-execution能力/planning/assets/02-方案设计_needs-approval_design-choice@v1.md`
- asset_ref：`stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`
- 当前状态：待审批（`ready-for-approval`）
- 当前是否需要审批：需审批。批准后才能进入实施蓝图阶段。

## 目标

在不恢复 Superpowers 被裁剪掉的独立技能入口、不破坏 HILP 规划 / 执行边界的前提下，补回 `human-in-loop-execution/` 已拥有技能中被压缩掉的关键执行能力，使其接近 Superpowers 对应技能的实际执行可靠性。

## 范围

### 包含

- `human-in-loop-execution/SKILL.md`
- `human-in-loop-execution/references/*.md`
- `human-in-loop-execution/references/prompt-templates/*.md`
- 必要时更新 `human-in-loop-execution/README.md`，说明能力补回边界。

### 不包含

- 不恢复 `brainstorming`、`using-git-worktrees`、`using-superpowers` 独立入口。
- 不复制 Superpowers 插件、hooks、commands、assets、历史 plans/specs、测试工程或上游贡献规则。
- 不修改 `superpowers/` 目录内容。
- 不把 HILP 的需求、设计、审批、蓝图职责写回执行技能。
- 不把待审批方案当作已批准蓝图使用。

## 成功标准

补回完成后应满足：

1. 每个 `human-in-loop-execution/` 已拥有技能都保留 HILP asset_ref、禁止越界项、停止回退条件。
2. 对应 Superpowers 技能中的强制门、红旗、常见误用、关键示例和验证校准被选择性补回。
3. TDD、系统调试、完成前验证、代码审查、subagent 执行和写技能六类高风险能力不再只是摘要清单。
4. prompt templates 能直接指导 subagent 提问、升级、审查、复审和报告，而不是只列输入字段。
5. 文档仍是中文裁剪版，不成为 Superpowers 原文全文翻译或插件复刻。
6. 任何执行中发现蓝图错误、新事实、越界需求或审批缺失，仍必须回到 HILP 重审。

## 关键事实

- 审核报告已确认：`human-in-loop-execution/` 不是无效技能包，但多数文件从“可执行流程”退化为“纪律摘要”。
- 劣化最严重的文件包括：`test-driven-development.md`、`systematic-debugging.md`、`writing-skills.md`、`testing-anti-patterns.md`、`subagent-driven-development.md`、`code-review.md`、`finishing-branch.md`。
- HILP 治理增强与 Superpowers 执行能力不是同一类能力；补回时必须两者并存。
- 当前任务是补回已保留技能的质量，不是扩大技能集合。

## 推荐方案

### 名称

**选择性忠实补回：保留 HILP 边界，补回 Superpowers 的执行强制门和抗误用细节。**

### 核心思路

以审核报告中的劣化项为索引，对每个已有 reference / prompt template 执行“能力补回”而不是“全文翻译”：

1. 先补回原技能中决定行为可靠性的强制规则。
2. 再补回 agent 容易犯错处的红旗、反例、常见借口和停止条件。
3. 最后补回必要的示例、输出格式、检查矩阵和 subagent prompt 校准。
4. 所有补回内容都加上 HILP 绑定：asset_ref、禁止越界项、蓝图外停止并回退。

### 为什么推荐

该方案能最大程度修复审核报告指出的能力劣化，同时避免两个极端：

- 避免“只加几句原则”导致执行可靠性仍不够。
- 避免“全文翻译 Superpowers”导致文档膨胀、HILP 边界混乱、裁剪目标失效。

## 备选方案

### 方案 A：最小补丁式补回

- 核心思路：只在每个 reference 中增加少量缺失条目，例如 TDD 增加“先写代码则删除重来”、debugging 增加“不得猜测修复”。
- 优点：改动小，审查成本低，不容易引入新边界问题。
- 代价：无法恢复 Superpowers 原技能的抗误用能力；仍可能只是更长的摘要。
- 不选原因：审核报告指出的问题是系统性劣化，最小补丁不足以让能力接近原版。

### 方案 B：全文汉化 Superpowers 对应技能

- 核心思路：把 Superpowers 对应文件完整翻译后嵌入 `human-in-loop-execution/references/`，再加入 HILP 约束。
- 优点：能力最接近原版，遗漏风险低。
- 代价：文档膨胀，重复内容多，容易恢复被裁剪掉的上下文假设，维护成本高。
- 不选原因：与“裁剪和汉化版本”的定位冲突，且可能把 Superpowers 的非 HILP 假设重新带入执行层。

## 具体补回包

### 补回包 P0：统一补回框架与 HILP 边界

- 目标文件：`SKILL.md`、必要时 `README.md`。
- 补回内容：
  - 明确“补回执行强制门，不补回设计审批入口”。
  - 在资源加载顺序中强调高风险纪律文件优先级：TDD、systematic-debugging、verification-before-completion、code-review。
  - 明确所有 reference 的补回内容必须受执行交接资产约束。
- 验收标准：
  - `SKILL.md` 仍不触发 brainstorming / using-worktrees / using-superpowers。
  - 输出纪律仍要求 HILP 三类 asset_ref。

### 补回包 P1：TDD、验证、调试三大硬纪律

#### P1.1 `test-driven-development.md`

补回内容：

- Iron Law：没有先失败的测试，不写生产代码。
- 违规处理：如果先写生产代码，删除并从测试重来；不得保留为参考。
- RED 验证要求：测试必须失败，失败原因必须是目标行为缺失，不是拼写或环境错误。
- GREEN 要求：最小实现，不加蓝图外能力。
- REFACTOR 要求：只在测试保持通过时清理。
- 好测试 / 坏测试示例：至少保留一个 mock 误用示例和一个真实行为示例。
- 常见借口表：太简单、稍后补测试、手工测过、赶时间、测试很难写。
- 输出要求：RED 命令、失败摘要、GREEN 命令、通过摘要、回归命令、未覆盖项。

验收标准：

- 文档中出现“删除并从测试重来”类强约束。
- 文档中包含至少一个好/坏测试对照。
- 检查清单能阻止“测试后补”被包装成 TDD。

#### P1.2 `verification-before-completion.md`

补回内容：

- Gate function：识别声明、运行完整命令、读取退出码、核对输出、再声明。
- 声明与证据矩阵：测试通过、构建通过、bug fixed、agent 完成、需求满足分别需要什么证据。
- 禁止措辞：应该、看起来、大概、agent 说完成。
- regression 验证：必要时要求 red-green 或回退验证证明测试能抓住问题。
- agent 委派后的独立验证：不得信任 agent 报告。

验收标准：

- 文档能明确禁止未运行新鲜命令就声明完成。
- 输出契约要求命令、退出码、关键输出摘要和未覆盖风险。

#### P1.3 `systematic-debugging.md`

补回内容：

- Iron Law：未完成根因调查前不得提出修复。
- 四阶段展开：根因调查、模式分析、单假设验证、实现修复。
- 多组件诊断：在边界处记录输入、输出、环境、配置传播。
- 一次一个假设：不得堆叠多个猜测性改动。
- 三次修复失败后停止并质疑架构或蓝图。
- 红旗和常见借口表：快速修一下、先试试、应该是 X、同时改几处。
- HILP 回退触发：若修复改变接口、数据形状、执行范围或禁止越界项，停止重审。

验收标准：

- 文档能阻止“猜测修复”。
- 明确三次失败后的停止条件。
- 与 `root-cause-tracing.md`、`defense-in-depth.md`、`condition-based-waiting.md` 存在清晰引用关系。

### 补回包 P2：计划与 subagent 编排

#### P2.1 `writing-plans.md`

补回内容：

- 固定 plan header：HILP 三类 asset_ref、目标、架构摘要、执行约束、禁止越界项。
- 文件结构锁定：先列文件职责，再拆任务。
- 任务粒度：每步 2-5 分钟，包含写失败测试、验证失败、最小实现、验证通过、提交或记录变更。
- No placeholders：禁止 TODO、TBD、“后续再定”、“类似上一步”、“写适当测试”。
- 每个任务必须含：精确文件路径、测试代码或验证命令、预期输出、验收点。
- 自检：蓝图覆盖、占位符扫描、类型 / 方法签名一致性、禁止越界项检查。

验收标准：

- 计划模板足以让低上下文执行者实施。
- 计划不能让执行者自行补设计判断。

#### P2.2 `subagent-driven-development.md`

补回内容：

- 控制者职责：读取计划、抽取任务全文、建立任务状态，不让 subagent 自行读全计划。
- 状态处理：DONE、DONE_WITH_CONCERNS、NEEDS_CONTEXT、BLOCKED 的处理规则。
- 提问循环：subagent 有疑问必须先问，控制者补上下文后重派。
- 审查循环：规格审查通过后才能质量审查；有问题必须修复并复审。
- 失败处理：subagent 失败时优先补上下文、换更强模型或拆任务，不得静默手工修复掩盖问题。
- 并行限制：仍禁止多个 subagent 编辑同一文件集或同一 HILP 资产。

验收标准：

- 文档明确“不得跳过 spec review 或 quality review”。
- 文档明确 BLOCKED / NEEDS_CONTEXT 时如何处理。
- 文档不允许以 subagent 为借口扩大 HILP 范围。

#### P2.3 prompt templates：实现、规格审查、质量审查

目标文件：

- `prompt-templates/implementer-prompt.md`
- `prompt-templates/spec-reviewer-prompt.md`
- `prompt-templates/code-quality-reviewer-prompt.md`

补回内容：

- 实现 prompt：增加背景上下文、开始前提问、代码组织、升级条件、自查维度、报告格式。
- 规格审查 prompt：增加“不信任实现报告”、逐项对照任务、缺失 / 额外 / 误解分类、file:line 输出。
- 质量审查 prompt：增加清晰职责、边界验证、测试真实行为、计划文件结构一致性、严重性校准。

验收标准：

- prompt 能直接复制给 subagent 使用。
- 每个 prompt 均包含 HILP asset_ref、禁止越界项、停止并回退条件。

### 补回包 P3：代码审查、反馈处理、分支收尾

#### P3.1 `code-review.md` 与 `prompt-templates/code-reviewer.md`

补回内容：

- 请求审查工作流：BASE_SHA、HEAD_SHA、diff 范围、实现说明、计划或需求引用。
- 审查类型：规格符合性、代码质量、测试质量、生产就绪性、HILP 越界风险。
- 接收反馈规则：先理解、再验证、再实现；外部反馈必须怀疑性验证。
- 禁止表演式附和：不得以“你说得对”替代技术判断。
- YAGNI 检查：审查建议若引入蓝图外能力，应标记为需 HILP 重审或拒绝。
- 多项反馈处理顺序：先澄清全部不明项，再按 Critical、简单修复、复杂修复顺序处理。

验收标准：

- 审查请求能固定到 git 范围。
- Critical 阻断继续，Important 修完再继续。
- 蓝图外建议不能被直接实现。

#### P3.2 `finishing-branch.md`

补回内容：

- 收尾前必须运行完成前验证和审查阻断项检查。
- 固定后续选项：本地合并、推送创建 PR、保留分支、丢弃工作。
- 丢弃工作必须 typed confirmation。
- 合并或 PR 前后都要验证；失败不得继续。
- worktree cleanup 只在安全选项下执行，不自动删除用户工作。
- 完成后回写 HILP 执行结果、偏差、新事实或重审触发。

验收标准：

- 文档能阻止测试失败时进入 merge / PR。
- 文档能阻止未确认删除工作。
- HILP 归档与 git 分支收尾边界清楚。

### 补回包 P4：测试与调试支持技术

#### P4.1 `testing-anti-patterns.md`

补回内容：

- 五类反模式：测试 mock 行为、测试专用生产方法、不了解依赖就 mock、不完整 mock、把集成测试当附加事项。
- 每类至少包含：违规信号、为什么错、修复方式、gate function。
- 强调 TDD 如何预防这些反模式。

验收标准：

- 文档能阻止“断言 mock 存在”被当成行为测试。
- 文档能阻止向生产类加入测试专用方法。

#### P4.2 `root-cause-tracing.md`

补回内容：

- 从症状点向上追踪的标准步骤。
- 何时添加 stack trace / diagnostic instrumentation。
- 直接失败点、调用者、参数来源、最早触发点四层输出要求。
- 明确“不要只修深层症状点”。

验收标准：

- 文档能指导定位坏值来源，而不是只修报错处。

#### P4.3 `defense-in-depth.md`

补回内容：

- 四层验证模型：入口边界、业务逻辑、危险环境守卫、诊断记录。
- 数据流映射方法。
- 每层验证都要有测试或命令证据。
- 单点验证不足的说明。

验收标准：

- 文档能指导把已确认根因转化为多层防再发约束。

#### P4.4 `condition-based-waiting.md`

补回内容：

- waitFor 伪代码或语言无关模式。
- 场景表：事件、状态、数量、文件、复杂条件。
- 允许固定等待的唯一条件：真实时间行为测试，且先等触发条件，再等已知时间。
- 常见错误：轮询过快、无超时、缓存旧状态。

验收标准：

- 文档能阻止随意 sleep 修 flaky。
- 等待失败信息必须可诊断。

### 补回包 P5：写技能元纪律

#### P5.1 `writing-skills.md`

补回内容：

- 技能编写等同于文档 TDD。
- 先有压力场景，再写或修改技能。
- RED：无技能基线失败；GREEN：最小技能；REFACTOR：补漏洞再测。
- description 只写触发条件，不写流程摘要。
- CSO 要点：关键词、触发条件、避免描述即流程。
- 文件组织：何时放 SKILL.md、何时拆 supporting file。
- 部署前 checklist。

验收标准：

- 文档不再只是 35 行摘要。
- 能阻止无压力场景直接写技能。
- 不恢复 Superpowers 插件 / hooks / commands。

## 关键取舍

- 正确性 / 安全性：优先补回强制门和停止条件，而不是补更多普通说明。
- 可回退性：每个补回包可独立审查；若某包引发边界问题，可单独回滚。
- 改动范围：集中在 `human-in-loop-execution/`，不触碰 `superpowers/`。
- 可维护性：不全文翻译，降低同步负担；但保留足够原理与示例避免再次退化为摘要。
- 未来扩展性：后续可基于压力测试继续补漏洞，但本轮先补最明显能力缺口。

## 风险与控制

### 风险 1：文档膨胀导致使用成本上升

- 控制：只补回强制门、反误用细节、关键示例和 prompt 校准；避免迁移长篇历史解释。

### 风险 2：恢复 Superpowers 非 HILP 假设

- 控制：所有新增内容必须显式绑定 HILP asset_ref、执行交接、禁止越界项和回退条件。

### 风险 3：补回后仍不可验证

- 控制：每个补回包都定义文本验收标准；实施蓝图阶段再转为确定性检查命令。

### 风险 4：把设计审批内容写进执行技能

- 控制：新增内容只处理“怎么安全实现、测试、审查、调试、收尾”，不处理需求选择、方案审批或蓝图补齐。

## 建议实施顺序

1. P1：先补硬纪律，防止后续执行继续退化。
2. P2：补计划与 subagent 编排，让执行路径可落地。
3. P3：补审查和收尾，恢复质量 gate。
4. P4：补支持技术，提高测试和调试质量。
5. P5：补元技能，避免以后改技能时继续无测试退化。
6. P0：贯穿执行，最后统一检查入口和 README 边界。

## 建议验证策略

后续实施蓝图应把以下验证转成具体命令或检查：

- 文件存在性：所有目标 reference 与 prompt template 存在。
- 禁止路径：不修改 `superpowers/`，不新增插件、hooks、commands、assets、tests。
- 关键词检查：
  - TDD 文件包含失败测试、删除重来、RED-GREEN-REFACTOR、常见借口或红旗。
  - debugging 文件包含根因、假设、三次失败、架构或蓝图回退。
  - verification 文件包含新鲜验证、退出码、输出摘要、不得声明完成。
  - subagent 文件包含 DONE_WITH_CONCERNS、NEEDS_CONTEXT、BLOCKED、两阶段审查。
  - code review 文件包含 BASE_SHA、HEAD_SHA、Critical、Important、Minor、外部反馈验证。
- 结构检查：每个 reference 仍保留适用时机、输入契约、执行规则、禁止事项、输出契约、检查清单。
- 压力场景检查：至少为 TDD、debugging、verification、subagent、code-review、writing-skills 各写一个误用场景，确认新增文本能阻止误用。

## 需要用户决定什么

- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项；如果用户不批准，则不能进入实施蓝图。
- 问题描述：是否批准采用“选择性忠实补回”作为后续蓝图依据。
- 可选项：
  1. 批准推荐方案：选择性忠实补回。
  2. 改为最小补丁式补回。
  3. 改为全文汉化 Superpowers 对应技能。
  4. 要求修订本方案。
- 建议：批准选项 1。
- 默认路径：若用户不明确选择，保持待审批，不进入实施蓝图。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：不得把“选择性忠实补回”当作已批准实施路线；不得开始修改 `human-in-loop-execution/` 文件。

## 当前状态

- 中文状态名：待审批
- 内部状态值：`ready-for-approval`
- 进入该状态的理由：目标、范围、成功标准、关键事实和影响面已由审核报告支持；不存在必须人工裁决的技术阻断；推荐方案可提交人工审批。

## 下一步

- 下一阶段：等待用户批准；批准后进入实施蓝图阶段。
- 继续前提：用户明确批准 `stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]` 的推荐方案，或指定修订方向。
- 当前阻断项：无阻断项，但缺少人工批准，不能进入绑定性蓝图。
