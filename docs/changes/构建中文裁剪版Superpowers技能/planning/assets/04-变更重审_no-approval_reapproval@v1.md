---
asset_id: hilp-superpowers-skills-reapproval
artifact_name: stage-reapproval/reapproval-decision
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-reapproval
created_from: stage-3/design-choice@v1
last_event: new-facts-before-approval
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/04-变更重审_no-approval_reapproval@v1.md
---

# 变更重审阶段

## 这个阶段要做什么
当旧方案被新事实影响时，先判断哪些内容还能继续用，哪些必须回退修订。

## 当前裁决完整性
- 当前裁决类型：完整。
- 缺失输入：无影响重审判断的缺失输入。
- 缺失输入是否阻止最终判断：否。

## 发生了什么变化
- 变化 1：用户要求裁剪后的技能包不要再命名为 `superpowers-skills`，虽然其来源是 Superpowers 的裁剪与汉化。
- 变化 2：当前仓库只是 skill 管理仓库，仓库内 skill 不需要被 agents 自动发现；真实使用时会由用户让 agent 从仓库安装。
- 变化 3：用户通常在使用 HILP 之前已经手动创建 worktree，因此裁剪后的技能包不需要保留 `using-git-worktrees` 相关能力。

## 影响优先级
1. 技能包命名与目录命名影响后续所有正式蓝图路径，必须修订设计。
2. 自动发现假设影响安装说明和 README 边界，必须从设计中移除。
3. `using-git-worktrees` 原本列入执行主链路，现在应从保留清单中删除。

## 受影响资产
- 资产：`stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`
- 原状态：`ready-for-approval｜中文状态=待审批`
- 新状态：`needs-revision｜中文状态=待修订`
- 变化原因：用户新增事实改变了技能包名称、安装发现边界和保留技能清单。
- 分层蓝图包影响：无；尚未进入实施蓝图阶段。

## 回退判断
- 最近受影响的上游阶段：方案设计与审批阶段。
- 必须回退的原因：设计结论和审批对象已变化，不能继续批准旧版本 `stage-3/design-choice@v1`。

## 治理强度变化
- 是否升级：否。
- 是否降级：否。
- 新治理模式：standard。
- 是否需要补齐新增控制件：否。

## 当前还能继续做什么
- 当前允许：基于新事实生成 `stage-3/design-choice@v2`，重新提交审批。
- 当前禁止：禁止基于旧的 `superpowers-skills/` 命名、自动发现假设或保留 worktree 技能进入实施蓝图。
- 当前阻断项：无阻断项；但旧设计资产不得继续作为审批对象。

## 下一步
- 下一阶段：方案设计与审批阶段。
- 原因：受影响的是设计边界和保留/删除清单，需要形成修订后的可审批设计资产。