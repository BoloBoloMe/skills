---
name: to-execution-spec
description: 将 Product/Technical Spec 拆成 LLM 可执行的 Execution Spec 和垂直切片 issues.
disable-model-invocation: true
---

开始前, 调用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

目标: 编写 Execution Spec: `EXECUTION.md` 和 issues. 常规工作拆成可独立领取的垂直切片; 宽重构按扩展-收缩特例处理. 文档只供 LLM 使用, 不要求我阅读文档后确认.

按信源顺序收集 `EXECUTION.md` 需要的信息: `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, 领域文档, 代码事实. Product/Technical/Decisions 定义意图; 代码事实只验证可行性和既有形状. 信源冲突, 或需要新增/改变决策内容时, 调用 `grilling` skill 盘问我.

输出:
`<产物根目录>/EXECUTION.md`
`<产物根目录>/issues/ISSUE-<NN>-<slug>.md`, 从 `ISSUE-01` 连续编号.
产物根目录默认 `docs/changes/<feature-slug>/`; 调用方可指定其他根目录, 落盘前须和我确认输出目录是否正确.

# 起草垂直切片

把工作拆成 **tracer bullet** issues. Issues 将由全新上下文窗口中的执行 agent 领取, 只有端到端可独立验证的切片才能让执行者无需折返追问.

<vertical-slice-rules>

- 每个切片都走过本变更涉及的适用层的窄而 **完整** 路径, 例如 schema, API, UI, tests. 它是垂直切片, 切勿是单层水平切片
- 完成的切片本身可以演示, 或可独立验证
- 每个切片都应适合一个全新的上下文窗口
- 只有当前切片无法在保持边界和验证的前提下推进时, 才创建阻塞它的预重构 issue

</vertical-slice-rules>

为每个 issue 写出 **blocking edges**: 哪些其他 issues 必须先完成, 这个 issue 才能开始. 没有 blockers 的 issue 可以立即开始.

**宽重构是垂直切片的例外.** 宽重构是一次机械改动. 例如重命名列, 或修改共享符号类型. 
它的 **blast radius** 会扩散到整个代码库. 一次编辑会打断成千上万个调用点. 没有任何垂直切片能独立保持绿色. 切勿强塞成 tracer bullet. 
宽重构按 **扩展-收缩** (先兼容新增, 再迁移旧用法, 最后清理旧形式) 处理: 先让新旧两种形式并存, 再分批迁移调用者, 最后删除旧形式. 这样每一批迁移后都有机会保持项目可验证.

- 兼容扩展 issue: 添加新形式, 保留旧形式, 不大批迁移调用者. 完成后现有路径仍然可用
- 分批迁移 issues: 按 package, 目录或调用者类型分批把使用处从旧形式改到新形式. 每批都是一张 issue, 且由兼容扩展 issue 阻塞. 因为旧形式仍存在, 每批完成后都应能通过验证
- 收缩清理 issue: 确认没有调用者再使用旧形式后, 删除旧形式. 这个 issue 由所有分批迁移 issues 阻塞

若任何分批迁移 issue 单独完成后都无法保持绿色, 仍保留兼容扩展/分批迁移/收缩清理序列, 但这些 issue 不再标为可独立领取. 将它们标为 HITL/integration 特例, 写明共享 integration branch, 每个中间 issue 的局部完成证据, 以及最终整合验证 issue 的整体绿色承诺. 这些 issues 都阻塞最终的整合验证 issue.

起草完成标准: 每个 AC/TG/NFR 被至少一个拟议 issue 覆盖或明确说明无需执行任务; 每个切片符合 vertical-slice-rules; blockers 无环且只包含真正阻塞项; 宽重构已命中特例规则或明确不适用.

# 盘问我

把建议拆分展示为编号列表. 每个 issue 都展示:

- **标题**: 简短描述名
- **被阻塞于**: 哪些其他 issues 必须先完成, 若无则写无
- **交付内容**: 这个 issue 打通的端到端行为

询问我:

- 粒度是否合适? 是太粗, 还是太细?
- Blocking edges 是否正确?
- 是否需要合并或继续拆分 issues?

持续迭代, 直到我批准拆分.

# 固化 Execution Spec 和 issues

按模板生成已批准的 issues, 再生成引用真实 issue 路径的 `EXECUTION.md`. 按依赖顺序编号. 信源与决策的引用路径按实际位置解析, 不假设它们位于产物根目录. 
存在相关 DECISIONS.md 时, 每个 issue 单向引用相关决策 ID, 见 issue 模板的 相关决策 节. 引用只从产物指向账本: DECISIONS.md 是权威信源, 产物是派生视图, 账本不记录产物引用. 不新增或改变决策内容. 无相关决策时 issue 写"无".
不复制 Product/Technical Spec 的正文, 只引用稳定 ID 和执行所需摘要.

完成标准: 
`EXECUTION.md` 任务图中的每个引用可解析; 
覆盖矩阵与批准的拆分一致, 无遗漏; 
每个 issue 有代码定位提示和可执行 TDD 切片, 或明确标记非代码/人工验证/HITL 特例; 
issue 编号连续; 
决策引用单向完整: 每个 issue 的 相关决策 节引用真实存在的决策 ID, 或已明确无相关决策.

<execution-spec-template>
# <变更标题> Execution Spec
## 权威输入
- Product Spec: `<PRODUCT.md 实际路径>`
- Technical Spec: `<TECHNICAL.md 实际路径>`
- Decisions: `<DECISIONS.md 实际路径>` 或"无"
## 全局允许范围
- 可修改的模块, 目录, 文件模式或行为范围.
## 全局禁止范围
- 不可修改的模块, API, schema, 行为或非目标.
## 完成定义
- 必须通过的 build/lint/test/benchmark/人工验证及通过标准.
## 测试策略
- AC/TG/NFR 对应的测试类型, 已确认测试接缝和验证入口.
- 每个 issue 至少有一个可执行 TDD 切片, 或明确说明该 issue 是非代码/人工验证/HITL 特例.
## 任务图
- ISSUE-01: `issues/ISSUE-01-<slug>.md`; 覆盖: AC-001, TG-001; 依赖: 无.
## 覆盖矩阵
- AC-001 -> ISSUE-01 -> TC-001 -> 验证入口.
- TG-001 -> ISSUE-01 -> TC-001 -> 验证入口.
## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围或触碰禁止范围时停止.
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
- Product: `<PRODUCT.md 实际路径>`, AC-001
- Technical: `<TECHNICAL.md 实际路径>`, TG-001, NFR-001
## 相关决策
- `<DECISIONS.md 实际路径>`: D001. 无则写"无".
## 允许范围
可以修改的模块, 目录, 文件模式或行为范围.
## 禁止范围
明确不能修改的模块, API, schema, 行为或非目标.
## 代码定位提示
入口文件, 相关模块, 已有测试位置和必要阅读顺序. 只写定位线索, 不写逐文件实现计划.
## TDD 切片
- TS-001:
  接缝: 已确认的公开测试边界.
  测试用例: TC-001.
  先写的失败测试: 一句话说明测试名称和预期失败原因.
  最小绿色实现范围: 让该测试通过所需的最小行为范围.
  不得测试: 内部实现, 私有方法, 内部协作者调用次数或未确认用例.
  覆盖: AC-001, TG-001.
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
- ISSUE 引用. 无则写"无".
</issue-template>
