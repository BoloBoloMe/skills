# 批准命令速查

请使用精确命令，避免把“批准”和“继续执行”混在一起。

```text
模板：批准设计：批准 phase-02/design-choice@vN；正式示例：批准设计：批准 phase-02/design-choice@v3
模板：批准蓝图：批准 phase-03/implementation-blueprint@vN；正式示例：批准蓝图：批准 phase-03/implementation-blueprint@v2
模板：确认执行：确认执行 Runbook <path>；正式示例：确认执行：确认执行 Runbook docs/changes/sample/execution/agent/03-runbook.yaml.md
模板：确认执行：确认执行 Plan <path>；正式示例：确认执行：确认执行 Plan docs/changes/sample/execution/agent/03-plan.yaml.md
模板：批准重审：批准 phase-04/reapproval@vN；正式示例：批准重审：批准 phase-04/reapproval@v2
模板：批准重审：重做设计 phase-04/reapproval@vN；正式示例：批准重审：重做设计 phase-04/reapproval@v2
模板：批准重审：重做蓝图 phase-04/reapproval@vN；正式示例：批准重审：重做蓝图 phase-04/reapproval@v2
模板：批准重审：重做交接 phase-04/reapproval@vN；正式示例：批准重审：重做交接 phase-04/reapproval@v2
模板：批准重审：阻断执行 phase-04/reapproval@vN；正式示例：批准重审：阻断执行 phase-04/reapproval@v2
模板：批准重审：维持原批准 phase-04/reapproval@vN；正式示例：批准重审：维持原批准 phase-04/reapproval@v2
```

如果审核包里给出的 asset_ref 或路径与你想批准的不一致，不要批准；要求 agent 先修正审核包。

上一页：[变更重审与归档](05-reapproval-and-archive.md) ｜ 回到：[从这里开始](00-start.md)


## 模板占位不可直接复制

文档中的 `@vN`、`<path>`、`<change_slug>` 是模板占位。正式批准、蓝图批准或执行确认时，必须替换为具体版本或真实路径，例如 `@v3` 或 `docs/changes/example/execution/agent/03-runbook.yaml.md`。
