---
asset_id: hilp-archive-execution-handoff
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: human-approval-2026-04-28-hilp-archive-blueprint-v1
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/hilp/改进HILP规划资产归档/05-执行交接_no-approval_execution-handoff@v1.md
---

# 执行交接阶段

## 这个阶段要做什么
把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产
- 文件路径：`D:/Workspace/skills/docs/hilp/改进HILP规划资产归档/05-执行交接_no-approval_execution-handoff@v1.md`
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）。
- 当前是否需要审批：无需审批；该交接绑定已批准蓝图。

## 上游资产
- 已批准需求边界：`stage-1-2/requirements-and-facts@v1 [state=archived｜中文状态=已归档]`
- 已批准设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图。
- 分层蓝图包 manifest：无。
- 当前蓝图版本：v1。

## 执行范围
- 范围类型：整包。
- 改动切片：
  1. 更新 `human-in-loop-planning/SKILL.md`。
  2. 更新 `human-in-loop-planning/references/event-action-rules.md`。
  3. 更新 `human-in-loop-planning/references/handoff-contracts.md`。
  4. 更新 `human-in-loop-planning/references/routing-matrix.md`。
  5. 更新 `human-in-loop-planning/references/execution-handoff.md`。
  6. 新增 `human-in-loop-planning/references/archive.md`。
  7. 更新 `human-in-loop-planning/references/skill-pressure-test.md`。
- 依赖顺序：先新增归档参考文件，再更新交接契约和事件规则，再更新总入口、路由矩阵和执行交接模板，最后更新压力测试样例。
- 禁止越界项：
  - 不修改本清单之外的真实 skill 文件。
  - 不移动既有 HILP 资产文件。
  - 不生成 `CURRENT.md`。
  - 不把上游 approved 资产改成 archived。
  - 不新增未在蓝图中批准的归档行为。

## 必须遵守的实现约束
- 接口约束：`hilp-execution-handoff` 成功后自动尝试进入 `hilp-archive`；`hilp-archive` 作为规划链闭环，不交给新的业务阶段。
- 数据形状：归档资产使用 `stage-7/archive-manifest@vN [state=archived｜中文状态=已归档]`；文件名使用 `06-规划资产归档_no-approval_archive-manifest@vN.md`。
- 错误处理：归档失败不阻断执行交接，必须报告失败原因，不得声称归档完成。
- 测试承诺：执行后进行关键术语静态检查和人工核对。

## 风险与验证
- 风险检查点：
  - 阶段门控不能被归档阶段绕过。
  - 归档不能改变审批语义。
  - 手动归档不能跳过有效执行交接资产验证。
- 发布 / 验证检查点：
  - 执行文件修改。
  - 运行 `rg` 静态检查。
  - 人工检查新增归档规则覆盖入口、输出、失败和重触发。

## 执行模式
- 单代理。
- 选择原因：变更范围是 Markdown 规则文件，文件边界明确，无需多代理分工。

## 执行入口检查
- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：执行者只能按本交接资产和已批准蓝图修改列出的文件。
- 停止并回退条件：发现需要修改蓝图未列出的文件、需要新增未批准行为、或发现现有规则与蓝图冲突且无法按蓝图唯一处理时，停止执行并回到实施蓝图阶段或变更重审阶段。

## 规划资产归档
- 自动归档结果：已完成。
- 文件路径：`D:/Workspace/skills/docs/hilp/改进HILP规划资产归档/06-规划资产归档_no-approval_archive-manifest@v1.md`
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。
