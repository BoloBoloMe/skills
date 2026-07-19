# PROBE-03 结论: Probe SKILL.md 大纲

经 grilling 确定完整大纲, 详见最终产物: `/workflow/probe/SKILL.md`.

核心决定:

- 调用方式: 用户调用 (`disable-model-invocation: true`)
- 两种模式: 绘制 Backlog / 遍历 Backlog, 每次会话最多一个非 research Item
- 自检: 单会话能装下 → 直接 propose; 不能 → 绘制
- 战争迷雾 + 范围外: 完整保留 wayfinder 的管理哲学
- 规划而非执行: task 是唯一执行类型
- Item 类型: research (AFK) / grilling (HITL, 调 propose) / prototype (HITL) / task (AFK/HITL)
- 子代理派发: research 并行上限 3, 其余串行
- AFK→HITL 切换: research 解锁新 HITL Item 时询问用户是否继续
- 产物: BACKLOG.md + ITEM-NN.md + 阻塞连线图, 放 `docs/changes/<feature-slug>/`
