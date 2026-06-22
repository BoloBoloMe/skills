默认用中文回复, 也用中文写落盘文档, 但代码, 命令, 路径, 技术术语, 领域语言保持原文 (通常是英文).
回复写成*电报文*: 短, 准, 高信息密度. 删掉客套, 铺垫, 修饰, 比喻, 语气词, 非必要转折. 保留结论, 原因, 动作, 风险, 边界条件.
任何情况下都只用半角 ASCII 标点. 禁用中文全角标点, 尤其 U+3001. 普通并列用 `,`. 短选项或紧密组合用 `/`. 长并列直接分行写.
不要复述已经读过的文档. 需要引用时, 只给概述和位置, 格式用 `path:start~end`.
遇到需求澄清, 架构设计, 复杂取舍, 风险分析, 可以放宽电报文压缩, 但不能省略关键推理, 边界条件, 决策依据.
**只压缩回复,不省略思考**

## 文档目录结构(Docs Directory Structure)

### 问题跟踪器(Issue tracker)

本仓库使用本地 Markdown issue tracker: PRD 和 issues 存放在 `docs/changes/`. 见 `docs/agents/issue-tracker.md`.

### 分流标签(Triage labels)

使用默认 label 词汇: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. 见 `docs/agents/triage-labels.md`.

### 领域文档(Domain docs)

单上下文布局: `docs/language/UBIQUITOUS_LANGUAGE.md` + `docs/adr/`. 见 `docs/agents/domain.md`.