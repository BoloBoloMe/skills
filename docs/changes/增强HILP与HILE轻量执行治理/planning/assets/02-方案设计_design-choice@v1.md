---
asset_id: hilp-hile-gsd-lite-design-choice-v1
artifact_name: stage-3/design-choice
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: original-task
last_event: human-approval-granted
last_decision: human-approval-gsd-lite-hilp-hile-2026-05-02
approval_marker: approved
approval_marker_label: 已批准
asset_path: docs/changes/增强HILP与HILE轻量执行治理/planning/assets/02-方案设计_design-choice@v1.md
asset_link: [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
---

# 方案设计与审批阶段

## asset_ref

`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`

## 当前状态

已批准。

## 设计目标

为 `human-in-loop-planning` 和 `human-in-loop-execution` 制定最小修改方案，吸收 GSD 的核心优点，但保留 HILP / HILE 的核心气质：按需加载、人工门控、资产审计、不自动越权、不引入 runtime 平台。

## 推荐方案：方案 C，五项轻量治理增强方案

只吸收 GSD 的协议级优点：

1. Execution Unit Contract
2. Must-haves Verification Ladder
3. Context Packet
4. Execution Ledger + Unit Summary
5. Failure Forensics

不吸收 GSD 的平台级机制：CLI、auto runtime、worktree orchestration、model routing、dashboard、provider management。

## 备选方案

### 方案 A：只改 HILE，不改 HILP

不选原因：会把规划压力推迟到执行阶段，让 HILE 变相做规划。

### 方案 B：把 GSD 风格完整搬进 HILP / HILE

不选原因：Skill 会变重，并与按需加载、人工门控冲突。

## 关键取舍

- 正确性 / 安全性：把 execution_unit、must_haves、verification 和 stop_conditions 前移到 HILP 蓝图与交接阶段。
- 可回退性：全部为 Markdown reference 与模板改动，不引入 runtime。
- 改动范围：只修改两个 Skill 的 `SKILL.md` 与若干 `references/*.md`。
- 可维护性：细节放入 references，`SKILL.md` 只保留加载规则。

## 批准记录

用户批准语句：

> 批准推荐方案 C：五项轻量治理增强方案

批准日期：2026-05-02
