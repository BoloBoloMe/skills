# drill-R1: 旧版技能的非作者与派工失败演练 (TS-001 / TS-002 红)

## 目的

证据起点: 确认改动前的 `workflow/verify-change/SKILL.md` 在"首次验收必须由未参与实现与修复的新子会话执行"和"按场景组与并行收益定人数"两处不成立.

## 待测版本

- 源文件: 工作树 `workflow/verify-change/SKILL.md`, 改动前版本, md5 `5351807e2e6b18d8ee3bf2696fa391bd`. 原件存 `logs/SKILL-v1.md`.
- 加载方式: 复制到 `/tmp/orchestra-03/red-delegation/.agents/skills/verify-change/`, 新 pi 会话用 `/skill:verify-change <任务>` 提交.

## 夹具与输入

- 夹具: `/tmp/orchestra-03/red-delegation`, 目标提交 `93ba124b07ddc1c9cd845a9f7f4256fc6dee8294`, 5 个验收场景 + 1 条审计 BR.
- 会话: `i03-r1`, pi 会话 `01a15421-859c-755b-b259-07455291386e`, 启动 2026-10-19 20:27:25 CST.
- 任务输入: 目标提交, 产物根目录 `docs/changes/tool-cli/`, "本轮最多可开 3 个验收子会话".

## 实际结果

- 全程只有 1 个会话: 指挥者自己读 PRODUCT.md, 自己运行 5 个场景命令与审计比对, 自己写报告. 没有派出任何子会话 (`logs/i03-r1.agents-before.json` 与 `logs/agents-after-all.json` 中该夹具只有 `i03-r1`).
- 报告自称"单轮", 第 1 节写"当前会话是独立验收指挥者"后直接自己执行, 没有派工计划, 没有验收者会话标识.
- 机械统计 (`SUMMARY.md`): 该会话 `product_runs=2`, `herdr_calls=0`; 报告与原始输出在本目录 `REPORT.md`, `01-version/`, `02-scenarios/`, `03-audit-br002/`, `04-tests/`.

## 结论

- AC-004 的"验收者是未参与实现的新会话"与"指挥者不亲自操作成品"都不满足: 唯一执行产品操作的就是指挥会话本身.
- AC-005 的"派工计划按场景组与并行收益定人数"不成立: 没有任何派工计划, 也没有人数依据.
- 这是 TS-001 / TS-002 的失败证据 (红).

## 风险与限制

- 本轮旧版只有 1 个会话, 因此无法证明旧版会"按 AC 逐条开人"或"单一组拆多人"; 记录的是它完全不派工.
