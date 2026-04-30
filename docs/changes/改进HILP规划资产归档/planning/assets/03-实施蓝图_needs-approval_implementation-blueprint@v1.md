---
asset_id: hilp-archive-implementation-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/changes/改进HILP规划资产归档/planning/assets/03-实施蓝图_needs-approval_implementation-blueprint@v1.md
---

# 实施蓝图阶段

## 这个阶段要做什么
把已批准的方案转成可执行的改动切片、顺序、约束和验证检查点。

## 已保存资产
- 文件路径：`D:/Workspace/skills/docs/changes/改进HILP规划资产归档/planning/assets/03-实施蓝图_needs-approval_implementation-blueprint@v1.md`
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`
- 蓝图形式：单体蓝图。
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 当前状态：待审批（内部状态值：`ready-for-approval`）。
- 当前是否需要审批：需要用户明确批准当前蓝图版本。

## 改动拓扑
- 改动切片：
  1. 主入口规则切片：修改 `human-in-loop-planning/SKILL.md`，加入 `hilp-archive`、规划资产归档阶段、阶段前缀 `06`、资源加载项、路由决策树自动归档规则、参考文件索引和输出纪律补充。
  2. 事件规则切片：修改 `human-in-loop-planning/references/event-action-rules.md`，加入“执行交接完成后自动归档”事件、归档失败不阻断交接、归档不改写上游资产状态和归档资产版本规则。
  3. 交接契约切片：修改 `human-in-loop-planning/references/handoff-contracts.md`，加入 `hilp-execution-handoff -> hilp-archive`、`hilp-archive` 允许关系、最小输入契约、最小输出契约、文件前缀 `06` 和禁止事项。
  4. 路由矩阵切片：修改 `human-in-loop-planning/references/routing-matrix.md`，加入用户可见阶段名称和下一跳默认映射中的归档规则。
  5. 执行交接切片：修改 `human-in-loop-planning/references/execution-handoff.md`，在工作流和输出模板中加入执行交接成功后的自动归档摘要与失败说明边界。
  6. 归档模块切片：新增 `human-in-loop-planning/references/archive.md`，定义归档模块职责、入口条件、失败条件、手动触发规则、阅读角色判定算法、输出模板和硬约束。
  7. 压力测试切片：修改 `human-in-loop-planning/references/skill-pressure-test.md`，加入自动归档成功、自动归档失败、手动重新归档和多候选执行交接链不唯一的测试场景。
- 依赖顺序：
  1. 先新增 `references/archive.md`，固定归档阶段的完整契约。
  2. 再更新 `handoff-contracts.md`，把归档模块纳入交接关系和契约。
  3. 再更新 `event-action-rules.md`，加入自动归档事件和失败处理。
  4. 再更新 `routing-matrix.md` 和 `SKILL.md`，把阶段名称、文件前缀、资源加载和下一跳规则暴露到总入口。
  5. 再更新 `execution-handoff.md`，把执行交接成功后的自动归档结果接入输出。
  6. 最后更新 `skill-pressure-test.md`，增加回归场景。
- 风险检查点：
  1. 检查归档阶段没有降低蓝图和执行交接入口门槛。
  2. 检查归档失败规则明确写为不阻断已完成执行交接。
  3. 检查归档 manifest 规则没有要求移动文件、覆盖旧文件或生成 `CURRENT.md`。
  4. 检查 `approved` 资产在归档后仍保持 `approved`。
  5. 检查手动重新归档仍要求有效执行交接资产。
- 发布检查点：
  1. 所有规则文件修改完成后一次性提交给验证步骤。
  2. 验证通过后进入执行交接阶段。
  3. 执行交接完成后按新增规则生成规划资产归档 manifest。
- 验证检查点：
  1. 使用 `rg "hilp-archive|规划资产归档阶段|archive-manifest|stage-7/archive-manifest" human-in-loop-planning` 检查新增术语覆盖。
  2. 使用 `rg "CURRENT.md" human-in-loop-planning` 检查仅存在禁止生成 `CURRENT.md` 的规则，不存在要求创建该文件的规则。
  3. 使用 `rg "执行交接完成后自动归档|归档失败不阻断执行交接|external-reference|needs-revision-history" human-in-loop-planning/references` 检查关键规则落点。
  4. 人工阅读 `SKILL.md`、`handoff-contracts.md`、`event-action-rules.md`、`archive.md`，确认阶段门控和审批边界一致。
- 涉及模块 / 子系统 / 文件范围：
  - `human-in-loop-planning/SKILL.md`
  - `human-in-loop-planning/references/event-action-rules.md`
  - `human-in-loop-planning/references/handoff-contracts.md`
  - `human-in-loop-planning/references/routing-matrix.md`
  - `human-in-loop-planning/references/execution-handoff.md`
  - `human-in-loop-planning/references/skill-pressure-test.md`
  - `human-in-loop-planning/references/archive.md`

## 分层蓝图包 manifest
- 使用条件：无，本次使用单体蓝图。
- 包内资产清单：无。
- 切片索引：无。
- 跨切片依赖图 / 波次：无。
- 覆盖矩阵：无。
- 审批边界：本蓝图审批仅覆盖 `stage-4-5/implementation-blueprint@v1` 中列出的七个文件范围和验证步骤。

## 实现约束
- 数据形状：
  - 新增资产引用格式固定为 `stage-7/archive-manifest@vN [state=archived｜中文状态=已归档]`。
  - 归档文件名固定为 `06-规划资产归档_no-approval_archive-manifest@vN.md`。
  - 归档 manifest 元数据必须使用 `owner_skill=hilp-archive`、`state=archived`、`state_label=已归档`、`approval_marker=no-approval`、`approval_marker_label=无需审批`。
  - 阅读角色集合固定为 `final-entry`、`active-baseline`、`supporting-context`、`superseded`、`process-only`、`needs-revision-history`、`archive-index`、`external-reference`。
- 接口约束：
  - `hilp-execution-handoff` 成功后自动尝试交给 `hilp-archive`。
  - `hilp-archive` 不交给新的业务阶段；它作为本轮规划链闭环。
  - 手动触发归档入口接受用户指定的有效执行交接资产，或当前变更目录中可唯一识别的有效执行交接资产。
  - 外部引用资产只进入“外部引用资产”章节，并标为 `external-reference`。
- 局部算法骨架：
  1. 枚举当前变更目录内 HILP 资产文件。
  2. 识别有效执行交接资产：`owner_skill=hilp-execution-handoff`、artifact 为 `stage-6/execution-handoff`、无阻断项、执行入口检查已通过、绑定已批准设计和已批准蓝图。
  3. 当存在用户指定执行交接资产时，只验证该资产；当没有用户指定时，要求候选最终执行交接链唯一。
  4. 从最终执行交接资产提取引用链：执行交接、实施蓝图、方案设计、需求事实、路由和重审记录。
  5. 标注当前 manifest 为 `archive-index`。
  6. 标注最终执行交接资产为 `final-entry`。
  7. 标注最终链中的设计、蓝图和交接资产为 `active-baseline`。
  8. 标注状态为 `needs-revision` 的当前目录资产为 `needs-revision-history`。
  9. 标注被最终链中更高版本替代的同 artifact 旧版本为 `superseded`。
  10. 标注最终链引用的事实、路由和重审资产为 `supporting-context`。
  11. 标注其余当前目录资产为 `process-only`。
  12. 标注目录外引用资产为 `external-reference`。
  13. 写入新版本 `archive-manifest@vN`，不覆盖旧 manifest。
- 错误处理要求：
  - 找不到有效执行交接资产时，不生成归档 manifest，并报告失败原因。
  - 多个候选执行交接资产无法唯一确定最终链时，不生成归档 manifest，并报告失败原因。
  - 当前变更目录无法枚举时，不生成归档 manifest，并报告失败原因。
  - manifest 写入失败时，不声称归档完成，并报告写入失败。
  - 归档失败不改变执行交接资产、设计资产和蓝图资产状态。
- 测试承诺：
  - 静态检查所有新增术语的引用完整性。
  - 静态检查交接契约中存在 `hilp-execution-handoff -> hilp-archive`。
  - 静态检查 `archive.md` 同时覆盖自动归档、手动归档、失败处理和阅读角色。
  - 人工核对执行交接输出模板包含成功简短展示和失败详细说明。
  - 人工核对压力测试模块包含归档相关场景。

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无。

## 当前判断
- 当前是否可交接到执行层：否。蓝图仍处于待审批状态，必须先获得用户明确批准。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：无兼容窗口；回滚边界为仅修改 Markdown 规则文件和新增一个 Markdown 参考文件，执行层可通过版本控制撤销本蓝图列出的文件改动。
- 当前状态：待审批（内部状态值：`ready-for-approval`）。

## 下一步需要用户做什么
请明确批准当前蓝图资产版本：

`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`

批准后才能进入执行交接阶段；未批准前不得修改真实 skill 文件。
