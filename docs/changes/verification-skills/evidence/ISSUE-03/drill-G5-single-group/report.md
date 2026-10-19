# 独立产品验收报告 (verify-v1-20261019T1250Z)

- 目标提交: `42c51b8a51c216d5689a1c918c319ae4474aafd6` (HEAD, `feat: greet 支持全大写输出`)
- 上一提交 (审计基线): `b0cde8238ee84b94ce0e3f7a39142e75f58a65af`
- 被验项目: `/tmp/orchestra-03/green-single-group`
- 判据来源: `docs/changes/tool-cli/PRODUCT.md` 的 `验收标准` (含 `<!-- confirmed-flow: v1 -->`) 与 `业务规则` 原文
- 证据目录: `docs/changes/tool-cli/verify-v1-20261019T1250Z/`
- 报告时间: 2026-10-19T12:51Z

## 必验清单与逐项结果

| 编号 | 标准摘要 | 材料类型 | 实际操作 / 引用 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
|---|---|---|---|---|---|---|---|
| AC-001-1 | 默认问候: stdout `Hello, Ada!`, 退出码 0 | 当前观察 (实机运行) | `python3 tool.py greet --name Ada` | stdout 恰为 `Hello, Ada!` (print 带行尾换行), stderr 空, 退出码 0 | `ac001-1.log` | 2026-10-19T12:49:12Z, HEAD 42c51b8 | 通过 |
| AC-001-2 | 全大写问候: stdout `HELLO, ADA!`, 退出码 0 | 当前观察 (实机运行) | `python3 tool.py greet --name Ada --shout` | stdout 恰为 `HELLO, ADA!`, stderr 空, 退出码 0 | `ac001-2.log` | 2026-10-19T12:49:12Z, HEAD 42c51b8 | 通过 |
| BR-002 | 不新增第三方依赖, 依赖清单/锁文件/构建材料与上一提交逐项一致 (审计) | 当前观察 (静态材料核对结果, 不是运行行为结果) | `git diff --name-status b0cde82..HEAD`; 对 `deps.txt`, `deps.lock`, `build.sh`, `prepare.sh` 逐个 `git diff b0cde82 HEAD -- <file>` 并比对 `git ls-tree` blob 哈希 | 4 个文件 diff 为空, blob 哈希两提交完全相同 (`bbb5297` / `f5f745d` / `7796246` / `f6c7c17`); 变更仅 `tests/test_tool.py`, `tool.py`, 均不在该项范围 | `br002.log`, `br002-diff-list.log` | 2026-10-19T12:49:36Z, b0cde82 vs 42c51b8 | 通过 |

汇总: 必验 3 项, 通过 3, 失败 0, 未验证 0.

## 派工记录

- 分组依据: 两类场景同打一份成品副本, 同一 `greet` 命令族, 无资源可隔离; 审计 BR 也是同一工作区的静态 git 比对. 总工作量只有 2 条 CLI 命令加 1 次版本比对, 多开会话要重复启动/信任确认/读 Spec 的固定准备, 重复准备大于并行收益. 因此只设 1 组 `G-ALL`, 计划 1 人, 不按 AC 逐条开会话. 计划见 `plan.md`.
- 当轮可用非作者验收者上限: 3; 实际派出: 1 (与组数一致, 未凑人数).
- 验收者: herdr agent `acc-verify`, tab `w1J:t4G`, pane `w1J:p4J`
  - pi session id: `01a15433-cd28-77f7-a744-2113227a15f1`
  - session 文件: `/home/bolo/.pi/agent/sessions/--tmp-orchestra-03-green-single-group--/2026-10-19T12-47-23-432Z_01a15433-cd28-77f7-a744-2113227a15f1.jsonl`
  - 创建时间: 2026-10-19T12:47:23.432Z
  - 模型: `cli/glm-5.3-flash`, thinking `high`; 启动 argv `["pi","--model","cli/glm-5.3-flash:high","--approve"]`, 无 `--session/--continue/--fork`, 不继承任何会话过程
  - 承接标准: AC-001-1, AC-001-2, BR-002
  - 未参与本次实现与修复的可核对事实:
    1. 实现提交 committer 时间 2026-10-19T20:27:16+08:00 (=12:27:16Z), 作者会话 `i03-author` 位于 `/tmp/orchestra-03/author` (状态 done); 验收者 session 创建于 12:47:23Z, 晚于实现提交约 20 分钟.
    2. 该 session 的全部工具动作 (见 `dispatch-facts.log`) 只有 read Spec, 运行两条验收命令, git 比对, 写 `summary.md` 到证据目录; 没有修改产品源码, 配置, 测试, 没有提交.
- 会话记录原件: `session-transcript-acc-verify.txt` (herdr `agent read` 抓取的终端记录), `dispatch-facts.log` (session 元数据与逐条工具动作).

## 覆盖范围与非产品判据

- 本轮只覆盖 PRODUCT.md 列出的 2 个验收场景和 1 条审计 BR, 共 3 项.
- G-002 (统计词数/字符数), G-003 (导出 JSON) 在 PRODUCT.md 中只有目标, 没有验收场景, 不属必验清单, 本轮未判.
- TECHNICAL.md 的 `python3 -m pytest -q`, `bash build.sh`, `bash prepare.sh` + `dist/app.txt` 属操作线索和技术事项, 不是产品通过条件; 本轮未把它们当作通过依据, 也未评内部代码划分.
- 证据目录写入位置: 仓库内 `docs/changes/tool-cli/verify-v1-20261019T1250Z/`, 只含 .md/.log/.txt. build.sh 只编译 `tool.py`, prepare.sh 只写 `dist/app.txt`, pytest 只收集 `tests/`, 因此这些文件不进入构建, 测试发现或运行输入.

## 过程偏差 (如实记录, 不影响结论)

- 验收者中途误建空目录 `docs/changes/tool-cli/verify-v1-202619T1250Z`, 当场 `rmdir` 删除, 无残留 (见 `dispatch-facts.log` 工具动作).
- 验收者把两条场景命令的 stderr 临时重定向到 `/tmp/ac001-1.err`, `/tmp/ac001-2.err` (均 0 字节), 未放在证据目录内; 已由指挥者清理. 原始 stdout/stderr/退出码已完整落在 `ac001-1.log`, `ac001-2.log`.
- 场景期望输出未写行尾换行, 实际 stdout 由 `print` 带一个行尾换行; 按常规 CLI 语义判定为一致, 已在此注明.

## 收尾

- 除本次证据目录的输出外, 源码与 Spec 未变 (HEAD 仍为 42c51b8, `git diff` 为空, 未跟踪文件仅在本证据目录内).
- 本报告不构成正式人工验收, 结论仍需用户逐项确认并走正式人工验收流程; 不宣布正式交付或关闭用户验收.
