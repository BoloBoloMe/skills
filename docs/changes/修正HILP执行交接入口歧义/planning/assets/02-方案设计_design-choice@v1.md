---
asset_id: fix-hilp-execution-handoff-intake-ambiguity-design-choice
artifact_name: stage-3/design-choice
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-test/skill-pressure-test@v1 [state=archived｜中文状态=已归档]
last_event: human-approval-granted
last_decision: human-approval-2026-04-29-approve-design-choice-v1
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/修正HILP执行交接入口歧义/planning/assets/02-方案设计_design-choice@v1.md
asset_link: [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么

把压力测试发现的执行交接入口歧义收敛为可审批的修正规则，并明确本轮只改文案与入口判定，不改规划侧状态模型。

## 已保存资产

- 文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- asset_ref：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 当前状态：已批准（内部状态值：`approved`）
- 当前是否需要审批：已批准；审核包已关闭并保留在 [02-design-choice@v1-review.md](../review-pack/02-design-choice@v1-review.md)。

## 事实基础

- 压力测试资产：[90-协议压力测试_pressure-test@v1.md](../../../HILP双Skill串联模拟测试/planning/assets/90-协议压力测试_pressure-test@v1.md)
- 审查报告：[HILP双Skill串联模拟测试-2026-04-29 17-18-56.md](../../../HILP双Skill串联模拟测试/review/HILP双Skill串联模拟测试-2026-04-29 17-18-56.md)
- 已确认规则事实：
  - 规划侧要求设计资产和蓝图资产必须为 `approved｜中文状态=已批准`。
  - 规划侧归档规则说明执行交接资产自身不要求 `approved｜中文状态=已批准`；有效交接要求成功落盘、入口检查无阻断、绑定已批准设计和已批准蓝图。
  - 执行侧 frontmatter 目前写有 “HILP execution handoff has been approved”，容易误导为执行交接资产自身也必须 approved。

## 推荐方案

### 名称

**精确修正文案：区分“已批准输入资产”和“有效执行交接资产”。**

### 核心思路

只修改 `human-in-loop-execution` 的入口描述和接收规则，把执行入口条件改成：

1. `stage-3/design-choice@vN` 必须是 `approved｜中文状态=已批准`。
2. `stage-4-5/implementation-blueprint@vM` 必须是 `approved｜中文状态=已批准`。
3. `stage-6/execution-handoff@vK` 不要求自身 `approved`；必须满足：
   - `owner_skill=hilp-execution-handoff`。
   - 已成功落盘。
   - 执行入口检查为“无阻断项”。
   - 执行范围、禁止越界项、停止并回退条件齐备。
   - 绑定的设计与蓝图版本与执行请求一致。
4. “不得把已归档规划资产当作已批准输入”改写为只约束设计和蓝图，不误伤已完成归档的执行交接记录。

### 为什么推荐

- 修复压力测试发现的真实歧义。
- 不改变规划侧资产状态模型，不需要迁移既有 HILP 资产。
- 改动范围小，风险低。
- 能让 execution skill 正确接收旧链路中 `state=archived｜中文状态=已归档` 但无阻断的执行交接资产。

## 备选方案

### 方案 A：要求执行交接资产也必须 approved

- 核心思路：把执行交接本身也纳入批准资产。
- 优点：入口条件表面更统一。
- 代价：与规划侧归档规则冲突，需要改状态模型、旧资产解释和自动归档语义。
- 不选原因：问题来自执行侧措辞歧义，不应扩大为规划状态模型变更。

### 方案 B：仅在回答中解释，不改 skill 文件

- 核心思路：保留现有文档，只在后续使用时人工解释。
- 优点：零代码/文档改动。
- 代价：歧义会持续触发，无法形成稳定入口规则。
- 不选原因：skill 行为依赖文档规则，应在规则源头修正。

## 关键取舍

- 正确性 / 安全性：保留设计和蓝图必须已批准的硬门槛；只放宽执行交接自身 approved 误读。
- 可回退性：只改 2 个 Markdown 规则文件，容易回退。
- 改动范围：限定在 `human-in-loop-execution/SKILL.md` 和 `human-in-loop-execution/references/hilp-handoff-intake.md`。
- 可维护性：统一 execution 入口术语为“有效执行交接 / 无阻断执行交接”。
- 未来扩展性：为后续兼容旧资产和新资产命名规则保留空间。

## 需要用户决定什么

- 是否存在：无必须人工裁决。
- 是否会阻止继续：无阻断项。
- 问题描述：本轮只有一个推荐修正方向，无不可兼得关键取舍。
- 可选项：
  - 采纳推荐方案：只改 execution skill 文案与入口判定。
  - 拒绝本轮修正：保留当前歧义。
- 建议：采纳推荐方案。
- 默认路径：无；用户已明确批准当前资产版本，可进入实施蓝图阶段。
- 用户是否已选择：已选择。
- 不得写成既定事实的内容：不得把本方案批准解释为蓝图批准或执行许可。

## 当前状态

- 中文状态名：已批准
- 内部状态值：`approved`
- 进入该状态的理由：用户明确批准 `stage-3/design-choice@v1`，批准决策为 `human-approval-2026-04-29-approve-design-choice-v1`。

## 下一步

- 下一阶段：实施蓝图阶段。
- 继续前提：实施蓝图必须仅覆盖已批准方案范围，并通过确定性检查。
- 当前阻断项：无阻断项。
