# 交接契约

本文件定义 7 个内部模块 之间允许的交接关系、最小输入契约、最小输出契约，以及禁止交接的情况。

---

## 一、总原则

1. 内部模块之间按职责交接，不按任务名称交接。
2. 对普通用户说明交接时，使用中文阶段名和自然语言描述：
   - 为什么现在要进入下一阶段
   - 下一阶段要解决什么
   - 当前还缺什么或需要用户做什么
3. 内部模块名、事件名和完整状态计算过程默认写入资产元数据或审计说明，不作为普通用户回答的主内容。
4. 所有落盘文档和用户交互中的状态必须给出清晰中文状态名；涉及精确资产引用、审计或交接时，采用“内部状态值｜中文状态=中文名”的双写格式。
5. 若发现旧上游结论失效，不得继续沿旧链路推进，必须转向 `hilp-reapproval`。
6. 所有绑定性推进都要求上游满足最小输入契约。
7. 交接契约不得覆盖事件动作规则；若事件规则判定阻断，交接必须暂停。
8. 交接时必须引用资产 ID、版本、内部状态和中文状态名，不能只写“上游已批准”。
9. 每个阶段交接前都必须先完成当前阶段资产落盘；若落盘失败，不得声称该阶段已完成。

---

## 二、模块间允许关系

### `hilp-router`
允许交给：
- `hilp-requirements-facts`
- `hilp-design-approval`
- `hilp-reapproval`

禁止直接交给：
- `hilp-blueprint`
- `hilp-execution-handoff`

原因：
路由器只能决定路径，不能替代事实建立与设计门控。

---

### `hilp-requirements-facts`
允许交给：
- `hilp-design-approval`
- `hilp-router`
- `hilp-reapproval`

禁止直接交给：
- `hilp-execution-handoff`

条件：
- 只有当目标、范围、成功标准与关键事实足以支持设计比较时，才能交给 `hilp-design-approval`。

---

### `hilp-design-approval`
允许交给：
- `hilp-blueprint`
- `hilp-reapproval`
- `hilp-requirements-facts`

条件：
- 只有状态为 `approved`（已批准），才能交给 `hilp-blueprint`。
- `ready-for-approval`（待审批）只表示可提交审批，不是可绑定推进。
- `ready-for-human-decision`（待人工裁决）必须先解决 必须人工裁决的决策。
- 若暴露出上游事实不足，则回交 `hilp-requirements-facts`。

---

### `hilp-blueprint`
允许交给：
- `hilp-execution-handoff`
- `hilp-reapproval`
- `hilp-design-approval`

条件：
- 只有当蓝图资产为 `stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]`、`owner_skill=hilp-blueprint`、存在 `last_decision`，且不存在未解决的 必须人工裁决的决策和上游失效事件时，才能交给 `hilp-execution-handoff`。
- 蓝图资产为 `draft`（草稿）、`ready-for-human-decision`（待人工裁决）、`ready-for-approval`（待审批）、`needs-revision`（待修订）或 `archived`（已归档）时，不得交给 `hilp-execution-handoff`。

---

### `hilp-reapproval`
允许交给：
- `hilp-router`
- `hilp-requirements-facts`
- `hilp-design-approval`
- `hilp-blueprint`

规则：
- 它只决定回退点与下一跳，不负责替代目标内部模块的正常工作。

---

### `hilp-execution-handoff`
允许交给：
- 外部执行层
- `hilp-blueprint`
- `hilp-reapproval`

规则：
- 入口必须绑定 `approved`（已批准）蓝图资产，而不是自然语言“蓝图完成”的判断。
- 只要发现上游不稳，不得继续交接给执行层。

---

### `hilp-skill-pressure-test`
允许回指：
- 任意内部模块
- 共享 references

规则：
- 它不属于正常业务推进链。

---

## 三、资产引用与落盘格式

### 资产保存位置

所有阶段资产都必须保存到当前项目目录下：

```text
项目根目录/hilp/变更概述/
```

“变更概述”使用本次任务的简短中文概括，便于用户在项目目录中直接找到相关文档。旧资产不迁移；本规则只约束新产生的资产。

### 文件命名规则

推荐文件名格式：

```text
<阶段前缀>-<阶段中文名>_<审批标记>_<artifact>@vN.md
```

阶段前缀：

- `00`：初始分流阶段
- `01`：需求对齐与事实求证阶段
- `02`：方案设计与审批阶段
- `03`：实施蓝图阶段
- `04`：变更重审阶段
- `05`：执行交接阶段
- `90`：协议压力测试阶段

审批标记：

- `no-approval`：无需审批，仅作为过程记录
- `needs-decision`：需要用户先做裁决
- `needs-approval`：可提交审批，但尚未批准
- `approved`：已明确批准
- `needs-revision`：需要修订
- `archived`：已归档

示例：

```text
02-方案设计_needs-approval_design-choice@v1.md
03-实施蓝图_approved_implementation-blueprint@v1.md
```

### 资产元数据

每个落盘资产开头必须包含最小元数据块：

```text
asset_id: <stable-id>
artifact_name: <stage>/<artifact-name>
version: v<number>
state: draft | ready-for-human-decision | ready-for-approval | approved | needs-revision | archived
state_label: 草稿 | 待人工裁决 | 待审批 | 已批准 | 待修订 | 已归档
owner_skill: <skill-name>
created_from: <asset_ref | original-task>
last_event: <none | event-name>
last_decision: <none | decision-id>
approval_marker: no-approval | needs-decision | needs-approval | approved | needs-revision | archived
approval_marker_label: 无需审批 | 待裁决 | 需审批 | 已批准 | 待修订 | 已归档
```

这些字段用于追踪和重审。普通用户回答默认只展示“文件已保存到哪里、当前中文状态是什么、当前是否需要审批、下一步要做什么”。

状态中文名固定映射如下：

| 内部状态值 | 中文状态名 |
|---|---|
| `draft` | 草稿 |
| `ready-for-human-decision` | 待人工裁决 |
| `ready-for-approval` | 待审批 |
| `approved` | 已批准 |
| `needs-revision` | 待修订 |
| `archived` | 已归档 |

审批标记中文名固定映射如下：

| 内部审批标记 | 中文状态名 |
|---|---|
| `no-approval` | 无需审批 |
| `needs-decision` | 待裁决 |
| `needs-approval` | 需审批 |
| `approved` | 已批准 |
| `needs-revision` | 待修订 |
| `archived` | 已归档 |

无需审批过程资产的生命周期规则：
- 过程记录正在形成时：`state=draft`（草稿），`approval_marker=no-approval`（无需审批）。
- 过程记录完成且不再活跃推进时：`state=archived`（已归档），`approval_marker=no-approval`（无需审批）。
- 过程记录产生需要采纳的规则修改建议时：另建新的设计资产，由新资产进入 `ready-for-approval`（待审批）。

### 跨阶段资产引用

所有跨阶段交接、重审和执行交接都必须用统一格式引用上游资产：

```text
asset_ref: <stage>/<artifact-name>@v<version> [state=<state>｜中文状态=<state_label>]
owner_skill: <skill-name>
source_event: <none | 触发器-name | decision-id>
last_decision: <none | decision-id>
summary: <one-line summary>
```

示例：

```text
asset_ref: stage-3/design-choice@v2 [state=approved｜中文状态=已批准]
owner_skill: hilp-design-approval
source_event: human-approval-2026-04-27-a
last_decision: decision-api-compatibility-window
summary: choose adapter-based 迁移（migration） with rollback checkpoint
```

引用规则：
- 下游只能绑定引用 `approved`（已批准）资产。
- `ready-for-approval`（待审批）资产只能作为待审批输入，不能作为蓝图依据。
- `ready-for-human-decision`（待人工裁决）资产只能作为待裁决输入，不能前推。
- `needs-revision`（待修订）和 `archived`（已归档）资产不得作为新的绑定依据。
- 每次重审导致内容变化时必须递增版本号。
- 所有跨阶段资产引用必须同时包含内部状态值和中文状态名。

---

## 四、最小输入契约

### 给 `hilp-router`
最少需要：
- 原始任务描述

### 给 `hilp-requirements-facts`
最少需要：
- 原始任务摘要
- 当前路由判断
- 当前治理模式

### 给 `hilp-design-approval`
最少需要：
- 目标
- 范围 / 非目标
- 成功标准
- 关键事实
- 关键未知项

### 给 `hilp-blueprint`
最少需要：
- `approved`（已批准）的 Stage 3 设计资产引用
- 推荐设计
- 关键 trade-off
- required / recommended 决策点状态
- `人工批准授予（Human Approval Granted）` 对应的 `last_decision`

### 给 `hilp-reapproval`
最低入口输入：
- 重审语义或疑似触发事件
- 用户提供的当前上下文

完整裁决输入：
- 命中的事件
- 当前资产状态
- 当前所处阶段
- 旧的推进链路

规则：
- 即使完整裁决输入不足，只要存在重审语义，也应优先进入 `hilp-reapproval`。
- 若完整裁决输入不足，输出 provisional（临时） 重审决议，并把缺失的资产状态、阶段和旧链路列为阻断项。

### 给 `hilp-execution-handoff`
最少需要：
- `stage-4-5/implementation-blueprint@vN [state=approved｜中文状态=已批准]` 的完整蓝图资产引用
- `owner_skill=hilp-blueprint`
- 蓝图 `last_decision=<human approval decision-id>`
- 仍有效的上游 `stage-3/design-choice@vM [state=approved｜中文状态=已批准]` 引用
- 当前阻断项状态为“无”

### 给 `hilp-skill-pressure-test`
最少需要：
- 被测试对象
- 测试场景
- 预期行为描述

---

## 五、最小输出契约

### `hilp-router` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 主 / 次规划原型
- 治理模式
- 主 / 辅规格策略
- 主 / 辅验证策略
- 需要用户知道的决策点
- 下一阶段中文名称

### `hilp-requirements-facts` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 目标
- 范围 / 非目标
- 成功标准
- 已知事实
- 证据来源
- 关键未知项
- 初步影响面
- 下一步需要用户确认或补充的内容

### `hilp-design-approval` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 推荐方案
- 备选方案
- 关键取舍
- 需要用户裁决或批准的内容
- 当前状态：必须同时写内部状态值和中文状态名（草稿 / 待人工裁决 / 待审批）

### `hilp-blueprint` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 改动切片
- 依赖顺序
- 风险检查点
- 发布 / 验证检查点
- 接口约束
- 数据形状
- 测试承诺
- 当前是否需要用户批准

### `hilp-reapproval` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 用自然中文说明发生了什么变化
- 受影响资产
- 回退判断
- 治理模式变化
- 当前允许和禁止继续做什么
- 下一阶段中文名称

### `hilp-execution-handoff` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 上游资产引用
- 执行范围
- 必守实现约束
- 风险与验证检查点
- 执行模式
- 当前阻断项

### `hilp-skill-pressure-test` 输出
必须包含：
- 中文阶段名称
- 阶段目的
- 已保存资产路径
- 内部状态值和中文状态名
- 测试场景
- 预期行为
- 实际行为
- 偏差分析
- 修订建议

---

## 六、禁止交接清单

### 任何 skill 都不得：
- 在上游失效时继续沿旧链路推进
- 绕过 `hilp-reapproval`
- 把 必须人工裁决的决策未解决的状态交给绑定性下游步骤
- 在交接时偷偷补写本不属于自己职责的内容

### 特别禁止
- `hilp-router` 不得直接交给 `hilp-blueprint`
- `hilp-requirements-facts` 不得直接交给 `hilp-execution-handoff`
- `hilp-design-approval` 在 `draft`（草稿）状态下不得交给 `hilp-blueprint`
- `hilp-blueprint` 在存在 必须人工裁决阻断时不得交给 `hilp-execution-handoff`

---

## 七、默认回退逻辑

- 事实问题 → 回到 `hilp-requirements-facts`
- 设计问题 → 回到 `hilp-design-approval`
- 蓝图问题 → 回到 `hilp-blueprint`
- 路由前提变化 → 回到 `hilp-router`
- 失效 / 升级 / 必须人工裁决阻断 → 先到 `hilp-reapproval`
