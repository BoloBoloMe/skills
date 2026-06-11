---
name: grill-with-docs
description: 一场项目感知的拷问式会话,用既有领域模型,代码事实和已记录决策挑战计划,打磨术语,并在决策成形时内联更新 docs/language/UBIQUITOUS_LANGUAGE.md 与 ADR.由 orchestrate 决定何时使用.
---

<what-to-do>

围绕计划或者方案的每个方面不断追问我,直到我们达成共识.沿着设计树的每个分支往下走,逐一解决决策之间的依赖关系.

一次只问一个问题,对每个问题都提供你推荐的答案.

如果某个问题可以通过探索代码库来回答,就改为探索代码库.

当你认为可以结束追问时,询问我的意见.

</what-to-do>

<supporting-info>

## 领域感知

在代码库探索期间,也查找现有文档:

### 文件结构

大多数仓库只有一个上下文:

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

如果 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 存在,该仓库有多个上下文.该地图指向每个上下文所在的位置:

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

惰性创建文件--只在确实有内容要写时创建.如果不存在 `docs/language/UBIQUITOUS_LANGUAGE.md`,在解析第一个术语时创建它.如果不存在 `docs/adr/`,在需要第一篇 ADR 时创建它.新建 ADR 和 glossary 正文中文优先; `Status` frontmatter key 与状态值保持英文, 代码或领域模型已有英文术语时不强制翻译.

## 会话期间

### 对照词汇表挑战

当用户使用的术语与 `UBIQUITOUS_LANGUAGE.md` 中的既有语言冲突时,立即指出."你的词汇表把 'cancellation' 定义为 X,但你看起来是指 Y--到底是哪一个?"

### 打磨模糊语言

当用户使用含糊或过载的术语时,提出精确的规范术语."你说的是 'account'--你是指 Customer 还是 User?它们是不同的东西."

### 讨论具体场景

讨论领域关系时,用具体场景进行压力测试.发明能探测边缘情况的场景,迫使用户精确说明概念之间的边界.

### 与代码交叉引用

当用户说明某个东西如何工作时,检查代码是否一致.如果发现矛盾,就指出来:"你的代码会取消整个 Order,但你刚才说可以部分取消--哪个是对的?"

### 内联更新 UBIQUITOUS_LANGUAGE.md

当术语被解析清楚时,立即更新 `UBIQUITOUS_LANGUAGE.md`.不要批量攒起来--在发生时就捕获.使用 [UBIQUITOUS_LANGUAGE_FORMAT.md](UBIQUITOUS_LANGUAGE_FORMAT.md) 中的格式.

`UBIQUITOUS_LANGUAGE.md` 应完全不含实现细节.不要把 `UBIQUITOUS_LANGUAGE.md` 当成规范,草稿纸或实现决策的存储库.它只是词汇表,仅此而已.

### 谨慎提出 ADR

只有当以下三项全部为真时,才提出创建 ADR:

1. **难以逆转**--以后改变主意的成本有意义
2. **缺少上下文会令人意外**--未来读者会疑惑"为什么他们要这样做?"
3. **真实权衡的结果**--当时存在真正的替代方案,而你出于具体原因选择了其中一个

如果缺少其中任何一项,就跳过 ADR.使用 [ADR-FORMAT.md](ADR-FORMAT.md) 中的格式.

</supporting-info>
