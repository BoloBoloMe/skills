---
name: domain-awareness
description: 只读感知当前工作目录的领域模型.
disable-model-invocation: true
---

# 读取流程

先判定阶段: 当前任务处于执行阶段 (权威输入在手, 按 spec/issue 落地实现) 而非方案对齐阶段时, 跳过以下探测, 仅恒定返回元词汇表引用 — 执行阶段的问题已由权威输入回答, 重读领域文档只付 token 不换信息.

从当前工作目录定位所属仓库并读取 `AGENTS.md`. 优先遵循其中的领域文档约定; 无约定时按参考布局探测 `docs/language/`, `docs/adr/`, 布局与单/多上下文判定见 [REPO-LAYOUT.md](REPO-LAYOUT.md).
多上下文: 先读 `UBIQUITOUS_LANGUAGE_MAP.md` 确定上下文边界, 再读根级 `UBIQUITOUS_LANGUAGE.md` 和当前任务相关的上下文语言与 ADR. 不确定属于哪个上下文时询问.

领域语言文件格式见 [UBIQUITOUS_LANGUAGE_FORMAT.md](UBIQUITOUS_LANGUAGE_FORMAT.md). ADR 格式见 [ADR-FORMAT.md](ADR-FORMAT.md).

# 行为约束

只读. 不创建或修改任何文件. 文档不存在则如实报告, 不臆造领域事实.
将已定义术语, 边界, 相关 ADR 和冲突返回调用方; 输出恒定包含指向 [WORKFLOW_VOCABULARY.md](WORKFLOW_VOCABULARY.md) 的引用, 无论探测结果如何.

# 完成标准

调用方获得当前任务所需的领域上下文, 或明确知道没有可用领域文档; 执行阶段跳过时如实说明判定.
