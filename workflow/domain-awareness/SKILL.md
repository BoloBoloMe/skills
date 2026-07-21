---
name: domain-awareness
description: 只读感知当前工作目录的领域模型.
disable-model-invocation: true
---

从当前工作目录定位所属仓库并读取 `AGENTS.md`. 优先遵循其中的领域文档约定和 `docs/agents/domain.md`; 无约定时探测 `docs/language/`/`docs/adr/`. 多上下文先读 context map, 再读当前任务相关的领域语言和 ADR.
只读, 不创建或修改文件, 不调用 `domain-modeling`. 文档不存在则继续, 不臆造领域事实. 将已定义术语, 边界, 相关 ADR 和冲突返回调用方.
完成标准: 调用方获得当前任务所需的领域上下文, 或明确知道没有可用领域文档.
