# HILE 人类审核视图：从这里开始

HILE 是执行层。它只在用户明确要求使用 HILE / human-in-loop execution / 本 Skill 后进入；普通实现、调试、测试、review 或 handoff 相关咨询不自动进入。进入后，它只执行 HILP 已批准并交接的工作，不重新做规划，也不扩大范围。

阅读顺序：

1. [入口检查](01-intake.md)
2. [执行分级](02-execution-tiers.md)
3. [Runbook / Plan 审核与确认](03-runbook-plan-confirmation.md)
4. [失败、重审与停止](04-failure-and-reapproval.md)
5. [验证与完成](05-verification-and-finish.md)

快速参考：[一页速查](99-canonical-summary.md)

下一页：[入口检查](01-intake.md)

## v2.24.1 审核辅助材料

- 执行前确认 runbook/plan：使用 [Runbook/Plan 确认检查表](checklists/runbook-confirmation-checklist.md)。
- 完成后审核交付：使用 [完成审核检查表](checklists/completion-review-checklist.md)。
- 失败后判断是否回到 HILP：使用 [失败取证审核检查表](checklists/failure-forensics-review-checklist.md)。
- 示例：[tiny flow](../examples/tiny-flow/README.md) 与 [strict runbook flow](../examples/strict-runbook-change/README.md)。

## 生成资产入口要求

正式执行包中的 `execution/human/00-start.md` 必须是具体变更的审核入口，不能是 “HILE Human Status Start” 这类占位文件。它至少要包含：change slug、来源 HILP manifest、来源 handoff、执行分级、HILE manifest、当前状态指针、阅读顺序、当前需要审核什么、固定确认命令说明和阻塞/回退判断。

strict 执行必须在人类入口或 Runbook 确认页链接到完整的 [HILE Strict Runbook（人类审核版）](06-strict-runbook.md) 生成规范；实际资产默认路径为 `execution/human/02-strict-runbook.md`。

## HILE 不是普通代码修改入口

HILE 只执行已经通过 HILP 规划、批准和交接的工作。没有已批准设计、已批准蓝图和有效 handoff 时，HILE 应该阻塞并回到 HILP，而不是临时帮用户补计划或直接改代码。

固定回应模板：

```text
HILE 只能执行已批准的 HILP handoff。当前请求没有提供 phase-05/execution-handoff@vN，也没有可机械验证的 approved design 和 approved blueprint，因此我不能启动正式 HILE 执行。

下一步应先用 HILP 生成并批准：
1. phase-02/design-choice@vN
2. phase-03/implementation-blueprint@vN
3. phase-05/execution-handoff@vN

拿到 handoff 和 workspace 后，再进入 HILE intake。
```


## 术语阅读约定

人类视图优先使用中文主名，并在首次出现时保留英文括注；agent schema 字段保持 canonical English。


## 审核员快速路径

从 [00-reviewer-decision-tree.md](00-reviewer-decision-tree.md) 开始判断本次应给出什么结论，然后只打开当前 review target 对应的检查表。
