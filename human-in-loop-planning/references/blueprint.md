# 实施蓝图模块

## 模块元信息
- internal_module: `hilp-blueprint`
- 原触发描述：用于把已明确 已批准的 Stage 3 设计资产转成确定、唯一、可审批的实施蓝图，明确改动切片、依赖顺序、风险检查点和实现约束。只有在存在完整 asset_ref、owner_skill=hilp-design-approval、last_decision 为 人工批准授予（Human Approval Granted） 决策、不存在未解决 必须人工裁决的决策，且所有会影响实施的变量均已确定时才应触发。若当前设计仅为 ready-for-approval（待审批）、方案选择未定、缺少批准资产引用、存在实施关键未确定项或上游前提失效，不要触发本 Skill。

# 概览

你负责两个阶段：
- Stage 4：改动拓扑（Change Topology）
- Stage 5：实现约束（Implementation Constraints）

你的目标是把上游设计转成“确定、唯一、可执行但仍属于规划层”的实施蓝图。正式蓝图不得承载任何待定、可选、后续确认或执行时再判断的内容。

蓝图可以有两种组织形式：
- 单体蓝图：所有 Stage 4/5 内容集中在一个 `implementation-blueprint` 资产中。
- 分层蓝图包：以 `implementation-blueprint` 作为主蓝图 / manifest，绑定若干子蓝图和覆盖矩阵。分层蓝图包只改变组织形式，不降低确定性、覆盖性或审批纪律。

你必须明确：
- 改动切片（change slices）
- 依赖顺序（dependency order）
- Execution Plan Contract（包含 `execution_plan_contract`、`parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources`）
- 风险检查点（risk checkpoints）
- 发布 / 验证检查点（rollout / verification checkpoints）
- 数据形状（data shape）
- 接口约束（interface constraints）
- 局部算法骨架（local algorithm skeleton）
- 错误处理要求（error handling requirements）
- 测试承诺（test commitments）

你不负责：
- 不重新定义需求
- 不重新发明设计路线
- 不直接开始写最终实现代码
- 不把未确定项写入正式蓝图资产
- 不用分层蓝图包隐藏缺口、弱化审批或把规划判断留给执行者

## 极简工作流

进入本模块前必须存在完整资产引用：

```text
asset_ref: stage-3/design-choice@vN [state=approved｜中文状态=已批准]
owner_skill: hilp-design-approval
last_decision: <human approval decision-id>
```

若缺少上述任一项，不得仅凭“方案已经定了”“就按这个做”等自然语言判断进入蓝图；必须回到 `hilp-design-approval`、等待 `人工批准授予（Human Approval Granted）`，或交给 `hilp-reapproval` 裁决。

1. 检查并读取完整的已批准 Stage 3 设计资产。
2. 判定蓝图规模：`single`（单体蓝图）或 `package`（分层蓝图包）。
3. 输出 Stage 4 的改动拓扑。若使用分层蓝图包，主蓝图只展开跨切片拓扑，子蓝图承载局部细节。
4. 输出 Stage 5 的实现约束。若使用分层蓝图包，全局约束写入主蓝图，局部约束写入对应子蓝图。
5. 执行确定性检查，确认文件范围、接口、数据形状、算法骨架、错误处理、测试承诺、风险处理、发布 / 验证顺序均无未确定项。分层蓝图包必须对主蓝图、全部子蓝图和覆盖矩阵逐项检查。
6. 检查兼容 / 回滚检查要求是否已经确定。
7. 只有确定性检查通过时，才输出蓝图状态并保存 `implementation-blueprint` 资产；分层蓝图包还必须保存 manifest 绑定的全部子蓝图和覆盖矩阵。
8. 决定是否可交接到执行层；只有已批准且确定性检查通过的蓝图或蓝图包才能交接。
9. 若发现上游前提失效，则改走 `hilp-reapproval`；若发现设计未真正收敛，则回交 `hilp-design-approval`；若发现事实不足，则回交 `hilp-requirements-facts`。

lean / standard / strict 的详细差异见 `references/routing-matrix.md`。
交接契约见 `references/handoff-contracts.md`。
事件规则见 `references/event-action-rules.md`。

## 蓝图规模判定

蓝图规模判定只决定组织形式，不改变阶段门槛。无法确定规模时，选择能够让审批者完整审查且不会隐藏细节的更严格组织形式。

### 单体蓝图

适用于：
- 局部或低耦合修改。
- 改动切片较少，依赖关系可线性表达。
- 文件范围、接口和验证承诺在一个文档中仍可清晰审查。
- 无跨波次发布、长兼容窗口或复杂回滚边界。

### 分层蓝图包

命中以下任一条件时，应使用分层蓝图包：
- 涉及多个子系统、模块族或调用链层级。
- 改动切片数量较多，平铺后会显著降低审查可读性。
- 文件范围庞大，主文档列出完整文件级细节会掩盖关键拓扑。
- 依赖关系不是单一线性链，需要按 DAG、波次或阶段表达。
- 存在多阶段发布、兼容窗口、迁移路径、回滚边界或人工操作点。
- 治理模式为 `strict`，且蓝图细节足以形成多个独立审查域。
- 审批者需要按领域、波次或风险等级分开审查。

## 分层蓝图包规则

分层蓝图包由一个主蓝图 / manifest、若干子蓝图和一个覆盖矩阵组成：

```text
stage-4-5/implementation-blueprint@vN       # 主蓝图 / manifest
stage-4-5/blueprint-slice-<slice-id>@vN     # 子蓝图
stage-4-5/coverage-matrix@vN                # 覆盖矩阵
```

推荐文件名：

```text
assets/03-实施蓝图_implementation-blueprint@vN.md
assets/03-实施蓝图_blueprint-slice-<slice-id>@vN.md
assets/03-实施蓝图_coverage-matrix@vN.md
```

主蓝图 / manifest 必须包含：
- `blueprint_form: package`
- 包内资产清单，逐项绑定 `asset_ref`、版本、状态和中文状态名。
- 切片索引，说明每个切片的职责、风险等级、依赖、发布波次和子蓝图引用。
- 跨切片依赖图或波次顺序。
- 全局不变量、全局接口 / 数据边界、全局风险与回滚边界。
- 发布 / 验证总顺序。
- 覆盖矩阵引用。
- 审批边界：本次审批精确覆盖哪些主蓝图、子蓝图和覆盖矩阵版本。

子蓝图必须包含：
- `blueprint_form: package-slice`
- 所属主蓝图引用。
- 切片 ID、职责边界、前置依赖和禁止越界项。
- 涉及模块 / 子系统 / 文件范围。
- 数据形状、接口约束、局部算法骨架、错误处理要求。
- 局部风险检查点、局部发布 / 验证检查点和测试承诺。
- 局部确定性检查结果。

覆盖矩阵必须至少覆盖：

```text
| 设计决策 / 需求承诺 | 改动切片 | 子蓝图 | 验证项 | 风险检查点 |
|---|---|---|---|---|
```

覆盖矩阵用于证明：
- 每个已批准设计决策都有对应改动切片。
- 每个必要改动切片都有验证承诺。
- 每个高风险点都有检查点。
- 主蓝图未遗漏子蓝图中的关键约束。

## 分层审批纪律

分层蓝图包的审批对象不是自然语言意义上的“主蓝图”，而是主蓝图 / manifest 绑定的固定版本集合。

批准语义必须明确绑定类似以下清单：

```text
approved_package_manifest: stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]
package_members:
  - stage-4-5/blueprint-slice-domain-model@v2 [state=approved｜中文状态=已批准]
  - stage-4-5/blueprint-slice-service-layer@v1 [state=approved｜中文状态=已批准]
  - stage-4-5/coverage-matrix@v3 [state=approved｜中文状态=已批准]
```

规则：
- 主蓝图 / manifest、全部子蓝图和覆盖矩阵均必须通过确定性检查。
- 任一包内资产仍为 `draft`（草稿）、`ready-for-human-decision`（待人工裁决）、`ready-for-approval`（待审批）、`needs-revision`（待修订）或 `archived`（已归档）时，蓝图包整体不得作为 `approved`（已批准）输入交接给执行层。
- 任一子蓝图内容性修订必须递增该子蓝图版本，并更新主蓝图 / manifest 的包内资产清单。
- 主蓝图 / manifest 的包内资产清单发生变化时，旧批准不自动覆盖新集合，必须重新审批或进入变更重审。
- 分层蓝图包不得通过“主蓝图已批准”绕过未批准、未确定或已失效的子蓝图。

## 未通过确定性检查时的处理

不得创建或更新 `stage-4-5/implementation-blueprint` 正式资产。用户可见输出只说明：缺少哪些确定结论、为什么不能进入实施蓝图、需要回到哪个前置阶段解决。若已有旧蓝图资产受影响，必须按事件规则标记为 `needs-revision`（待修订）或进入重审。分层蓝图包中任一成员未通过确定性检查时，整个蓝图包不得进入 `ready-for-approval`（待审批）或 `approved`（已批准）。

## 输出模板

# 实施蓝图阶段

## 这个阶段要做什么
- 用一句话说明：把已批准的方案转成可执行的改动切片、顺序、约束和验证检查点。

## 已保存资产
- 文件链接：[03-实施蓝图_implementation-blueprint@vN.md](相对路径到assets/03-实施蓝图_implementation-blueprint@vN.md)
- asset_ref：`stage-4-5/implementation-blueprint@vN [state=<state>｜中文状态=<state_label>]`
- 蓝图形式：单体蓝图 / 分层蓝图包。
- 上游设计：`stage-3/design-choice@vM [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@vM.md](相对路径到assets/02-方案设计_design-choice@vM.md)
- 当前状态：必须写中文状态名，必要时附内部状态值。
- 当前是否需要审批：只能说明待审批或已批准；若仍需要补蓝图或人工裁决，不得产出正式蓝图资产。
- 若当前状态为 `ready-for-approval｜中文状态=待审批`：同时列出审核包链接 [03-implementation-blueprint@vN-review.md](相对路径到review-pack/03-implementation-blueprint@vN-review.md) 和当前待审入口 [当前待审.md](相对路径到_current/当前待审.md)；分层蓝图包还必须说明审核范围覆盖主蓝图 / manifest 绑定的固定版本集合。

## 改动拓扑
- 改动切片：
- 依赖顺序：
- 风险检查点：
- 发布检查点：
- 验证检查点：
- 涉及模块 / 子系统 / 文件范围：

## 蓝图审核摘要
- 本蓝图要实现什么：
- 执行拓扑：用一行或短列表说明波次 / 主链路，不展开完整 YAML。
- 关键依赖：只列影响审核判断的前置关系。
- 禁止越界项：
- 主要风险检查点：
- 验证承诺：
- 当前是否可提交审批：是 / 否；若否，说明阻断项。
- 表达原则：必须清爽、精炼，只展示审核者判断蓝图是否合理所需的信息，不得要求审核者阅读完整 YAML 才能理解执行顺序。
- 禁止内容：不得在正文审核视图中展开完整 `execution_plan_contract`、大段 `allowed_files`、`verification_resources`、`context_packet`、`must_haves`、`stop_conditions` 或其他 agent 专用字段。
- 一致性要求：人类审核视图必须与机器执行契约语义一致；若二者冲突，不得提交审批，必须先修订蓝图。

## Execution Plan Contract
- 适用条件：当蓝图需要交接为一个或多个执行单元、发布波次或整包执行任务时填写；不拆分时写“无”。
- 契约来源：读取并遵守 `references/execution-plan-contract.md`。
- 表达位置：完整 `execution_plan_contract` 应放入附录、折叠区或独立 contract 资产；蓝图正文优先展示“人类审核视图”。
- 顶层字段：必须使用 `execution_plan_contract`，不得把 `execution_unit` 写成顶层 contract。
- `parallelization`：必须固定 `strategy`、`user_opt_in_required`、`conflict_policy` 和 `integration_required_after_parallel_group`。
- 单元调度字段：每个 `units[]` 必须固定 `order`、`depends_on`、`parallel_group`、`parallel_eligible`、`allowed_files`、`forbidden_files`、`file_domain`、`shared_state` 和 `verification_resources`。
- HILE 边界：执行交接只能摘录已批准机器执行契约，不得从人类审核摘要中推断、补齐或改写执行顺序与依赖关系；不得让 HILE 临场决定 EU 是否存在、是否独立、是否可并行。缺少任一调度字段时不得交接执行。

## Execution Unit Contract
- 适用条件：当蓝图需要交接为一个或多个 `execution_unit` 时填写；不拆分时写“无”。
- 契约来源：读取并遵守 `references/execution-unit-schema.md`；若存在 `execution_plan_contract`，该契约只定义 `units[]` 的单元字段。
- 每个 `execution_unit` 必须固定：`unit_id`、标题、依赖、`allowed_files`、`context_packet`、`must_haves`、验证命令、停止条件和前序摘要。
- 允许文件：`allowed_files` 必须是精确文件路径，不得写成目录级模糊范围或执行时按需扩展。
- 依赖：逐单元列出前置 `execution_unit` 或资产条件；依赖顺序不得留给执行层判断。
- 验证：逐单元列出必须运行的命令、期望退出码和输出摘要。
- 停止条件：逐单元列出命中后停止并回退的条件，不得写成继续修复策略。
- 上下文包：逐单元列出 `context_packet`，只包含当前单元所需的已批准设计、已批准蓝图、有效交接、必读章节、相关决策、前序摘要和明确忽略项。

## Must-haves Verification Ladder
- 适用条件：当蓝图包含测试承诺、验收口径或 execution_unit 完成条件时填写；无额外 must-have 时写“无”。
- 契约来源：读取并遵守 `references/verification-contract.md`。
- `must_haves`：逐项列出 must_have_id、Truths、Artifacts、Key Links、验证层级、完成标准和未覆盖风险。
- 验证梯度：每个 `must_haves` 项必须绑定静态检查、命令执行、行为测试或人工检查之一；自动化证据不足时必须说明人工检查依据。
- 完成门槛：声明蓝图可执行前，所有 `must_haves` 都必须有可复核证据链、明确验证命令或人工检查方式、期望退出码 / 通过标准和重审触发条件。
- 测试承诺：`测试承诺` 必须引用对应 `must_haves`，不得只写笼统的“运行测试”或“人工确认”。

## 分层蓝图包 manifest
- 使用条件：仅当蓝图形式为分层蓝图包时填写；单体蓝图写“无”。
- 包内资产清单：
- 切片索引：
- 跨切片依赖图 / 波次：
- 覆盖矩阵：
- 审批边界：

## 实现约束
- 数据形状：
- 接口约束：
- 局部算法骨架：
- 错误处理要求：
- 测试承诺：

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：单体蓝图写“无”；分层蓝图包必须列出主蓝图、全部子蓝图和覆盖矩阵均已通过。

## 当前判断
- 当前是否可交接到执行层：仅当蓝图资产或蓝图包为 `approved`（已批准）、上游设计仍有效且确定性检查通过时才写“是”。
- 当前阻断项：正式蓝图资产中只能写“无阻断项”。若存在阻断项，不得产出正式蓝图资产。
- 是否存在兼容 / 回滚约束：必须写明确定约束；不存在时写“无”。
- 当前状态：写中文状态名，必要时附内部状态值。

## 下一步需要用户做什么
- 若蓝图可审批，要求用户明确批准当前资产版本；分层蓝图包必须要求用户明确批准主蓝图 / manifest 绑定的固定版本集合。
- 若蓝图已批准，说明可进入执行交接阶段。

## Stage 4/5 蓝图审批门槛

只有同时满足以下条件时，蓝图才能进入 `ready-for-approval`（待审批）：

1. 改动切片已覆盖推荐设计的全部必要改动。
2. 依赖顺序足以支持安全实施。
3. 风险检查点与发布 / 验证检查点已明确且没有待选分支。
4. 接口约束、数据形状、局部算法骨架、错误处理要求与测试承诺已明确。
5. 文件范围、模块范围、执行边界和禁止越界项已明确。
6. 需要执行单元时，`execution_plan_contract`、`parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 和 `verification_resources` 已明确。
7. 不存在未解决的 `human_decision_required`（必须人工裁决）。
8. 不存在待定、可能、视情况、后续确认、执行时再判断、可选 A/B、暂按、大概、原则上、TODO、TBD、问号、空字段或占位符。
9. 蓝图未改写 Stage 3 已批准设计 的边界或取舍。
10. 上游设计资产 仍为 `approved`（已批准），未被标记为 `needs-revision`（待修订）或 `archived`（已归档）。
11. 若使用分层蓝图包，主蓝图 / manifest、全部子蓝图和覆盖矩阵均已保存、版本固定、相互引用一致、确定性检查通过，且覆盖矩阵证明设计决策、切片、验证项和风险检查点没有遗漏。

若存在 必须人工裁决的决策，不得产出正式蓝图资产，必须回到可裁决该问题的前置阶段。
若缺少关键蓝图内容，不得以 `draft`（草稿）形式承载缺口；必须回到 `hilp-requirements-facts`、`hilp-design-approval` 或 `hilp-reapproval` 消除不确定性。

进入 `hilp-execution-handoff` 的蓝图必须是 `approved`（已批准）。lean 模式下，批准可以是显式轻量批准，例如“确认按此蓝图执行”，但仍必须明确绑定当前蓝图资产版本；分层蓝图包必须明确绑定主蓝图 / manifest 的包内资产版本集合。

## 硬约束

- `human_decision_required`（必须人工裁决）未解决时，不得形成绑定性蓝图。
- 存在任何会影响实现路线、文件范围、接口形态、数据形状、算法骨架、错误处理、风险处理、验证口径、发布顺序或执行边界的未确定项时，不得产出正式蓝图资产。
- 不得改写上游批准边界。
- 不得把实现约束扩张成新的设计讨论。
- 不得省略风险检查点与验证检查点。
- 不得把蓝图直接写成最终代码。
- 不得把并行资格、文件域、共享状态或验证资源留给 HILE 执行阶段补齐。
- 不得用分层蓝图包把必需细节从主蓝图移走后不落入任何子蓝图或覆盖矩阵。
- 不得批准未绑定固定版本集合的分层蓝图包。

## 交接规则

- 只有蓝图资产为 `stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]`、`owner_skill=hilp-blueprint`、存在 `last_decision`、确定性检查通过，且上游设计资产仍为 `approved`（已批准）时，才能交给 `hilp-execution-handoff`。
- 若蓝图形式为分层蓝图包，主蓝图 / manifest 绑定的全部子蓝图和覆盖矩阵也必须为 `approved`（已批准），且版本与 manifest 完全一致。
- 蓝图建立在已失效的需求、事实或设计之上时，交给 `hilp-reapproval`。
- 发现问题本质是设计并未真正收敛时，回交 `hilp-design-approval`。
