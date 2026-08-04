# 设置领域文档

仓库还没有领域文档约定时, 在根 `AGENTS.md` 建立唯一的 `## 领域文档` 区块, 让之后每个会话的 agent 知道领域文档的布局, 以及约定找谁. 
区块:

```markdown
## 领域文档

<按已确认布局填写路径摘要>
```

## 1. 探索

检查: 根 `AGENTS.md` 是否存在, 是否已有领域文档区块; `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 是否存在 (多上下文信号).

完成标准: 已知 `AGENTS.md` 与区块的存在性, 当前布局信号.

## 2. 会话确认布局

简短说明发现, 一次只问 "使用单上下文还是多上下文?", 并给出推荐:

- 单上下文: `docs/language/UBIQUITOUS_LANGUAGE.md` + `docs/adr/`. 适合大多数仓库.
- 多上下文: 根级 `UBIQUITOUS_LANGUAGE.md` (系统级术语) + `UBIQUITOUS_LANGUAGE_MAP.md` + `docs/language/contexts/` + `docs/adr/contexts/`. 仅当多个 bounded contexts 有独立词义和决策时使用.

完成标准: 我已在会话中选择布局; 不需要阅读文件才能理解该选择的影响.

## 3. 写入

`AGENTS.md` 不存在时, 先询问是否创建. 
添加或更新唯一区块, 不触碰其他内容.

完成标准: `AGENTS.md` 只有一个领域文档区块, 布局摘要与已确认布局一致; 未覆盖无关已有内容.

## 4. 会话交付

直接告诉我: 采用的布局, 创建/更新/删除的路径. 不展示文件全文.

完成标准: 我从会话中知道设置结果, 无需阅读生成文档.
