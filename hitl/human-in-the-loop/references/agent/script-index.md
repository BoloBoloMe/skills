# HITL 脚本索引

除非脚本报错、需要调试或需要确认实现细节，不要读取脚本源码；优先按本索引或脚本 `--help` 调用。

## 资产包与资产

- `scripts/init_hitl_package.py`：初始化 `docs/changes/<中文变更>/`，创建 `manifest.yaml`、`agent/`、`agent/archive/`；初始化不得创建 `human-view.html`。
- `scripts/write_agent_asset.py`：写入或替换 agent YAML 资产，登记 registry，并刷新 `human-view.html` 与 `human-view@current`。
- `scripts/archive_asset.py`：把历史资产移动到 `agent/archive/`，更新 registry，并刷新 human-view。
- `scripts/transform_human_view.py`：生成或检查 `human-view.html`；任何批准或确认前必须运行 `--check`。

## gate、批准与状态转换

- `scripts/validate_interrogation_gate.py`：校验 `pre_design`、`pre_blueprint`、`pre_execution_plan` gate 是否可用于目标资产。
- `scripts/transition_manifest.py close-gate`：关闭盘问 gate，必须显式记录固定命令 `关闭盘问: <gate> <asset_ref>`。
- `scripts/transition_manifest.py record-decision`：记录固定批准或执行确认命令，只写入 `manifest.decision_log`。
- `scripts/validate_manifest.py`：校验 manifest 结构、registry、current pointers、human-view registry 等基础一致性。

## 规划与执行资产

- `scripts/compose_implementation_package.py`：生成 `planning/implementation-package@vN`，绑定 facts/design/blueprint 的 path 与 sha256。
- `scripts/validate_planning_assets.py`：校验 planning assets 的基础结构和门禁条件。
- `scripts/validate_asset_check.py`：校验并可记录 `checks/asset-check@vN`；批准前使用 `--pre-approval --target-ref <asset_ref> --record-ref checks/asset-check@vN`，生成 Plan/Runbook 前使用 final 模式 `--target-ref <implementation-package-ref> --workspace <repo> --record-ref checks/asset-check@vN`。
- `scripts/scaffold_execution_plan.py`：基于 blueprint、implementation-package 和 repo context 生成 Plan / Runbook 机械骨架；要求已有匹配的 completed/pass/final asset-check，并即时重跑最终 asset-check 与 pre-execution gate。
- `scripts/validate_plan_or_runbook.py`：校验 Plan / Runbook 的结构、trace、planned files、source-level intent 与 interrogation refs。

## 端到端示例

- `references/agent/e2e-command-chain.md`：从 init 到 close 的标准命令链示例。

## 文件范围与执行证据

- `scripts/check_allowed_files.py`：执行前校验 planned files，完成前校验 changed files；支持 snapshot 排除执行前既有变更。
- `scripts/write_verification_record.py`：写入基础 verification 记录。
- `scripts/record_execution_evidence.py verification|close`：正式写入 verification 与 close；close 前必须通过 changed-files gate。
