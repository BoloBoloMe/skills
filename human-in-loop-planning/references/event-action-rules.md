# 事件动作规则

本文件定义“人在回路”协议的最小事件-动作规则，格式统一为：

`触发器 -> 必需动作 -> 被阻断的转移 -> 资产状态变化`

---

## 一、上位优先级规则

### 规则 A：安全优先于效率
安全性优先于效率。
凡命中以下触发器，均优先于 lean 默认和推进连续性：
- 证据触发器
- 失效触发器
- 回滚 / 兼容安全要求
- `human_decision_required`

### 规则 B：新事实优先于旧批准
新事实优先于旧批准。
只要新证据足以推翻此前边界、假设或设计前提：
- 原批准可以失效
- 相关下游资产进入 `needs-revision`
- 不允许以“已经批准过”为由跳过回看

### 规则 C：主规划原型拥有主流程
主规划原型决定主流程。
- 主原型决定主路线
- 次原型只追加检查项、验证要求与风险控制
- 不允许通过原型叠加创建新的阶段体系

---

## 二、并发处理总规则

当多个事件同时活跃时：
1. 先处理阻断性事件
2. 再处理非阻断性事件
3. 每轮处理后都重算 允许状态转移（允许状态转移）
4. 每轮处理后都重算相关资产状态

阻断性事件包括：
- 证据触发器
- 失效
- 回滚 / 兼容安全要求
- `human_decision_required`

非阻断性事件包括：
- `human_decision_recommended`
- 治理降级
- 折叠与归档类动作

---

## 三、事件-动作表

### 事件 0：人工批准授予（Human Approval Granted）

**触发器**
- 人类明确批准 `ready-for-approval` 资产

**必需动作**
- 将该资产状态从 `ready-for-approval` 改为 `approved`
- 保留同一内容版本
- 记录 `last_decision=<decision-id>`
- 按批准对象所属阶段重新计算下一跳

**被阻断的转移**
- 无



**批准语言规则**
- 只有用户明确表达批准当前具体 `asset_ref` / 资产版本时，才能视为 人工批准授予（Human Approval Granted）。
- 泛泛的“可以执行了”“差不多了”“按这个来”不得自动视为批准，除非上下文明确绑定到当前资产版本。
- lean 模式允许轻量批准，但轻量批准仍必须明确绑定当前 Stage 3 设计资产或 Stage 4/5 蓝图资产版本。

**资产状态变化**
- 同一版本, `state=approved`, `last_decision=<decision-id>`
- 若批准对象是 `stage-3/design-choice@vN` 且 `owner_skill=hilp-design-approval`，下一步为 `hilp-blueprint`
- 若批准对象是 `stage-4-5/implementation-blueprint@vN` 且 `owner_skill=hilp-blueprint`，下一步为 `hilp-execution-handoff`
- 若批准对象不是 Stage 3 设计资产或 Stage 4/5 蓝图资产，不得自动进入 `hilp-blueprint` 或 `hilp-execution-handoff`，必须按 `handoff-contracts.md` 重算下一跳

### 事件 1：证据触发器命中

**触发器**
- 根因不明
- 现状行为未建立
- 影响面未知
- 兼容窗口不清

**必需动作**
- 先补 Stage 2
- 暂停基于未证实前提形成的新设计结论

**被阻断的转移**
- 禁止进入 Stage 3 的可审批设计结论
- 禁止把未证实结论写入 Stage 4 / Stage 5

**资产状态变化**
- 基于未证实前提写出的 Stage 3 / 4 / 5 内容改为 `needs-revision`

---

### 事件 2：必须人工裁决命中

**触发器**
- 范围冲突
- 关键取舍不可兼得
- 高回滚成本且收益不确定
- 多合理方向无法由证据排除

**必需动作**
- 显式列出待裁决问题、选项与建议
- 暂停相关绑定性推进

**被阻断的转移**
- 禁止把相关结论标记为 `approved`
- 禁止依赖该决策继续产出绑定性 Stage 4 / Stage 5 内容

**资产状态变化**
- 当前阶段进入 `ready-for-human-decision`
- 未决项不得进入 `ready-for-approval` 或 `approved`

---

### 事件 3：建议人工裁决命中

**触发器**
- 多个方向都合理但差异不大
- 结构更优雅但改动面更大
- 长期收益更好但短期收益有限

**必需动作**
- 显式写出建议裁决点
- 标注默认路径

**被阻断的转移**
- 不阻断当前阶段进入 `ready-for-approval`
- 仅阻断将“人未选的优先选项”写成既定事实

**资产状态变化**
- 资产可进入 `ready-for-approval`

---

### 事件 4：已批准上游资产失效

**触发器**
- 已批准的需求边界、关键假设或设计前提被新证据推翻

**必需动作**
- 回到最近受影响的上游阶段修订
- 登记影响范围

**被阻断的转移**
- 禁止继续依赖旧版本进入后续审批

**资产状态变化**
- 被影响的下游资产全部变为 `needs-revision`

---

### 事件 5：治理升级

**触发器**
- 耦合范围扩大
- 回退成本上升
- 发现兼容窗口
- 从单点问题变为多模块联动

**必需动作**
- 当前阶段即时应用更高治理模式
- 补齐新增必需资产

**被阻断的转移**
- 禁止跳过升级后必需控制件直接向后审批

**资产状态变化**
- 已有资产保持原状态
- 新增资产以 `draft` 创建

---

### 事件 6：治理降级

**触发器**
- 风险收缩
- 不确定性下降
- 兼容窗口被排除
- 范围回落为局部变更

**必需动作**
- 显式确认可降级
- 折叠不再必要的活跃控制件

**被阻断的转移**
- 不阻断推进
- 但不得丢失仍有判断价值的历史依据

**资产状态变化**
- 不再活跃维护的控制件改为 `archived`

---

## 四、资产状态规则

只保留以下六种资产状态：
- `draft`
- `ready-for-human-decision`
- `ready-for-approval`
- `approved`
- `needs-revision`
- `archived`

状态语义：
- `draft`：内容未达到当前阶段门槛，不能提交审批或绑定推进。
- `ready-for-human-decision`：存在 必须人工裁决的决策，等待人类裁决；不能进入蓝图或执行交接。
- `ready-for-approval`：内容可提交人工审批；仍不是批准状态，不能被下游当作已批准资产引用。
- `approved`：人类明确批准后产生；只有该状态允许绑定性下游推进。
- `needs-revision`：上游变化、证据触发或失效事件导致不可继续依赖。
- `archived`：不再活跃参与判断，但保留历史依据。

规则：
- 不单列 `stale`，上游变化导致不可直接继续依赖的资产，一律归入 `needs-revision`。
- 不把 `ready-for-approval` 当作 `approved`。
- 不再参与活跃判断但仍保留历史价值的资产，一律归入 `archived`。

---

## 五、允许状态转移 重算规则

每次事件处理后，必须重新判断：
- 当前阶段是否还能进入 `ready-for-human-decision`
- 当前阶段是否还能进入 `ready-for-approval`
- 当前阶段是否还能进入 `approved`
- 是否允许进入下一个内部模块
- 是否必须回退到更早阶段

若以下任一条件成立，则禁止前推：
- 关键事实未建立
- 必须人工裁决的决策未解决
- 上游批准已失效
- 升级后必需控制件未补齐

---

## 六、资产版本规则

每个资产必须携带以下最小元数据：

```text
asset_id: <stable-id>
artifact_name: <stage>/<artifact-name>
version: v<number>
state: draft | ready-for-human-decision | ready-for-approval | approved | needs-revision | archived
owner_skill: <skill-name>
created_from: <asset_ref | original-task>
last_event: <none | event-name>
last_decision: <none | decision-id>
```

版本递增规则：
- 内容性修订必须递增版本号。
- 单纯状态变化可以保留版本号，但必须记录 `last_event`。
- 从 `ready-for-approval` 变为 `approved` 只能通过 `人工批准授予（Human Approval Granted）` 事件发生；这是状态变化，不自动改变内容版本。
- 从 `approved` 变为 `needs-revision` 必须记录触发事件，并阻断所有依赖该资产的下游绑定推进。

---

## 七、资产生命周期规则

### 必须保留到结束的内容
- 已批准的需求边界
- 已批准的关键设计选择
- 仍影响编码或验证的未决问题
- strict 模式下仍影响回滚 / 兼容判断的检查点

### 可折叠的内容
- 已关闭且不再影响判断的开放问题
- 已确认并吸收入主文档的假设
- 仅服务于早期路由、后续已无价值的说明

### 治理降级后应归档的内容
- 原为高风险预防而创建、现已不再影响判断的扩展控制件
- 不再参与活跃重审传播的影响登记

规则：
- 活跃集只保留仍会改变后续判断的内容
- 其余内容进入 `archived`
