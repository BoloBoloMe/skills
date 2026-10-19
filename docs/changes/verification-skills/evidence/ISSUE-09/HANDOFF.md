# HANDOFF: ISSUE-09 benchmark-checklist 粗估例外与结论/PR 主数字

## 交付了什么

在 `workflow/benchmark-checklist/SKILL.md` 上增量三处, 不动已实现的测量前/调优/重复/错误计数/收益上限/基线/一次性实验各节, 也不重复实现 blast-radius:

- 新增 "粗估与选型" 节: 用户只要粗略量级时可用单次测量, 但必须声明单次, 给单位, 同一轮查第 4 问 (失败计数与输出正确性) 与第 7 问 (工作是否在计时区内), 只用来说明量级; 出现非成功响应, 输出与预期不符, 数字与实现常量对不上时继续查因, 暂不下结论, 补齐检查后重测. 选型永远不走这个例外: 两侧版本/数据/缓存/构建/配置都要对齐, 一侧跑默认值先调优再测, 交替重复后按判定词给结论, 补不齐就写无法下结论与缺口.
- "判定" 节补齐: 正式比较的判定要跟齐单位, 每侧次数, 极差, 限制因素; "一律无法下结论" 的清单加上说不出限制因素, 第 4 问错误计数或输出正确性缺失, 第 7 问工作是否发生无法检查.
- 新增 "对外报告" 节: PR 正文只放一个主数字, 带单位, 前后对照与证据链接; 完整次数/极差/方法/失败数/限制因素留在链接材料, 内部验收证据不因对外简短而缩减; 本清单只产出草稿与判定, 提交/推送/开 PR/合并由使用者做.
- `description` 补上 "粗估例外与选型边界, 结论状态与 PR 主数字", 仍是单行人类摘要, `disable-model-invocation: true` 保留.
- 本目录证据: 红轮 1 个会话 5 份产物, 绿轮 2 个会话 3 份记录, 3 份会话转录, 初始夹具全文, 机械检查日志与全量快层原始输出.

## 每个 AC 对应的证据

| AC | 证据文件 | 关键原始材料 |
| --- | --- | --- |
| AC-028-1 单次粗估声明单次, 给单位, 同轮查第 4/7 问, 只用来说明量级 | `TS-001.md` | `green-ts001/docs/green1.md` (a) 节 "单次粗估" 与第 4/7 问 |
| AC-028-2 500 异常时继续查因, 暂不下结论, 补齐后重测 | `TS-001.md` | `green1.md` (b1) 节, 含复跑 24.22ms 与 3.02ms 溯源到 rows=250, 及 7 次正常路径重测 |
| AC-028-2 输出与预期不符时同样处理 | `TS-001.md` | `green1.md` (b2) 节, `checksum_ok=False` 抓到错误输出, 判无法下结论并重测 |
| AC-028-3 选型按完整对照处理两侧条件, 不按粗估给赢家 | `TS-001.md` | `green1.md` (c) 节, 首轮未调优声明不选赢家, 调优后 7 轮交替 liteidx 110.10ms 对 fastidx 40.07ms |
| AC-029-1 PR 正文只有一个主数字, 带单位/前后对照/证据链接 | `TS-002.md` | `green-ts002/docs/green2-pr.md` "性能" 节 |
| AC-029-1 完整次数与极差留在链接材料, 内部证据未缩减 | `TS-002.md` | `green-ts002/docs/green2.md` (a) 表格; `red-round/fixtures/docs_measure-2000.log` 与演练项目 HEAD 里的同名文件 md5 一致 (`fc1544c9f43822b2c752215efff705de`) |
| AC-029-1 不自动开 PR/提交 | `TS-002.md` | `green2-pr.md` 为文件草稿; 演练项目 `git log` 顶端仍是编排者提交 `6052846`, `git status` 只有两个未跟踪记录 |
| AC-029 结论为四选一, 带单位/次数/极差/限制因素 | `TS-002.md` | `green2.md` (a) 判定 "更快" 与四样材料表 |
| AC-029-2 说不出限制因素 / 缺第 4 问错误计数 / 第 7 问无法检查时无法下结论 | `TS-002.md` | `green2.md` (b) 四条缺口与 "不宣称更快, 也不宣称更慢, 也不宣称无差异" |

红轮 (v0 技能) 原始产物: `red-round/docs/red1.md` 到 `red4.md`, PR 草稿 `red-round/docs/red3-pr.md`, 会话转录 `red-round/sessions/bm9-red.jsonl`, 会话对 `bench/two_libs.py` 的改动 `red-round/bench/two_libs.py.diff`.

## 跑过的命令与退出码

- `uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md` -> `OK`, exit 0 (v0 基线与 v1 交付版各一次).
- `uv run python general/writing-for-llm/check_skill.py workflow/blast-radius/SKILL.md` -> `OK`, exit 0 (确认未连带破坏).
- 全角标点扫描 (U+3000-303F, U+FF00-FFEF, U+2018-201F, U+FE10-FE1F) 覆盖 `workflow/benchmark-checklist/**` 与本目录 `*.md` -> `hits=0`. 唯一全角标点是 SKILL.md 第 38 行既有的 U+2014 长破折号, 来自 ISSUE-06 正文, 未改写.
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` -> `7 passed, 18 subtests passed`, exit 0.
- `uv run --with pytest python -m pytest -m "not e2e" -q` -> `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed` (275s), exit 1. 6 个失败是 `general/present/tests/test_browser_session.py` 5 个与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest` 1 个, 均为 socket TimeoutError, 与 ISSUE-07/08 记录的既有失败集合完全一致; `rg -l "benchmark-checklist" tests general` 无命中, 与本 ISSUE 无关. 原始输出 `full-suite.log`.
- 明细见 `machine-checks.log`.

## 会话, 临时项目, 清理

- 宿主: Ubuntu 26.04.1 LTS, 16 核, herdr 0.9.4, pi 1.3.0; 会话模型 `cli/deepseek-v4.1-flash-expires-on-0910` thinking high, 启动参数 `-a` (一次性项目信任, 未改全局配置).
- 加载方式: 临时项目 `.agents/skills/benchmark-checklist/` 里的待测副本 + `/skill:benchmark-checklist <任务>`; 会话转录每条用户消息带该副本的绝对路径前缀; 演练期间全机只有这一份同名技能目录.
- 会话名: `bm9-red` (v0, 红轮四个任务), `bm9-g1` (v1, AC-028), `bm9-g2` (v1, AC-029).
- 提交渠道: `herdr pane send-text` + `herdr agent send-keys <名> "alt+\\"`; 状态与输出用 `herdr agent get` / `herdr pane read --source recent-unwrapped` 读取.
- 临时项目: `/tmp/orchestra-09/lab`, 提交 `3c187b7` (初始材料 + v0) -> `043713c` (红轮记录) -> `a4c29c4` (v1) -> `6f44e57` (绿轮 AC-028 记录) -> `6052846` (复位).
- 清理: 三个演练会话的 tab 全部关闭, 关闭后 `herdr agent list` 与 `herdr tab list` 里没有 `bm9-*`; 未触碰其他执行者的会话. `/tmp/orchestra-09` 在证据抄完后删除 (`rm -rf /tmp/orchestra-09`). 逐轮复位用 `git rm` 加删除未跟踪文件, 没有用 `git reset --hard`.

## 缺口, 风险, 未验证

- 红轮只在本模型上跑红一条: AC-029-1 的 PR 正文 (v0 下把完整中位数/极差表搬进 PR 正文, 且没有证据链接). AC-028 三条与 AC-029-2 在该模型上没跑红, 如实记录, 不写成红轮通过; v0 文本确实没有这些规则 (见 `git show 1049cbb:workflow/benchmark-checklist/SKILL.md`), 但"规则缺失"不等于"行为必然失败", 换模型或换材料可能红, 本轮未验证.
- 演练数字全部来自 `time.sleep` 模拟的受控材料, 只证明方法与判定流程, 不代表任何真实产品性能; 对外引用前须在真实实现上复测.
- PR 草稿的证据链接指向项目内记录文件, 真实仓库需换成证据材料实际位置; 本轮没有真实远端仓库, 换链后的可读性未验证.
- 只在单一宿主 (16 核) 与 pi 1.3.0 + herdr 0.9.4 上做过; 其他运行时点名加载未验证. 未运行 `sync-to-pi.py`, 未写任何全局部署副本, 结论不覆盖全局部署已生效.
- 完整 MIT 许可文本与逐项差异记录按 ISSUE-13 统一补齐; 补齐前该副本不对外发布.

## 提交

- `e977607` feat: ISSUE-09: benchmark-checklist 增加粗估例外与结论 PR 主数字切片
- 证据与本报告的提交见分支 `issue/09` 顶端.
