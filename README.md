# Skills

本仓库沉淀可复用的 AI coding agent skills.

## 目录

### 通用技能

- [`general/access-web/SKILL.md`](general/access-web/SKILL.md): 网页搜索, 正文提取, 文件下载, 截图, 登录和 JS 交互.
- [`general/grilling/SKILL.md`](general/grilling/SKILL.md): 通过决策树分轮盘问, 逐步敲定设计决策.
- [`general/grill-me/SKILL.md`](general/grill-me/SKILL.md): 结合领域感知和盘问流程, 帮助澄清设计问题.
- [`general/handoff/SKILL.md`](general/handoff/SKILL.md): 将当前会话压缩成脱敏交接文档, 供后续 agent 接手.
- [`general/llm-select/SKILL.md`](general/llm-select/SKILL.md): 根据设备评分和任务画像, 为子代理选择模型与 thinking 档位.
- [`general/opposing-viewpoint/SKILL.md`](general/opposing-viewpoint/SKILL.md): 从反方分析既有观点, 找出薄弱前提并提出替代主张.
- [`general/present/SKILL.md`](general/present/SKILL.md): 把内容生成自包含 HTML 页面并在本地或远程展示.
- [`general/receive-handoff/SKILL.md`](general/receive-handoff/SKILL.md): 读取交接文档, 汇报理解和建议, 不擅自开始后续任务.
- [`general/teach/SKILL.md`](general/teach/SKILL.md): 建立长期学习工作区, 按记录状态持续教授技能或概念.
- [`general/translate-a-skill/SKILL.md`](general/translate-a-skill/SKILL.md): 汉化或适配英文 skill, 保持行为语义和较低上下文负载.
- [`general/use-herdr/SKILL.md`](general/use-herdr/SKILL.md): 操作 Herdr 的工作空间, 标签页, 窗格和 agent 会话.
- [`general/writing-for-llm/SKILL.md`](general/writing-for-llm/SKILL.md): 编写供 LLM 消费的 skill, AGENTS.md 和指针文档.
- [`general/wtf/SKILL.md`](general/wtf/SKILL.md): 把难懂的回答改写成说明背景, 问题, 行动和建议的大白话.

### 工作流技能

- [`workflow/codebase-design/SKILL.md`](workflow/codebase-design/SKILL.md): 用模块, 接口和接缝原则指导代码库设计与可测试性.
- [`workflow/code-review/SKILL.md`](workflow/code-review/SKILL.md): 沿规范和 spec 两条轴分别评审代码变更.
- [`workflow/decision-ledger/SKILL.md`](workflow/decision-ledger/SKILL.md): 记录和维护 DECISIONS.md 中已确认的决策与事实.
- [`workflow/deliberate/SKILL.md`](workflow/deliberate/SKILL.md): 通过盘问关闭产品与技术决策, 并维护相关记录文件.
- [`workflow/diagnosing-bugs/SKILL.md`](workflow/diagnosing-bugs/SKILL.md): 为硬 bug 和性能回归建立反馈循环并定位原因.
- [`workflow/domain-awareness/SKILL.md`](workflow/domain-awareness/SKILL.md): 只读发现当前仓库的领域语言, 边界和相关 ADR.
- [`workflow/domain-modeling/SKILL.md`](workflow/domain-modeling/SKILL.md): 维护领域语言和 ADR, 持续澄清模糊的领域概念.
- [`workflow/explain-diff/SKILL.md`](workflow/explain-diff/SKILL.md): 生成包含背景, 直觉, 代码走读和测验的交互式 diff 讲解页.
- [`workflow/follow-the-money/SKILL.md`](workflow/follow-the-money/SKILL.md): 沿价值流审查变更, 检查授权, 数量和执行造成的资损风险.
- [`workflow/improve-codebase-architecture/SKILL.md`](workflow/improve-codebase-architecture/SKILL.md): 发现架构摩擦, 并提出把浅模块深化的重构机会.
- [`workflow/lazy-dev/SKILL.md`](workflow/lazy-dev/SKILL.md): 用决策阶梯和实现阶梯收敛到最小且无未来负担的方案.
- [`workflow/mailbox/SKILL.md`](workflow/mailbox/SKILL.md): 管理 session 间传信的 mailbox mesh 和 OpenAI 兼容 LLM 中转.
- [`workflow/navigate/SKILL.md`](workflow/navigate/SKILL.md): 在目的地和路线不清时, 用 Roadmap 和 Milestone 组织探索.
- [`workflow/prototype/SKILL.md`](workflow/prototype/SKILL.md): 构建一次性原型, 验证逻辑状态模型或 UI 外观问题.
- [`workflow/tdd/SKILL.md`](workflow/tdd/SKILL.md): 在小型编程任务中用面向接缝的测试执行 TDD 循环.
- [`workflow/tdd-as-orchestra/SKILL.md`](workflow/tdd-as-orchestra/SKILL.md): 将大型任务分给执行者和审核者, 按 TDD 与 worktree 流程协作.
- [`workflow/to-execution/SKILL.md`](workflow/to-execution/SKILL.md): 把 Product/Technical Spec 拆成 Execution Spec 和可执行 issues.
- [`workflow/to-spec/SKILL.md`](workflow/to-spec/SKILL.md): 把已确认的产品和技术决策整理成两份权威 spec.
- [`workflow/use-sandbox-worktree/SKILL.md`](workflow/use-sandbox-worktree/SKILL.md): 管理 host worktree 与 sandbox 容器绑定对的生命周期.
- [`workflow/use-worktree/SKILL.md`](workflow/use-worktree/SKILL.md): 识别, 创建, 删除和迁移 Git worktree, 并执行安全检查.
