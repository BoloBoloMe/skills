---
name: to-execution-spec
description: 将 Product/Technical Spec 拆成 AI 可执行的 Execution Spec 和垂直切片 issues.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 只读感知当前工作目录的领域模型.
生成 `EXECUTION.md` 和可独立领取的垂直切片 issues. `EXECUTION.md` 是全局执行约束和任务拓扑, issue 是 `afk` 的直接输入. 文档只供 AI 使用. 本 skill 不新增产品/API/架构决策, 不要求我阅读文档后确认.
切片采用两步承诺: 本 skill 冻结切片数量上限, 首 issue 全文, 其余切片的粗轮廓和重切授权边界; 后续 issue 由 `afk` 在每个 issue 关闭时依据实现知识在授权内物化. 不把零实现知识时的猜测固化为全部切片.

## 1. 收集上下文

确认已获得本地 Spec 工作区约定. 没有则停止, 请我调用 `setup-workspace` skill 完成本地 Spec 工作区初始化. 读取同一 feature 下的 `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md` (如存在). 需要维护决策引用时调用 `decision-ledger`.
缺少 `PRODUCT.md` 或 `TECHNICAL.md` 时停止. 来源之间冲突, 或拆分需要新产品/API/架构/范围取舍时停止, 在会话中说明影响并请我回到 `deliberate`.
完成标准: 三层输入属于同一 feature; 无阻塞冲突; 当前有效决策已读取或明确无相关决策.

## 2. 聚焦探索代码库

如果当前上下文不足, 读取相关代码, 测试和配置, 只为确定:

- 可独立验证的垂直切片.
- 模块/目录/行为级允许和禁止范围.
- 真实验证入口和全局完成定义.
- 切片依赖和停止条件.

禁止把早期猜测固化为逐文件计划. 预计文件只允许在迁移或高风险任务中作为非约束提示, 并标明需要执行时复核.
完成标准: 首切片可独立验证; 轮廓切片有暂定覆盖和验证方向; 首切片的范围和验证入口来自 Spec 或代码事实.

## 3. 判断切片粒度 (两步承诺)

优先单 issue. 只有存在 2 条以上可独立验证的端到端结果, 需要分阶段合并降低风险, 或不同角色可独立领取时才拆分.
每个 issue 必须是贯穿所需层次的 tracer bullet, 完成后可单独演示或验证. 禁止按 schema/API/UI/tests 水平拆分.

多 issue 时, 输出按确定性分两层:

- **冻结**: 首 issue 的完整内容 (覆盖 ID, 范围, 验证入口, 风险, AFK/HITL 归属) - 它最近, 认知最充分.
- **未决轮廓**: 其余切片只写暂名, 暂覆盖 ID, 依赖假设和主要不确定性. 轮廓是零实现知识时的暂定猜测, 允许 `afk` 在重切授权内物化时调整.

同时给出切片数量上限 (含理由) 和重切授权边界:

- 轻量重切 (afk 自主): 调整未决切片的覆盖 ID 组合, 顺序和边界; 按实现知识拆分或合并轮廓.
- 越权停止: 切片数超上限; 需推翻已关闭 issue 的假设; 需改变 PRODUCT/TECHNICAL/DECISIONS.

完成标准: 数量上限有理由; 首切片可独立验证且完整; 轮廓暂定覆盖全部剩余 AC/TG/NFR 且标明不确定性; 授权边界可执行 (轻量与越权可区分).

## 4. 会话盘问切片

调用 `grilling` skill 确认两步承诺. 文档不是审批界面. 在会话中先给出你的推荐 (数量上限和理由), 然后说明:

- 首 issue: 名称和用户/系统可观察结果, 覆盖的 `AC/TG/NFR`, 主要风险, 适合 AFK 或需要 HITL 的原因.
- 其余轮廓: 暂名, 暂覆盖, 依赖假设, 主要不确定性.
- 重切授权边界: 哪些调整授权 `afk` 自主, 哪些触发停止回到我.

一次只问一个会改变上限, 首 issue 边界或授权边界的问题. 不展示 issue 全文, 不让我阅读草稿. 我确认的是首切片, 数量上限, 轮廓走向和授权边界, 不是 Markdown 文件, 也不是后续切片的最终边界.
完成标准: 我已在 grilling 会话中明确确认数量上限, 首 issue 内容, 轮廓走向和重切授权边界; 没有把文档阅读当作确认条件; 未把轮廓当作已冻结切片要我确认.

## 5. 编写 Execution Spec 和 issues

输出:

- `docs/changes/<feature-slug>/EXECUTION.md`.
- `docs/changes/<feature-slug>/issues/ISSUE-01-<slug>.md` (仅首 issue 落盘全文).

先生成首 issue, 再生成引用其路径的 `EXECUTION.md`; 未决轮廓只写在 `EXECUTION.md` 任务图中, 不生成 issue 文件, 由 `afk` 物化时按当时依赖顺序连续编号落盘. 单 issue 变更直接全部冻结, 无轮廓. 存在相关 DECISIONS.md 时, 首 issue 与相关决策维护双向引用; 无相关决策时 issue 写"无". 不复制 Product/Technical Spec 的正文, 只引用稳定 ID 和执行所需摘要. 不记录 `Status:`.
完成标准: 首 issue 引用可解析; 每个 AC/TG/NFR 被首 issue 或某轮廓暂定覆盖, 或明确说明无需执行任务; 轮廓不含实现细节; 任务图标明冻结/未决; 依赖无环; 决策双向引用完整 (首 issue), 或已明确无相关决策.

<execution-spec-template>
# <变更标题> Execution Spec
## 权威输入
- Product Spec: `PRODUCT.md`
- Technical Spec: `TECHNICAL.md`
- Decisions: `DECISIONS.md` 或"无"
## 全局允许范围
- 可修改的模块, 目录, 文件模式或行为范围.
## 全局禁止范围
- 不可修改的模块, API, schema, 行为或非目标.
## 完成定义
- 必须通过的 build/lint/test/benchmark/人工验证及通过标准.
## 测试策略
- AC/TG/NFR 对应的测试类型和验证入口.
## 任务图
- ISSUE-01 (已冻结): `issues/ISSUE-01-<slug>.md`; 覆盖: AC-001, TG-001; 依赖: 无.
- ISSUE-02 (未决轮廓): 暂名 <名称>; 暂覆盖: AC-002; 依赖: ISSUE-01; 不确定性: <...>.
## 重切授权
- 切片数量上限: <N> (理由: <...>).
- 轻量重切 (afk 自主): 调整未决切片的覆盖 ID 组合, 顺序和边界; 按实现知识拆分或合并轮廓.
- 越权停止: 切片数超上限; 需推翻已关闭 issue 的假设; 需改变 PRODUCT/TECHNICAL/DECISIONS.
## 覆盖矩阵
- AC-001 -> ISSUE-01 (已冻结) -> 验证入口.
- AC-002 -> ISSUE-02 (未决轮廓, 暂定) -> 验证入口.
- TG-001 -> ISSUE-01 (已冻结) -> 验证入口.
## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围或触碰禁止范围时停止.
- 重切触发越权条件时停止.
- Spec 与代码事实冲突或无法提供完成证据时停止.
</execution-spec-template>

<issue-template>
## 父级
- `../EXECUTION.md`
## 执行(Execution)
- [ ] 已实现
## 要构建什么
端到端可观察结果. 结尾说明适合 AFK 或需要 HITL 的原因.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-001
- Technical: `../TECHNICAL.md`, TG-001, NFR-001
## 相关决策
- `../DECISIONS.md`: D001. 无则写"无".
## 允许范围
可以修改的模块, 目录, 文件模式或行为范围.
## 禁止范围
明确不能修改的模块, API, schema, 行为或非目标.
## 验证入口
真实命令, 测试目标或可观察验收方式及通过标准.
## 风险提示
已知高风险点和防护.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
无需进一步产品/API/架构决策的证据. 不适合时写明 HITL 原因.
## 验收标准
- [ ] 与覆盖依据一致的可观察标准.
## 被阻塞于
- ISSUE 引用. 无则写"无 - 可以立即开始".
</issue-template>

## 6. 生成 AFK 步骤文件

AFK 步骤文件是为调用 skill `afk` 的另一个父会话准备的. 切片确认并落盘后:

1. 读取 `references/step-gen-guide.md`.
2. 在 `afk-running/` 根生成 `_current.md` 和 `step-01.md` 到 `step-06.md`.
3. `_current.md` 初始内容为第一个 issue key 加 `:01`, 例如 `ISSUE-01:01`.
4. 步骤文件内容严格来自生成指引, 不加入 feature 特有实现细节.

完成标准: `_current.md` 和 6 个步骤文件存在; 第一个 issue 可由 `_current.md` 唯一定位.

## 7. 会话交付

直接告诉我: 已生成的三类路径, 数量上限和首 issue 名称/覆盖, 轮廓走向, 重切授权边界, AFK 与 HITL 归属, 是否有阻塞. 不展示文档全文, 不让我阅读后确认.
完成标准: 我从会话中知道首 issue 做什么, 上限是多少, 后续切片如何随实现显形, 无需阅读 `EXECUTION.md` 或 issues.
