# 实施蓝图模块

## 模块元信息
- internal_module: `hilp-blueprint`
- 原触发描述：用于把已明确 已批准的 Stage 3 设计资产转成实施蓝图，明确改动切片、依赖顺序、风险检查点和实现约束。只有在存在完整 asset_ref、owner_skill=hilp-design-approval、last_decision 为 人工批准授予（Human Approval Granted） 决策、且不存在未解决 必须人工裁决的决策时才应触发。若当前设计仅为 ready-for-approval、方案选择未定、缺少批准资产引用或上游前提失效，不要触发本 Skill。

# 概览

你负责两个阶段：
- Stage 4：改动拓扑（Change Topology）
- Stage 5：实现约束（Implementation Constraints）

你的目标是把上游设计转成“可执行但仍属于规划层”的实施蓝图。

你必须明确：
- 改动切片（change slices）
- 依赖顺序（dependency order）
- 风险检查点（risk checkpoints）
- 发布 / 验证检查点（rollout / verification checkpoints）
- 数据形状（data shape）
- 接口约束（interface constraints）
- 局部算法骨架（local algorithm skeleton）
- 错误处理要求（error handling requirements）
- 测试承诺（test commitments）

你不负责：
- 不重新定义需求
- 不重新发明设计路线
- 不直接开始写最终实现代码

## 极简工作流

进入本模块前必须存在完整资产引用：

```text
asset_ref: stage-3/design-choice@vN [state=approved]
owner_skill: hilp-design-approval
last_decision: <human approval decision-id>
```

若缺少上述任一项，不得仅凭“方案已经定了”“就按这个做”等自然语言判断进入蓝图；必须回到 `hilp-design-approval`、等待 `人工批准授予（Human Approval Granted）`，或交给 `hilp-reapproval` 裁决。

1. 检查并读取完整的已批准 Stage 3 设计资产。
2. 输出 Stage 4 的改动拓扑。
3. 输出 Stage 5 的实现约束。
4. 检查蓝图是否依赖未决上游问题。
5. 检查兼容 / 回滚检查要求。
6. 输出蓝图状态。
7. 决定是否可交接到执行层。
8. 若发现上游前提失效，则改走 `hilp-reapproval`。

lean / standard / strict 的详细差异见 `references/routing-matrix.md`。
交接契约见 `references/handoff-contracts.md`。
事件规则见 `references/event-action-rules.md`。

## 输出模板

# 实施蓝图

## Stage 4：改动拓扑
- 改动切片：
- 依赖顺序：
- 风险检查点：
- 发布检查点：
- 验证检查点：
- 涉及模块 / 子系统 / 文件范围：

## Stage 5：实现约束
- 数据形状：
- 接口约束：
- 局部算法骨架：
- 错误处理要求：
- 测试承诺：
- 必要的代码草图：

## 蓝图资产状态
- asset_ref：`stage-4-5/implementation-blueprint@vN [state=draft | ready-for-human-decision | ready-for-approval | approved | needs-revision | archived]`
- owner_skill：`hilp-blueprint`
- upstream_design_ref：`stage-3/design-choice@vM [state=approved]`
- last_decision：
- 当前是否可交接到执行层：仅当蓝图资产为 `approved` 且上游设计仍有效时才写“是”
- 当前阻断项：
- 是否依赖未决上游问题：
- 是否存在兼容 / 回滚约束：

## Stage 4/5 蓝图审批门槛

只有同时满足以下条件时，蓝图才能进入 `ready-for-approval`：

1. 改动切片已覆盖推荐设计的全部必要改动。
2. 依赖顺序足以支持安全实施。
3. 风险检查点与发布 / 验证检查点已明确。
4. 接口约束、数据形状、错误处理要求与测试承诺已明确。
5. 不存在未解决的 `human_decision_required`。
6. 蓝图未改写 Stage 3 已批准设计 的边界或取舍。
7. 上游设计资产 仍为 `approved`，未被标记为 `needs-revision` 或 `archived`。

若存在 必须人工裁决的决策，进入 `ready-for-human-decision`。
若缺少关键蓝图内容，保持 `draft`。

进入 `hilp-execution-handoff` 的蓝图必须是 `approved`。lean 模式下，批准可以是显式轻量批准，例如“确认按此蓝图执行”，但仍必须明确绑定当前蓝图资产版本。

## 硬约束

- `human_decision_required` 未解决时，不得形成绑定性蓝图。
- 不得改写上游批准边界。
- 不得把实现约束扩张成新的设计讨论。
- 不得省略风险检查点与验证检查点。
- 不得把蓝图直接写成最终代码。

## 交接规则

- 只有蓝图资产为 `stage-4-5/implementation-blueprint@vN [state=approved]`、`owner_skill=hilp-blueprint`、存在 `last_decision`，且上游设计资产仍为 `approved` 时，才能交给 `hilp-execution-handoff`。
- 蓝图建立在已失效的需求、事实或设计之上时，交给 `hilp-reapproval`。
- 发现问题本质是设计并未真正收敛时，回交 `hilp-design-approval`。
