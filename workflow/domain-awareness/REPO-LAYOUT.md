# 领域文档参考布局

多数仓库是单上下文:

```text
project-root/
|-- docs/
|   |-- language/
|   |   `-- UBIQUITOUS_LANGUAGE.md
|   `-- adr/
|       |-- 0001-slug.md
|       `-- 0002-slug.md
`-- src/
```

多上下文仓库存在 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 它列出各上下文及其关系:

```text
project-root/
|-- docs/
|   |-- language/
|   |   |-- UBIQUITOUS_LANGUAGE.md
|   |   |-- UBIQUITOUS_LANGUAGE_MAP.md
|   |   `-- contexts/
|   |       |-- ordering.md
|   |       `-- billing.md
|   `-- adr/
|       |-- 0001-system-wide-decision.md
|       `-- contexts/
|           |-- ordering/
|           `-- billing/
`-- src/
```

先读 `UBIQUITOUS_LANGUAGE_MAP.md` 确定上下文边界, 再读根级 `UBIQUITOUS_LANGUAGE.md` 和当前任务相关的上下文语言与 ADR