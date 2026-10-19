# 补验计划: 按项目配方重新核对 (目标提交 d1f656e)

- 目标提交: `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72` (HEAD)
- 判据来源: `docs/changes/board/PRODUCT.md` 的 `验收标准` (确认标记 `<!-- confirmed-flow: v1 -->`)
  与 `业务规则` 中标 `(审计)` 的 BR-001
- 补验对象: 项目自带验证配方 `.agents/skills/verify-board/SKILL.md`
- 证据目录: `docs/changes/board/evidence/accept-d1f656e-recipe-r1/`
- 日期: 2026-10-19

## 影响判断

项目无自动化测试, 无构建脚本, 无测试配置; `app.py` 不扫描 `docs/`. 本轮证据仍写入
`docs/changes/board/evidence/accept-d1f656e-recipe-r1/`, 不会进入构建, 测试发现或运行输入.
`runtime/` 在 `.gitignore` 中. 不覆盖上一轮 `accept-d1f656e-r1/` 的证据.

## 必验清单 (3 条, 编号照 PRODUCT.md 原文)

| 编号 | 类别 | 标准摘要 |
| --- | --- | --- |
| AC-001-1 | 验收场景 | 实例 board 在 127.0.0.1:18201 且 health 返回 `ok instance=board`; status 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 退出码 0 |
| AC-002-1 | 验收场景 | report 输出形如 `relay-report instance=board version=relay-v2 dep=<n>`, 退出码 0, 且 dep 与 `deps.txt` 一致 |
| BR-001 | 审计业务规则 | status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变 |

## 配方与产品标准的已知冲突 (须由本轮实际运行核实)

配方与已确认的 PRODUCT.md 在以下三处不一致; 配方不是产品判据, 只作运行线索:

1. 配方启动命令用 `--data-root runtime/board`, 而 `app.py serve` 接受的是 `--data-dir`;
   字面执行预计启动失败.
2. 配方使用 18001 端口, PRODUCT.md 的 AC 要求 18201.
3. 配方要求 `version=relay-v1`, report 形如 `relay-report instance=board version=relay-v1`
   (不带 dep); PRODUCT.md 要求 `version=relay-v2` 且 report 必须带 `dep=<n>`.

本轮不得用配方自述的"通过"条件替代 PRODUCT.md; 配方步骤实际跑出什么, 照原件记录并单独说明.

## 分组与人数

- 场景组: 唯一组 `R`, 承接配方字面执行, 配方最小修正后的诊断运行, PRODUCT.md 的 3 条必验项.
- 计划人数: 1 名非作者验收者.
- 只派一人的理由:
  1. 配方运行 (18001) 与产品验收 (18201) 虽端口不同, 但都是同一项目的短命令检查,
     拆组只能增加重复准备和会话成本, 无实质并行收益.
  2. 三条 PRODUCT 必验项共用同一实例和同一份 deps.txt, 属不可再分的单组.
  3. 本轮重点是说明"配方实际跑出什么"与"产品判据要求什么", 同一验收者连续执行更易保持证据链完整.
- 并行标记: 无. 资源: 18001 与 18201 顺序使用; 18290 保持不可用 (BR-001 条件); 不启动 relay 替身.

## 执行阶段与原始材料归属

1. **R 阶段: 配方字面执行.** 严格按配方命令, 端口 18001, `--data-root`; 逐条记录 stdout/stderr/
   退出码. 预计 serve 因参数错误退出, health/status/report 因无实例失败; 以实际为准.
2. **R2 阶段: 配方最小修正诊断.** 仅把 `--data-root` 改为 `--data-dir`, 仍在 18001;
   记录 health/status/report 实际输出, 与配方自述的 relay-v1 / 无 dep 期望对照.
   此阶段只说明配方过时, 不作为产品通过依据.
3. **P 阶段: PRODUCT.md 验收.** 在 127.0.0.1:18201 启动 board, health, 逐条实跑 AC-001-1,
   AC-002-1; dep 与 deps.txt 比对.
4. **B 阶段: BR-001.** 在 18290 不可用条件下重跑 status/report, 记录 version 是否改变;
   可补充 connect 追踪或 HTTP 直取比对, 代码阅读只能标推断.
5. 清理: kill 两阶段启动的实例, 删本轮空 runtime/, 记录结果.

- 原始材料: 全部由验收者写入本目录 `acceptor/raw/`; 结果写 `acceptor/result.md`.
- 最终报告: 指挥者写本目录 `report.md`.
- 共用准备: 无跨组共用; 各阶段由同一验收者顺序启动并清理.
- 争用片段: 18001 与 18201 由同一验收者顺序占用, 无并行写者; 清理 kill 由同一验收者执行.

## 验收者限制

- 只读被验项目: 不改 `app.py`, 配方, 配置, 测试, PRODUCT.md; 只在证据目录和 `runtime/` 下写.
- 判据只取 PRODUCT.md; 配方与技术材料只作运行线索, 不把配方期望当通过条件.
- relay 服务不在仓库内, 不启动自建 relay 桩或替身; relay 不可用本身是 BR-001 的观察条件.
- 每条结论标材料类型 (当前观察/引用旧观察/推断/未运行); 推断与未运行只能记未验证.
- 不做修复, 不提交, 不推送.
