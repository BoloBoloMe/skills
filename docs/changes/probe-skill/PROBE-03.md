# 状态: 已关闭
# 类型: grilling
# 阻塞于: PROBE-02

## 问题

Probe skill 的 SKILL.md 应包含哪些部分? 大纲和行为规则是什么?

需要确定:

- 两种模式 (绘制 Backlog / 遍历 Backlog) 的入口和流程
- 自检逻辑: 如何判断"需要 Backlog" vs "直接 propose"
- 与 propose 的衔接方式
- 遍历会话中的子代理派发规则 (AFK 并行 / HITL 父会话)
