# 独立验收报告 - 记录板 (第 1 轮)

- 目标提交: d1f656ed1c928f74aa6adf9fd69b067a11f1ad72 ("初始化记录板骨架与产品标准", 提交时间 2026-10-19T23:09:40+08:00)
- 判据来源: docs/changes/board/PRODUCT.md, `验收标准` 节 confirmed-flow: v1, 2 个场景 + `业务规则` 节 1 条 (审计) 规则 = 必验清单 3 项
- 证据目录: docs/changes/board/evidence/r1-d1f656e-20261019T152113Z/
- 本轮日期: 2026-10-19, 验收者操作时段 UTC 15:22:04Z~15:26:47Z

## 逐项结果

| 编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 (验收者本轮实跑) | README 起实例后 `python3 app.py health --port 18201`(前提), `python3 app.py status --port 18201` | health: `ok instance=board` exit=0; status 输出含 `instance=board`, `state=ready`, `version=relay-v2`, exit=0 | raw/01-serve-health.txt, raw/02-ac001-ac002.txt, 逐条比对见 11-ac001.md | 2026-10-19T15:22:46Z~15:22:56Z / d1f656e | 通过 |
| AC-002-1 | 当前观察 (验收者本轮实跑) | `python3 app.py report --port 18201`; `cat deps.txt` 比对 | `relay-report instance=board version=relay-v2 dep=1.3` exit=0; deps.txt = `relaylib (vendor) 1.3`, dep 1.3 一致 | raw/02-ac001-ac002.txt, 比对见 12-ac002.md | 2026-10-19T15:22:56Z / d1f656e | 通过 |
| BR-001 (审计) | 当前观察 (运行过程断言, 本轮实跑) | 全程确认 18290 无监听 (`ss -ltn` 判定 18290 未监听, 二次精确核对 `ss_grep_exit=1`); relay 不可用下取 status/report; 再让实例经一次 sync 失败 (`HTTP Error 503`, exit=1) 后复查 status/report | 三次取样的 version 恒为 `relay-v2` (status 与 report 皆同), 失败前后无变化; version 来源另有只读代码补充 (app.py 内常量 `VERSION`) 标为推断, 未顶替运行记录 | raw/03-br001.txt, raw/04-br001-precheck-fix.txt, 结论见 13-br001.md | 2026-10-19T15:22:04Z~15:23:37Z / d1f656e | 通过 |

汇总: 通过 3 项, 失败 0 项, 未验证 0 项.

## 派工记录

- 场景组划分: 3 项全部绑定同一被验对象 (标准钉住 `127.0.0.1:18201`, 实例名 `board`), 都是对该实例的只读查询;
  BR-001 的 "relay 不可用" 前提在当轮环境天然成立, 与两个场景共用同一实例. 拆组只能靠新开实例/改端口,
  按规则不得为制造并行去加实例, 故判定为一个不可再分组, 只派 1 人. 计划原文: 00-plan.md.
- 可用非作者会话: 可新开 (不限); 计划人数 1, 实际派出 1; 只派一人的理由: 唯一场景组 + 共用准备不可复用于其他组.
- 验收者: herdr agent `verify-board-r1` (tab w1E:t19, pane w1E:p19), kind pi, model cli/glm-5.3-flash, thinking xhigh
  (选型依据: llm-select 候选 4 个, 选 review 画像 1.000 且无弱依据维度、价格便宜的 glm-5.3-flash; thinking 取第二深档 xhigh).
- 验收者 pi 会话: 01a154c0-d72b-714e-beef-91e54c438937, 会话文件 2026-10-19T15-21-26-571Z_01a154c0-d72b-714e-beef-91e54c438937.jsonl,
  创建时间 2026-10-19T15:21:26Z.
- 未参与本次实现与修复的可核对事实: (1) 会话创建时间 15:21:26Z 晚于唯一实现提交时间 15:09:40Z;
  (2) 新开会话, 未 fork/continue 实现会话, 不继承其过程; (3) 该会话工具调用记录只有 read (派工单, PRODUCT.md, app.py),
  bash (查验与取证命令), write (仅证据目录内文件), 没有任何改动产品文件的动作; (4) 本轮 `git diff` 为空,
  工作区相对 d1f656e 只有证据目录未跟踪文件.
- 承接标准: AC-001-1, AC-002-1, BR-001 (全部 3 项), 派工单 01-workorder-verify-board-r1.md.
- 共用准备: 起实例 `serve --port 18201 --instance board --data-dir runtime/board` 由该验收者执行一次 (PID 4189728, 15:22:44Z 启动).
- 原始材料归属: raw/01~05 全部由 verify-board-r1 本轮产生; 无跨会话共享材料, 无需接收方适用性复核.
- 组开始/结束: 15:22:04Z 开始, 15:25:02Z 实例清理完成, 15:26:47Z 材料封笔.
- 争用片段: 只有 "实例启动并占用 18201" 一段写入, 由唯一验收者按 启动 -> 只读查询 -> 停实例 的顺序自行完成, 无跨会话排队;
  无并行组, 无 "前一段执行者" 记录需要.
- 清理: `kill 4189728` (exit=0), 进程消失 (ps_exit=1), 18201 不再监听 (ss_grep_exit=1), 18290 未触碰 (仍无监听), 见 raw/05-cleanup.txt, 20-cleanup.md.
  指挥者在验收后另行核对: `ss -ltn` 无 1820x/1829x 监听, 无 `app.py serve` 进程.

## 覆盖范围与非产品判据注明

- 覆盖: PRODUCT.md v1 的全部必验项 (2 场景 + 1 审计 BR), 全部在本轮目标提交上实跑, 未引用任何旧观察, 无未验证项.
- 非产品判据: 仓库没有 TECHNICAL.md / EXECUTION.md, 也没有自动化测试与项目级验证配方, 本轮按 README 命令操作;
  验收者另记的代码细节 (version 常量位置, 模块划分) 不属产品判据, 既不判通过也不判失败, 只作补充注明.
- 产品行为之外的环境痕迹: 运行产品产生 `vendor/__pycache__/` 与 `runtime/` (两者均在 .gitignore 内, 未进入版本控制);
  BR-001 过程中执行 `sync` 得到的 503 失败不是本轮判据项, 仅作过程证据.
- 收尾说明: 除本次证据目录的输出 (及被忽略的 runtime/, __pycache__/) 外, 源码与 Spec 未变.

## 结论的使用范围

本轮结论为技术性独立验收, 仍需用户逐项确认并完成正式人工验收; 本报告不宣布正式交付, 也不关闭用户验收.
