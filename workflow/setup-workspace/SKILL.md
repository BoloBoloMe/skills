---
name: setup-workspace
description: Workflow 工作区约定初始化. 当仓库缺少 issue tracker, triage 标签或领域文档, 且后续 workflow 需要这些约定时使用.
disable-model-invocation: true
---

# 设置工作区

搭建工程技能所假定的每仓库配置:

- **问题跟踪器(Issue tracker)**--固定使用本地 Markdown:issue 和 PRD 写入 `docs/changes/`
- **分流标签(Triage labels)**--五个标准分流(triage)角色所使用的字符串
- **领域文档**--`docs/language/UBIQUITOUS_LANGUAGE.md` 和 ADR 的位置,以及读取它们的消费规则

这是一个由提示驱动的技能,而不是确定性脚本.先探索,展示发现,向用户确认,然后再写入.

## 流程

### 1. 探索

查看当前仓库,理解它的初始状态.读取已经存在的内容;不要假设:

- 仓库根目录的 `AGENTS.md`--是否存在?其中是否已经有 `## Docs Directory Structure`,`## 文档目录结构`,`## 文档目录结构(Docs Directory Structure)` 或旧版技能配置区块?
- `docs/language/UBIQUITOUS_LANGUAGE.md` 和 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`
- `docs/adr/` 和 `docs/adr/contexts/` 目录
- `docs/agents/`--这个技能之前的输出是否已经存在?
- `docs/changes/`--本地 Markdown issue tracker 的既有约定和内容

### 2. 展示发现并询问

总结已存在和缺失的内容.然后带用户逐一完成两个决策--展示一个区块(section),获得用户回答,再进入下一个.不要一次性倾倒所有问题.

本技能只内置支持**本地 Markdown issue tracker**.无需询问或生成任何远程 issue tracker 工作流;即使仓库已有远程 issue,也以 `docs/changes/` 本地 Markdown 约定为准.

**Section A--Triage label 词汇.**

> 解释:当 `triage` 技能处理传入 issue 时,它会让 issue 通过一个状态机--需要评估,等待 reporter,准备好由 AFK agent 接手,准备好由人类处理,或不会修复.为此,它需要应用与你实际使用的字符串匹配的状态值.如果你的仓库已经使用不同的名称(例如 `bug:triage` 而不是 `needs-triage`),请在这里映射它们,这样技能会写入正确的状态,而不是制造重复词汇.

五个标准角色:

- `needs-triage`--maintainer 需要评估
- `needs-info`--等待 reporter
- `ready-for-agent`--已完整说明,适合 AFK(agent 无需人类上下文即可接手)
- `ready-for-human`--需要人类实施
- `wontfix`--不会处理

默认值:每个角色的字符串都等于它自己的名称.询问用户是否想覆盖其中任何一个.如果没有既有约定,默认值即可.

**Section B--Domain docs.**

> 解释:一些技能(`improve-codebase-architecture`,`diagnosing-bugs`,`tdd`)会读取 `docs/language/UBIQUITOUS_LANGUAGE.md` 文件来了解项目的领域语言,并读取 `docs/adr/` 来了解过去的架构决策.它们需要知道仓库是一个全局上下文,还是多个上下文(例如分别有 frontend/backend 上下文的 monorepo),这样才能在正确位置查找.

确认布局:

- **单上下文**--`docs/language/UBIQUITOUS_LANGUAGE.md` + `docs/adr/`.大多数仓库都是这样.
- **多上下文**--`docs/language/UBIQUITOUS_LANGUAGE_MAP.md`,指向 `docs/language/contexts/` 下的上下文语言文件(通常是 monorepo).

### 3. 确认并编辑

向用户展示以下草稿:

- 要添加到 `AGENTS.md` 中的 `## 文档目录结构(Docs Directory Structure)` 区块
- `docs/agents/issue-tracker.md`,`docs/agents/triage-labels.md`,`docs/agents/domain.md` 的内容

在写入前允许用户修改.

### 4. 写入

**选择要编辑的文件:**

- 如果仓库根目录存在 `AGENTS.md`,编辑它.
- 如果不存在,询问用户是否创建 `AGENTS.md`--不要替用户静默创建.

如果所选文件中已经存在文档目录结构区块, 就原地更新其内容, 而不是追加重复区块.兼容识别这些标题: `## Docs Directory Structure`,`## 文档目录结构`,`## 文档目录结构(Docs Directory Structure)`.不要覆盖周边 section 中的用户编辑.

如果所选文件中存在包含 Issue tracker,Triage labels,Domain docs 的旧版技能配置区块, 将其标题改为 `## 文档目录结构(Docs Directory Structure)` 并原地更新内容.旧版子标题也要兼容识别: `### Issue tracker`,`### 问题跟踪器`,`### 问题跟踪器(Issue tracker)`,`### Triage labels`,`### 分流标签`,`### 分流标签(Triage labels)`,`### Domain docs`,`### 领域文档`,`### 领域文档(Domain docs)`.

区块:

```markdown
## 文档目录结构(Docs Directory Structure)

### 问题跟踪器(Issue tracker)

本仓库使用本地 Markdown issue tracker: PRD 和 issues 存放在 `docs/changes/`. 见 `docs/agents/issue-tracker.md`.

### 分流标签(Triage labels)

[label 词汇的一行摘要]. 见 `docs/agents/triage-labels.md`.

### 领域文档(Domain docs)

[布局的一行摘要: "single-context" 或 "multi-context"]. 见 `docs/agents/domain.md`.
```

然后使用此技能文件夹中的种子模板作为起点,写入三个 docs 文件:

- [issue-tracker-local.md](./issue-tracker-local.md)--本地 Markdown 问题跟踪器(issue tracker)
- [triage-labels.md](./triage-labels.md)--label 映射
- [domain.md](./domain.md)--领域文档消费规则 + 布局

### 5. 完成

告诉用户设置已完成,以及哪些工程技能现在会读取这些文件.说明他们之后可以直接编辑 `docs/agents/*.md`--只有当他们想重建本地 Markdown 工作区约定或从头开始时,才需要重新运行此技能.
