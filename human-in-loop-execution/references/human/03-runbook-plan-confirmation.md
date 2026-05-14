# Runbook / Plan 审核与确认

Runbook 或 Plan 应回答：会改哪些文件，哪些文件不改，步骤怎么走，源码级修改意图是什么，失败时停在哪里，验证通过的标准是什么。

确认执行只能使用明确命令：

```text
模板：确认执行：确认执行 Runbook <path>；正式示例：确认执行：确认执行 Runbook docs/changes/sample/execution/agent/03-runbook.yaml.md
模板：确认执行：确认执行 Plan <path>；正式示例：确认执行：确认执行 Plan docs/changes/sample/execution/agent/03-plan.yaml.md
```

确认命令里的 `<path>` 指向被执行的 canonical agent Plan/Runbook 文件；在生成的 review-pack 中应等于 `review_target.agent_view`，不是 review-pack 文件路径。

这条命令只确认当前执行文件，不批准设计或蓝图。如果上游批准缺失，执行必须停止。

上一页：[执行分级](02-execution-tiers.md) ｜ 下一页：[失败、重审与停止](04-failure-and-reapproval.md)


## 模板占位不可直接复制

文档中的 `@vN`、`<path>`、`<change_slug>` 是模板占位。正式批准、蓝图批准或执行确认时，必须替换为具体版本或真实路径，例如 `@v3` 或 `docs/changes/example/execution/agent/03-runbook.yaml.md`。

## 审核重点：repo-aware 具体计划

确认 Plan/Runbook 时，不要只看 HILP EU 的一句目标。应检查 HILE 是否已经读取真实 repo，并列出目标文件是否存在、相关符号/anchor、具体修改顺序、源码级修改意图、每步验证、风险检查、停止条件、planned-files gate 结果，以及固定确认命令。standard 必须确认 Plan；strict 必须确认 Runbook。源码级修改意图应说明每个 planned file 将影响哪些类、函数、枚举、字段、配置键、路由、测试或其他稳定 anchor；如果只有文件名而没有符号级意图，应视为审核信息不足。


## Strict Runbook 的人类审核版

strict 执行不能只让审核员阅读 `agent/03-runbook.yaml.md`。生成 strict Runbook 时，必须同步生成 `human/02-strict-runbook.md`，并把它作为 runbook 的主要人类视图。源码级修改意图必须放在每个 execution unit 的详细 Runbook 内，紧跟计划步骤；不能做成独立的全局“源码级修改意图”章节。确认页可以保留简短摘要，但必须链接到完整人类版 Runbook。完整结构和覆盖要求见 [HILE Strict Runbook（人类审核版）](06-strict-runbook.md)。
