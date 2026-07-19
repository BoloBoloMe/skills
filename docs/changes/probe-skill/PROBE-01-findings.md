# PROBE-01 分析: wayfinder tracker 依赖点 → markdown 替代

## 方法

逐段通读 wayfinder SKILL.md，提取每个依赖 issue tracker 原生功能的机制，然后评估: (1) 该机制在纯 markdown 下是否可替代; (2) 替代方案是什么; (3) 替代是否会改变语义或工作流。

已确认前提 (来自 PROBE.md Notes): 单人场景无并发冲突; 载体为本地 markdown; 认领不需要。

---

## 依赖点清单

### 1. 地图 → 索引 markdown 文件

**机制**: 地图是 issue tracker 上标记 `wayfinder:map` 的 issue，子 ticket 是其子 issue。

**替代**: 本地 markdown 索引文件 (`PROBE.md`)。子 ticket 是同级目录下按命名约定关联的文件 (`PROBE-NN.md`)。

**影响**: 无。wayfinder 地图本身就是索引角色，markdown 文件天然胜任。`wayfinder:map` 标签无意义 — 文件名即身份。

**已采纳**: PROBE.md 当前结构已实现此替代。

---

### 2. 子 issue 层级 → 文件命名约定

**机制**: ticket 是地图的子 issue，tracker 提供层级可视化。

**替代**: 命名约定 `PROBE-NN.md` 表达归属; Backlog 索引文件中的前沿列表和 Decisions so far 表提供结构化层级视图。

**影响**: 失去 tracker UI 的树形可视化，但索引文件的手动维护足够单人场景。wayfinder 原文也说"地图是索引，非仓库" — 这与 markdown 索引文件角色一致。

**已采纳**: PROBE.md + PROBE-NN.md 命名。

---

### 3. 标签系统 (`wayfinder:<type>`) → 文件头或命名前缀

**机制**: 每个 ticket 携带 `wayfinder:research` / `wayfinder:prototype` / `wayfinder:grilling` / `wayfinder:task` 标签，区分类型。

**替代**: Item 文件头字段，如 `# 类型: probe:research` 或直接含在标题中。Backlog Decisions so far 也可附类型。

**影响**: 失去 tracker 按标签过滤/分组能力。单人场景下一次只处理少量 Item，手动查看文件头足够。如需检索，`grep` 即可。

**建议**: 文件头 `类型: probe:research` — 简洁，grep 友好，与"阻塞于"字段风格统一。

---

### 4. 认领机制 (分配给自己) → 文件头状态字段

**机制**: 会话通过将 issue 分配给自己来认领; 分配者是认领标记。

**替代**: Item 文件头 `状态: 进行中`。

**影响**: 无并发冲突场景下，状态字段仅作为会话内的进度标记，不需要"谁认领"的身份信息。wayfinder 原文说分配者*就是*认领标记 — 单人场景中身份冗余。

**已采纳**: PROBE-01.md 已用 `状态: 进行中`。

---

### 5. 阻塞 (原生依赖关系) → 文件头 + Backlog 双重表达

**机制**: tracker 原生依赖关系 — 可视化呈现前沿，人类无需打开地图就能看到哪些可做。

**替代**: 双重机制: (1) Item 文件头 `阻塞于: PROBE-NN` 声明依赖; (2) Backlog 前沿列表显式维护哪些开放且已解除阻塞。

**影响**: 失去 tracker UI 的原生阻塞图可视化。但 Backlog 前沿列表 + 文件头声明的组合在单人场景下足够 — 读取 Backlog 一眼看到前沿，读 Item 文件头确认阻塞状态。阻塞链条线性的场景尤其简单。

**风险**: 阻塞图复杂时 (DAG 而非链表)，Backlog 前沿列表需手动推导。当前阻塞链是线性的 (`01 → 02 → 03`)，暂时无此问题。未来如出现复杂 DAG，需在 Backlog 中显式标注每个被阻塞者和所有阻塞者。

**已采纳**: PROBE-02.md, PROBE-03.md 已用 `阻塞于: PROBE-NN`。

---

### 6. 前沿查询 → Backlog 显式列表

**机制**: 前沿 = 开放 + 已解除阻塞 + 未被认领的子 issue，通过 tracker 查询获得。

**替代**: Backlog 文件显式 `📍 前沿` 列表，由遍历会话在关闭 Item 后手动更新。

**影响**: 需要遍历会话记得更新前沿列表。这是手动步骤，可能遗漏。wayfinder 原文的前沿是 tracker 查询的*视图* — 动态计算; markdown 下变成了静态列表。但 HANDOVER.md 已将此作为规则 ("前沿由 Backlog 维护")，降低了遗漏风险。

**风险**: 遍历会话忘记更新前沿 → 下一个会话看到过时的前沿列表。可通过 HANDOVER.md 步骤检查清单缓解。

**已采纳**: PROBE.md 已有 `📍 前沿` 列表。

---

### 7. 解决评论 → 产物文件 + Backlog 摘要

**机制**: 答案作为解决评论发布到 issue 上。

**替代**: 答案写入独立产物文件 (如 `PROBE-01-findings.md`)，Backlog Decisions so far 追加一句话摘要 + 链接。

**影响**: wayfinder 原文强调"答案在 ticket，不在地图" — 避免地图膨胀。产物文件 + Backlog 链接模式实现了同样效果：详情在产物文件，Backlog 只存索引。

**已采纳**: HANDOVER.md 已规定此模式。

---

### 8. 关闭 issue → 文件头状态

**机制**: 关闭 issue，使其离开前沿。

**替代**: Item 文件头 `状态: 已关闭`。

**影响**: 无法用 tracker 查询区分"已关闭"和"开放"。但通过文件头 grep 即可，单人场景足够。

---

### 9. 并发安全 (多会话同时编辑) → 不需要

**机制**: tracker 提供事务性编辑和冲突检测，允许多会话并行认领已解除阻塞的 ticket。

**替代**: 不需要。PROBE.md Notes 已确认"认领: 不需要 (单人场景，无并发冲突)"。

**影响**: 无。但如果未来扩展到多人协作，这是 markdown 载体的最大弱点 — 需要 git 分支或文件锁等额外机制。

**不在本次范围**: 与 PROBE.md 的范围外一致。

---

### 10. Ticket 创建时序 (先创建后连线) → 直接写文件

**机制**: 创建 ticket (获得 id) 后，在第二轮中连接阻塞边 — 因为阻塞引用需要目标 id 存在。

**替代**: markdown 下无 id 分配问题 — 文件名在创建时确定，阻塞引用直接用文件名。创建 Item 文件和声明阻塞可在同一步完成。

**影响**: 简化了流程。wayfinder 的两轮创建是 tracker 的 id 分配时序导致的约束，markdown 下消失。

---

### 11. Not yet specified / Out of scope → Backlog 对应区段

**机制**: 地图正文中的两个区段，记录迷雾和范围外。

**替代**: Backlog markdown 文件的 `🌫️ Not yet specified` 和 `🚫 Out of scope` 区段。

**已采纳**: PROBE.md 已有。

---

## 总结

| wayfinder 机制 | tracker 依赖 | markdown 替代 | 状态 |
|---|---|---|---|
| 地图 | `wayfinder:map` issue | 索引 markdown (`PROBE.md`) | 已采纳 |
| 子 issue 层级 | tracker 父子关系 | 命名约定 + Backlog 索引 | 已采纳 |
| 标签 (`wayfinder:<type>`) | issue 标签 | 文件头字段 | 建议统一 |
| 认领 | issue 分配 | 文件头 `状态` | 已采纳 |
| 阻塞 | 原生依赖 | 文件头 `阻塞于` + Backlog 前沿 | 已采纳 |
| 前沿查询 | tracker 查询 | Backlog 显式列表 | 已采纳 |
| 解决评论 | issue 评论 | 产物文件 + Backlog 摘要链接 | 已采纳 |
| 关闭 | 关闭 issue | 文件头 `状态: 已关闭` | 已采纳 |
| 并发安全 | tracker 事务 | 不需要 (单人) | 已采纳 |
| Ticket 创建时序 | id 分配 | 直接写文件 (无时序约束) | 简化 |
| Not yet specified | 地图正文 | Backlog 对应区段 | 已采纳 |
| Out of scope | 地图正文 | Backlog 对应区段 | 已采纳 |

## 对其他 Item 的影响

- **PROBE-02 (模板)**: 本分析确认了文件头字段的具体需求 — 至少需要 `状态`, `阻塞于`, `类型`。标签类型的命名约定 (`probe:research` vs 其他) 留待 PROBE-02 敲定。
- **PROBE-03 (SKILL.md 大纲)**: 本分析确认遍历会话中无需认领步骤 (单人)、无需并发协调、创建 Item 无需两轮时序。这些简化应体现在 SKILL.md 的遍历流程中。
