# Task for reviewer

审核以下三个文件的修改是否与设计文档一致. 只读, 不改任何文件.

**设计文档 (权威来源)**:
- /var/mnt/DATA/Workspace/skills/docs/changes/blinders/DECISIONS.md — 决策账本 (D001-D017)
- /var/mnt/DATA/Workspace/skills/docs/changes/blinders/CONTRACT.md — 执行契约

**被审核文件**:
- /var/mnt/DATA/Workspace/skills/workflow/to-issues/references/step-gen-guide.md — 步骤生成指引
- /var/mnt/DATA/Workspace/skills/workflow/run-afk-workflow/SKILL.md — AFK 控制器
- /var/mnt/DATA/Workspace/skills/workflow/to-issues/SKILL.md — to-issues 流程

**检查项**:

1. step-gen-guide 是否定义了 6 步 (D011), 且步骤职责与 D011 一致?
2. step-gen-guide 是否使用了目录角色名而非绝对路径/占位符 (D015)?
3. run-afk-workflow/SKILL.md 执行循环是否实现了 `ISSUE-KEY:NN` 格式和 `done` sentinel (D013)?
4. run-afk-workflow/SKILL.md 步骤文件位置是否描述为 `afk-running/` 根 + `ISSUE-*/` 产物目录 (D012)?
5. run-afk-workflow/SKILL.md 是否包含路径推断约定 (D015)?
6. run-afk-workflow/SKILL.md 盲视约束是否保留 (D001): 不读其他 step-NN.md, 不知全局?
7. to-issues/SKILL.md 步骤 6a 是否描述为"一次性全局生成"而非"per-issue 生成" (D014)?
8. to-issues/SKILL.md 步骤 6a `_current.md` 初始值是否为 `ISSUE-01:01` (D013)?
9. 步骤文件数量: step-gen-guide 是否只有 6 步 (非 15), to-issues 6a 是否说生成 7 个文件 (非 16)?
10. step-06 (收尾) 是否包含多 issue 扫描切换逻辑 (D017)?

逐项报告: 一致/不一致/部分一致. 不一致时指出具体偏差.

## Acceptance Contract
Acceptance level: attested
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Return concrete findings with file paths and severity when applicable

Required evidence: review-findings, residual-risks

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```