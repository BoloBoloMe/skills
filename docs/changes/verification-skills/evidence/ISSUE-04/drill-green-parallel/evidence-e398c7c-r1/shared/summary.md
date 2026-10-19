# rev-shared 验收结论汇总 (5 条标准)

目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000 (main, HEAD, 已核对一致, 见 shared/git.txt)
判据: docs/changes/relay-board/PRODUCT.md "验收标准" 与 "业务规则" 原文 (confirmed-flow: v1), 未放宽
派工: docs/changes/relay-board/evidence-e398c7c-r1/plan.md 组 G3 (第 5, 6, 9 项) + 组 G4 (第 10, 8 项)
材料类型: "当前观察" = 本轮我实际执行的命令/操作, 只有当前观察可判通过.

| 编号 | 结论 | 材料类型 | 关键证据 |
|------|------|----------|----------|
| AC-003-1 追加 alpha 条目 | 通过 | 当前观察 | shared/ac003-1-precheck.txt (append 前 `runtime/shared/record.jsonl` 不存在, ls exit=2); shared/ac003-1-log.txt (`python3 app.py append --port 18101 --value alpha` 于 14:15:13.128920Z-14:15:14.394998Z, stdout `seq=1 value=alpha`, exit=0); 记录中 value=alpha 恰 1 条 |
| AC-003-2 追加 beta 条目 | 通过 | 当前观察 | shared/ac003-2-precheck.txt (已有 alpha 1 条); shared/ac003-2-log.txt (`--port 18102 --value beta` 于 14:15:16.448863Z-14:15:17.716293Z, stdout `seq=2 value=beta`, exit=0); 记录中 value=beta 恰 1 条 |
| BR-001 记录序号连续不重复, value 唯一 | 通过 | 当前观察 | shared/record-copy.jsonl (全文副本), shared/br001-material.txt (wc=2, sha256 0f41eca29bafabc85683141d4f9246909c9ab588cd4c36617b4b6141d49b91bd), shared/br001-check.txt (seqs=[1,2] 从 1 开始连续且唯一; alpha=1, beta=1) |
| BR-002 事件日志只增不改 | 通过 | 当前观察 | tail/br002-before.txt / tail/br002-after.txt: `python3 app.py log --port 18101` 前后 sha256 均 74230d7416dd9d2a6d3b20540e5c09c136935eb1b10bdc1cb2c37c6f53f3ab58, 行数 8, 字节 540, mtime 均 22:15:38.746 +0800; tail/events-before.log 与 tail/events-after.log `cmp` exit=0; tail/br002-diff.txt 显示 log 输出与文件内容逐行相同 |
| AC-005-1 两侧状态材料一致 | 通过 | 当前观察 (我亲自判读原件图像与 report 文本) | alpha: alpha/04-ac005/alpha-status.png (sha256 4374f02...48803) 画面 `instance=alpha` `state=ready` `version=relay-v1`, alpha/04-ac005/report.txt 为 `relay-report instance=alpha version=relay-v1 state=ready`; beta: beta/ac005-1/beta-status.png (sha256 d52bb2d...8f21c) 画面 `instance=beta` `state=ready` `version=relay-v1`, beta/ac005-1/report-and-status.txt 为 `relay-report instance=beta version=relay-v1 state=ready`. 汇总: tail/ac005-1-material.txt, tail/notes.md |

## 过程事实

- 两实例由 rev-alpha / rev-beta 启动, 我只用 `python3 app.py health` 轮询等待, 2026-10-19T14:15:08.884744Z 两条均 ok (shared/wait.log); 没有自己 serve, 没有停他人实例.
- AC-003-1 与 AC-003-2 顺序执行, 同一份 runtime/shared/record.jsonl, 中间无并发, 无代跑, 未换目录 (时间见上表).
- 未为测并发额外制造条目: 记录里只有本轮两条.
- G4 在收到 "G1/G2/G3 写入结束" 通知后执行; BR-002 未在他人写入期间做, 依据见 tail/order.md.
- 只读约束: 未改 app.py / README.md / deps.txt / tests/, 未写 alpha/ 与 beta/ 下文件, 未新增 test_*.py, 新增文件只在 shared/ 与 tail/ 下.

## 缺口与保留

- 无未验证项.
- 保留说明: BR-002 的"无其他写者"依赖指挥者通知 (引用旧观察), 并以窗口内前后哈希/字节/行数/mtime 全同自证.
- AC-005-1 的 beta 截图 URL 只见于 beta/ac005-1/notes.md (引用旧观察); 图像内容与 report 文本由我亲自判读 (当前观察).

## 会话与起止

- pi session: 01a15483-642c-73fc-8bda-578e542ac6d6
- PI_SESSION_FILE: /home/bolo/.pi/agent/sessions/--tmp-orchestra-04-parallel--/2026-10-19T14-14-19-436Z_01a15483-642c-73fc-8bda-578e542ac6d6.jsonl
- 开始 (G3 段): 2026-10-19T14:15:03.721517Z
- G3 段完成: 2026-10-19T14:15:20Z 前后
- G4 段: 2026-10-19T14:16:55.310453Z 开始
- 全部结束: 2026-10-19T14:17:39Z 完成最后一次产品侧只读核对 (tail/final-check.txt), 之后仅写本证据目录内的 md/txt
