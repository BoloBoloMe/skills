---
asset_id: hilp-archive-requirements-and-facts
artifact_name: stage-1-2/requirements-and-facts
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-requirements-facts
created_from: stage-0/routing@v1 [state=archived｜中文状态=已归档]
last_event: none
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/改进HILP规划资产归档/planning/assets/01-需求事实_no-approval_requirements-and-facts@v1.md
---

# 需求对齐与事实求证阶段

## 这个阶段要做什么
先把“想达到什么”和“现在真实情况是什么”分开，避免基于猜测设计归档阶段。

## 需求对齐
- 目标：在执行交接成功后自动生成规划资产归档索引，解决当前变更目录内 HILP 文档多版本混杂导致的阅读混乱。
- 范围：
  - 新增用户可见阶段：规划资产归档阶段。
  - 新增内部模块：`hilp-archive`。
  - 新增资产：`stage-7/archive-manifest@vN`。
  - 新增文件：`references/archive.md`。
  - 更新主入口、交接契约、事件动作规则、路由矩阵和执行交接相关规则，使执行交接成功后自动归档。
  - 增加归档 manifest 模板、入口条件、失败条件、阅读角色和手动重新触发规则。
- 非目标：
  - 不移动既有文件。
  - 不生成 `CURRENT.md`。
  - 不修改上游资产状态。
  - 不把已批准资产改为已归档。
  - 不新增设计判断、蓝图约束或执行交接范围。
  - 不治理当前变更目录之外的资产。
  - 不验证真实代码执行结果。
- 成功标准：
  - 执行交接成功后可自动生成 `06-规划资产归档_no-approval_archive-manifest@vN.md`。
  - 归档 manifest 只治理当前变更目录，外部引用仅记录为 `external-reference`。
  - manifest 能明确最终阅读入口、最终有效资产、支撑上下文、历史过程资产、待修订历史和后续重审入口。
  - 归档失败不阻断执行交接，并明确报告失败原因。
  - 手动重新触发归档可以基于有效执行交接资产生成新版本 manifest，且不覆盖旧 manifest。
  - 所有新增规则不破坏现有审批语义：`ready-for-approval` 仍不等于 `approved`，蓝图和交接门槛不降低。
- 显式约束：
  - 归档成功时默认只在执行交接回复末尾简短展示。
  - 归档失败时详细说明失败原因和影响。
  - 阅读角色以最终执行交接资产的引用链为准，而不是简单按最高版本判断。
  - `needs-revision` 资产优先标为 `needs-revision-history`。
  - 多个候选执行交接资产无法唯一确定最终链时，归档失败但不阻断交接。
- 待确认项：无阻断性待确认项。需要用户在方案设计阶段明确批准具体设计资产后，才能进入实施蓝图阶段。

## 事实求证
- 已知事实：
  - 当前 HILP 已有 `archived` 状态和 `archived` 审批标记，但缺少执行交接后的正式归档阶段。
  - 当前阶段前缀已有 `00` 到 `05`，`90` 用于协议压力测试。
  - 当前用户可见阶段列表不包含规划资产归档阶段。
  - 当前允许交接关系中，`hilp-execution-handoff` 允许交给外部执行层、实施蓝图阶段或变更重审阶段，不包含归档阶段。
  - 当前资产落盘规则要求阶段资产保存到 `docs/hilp/变更概述/`。
  - 当前执行交接阶段要求绑定已批准且通过确定性检查的蓝图，并且无阻断项。
- 证据来源：
  - `human-in-loop-planning/SKILL.md`
  - `human-in-loop-planning/references/event-action-rules.md`
  - `human-in-loop-planning/references/handoff-contracts.md`
  - `human-in-loop-planning/references/routing-matrix.md`
  - `human-in-loop-planning/references/execution-handoff.md` 的现有职责边界需要在蓝图阶段进一步读取并纳入修改范围。
  - 本次讨论已确认的用户决策。
- 关键未知项：
  - 具体每个文件的精确改动位置需在实施蓝图阶段逐项列出。
  - 是否需要为压力测试补充新场景，设计阶段建议纳入，蓝图阶段确定具体样例。
- 初步影响面：
  - 主入口说明：模块列表、资源加载顺序、阶段名称、阶段前缀、路由与输出纪律。
  - 交接契约：允许关系、最小输入契约、最小输出契约、禁止交接清单。
  - 事件动作规则：自动归档事件、失败处理、资产状态不变规则。
  - 路由矩阵：用户可见阶段名称和默认映射。
  - 新模块参考文件：归档工作流和模板。
  - 执行交接参考文件：成功输出后追加归档摘要。
  - 协议压力测试参考文件：覆盖自动归档、失败归档、手动归档和多候选链路。

## 当前判断
- 是否有事实缺口会阻止继续：无阻断项。
- 是否建议提高治理强度：保持 standard。
- 当前是否足以进入方案设计：是。
- 当前状态：已归档（内部状态值：`archived`）。
- 若不足，缺的是什么：无。

## 下一步需要用户做什么
进入方案设计与审批阶段，审查推荐方案并明确是否批准具体设计资产。
