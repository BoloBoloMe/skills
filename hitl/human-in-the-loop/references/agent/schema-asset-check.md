# Asset Check Schema

通用头字段和禁止字段见 `schema-common.md`。

## checks/asset-check

`checks/asset-check@vN` 记录一次机械校验输入、目标 hash、结果、失败路由或下一步。它不是人工批准点，也不能替代固定人工批准/确认命令。

生成记录必须使用：

```bash
scripts/validate_asset_check.py --manifest <manifest.yaml> --target-ref <asset_ref> --record-ref checks/asset-check@vN
```

批准前必须使用 pre-approval 模式：

```bash
scripts/validate_asset_check.py --manifest <manifest.yaml> --pre-approval --target-ref <asset_ref> --record-ref checks/asset-check@vN
```

## 固定最小字段

```yaml
asset_ref: checks/asset-check@v1
artifact: asset-check
schema_version: "0.0.1"
check_mode: pre-approval # 或 final
target_ref: planning/implementation-package@v1
target_path: agent/implementation-package.v1.yaml
target_sha256: <sha256>
target_lifecycle_state: ready-for-approval
reviewer_view_hashes:
  path: human-view.html
  html_sha256: <sha256>
  payload_sha256: <sha256>
workspace: <final 模式必填>
result: pass # 或 fail
errors: []
checked_at: <UTC>
validator:
  script: validate_asset_check.py
  options:
    pre_approval: true
next_action: <下一步或失败路由>
```

说明：字段名使用 `reviewer_view_hashes`，避免违反 `schema-common.md` 对 agent asset 顶层 `human_view` 字段的禁令。

## 门禁使用规则

- `transition_manifest.py record-decision --decision-type approval` 只接受 `completed/pass/pre-approval` 的 latest asset-check，且必须绑定当前批准目标、目标路径、目标 sha256 和目标 lifecycle state。
- `scaffold_execution_plan.py` 只接受 `completed/pass/final` 的 latest asset-check，且必须绑定当前 implementation-package 和 workspace。
- `blocked/fail` 记录只保留失败审计；不得用于批准或生成 Plan/Runbook。后续通过时，必须先显式归档旧 check，再记录新版本。
- 同一时间只能有一个 current `checks/asset-check@vN`。新 check 前如已有 current check，先用 `archive_asset.py` 显式归档。
