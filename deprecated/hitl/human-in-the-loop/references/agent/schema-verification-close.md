# Verification / Close Schema

通用头字段和禁止字段见 `schema-common.md`。

## execution/verification

记录验证命令、执行结果、输出摘要、未运行项、残余风险和关联 Plan / Runbook / unit。正式流程使用 `scripts/record_execution_evidence.py verification`，一次可记录多条 `commands[]`；`overall_result: pass` 时所有命令结果都必须为 `pass`。

## execution/close

记录实际变更文件、changed-files gate、验证结果、未运行项、scope compliance、残余风险和完成结论。正式流程使用 `scripts/record_execution_evidence.py close`，写入前必须满足：source Plan / Runbook 已 confirmed、verification 存在且 `overall_result: pass`、changed-files gate 通过。

固定结构：

```yaml
source_plan_or_runbook_ref: execution/plan@v1
verification_ref: execution/verification@v1
changed_files: []
changed_files_gate:
  result: pass
  blueprint_ref: planning/blueprint@v1
  source: changed-file|git
  checked_at: "..."
  violations: []
verification_result: pass
skipped_items: []
residual_risks: []
scope_compliance: pass
conclusion: completed|completed-with-risks
```
