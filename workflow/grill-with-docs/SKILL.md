---
name: grill-with-docs
description: 结合领域文档, ADR 和代码事实的项目感知设计盘问.
disable-model-invocation: true
---

# Grill With Docs

用领域语言, ADR 和代码事实进行设计盘问. 目标不是普通追问, 而是把需求边界压到能写 PRD, issue, PLAN 或 ADR 的程度.

## 流程

### 1. 读取项目语境

先读取目标项目的领域语言和 ADR:

- 若存在 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 先读 map, 再读相关 `docs/language/contexts/*.md`.
- 否则读取 `docs/language/UBIQUITOUS_LANGUAGE.md`.
- 读取相关 `docs/adr/*.md` 或 `docs/adr/contexts/<context>/*.md`.
- 如果这些文件不存在, 记录为 `未知`, 不要为创建文件中断会话.

完成标准: 已得到相关术语, 已知决策约束, 缺失文档清单.

### 2. 聚焦探索代码事实

根据用户计划中的领域词, 模块名, API 名, 入口点做聚焦搜索. 只读相关代码, 目标是回答需求边界问题, 不是全仓库扫描.

完成标准: 每个关键问题都有代码事实引用, 或被明确标记为 `代码事实未知`. 引用格式使用 `path:start~end`.

### 3. 运行 grilling 会话

按 `/grilling` 的方式追问: 一次只问一个问题, 给出推荐答案, 审视用户回答, 必要时提出反对意见. 问题优先来自领域语言冲突, ADR 约束, 代码事实和边界场景.

完成标准: 设计树中的关键分支已闭合, 或仍开放的分支被列为待决问题并说明阻塞影响.

### 4. 同步领域模型

需要固定新术语, 修正术语或记录难以逆转的设计决策时, 使用 `/domain-modeling`. 单纯读取领域语言不算使用 `/domain-modeling`.

完成标准: 已成形术语写入领域语言, 满足 ADR 条件的决策已提出或写入 ADR. 不满足条件的决策留在当前会话结论中.

## 输出格式

每轮答复保持电报文:

- `事实`: 领域语言/ADR/代码事实摘要, 带引用.
- `冲突`: 与现有事实不一致或不确定之处.
- `建议`: 推荐答案.
- `问题`: 一个需要用户回答的问题.

结束时输出:

- 已闭合决策
- 待决问题
- 已更新文档路径(如有)
- 建议下一步: PRD / issues / PLAN / ADR / 实现
