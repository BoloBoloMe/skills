# 为 LLM 写文档

writing-for-llm 的写作上下文: 一切由 LLM 消费的文档 — skill, `AGENTS.md`/`CLAUDE.md`, 由 *指针* 抵达的文档. 术语统一, 让每个词稳定指向同一对象.

## 语言

**LLM**:
大语言模型, 这些文档的读者.
_避免_: AI, 模型, 大模型

**harness**:
运行 LLM 的外壳: 与 LLM (及累积上下文) 合起来就是 agent.
_避免_: scaffold, 框架, 平台

## 示例对话

我: 文档里写 "向模型解释为什么" 可以吗?
维护者: 写 "向 LLM 解释为什么". AI 和 模型 是避开的别名, 同一对象只用一个称呼.
我: 那 agent 呢? 文档里到处在说 agent.
维护者: 不同对象: agent 是运行 LLM 的 harness 与上下文, LLM 是被它包装的读者. 指运行机制用 agent, 指读懂并遵循文档的读者用 LLM.
