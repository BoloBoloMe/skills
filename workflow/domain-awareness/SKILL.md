---
name: domain-awareness
description: 只读感知当前工作目录的领域模型.
disable-model-invocation: true
---

判断任务处于哪个阶段:
- 设计阶段: 优先遵循仓库内 `AGENTS.md` 的领域文档约定, 无约定时探索仓库内的 `docs/language/`, `docs/adr/`.
- 执行阶段: 任务已经拆分成可执行切片, 跳过探测, 直接读 `WORKFLOW_VOCABULARY.md`.

布局与单/多上下文判定读 `REPO-LAYOUT.md`.
领域语言文件格式见 `UBIQUITOUS_LANGUAGE_FORMAT.md`.
ADR 格式见 `ADR-FORMAT.md`.