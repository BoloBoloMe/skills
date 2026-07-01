---
name: setup-workspace
description: Workflow 工作区约定初始化, 创建本地议题跟踪器和领域文档约定.
disable-model-invocation: true
---

# 设置工作区

搭建工程 skills 所假定的每仓库配置:

- **议题跟踪器** - 固定使用本地 Markdown: 执行契约和 issues 写入 `docs/changes/`. PRD 只是可选团队汇报文档.
- **领域文档** - `docs/language/UBIQUITOUS_LANGUAGE.md` 和 ADR 的位置, 以及读取它们的消费规则.

这是一个提示驱动的 skill, 而非确定性脚本. 先探索, 展示发现, 向用户确认, 再写入.

## 流程

### 1. 探索

查看当前仓库, 理解它的初始状态. 读取已存在的内容; 不要假设:

- 仓库根目录的 `AGENTS.md` - 是否存在? 其中是否已有 `## Docs Directory Structure`, `## 文档目录结构`, `## 文档目录结构(Docs Directory Structure)` 或旧版技能配置区块?
- `docs/language/UBIQUITOUS_LANGUAGE.md` 和 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`.
- `docs/adr/` 和 `docs/adr/contexts/` 目录.
- `docs/agents/` - 这个技能之前的输出是否已存在?
- `docs/changes/` - 本地 Markdown 议题跟踪器的既有约定和内容.

### 2. 展示发现并询问

总结已存在和缺失的内容. 然后确认领域文档布局. 不要询问或生成远程议题跟踪器工作流; 本技能只内置支持 **本地 Markdown 议题跟踪器**, 即使仓库已有远程 issue, 也以 `docs/changes/` 本地 Markdown 约定为准.

**Section A - Domain docs.**

> 解释: `improve-codebase-architecture` skill 和 `tdd` skill 会读取 `docs/language/UBIQUITOUS_LANGUAGE.md` 了解项目领域语言, 并读取 `docs/adr/` 了解过去的架构决策. 它们需要知道仓库是单上下文还是多上下文 (例如分别有 frontend/backend 上下文的 monorepo), 才能在正确位置查找.

确认布局:

- **单上下文** - `docs/language/UBIQUITOUS_LANGUAGE.md` + `docs/adr/`. 大多数仓库都是这样.
- **多上下文** - `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 指向 `docs/language/contexts/` 下的上下文语言文件 (通常是 monorepo).

### 3. 确认并编辑

向用户展示以下草稿:

- 要添加到 `AGENTS.md` 中的 `## 文档目录结构(Docs Directory Structure)` 区块.
- `docs/agents/issue-tracker.md`, `docs/agents/domain.md` 的内容.

写入前允许用户修改.

### 4. 写入

**选择要编辑的文件:**

- 仓库根目录存在 `AGENTS.md` 时, 编辑它.
- 不存在时, 询问用户是否创建 `AGENTS.md` - 不要替用户静默创建.

所选文件已存在文档目录结构区块时, 原地更新其内容, 而非追加重复区块. 兼容识别这些标题: `## Docs Directory Structure`, `## 文档目录结构`, `## 文档目录结构(Docs Directory Structure)`. 不要覆盖周边 section 中的用户编辑.

所选文件存在旧版三子节 skill 配置区块时, 将其标题改为 `## 文档目录结构(Docs Directory Structure)` 并原地更新为当前两子节内容. 旧版多余子节应删除, 不保留已废弃配置.

区块:

```markdown
## 文档目录结构(Docs Directory Structure)

### 议题跟踪器

本仓库使用本地 Markdown 议题跟踪器: 执行契约和 issues 存放在 `docs/changes/`. 执行契约位于 `docs/changes/<feature-slug>/CONTRACT.md`. issue 只记录任务拆分结果和 `- [ ] 已实现` / `- [x] 已实现` 执行标记. 见 `docs/agents/issue-tracker.md`.

### 领域文档(Domain docs)

[布局的一行摘要: "single-context" 或 "multi-context"]. 见 `docs/agents/domain.md`.
```

然后用本 skill 文件夹中的种子模板作为起点, 写入两个 docs 文件:

- [issue-tracker-local.md](./issue-tracker-local.md) - 本地 Markdown 议题跟踪器.
- [domain.md](./domain.md) - 领域文档消费规则 + 布局.

### 5. 完成

告诉用户设置已完成, 以及哪些工程 skills 现在会读取这些文件. 说明他们之后可直接编辑 `docs/agents/*.md` - 只有想重建议题跟踪器工作区约定或从头开始时, 才需重新运行此 skill.
