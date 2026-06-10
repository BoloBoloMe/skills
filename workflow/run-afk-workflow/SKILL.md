---
name: run-afk-workflow
description: 为 workflow 父会话选择 direct subagent recipes. 当 orchestrate 已分类, 且需要只读代码库探索, AFK 单阶段编码, diff 后 review, 或 accepted finding 修复时使用. 不用于需求对齐, 方案制定, PRD, 议题拆分或执行决策外包.
---

# 运行 AFK 工作流

本技能只供父会话使用. 不注入普通子代理.

本技能不做全局 workflow 分类. 普通工程请求必须先经过 `orchestrate`. 若没有 `orchestrate` 分类或 AFK checkpoint, 停止并回到 `orchestrate`.

## 文件关系

- 本文件: 只做 AFK 阶段选择, 不承载长模板和运行手册.
- [AFK-RUNBOOK.md](AFK-RUNBOOK.md): 保存父会话状态机, checkpoint, synthesis 和失败恢复.
- [AFK-RECIPES.md](AFK-RECIPES.md): 保存可复制 direct `subagent({...})` 调用.

## AFK 阶段表

| 场景 | 动作 | 参考 |
|---|---|---|
| 需要只读代码事实以压缩父会话上下文 | 调用 scout direct recipe | `AFK-RECIPES.md#context-scout` |
| 计划已批准, 范围和验收明确, 只实现一个 milestone | 父会话 preflight 后调用 implement-only | `AFK-RUNBOOK.md#父会话步骤`, `AFK-RECIPES.md#implement-only` |
| worker 完成, 父会话已检查真实 diff 并写 `diff-summary.md` | 调用 review-only | `AFK-RECIPES.md#review-only` |
| `review-synthesis.md` 存在可立即修复的 `accepted_now` | 调用 fix-only | `AFK-RECIPES.md#fix-only` |
| 子代理 runtime 状态与 artifact/diff 冲突 | 父会话先补验事实, 不自动重跑 writer | `AFK-RUNBOOK.md#runtime-信号冲突处理`, `AFK-RUNBOOK.md#失败恢复` |
| 需要产品/API/架构/范围判断, 验收未定稿, 文档冲突, dirty worktree 归属不清 | 不调用子代理, 父会话处理或问用户 | `AFK-RUNBOOK.md#失败恢复` |

## 不变量

- `orchestrate` 决定何时进入 AFK. 本技能只决定 AFK 阶段内怎么调用 direct recipes.
- 父会话保留需求对齐, 方案制定, PRD, 议题拆分, 验收标准定稿, 是否执行, diff check, review synthesis, failure recovery 和 final report.
- 写入阶段单写入者. review 阶段只读且可并行.
- 子代理 step 必须设置 `reads:false`, `progress:false`, `outputMode:"file-only"`.
- writer/fix 使用 builtin `worker`. review 使用 builtin `reviewer`. scout 使用 builtin `scout`.
- writer/fix 是硬 TDD 阶段. 修改生产代码前必须先有行为测试或可执行检查的 RED 失败证据, 再做最小 GREEN 实现, 必要时重构并复跑验证.
- writer/fix 不能静默绕过 TDD. 若测试文件不在 `allowed-files.txt`, 缺少测试接缝, 需求不可验证, 或无法得到可信 RED, 必须报告 blocker, 不得先改生产代码.
- writer/fix 必须继承 `manifest.yaml` 或 `validation-profile.yaml` 中的验证环境. 错误 JDK/错误 profile 的失败不能作为代码失败证据.
- writer/fix 最终回复必须包含可解析的 `acceptance-report` fenced block, 且包含 `tdd-cycles` 和 `tests-added-or-changed`. 代码已改但 acceptance parse failed 时, 父会话先按 artifact, 真实 diff 和验证命令补验.

## 父会话最小检查

- [ ] 写入阶段前已得到用户执行确认.
- [ ] `<AFK_RUN_DIR>` 已创建, 且 task 中的 `AFK_RUN_DIR` 与 `chainDir` 一致.
- [ ] `manifest.yaml`, `baseline.txt`, `doc-pointers.md`, `allowed-files.txt` 已存在.
- [ ] `allowed-files.txt` 已包含本 milestone 需要的测试文件. 若不能包含, preflight 必须记录为 TDD blocker, 不启动 writer/fix.
- [ ] 项目有特定 JDK/Maven/测试约束时, `validation-profile.yaml` 或 `manifest.yaml.validation_profile` 已写入可执行命令或 blocker.
- [ ] `validation-profile.yaml` 已给出可执行的 RED/GREEN 聚焦测试命令, 或明确写入不能执行 TDD 的 blocker.
- [ ] worker 结束后由父会话检查真实 diff, 不只信 worker 输出.
- [ ] review findings 只接受有文件, 行号, diff 片段或命令证据的项.
- [ ] completed 后到达的同 run `needs_attention` 先按 stale control event 排查, 不直接 interrupt.
- [ ] final validation 和 `final-report.md` 由父会话完成.
