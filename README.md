# Skills

本仓库沉淀可复用的 AI coding agent skills. `workflow/probe` 是大任务入口, `workflow/deliberate` 是常规任务入口.

调用策略: `probe`/`deliberate` 等 workflow skills 使用用户调用; `domain-awareness`/`decision-ledger` 等共享能力使用模型调用.

## 目录

```text
.
|-- general/                     # 通用交互/写作/访问技能
|-- workflow/                    # 代码库工作流技能
|-- others/                      # 特定技术栈技能
|-- docs/                        # 本仓库领域/ADR/变更资料
|-- deprecated/                  # 已归档技能
|-- pi/                          # pi agent 配置 (AGENTS.md, extensions, ...)
`-- README.md
```

## Spec 工作流

主链:

```text
probe -> deliberate
  -> to-product-spec
  -> to-technical-spec
  -> to-execution-spec
  -> afk
```

- `probe`: 当任务超出单会话容量时, 绘制 Roadmap 拆分决策调查, 遍历关闭后路径清晰, 移交 deliberate.
- `deliberate`: 在会话中关闭产品和技术设计树, 延迟固化到盘问结束, 可选生成 Spec 链.
- `to-product-spec`: 把已确认产品结果写入 `PRODUCT.md`.
- `to-technical-spec`: 把已确认技术设计写入 `TECHNICAL.md`.
- `to-execution-spec`: 生成 `EXECUTION.md`, 首 issue 全文与后续切片粗轮廓 (由 `afk` 按重切授权随实现物化) 和 AFK 步骤文件.
- `afk`: 按当前 issue 调度 worker/reviewer, 完成实现/审查/验证/证据闭环.

Spec Pack 和运行文档只供 AI 使用. 人类不通过阅读文档批准方案. 影响产品, API, 架构, 范围, 风险或验证的决定必须在 `deliberate` 会话中解释并确认. 后续 Spec skill 只能整理已确认内容, 发现新决策或冲突时退回盘问.

## 目标项目结构

```text
project-root/
|-- AGENTS.md
|-- docs/
|   |-- agents/
|   |   |-- issue-tracker.md
|   |   `-- domain.md
|   |-- language/
|   |   |-- UBIQUITOUS_LANGUAGE.md
|   |   `-- UBIQUITOUS_LANGUAGE_MAP.md
|   |-- adr/
|   `-- changes/
|       `-- <feature-slug>/
|           |-- PRODUCT.md
|           |-- TECHNICAL.md
|           |-- EXECUTION.md
|           |-- DECISIONS.md
|           |-- issues/
|           |   |-- ISSUE-01-<slug>.md
|           |   `-- ISSUE-02-<slug>.md
|           `-- afk-running/
|               |-- _current.md
|               |-- step-01.md ~ step-06.md
|               `-- ISSUE-01/
`-- src/
```

每类事实只有一个权威来源:

- 产品结果和验收: `PRODUCT.md`.
- 技术设计和机器契约索引: `TECHNICAL.md`.
- 执行边界/任务图/DoD: `EXECUTION.md`.
- 决策历史和代码追踪: `DECISIONS.md`.
- 单个执行单元: `issues/ISSUE-*.md`.
- 运行状态和证据: `afk-running/`.

## Workflow skills

- `workflow/probe`: 大任务入口 — 绘制和遍历决策调查 Roadmap.
- `workflow/probe`: 大任务入口 — 绘制和遍历决策调查 Roadmap.
- `workflow/setup-workspace`: 初始化 Spec 工作区和领域文档约定.
- `workflow/deliberate`: 会话式产品/技术盘问与决策关闭.
- `workflow/to-product-spec`: Product Spec 生成.
- `workflow/to-technical-spec`: Technical Spec 生成.
- `workflow/to-execution-spec`: Execution Spec/issue/AFK 步骤生成.
- `workflow/afk`: AFK 父会话控制器.
- `workflow/decision-ledger`: 功能级决策账本.
- `workflow/tdd`: red-green-refactor 实现循环.
- `workflow/lazy-design`: 最小可交付设计约束.
- `workflow/lazy-code`: 最小正确实现约束.
- `workflow/domain-awareness`: 只读感知领域语言和 ADR.
- `workflow/domain-modeling`: 维护领域语言和 ADR.
- `workflow/codebase-design`: deep module/interface/seam 设计词汇.
- `workflow/improve-codebase-architecture`: 架构评审报告.
- `workflow/code-review-with-me`: 会话式代码评审.
- `workflow/use-worktree`: Git worktree 管理.
- `workflow/receive-handoff`: 接收会话交接.

## AFK

`afk` 是运行时无关父会话控制器. 它不绑定具体子代理插件, 不直接编写生产/测试代码, 不替代 reviewer. `to-execution-spec` 生成全 feature 共用的 6 个步骤文件, `afk` 每次只读取 `_current.md` 和当前步骤, 按状态机推进.

执行前必须在会话中说明当前 issue 的可观察结果, 代码边界, 验证方式和最高风险, 再询问 `是否执行?`. 停止或完成时直接在会话中说明影响/结果/风险, 不要求人类阅读运行产物.

## Setup

首次在目标项目使用 Spec 工作流时运行 `setup-workspace`. 它生成或更新:

- `AGENTS.md` 中的文档目录约定.
- `docs/agents/issue-tracker.md`.
- `docs/agents/domain.md`.

## 其他技能

`general/` 包含网页访问, 仓库探索, grilling, handoff, 教学, skill 编写等通用能力. `others/` 包含支付评审和 Spring Boot Hurl 生成器. `deprecated/` 仅保留历史资料, 新流程不依赖它.

## 维护

- 新 skill 使用独立目录和 `SKILL.md`.
- 需要生成文档或与我交流的 workflow skill, 必须在 frontmatter 后第一条调用 `domain-awareness`.
- 强约束写入 skill, 不只存在于脚本或对话.
- 一个意义只保留一个权威位置.
- 修改主链名称/产物/路径时同步 `setup-workspace`, `README` 和所有引用方.
- skill 文档站在我的第一视角: agent 是"你", 发起者是"我".
