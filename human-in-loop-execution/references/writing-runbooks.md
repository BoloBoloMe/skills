# Execution Runbook 编写

## 适用时机

HILP 执行交接包含 `execution_plan_contract` 时使用。本规则把已批准 contract 机械复制为 HILE 可执行的 `execution_runbook`，不重新规划、不补齐字段、不改变并行资格。runbook 不是规划资产，保存后必须停止，等待用户明确确认当前 runbook 文件。

## 输入契约

必须提供：

- HILP design asset_ref：`stage-3/design-choice@vN [state=approved｜中文状态=已批准]`。
- HILP blueprint asset_ref：`stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]`。
- HILP execution handoff asset_ref：`stage-6/execution-handoff@vK [state=<state>｜中文状态=<state_label>]`。
- `execution_plan_contract`，且包含 `execution_scope`、`execution_mode`、`parallelization` 和 `units`。
- 当前工作区、禁止越界项、停止并回退条件。
- 用户选择模式：`serial` 或 `subagent`；用户未选择时按执行交接默认值写入 `serial`。

## 输出路径

runbook 保存到：

```text
docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>-runbook.md
```

## 固定 runbook 头

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
执行确认状态: waiting-for-user-confirmation
当前工作区:
用户选择模式:
禁止越界项:
停止并回退条件:
```

## 数据形状

```yaml
execution_runbook:
  source_contract_ref: stage-6/execution-handoff@vK#execution_plan_contract
  workspace: D:/Workspace/skills
  confirmation_state: waiting-for-user-confirmation
  user_selected_mode: serial
  scheduling:
    source: execution_plan_contract.parallelization
    strategy: hilp-defined-groups
    user_opt_in_required: true
    conflict_policy: no-shared-files-no-shared-state-no-verification-resource-conflict
    integration_required_after_parallel_group: true
    serial_units:
      - EU-001
    parallel_groups: []
    contract_parallel_groups:
      - group_id: PG-001
        units:
          - EU-001
        active_in_current_mode: false
    conflict_checks:
      file_domain: pass
      shared_state: pass
      verification_resources: pass
  units:
    - unit_id: EU-001
      copied_order: 1
      copied_depends_on: []
      copied_parallel_group: PG-001
      copied_parallel_eligible: false
      copied_allowed_files: []
      copied_forbidden_files: []
      copied_file_domain: []
      copied_shared_state: []
      copied_verification_resources: []
      copied_must_haves: {}
      copied_verification: {}
      operation_steps: []
      runnable_verification_commands: []
      human_checks: []
      copied_stop_conditions: []
      completion_outputs:
        - unit_summary
        - execution_ledger_update
  post_parallel_group_checks:
    - conflict_check
    - integration_verification
    - spot_check
    - unit_summary
    - execution_ledger_update
```

## 编写规则

1. 读取执行交接中的 `execution_plan_contract`。
2. 核对 contract 顶层字段和每个 unit 调度字段均存在；缺字段时停止，不得补写。
3. 逐字段复制 `order`、`depends_on`、`parallel_group`、`parallel_eligible`、`allowed_files`、`forbidden_files`、`file_domain`、`shared_state`、`verification_resources`、`must_haves`、`verification`、`stop_conditions` 和 `completion_outputs`。
4. `user_selected_mode=serial` 时，`serial_units` 按 `copied_order` 与 `copied_depends_on` 排列，`parallel_groups` 写空列表，`contract_parallel_groups` 只作为只读来源记录。
5. `user_selected_mode=subagent` 时，只能把 `copied_parallel_eligible=true`、依赖已满足且同组无 `file_domain`、`shared_state`、`verification_resources` 冲突的 unit 写入 `parallel_groups`。
6. `parallel_eligible=false`、缺少 `parallel_group`、共享文件域、共享状态或验证资源冲突的 unit 必须写入 `serial_units` 或标记阻断，不得并行。
7. 每个 unit 的操作步骤只能来自已批准蓝图和执行交接，不得新增文件范围、验证口径或停止条件。
8. 保存 runbook 后立即停止，等待用户明确确认当前 runbook 文件；不得修改目标文件、派发 subagent 或执行实现步骤。

## 禁止事项

- 不得把 runbook 当作规划资产审批。
- 不得让 HILE 更改 contract 字段。
- 不得让 HILE 新增、删除、重排或合并 unit。
- 不得把未标记 `parallel_eligible=true` 的 unit 并行调度。
- 不得在用户未选择子代理模式时启用 parallel_groups。
- 不得取消 runbook 确认门。

## 输出契约

输出已保存 runbook 路径、绑定的三类 HILP asset_ref、`user_selected_mode`、`serial_units`、`parallel_groups`、禁止越界项、自检结果和用户确认请求。若无法生成 runbook，输出缺失字段、为什么不能执行、应回到的 HILP 阶段。

## 检查清单

- [ ] runbook 绑定三类 HILP asset_ref。
- [ ] `execution_runbook.source_contract_ref` 指向当前 handoff 的 `execution_plan_contract`。
- [ ] `user_selected_mode` 已记录。
- [ ] `parallel_groups` 只包含用户选择子代理模式且 contract 标记可并行的 unit。
- [ ] `copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 和 `copied_verification_resources` 已逐字段复制。
- [ ] runbook 保存后停止等待用户确认。
