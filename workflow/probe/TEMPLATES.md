# Probe 模板

## ROADMAP.md

```markdown
# <标题>

## 目的地

<到达时的样子 — 1-2 句话. 每个会话选 Milestone 前都以此定向.>

## 笔记

<领域; 每个会话应查阅的 skill; 本次任务的固定偏好>

## 已关闭决策

<!-- 每个已关闭 Milestone 一行: 链接 + 一句话摘要 -->
- [<MILESTONE-NN>](<链接>) — <一句话摘要>

## 前沿

<!-- 开放 + 已解除阻塞 + 未被认领的 Milestone -->
- [<MILESTONE-NN>](<链接>) — `<类型>` — <问题简述>

## 未决迷雾

<!-- 范围内但尚无法精确表述为 Milestone 的模糊视图; 随前沿推进而转化 -->

## 范围外

<!-- 目的地之外, 有意识排除的工作; 标注排除原因 -->

## 阻塞关系

<!-- Milestone 间依赖图, ASCII 箭头表达 -->
```

## MILESTONE-NN.md

```markdown
# 状态: <待处理|进行中|已关闭>
# 类型: <research|deliberate|prototype|task>
# 阻塞于: <MILESTONE-NN|无>

## 问题

<本 Milestone 要解决的决策或调查>
```

### 规则

- `状态`: 三种 — `待处理` (初始), `进行中` (已认领), `已关闭` (已完成)
- `类型`: `research`, `deliberate`, `prototype`, `task`
- `阻塞于`: 无阻塞时写 `无`; 多项时逗号分隔
- 答案不写入 Milestone 正文 — 写入独立产物文件 (如 `MILESTONE-NN-findings.md`), 由 ROADMAP `已关闭决策` 链接
- 全部产物放在 `docs/changes/<feature-slug>/` 子目录下
