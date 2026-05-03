# Execution Plan Contract

## 适用时机

实施蓝图或执行交接需要把执行范围、单元顺序、依赖关系、文件边界、共享状态、验证资源和并行资格结构化交给 HILE 时使用。本契约由 HILP 生成和审批绑定，HILE 只能读取并复制到 Execution Runbook，不得在执行阶段补齐、改写或推断 contract 字段。

## 输入契约

生成 `execution_plan_contract` 前必须同时具备：

- `stage-3/design-choice@vN [state=approved｜中文状态=已批准]`。
- `stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]`。
- 已确定的执行范围、执行模式、执行单元、依赖顺序、允许文件、禁止文件、文件域、共享状态、验证资源、must_haves、验证承诺和停止条件。

任一字段无法从已批准设计或已批准蓝图确定时，不得生成执行交接，不得把缺口交给 HILE。

## 人类审核视图与机器执行契约

实施蓝图必须区分人类审核视图与机器执行契约。人类审核视图必须清爽、精炼，只展示执行拓扑摘要、波次、关键依赖、并行判断和审核关注点，不得要求审核者阅读完整 YAML 才能理解执行顺序。完整 `execution_plan_contract` 应放入附录、折叠区或独立 contract 资产，且仍必须完整保留 `units[].order`、`units[].depends_on`、`parallel_group`、`parallel_eligible`、文件边界、验证资源、上下文包和停止条件。执行交接只能摘录已批准机器执行契约，不得从人类审核摘要中推断、补齐或改写执行顺序与依赖关系。

## 顶层数据形状

`execution_plan_contract` 是 HILP 交给 HILE 的唯一结构化执行 contract 顶层。`execution_unit` 只作为 `units[]` 内的单元字段来源，不再作为顶层 contract。

```yaml
execution_plan_contract:
  execution_scope: whole-package
  execution_mode: user-selected-subagent-or-serial
  parallelization:
    strategy: hilp-defined-groups
    user_opt_in_required: true
    conflict_policy: no-shared-files-no-shared-state-no-verification-resource-conflict
    integration_required_after_parallel_group: true
  units:
    - unit_id: EU-001
      title: HILP 引入带并行资格的 Execution Plan Contract schema
      order: 1
      depends_on: []
      parallel_group: PG-HILP-001
      parallel_eligible: false
      allowed_files:
        - human-in-loop-planning/references/execution-plan-contract.md
      forbidden_files:
        - human-in-loop-execution/**
      file_domain:
        - hilp-contract-schema
      shared_state:
        - planning-reference-index
      verification_resources:
        - static-grep
      context_packet:
        approved_design_ref: stage-3/design-choice@vN [state=approved｜中文状态=已批准]
        approved_blueprint_ref: stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]
        handoff_ref: stage-6/execution-handoff@vK
        required_sections:
          - Execution Plan Contract
        relevant_decisions:
          - HILP 负责上游 contract 和并行资格
        prior_summaries: []
        explicitly_ignore:
          - runtime scheduler
      must_haves:
        truths:
          - HILP contract 顶层必须是 execution_plan_contract，并包含 parallelization。
        artifacts:
          - human-in-loop-planning/references/execution-plan-contract.md
        key_links:
          - grep parallelization 证明并行资格字段已落盘。
      verification:
        static_checks:
          - grep -n 'execution_plan_contract' human-in-loop-planning/references/execution-plan-contract.md
        commands: []
        human_checks:
          - 人工确认 execution-unit-schema 不再作为顶层 contract。
      stop_conditions:
        - 需要新增 runtime、CLI 或脚本。
        - 并行资格需要 HILE 执行阶段补齐。
      completion_outputs:
        - unit_summary
        - execution_ledger_update
```

## 字段规则

- `execution_scope`：只能填写已批准蓝图确定的整包、发布波次或 manifest 中已定义切片集合。
- `execution_mode`：只能填写已批准蓝图确定的执行模式；用户选择子代理或串行时，HILE 只在 runbook 中记录当前选择，不改变 contract。
- `parallelization.strategy`：固定表达并行资格来源。当前支持 `hilp-defined-groups`，表示并行分组由 HILP 定义。
- `parallelization.user_opt_in_required`：为 `true` 时，HILE 只有在用户明确选择子代理模式后才允许启用并行调度。
- `parallelization.conflict_policy`：固定为无共享文件、无共享状态、无验证资源冲突才允许并行。
- `parallelization.integration_required_after_parallel_group`：为 `true` 时，每个并行组返回后必须统一做冲突检查、集成验证、spot check、unit summary 和 execution ledger 更新。
- `units[].order`：由 HILP 固定，HILE 不得改变。
- `units[].depends_on`：由 HILP 固定，HILE 不得推断或新增依赖。
- `units[].parallel_group`：由 HILP 固定；缺失时该单元不得并行。
- `units[].parallel_eligible`：由 HILP 固定；`false` 时即使同组无冲突也必须串行。
- `units[].allowed_files` 与 `units[].forbidden_files`：执行层的文件边界；HILE 不得扩大 allowed_files 或绕过 forbidden_files。
- `units[].file_domain`：用于并行冲突检查；同一并行组内共享文件域时不得并行。
- `units[].shared_state`：用于并行冲突检查；同一并行组内共享状态时不得并行。
- `units[].verification_resources`：用于并行冲突检查；验证资源互斥时不得并行。
- `units[].context_packet`、`must_haves`、`verification`、`stop_conditions` 与 `completion_outputs`：由已批准蓝图确定，执行交接只摘录，HILE 只复制。

## HILE 只读边界

HILE 可以把 `execution_plan_contract` 复制为 `execution_runbook`，并根据用户选择记录当前串行或子代理执行模式。HILE 不得：

- 新增、删除或重排 unit。
- 改变 `order`、`depends_on`、`parallel_group`、`parallel_eligible`、`allowed_files`、`forbidden_files`、`file_domain`、`shared_state`、`verification_resources`、`must_haves`、`verification` 或 `stop_conditions`。
- 将缺失并行字段解释为可并行。
- 在执行阶段补做并行资格、文件域、共享状态或验证资源判断。

## 检查清单

- [ ] 顶层字段为 `execution_plan_contract`。
- [ ] 包含 `parallelization`，且策略、用户选择门、冲突策略和并行后集成要求已固定。
- [ ] 每个 unit 均包含 `order`、`depends_on`、`parallel_group`、`parallel_eligible`、`allowed_files`、`forbidden_files`、`file_domain`、`shared_state` 和 `verification_resources`。
- [ ] 每个 unit 均包含 context_packet、must_haves、verification、stop_conditions 和 completion_outputs。
- [ ] 任一字段缺失时未交给 HILE 补齐。
- [ ] 未引入 runtime、CLI、auto loop、dashboard、provider routing、Git worktree 自动化或 runtime scheduler。
