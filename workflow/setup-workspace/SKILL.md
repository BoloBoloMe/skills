---
name: setup-workspace
description: 初始化 Spec 工作区和领域文档约定.
disable-model-invocation: true
---

开始前, 使用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

# 设置工作区

建立工程 skills 所需的每仓库配置:

- Spec Pack/decisions/issues/AFK 产物固定写入 `docs/changes/`.
- 领域语言和 ADR 使用单上下文或多上下文布局.
- `AGENTS.md` 指向 `docs/agents/issue-tracker.md` 和 `docs/agents/domain.md`.

生成文档只供 AI 使用. 我不需要阅读或批准文档正文. 需要我选择的布局必须在会话中解释含义, 影响和你的推荐.

## 1. 探索

读取并检查:

- 根 `AGENTS.md`.
- `docs/agents/`.
- `docs/changes/`.
- `docs/language/UBIQUITOUS_LANGUAGE.md`.
- `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 和 `docs/language/contexts/`.
- `docs/adr/` 和 `docs/adr/contexts/`.

完成标准: 已知道哪些路径存在, 当前仓库是否明显包含多个 bounded contexts, 以及写入是否会覆盖用户内容.

## 2. 会话确认领域布局

在会话中简短说明发现和推荐:

- 单上下文: `docs/language/UBIQUITOUS_LANGUAGE.md` + `docs/adr/`. 适合大多数仓库.
- 多上下文: `UBIQUITOUS_LANGUAGE_MAP.md` + `docs/language/contexts/` + `docs/adr/contexts/`. 仅当多个 bounded contexts 有独立词义和决策时使用.

一次只问"使用单上下文还是多上下文?", 并给出推荐. 不展示生成文档草稿.

完成标准: 我已在会话中选择布局; 不需要阅读文件才能理解该选择的影响.

## 3. 写入

根 `AGENTS.md` 不存在时, 在会话中询问是否创建. 存在时, 添加或更新唯一的 `## Spec 工作区(Spec workspace)` 区块, 不覆盖其他内容.

区块:

```markdown
## Spec 工作区(Spec workspace)

### Spec 和 issues

本仓库使用本地 Spec 工作区: 每个 feature 的 `PRODUCT.md`, `TECHNICAL.md`, `EXECUTION.md`, `DECISIONS.md` 和 issues 存放在 `docs/changes/<feature-slug>/`. issue 使用 `issues/ISSUE-<NN>-<slug>.md`, 并以 `- [ ] 已实现` / `- [x] 已实现` 记录执行结果. 见 `docs/agents/issue-tracker.md`.

### 领域文档(Domain docs)

<single-context 或 multi-context 布局摘要>. 见 `docs/agents/domain.md`.
```

使用本 skill 目录中的种子文件生成或更新:

- `issue-tracker-local.md` -> `docs/agents/issue-tracker.md`.
- `domain.md` -> `docs/agents/domain.md`, 按已确认布局替换对应内容.

完成标准: `AGENTS.md` 只有一个 Spec 工作区区块; 两个 `docs/agents` 文件存在; 路径和所选领域布局一致; 未覆盖无关用户内容.

## 4. 会话交付

直接告诉我: 采用的领域布局, 创建/更新的路径, 哪些 skills 会消费这些约定. 不展示文件全文, 不让我阅读后确认.

完成标准: 我从会话中知道设置结果和影响, 无需阅读生成文档.
