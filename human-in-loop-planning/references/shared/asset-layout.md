# 双视图资产布局

正式 HILP 资产保存到当前项目目录下：

```text
docs/changes/<change_slug>/planning/
  manifest.md
  _current/
    human-review.md
    agent-directory.md
    latest-approved.md
  human/
    00-start.md
    01-requirements-and-facts.md
    02-design-decision.md
    03-implementation-blueprint.md
    04-reapproval-log.md
    05-execution-handoff.md
    06-archive-summary.md
  agent/
    00-directory.md
    01-requirements-facts.yaml.md
    02-design-choice.yaml.md
    03-implementation-blueprint.yaml.md
    04-reapproval.yaml.md
    05-execution-handoff.yaml.md
    06-archive-index.yaml.md
  review-pack/
    phase-02-design-choice@vN-review.md
    phase-03-implementation-blueprint@vN-review.md
    phase-05-execution-handoff@vN-review.md
  audit/
    audit-trail.md
```

## 人类视图要求

- 使用自然语言说明“为什么、改什么、不改什么、风险是什么、如何批准”。
- 每份文档底部提供“上一页 / 下一页 / 回到目录”链接。
- 不把 `execution_plan_contract`、`allowed_files`、`parallel_group` 等字段作为正文主线；可用自然语言解释。

## Agent 视图要求

- 每份文件顶部包含 `asset_ref`、`phase_id`、`lifecycle_state`、`record_role`、`depends_on`、`invalidates`。
- `00-directory.md` 必须列出当前执行环节的最小必读文件。
- 结构化字段可用 YAML fenced block；字段名保持稳定。
- 不写给人类的铺垫性解释，避免过度读取。

## 同源一致性

两套视图必须来自同一事实集。若人类视图和 agent 视图冲突，立即阻塞下游推进并生成重审记录。manifest 中最新 `approved` 或 `closed-record` 的 agent 视图只能作为取证基准；不得据此自动继续执行。


## Strict audit trail

Strict mode must maintain `audit/audit-trail.md`. Record approvals, state transitions, script gates, re-review triggers, handoff creation, archive creation, and any validator block. The audit trail is not a substitute for manifest state; it is the chronological evidence log.
