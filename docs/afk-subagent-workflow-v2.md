# AFK 子代理编码工作流 v2 稳定性改进提案

## 背景

当前 `workflow-afk-implement-review` 使用长 async chain 承载完整流程:

```text
worker -> reviewer fanout -> synthesis -> fix worker -> final audit
```

近期运行中多次在首个 worker 阶段失败. 失败表现不是业务代码错误, 编译错误或测试失败, 而是 async runner 进程在写出结果前消失, 随后由 stale-run reconciliation 标记为 failed.

典型证据:

- `7cf69d5a-6068-4532-96b5-37623f3fbb1d`: step 0 worker 失败, error 为 `Async runner process 19068 exited or disappeared before writing a result`.
- `b4bb0cdc-24e2-4b2b-9f7e-08b28598c1c9`: step 0 worker 同型失败.
- `58a48250-9f49-4208-854e-5dfd35ab67aa`: single worker 同型失败, 且失败前已有 edit 行为.

共同特征:

- worker 在 2 到 3.5 分钟内读取大量上下文, token 约 60k 到 80k.
- chain 后续 reviewer, synthesis, fix worker, final audit 多数未实际启动, 只是级联标记 failed.
- 自动 reads 触发不存在的 `context.md` 和 `plan.md`, 产生 ENOENT 噪音.
- progress 注入可能要求在仓库根维护 `progress.md`, 与 dirty worktree preflight 规则冲突.
- 输出和 session 路径较长, Windows 环境下增加路径和诊断复杂度.

## 目标

建立可复用, 可稳定运行, 可恢复的 AFK 编码工作流. 核心目标不是让单个子代理承担更多工作, 而是让父会话保持调度权, 让每个子代理只承担短任务, 并在磁盘上保留可恢复 checkpoint.

## 非目标

- 不追求一个 chain 自动完成所有实现和审查.
- 不让子代理代替父会话做产品, 架构, API 或范围决策.
- 不让 writer 和 reviewer 并发修改同一工作树.
- 不依赖子代理长会话自审多轮来保证质量.

## 核心原则

1. 父会话是调度器, 子代理是单阶段执行器.
2. 写入阶段单写入者, review 阶段可并行只读.
3. 每个阶段必须有磁盘 checkpoint, 失败后按 checkpoint 恢复.
4. worker 直接读取既有 PRD, PLAN 和 issue 的必要部分, 父会话不另写需求简报.
5. writer 默认 foreground 或短 async, reviewer 才 async.
6. 子代理默认 `reads:false`, `progress:false`.
7. 所有 artifacts 和 session 使用短路径, 不写仓库根临时文件.
8. 父会话负责合并 reviewer findings 和决定 fix scope.

## 推荐状态机

```text
INIT
-> PARENT_PREFLIGHT
-> DOC_POINTERS_READY
-> WORKER_RUNNING
-> WORKER_DONE | WORKER_FAILED
-> PARENT_DIFF_CHECK
-> REVIEW_RUNNING
-> REVIEW_DONE
-> PARENT_SYNTHESIS
-> FIX_RUNNING | FINAL_VALIDATE
-> FINAL_VALIDATE
-> DONE | NEEDS_HUMAN
```

### 状态职责

| 状态 | 负责人 | 产物 | 说明 |
| --- | --- | --- | --- |
| `PARENT_PREFLIGHT` | 父会话 | `baseline.txt`, `manifest.yaml` | 检查 branch, HEAD, dirty 状态, allowed files. |
| `DOC_POINTERS_READY` | 父会话 | `manifest.yaml` 中的 document pointers | 指定 PRD, PLAN, issue 路径和必读章节, 不重写需求简报. |
| `WORKER_RUNNING` | worker | `worker-preflight.md`, `worker-plan.md`, `worker-result.md` | 单写入者实现一个 milestone. |
| `PARENT_DIFF_CHECK` | 父会话 | `diff-summary.md` | 检查真实 diff, 决定是否进入 review. |
| `REVIEW_RUNNING` | reviewer fanout | `review-*.md` | 并行只读 review. |
| `PARENT_SYNTHESIS` | 父会话 | `review-synthesis.md` | 合并 findings, 决定 accepted_now. |
| `FIX_RUNNING` | fix worker | `fix-result.md` | 只修复 accepted_now. |
| `FINAL_VALIDATE` | 父会话或只读 reviewer | `final-report.md` | 汇总最终 diff, 验证, 风险. |

## 目录布局

建议所有 AFK 临时 artifacts 写到系统临时目录下, 不写仓库. 父会话先解析临时目录, 再把绝对路径传给子代理, 不依赖 shell 自动展开环境变量.

推荐变量:

```text
<AFK_RUN_ROOT> = <system-temp>/pi-afk-runs
<AFK_RUN_DIR> = <AFK_RUN_ROOT>/<run-id>
<AFK_SESSION_DIR> = <system-temp>/pi-afk-sessions
```

当前 Windows 环境示例:

```text
<AFK_RUN_DIR> = C:/Users/L9214/AppData/Local/Temp/pi-afk-runs/<run-id>
<AFK_SESSION_DIR> = C:/Users/L9214/AppData/Local/Temp/pi-afk-sessions
```

`<AFK_RUN_DIR>` 建议结构:

```text
<AFK_RUN_DIR>/
  manifest.yaml
  baseline.txt
  allowed-files.txt
  doc-pointers.md
  worker-preflight.md
  worker-plan.md
  worker-result.md
  diff-summary.md
  review-correctness.md
  review-tests.md
  review-simplicity.md
  review-synthesis.md
  fix-result.md
  final-report.md
  orphan-worker.patch
```

原因:

- 避免仓库 dirty.
- 临时产物符合一次性 AFK 调度语义.
- 失败后可按 run-id 复盘.
- 可由系统或脚本定期清理.
- 使用单独 `pi-afk-*` 前缀, 避免混入项目文件.

## 父会话 preflight

父会话先运行:

```bash
git status --short --branch
git rev-parse HEAD
git diff --stat
git diff --name-only
```

父会话写 `manifest.yaml`:

```yaml
run_id: apple-iap-issue01-20260608-001
repo: D:/Workspace/ChangZhi/cz_sdk/cz_sdk-master-feat-apple-iap-non-consumable-delivery
branch: feat/20260609-apple-iap-non-consumable-delivery
head: <sha>
state: DOC_POINTERS_READY
task: docs/changes/apple-iap-non-consumable-delivery/issues/01-apple-s2s-one-time-charge-delivery-main-flow.md
documents:
  prd: docs/changes/apple-iap-non-consumable-delivery/PRD.md
  plan: docs/changes/apple-iap-non-consumable-delivery/PLAN.md
  issue: docs/changes/apple-iap-non-consumable-delivery/issues/01-apple-s2s-one-time-charge-delivery-main-flow.md
required_sections:
  prd:
    - 问题陈述
    - 解决方案
    - 实现决策
    - 测试决策
    - 范围外
  plan:
    - 当前 issue 对应章节
  issue:
    - 全文
allowed_files:
  - czsdk-paycenter/src/main/java/com/changzhi/paycenter/service/open/PurchaseServerNotifyAppleService.java
  - czsdk-paycenter/src/test/java/com/changzhi/paycenter/service/open/PurchaseServerNotifyAppleServiceTest.java
children: []
```

## 文档读取策略

PRD, PLAN 和 issue 已经是任务事实源. 父会话不再为 worker 改写需求简报, 避免二次转述引入偏差. 父会话只负责提供 document pointers 和读取顺序.

推荐读取顺序:

1. 先读目标 issue 全文, 明确本次切片的目标, 非目标, 验收标准.
2. 内读 PLAN 中目标 issue 对应章节, 获取源码级变更边界, 参考文件, 测试线索和风险点.
3. 再按需读 PRD 中必要章节: 问题陈述, 解决方案, 实现决策, 测试决策, 范围外.
4. 不要求 worker 复述文档. 读取后只输出 10 行以内的执行理解和疑点.
5. 若文档内部冲突, worker 停止并报告冲突, 不自行选择解释.

父会话可以把 document pointers 写入 `manifest.yaml`, 也可以直接写在子代理 task 中. 不建议生成新的 `brief.md`, 除非既有文档缺失或明显过长.

## writer 调度

### 推荐策略

writer 优先 foreground. 如果必须 async, 必须是短 async, 且只执行一个 milestone.

理由:

- writer 会修改工作树, 失败成本最高.
- foreground 更容易获得真实错误和完整工具结果.
- async stale-run 只能知道 runner 消失, 无法确认业务错误.

### 推荐调用形态

使用一阶段 chain, 便于在 step 上设置 `reads:false` 和 `progress:false`.

```json
{
  "chain": [
    {
      "agent": "worker",
      "reads": false,
      "progress": false,
      "output": "<AFK_RUN_DIR>/worker-result.md",
      "outputMode": "file-only",
      "task": "Read the target issue, the matching PLAN section, and the necessary PRD sections listed in manifest.yaml. Implement only this milestone. You are the sole writer."
    }
  ],
  "cwd": "D:/Workspace/ChangZhi/cz_sdk/cz_sdk-master-feat-apple-iap-non-consumable-delivery",
  "context": "fresh",
  "clarify": false,
  "timeoutMs": 900000,
  "sessionDir": "<AFK_SESSION_DIR>"
}
```

### worker 提示约束

worker prompt 应包含:

```text
- 不输出长篇推理或完整文档复述.
- 先读取目标 issue, PLAN 对应章节和 PRD 必要章节, 再读取必须源码.
- 最多精读 N 个文件. 超出要停止汇报.
- 最多 25 次 read/search 工具调用后必须进入编辑或停止汇报.
- 每次只改一个行为切片.
- 不使用仓库根 progress.md.
- 所有临时输出写 `<AFK_RUN_DIR>/`.
- bash 命令使用相对路径, 不手动把 D:/ 转成 /d/.
- 结束必须写 worker-result.md.
```

## reviewer 调度

reviewer 是只读任务, 可以 async fanout.

```json
{
  "tasks": [
    {
      "agent": "reviewer",
      "reads": false,
      "progress": false,
      "task": "Review current diff for correctness. Read the target issue, matching PLAN section, and necessary PRD sections from manifest.yaml. Do not modify project files.",
      "output": "<AFK_RUN_DIR>/review-correctness.md",
      "outputMode": "file-only"
    },
    {
      "agent": "reviewer",
      "reads": false,
      "progress": false,
      "task": "Review tests and validation evidence. Read the target issue, matching PLAN section, and necessary PRD sections from manifest.yaml. Do not modify project files.",
      "output": "<AFK_RUN_DIR>/review-tests.md",
      "outputMode": "file-only"
    },
    {
      "agent": "reviewer",
      "reads": false,
      "progress": false,
      "task": "Review simplicity and scope control. Read the target issue, matching PLAN section, and necessary PRD sections from manifest.yaml. Do not modify project files.",
      "output": "<AFK_RUN_DIR>/review-simplicity.md",
      "outputMode": "file-only"
    }
  ],
  "async": true,
  "concurrency": 3,
  "cwd": "D:/Workspace/ChangZhi/cz_sdk/cz_sdk-master-feat-apple-iap-non-consumable-delivery",
  "context": "fresh",
  "sessionDir": "<AFK_SESSION_DIR>"
}
```

reviewer 输出 schema:

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

## 父会话 synthesis

父会话读取 reviewer 输出, 写 `review-synthesis.md`.

分类规则:

- `accepted_now`: severity 为 blocker 或 required, 证据充分, minimal fix 明确, 不需要决策, 不扩大范围.
- `deferred`: 有价值但非必要, 或超出当前 milestone.
- `needs_human_decision`: 需要产品, API, 架构或范围判断.
- `rejected_as_not_evidenced`: 无文件, 行号, diff 或命令证据.

不要让子代理自动决定 `accepted_now` 后立即修复. synthesis 是父会话调度权的一部分.

## fix-worker 调度

fix worker 只读取 `review-synthesis.md`, 只处理 `accepted_now`.

```md
# Fix worker input

## Scope
Only apply accepted_now from review-synthesis.md.

## Accepted findings
- finding_id, file, minimal fix, validation hint.

## Forbidden
- Do not handle deferred.
- Do not handle needs_human_decision.
- Do not refactor unrelated code.
```

fix worker 仍按 writer 规则运行: 单写入者, `reads:false`, `progress:false`, foreground 优先.

## 失败恢复规则

### A. runner stale, 工作树干净, 无 checkpoint

处理:

- 不原样重跑.
- 缩小文档读取范围, 例如只读目标 issue, PLAN 对应章节和 PRD 必要章节.
- 确认 `reads:false` 和 `progress:false`.
- 改 foreground 重跑 worker.

### B. runner stale, 工作树干净, 有 checkpoint

处理:

- 从 checkpoint 判断阶段.
- 新 worker 使用 fresh context, 读取 document pointers 和 checkpoint.
- 不 resume 旧 session.

### C. runner stale, 工作树 dirty, 无 result

处理:

```bash
git diff > "<AFK_RUN_DIR>/orphan-worker.patch"
git diff --stat > "<AFK_RUN_DIR>/orphan-worker-stat.txt"
git diff --name-only > "<AFK_RUN_DIR>/orphan-worker-files.txt"
```

随后父会话审查 diff:

- 如果 diff 明显可用, 进入 reviewer.
- 如果 diff 半成品, 父会话决定继续, 手工修复或回滚.
- 禁止自动重跑 writer, 避免叠加坏 diff.

### D. worker result 存在, acceptance 不完整

处理:

- 父会话用真实 diff 和命令补验.
- 不让原 worker 自审多轮.
- 必要时启动只读 reviewer.

## 推荐拆分 saved chains

废弃或降级原 `workflow-afk-implement-review` 长 chain. 新增三个小 chain.

### `workflow-afk-implement-only`

职责:

- 单 worker.
- 只实现一个 approved milestone.
- 不包含 reviewer.

默认:

- `reads:false`
- `progress:false`
- `outputMode:file-only`
- `maxFinalizationTurns:1`
- artifacts 写 `<AFK_RUN_DIR>/`

### `workflow-afk-review-only`

职责:

- 只读 reviewer fanout.
- 不修改项目源码, 配置, 文档, 依赖文件和测试文件.

默认:

- `reads:false`
- `progress:false`
- `async:true`
- `outputMode:file-only`

### `workflow-afk-fix-only`

职责:

- 单 fix worker.
- 只处理父会话 synthesis 的 `accepted_now`.

默认:

- `reads:false`
- `progress:false`
- foreground 优先
- 不处理 deferred 和 needs_human_decision

## 推荐专用 agent

不直接改通用 `worker`. 建议新增 `workflow.afk-worker`.

建议配置:

```json
{
  "name": "afk-worker",
  "package": "workflow",
  "model": "ai-work-deepseek/deepseek-v4-pro",
  "thinking": "medium",
  "defaultContext": "fresh",
  "reads": false,
  "progress": false,
  "inheritProjectContext": true,
  "inheritSkills": false
}
```

原因:

- 不影响普通 worker.
- 降低流式事件量和 token 压力.
- 默认不读不存在的 `context.md` 和 `plan.md`.
- 默认不写仓库根 `progress.md`.

## acceptance contract 精简策略

不要把完整 issue 验收标准同时塞入 task 和 acceptance. worker acceptance 只要求证据完整.

推荐:

```json
{
  "criteria": [
    "Only approved milestone scope is implemented",
    "Allowed file boundaries are respected",
    "Focused validation is run or a blocker is reported",
    "No staged files remain",
    "Changed files and residual risks are reported"
  ],
  "evidence": [
    "changed-files",
    "commands-run",
    "validation-output",
    "residual-risks",
    "no-staged-files"
  ],
  "maxFinalizationTurns": 1
}
```

完整业务验收由 PRD, PLAN, issue, 父会话 diff check 和 reviewer 共同检查.

## 工具和上下文预算

### scout

- 最多 30 次工具调用.
- 最多精读 12 个文件.
- 最多 1 次测试线索集中搜索.
- 禁止编辑.

### worker

- 首次编辑前最多 25 次 read/search 工具调用.
- 优先读取目标 issue 全文, PLAN 对应章节和 PRD 必要章节, 不无目标扫读所有变更文档.
- 如还需要更多上下文, 停止并报告缺失信息.
- 不跑全量测试, 除非 issue, PLAN 或父会话 task 明确要求.

### reviewer

- 必须检查真实 diff.
- 最多精读 15 个文件.
- 只返回有证据 findings.
- 禁止编辑.

## 调度指标

每次 AFK run 在 manifest 记录:

```yaml
worker:
  run_id: <subagent-run-id>
  pid: <pid>
  start: <time>
  end: <time>
  state: done|failed|stale
  token_total: <number>
  tool_count: <number>
  output_file: <AFK_RUN_DIR>/worker-result.md
  checkpoint_files: []
  dirty_after: true|false
  changed_files: []
failure:
  type: stale_runner|child_failed|validation_failed|needs_decision
  recovery_action: <action>
```

这些指标用于判断瓶颈来自模型, runner, 路径, token, 工具调用, 还是任务拆分过大.

## 落地路线

### 阶段 1, 立即改

1. 停用 `workflow-afk-implement-review` 长 chain.
2. 新增 `workflow-afk-implement-only`, `workflow-afk-review-only`, `workflow-afk-fix-only`.
3. 所有子任务加 `reads:false`, `progress:false`.
4. artifacts 写 `<AFK_RUN_DIR>/`.
5. writer foreground, reviewer async.

### 阶段 2, 稳定性增强

1. 新增 `workflow.afk-worker` 专用 agent.
2. 父会话生成 `manifest.yaml`, `doc-pointers.md`, `allowed-files.txt`, 只记录文档指针和读取顺序, 不改写需求简报.
3. worker 写 `worker-preflight.md`, `worker-result.md`.
4. 失败恢复按 dirty 和 checkpoint 分类.

### 阶段 3, 产品化

1. 将父会话状态机沉淀成 skill 或 runbook.
2. 增加 manifest 模板.
3. 增加 reviewer finding schema.
4. 增加 recovery decision table.
5. 定期清理 `<system-temp>/pi-afk-runs` 和 `<system-temp>/pi-afk-sessions`.

## 最小可行 v2

```text
parent preflight
-> write <AFK_RUN_DIR>/manifest.yaml with document pointers
-> foreground one-step worker chain, reads:false, progress:false
-> parent diff check
-> async reviewer fanout, reads:false, progress:false
-> parent synthesis
-> foreground fix worker if needed
-> parent final validation
```

这是当前环境下最稳的可复用 AFK 编码工作流. 关键改进是缩短子代理生命周期, 让子代理读取既有事实源的必要部分, 减少自动副作用, 将决策和恢复留在父会话.
