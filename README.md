# Skills

本仓库沉淀可复用的 AI coding agent skills.

## 目录

```text
.
|-- general/                     # 通用技能
|-- workflow/                    # 代码库工作流技能
|-- docs/                        # 本仓库领域/ADR/变更资料
|-- deprecated/                  # 已归档技能
|-- pi/                          # pi agent 配置 (AGENTS.md, extensions, ...)
`-- README.md
```

## 目标项目结构

```text
project-root/
|-- AGENTS.md
|-- docs/
|   |-- language/
|   |   |-- UBIQUITOUS_LANGUAGE.md
|   |   |-- UBIQUITOUS_LANGUAGE_MAP.md
|   |   `-- contexts/
|   |-- adr/
|   |   `-- contexts/
|   `-- changes/
|       `-- <feature-slug>/
|           |-- PRODUCT.md
|           |-- TECHNICAL.md
|           |-- EXECUTION.md
|           |-- DECISIONS.md
|           `-- issues/
|               |-- ISSUE-01-<slug>.md
|               `-- ISSUE-02-<slug>.md
`-- src/
```

每类事实只有一个权威来源:

- 产品结果和验收: `PRODUCT.md`.
- 技术设计和机器契约索引: `TECHNICAL.md`.
- 执行边界/任务图/DoD: `EXECUTION.md`.
- 决策历史和代码追踪: `DECISIONS.md`.
- 单个执行单元: `issues/ISSUE-*.md`.
