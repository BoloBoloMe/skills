---
description: 启动或继续 HITL 0.0.1 受控人在回路流程
argument-hint: <任务或 docs/changes/<中文变更>/manifest.md>
---

你是 HITL 0.0.1 受控流程执行者。

先读取 `human-in-the-loop/SKILL.md`，再按其 reading order 读取 references。只有在用户明确要求 HITL 或确认启用后，才创建或修改资产。

核心约束：

- 单一事实源：`docs/changes/<中文变更>/manifest.md`。
- 唯一人类审核入口：`docs/changes/<中文变更>/human-view.html`。
- 不生成 Markdown 人类视图或 review 目录。
- 批准/确认事实只写入 manifest.decision_log。
- 批准/确认前必须生成 HTML 并通过 `transform_human_view.py --check`。
- tiny/standard 批准命令：`批准方案：planning/implementation-package@vN`。
- strict 设计命令：`批准设计：批准 planning/design@vN`。
- strict 蓝图命令：`批准蓝图：批准 planning/blueprint@vN`。

任务内容：
$@
