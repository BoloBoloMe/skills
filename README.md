# Skills

本仓库沉淀可复用的 AI coding agent skills.

## 目录

```text
.
|-- general/                     # 通用技能
|   |-- access-web/              # 网页搜索, 正文提取, 文件下载, 截图, 登录和 JS 交互.
|   |-- grilling/                # 通过决策树分轮盘问, 逐步敲定设计决策.
|   |-- grill-me/                # 结合领域感知和盘问流程, 帮助澄清设计问题.
|   |-- handoff/                 # 将当前会话压缩成脱敏交接文档, 供后续 agent 接手.
|   |-- llm-select/              # 根据设备评分和任务画像, 为子代理选择模型与 thinking 档位.
|   |-- opposing-viewpoint/      # 从反方分析既有观点, 找出薄弱前提并提出替代主张.
|   |-- present/                  # 把内容生成自包含 HTML 页面并在本地或远程展示.
|   |-- receive-handoff/         # 读取交接文档, 汇报理解和建议, 不擅自开始后续任务.
|   |-- teach/                   # 建立长期学习工作区, 按记录状态持续教授技能或概念.
|   |-- translate-a-skill/       # 汉化或适配英文 skill, 保持行为语义和较低上下文负载.
|   |-- use-herdr/               # 操作 Herdr 的工作空间, 标签页, 窗格和 agent 会话.
|   |-- writing-for-llm/          # 编写供 LLM 消费的 skill, AGENTS.md 和指针文档.
|   `-- wtf/                     # 把难懂的回答改写成说明背景, 问题, 行动和建议的大白话.
|-- workflow/                    # 代码库工作流技能
|   |-- codebase-design/         # 用模块, 接口和接缝原则指导代码库设计与可测试性.
|   |-- code-review/             # 沿规范和 spec 两条轴分别评审代码变更.
|   |-- decision-ledger/         # 记录和维护 DECISIONS.md 中已确认的决策与事实.
|   |-- deliberate/              # 通过盘问关闭产品与技术决策, 并维护相关记录文件.
|   |-- diagnosing-bugs/         # 为硬 bug 和性能回归建立反馈循环并定位原因.
|   |-- domain-awareness/        # 只读发现当前仓库的领域语言, 边界和相关 ADR.
|   |-- domain-modeling/         # 维护领域语言和 ADR, 持续澄清模糊的领域概念.
|   |-- explain-diff/            # 生成包含背景, 直觉, 代码走读和测验的交互式 diff 讲解页.
|   |-- follow-the-money/        # 沿价值流审查变更, 检查授权, 数量和执行造成的资损风险.
|   |-- improve-codebase-architecture/ # 发现架构摩擦, 并提出把浅模块深化的重构机会.
|   |-- lazy-dev/                # 用决策阶梯和实现阶梯收敛到最小且无未来负担的方案.
|   |-- mailbox/                 # 管理 session 间传信的 mailbox mesh 和 OpenAI 兼容 LLM 中转.
|   |-- navigate/                # 在目的地和路线不清时, 用 Roadmap 和 Milestone 组织探索.
|   |-- prototype/               # 构建一次性原型, 验证逻辑状态模型或 UI 外观问题.
|   |-- tdd/                     # 在小型编程任务中用面向接缝的测试执行 TDD 循环.
|   |-- tdd-as-orchestra/        # 将大型任务分给执行者和审核者, 按 TDD 与 worktree 流程协作.
|   |-- to-execution/            # 把 Product/Technical Spec 拆成 Execution Spec 和可执行 issues.
|   |-- to-spec/                 # 把已确认的产品和技术决策整理成两份权威 spec.
|   |-- use-sandbox-worktree/    # 管理 host worktree 与 sandbox 容器绑定对的生命周期.
|   `-- use-worktree/            # 识别, 创建, 删除和迁移 Git worktree, 并执行安全检查.
|-- docs/                        # 本仓库领域/ADR/变更资料
|-- pi/                          # pi agent 配置 (AGENTS.md, extensions, ...)
`-- README.md
```
