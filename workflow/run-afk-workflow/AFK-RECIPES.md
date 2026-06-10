# AFK direct recipes

主路由见 [SKILL.md](SKILL.md). 运行步骤和恢复策略见 [AFK-RUNBOOK.md](AFK-RUNBOOK.md). 本文件只保存可复制 direct `subagent({...})` 模板.

## 公共约束

- 本仓库不维护 workflow chain JSON. 所有模板通过 direct `subagent({...})` 调用.
- writer/fix 使用 builtin `worker`. review 使用 builtin `reviewer`. scout 使用 builtin `scout`.
- 子代理 task 使用中文. schema key, 命令, JSON key, path placeholder 保持英文.
- 每个子代理 step 必须设置 `reads:false`, `progress:false`, `outputMode:"file-only"`.
- AFK 写入阶段必须设置 `chainDir:"<AFK_RUN_DIR>"`, `sessionDir:"<AFK_SESSION_DIR>"`, `context:"fresh"`.
- worker/fix 是硬 TDD 阶段. 修改生产代码前必须先新增或修改一个行为测试, 运行并记录 RED 失败, 再写最小实现到 GREEN, 必要时重构并复跑验证.
- worker/fix 不能静默绕过 TDD. 若缺少测试接缝, 测试文件不在 `allowed-files.txt`, 需求不可验证, 或验证环境不可满足, 必须停止并报告 blocker, 不得先改生产代码.
- worker/fix 运行验证前必须读取 `manifest.yaml` 的 `validation_profile`. 若指定 JDK, Maven 或命令, 必须使用该 profile. 若环境不可满足, 报告 blocker, 不把错误环境下的失败当作代码失败证据.
- worker/fix 最终回复必须包含可解析的 `acceptance-report` fenced block, 且包含 TDD 循环证据. 不要只写普通 Markdown artifact.
- 不写仓库根 `progress.md`. 不 stage 文件.

## context-scout

```js
subagent({
  chain: [
    {
      agent: "scout",
      as: "contextFacts",
      phase: "Recon",
      label: "快速代码事实",
      skill: "zoom-out",
      reads: false,
      progress: false,
      output: "context-scout/context-facts.md",
      outputMode: "file-only",
      task: "为以下任务做快速只读代码库探索: <TASK>. 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件. 只允许写指定 output artifact. 不制定需求, 不制定方案, 不写 PRD, 不拆议题, 不给验收标准定稿, 不判断是否执行, 不做产品/API/架构/范围决策. 目标 25 次以内工具调用, 上限 30 次. 最多精读 12 个核心文件. 输出 10 行以内事实, 相关文件, 既有行为, 约束风险, 验证线索和未知项. 每个事实必须带路径, 命令输出线索, 或明确标为推断."
    }
  ],
  cwd: "<repo>",
  context: "fresh",
  chainDir: "<RUN_DIR>",
  sessionDir: "<SESSION_DIR>",
  clarify: false,
  timeoutMs: 300000
})
```

## implement-only

```js
subagent({
  chain: [
    {
      agent: "worker",
      phase: "Implementation",
      label: "实现已批准 milestone",
      as: "implementation",
      reads: false,
      progress: false,
      output: "worker-result.md",
      outputMode: "file-only",
      skill: "tdd",
      task: "AFK_RUN_DIR=<AFK_RUN_DIR>. 读取 manifest.yaml, doc-pointers.md, allowed-files.txt, 目标 issue 全文, PLAN 对应章节和 PRD 必要章节. 运行验证前先读取 manifest.yaml 的 validation_profile. 若指定 JDK, Maven 或命令, 必须使用该 profile. 若验证环境无法满足, 报告 blocker, 不把其他 JDK 或错误环境下的失败作为代码失败证据. 只实现本次已批准 milestone. 你是当前工作树唯一写入者. 首次编辑前写 worker-preflight.md 和 worker-plan.md, 其中必须列出第一个行为测试, RED 命令, GREEN 命令, 以及允许修改的测试文件. 硬 TDD: 修改生产代码前必须先新增或修改一个通过公共接口验证行为的测试, 运行并记录 RED 失败, 再写最小生产代码到 GREEN, 必要时重构并复跑验证. 每个行为切片按 RED->GREEN 小循环推进, 不得批量先写所有测试再批量实现. 若缺少测试接缝, 测试文件不在 allowed-files.txt, 需求不可验证, 或无法得到可信 RED, 必须停止并报告 blocker, 不得先改生产代码. 只修改 allowed-files.txt 允许文件. 不使用仓库根 progress.md. 如缺少文档指针, 文档冲突, 需要修改非 allowed files, 或出现未批准的产品/API/架构/范围决策, 停止并报告. 结束前运行 git diff --stat, git diff --name-only, git status --short 和聚焦验证命令. 不 stage 文件. 结束时除写入 worker-result.md 外, 最后一段必须输出可解析的 acceptance-report fenced block. 必须包含 tdd-cycles, tests-added-or-changed, changed-files, commands-run, validation-output, residual-risks, no-staged-files. 不要只写普通 Markdown 总结. 若 runtime 只要求修复 acceptance-report 格式, 只修最终报告格式, 不再编辑源码.",
      acceptance: {
        criteria: [
          "Only approved milestone scope is implemented",
          "At least one behavior test is added or changed before production code is changed, or a blocker stops the run before production code changes",
          "RED failure and GREEN pass commands are recorded for each implemented behavior slice",
          "Allowed file boundaries are respected",
          "Focused validation is run or a blocker is reported",
          "No staged files remain",
          "Changed files and residual risks are reported"
        ],
        evidence: [
          "tests-added",
          "changed-files",
          "commands-run",
          "validation-output",
          "residual-risks",
          "no-staged-files"
        ],
        maxFinalizationTurns: 2
      }
    }
  ],
  cwd: "<repo>",
  context: "fresh",
  chainDir: "<AFK_RUN_DIR>",
  sessionDir: "<AFK_SESSION_DIR>",
  clarify: false,
  timeoutMs: 900000
})
```

worker/fix 最后一段使用此最小模板. `result` 只能使用 `passed`, `failed`, `not-run`:

````md
```acceptance-report
tdd-cycles:
  - behavior: <observable behavior>
    test: <test file or blocker>
    red: <failing command and failure signal>
    green: <passing command>
tests-added-or-changed:
  - path: <test file or none>
    behavior: <behavior covered>
changed-files:
  - path: <file>
    reason: <why changed>
commands-run:
  - command: <command>
    result: <passed|failed|not-run>
validation-output:
  - <evidence or blocker>
residual-risks:
  - <risk or none>
no-staged-files: true
```
````

## review-only

```js
subagent({
  chain: [
    {
      parallel: [
        {
          agent: "reviewer",
          as: "correctnessReview",
          phase: "Review",
          label: "正确性和回归风险",
          reads: false,
          progress: false,
          output: "review-correctness.md",
          outputMode: "file-only",
          task: "AFK_RUN_DIR=<AFK_RUN_DIR>. 只读审查当前 diff 的正确性和回归风险. 读取 manifest.yaml, doc-pointers.md, allowed-files.txt, worker-result.md, diff-summary.md, 目标 issue, PLAN 对应章节和 PRD 必要章节. 必须直接检查真实 diff. 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件. 不使用仓库根 progress.md. 不做产品/API/架构/范围决策. 只返回有文件, 行号, diff 片段或命令证据的 findings."
        },
        {
          agent: "reviewer",
          as: "testsReview",
          phase: "Review",
          label: "测试和验证质量",
          reads: false,
          progress: false,
          output: "review-tests.md",
          outputMode: "file-only",
          task: "AFK_RUN_DIR=<AFK_RUN_DIR>. 只读审查当前 diff 的测试和验证质量. 读取 manifest.yaml, doc-pointers.md, allowed-files.txt, worker-result.md, tdd-cycles.md, diff-summary.md, 目标 issue, PLAN 对应章节和 PRD 必要章节. 必须直接检查真实 diff, 测试变更和 TDD RED/GREEN 证据. 若生产代码变更缺少可信 RED 失败或 GREEN 通过证据, 作为 required finding 返回. 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件. 不使用仓库根 progress.md. 不做产品/API/架构/范围决策. 只返回有文件, 行号, diff 片段或命令证据的 findings."
        },
        {
          agent: "reviewer",
          as: "simplicityReview",
          phase: "Review",
          label: "简洁性和范围控制",
          reads: false,
          progress: false,
          output: "review-simplicity.md",
          outputMode: "file-only",
          task: "AFK_RUN_DIR=<AFK_RUN_DIR>. 只读审查当前 diff 的简洁性和范围控制. 读取 manifest.yaml, doc-pointers.md, allowed-files.txt, worker-result.md, diff-summary.md, 目标 issue, PLAN 对应章节和 PRD 必要章节. 必须直接检查真实 diff. 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件. 不使用仓库根 progress.md. 不做产品/API/架构/范围决策. 只返回有文件, 行号, diff 片段或命令证据的 findings."
        }
      ],
      concurrency: 3
    }
  ],
  cwd: "<repo>",
  context: "fresh",
  chainDir: "<AFK_RUN_DIR>",
  sessionDir: "<AFK_SESSION_DIR>",
  clarify: false,
  async: true,
  control: {
    needsAttentionAfterMs: 180000,
    activeNoticeAfterMs: 240000,
    notifyOn: ["needs_attention"]
  },
  timeoutMs: 900000
})
```

Runtime 信号规则:

- 已收到 completed result 后, 同 run id 的 `needs_attention` 先按 stale control event 处理.
- 先检查 artifacts, grouped output 和 session log, 再考虑 status 或 interrupt.

Finding schema:

```yaml
review_scope:
  commands: []
  files: []
findings:
  - finding_id: R1
    severity: blocker|required|recommended|deferred
    evidence: path:line or diff fragment
    why_now: reason
    minimal_fix: smallest safe fix
    requires_decision: false
no_findings: none or summary
deferred_notes: []
```

## fix-only

```js
subagent({
  chain: [
    {
      agent: "worker",
      phase: "Fixes",
      label: "应用 accepted_now 修复",
      as: "fixes",
      reads: false,
      progress: false,
      output: "fix-result.md",
      outputMode: "file-only",
      skill: "tdd",
      task: "AFK_RUN_DIR=<AFK_RUN_DIR>. 只读取并处理 review-synthesis.md 中的 accepted_now. 不处理 deferred, needs_human_decision, rejected_as_not_evidenced. 每个修复必须引用 finding_id. 运行验证前先读取 manifest.yaml 的 validation_profile. 若指定 JDK, Maven 或命令, 必须使用该 profile. 若验证环境无法满足, 报告 blocker, 不把其他 JDK 或错误环境下的失败作为代码失败证据. 硬 TDD: 修改生产代码前必须先新增或修改一个能复现 finding 的行为测试, 运行并记录 RED 失败, 再写最小修复到 GREEN, 必要时重构并复跑验证. 若 finding 只涉及测试, 文档或报告格式, 仍必须先用可执行检查或既有测试得到失败信号. 若缺少测试接缝, 测试文件不在 allowed-files.txt, finding 不可验证, 或无法得到可信 RED, 必须停止并报告 blocker, 不得先改生产代码. 只修改 allowed-files.txt 允许文件. 不重构无关代码, 不扩大范围, 不自行决定产品/API/架构/范围问题. 不使用仓库根 progress.md. 结束前运行 git diff --stat, git diff --name-only, git status --short 和聚焦验证命令. 不 stage 文件. 结束时除写入 fix-result.md 外, 最后一段必须输出可解析的 acceptance-report fenced block. 必须包含 tdd-cycles, tests-added-or-changed, changed-files, commands-run, validation-output, residual-risks, no-staged-files. 不要只写普通 Markdown 总结. 若 runtime 只要求修复 acceptance-report 格式, 只修最终报告格式, 不再编辑源码.",
      acceptance: {
        criteria: [
          "Only accepted_now findings are handled",
          "Deferred and decision-needed findings are not handled",
          "Each applied fix references finding_id",
          "Each production-code fix is preceded by a failing behavior test or executable failing check that reproduces the finding",
          "RED failure and GREEN pass commands are recorded for each applied fix",
          "Allowed file boundaries are respected",
          "Focused validation is run or a blocker is reported",
          "No staged files remain",
          "Changed files and residual risks are reported"
        ],
        evidence: [
          "tests-added",
          "changed-files",
          "commands-run",
          "validation-output",
          "residual-risks",
          "no-staged-files"
        ],
        maxFinalizationTurns: 2
      }
    }
  ],
  cwd: "<repo>",
  context: "fresh",
  chainDir: "<AFK_RUN_DIR>",
  sessionDir: "<AFK_SESSION_DIR>",
  clarify: false,
  timeoutMs: 900000
})
```
