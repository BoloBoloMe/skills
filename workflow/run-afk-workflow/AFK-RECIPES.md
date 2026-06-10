# AFK direct recipes

主路由见 [SKILL.md](SKILL.md). 运行步骤和恢复策略见 [AFK-RUNBOOK.md](AFK-RUNBOOK.md). 本文件只保存可复制 direct `subagent({...})` 模板.

## 公共约束

- 本仓库不维护 workflow chain JSON. 所有模板通过 direct `subagent({...})` 调用.
- worker/fix 使用 builtin `worker`. review 使用 builtin `reviewer`. scout 使用 builtin `scout`.
- 子代理 task 使用中文. schema key, 命令, JSON key, path placeholder 保持英文.
- 每个子代理 step 必须设置 `reads:false`, `progress:false`, `outputMode:"file-only"`.
- AFK 写入阶段必须设置 `chainDir:"<AFK_RUN_DIR>"`, `sessionDir:"<AFK_SESSION_DIR>"`, `context:"fresh"`. `<AFK_RUN_DIR>` 须与 recipe 外层 `chainDir` 一致.
- 父会话必须定义 `AFK_ARTIFACT_DIR=<absolute path>`. 默认可等于 `<AFK_RUN_DIR>`. 所有 artifact 写入 `AFK_ARTIFACT_DIR`.
- 子代理 task 必须使用 `<AFK_ARTIFACT_DIR>/...` 绝对路径读取 artifact. 禁止依赖 chain 相对路径, 禁止读取 `<AFK_RUN_DIR>/<step-run-id>/...`.
- TDD 循环, blocker, 验证 profile 和 `acceptance-report` 约束见 SKILL.md 不变量. 下方 task 字符串已包含 worker 所需的完整指令和可复制模板.
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
      output: "<AFK_ARTIFACT_DIR>/context-scout/context-facts.md",
      outputMode: "file-only",
      task: "AFK_ARTIFACT_DIR=<AFK_ARTIFACT_DIR>. 为以下任务做快速只读代码库探索: <TASK>. 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件. 只允许写指定 output artifact. 不制定需求, 不制定方案, 不写 PRD, 不拆议题, 不给验收标准定稿, 不判断是否执行, 不做产品/API/架构/范围决策. 目标 25 次以内工具调用, 上限 30 次. 最多精读 12 个核心文件. 输出 10 行以内事实, 相关文件, 既有行为, 约束风险, 验证线索和未知项. 每个事实必须带路径, 命令输出线索, 或明确标为推断."
    }
  ],
  cwd: "<repo>",
  context: "fresh",
  chainDir: "<AFK_RUN_DIR>",
  sessionDir: "<AFK_SESSION_DIR>",
  clarify: false,
  timeoutMs: 300000
})
```

## implement-only

````js
subagent({
  chain: [
    {
      agent: "worker",
      phase: "Implementation",
      label: "实现已批准 milestone",
      as: "implementation",
      reads: false,
      progress: false,
      output: "<AFK_ARTIFACT_DIR>/worker-result.md",
      outputMode: "file-only",
      skill: "tdd",
      task: "AFK_RUN_DIR=<AFK_RUN_DIR>. AFK_ARTIFACT_DIR=<AFK_ARTIFACT_DIR>. 从 AFK_ARTIFACT_DIR 读取 manifest.yaml, validation-profile.yaml, project-constraints.md, doc-pointers.md, allowed-files.txt, 目标 issue 全文, PLAN 对应章节和 PRD 必要章节. 运行验证前先读取 <AFK_ARTIFACT_DIR>/manifest.yaml 的 validation_profile 和 <AFK_ARTIFACT_DIR>/validation-profile.yaml. 若指定 JDK, Maven 或命令, 必须使用该 profile. 若验证环境无法满足, 报告 blocker, 不把其他 JDK 或错误环境下的失败作为代码失败证据. 只实现本次已批准 milestone. 你是当前工作树唯一写入者. 首次编辑前写 <AFK_ARTIFACT_DIR>/worker-preflight.md 和 <AFK_ARTIFACT_DIR>/worker-plan.md, 其中必须列出第一个行为测试, RED 命令, GREEN 命令, 以及允许修改的测试文件. 每个行为切片追加记录到 <AFK_ARTIFACT_DIR>/tdd-cycles.md. 硬 TDD: 修改生产代码前必须先新增或修改一个通过公共接口验证行为的测试, 运行并记录 RED 失败, 再写最小生产代码到 GREEN, 必要时重构并复跑验证. 每个行为切片按 RED->GREEN 小循环推进, 不得批量先写所有测试再批量实现. 若缺少测试接缝, 测试文件不在 allowed-files.txt, 需求不可验证, 或无法得到可信 RED, 必须停止并报告 blocker, 不得先改生产代码. 只修改 allowed-files.txt 允许文件. 不使用仓库根 progress.md. 如缺少文档指针, 文档冲突, 需要修改非 allowed files, 或出现未批准的产品/API/架构/范围决策, 停止并报告. 结束前运行 git diff --stat, git diff --name-only, git status --short, git diff --check 和聚焦验证命令. 不 stage 文件. 结束时除写入 <AFK_ARTIFACT_DIR>/worker-result.md 外, 最后一段必须输出可解析的 acceptance-report fenced block. 必须包含 tdd-cycles, tests-added-or-changed, changed-files, commands-run, validation-output, residual-risks, no-staged-files. 不要只写普通 Markdown 总结. 若 runtime 只要求修复 acceptance-report 格式, 只修最终报告格式, 不再编辑源码. 最后一段必须按此模板输出, result 只能使用 passed, failed, not-run:\n```acceptance-report\ntdd-cycles:\n  - behavior: <observable behavior>\n    test: <test file or blocker>\n    red: <failing command and failure signal>\n    green: <passing command>\ntests-added-or-changed:\n  - path: <test file or none>\n    behavior: <behavior covered>\nchanged-files:\n  - path: <file>\n    reason: <why changed>\ncommands-run:\n  - command: <command>\n    result: <passed|failed|not-run>\nvalidation-output:\n  - <evidence or blocker>\nresidual-risks:\n  - <risk or none>\nno-staged-files: true\n```",
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
````

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

## review-only-safe

默认 review recipe. 使用 foreground 单 reviewer, 覆盖 correctness, tests, simplicity. 需要拆分时由父会话串行运行多个 review, 不默认 async 并行.

```js
subagent({
  chain: [
    {
      agent: "reviewer",
      as: "safeReview",
      phase: "Review",
      label: "单 reviewer 安全审查",
      reads: false,
      progress: false,
      output: "<AFK_ARTIFACT_DIR>/review.md",
      outputMode: "file-only",
      task: "AFK_RUN_DIR=<AFK_RUN_DIR>. AFK_ARTIFACT_DIR=<AFK_ARTIFACT_DIR>. 只读审查当前 diff 的正确性, 回归风险, 测试和验证质量, 简洁性和范围控制. 只读取 <AFK_ARTIFACT_DIR>/manifest.yaml, <AFK_ARTIFACT_DIR>/doc-pointers.md, <AFK_ARTIFACT_DIR>/allowed-files.txt, <AFK_ARTIFACT_DIR>/worker-result.md, <AFK_ARTIFACT_DIR>/diff-summary.md, 以及存在时的 <AFK_ARTIFACT_DIR>/tdd-cycles.md, 目标 issue, PLAN 对应章节和 PRD 必要章节. 禁止读取 <AFK_RUN_DIR>/<step-run-id>/diff-summary.md 或任何 chain step 子目录中的替代 artifact. 必须直接检查真实 diff, 测试变更和 TDD RED/GREEN 证据. 若生产代码变更缺少可信 RED 失败或 GREEN 通过证据, 作为 required finding 返回. 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件. 不使用仓库根 progress.md. 不做产品/API/架构/范围决策. 只返回有文件, 行号, diff 片段或命令证据的 findings. 若必需 artifact 缺失, 只写缺失清单和 blocker, 不猜测相对路径."
    }
  ],
  cwd: "<repo>",
  context: "fresh",
  chainDir: "<AFK_RUN_DIR>",
  sessionDir: "<AFK_SESSION_DIR>",
  clarify: false,
  async: false,
  timeoutMs: 900000
})
```

## review-only

`review-only` 现在是 `review-only-safe` 的别名. 默认复制 [review-only-safe](#review-only-safe). 禁止默认启动 3 个 async reviewer. 若父会话确实需要拆分 correctness, tests, simplicity, 必须串行运行, 并分别输出 `review-correctness.md`, `review-tests.md`, `review-simplicity.md`.

Runtime 信号规则:

- 已收到 completed result 后, 同 run id 的 `needs_attention` 先按 stale control event 处理.
- 先检查 artifacts, grouped output 和 session log, 再考虑 status 或 interrupt.
- reviewer stale 时最多重试一次 `review-only-safe`. 再失败则父会话直接审查并写 `review-synthesis.md`.

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

````js
subagent({
  chain: [
    {
      agent: "worker",
      phase: "Fixes",
      label: "应用 accepted_now 修复",
      as: "fixes",
      reads: false,
      progress: false,
      output: "<AFK_ARTIFACT_DIR>/fix-result.md",
      outputMode: "file-only",
      skill: "tdd",
      task: "AFK_RUN_DIR=<AFK_RUN_DIR>. AFK_ARTIFACT_DIR=<AFK_ARTIFACT_DIR>. 只读取并处理 <AFK_ARTIFACT_DIR>/review-synthesis.md 中的 accepted_now. 不处理 deferred, needs_human_decision, rejected_as_not_evidenced. 每个修复必须引用 finding_id. 运行验证前先读取 <AFK_ARTIFACT_DIR>/manifest.yaml 的 validation_profile 和 <AFK_ARTIFACT_DIR>/validation-profile.yaml. 若指定 JDK, Maven 或命令, 必须使用该 profile. 若验证环境无法满足, 报告 blocker, 不把其他 JDK 或错误环境下的失败作为代码失败证据. 硬 TDD: 修改生产代码前必须先新增或修改一个能复现 finding 的行为测试, 运行并记录 RED 失败, 再写最小修复到 GREEN, 必要时重构并复跑验证. 若 finding 只涉及测试, 文档或报告格式, 仍必须先用可执行检查或既有测试得到失败信号. 若缺少测试接缝, 测试文件不在 allowed-files.txt, finding 不可验证, 或无法得到可信 RED, 必须停止并报告 blocker, 不得先改生产代码. 只修改 allowed-files.txt 允许文件. 不重构无关代码, 不扩大范围, 不自行决定产品/API/架构/范围问题. 不使用仓库根 progress.md. 每个行为切片追加记录到 <AFK_ARTIFACT_DIR>/tdd-cycles.md. 结束前运行 git diff --stat, git diff --name-only, git status --short, git diff --check 和聚焦验证命令. 不 stage 文件. 结束时除写入 <AFK_ARTIFACT_DIR>/fix-result.md 外, 最后一段必须输出可解析的 acceptance-report fenced block. 必须包含 tdd-cycles, tests-added-or-changed, changed-files, commands-run, validation-output, residual-risks, no-staged-files. 不要只写普通 Markdown 总结. 若 runtime 只要求修复 acceptance-report 格式, 只修最终报告格式, 不再编辑源码. 最后一段必须按此模板输出, result 只能使用 passed, failed, not-run:\n```acceptance-report\ntdd-cycles:\n  - behavior: <observable behavior>\n    test: <test file or blocker>\n    red: <failing command and failure signal>\n    green: <passing command>\ntests-added-or-changed:\n  - path: <test file or none>\n    behavior: <behavior covered>\nchanged-files:\n  - path: <file>\n    reason: <why changed>\ncommands-run:\n  - command: <command>\n    result: <passed|failed|not-run>\nvalidation-output:\n  - <evidence or blocker>\nresidual-risks:\n  - <risk or none>\nno-staged-files: true\n```",
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
````
