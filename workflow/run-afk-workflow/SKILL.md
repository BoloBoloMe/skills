---
name: run-afk-workflow
description: 为 workflow 父会话选择 direct subagent recipes. 当 orchestrate 已分类, 且需要只读代码库探索, AFK 单阶段编码, diff 后 review, 或 accepted finding 修复时使用. 不用于需求对齐, 方案制定, PRD, 议题拆分或执行决策外包.
---

# 运行 AFK 工作流

本技能只供父会话使用. 不注入普通子代理.

## 文件关系

- 本文件: 只做路由, 不承载长模板和运行手册.
- [AFK-RUNBOOK.md](AFK-RUNBOOK.md): 保存父会话状态机, checkpoint, synthesis 和失败恢复.
- [AFK-RECIPES.md](AFK-RECIPES.md): 保存可复制 direct `subagent({...})` 调用.

## 路由表

| 场景 | 动作 | 参考 |
|---|---|---|
| 需要只读代码事实以压缩父会话上下文 | 调用 scout direct recipe | `AFK-RECIPES.md#context-scout` |
| 计划已批准, 范围和验收明确, 只实现一个 milestone | 父会话 preflight 后调用 implement-only | `AFK-RUNBOOK.md#父会话步骤`, `AFK-RECIPES.md#implement-only` |
| worker 完成, 父会话已检查真实 diff 并写 `diff-summary.md` | 调用 review-only | `AFK-RECIPES.md#review-only` |
| `review-synthesis.md` 存在可立即修复的 `accepted_now` | 调用 fix-only | `AFK-RECIPES.md#fix-only` |
| 需要产品/API/架构/范围判断, 验收未定稿, 文档冲突, dirty worktree 归属不清 | 不调用子代理, 父会话处理或问用户 | `AFK-RUNBOOK.md#失败恢复` |

## 不变量

- 父会话保留需求对齐, 方案制定, PRD, 议题拆分, 验收标准定稿, 是否执行, diff check, review synthesis, failure recovery 和 final report.
- 写入阶段单写入者. review 阶段只读且可并行.
- 子代理 step 必须设置 `reads:false`, `progress:false`, `outputMode:"file-only"`.
- writer/fix 使用 builtin `worker`. review 使用 builtin `reviewer`. scout 使用 builtin `scout`.

## 父会话最小检查

- [ ] 写入阶段前已得到用户执行确认.
- [ ] `<AFK_RUN_DIR>` 已创建, 且 task 中的 `AFK_RUN_DIR` 与 `chainDir` 一致.
- [ ] `manifest.yaml`, `baseline.txt`, `doc-pointers.md`, `allowed-files.txt` 已存在.
- [ ] worker 结束后由父会话检查真实 diff, 不只信 worker 输出.
- [ ] review findings 只接受有文件, 行号, diff 片段或命令证据的项.
- [ ] final validation 和 `final-report.md` 由父会话完成.
