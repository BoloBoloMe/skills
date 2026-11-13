---
name: domain-awareness
description: 只读感知当前工作目录的领域模型.
disable-model-invocation: true
---

# 领域感知

判断任务处于哪个阶段:
- 设计阶段: 优先遵循仓库内 `AGENTS.md` 的领域文档约定, 无约定时探索仓库内的 `docs/language/`, `docs/adr/`.
- 执行阶段: 任务已经拆分成可执行切片, 跳过探测; 已有产物 (EXECUTION.md, issue) 记录的领域信息与本轮一致时直接复用, 不重复探测或复述.

只读. 不创建或修改任何文件. 文档不存在则如实报告, 不臆造领域事实.
将已定义术语, 边界, 相关 ADR 和冲突返回调用方.
完成标准: 阶段已判定; 设计阶段已给出所循约定的实际路径或报告无约定, 并列出找到的术语, 边界与 ADR 位置; 执行阶段已指到复用的产物位置, 或说明为何仍需探测.

布局与单/多上下文判定: 仓库的 `docs/language/` 下有多份上下文文件, 或有 `docs/language/contexts/` 时读 `REPO-LAYOUT.md`.
要新建或改写 `docs/language/` 下的文件: 读 `UBIQUITOUS_LANGUAGE_FORMAT.md`.
要新建或改写 ADR: 读 `ADR-FORMAT.md`.
