asset_id: hilp-execution-capability-restoration-reapproval-v1
artifact_name: stage-reapproval/reapproval-decision
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-reapproval
created_from: stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]
last_event: new-fact-original-examples-confirmed
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批

# 变更重审阶段

## 这个阶段要做什么

当旧补强建议被新事实影响时，先判断哪些内容还能继续用，哪些必须进入新版补强方案。

## 已保存资产

- 文件路径：`docs/hilp/补回human-in-loop-execution能力/04-变更重审_no-approval_reapproval@v1.md`
- asset_ref：`stage-reapproval/reapproval-decision@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（`archived`）
- 当前是否需要审批：无需审批；本资产只记录重审裁决。

## 当前裁决完整性

- 当前裁决类型：完整。
- 缺失输入：无。
- 缺失输入是否阻止最终判断：否。

## 发生了什么变化

- 变化 1：用户确认只继续补强此前三项建议中的第 1 项和第 2 项。
- 变化 2：第 3 项是否纳入取决于原版事实：TDD、调试、测试反模式原版是否存在代码示例。
- 变化 3：已核查原版确实存在代码示例，并保存报告：`docs/review/核查Superpowers原版代码示例-2026-04-29 11-13-23.md`。

## 影响优先级

1. 新事实确认第 3 项可以纳入补强范围。
2. 已批准旧补强链路仍可作为基础，但需要新一版设计方案覆盖增量补强。
3. 执行前必须重新形成新版待审批方案，不能直接沿旧执行交接扩大范围。

## 受影响资产

- 资产：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
  - 原状态：`approved｜中文状态=已批准`
  - 新状态：保持已批准。
  - 变化原因：旧设计仍作为基础方向有效。
  - 分层蓝图包影响：旧蓝图包可作为历史基线，但新版增量补强需另行审批。
- 资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
  - 原状态：`approved｜中文状态=已批准`
  - 新状态：保持已批准，作为已完成基线。
  - 变化原因：新请求是追加二次补强，不推翻旧蓝图。
  - 分层蓝图包影响：无须标记旧包失效；新方案批准后再生成 v2 或增量蓝图。
- 资产：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
  - 原状态：`archived｜中文状态=已归档`
  - 新状态：保持已归档。
  - 变化原因：旧执行交接已闭环，新请求应走新一轮补强链。

## 回退判断

- 最近受影响的上游阶段：方案设计与审批阶段。
- 必须回退的原因：用户重新裁定补强范围，并有新事实支持第 3 项纳入，需要形成新版可审批设计方案。

## 治理强度变化

- 是否升级：否。
- 是否降级：否。
- 新治理模式：standard。
- 是否需要补齐新增控制件：需要新版方案设计资产；批准后再生成实施蓝图。

## 当前还能继续做什么

- 当前允许：制定最新版补强方案，提交用户审批。
- 当前禁止：未获批准前直接修改 `human-in-loop-execution/` 文件或扩大旧执行交接范围。
- 当前阻断项：无阻断项，但需要用户审批新版方案后才能进入蓝图。

## 下一步

- 下一阶段：方案设计与审批阶段。
- 原因：需要把“补强 1、2，并基于原版事实纳入 3”的范围形成新的审批资产。
