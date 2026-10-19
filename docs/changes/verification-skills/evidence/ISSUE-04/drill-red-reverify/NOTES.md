# drill-red-reverify: 旧版技能的修复后复验失败演练 (TS-002 红, AC-007)

## 目的

证据起点: 确认改动前的 `workflow/verify-change/SKILL.md` (md5 `9ac67b01f3e9a5d3714e3292dcba6277`) 没有复验规则, 结果是参与修复的验收者继续承担独立验收, 已关闭的验收会话不被替换, 修复后的验证停在等待旧会话.

## 待测版本与加载方式

- 源文件: 工作树 `workflow/verify-change/SKILL.md` 改动前版本, 原件 `../logs/SKILL-v2-red.md`.
- 加载方式: 复制到 `/tmp/orchestra-04/red-reverify/.agents/skills/verify-change/`, 新 pi 会话用 `/skill:verify-change <任务>` 点名加载.

## 夹具与目标提交

- 夹具: `/tmp/orchestra-04/red-reverify` (从平行夹具 clone 后换成单实例版).
- 首轮被验提交 (含真实缺陷): `cd087542b4610c49ded0a1278fe8065726b62d9d`, `Board.report()` 把 state 写死成 `loading`.
- 修复提交: `ad2ed33496a31c59333dccdd6422e69a89bbbc19` (`fix: report 输出实例真实状态而非硬编码 loading`), 由第 1 轮的验收者会话在修复阶段亲自完成. 见 `fix-commit.txt`, `git-log.txt`.
- 产品标准: `docs/changes/relay-board/PRODUCT.md` (4 个场景 + 1 条审计 BR).

## 执行经过

1. 首轮验收: 指挥者 `i04-r2` (pi session `01a15455-83b2-74f5-ab2b-4b2640d482b9`, 启动 21:24:12) 派 2 名验收者 (`verify-g1` session `01a15457-d661...`, `verify-g2` session `01a15457-d660...`, 21:26:45). `verify-g2` 实跑 4 次都得到 `state=loading`, AC-003 判失败. 首轮报告见 `verify-r1/REPORT.md`.
2. 修复: 操作者恢复 `verify-g2` 的 pi 会话 (同 session id, `pi --session ...`), 让它修复并提交 `ad2ed33`, 作者材料写到 `/tmp/orchestra-04/author-materials/red/`. 记录见 `author-materials/`, `logs/verify-g2-fix.*`.
3. 复验: 操作者按调用方安排把复验任务交给同一个 `verify-g2` 会话 (`logs/verify-g2-reverify.prompt.txt`). 它绑定了新提交 `ad2ed33`, 重跑 AC-002/003/004 三项并写 `verify-r1/verifier-b/REVERIFY-ad2ed33.md`.
4. 缺口: 它需要 AC-001 的第 2 轮截图, 但 `verify-g1` 的会话已在首轮结束时关闭. 它没有新开非作者会话, 而是轮询一个已关闭会话的目录, 先等 10 分钟再等第 2 个 10 分钟; 操作者插话说明该会话已关闭后, 它以"AC-001 不在我的复验范围"收尾, 自述"无流程偏差".

## 结论

- AC-007-2 不满足: 亲自动手修复的验收者继续承担受影响标准的独立验收, 还给出了该缺陷的通过结论; 它参与修复前的证据也没有交给其他非作者核对.
- AC-007-1 的"原会话关闭时换新验收会话"不满足: 旧会话已关闭时旧版不会新开, 只会等待, 16 分钟没有产出; AC-001 的第 2 轮观察因此缺失.
- AC-007-3 不满足: 没有"调用方未选择恢复"分支的处理规则, 也没有"不因原会话不可用而阻塞"的行为.
- AC-007-4 不满足: 受影响关键路径 (report) 由修复者本人实跑, 作者材料与验收观察是同一个人, 不构成非作者实跑.
- 部分做对的地方如实记录: 它确实绑定了新提交 `ad2ed33`, 也重跑了 3 项; 这与"没有复验规则"并不矛盾, 因为同一会话接着做下去本来就会看到新 HEAD.

## 限制

- 复验前的"验证者会话恢复"由操作者用 `pi --session` 完成; 旧版技能自己没有恢复会话的规则. 这正好是 AC-007 要补的能力缺口.
- 首轮指挥者在结束时关闭了两个验收者会话, 所以复验时不存在可恢复的 `verify-g1`; 这对应"原验收会话已关闭"的例子, 不是夹具故障.
