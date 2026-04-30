---
asset_id: hilp-asset-dir-exec-confirm-requirements-facts-v1
artifact_name: stage-1-2/requirements-and-facts
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-requirements-facts
created_from: stage-0/routing@v1
last_event: none
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/改进HILP资产目录与执行确认/planning/assets/01-需求对齐与事实求证_requirements-and-facts@v1.md
asset_link: [01-需求对齐与事实求证_requirements-and-facts@v1.md](./01-需求对齐与事实求证_requirements-and-facts@v1.md)
---

# 需求对齐与事实求证阶段

## 这个阶段要做什么
先把用户期望和仓库当前真实情况分开，避免基于猜测设计资产路径和执行确认门槛。

## 需求对齐
- 目标：改进 `human-in-loop-planning` 与 `human-in-loop-execution`，让规划资产和执行资产使用不同但具有关联命名的文件夹，并让执行层写完执行计划后等待用户确认再执行。
- 范围：
  - 规划 skill 的资产落盘路径规则与相关引用规则。
  - 执行 skill 的计划保存路径规则与执行启动纪律。
  - 两个 skill 之间关于 HILP 资产和执行计划的交互说明。
  - 文档中会导致新资产继续落到旧路径或计划写完即执行的规则。
- 非目标：
  - 不迁移、重命名或删除既有历史资产。
  - 不引入与规划 skill 同等复杂的执行计划审批状态机。
  - 不改变 HILP 设计、蓝图、执行交接的审批语义。
  - 不实现业务代码变更。
- 成功标准：
  - 新规划资产默认保存到体现“规划”的文件夹。
  - 新执行计划默认保存到体现“执行”的文件夹。
  - 两个文件夹名称有共同前缀，且通过不同后缀区分规划与执行。
  - 执行 skill 在生成计划后输出确认提示并停止，不直接执行任务、派发 agent 或修改代码。
  - 用户明确确认执行后，执行 skill 才进入后续执行阶段。
  - 旧资产路径仍可作为历史输入被读取，不被要求迁移。
- 显式约束：
  - 新规则必须保持 Markdown 链接可点击。
  - 执行确认门槛只做轻量确认，不维护规划式状态机。
  - 从实施蓝图阶段开始仍遵守确定性纪律。
- 待确认项：用户是否接受推荐文件夹命名 `docs/hilp-planning/` 与 `docs/hilp-execution/`。

## 事实求证
- 已知事实：
  - `human-in-loop-planning/SKILL.md` 当前规定规划资产保存到 `项目根目录/docs/hilp/变更概述/`。
  - `human-in-loop-planning/references/handoff-contracts.md` 同样规定规划资产保存到 `项目根目录/docs/hilp/变更概述/`。
  - `human-in-loop-execution/SKILL.md` 当前规定执行计划保存到 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - `human-in-loop-execution/references/writing-plans.md` 当前规定生成计划后输出已保存路径、任务摘要、绑定 asset_ref、自检结果和推荐执行方式，但没有明确“写完计划后必须等待用户确认”。
- 证据来源：
  - [human-in-loop-planning/SKILL.md](../../../../../human-in-loop-planning/SKILL.md)
  - [human-in-loop-planning/references/handoff-contracts.md](../../../../../human-in-loop-planning/references/handoff-contracts.md)
  - [human-in-loop-execution/SKILL.md](../../../../../human-in-loop-execution/SKILL.md)
  - [human-in-loop-execution/references/writing-plans.md](../../../../../human-in-loop-execution/references/writing-plans.md)
- 关键未知项：
  - 是否必须迁移旧资产：按用户描述未要求，且为降低风险，设计默认不迁移。
  - 是否要对执行计划建立审批资产：用户明确“不像 planning 一样用一套状态机维护”，因此默认不建立审批资产。
- 初步影响面：
  - 规划 skill：`SKILL.md`、`references/handoff-contracts.md`、`references/event-action-rules.md`，以及所有写死 `docs/hilp/` 规划资产根路径的参考文件。
  - 执行 skill：`SKILL.md`、`references/writing-plans.md`、可能涉及执行路由或执行入口说明的参考文件。
  - 仓库文档：README 或示例中若引用旧路径，需要同步判断是否仅保留历史说明或更新为新默认。

## 当前判断
- 是否有事实缺口会阻止继续：无阻断项。
- 是否建议提高治理强度：保持 standard；没有发现需要 strict 的兼容窗口、发布切换或回滚安全要求。
- 当前是否足以进入方案设计：足以。
- 当前状态：已归档（`archived`）。
- 若不足，缺的是什么：无。

## 下一步需要用户做什么
进入方案设计与审批阶段，审阅并批准推荐命名与执行确认策略，或要求修订命名方案。
