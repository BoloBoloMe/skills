---
name: orchestrate
description: 选择并编排 workflow skills.
disable-model-invocation: true
---

开始前, 使用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

判断工作从哪条 flow 进入, 加载对应 skill 的 `SKILL.md` 按它执行. 选不中 -> `grill-me` 澄清.

## Spec 执行流

- 新想法, 产品或技术边界未定, 有代码库 -> `propose`.
- 产品/技术决策已在会话中确认, 要生成产品基线 -> `to-product-spec`.
- `PRODUCT.md` 已存在, 要整理技术契约 -> `to-technical-spec`.
- `PRODUCT.md` 和 `TECHNICAL.md` 已存在, 要拆执行切片 -> `to-execution-spec`.
- `EXECUTION.md`/issues/DECISIONS 已就绪, issue 已在会话中确认 -> `afk`.
- 行为已明确, 由当前会话直接测试先行实现 -> `tdd`.

完整主链:

```text
propose -> to-product-spec -> to-technical-spec -> to-execution-spec -> afk
```

Product/Technical/Execution Spec 和运行产物只供 AI 使用. 所有影响产品, API, 架构, 范围, 风险或验证的决定必须在 `propose` 会话中向我解释并确认. 不路由到"让我阅读文档后批准"的步骤.

## on-ramp

- worktree/repo 布局/分支隔离 -> `use-worktree`.
- 交互式代码评审/逐段走读 -> `code-review-with-me`.
- 远程仓库 URL, 要了解 -> `explore-repo`.

## codebase health

- 全库架构报告 -> `improve-codebase-architecture`.
- module interface/seam/deep module/可测试性 interface 设计 -> `codebase-design`.
- 固定或扩展领域术语/ubiquitous language/context map/ADR -> `domain-modeling`.

## 兜底

- 无代码库, 路由不清, 纯对话压力测试 -> `grill-me`.

## 前置

仓库缺本地 issue tracker/领域文档约定, 且后续 flow 需要 -> 先 `setup-workspace`, 完成后回原 flow.

## 衔接

各环节不自动触发下一环节, 推进由我显式发起. 主链尽量留在同一上下文, 中途不 compact. 会话过满或需独立线程 -> `handoff`, 新会话用 `receive-handoff` 接续.
后续 Spec 生成 skill 发现新决策或来源冲突时, 必须退回 `propose`, 在会话中解释影响并盘问, 不得藏进文档让我发现.
