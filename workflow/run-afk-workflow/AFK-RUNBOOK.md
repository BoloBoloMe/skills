# AFK 子代理运行手册

主路由见 [SKILL.md](SKILL.md). 可复制模板见 [AFK-RECIPES.md](AFK-RECIPES.md).

## 何时阅读

- 准备执行 implement-only 前: 读到 `父会话步骤`.
- worker 完成后: 读 `父会话步骤` 中 diff, review, synthesis, validation 段落.
- 子代理异常或输出不完整: 读 `失败恢复`.

## 核心原则

- 父会话是调度器, 子代理是单阶段执行器.
- 每个阶段必须有磁盘 checkpoint.
- writer/fix 单写入者, reviewer 并行只读.
- worker 直接读取 PRD, PLAN 和 issue 的必要部分. 父会话不改写需求简报.
- writer 默认 foreground 或短 async, reviewer 才 async.
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

- `manifest.yaml`: run id, repo, branch, head, task, PRD/PLAN/issue 路径, required sections, allowed files.
- `allowed-files.txt`: 本 milestone 允许修改的文件.
- `doc-pointers.md`: PRD, PLAN, issue 路径, 必读章节, 推荐读取顺序.

worker 推荐读取顺序: manifest, doc pointers, allowed files, issue 全文, PLAN 对应章节, PRD 必要章节, 必须源码和测试.

### 2. Implement

使用 [implement-only](AFK-RECIPES.md#implement-only).

writer 约束:

- 首次编辑前写 `worker-preflight.md` 和 `worker-plan.md`.
- 首次编辑前最多 25 次 read/search 工具调用.
- 最多精读 12 个源码/测试文件.
- 只改 `allowed-files.txt` 允许文件.
- 不跑全量测试, 除非 issue, PLAN 或父会话 task 明确要求.
- 不 stage 文件.

### 3. Diff check

worker 结束后运行:

```bash
git diff --stat
git diff --name-only
git status --short
```

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
- tests: 测试和验证质量.
- simplicity: 简洁性和范围控制.

只接受有文件, 行号, diff 片段或命令证据的 findings.

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

使用 [fix-only](AFK-RECIPES.md#fix-only). fix worker 只处理 `accepted_now`, 不处理 `deferred`, `needs_human_decision`, `rejected_as_not_evidenced`. 每个修复必须引用 `finding_id`.

### 7. Final validation

父会话运行聚焦验证, 写 `final-report.md`:

```md
# Final report

## Final diff
## Validation
## Review resolution
## Remaining blockers
## Residual risks
## Next action
```

## 失败恢复

| 情况 | 处理 |
|---|---|
| runner stale, 工作树干净, 无 checkpoint | 不原样重跑. 缩小文档读取范围, 确认 `reads:false` 和 `progress:false`, 改 foreground 重跑 worker. |
| runner stale, 工作树干净, 有 checkpoint | 从 checkpoint 判断阶段. 新 worker 使用 fresh context, 读取 document pointers 和 checkpoint. 不 resume 旧 session. |
| runner stale, 工作树 dirty, 无 result | 保存 orphan diff, 由父会话审查后决定 review, 手工修复, 继续或回滚. 禁止自动重跑 writer. |
| worker result 存在, acceptance 不完整 | 父会话用真实 diff 和命令补验. 不让原 worker 自审多轮. 必要时启动只读 reviewer. |

保存 orphan diff:

```bash
git diff > "<AFK_RUN_DIR>/orphan-worker.patch"
git diff --stat > "<AFK_RUN_DIR>/orphan-worker-stat.txt"
git diff --name-only > "<AFK_RUN_DIR>/orphan-worker-files.txt"
```
