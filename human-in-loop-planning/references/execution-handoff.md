# 执行交接模块

## 模块元信息
- internal_module: `hilp-execution-handoff`
- 原触发描述：用于在规划完成后，把已明确 已批准的蓝图资产安全交接给执行层。只有在存在完整 blueprint asset_ref、owner_skill=hilp-blueprint、state=approved（已批准）、last_decision 为 人工批准授予（Human Approval Granted） 决策，且上游已批准设计资产 仍有效、无未解决阻断项时才应触发。若蓝图只是 draft（草稿）或 ready-for-approval（待审批）、缺少批准资产引用、仍缺关键内容，或执行中暴露出上游失效，不要继续交接，应回到 hilp-blueprint 或 hilp-reapproval。

# 概览

你负责规划层到执行层的交接。
你不直接执行代码，只负责把执行边界讲清楚。

你必须整理：
- 上游已批准资产
- 改动切片
- 实现约束
- 风险检查点
- 验证承诺
- 下一执行模式

你不负责：
- 不重写规划内容
- 不修订蓝图
- 不绕过未决阻断项

## 极简工作流

进入本模块前必须同时存在完整蓝图资产引用和仍有效的上游设计资产引用：

```text
asset_ref: stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]
owner_skill: hilp-blueprint
last_decision: <human approval decision-id>
upstream_design_ref: stage-3/design-choice@vM [state=approved｜中文状态=已批准]
```

若缺少上述任一项，不得仅凭“蓝图已经写完”“可以开工”“按这个执行”等自然语言判断进入执行交接；必须回到 `hilp-blueprint` 补齐或等待审批，或交给 `hilp-reapproval` 裁决。

1. 读取完整的 `approved`（已批准）蓝图资产引用。
2. 检查上游设计资产仍为 `approved`（已批准），且未被新事件标记为 `needs-revision`（待修订）或 `archived`（已归档）。
3. 检查蓝图资产是否完整包含 改动切片、依赖顺序、风险检查点、发布 / 验证检查点、接口约束、数据形状与测试承诺。
4. 整理执行所需最小包。
5. 明确执行模式。
6. 输出交接摘要。
7. 若发现前提不稳，回退到 `hilp-reapproval` 或 `hilp-blueprint`。

交接契约见 `references/handoff-contracts.md`。
事件规则见 `references/event-action-rules.md`。

## 输出模板

# 执行交接阶段

## 这个阶段要做什么
- 用一句话说明：把已批准蓝图整理成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产
- 文件路径：`项目根目录/hilp/变更概述/05-执行交接_<审批标记>_execution-handoff@vN.md`
- asset_ref：`stage-6/execution-handoff@vN [state=<state>｜中文状态=<state_label>]`
- 当前状态：必须写中文状态名，必要时附内部状态值。
- 当前是否需要审批：通常绑定已批准蓝图；若仍有阻断项，说明不能交接执行，并写明“有阻断项”。

## 上游资产
- 已批准需求边界：
- 已批准设计：必须使用 `stage-3/design-choice@vM [state=approved｜中文状态=已批准]` 格式。
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]`
- 当前蓝图版本：

## 执行范围
- 改动切片：
- 依赖顺序：
- 禁止越界项：

## 必须遵守的实现约束
- 接口约束：
- 数据形状：
- 错误处理：
- 测试承诺：

## 风险与验证
- 风险检查点：
- 发布 / 验证检查点：

## 执行模式
- 人类开发者 / 单代理 / 多代理 / 暂不执行
- 选择原因：

## 当前阻断项
- 若无，写“无阻断项”。
- 若有，写“有阻断项”，并说明缺什么、为什么不能交接执行。

## 硬约束

- 缺少 `stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]` 时，不得交接到执行层。
- 蓝图资产的 `owner_skill` 不是 `hilp-blueprint` 或缺少 `last_decision` 时，不得交接到执行层。
- 上游 Stage 3 设计资产不是 `approved`（已批准），或已进入 `needs-revision`（待修订） / `archived`（已归档）时，不得交接到执行层。
- `human_decision_required`（必须人工裁决）未完成时，不得交接到执行层。
- 不得把交接说明写成实现代码。
- 不得把交接阶段变成新的设计阶段。
- 不得默认“规划完成就必须立刻执行”。

## 交接规则

- 蓝图资产为 `draft`（草稿）、`ready-for-human-decision`（待人工裁决）、`ready-for-approval`（待审批）、`needs-revision`（待修订）或 `archived`（已归档）时，禁止交接到执行层。
- 缺少必要蓝图细节但上游仍稳定时，回交 `hilp-blueprint`。
- 暴露出上游资产失效、治理升级或新的 必须人工裁决的决策点时，交给 `hilp-reapproval`。
