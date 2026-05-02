---
asset_id: hilp-hile-boundary-correction-design-choice-v1
artifact_name: stage-3/design-choice
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-reapproval/reapproval-decision@v1
last_event: human-approval-granted
last_decision: human-approval-boundary-correction-design-choice-v1-2026-05-02
approval_marker: approved
approval_marker_label: 已批准
asset_path: docs/changes/修正HILP-HILE执行边界/planning/assets/02-方案设计_design-choice@v1.md
asset_link: [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
---

# 方案设计与审批阶段

## asset_ref

`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`

## 当前状态

已批准。

## 当前是否需要审批

已批准，无需继续审批；可进入实施蓝图阶段。

## 设计目标

把现有“`execution_unit` + HILE 执行计划”边界修正为更清晰的二分模型：

- HILP 负责在执行交接阶段输出 `Execution Plan Contract`，它是执行计划 / 运行手册的上游契约。
- HILE 负责生成 `Execution Runbook`，它是基于 contract 和当前工作区生成的执行实例，不是规划资产。

## 推荐方案：方案 C，Contract / Runbook 二分修正方案

### 核心思路

1. 在 HILP 侧引入 `Execution Plan Contract` 作为执行交接阶段的稳定输出结构。
2. 将 contract 顶层固定为：

```yaml
execution_plan_contract:
  execution_scope: whole-package
  execution_mode: single-agent-serial
  units:
    - unit_id: EU-001
      title: <title>
      order: 1
      depends_on: []
      allowed_files: []
      forbidden_files: []
      context_packet: {}
      must_haves:
        truths: []
        artifacts: []
        key_links: []
      verification:
        static_checks: []
        commands: []
        human_checks: []
      stop_conditions: []
      completion_outputs:
        - unit_summary
        - execution_ledger_update
```

3. 要求 HILP 保证 contract 内容确定、唯一、无待定项，并绑定已批准设计和已批准蓝图。
4. 将 HILE 生成物语义从“执行计划”收窄为 `Execution Runbook`。
5. 明确 HILE 只能读取 contract、核对当前工作区、把每个 unit 转为操作步骤、列出当前环境可运行的验证命令、保存 runbook、停止等待用户确认。
6. 明确 HILE 不得新增 unit、改变顺序、扩大 `allowed_files`、新增 forbidden_files 之外的例外、改变 must_haves、替换 verification 口径或改变 stop_conditions。

### 为什么推荐

该方案最贴合用户提出的边界，同时保持现有 HILP / HILE 的核心气质：Markdown 协议、人工门控、资产审计、按需加载、不引入 runtime 平台。它修正职责命名和契约字段，不扩张为 CLI、dashboard、自动调度或执行引擎。

## 备选方案

### 方案 A：只做术语改名

- 核心思路：把“执行计划”改名为“运行手册”，但不引入 `execution_plan_contract` 顶层结构。
- 优点：改动最小。
- 代价：无法解决字段缺失和上游 contract 不完整的问题。
- 不选原因：审查报告指出的核心风险是边界与字段契约不完整，单纯改名不足以防止 HILE 被理解为规划层。

### 方案 B：引入可执行 contract 校验 runtime

- 核心思路：为 `execution_plan_contract` 增加脚本、CLI 或 runtime 校验器。
- 优点：自动化校验更强。
- 代价：违反本轮边界，不符合“不引入 runtime、CLI、auto loop”的约束。
- 不选原因：本次需求是 Skill 协议层修正，不是平台工程建设。

## 关键取舍

- 正确性 / 安全性：把执行边界固定在 HILP contract 中，HILE 只能实例化 runbook，降低执行阶段补规划的风险。
- 可回退性：只修改 Markdown Skill 协议和 reference 规则，不引入不可逆 runtime 机制。
- 改动范围：仅限 `human-in-loop-planning` 与 `human-in-loop-execution` 相关 Skill 文档和 references；不修改其他 Skill。
- 可维护性：用 `Execution Plan Contract` 与 `Execution Runbook` 两个稳定术语分离上游契约和下游执行实例，减少未来 agent 误读。
- 未来扩展性：后续若要自动校验，可在新需求中基于 contract 另行设计；本轮不预留运行时入口。

## 需要用户决定什么

- 是否存在：无必须人工裁决。
- 是否会阻止继续：无阻断项。
- 问题描述：本设计推荐采用 Contract / Runbook 二分模型。
- 可选项：方案 A 只改名；方案 B 引入 runtime；方案 C Contract / Runbook 二分修正。
- 建议：批准方案 C。
- 默认路径：无。
- 用户是否已选择：已选择。
- 不得写成既定事实的内容：无；用户已批准方案 C。

## 当前状态

- 中文状态名：已批准。
- 内部状态值：`approved`。
- 进入该状态的理由：用户明确批准 `stage-3/design-choice@v1`，采用方案 C：Contract / Runbook 二分修正方案。

## 下一步

- 下一阶段：实施蓝图阶段。
- 继续前提：基于本已批准设计生成确定、唯一、可审批的实施蓝图。
- 当前阻断项：无阻断项。

## 批准记录

用户批准语句：

> 准 stage-3/design-choice@v1，采用方案 C：Contract / Runbook 二分修正方案。

批准日期：2026-05-02
