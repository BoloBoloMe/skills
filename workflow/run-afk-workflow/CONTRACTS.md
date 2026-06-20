# AFK contracts

本文件定义 AFK workflow 的稳定契约. 父会话在任何 AFK run 开始前必须读取本文件. 具体流程见 `RUNBOOK.md`, 异常恢复见 `RECOVERY.md`, 测试 only 轻量路径见 `LIGHTWEIGHT-TEST-ONLY.md`.

## 核心原则

- `afk-running/` 是本次 AFK run 的根产物目录.
- 每个 issue 使用独立 issue 产物目录: `afk-running/<issueKey>/`.
- run root 只存放跨 issue 共享产物.
- issue 目录存放该 issue 的 implementation, review, synthesis, fix, recovery 产物.
- 子代理通过文件契约接收上下文, 不继承父会话历史.

## run root 产物

推荐路径: `docs/changes/<feature-slug>/afk-running/`.

| 产物 | 写入者 | 用途 |
|---|---|---|
| `validation-env.md` | 父会话 | 记录依赖预热, 聚焦测试命令模板, full build 命令和 smoke 结果 |
| `agent-binding.md` | 父会话 | 记录运行时无关的角色绑定和角色契约 |
| `run-manifest.md` | 父会话 | 记录 issue 顺序, issueKey, issue 产物目录 |

## issue 产物目录

`issueKey` 优先使用 issue 编号, 如 `issue02`. 没有编号时使用 issue 文件名 stem 的安全化结果.

| 阶段 | 产物 | 写入者 | 下游消费者 |
|---|---|---|---|
| 预检 | `review-policy.md` | 父会话 | 差异检查, review |
| 实现 | `worker-status.md` | worker | 恢复, 最终验证 |
| 实现 | `tdd-cycles.md` | worker | review, 修复, 最终验证 |
| 实现 | `worker-result.md` | worker | review, 综合判定 |
| review | `review-rN-一致性.md` | reviewer | 综合判定 |
| review | `review-rN-正确性.md` | reviewer | 综合判定 |
| review | `review-rN-简洁性.md` | reviewer | 综合判定 |
| 轻量跳过 | `review-skipped.md` | 父会话 | 最终验证 |
| 综合判定 | `review-综合判定-rN.md` | 父会话 | 修复 |
| 修复 | `fix-result-rN.md` | worker | 增量 review, 最终验证 |
| 恢复 | `recovery/recovery-observation-rN.md` | 父会话 | recovery worker |
| 恢复 | `recovery/dirty-diff-rN.patch` | 父会话 | recovery worker |
| 恢复 | `recovery/recovery-result-rN.md` | recovery worker | 后续流程 |

## review round 和 fix round

- 初版 review round 为 `r0`.
- 第一次 fix 后的 review round 为 `r1`, 后续递增.
- fix 结果使用 `fix-result-rN.md`, 其中 `rN` 与本轮 fix 后进入的 review round 一致.
- 最大 fix round 默认为 3 轮.

## validation-env.md

父会话只负责确认如何在目标模块内运行聚焦测试, 包括构建工具, 模块选择, 测试过滤语法, 工作目录和必要环境变量. worker 负责在每个 TDD 切片中选择具体测试类/测试方法并替换模板占位符.

`afk-running/validation-env.md` 必须覆盖:

```md
# validation-env

dependencyWarmupCommand: <命令或 none>
dependencyWarmupResult: <passed, failed, skipped>
dependencyWarmupDuration: <耗时或 unknown>

incrementalTestCommandTemplate: <聚焦测试命令模板>
templateSmokeCommand: <用已有测试验证模板的命令>
templateSmokeResult: <passed, failed, skipped>
workerMayChooseTestTarget: true
allowedFallbacks:
- test-method
- test-class
- target-module

fullBuildCommand: <完整构建命令或 none>
fullBuildOwner: parent-session
parallelBuild: <enabled, disabled, unknown>
parallelBuildReason: <原因>
```

规则:

- 若配置了 `dependencyWarmupCommand`, 父会话必须在启动 worker 前执行一次.
- 预热失败则不启动 worker.
- `incrementalTestCommandTemplate` 必须被父会话用已有测试 smoke 验证过.
- 模板只保证工具链, 模块选择和测试过滤机制可用, 不要求父会话提前知道 worker 将创建的测试名称.
- `-T 1C` 等并行编译只作为可选优化, 必须记录启用或禁用原因.
- worker 在 TDD 循环中优先使用增量测试命令, 不默认运行 root 级完整构建.

## agent-binding.md

核心 workflow 不绑定任何具体子代理插件. 父会话必须优先复用当前运行环境已有且满足角色契约的 agent/role/profile. 不因习惯或便利自动创建新 agent.

`afk-running/agent-binding.md` 必须覆盖:

```md
# agent-binding

implementationRole: <当前运行环境解析出的角色名或调用方式>
reviewRole: <当前运行环境解析出的角色名或调用方式>
recoveryRole: <当前运行环境解析出的角色名或调用方式>

roleSource: existing-runtime-role | user-provided | custom-created-after-approval
customRoleCreated: yes | no

implementationConstraints:
- single-writer
- allowed-files-only
- must-report-validation-evidence

reviewConstraints:
- read-only-source
- may-write-review-artifact
- evidence-backed-findings-only
```

规则:

- 如果现有角色是否满足契约无法判断, 父会话必须停下来询问用户.
- 如果没有合适角色, 必须先说明建议角色, scope, tools, system prompt 约束和资源上限风险, 获得用户明确批准后才能创建或配置.
- 不得设置会明显导致任务截断的人为资源上限.
- 插件命令, chain 配置, slash command 等只能出现在运行环境专属 adapter/recipe, 不写入核心 skill.

## review-policy.md

每个 issue 的 `review-policy.md` 位于 `afk-running/<issueKey>/review-policy.md`.

最小字段:

```md
issueExecutionMode: normal | test-only-light
reviewPolicy: full | skip-with-verification
changedLinesThreshold: 50
testFilePatterns:
- src/test/**
- test/**
- tests/**
- **/*Test.java
- **/*Tests.java
- **/*.test.*
- **/*.spec.*
productionFilePatterns:
- src/main/**
- app/**
- lib/**
- build.gradle
- pom.xml
- package.json
```

规则:

- `normal` issue 必须同时允许实现文件和测试文件.
- `test-only-light` 只能允许测试文件, 且必须满足 `LIGHTWEIGHT-TEST-ONLY.md` 的预声明和真实 diff 双门禁.
- 如果项目无法明确区分测试文件和生产文件, 不启用 `test-only-light`, 走完整 review.
