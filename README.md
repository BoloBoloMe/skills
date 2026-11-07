# Skills

本仓库沉淀可复用的 AI coding agent skills.

## Pi 配置

`pi/models.json` 的密钥只引用环境变量: CLIProxyAPI 用 `CLIPROXYAPI_KEY`, ai-work 用 `CHANG_ZHI_AI_WORK`. 启动前设置, 不将明文写回配置; 安全设置方法与容器注入区别见 [pi/README.md](pi/README.md).

## 目录

调用关系口径: 调用图只画执行调用; 引用, 分工声明与重新派活不算调用边. 维护本仓库时, 调用关系变化须人工核对 README 技能表与各 skill 正文中的执行调用语句, 并经非作者复核.

### 通用技能

| Skill | 说明 |
| --- | --- |
| [`access-web`](general/access-web/SKILL.md) | 网页搜索, 正文提取, 文件下载, 截图, 登录和 JS 交互. |
| [`grilling`](general/grilling/SKILL.md) | 通过决策树分轮盘问, 逐步敲定设计决策. |
| [`handoff`](general/handoff/SKILL.md) | 将当前会话压缩成脱敏交接文档, 供后续 agent 接手. |
| [`llm-select`](general/llm-select/SKILL.md) | 根据设备评分和任务画像, 为子代理选择模型与 thinking 档位. |
| [`mailbox`](general/mailbox/SKILL.md) | 会话间收发信与信箱维护. |
| [`opposing-viewpoint`](general/opposing-viewpoint/SKILL.md) | 从反方分析既有观点, 找出薄弱前提并提出替代主张. |
| [`present`](general/present/SKILL.md) | 把内容生成自包含 HTML 页面, 经常驻 web 服务交付已确认的局域网地址. |
| [`receive-handoff`](general/receive-handoff/SKILL.md) | 读取交接文档, 汇报理解和建议, 不擅自开始后续任务. |
| [`retro`](general/retro/SKILL.md) | 在独立会话中复盘一场或多场其他会话, 提出 agent 环境改进候选. |
| [`teach`](general/teach/SKILL.md) | 建立长期学习工作区, 按记录状态持续教授技能或概念. |
| [`translate-a-skill`](general/translate-a-skill/SKILL.md) | 汉化或适配英文 skill, 保持行为语义和较低上下文负载. |
| [`use-herdr`](general/use-herdr/SKILL.md) | 操作 Herdr 的工作空间, 标签页, 窗格和 agent 会话. |
| [`writing-for-llm`](general/writing-for-llm/SKILL.md) | 编写供 LLM 消费的 skill, AGENTS.md 和指针文档. |
| [`wtf`](general/wtf/SKILL.md) | 把难懂的回答改写成说明背景, 问题, 行动和建议的大白话. |

### 工作流技能

| Skill | 所在环节 | 说明 |
| --- | --- | --- |
| [`software-engineering-consensus`](workflow/software-engineering-consensus/SKILL.md) | 全流程工程约束 | 共享工程概念, 交付与验证边界, 以及本仓库工作流术语. |
| [`navigate`](workflow/navigate/SKILL.md) | 全流程领航 | 用 Roadmap 和分类 Milestone 组织探索, 规格, 执行与独立验证, 每步明确输入和产物目录. |
| [`use-worktree`](workflow/use-worktree/SKILL.md) | 准备工作环境 | 识别, 创建, 删除和迁移 Git worktree, 并执行安全检查. |
| [`use-sandbox-worktree`](workflow/use-sandbox-worktree/SKILL.md) | 准备工作环境 | 管理 host worktree 与 sandbox 容器绑定对的生命周期. |
| [`domain-awareness`](workflow/domain-awareness/SKILL.md) | 领域信息准备 | 只读发现当前仓库的领域语言, 边界和相关 ADR. |
| [`deliberate`](workflow/deliberate/SKILL.md) | 需求与决策澄清 | 通过盘问关闭产品与技术决策, 并维护相关记录文件. |
| [`demo`](workflow/demo/SKILL.md) | 需求与方案讨论 | 制作演示材料, 让人看清指定样子, 行为或过程. |
| [`domain-modeling`](workflow/domain-modeling/SKILL.md) | 领域模型维护 | 维护领域语言和 ADR, 持续澄清模糊的领域概念. |
| [`decision-ledger`](workflow/decision-ledger/SKILL.md) | 决策记录 | 记录和维护 DECISIONS.md 中已确认的决策与事实. |
| [`codebase-design`](workflow/codebase-design/SKILL.md) | 方案设计 | 用模块, 接口和接缝原则指导代码库设计与可测试性. |
| [`to-spec`](workflow/to-spec/SKILL.md) | 规格整理 | 把已确认的产品和技术决策整理成两份权威 spec. |
| [`verify-change`](workflow/verify-change/SKILL.md) | 权威输入确认后/独立验证成品 | 依据已确认的权威输入设计并确认验证方案, 成品实施后按方案独立验证并整理证据. |
| [`lazy-dev`](workflow/lazy-dev/SKILL.md) | 设计与实施方法 | 用决策阶梯和实现阶梯收敛到最小且无未来负担的方案, 可用于设计和实施. |
| [`to-execution`](workflow/to-execution/SKILL.md) | 拆分执行切片 | 把 Product/Technical Spec 拆成 Execution Spec 和可执行 issues. |
| [`verification-contract`](workflow/verification-contract/SKILL.md) | 实施验证契约 | 按改动类型说明如何验证, 什么结果算通过, 以及要留下哪些可复查证据. |
| [`drive-execution`](workflow/drive-execution/SKILL.md) | 实施切片 | 分派实施, 合并, 开发验证与评审返工, 不组织成品独立验证或正式验收. |
| [`code-review`](workflow/code-review/SKILL.md) | 实施后评审 | 按规范, spec 与按门槛纳入的旧行为影响分别评审代码变更. |
| [`blast-radius`](workflow/blast-radius/SKILL.md) | 影响面风险核查 | 调查变更在 diff 之外的影响, 用真实代码证明关键安全事实并交接风险. |
| [`follow-the-money`](workflow/follow-the-money/SKILL.md) | 资损风险核查 | 沿价值流审查变更, 检查授权, 数量和执行造成的资损风险. |
| [`benchmark-checklist`](workflow/benchmark-checklist/SKILL.md) | 性能测量 | 报告或采信性能数字前的测量核查, 覆盖公平调优, 重复与统计, 错误计数, 收益上限, 结论边界与 PR 主数字. |
| [`fix-bugs`](workflow/fix-bugs/SKILL.md) | 问题修复回路 | 修 bug 的详细手法: 复现, 定根因, 出修复方案, 修复复验, 复核没改坏. |
| [`explain-diff`](workflow/explain-diff/SKILL.md) | 交付讲解 | 生成包含背景, 主旨, 证据, 合并风险和测验的交互式 diff 讲解页. |
| [`improve-codebase-architecture`](workflow/improve-codebase-architecture/SKILL.md) | 架构改进探索 | 发现架构摩擦, 并提出把浅模块深化的重构机会. |
| [`codebase-map`](workflow/codebase-map/SKILL.md) | 按需代码库可视化 | 代码库结构与依赖可视化: 分析+常驻服务 (build/serve/stop 三子命令), 只由用户手动调用. |

正式验收由我依据验证证据决定; `verify-change` 的设计方式只产出待我确认的验证方案, 执行方式只负责独立验证并整理证据.
