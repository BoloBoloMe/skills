# Pre-design Interrogation

写 `planning/design@vN` 前必须关闭并校验 `pre_design` gate。design 前必须无情盘问计划的每个方面，直到双方对目标、范围、约束、方案分支、验证、风险、批准边界和执行分级达成共识。

## 盘问顺序

1. 目标与验收：确认业务目标、成功标准、非目标和不可接受结果。
2. 事实与约束：优先探索仓库、配置、测试、文档和已有资产；只向用户询问探索后仍未知且阻断的内容。
3. 影响边界：确认允许文件、禁止文件、外部系统、数据/安全/兼容边界。
4. 方案分支：列出可行分支及依赖关系，一次只关闭一个分支决策。
5. 风险与回退：确认失败模式、停止条件、回退路径和重新批准触发条件。
6. 验证策略：确认自动验证、人工检查、证据格式和通过/失败判定。
7. 批准与执行分级：确认 tier、批准命令粒度、Plan/Runbook 要求和执行确认边界。

gate 关闭后，运行：

```bash
scripts/validate_interrogation_gate.py --gate pre_design --target planning/design@vN
```
