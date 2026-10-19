# drill-green-parallel-run1: 跨验收者的争用片段先后与并行只读检查 (绿, AC-006-2)

## 目的

验证改动后的技能把"写同一条记录的两个片段"分给两名不同验收者时, 后一段等前一段完成再开始, 两段各留顺序记录, 无关只读检查照常并行.

## 待测版本与加载方式

- 源文件: 工作树 `workflow/verify-change/SKILL.md` md5 `82cb7913d710dfaf3b898c56d17c618c`, 原件 `../logs/SKILL-v3-green.md`.
- 加载: `/tmp/orchestra-04/parallel/.agents/skills/verify-change/` + `/skill:verify-change`; 本轮的夹具产品标准是第一版 (AC-001-1 用文本 status, AC-005-1 只涉及 alpha), 目标提交 `773fc6bf093c3b17f18a8817f924536902f13d2b`.
- 该轮证据目录里的 `PLAN.md` 是第一版计划, 与 `drill-green-parallel` 的最终版计划不同.

## 会话

| 角色 | 会话名 | pi session id |
| --- | --- | --- |
| 指挥者 | `i04-g1b` | 见 `../sessions/green-parallel-run1/` |
| alpha 组 | `ver-alpha` | 见 `../sessions/green-parallel-run1/` |
| beta 组 | `ver-beta` | 见 `../sessions/green-parallel-run1/` |
| 只读组 | `ver-read` | 见 `../sessions/green-parallel-run1/` |

## 实际结果

- ver-alpha 完成 AC-003-1 后写 `coord/record-alpha-done.txt` (22:06:24); ver-beta 轮询该标记 (每 2 秒), 看到后才执行 AC-003-2 (22:07:21-22), 自己的结论里写明"在 record-alpha-done.txt 标记出现后执行", 见 `evidence-773fc6b-r1/ver-beta/RESULT.md`.
- 记录最终 2 行: seq=1 alpha, seq=2 beta (`evidence-773fc6b-r1/` 内 BR-001 材料), 两段没有并发, 没有重复 seq.
- 无关只读检查照常: ver-read 在 22:06:23 拍状态页截图, 22:06:25 跑 report, 与两个写者的 append/job 并行; ver-beta 的 status/job 也在等待标记期间完成.
- 实例由 ver-alpha 统一启动 (22:06:10 写 `coord/instances-up.txt`), ver-beta 与 ver-read 不重启实例.

## 结论

- AC-006-2 通过: 两名验收者写同一共享记录的两段先后执行, 各自留下等待与执行时间记录; 只读检查与写入并行, 没有为并行扩大资源或写入授权.

## 限制

- 该轮 AC-001-1 与 AC-005-1 的产品标准与最终版不同, 所以它只承接 AC-006-2; 并行与共享证据由 `drill-green-parallel` 承接.
