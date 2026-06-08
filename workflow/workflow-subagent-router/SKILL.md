---
name: workflow-subagent-router
description: 为工作流技能选择少量已保存子代理链. 当父会话已用 `orchestrate` 分类, 且只需要只读代码库探索以压缩上下文, 或需要执行已批准且可 AFK 的编码任务时使用. 不用于需求对齐, 方案制定, PRD, 议题拆分或执行决策外包.
---

# 工作流子代理路由器

本技能只供父会话使用. 不注入普通子代理.

## 不变量

- `orchestrate` 先判断工作流类型, 本技能只判断是否调用已保存链.
- 只有两条合法链:
  - `workflow-context-scout`: 只读探索代码库, 压缩上下文.
  - `workflow-afk-implement-review`: 已批准计划的 AFK 编码执行和差异审查.
- 父会话负责需求对齐, 方案制定, PRD, 议题拆分, 验收标准定稿和是否执行.
- 子代理不得代写需求/方案/PRD/议题, 不得自行选择下一步工作流, 不得扩大范围.

## 路由

| 场景 | 链 |
|---|---|
| 需求对齐, 计划制定, 诊断前置理解, 架构理解需要读代码/文档/测试/配置, 且父会话直接读取会撑爆上下文 | `workflow-context-scout` |
| 计划已批准, 行为/范围/验收标准明确, 用户允许离线编码, 执行子代理不需要代做产品/架构/API/范围决策 | `workflow-afk-implement-review` |
| 其他场景 | 不用链. 父会话直接处理或使用对应工作流技能 |

## 调用约束

### `workflow-context-scout`

- 父会话调用时设置 `timeoutMs: 240000` 到 `300000`, 不依赖默认 120s.
- 只读探索. 提示中必须区分: 禁止修改项目源码/配置/文档, 但允许写 chain 指定 output artifact.
- 若需要更深 handoff, 先运行本链拿快速事实, 再由父会话决定是否另行调用 `context-builder`, 不在子代理内自行升级.

### `workflow-afk-implement-review`

- 仅在计划, 范围, 验收标准已获批准后调用.
- 默认单写入者. 若当前仓库可能已有 unrelated dirty 文件, 先由父会话检查或使用 worktree 隔离.
- 子链内 reviewer 是只读, fixes 只处理 review synthesis 的 `accepted_now`.
- 若出现 `needs_parent_decision`, 未批准范围变化, 关键验证无证据, 父会话接回决策, 不让子代理继续猜.

