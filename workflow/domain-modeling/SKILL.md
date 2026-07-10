---
name: domain-modeling
description: 领域模型维护. 当我需要固定领域术语, 维护 ubiquitous language, 记录 ADR 或同步领域模型时.
---

开始前, 使用 `domain-awareness` skill 只读感知当前工作目录的领域模型.

# Domain Modeling

在设计过程中主动构建和打磨项目领域模型. 本 skill 是主动纪律: 挑战术语, 制造边界场景, 并在术语或决策成形时立即写入领域语言文件或 ADR.

单纯读取 `docs/language/UBIQUITOUS_LANGUAGE.md` 获取词汇不算使用本 skill. 任何 skill 都可以读取领域语言. 只有需要改变模型时才使用本 skill.

## 文件结构

多数仓库是单上下文:

```text
project-root/
|-- docs/
|   |-- language/
|   |   `-- UBIQUITOUS_LANGUAGE.md
|   `-- adr/
|       |-- 0001-event-sourced-orders.md
|       `-- 0002-postgres-for-write-model.md
`-- src/
```

如果存在 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 仓库有多个上下文. map 指向每个上下文的语言文件和关系:

```text
project-root/
|-- docs/
|   |-- language/
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

惰性创建文件: 只有确实有内容要写时才创建. 不存在 `docs/language/UBIQUITOUS_LANGUAGE.md` 时, 在第一个术语被解析清楚时创建它. 不存在 `docs/adr/` 时, 在第一篇 ADR 需要记录时创建它.

## 会话期间

### 对照领域语言挑战

当用户使用的术语与既有领域语言冲突时, 立即指出. 示例: "你的词汇表把 cancellation 定义为 X, 但你现在像是在说 Y. 到底是哪一个?"

单上下文项目对照 `docs/language/UBIQUITOUS_LANGUAGE.md`. 多上下文项目先读 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`, 再对照相关 `docs/language/contexts/*.md`.

### 打磨模糊语言

当用户使用含糊或过载术语时, 提出精确规范术语. 示例: "你说 account. 是指 Customer 还是 User? 它们是不同概念."

### 讨论具体场景

讨论领域关系时, 用具体场景压力测试. 主动制造边缘场景, 迫使用户明确概念边界.

### 与代码交叉引用

当用户说明某个东西如何工作时, 检查代码是否一致. 发现矛盾立即指出. 示例: "代码会取消整个 Order, 但你刚才说可以部分取消. 哪个是事实?"

### 内联更新领域语言

当术语被解析清楚时, 立即更新 `docs/language/UBIQUITOUS_LANGUAGE.md` 或相关 `docs/language/contexts/*.md`. 不要批量积攒. 使用 [UBIQUITOUS_LANGUAGE_FORMAT.md](UBIQUITOUS_LANGUAGE_FORMAT.md) 中的格式.

领域语言文件不含实现细节. 不要把它当成规范, 草稿纸, 或实现决策仓库. 它只是项目领域词汇表.

### 谨慎提出 ADR

只有以下三项全部为真时, 才提出创建 ADR:

1. **难以逆转**: 以后改变主意的成本有意义.
2. **缺少上下文会令人意外**: 未来读者会疑惑为什么这样做.
3. **真实权衡的结果**: 存在真正替代方案, 且选择有具体理由.

缺少任一项则跳过 ADR. 使用 [ADR-FORMAT.md](ADR-FORMAT.md) 中的格式.
