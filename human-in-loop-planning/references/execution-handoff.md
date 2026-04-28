# 执行交接模块

## 模块元信息
- internal_module: `hilp-execution-handoff`
- 原触发描述：用于在规划完成后，把已明确 已批准且通过确定性检查的蓝图资产安全封装为执行入口。只有在存在完整 blueprint asset_ref、owner_skill=hilp-blueprint、state=approved（已批准）、last_decision 为 人工批准授予（Human Approval Granted） 决策，上游已批准设计资产仍有效、确定性检查已通过、执行范围与执行模式已确定且无未解决阻断项时才应触发。若蓝图只是 draft（草稿）或 ready-for-approval（待审批）、缺少批准资产引用、仍缺关键内容、含有未确定项、执行范围或执行模式未定，或执行中暴露出上游失效，不要继续交接，应回到 hilp-blueprint 或 hilp-reapproval。若蓝图是分层蓝图包，必须先确认主蓝图 / manifest 与全部包内成员均已批准且版本一致。

# 概览

你负责规划层到执行层的交接。
你不直接执行代码，也不重新规划；只负责把已批准蓝图封装成执行者可以遵守的执行入口。

你必须整理：
- 上游已批准资产
- 已批准蓝图版本；若是分层蓝图包，必须整理主蓝图 / manifest 和固定版本包内资产清单
- 从蓝图摘录的改动切片、实现约束、风险检查点和验证承诺
- 执行范围：整包、发布波次或 manifest 中已定义的切片集合
- 执行模式
- 开始前合法性检查
- 禁止越界项
- 停止并回退条件

你不负责：
- 不重写规划内容
- 不修订蓝图
- 不补齐蓝图缺口
- 不解释性扩展蓝图
- 不绕过未决阻断项

## 极简工作流

进入本模块前必须同时存在完整蓝图资产引用和仍有效的上游设计资产引用：

```text
asset_ref: stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]
owner_skill: hilp-blueprint
last_decision: <human approval decision-id>
upstream_design_ref: stage-3/design-choice@vM [state=approved｜中文状态=已批准]
determinism_check: passed
execution_scope: <整包 | 发布波次 | manifest 中已定义的切片集合>
execution_mode: <人类开发者 | 单代理 | 多代理 | 暂不执行>
```

若缺少上述任一项，不得仅凭“蓝图已经写完”“可以开工”“按这个执行”等自然语言判断进入执行交接；必须回到 `hilp-blueprint` 补齐或等待审批，或交给 `hilp-reapproval` 裁决。执行交接不得自行补写缺失的蓝图内容。

1. 读取完整的 `approved`（已批准）蓝图资产引用。
2. 检查上游设计资产仍为 `approved`（已批准），且未被新事件标记为 `needs-revision`（待修订）或 `archived`（已归档）。
3. 检查蓝图资产是否完整包含 改动切片、依赖顺序、风险检查点、发布 / 验证检查点、接口约束、数据形状与测试承诺，并确认确定性检查已通过。
4. 若蓝图形式为分层蓝图包，检查主蓝图 / manifest 绑定的全部子蓝图和覆盖矩阵均为 `approved`（已批准）、版本一致、确定性检查已通过。
5. 检查执行模式、执行范围、禁止越界项和停止条件是否已确定；按切片或波次交接时，执行范围必须来自 manifest 已定义的切片或波次。
6. 只摘录和重组已批准蓝图内容，整理执行所需最小包。
7. 输出交接摘要。
8. 若发现前提不稳，回退到 `hilp-reapproval`；若发现蓝图缺口或模糊项，回退到 `hilp-blueprint`，不得在交接阶段补写。

交接契约见 `references/handoff-contracts.md`。
事件规则见 `references/event-action-rules.md`。

## 未通过入口检查时的处理

不得创建或更新 `stage-6/execution-handoff` 正式资产。用户可见输出只说明：缺少哪个已批准资产、哪个蓝图字段仍不确定、执行模式为何不能确定，或哪项上游前提失效，并明确回退到实施蓝图阶段或变更重审阶段。

## 输出模板

# 执行交接阶段

## 这个阶段要做什么
- 用一句话说明：把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产
- 文件路径：`项目根目录/docs/hilp/变更概述/05-执行交接_<审批标记>_execution-handoff@vN.md`
- asset_ref：`stage-6/execution-handoff@vN [state=<state>｜中文状态=<state_label>]`
- 当前状态：必须写中文状态名，必要时附内部状态值。
- 当前是否需要审批：执行交接绑定已批准蓝图，通常不重新审批；若存在阻断项，不得产出执行交接资产。

## 上游资产
- 已批准需求边界：
- 已批准设计：必须使用 `stage-3/design-choice@vM [state=approved｜中文状态=已批准]` 格式。
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图 / 分层蓝图包。
- 分层蓝图包 manifest：单体蓝图写“无”；分层蓝图包列出主蓝图和包内资产清单。
- 当前蓝图版本：

## 执行范围
- 范围类型：整包 / 发布波次 / manifest 中已定义的切片集合。
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

## 执行入口检查
- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：
- 停止并回退条件：

## 硬约束

- 缺少 `stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]` 时，不得交接到执行层。
- 蓝图资产的 `owner_skill` 不是 `hilp-blueprint` 或缺少 `last_decision` 时，不得交接到执行层。
- 分层蓝图包缺少主蓝图 / manifest、包内资产清单、覆盖矩阵，或任一包内成员不是 `approved`（已批准）时，不得交接到执行层。
- 上游 Stage 3 设计资产不是 `approved`（已批准），或已进入 `needs-revision`（待修订） / `archived`（已归档）时，不得交接到执行层。
- `human_decision_required`（必须人工裁决）未完成时，不得交接到执行层。
- 蓝图未通过确定性检查、执行模式未确定或执行范围未绑定到蓝图 / manifest 时，不得交接到执行层。
- 不得把交接说明写成实现代码。
- 不得把交接阶段变成新的设计阶段。
- 不得在交接阶段新增、修订、补齐或解释性扩展蓝图内容。
- 不得默认“规划完成就必须立刻执行”。

## 交接规则

- 蓝图资产为 `draft`（草稿）、`ready-for-human-decision`（待人工裁决）、`ready-for-approval`（待审批）、`needs-revision`（待修订）或 `archived`（已归档）时，禁止交接到执行层。
- 分层蓝图包任一成员未批准、版本与 manifest 不一致，或执行范围超出 manifest 已定义边界时，禁止交接到执行层。
- 缺少必要蓝图细节、存在模糊项或确定性检查未通过但上游仍稳定时，回交 `hilp-blueprint`。
- 暴露出上游资产失效、治理升级或新的 必须人工裁决的决策点时，交给 `hilp-reapproval`。
