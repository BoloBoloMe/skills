# drill-red-parallel (首版): 加载方式有偏差的旧版并行演练

## 说明

这次演练的任务文本是多行提交, 第一行只有 `/skill:verify-change`, 后面才是任务细节. pi 没有把它当成技能命令展开, 模型于是自己按项目结构找到并读取 `.agents/skills/verify-change/SKILL.md`. 行为上仍然是旧版技能内容驱动, 但不是协议要求的"通过 `/skill:<技能名>` 点名加载".

## 结果

- 与 `../drill-red-parallel-load2/` 相同的失败形态: 3 名可用验收者只派 1 名, 10 项串行, 无并行, 无争用顺序记录, 无共享材料移交.
- 证据: `evidence-773fc6b/plan.md` (四个候选组被判为占用同一份资源, 只派 1 人), `evidence-773fc6b/REPORT.md` ("全部 10 项在同一会话内按编号顺序单线程执行").

## 处理

- 本目录保留为补充对照, 不作为 TS-001 的主证据. 主证据用 `../drill-red-parallel-load2/` (正确 `/skill` 点名加载).
- 该次偏差写入 `../HANDOFF.md` 的缺口与风险.
