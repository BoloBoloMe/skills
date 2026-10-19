# drill-R2: 旧版技能的派工人数失败演练 (TS-002 红)

## 目的

证据起点: 确认改动前的 `workflow/verify-change/SKILL.md` 不会按"场景组 + 并行收益 + 可用人数"定人数, 也就不会出现"多组低收益时只派一人并写明依据"这类有依据的计划.

## 待测版本

- 源文件: 改动前版本, md5 `5351807e2e6b18d8ee3bf2696fa391bd`, 原件 `../logs/SKILL-v1.md`.
- 加载方式: 复制到 `/tmp/orchestra-03/red-plan/.agents/skills/verify-change/`, 新会话 `/skill:verify-change`.

## 夹具与输入

- 夹具: `/tmp/orchestra-03/red-plan`, 目标提交 `f98bbfebfd974fd68a9f8f3b3ec616fdda637b44`, 3 个只读检查场景 (都读同一份 `dist/app.txt`) + 1 条审计 BR.
- 会话: `i03-r2`, pi 会话 `01a15424-2737-72c2-b9ea-72616ff782b4`, 启动 2026-10-19 20:30:17 CST.
- 任务输入: "本轮最多可开 3 个验收子会话".

## 实际结果

- 没有派出任何子会话, 也没有写派工计划: 指挥者自己 `bash prepare.sh` 一次, 自己读完三行, 自己写报告. 报告头部写"产品验收报告 tool-cli / f98bbfe 第 1 轮".
- 机械统计: `product_runs=3`, `prep_runs=5`, `herdr_calls=0`.
- 原始材料: `REPORT.md`, `run-prepare.log`, `run-scenarios.log`, `audit-br002.log`, `run-aux-tests.log`.

## 结论

- 旧版没有分组规则, 也没有"计划人数与组数, 收益, 可用人数一致"的实际产物. 该行为对 AC-005 的失败成立.
- 它确实"只做一次准备", 但那是因为只有一名执行者, 不是因为按收益判断后决定不拆; 计划与依据缺失本身即失败点.

## 风险与限制

- 不能据此断言旧版必然"逐条 AC 开人"; 记录的是它完全不派工.
