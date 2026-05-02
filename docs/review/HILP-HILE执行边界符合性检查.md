# HILP / HILE 执行边界符合性检查

## 结论

总体判断：**部分符合，但没有完全符合用户期望的边界**。

当前仓库已经把大部分字段前移到 HILP 侧，并且 HILE 侧也有“不得补蓝图、不得扩大 allowed_files、不得改变验证口径”的约束；但命名和职责边界仍停留在“执行计划 / execution_unit”模型，没有明确形成：

- HILP：`Execution Plan Contract`，作为执行交接阶段的上游契约。
- HILE：`Execution Runbook`，作为执行实例 / 运行手册，而不是规划。

因此，实际内容**接近方向，但仍会让未来 agent 把 HILE 生成物理解为执行计划甚至轻量规划**。

## Critical

无。当前内容没有发现会直接导致越界实现或自动 runtime 化的硬错误。

## Important

### 1. HILP 侧没有明确命名和输出 `Execution Plan Contract`

证据：

- `rg "Execution Plan Contract|execution_plan_contract" human-in-loop-planning human-in-loop-execution` 无命中。
- `human-in-loop-planning/references/execution-handoff.md:90` 仍使用 `Execution Units 交接包`。
- `human-in-loop-planning/references/execution-unit-schema.md:25` 的 YAML 顶层仍是 `execution_unit:`，不是 `execution_plan_contract:`。

影响：

当前 HILP 侧能表达 unit 契约，但没有把它包装成执行交接阶段的整体上游契约。`execution_scope`、`execution_mode`、`units`、`completion_outputs` 这些 contract 级字段没有形成一个统一结构。

### 2. Contract 字段不完整，缺少 `forbidden_files` 和 `completion_outputs`

证据：

- `rg "forbidden_files|forbidden files|forbidden" human-in-loop-planning human-in-loop-execution` 无命中。
- `human-in-loop-planning/references/execution-unit-schema.md:36-43` 只包含 `allowed_files`、`dependencies`、`must_haves`、`verification`、`stop_conditions` 等。
- `completion_outputs` 未作为字段出现。

影响：

当前只能约束允许修改文件，不能显式表达“禁止文件”和“完成后必须产出 unit_summary / execution_ledger_update”。这会削弱 HILP 对执行实例边界的上游约束力。

### 3. HILE 侧仍叫“执行计划”，没有转成 `Execution Runbook`

证据：

- `human-in-loop-execution/references/writing-plans.md:1` 标题是 `执行计划编写`。
- `human-in-loop-execution/SKILL.md:34-35` 阶段仍是 `执行计划阶段`、`执行计划确认阶段`。
- `human-in-loop-execution/references/writing-plans.md:31-35` 说明 HILE 生成“计划”，并“按 execution_unit 逐单元拆任务”。
- `rg "Execution Runbook|runbook|运行手册" human-in-loop-planning human-in-loop-execution` 无命中。

影响：

这与用户期望的“不要再理解为规划，而是运行手册 / 执行实例”不一致。虽然规则里限制了不得新增方案选择和扩大范围，但命名仍容易诱导 agent 把 HILE 输出当作下游规划。

### 4. HILE 的允许动作未被收窄为“读取 contract → 核对工作区 → 转步骤 → 列命令 → 保存 runbook → 停止”

证据：

- `human-in-loop-execution/references/writing-plans.md:35` 要求“每个任务的每步目标 2-5 分钟，包含精确文件路径、失败测试或验证命令、预期输出、最小实现、回归验证、提交或变更记录”。
- 当前没有明确说 HILE 只能从 `execution_plan_contract` 派生 runbook，不得生成 contract 之外的信息。

影响：

当前规则比用户期望更宽。它虽然禁止新增方案选择，但仍允许 HILE 在“执行计划”中组织较多实现步骤和验证细节，边界不如 `Execution Runbook` 清晰。

## Minor

### 1. `dependencies` 与用户给出的 `depends_on` 字段不一致

证据：

- `human-in-loop-planning/references/execution-unit-schema.md:37` 使用 `dependencies: []`。
- 用户期望字段为 `depends_on: []`。

影响：

不是本质错误，但会影响契约稳定性和跨文档一致性。

### 2. `verification` 当前没有分层为 `static_checks / commands / human_checks`

证据：

- `human-in-loop-planning/references/execution-unit-schema.md:39-42` 当前为 `commands`、`expected_exit_codes`、`expected_output_summary`。
- `human-in-loop-planning/references/execution-handoff.md:107-108` 有验证梯度概念，但没有落到 unit YAML 字段。

影响：

验证梯度已存在于说明文字中，但未成为稳定 contract 字段。

## 符合项

当前已有以下符合用户预期的部分：

1. HILP 已要求 unit 绑定已批准设计、已批准蓝图和有效 handoff。
   - `human-in-loop-planning/references/execution-unit-schema.md:9-18`
2. HILP 已要求 `allowed_files` 精确且执行层不得扩展。
   - `human-in-loop-planning/references/execution-unit-schema.md:52`
3. HILP 已要求 verification 不得留给执行者临场定义。
   - `human-in-loop-planning/references/execution-unit-schema.md:64`
4. HILE 已禁止扩大 `allowed_files`。
   - `human-in-loop-execution/references/execution-unit-intake.md:40`
5. HILE 已禁止 intake 变成蓝图补齐或方案选择。
   - `human-in-loop-execution/references/execution-unit-intake.md:39`
6. HILE 已禁止自动连续执行全部 execution_unit。
   - `human-in-loop-execution/references/execution-unit-intake.md:42`

## 建议的最小修正方向

1. 在 `human-in-loop-planning/references/execution-handoff.md` 中新增或替换为 `Execution Plan Contract` 小节。
2. 在 `human-in-loop-planning/references/execution-unit-schema.md` 中把顶层结构改为 `execution_plan_contract`，包含 `execution_scope`、`execution_mode`、`units`。
3. 给 unit 增加 `order`、`depends_on`、`forbidden_files`、`completion_outputs`。
4. 把 `verification` 固定为 `static_checks`、`commands`、`human_checks`。
5. 在 HILE 中把 `writing-plans.md` 语义改为 `writing-runbooks.md` 或至少正文改称 `Execution Runbook`。
6. 明确 HILE 只允许：读取 contract、核对工作区、转操作步骤、列当前环境验证命令、保存 runbook、停止等待确认。
7. 明确 HILE 不得改变 unit 顺序、allowed_files、forbidden_files、must_haves、verification、stop_conditions。

## 最终判断

不完全符合。当前实现是“execution_unit + 执行计划”边界，已经有不少防越界规则；但用户提出的是更清晰的“上游 Execution Plan Contract / 下游 Execution Runbook”二分模型。要达到该预期，需要一次边界命名和契约字段的收窄修正。
