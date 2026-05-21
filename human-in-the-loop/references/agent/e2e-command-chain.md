# HITL 端到端命令链示例

以下命令展示 standard tier 从 init 到 close 的标准路径。示例中的 YAML 内容文件需按对应 schema 预先准备；所有 ref 使用实际版本替换。

```bash
# 1. 初始化
python human-in-the-loop/scripts/init_hitl_package.py 示例变更 --root docs/changes --tier standard
MANIFEST=docs/changes/示例变更/manifest.yaml

# 2. 写 facts；design/blueprint 若 gate 未关闭只能先写 draft
python human-in-the-loop/scripts/write_agent_asset.py --manifest "$MANIFEST" --asset-ref planning/facts@v1 --artifact facts --state completed --role content-asset --stdin < facts.yaml
python human-in-the-loop/scripts/write_agent_asset.py --manifest "$MANIFEST" --asset-ref planning/design@v1 --artifact design --state draft --role content-asset --stdin < design.yaml
python human-in-the-loop/scripts/write_agent_asset.py --manifest "$MANIFEST" --asset-ref planning/blueprint@v1 --artifact blueprint --state draft --role content-asset --stdin < blueprint.yaml

# 3. 关闭并校验 planning gates，然后推进资产状态
python human-in-the-loop/scripts/transition_manifest.py close-gate --manifest "$MANIFEST" --gate pre_design --target planning/design@v1 --command "关闭盘问: pre_design planning/design@v1" --resolution-file pre-design-resolution.yaml
python human-in-the-loop/scripts/transition_manifest.py mark-asset --manifest "$MANIFEST" --asset-ref planning/design@v1 --state completed
python human-in-the-loop/scripts/transition_manifest.py close-gate --manifest "$MANIFEST" --gate pre_blueprint --target planning/blueprint@v1 --command "关闭盘问: pre_blueprint planning/blueprint@v1" --resolution-file pre-blueprint-resolution.yaml
python human-in-the-loop/scripts/transition_manifest.py mark-asset --manifest "$MANIFEST" --asset-ref planning/blueprint@v1 --state completed

# 4. 组合 implementation-package
python human-in-the-loop/scripts/compose_implementation_package.py --manifest "$MANIFEST" --asset-ref planning/implementation-package@v1 --facts planning/facts@v1 --design planning/design@v1 --blueprint planning/blueprint@v1 --content-file package-content.yaml

# 5. 批准前 asset-check 记录与固定批准命令
python human-in-the-loop/scripts/validate_asset_check.py --manifest "$MANIFEST" --pre-approval --target-ref planning/implementation-package@v1 --record-ref checks/asset-check@v1
python human-in-the-loop/scripts/transition_manifest.py record-decision --manifest "$MANIFEST" --decision-type approval --asset-ref planning/implementation-package@v1 --command "批准方案: planning/implementation-package@v1"

# 6. 归档 pre-approval check，记录 final check
python human-in-the-loop/scripts/archive_asset.py --manifest "$MANIFEST" --asset-ref checks/asset-check@v1 --state superseded
python human-in-the-loop/scripts/validate_asset_check.py --manifest "$MANIFEST" --target-ref planning/implementation-package@v1 --workspace . --record-ref checks/asset-check@v2

# 7. 关闭 pre_execution_plan gate，生成并确认 Plan
python human-in-the-loop/scripts/transition_manifest.py close-gate --manifest "$MANIFEST" --gate pre_execution_plan --target execution/plan@v1 --command "关闭盘问: pre_execution_plan execution/plan@v1" --resolution-file pre-execution-resolution.yaml
python human-in-the-loop/scripts/scaffold_execution_plan.py --manifest "$MANIFEST" --asset-ref execution/plan@v1 --implementation-package-ref planning/implementation-package@v1 --planned-file planned-files.txt --repo-root . --content-file plan-content.yaml
python human-in-the-loop/scripts/transition_manifest.py record-decision --manifest "$MANIFEST" --decision-type execution-confirmation --asset-ref execution/plan@v1 --command "执行计划: execution/plan@v1"

# 8. 执行后记录 verification 与 close
python human-in-the-loop/scripts/record_execution_evidence.py verification --manifest "$MANIFEST" --asset-ref execution/verification@v1 --source execution/plan@v1 --commands-file verification-commands.yaml --overall-result pass
python human-in-the-loop/scripts/record_execution_evidence.py close --manifest "$MANIFEST" --asset-ref execution/close@v1 --source execution/plan@v1 --verification-ref execution/verification@v1 --changed-file changed-files.txt --conclusion completed
```

关键约束：已有 current `checks/asset-check@vN` 时，新 check 前必须显式归档旧记录；blocked/fail check 不能用于批准或生成 Plan/Runbook。
