# Manifest 与版本规则

`manifest.yaml` 是 HITL 0.0.1 的唯一业务事实源，文件内容直接是 HITL manifest YAML mapping。脚本修改 manifest 后必须刷新 `human-view.html`；优先使用 `scripts/transition_manifest.py` 执行 gate、decision、workflow 与安全状态转换。

## 普通业务资产 ref

业务资产使用语义路径和版本号：

```text
planning/facts@v1
planning/design@v1
planning/blueprint@v1
planning/implementation-package@v1
planning/reassessment@v1
checks/asset-check@v1
execution/plan@v1
execution/runbook@v1
execution/ledger@v1
execution/unit-summary@v1
execution/verification@v1
execution/close@v1
```

## 盘问门禁

manifest 必须包含 `interrogation_gates.pre_design`、`pre_blueprint`、`pre_execution_plan`。写 `planning/design@vN`、`planning/blueprint@vN`、`execution/plan@vN` / `execution/runbook@vN` 前，目标 gate 必须满足：`status: closed`、`target_asset` 精确匹配、`blocking_unknowns: []`、`evidence` 非空、`closed_at` 非空。

`pre_execution_plan.resolution_items[]` 必须额外记录结构化源码级盘问证据：`resolution_id`、`unit_id`、`step_id`、`dependency_path`。`resolution_id` 固定格式为 `PEP-EU-001-S01-R001`，并被 Plan / Runbook 的 `source_level_change_intent[].interrogation_refs` 引用。

## human-view 特例

`human-view@current` 是唯一允许的 non-versioned current ref。

它必须满足：

- `asset_kind: derived-human-view`
- `record_role: derived-human-view`
- `lifecycle_state: completed` 或 `blocked`
- `path: human-view.html`
- 包含 `html_sha256`、`payload_sha256`、`generated_from`、`generated_at`

它不进入普通业务资产版本链，不得变成 `human-view@vN`，也不得被 `transform_human_view.py` 当作 YAML agent asset 解析。

## asset_kind 与物理路径

registry 至少区分：

- `agent-asset`：`agent/<artifact>.vN.yaml` 或 `agent/archive/<artifact>.vN.yaml` 下的 YAML agent 资产。
- `derived-human-view`：当前 HTML 人类视图。

`asset_ref` 保持 planning / checks / execution 语义；物理位置只看 `manifest.asset_registry[].path`。历史状态为 `superseded`、`retired`、`failed`、`closed`，必须位于 `agent/archive/`；其他状态必须位于 `agent/`。同一 artifact 只能有一个当前有效版本。

## hash 规则

- agent asset 使用 `sha256`。
- HTML 使用 `html_sha256`。
- HTML 内嵌 payload 使用 `payload_sha256`。
- payload canonical normalization 必须清空当前 `human-view@current.html_sha256` 与 `human-view@current.payload_sha256`，避免自引用 hash。
- 当前 human-view 的最终 hash 不得内嵌到 HTML 自身，只保存在 manifest。
