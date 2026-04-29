# 设计审批模块

## 模块元信息
- internal_module: `hilp-design-approval`
- 原触发描述：用于在需求边界和关键事实已基本稳定后，比较设计方向、形成推荐方案、标注关键取舍和人类决策点，并判断设计处于 draft（草稿）、ready-for-human-decision（待人工裁决）还是 ready-for-approval（待审批）。只有 goal、范围 / 非目标、成功标准、当前行为或证据基础 均已明确，影响面 至少有界，且 核心未知项 不阻断设计比较时才触发。若事实不足、根因未明、影响面无界，或上游批准已被新事实推翻，不要触发本 Skill，应改用 hilp-requirements-facts 或 hilp-reapproval。

# 概览

你负责 Stage 3：设计选择（Design Choice）。

唯一职责：形成方案并判断是否达到设计审批门槛。

只处理方案形成，不处理批准失效。

你负责：
- 比较设计方向
- 输出推荐方案
- 显式写出 trade-off（取舍）
- 识别 required / recommended 的人类决策点
- 判断当前设计处于 `draft`（草稿） / `ready-for-human-decision`（待人工裁决） / `ready-for-approval`（待审批）
- 给出 正常前推交接（normal forward handoff）

你不负责：
- 不处理旧批准被新事实推翻后的裁决
- 不负责治理模式重算
- 不负责 允许状态转移 重算
- 不写改动切片
- 不展开实现计划

## 极简工作流

1. 读取需求与事实输入。
2. 确认需求边界和关键事实足以支持方案比较。
3. 确定真正需要比较的设计方向。
4. 用最小必要方案集做比较。
5. 写出推荐方案、备选方案和关键取舍。
6. 判断 required / recommended 人类决策点。
7. 检查是否达到 Stage 3 审批门槛。
8. 输出 `draft`（草稿）、`ready-for-human-decision`（待人工裁决）或 `ready-for-approval`（待审批）。
9. 给出 normal forward handoff。

交接契约见 `references/handoff-contracts.md`。
事件规则见 `references/event-action-rules.md`。

## 输出模板

# 方案设计与审批阶段

## 这个阶段要做什么
- 用一句话说明：比较可行方案，给出推荐路径，并明确哪些内容需要用户决定或批准。

## 已保存资产
- 文件路径：`项目根目录/docs/hilp/变更概述/assets/02-方案设计_design-choice@vN.md`
- asset_ref：`stage-3/design-choice@vN [state=<state>｜中文状态=<state_label>]`
- 当前状态：必须写中文状态名，必要时附内部状态值。
- 当前是否需要审批：说明无需审批、待人工裁决、待审批或已批准。
- 若当前状态为 `ready-for-approval｜中文状态=待审批`：同时列出审核包路径 `项目根目录/docs/hilp/变更概述/review-pack/02-design-choice@vN-review.md` 和当前待审入口 `项目根目录/docs/hilp/变更概述/_current/当前待审.md`。

## 推荐方案
- 名称：
- 核心思路：
- 为什么推荐：

## 备选方案
### 方案 A
- 核心思路：
- 优点：
- 代价：
- 不选原因：

### 方案 B
- 核心思路：
- 优点：
- 代价：
- 不选原因：

## 关键取舍
- 正确性 / 安全性：
- 可回退性：
- 改动范围：
- 可维护性：
- 未来扩展性：

## 需要用户决定什么
- 是否存在：写“无 / 建议人工裁决 / 必须人工裁决”。
- 是否会阻止继续：写“无阻断项 / 有阻断项”。
- 问题描述：
- 可选项：
- 建议：
- 默认路径：仅在存在建议人工裁决时填写；必须满足安全边界且额外承诺最少。
- 用户是否已选择：未选择 / 已选择。
- 不得写成既定事实的内容：列出用户未选择前不能当作人工裁决结果的选项。

## 当前状态
- 中文状态名：草稿 / 待人工裁决 / 待审批 / 已批准 / 待修订 / 已归档
- 内部状态值：`draft` / `ready-for-human-decision` / `ready-for-approval` / `approved` / `needs-revision` / `archived`
- 进入该状态的理由：

## 下一步
- 下一阶段：写中文阶段名，或说明需要等待用户批准。
- 继续前提：
- 当前阻断项：写“无阻断项 / 有阻断项”。

## Stage 3 进入门槛

进入 `hilp-design-approval` 必须同时满足：

```text
目标：已知
范围 / 非目标: known
成功标准: known
当前行为或证据基础: known
影响面: at least bounded
核心未知项: not blocking design comparison
```

若任一条件不满足，默认回交 `hilp-requirements-facts`，不得主观放宽为“事实大致足够”。

## Stage 3 审批门槛

状态含义：

- `draft`（草稿）：事实、边界或设计比较尚不足，不能提交审批。
- `ready-for-human-decision`（待人工裁决）：存在 `human_decision_required`（必须人工裁决），需要人类先裁决；该状态不等于可审批，也不得交给蓝图。
- `ready-for-approval`（待审批）：不存在未解决的 必须人工裁决的决策，推荐路径和取舍已足以提交审批；该状态仍不等于 `approved`（已批准），不能被当作已批准资产。
- `approved`（已批准）：只能由明确的人类审批动作产生，表示可绑定推进到 `hilp-blueprint`。

只有同时满足以下条件时，才可进入 `ready-for-approval`（待审批）：

1. 已建立与当前设计选择直接相关的关键事实。
2. 不存在未解决的 `human_decision_required`（必须人工裁决）。
3. 当前推荐路径不依赖未经验证的核心假设。

若存在 `human_decision_required`（必须人工裁决），进入 `ready-for-human-decision`（待人工裁决）。
若关键事实或设计比较仍不足，保持为 `draft`（草稿）。

## 默认路径规则

当存在 `human_decision_recommended`（建议人工裁决）且未获人工裁决时：
- 必须显式写出默认路径。
- 必须写出“推荐裁决点”。
- 必须写出“用户是否已选择：未选择 / 已选择”。
- 必须写出“不得写成既定事实的内容”。
- 默认路径必须满足安全边界且额外承诺最少。
- 默认路径必须保留后续人工覆盖空间。
- 不得把默认路径解释为用户已经裁决。

## 硬约束

- `human_decision_required`（必须人工裁决）未解决时，不得生成绑定性的 Stage 4 / Stage 5 内容。
- 不得把未拍板的推荐选项写成既定事实。
- 不得把核心假设未验证的方案写成“已收敛设计”。
- 不得输出模块 / 文件级实现切片。
- 不得把设计比较扩张成执行计划。

## 交接规则

- 只有状态为 `approved`（已批准）时，才能交给 `hilp-blueprint`。
- 状态为 `ready-for-approval`（待审批）时，只能提交人工审批或等待明确批准，不得直接当作已批准设计使用。
- 状态为 `ready-for-human-decision`（待人工裁决）时，必须先解决 必须人工裁决的决策。
- 首次在当前 Stage 3 内识别 必须人工裁决的决策时，由本模块自己处理并输出 `ready-for-human-decision`（待人工裁决）。
- 已有 `approved`（已批准） / `ready-for-approval`（待审批） / 蓝图 / 交接 被 必须人工裁决的决策推翻或阻断时，交给 `hilp-reapproval`。
- 新事实推翻当前设计前提、关键假设失效或必须人工裁决的决策冻结既有路线时，交给 `hilp-reapproval`。
- 需求边界、成功标准或关键事实仍不足以支撑设计比较时，回交 `hilp-requirements-facts`。
