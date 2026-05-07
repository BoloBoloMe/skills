# 实施蓝图与执行交接

实施蓝图把已批准设计转换成可执行计划，但还不开始执行。你审核时重点看：会改哪些文件、哪些文件绝对不改、每个执行单元如何验证、失败时停在哪里、是否有回退或重审条件。

批准蓝图只能使用明确命令：

```text
模板：批准蓝图：批准 phase-03/implementation-blueprint@vN；正式示例：批准蓝图：批准 phase-03/implementation-blueprint@v2
```

执行交接是规划层给执行层的出口记录。它不需要再次被“批准”，但必须完整说明执行范围、禁止越界项、停止条件和验证标准。执行层之后还会要求你确认具体 Runbook 或 Plan：

```text
模板：确认执行：确认执行 Runbook <path>；正式示例：确认执行：确认执行 Runbook docs/changes/sample/execution/agent/03-runbook.yaml.md
```

上一页：[需求事实与方案审批](03-requirements-and-design.md) ｜ 下一页：[变更重审与归档](05-reapproval-and-archive.md)

## 执行确认示例

HILP 只生成交接记录；HILE 会决定使用 Runbook 或 Plan。人类看到 HILE review-pack 后，可能使用：

- `模板：确认执行：确认执行 Runbook <path>；正式示例：确认执行：确认执行 Runbook docs/changes/sample/execution/agent/03-runbook.yaml.md`
- `模板：确认执行：确认执行 Plan <path>；正式示例：确认执行：确认执行 Plan docs/changes/sample/execution/agent/03-plan.yaml.md`

确认命令里的 `<path>` 指向 HILE 生成并将执行的 canonical agent Plan/Runbook 文件，不是 review-pack 文件路径。

批准蓝图不等于确认执行。


## 模板占位不可直接复制

文档中的 `@vN`、`<path>`、`<change_slug>` 是模板占位。正式批准、蓝图批准或执行确认时，必须替换为具体版本或真实路径，例如 `@v3` 或 `docs/changes/example/execution/agent/03-runbook.yaml.md`。

## EU 与 HILE Plan/Runbook 的边界

在 HILP 阶段，审核员审查的是 execution unit 的目标、范围、允许/禁止文件、验证期望和停止条件；不要期待 EU 给出逐行 patch。具体目标符号、修改顺序、测试用例更新和 repo 观察应在 HILE 读取真实 repo 后，由 Plan 或 Runbook 呈现并确认。
