# Probe: 创建 Probe Skill

## 目的地

一个新的 **Probe skill** — 大任务入口。单会话广度优先盘问, 绘制 **Probe Backlog** (索引文件) 和 **Probe Items** (逐个决策调查); 后续遍历会话按 Item 类型和阻塞关系逐个关闭, 消除不确定性, 直到路径清晰。与领域无关。

## 笔记

- 每个会话查阅: wayfinder SKILL.md (原始参考), grilling, domain-modeling
- 固定偏好:
  - 载体: 本地 markdown, 无外部 issue tracker
  - 命名: 简洁 (`BACKLOG.md` / `ITEM-NN.md`)
  - 阻塞: Item 文件头声明 + Backlog 索引, 两者结合
  - 前沿: Backlog 显式维护前沿列表
  - 认领: 不需要 (单人场景, 无并发冲突)
  - 自检: Probe 自身判断是否需要 Backlog

## 已关闭决策

- [ITEM-01](./ITEM-01.md) — wayfinder 全部 12 个 tracker 依赖点已标注, markdown 替代方案已确认; 见 [ITEM-01-findings.md](./ITEM-01-findings.md)
- [ITEM-02](./ITEM-02.md) — Backlog 和 Item 的 markdown 模板已确定; 见 [ITEM-02-findings.md](./ITEM-02-findings.md)
- [ITEM-03](./ITEM-03.md) — Probe SKILL.md 大纲已确定; 最终产物 `/workflow/probe/SKILL.md`; 见 [ITEM-03-findings.md](./ITEM-03-findings.md)

## 前沿

(空 — 所有 Item 已关闭, 路径清晰)

## 未决迷雾

(空 — 所有迷雾已随前沿推进而转化)

## 范围外

- 修改 propose skill
- 使用外部 issue tracker
- 在 Probe 中生成 Product / Technical / Execution Spec
