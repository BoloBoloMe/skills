---
name: domain-awareness
description: 只读感知当前工作目录的领域模型.
disable-model-invocation: true
---

# 文件结构

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

领域语言文件格式见 [UBIQUITOUS_LANGUAGE_FORMAT.md](UBIQUITOUS_LANGUAGE_FORMAT.md). ADR 格式见 [ADR-FORMAT.md](ADR-FORMAT.md).

# 读取流程

从当前工作目录定位所属仓库并读取 `AGENTS.md`. 优先遵循其中的领域文档约定和 `docs/agents/domain.md`; 无约定时按上述文件结构探测 `docs/language/`, `docs/adr/`.
多上下文: 先读 `UBIQUITOUS_LANGUAGE_MAP.md` 确定上下文边界, 再读当前任务相关的领域语言和 ADR. 不确定属于哪个上下文时询问.

# 行为约束

只读. 不创建或修改任何文件. 文档不存在则如实报告, 不臆造领域事实.
将已定义术语, 边界, 相关 ADR 和冲突返回调用方.

# 完成标准

调用方获得当前任务所需的领域上下文, 或明确知道没有可用领域文档.
