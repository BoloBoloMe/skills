# 领域文档

工程 skills 在探索代码库时,应该如何使用此仓库的领域文档.

## 探索前,先阅读这些

- **`docs/language/UBIQUITOUS_LANGUAGE.md`**,或
- 如果存在,则阅读 **`docs/language/UBIQUITOUS_LANGUAGE_MAP.md`**--它会指向每个上下文对应的语言文件.阅读与当前主题相关的每一个.
- **`docs/adr/`**--阅读与你即将处理的区域相关的 ADR.在多上下文仓库中,也检查 `docs/adr/contexts/<context>/` 中的上下文级决策.

如果这些文件不存在,**静默继续**.不要提示它们缺失;不要一开始就建议创建它们.生产者 `propose` skill 会在术语或决策真正被澄清时,按需懒创建这些文件.

## 文件结构

单上下文仓库(大多数仓库):

```
/
├── docs/
│   ├── language/
│   │   └── UBIQUITOUS_LANGUAGE.md
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

多上下文仓库(存在 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`):

```
/
├── docs/
│   ├── language/
│   │   ├── UBIQUITOUS_LANGUAGE.md
│   │   ├── UBIQUITOUS_LANGUAGE_MAP.md
│   │   └── contexts/
│   │       ├── ordering.md
│   │       └── billing.md
│   └── adr/
│       ├── 0001-system-level-decision.md
│       └── contexts/
│           ├── ordering/
│           └── billing/
└── src/
```

## 使用 glossary 的词汇

当你的输出提到领域概念时(在 issue 标题,重构提案,假设,测试名称中),使用 `UBIQUITOUS_LANGUAGE.md` 中定义的术语.不要漂移到 glossary 明确避免的同义词.

如果你需要的概念还不在 glossary 中,那就是一个信号--要么你正在发明项目并不使用的语言(请重新考虑),要么确实存在缺口(为 `propose` skill 记录下来).

## 标记 ADR 冲突

如果你的输出与现有 ADR 矛盾,要显式指出,而不是静默覆盖:

> _与 ADR-0007(event-sourced orders)冲突--但值得重新打开讨论,因为......_
