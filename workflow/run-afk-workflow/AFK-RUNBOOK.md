# AFK 子代理运行手册

主路由见 [SKILL.md](SKILL.md). 可复制模板见 [AFK-RECIPES.md](AFK-RECIPES.md).

## 何时阅读

- 准备执行 implement-only 前: 读到 `父会话步骤`.
- worker 完成后: 读 `父会话步骤` 中 diff, review, synthesis, validation 段落.
- 子代理异常或输出不完整: 读 `失败恢复`.

## 核心原则

- 父会话是调度器, 子代理是单阶段执行器.
- 每个阶段必须有磁盘 checkpoint.
- worker/fix 单写入者, reviewer 并行只读.
- worker 直接读取 PRD, PLAN 和 issue 的必要部分. 父会话不改写需求简报.
- worker 默认 foreground 或短 async, reviewer 才 async.
- 父会话负责合并 reviewer findings 和决定 fix scope.

## 状态机

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

## Artifact 目录

```text
<AFK_RUN_ROOT> = <system-temp>/pi-afk-runs
<AFK_RUN_DIR> = <AFK_RUN_ROOT>/<run-id>
<AFK_SESSION_DIR> = <system-temp>/pi-afk-sessions
```

父会话创建 `<AFK_RUN_DIR>`, 并在 direct recipe 中设置 `chainDir:<AFK_RUN_DIR>`. task 中的 `AFK_RUN_DIR` 必须与 `chainDir` 一致.

推荐文件:

```text
manifest.yaml
baseline.txt
allowed-files.txt
doc-pointers.md
validation-profile.yaml
project-constraints.md
runtime-notes.md
worker-preflight.md
worker-plan.md
tdd-cycles.md
worker-result.md
diff-summary.md
review-correctness.md
review-tests.md
review-simplicity.md
review-synthesis.md
fix-result.md
final-report.md
orphan-worker.patch
orphan-worker-stat.txt
orphan-worker-files.txt
```

## 父会话步骤

### 1. Preflight

运行并保存到 `baseline.txt`:

```bash
git status --short --branch
git rev-parse HEAD
git diff --stat
git diff --name-only
```

写入:

- `manifest.yaml`: run id, repo, branch, head, task, PRD/PLAN/issue 路径, required sections, allowed files, `validation_profile` 摘要.
- `allowed-files.txt`: 本 milestone 允许修改的文件.
- `doc-pointers.md`: PRD, PLAN, issue 路径, 必读章节, 推荐读取顺序.
- `validation-profile.yaml`: JDK, Maven, 测试命令, quality checks 等验证约束. 若不需要特定环境, 明确写 `none`.
- `project-constraints.md`: 从 AGENTS, build skill 或项目文档提取的关键约束. 只写会影响本 run 的约束.
- `runtime-notes.md`: 记录 runtime 异常信号, stale notification, acceptance parse recovery 等调度事实.

`manifest.yaml` 中的 `validation_profile` 示例:

```yaml
validation_profile:
  required_jdk: 8
  jdk_home: "<jdk-home>"
  red_test_command: "<run focused test expected to fail>"
  green_test_command: "<run focused test expected to pass>"
  compile_command: "<set JAVA_HOME and run mvn>"
  build_scripts_available: false
  quality_checks:
    - id: changed-files-only
      command: "git diff --name-only"
    - id: no-staged-files
      command: "git status --short"
    - id: no-whitespace-errors
      command: "git diff --check"
    - id: changed-log-language
      command: "check changed hunks for non-English log messages"
```

若仓库有专用 build skill 或 AGENTS 指定 JDK, Maven, wrapper, 环境变量, 父会话必须把对应平台的可执行命令或 blocker 写入 `validation-profile.yaml` 和 `doc-pointers.md`. worker/fix 必须优先使用该 profile. 错误 JDK 或错误环境下的失败只记录为环境噪音.

TDD preflight 是写入阶段 gate:

- `allowed-files.txt` 必须包含实现文件和对应测试文件. 若测试文件未知, 写入允许的测试目录或新增测试文件路径.
- `validation-profile.yaml` 必须给出可执行的 RED/GREEN 聚焦测试命令, 或写明 blocker.
- 如果需求不可通过公共接口验证, 缺少测试接缝, 或测试文件不能进入 allowed files, 不启动 implement-only/fix-only.

worker 推荐读取顺序: manifest, validation-profile, project-constraints, doc-pointers, allowed-files, issue 全文, PLAN 对应章节, PRD 必要章节, 必须源码和测试.

### 2. Implement

使用 [implement-only](AFK-RECIPES.md#implement-only).

worker 约束:

- 首次编辑前写 `worker-preflight.md` 和 `worker-plan.md`.
- `worker-plan.md` 必须列出第一个行为测试, RED 命令, GREEN 命令, 允许修改的测试文件.
- TDD 循环和 blocker 规则见 SKILL.md 不变量. task 字符串已包含 worker 所需的完整 TDD 指令.
- 每个行为切片追加记录到 `tdd-cycles.md`: behavior, test file, RED command/output, GREEN command/output, refactor command/output.
- 首次编辑前最多 25 次 read/search 工具调用.
- 最多精读 12 个源码/测试文件.
- 只改 `allowed-files.txt` 允许文件.
- 不跑全量测试, 除非 issue, PLAN 或父会话 task 明确要求.
- 不 stage 文件.

### 3. Diff check

worker 完成后运行:

```bash
git diff --stat
git diff --name-only
git status --short
git diff --check
```

父会话还必须检查 TDD 证据:

- diff 中生产代码变更必须有测试变更或可执行检查证据对应.
- `worker-result.md` 或 `tdd-cycles.md` 必须记录 RED 失败和 GREEN 通过命令.
- 若生产代码已变更但缺少可信 RED 证据, 标记为 `WORKER_FAILED`, 不进入 review-only. 处理见 `失败恢复`.

如项目约束禁止新增非英文日志或类似局部风格规则, 只检查 changed hunks 或 changed files, 不要求当前任务修复历史问题.

写 `diff-summary.md`:

```md
# Diff summary

## Changed files
## Diff intent
## Validation observed
## Out-of-bound changes
## Parent decision
```

若 diff 为空或越过 allowed files, 父会话先处理, 不进入 review-only.

### 4. Review

使用 [review-only](AFK-RECIPES.md#review-only). 三个 reviewer 并行审查:

- correctness: 正确性和回归风险.
- tests: 测试和验证质量, 包括 TDD RED/GREEN 证据是否可信.
- simplicity: 简洁性和范围控制.

只接受有文件, 行号, diff 片段或命令证据的 findings.

若父会话已收到 completed result, 后续同 run id 的 `needs_attention` 先按 stale control event 处理. 检查顺序: artifacts 是否存在, grouped output 是否 completed, session log 是否结束, 必要时再 status(dir). 不直接 interrupt 已完成 run.

### 5. Synthesis

父会话读取 `review-correctness.md`, `review-tests.md`, `review-simplicity.md`, 写 `review-synthesis.md`:

```yaml
accepted_now: []
deferred: []
needs_human_decision: []
rejected_as_not_evidenced: []
reviewer_coverage: []
fix_worker_instructions: []
```

分类规则:

- `accepted_now`: blocker|required, 证据充分, minimal fix 明确, 不需要决策, 不扩大范围, 不越过 allowed files.
- `deferred`: 有价值但非必要, 或超出当前 milestone.
- `needs_human_decision`: 需要产品, API, 架构或范围判断.
- `rejected_as_not_evidenced`: 无文件, 行号, diff 或命令证据.

不启动 fix-only 的条件:

- `accepted_now` 为空: 直接 final validation.
- `needs_human_decision` 非空: 停止并询问用户.
- 修复会越过 `allowed-files.txt`: 交回父会话决策.

### 6. Fix

使用 [fix-only](AFK-RECIPES.md#fix-only). fix worker 只处理 `accepted_now`, 不处理 `deferred`, `needs_human_decision`, `rejected_as_not_evidenced`. 每个修复必须引用 `finding_id`. 每个会改生产代码的修复必须先用行为测试或可执行检查复现 finding 的 RED 失败, 再做最小 GREEN 修复. 无法复现时报告 blocker, 不得先改生产代码.

### 7. Final validation

父会话运行聚焦验证, 并复核 `tdd-cycles` 与真实 diff 一致, 写 `final-report.md`:

```md
# Final report

## Final diff
## TDD evidence
## Validation
## Review resolution
## Remaining blockers
## Residual risks
## Next action
```

父会话必须把最终事实来源排序写清楚: artifact, 真实 diff, 验证命令优先于 runtime 状态信号. 子代理状态是调度信号, 不是最终代码事实.

## Runtime 信号冲突处理

事实优先级:

1. 真实工作树 diff 和 allowed-files 检查.
2. 父会话运行的验证命令.
3. 已落盘 artifacts 和 session log.
4. subagent completed/failed/needs_attention 等 runtime 信号.

处理规则:

- completed result 优先于完成后到达的同 run `needs_attention`. 先按 stale control event 记录到 `runtime-notes.md`.
- `subagent({ action:"status", id })` 失败不等于 run 未完成. foreground completed run 可能只能通过 grouped output, session 或 artifact 判断.
- `acceptance-report` parse failure 不等于代码失败. 若 artifact 存在或工作树 dirty, 先补验 diff 和验证命令.
- 工作树 dirty 时禁止自动重跑 worker. 先保存 diff, 再由父会话决定 review, 手工修复, 继续或回滚.
- worker validation 若使用错误 JDK 或错误 profile 失败, 按 `validation-profile.yaml` 或项目 build skill 重跑. 错误环境失败只记为环境噪音.

## 失败恢复

| 情况 | 处理 |
|---|---|
| runner stale, 工作树干净, 无 checkpoint | 不原样重跑. 缩小文档读取范围, 确认 `reads:false` 和 `progress:false`, 改 foreground 重跑. |
| runner stale, 工作树干净, 有 checkpoint | 从 checkpoint 判断阶段. 新 run 使用 fresh context, 读取 doc-pointers 和 checkpoint. 不 resume 旧 session. |
| runner stale, 工作树 dirty, 无 result | 保存 orphan diff, 由父会话审查后决定 review, 手工修复, 继续或回滚. 禁止自动重跑 worker. |
| worker/fix 返回 failed, 原因为 acceptance-report parse failure, 且工作树 dirty 或 result artifact 存在 | 不自动重跑 worker. 父会话读取 result artifact, 检查真实 diff, 运行验证. 若 diff 合规且验证通过, 可视为 implementation/fix done, 并在 final report 记录 runtime acceptance 格式失败. |
| worker result 存在, acceptance 不完整 | 父会话用真实 diff 和命令补验. 不让原 worker 自审多轮. 必要时启动只读 reviewer. |
| completed 后收到同 run `needs_attention` | 查 artifact, grouped output, session log. 不 interrupt. 记录为 stale control event. |
| worker 验证使用错误 JDK 或错误 profile 失败 | 按 `validation-profile.yaml` 或项目 build skill 重跑. 错误环境失败只记为环境噪音, 不作为代码失败证据. |

保存 orphan diff:

```bash
git diff > "<AFK_RUN_DIR>/orphan-worker.patch"
git diff --stat > "<AFK_RUN_DIR>/orphan-worker-stat.txt"
git diff --name-only > "<AFK_RUN_DIR>/orphan-worker-files.txt"
```
