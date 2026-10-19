# 独立产品验收报告 (第 1 轮)

- 项目: /tmp/orchestra-04/parallel
- 目标提交: e398c7cc7ca4e493d23689bee3cca1a34d306000 (HEAD, main, 提交时间 2026-10-19T22:12:14+08:00)
- 判据来源: docs/changes/relay-board/PRODUCT.md, `验收标准` 节带确认标记 `<!-- confirmed-flow: v1 -->`; 只用其中的 gherkin 场景原文与 `业务规则` 原文 (BR-001, BR-002 均为审计规则).
- 产物根目录: docs/changes/relay-board/
- 本轮证据目录: docs/changes/relay-board/evidence-e398c7c-r1/ (新建, 未覆盖旧证据; 此前无旧证据)
- 验收类型: 首次验收, 不是复验.
- 素材: 没有任何 TECHNICAL.md 或 EXECUTION.md, 因此不存在技术材料顶替产品判据的问题; 本轮不做技术设计评审.

## 版本前提

| 检查 | 结果 |
|------|------|
| `git rev-parse HEAD` | e398c7cc7ca4e493d23689bee3cca1a34d306000 (与调用方给的目标提交一致) |
| 分支 | main |
| 开始验收时 `git status --porcelain` | 空 (已跟踪源码/配置/测试无未提交改动) |
| 开始验收时未跟踪产品文件 | 无; `runtime/` 与 `.agents/` 被 .gitignore 覆盖, runtime/shared 为空目录 (无 record.jsonl, 无 events.log), 由 rev-shared 于 22:15:10 现场确认 (shared/ac003-1-precheck.txt) |
| 收尾时 `git status --porcelain` | 只有 `?? docs/changes/relay-board/evidence-e398c7c-r1/` (本轮证据), 已跟踪文件 `git diff` 为空 |

结论: 版本前提满足, 结论绑定在上面的完整提交标识上, 用户可直接用该提交复核.

## 逐项结果 (必验清单: 8 个场景 + 2 条审计 BR = 10 项)

| # | 标准 | 材料类型 | 实际操作 / 引用信息 | 实际结果 | 证据位置 (相对 evidence-e398c7c-r1/) | 时间 / 版本 | 结论 |
|---|------|----------|--------------------|----------|--------------------------------------|-------------|------|
| 1 | AC-001-1 alpha 状态页与 report | 当前观察 (rev-alpha 实跑) + 指挥者复核图像 | `python3 app.py health --port 18101` 得 `ok instance=alpha`; google-chrome headless 900x400 截图 18101/status-page, exit=0; `python3 app.py report --port 18101` exit=0. 指挥者另亲自读图确认画面文字 | 截图画面为 `instance=alpha` / `state=ready` / `version=relay-v1`; report 原文 `relay-report instance=alpha version=relay-v1 state=ready` (逐字等于判据) | alpha/01-ac001/ (health.txt, screenshot-cmd.txt, alpha-status.png, report.txt, screenshot-sha256.txt); 同图副本 alpha/04-ac005/alpha-status.png (sha256 4374f026…48803) | 22:15:18~22:15:23 +0800; e398c7c | 通过 |
| 2 | AC-001-2 beta 实例状态页 | 当前观察 (rev-beta 实跑) | `python3 app.py health --port 18102` 得 `ok instance=beta`; `python3 app.py status --port 18102`, exit=0, 65 ms | 输出含 `instance=beta`, `state=ready`, `version=relay-v1` 三行, exit=0 | beta/ac001-2/ (health-pre.txt, out.txt, notes.md) | 22:15:08~22:15:10 +0800; e398c7c | 通过 |
| 3 | AC-002-1 alpha 耗时任务 | 当前观察 (rev-alpha 实跑) | `python3 app.py job --port 18101 --ms 4000`, exit=0, 实测 4067 ms (4067316912 ns) | stdout 为 `job-done instance=alpha elapsed_ms=4000`, exit=0, 实际耗时 >= 4000 ms | alpha/02-ac002/job.txt | 22:15:26~22:15:30 +0800; e398c7c | 通过 |
| 4 | AC-002-2 beta 耗时任务 | 当前观察 (rev-beta 实跑) | `python3 app.py job --port 18102 --ms 4000`, exit=0, 实测 4067 ms | stdout 为 `job-done instance=beta elapsed_ms=4000`, exit=0, 实际耗时 >= 4000 ms | beta/ac002-2/out.txt, notes.md | 22:15:12~22:15:16 +0800; e398c7c | 通过 |
| 5 | AC-003-1 追加 alpha 条目 | 当前观察 (rev-shared 实跑) | 前置: 22:15:10 `ls runtime/shared/record.jsonl` -> No such file (exit=2); `python3 app.py append --port 18101 --value alpha`, exit=0 | stdout `seq=1 value=alpha`, exit=0; 记录中 value=alpha 恰好 1 条 | shared/ac003-1-precheck.txt, ac003-1-log.txt, ac003-1-out.txt | 22:15:10 前置, 22:15:13.13~22:15:14.39 执行; e398c7c | 通过 |
| 6 | AC-003-2 追加 beta 条目 | 当前观察 (rev-shared 实跑) | 前置: 记录已有 1 条 alpha; `python3 app.py append --port 18102 --value beta`, exit=0 | stdout `seq=2 value=beta`, exit=0; 记录中 value=beta 恰好 1 条 | shared/ac003-2-precheck.txt, ac003-2-log.txt, ac003-2-out.txt | 22:15:16.45~22:15:17.72; e398c7c | 通过 |
| 7 | AC-004-1 只读查看事件日志 | 当前观察 (rev-alpha 实跑) | 22:15:34 后台起 alpha job (pid 4092125, --ms 4000); 任务存活期间 22:15:36 运行 `python3 app.py log --port 18101`, exit=0, 66 ms; 后台 job 22:15:38 才结束 | log 输出含 `… instance=alpha event=job-start ms=4000`, 且该行之后没有对应 job-end (证明读取时任务仍在执行), exit=0 | alpha/03-ac004/ (run.txt, log.out, job-bg.out) | 22:15:34~22:15:38; e398c7c | 通过 |
| 8 | AC-005-1 两个实例的状态材料互相一致 | 当前观察 (rev-shared 亲自判读两侧原件) + 指挥者复核两张图 | rev-shared 读取 alpha/04-ac005/(截图+report) 与 beta/ac005-1/(截图+report-and-status.txt), 逐项比对; 指挥者另亲自读两张 PNG | alpha: 截图 `instance=alpha` `state=ready` `version=relay-v1`, report `relay-report instance=alpha version=relay-v1 state=ready`; beta: 截图 `instance=beta` `state=ready` `version=relay-v1`, report `relay-report instance=beta version=relay-v1 state=ready`. 每侧截图与 report 的 instance, version 相同, 两侧 report 都含 state=ready | tail/notes.md, tail/ac005-1-material.txt, tail/ac005-1-crosscheck.txt; 原件 alpha/04-ac005/alpha-status.png (4374f02…), alpha/04-ac005/report.txt, beta/ac005-1/beta-status.png (d52bb2d…), beta/ac005-1/report-and-status.txt | 原件产生 22:15:20~22:15:22; rev-shared 核对 22:17:08; e398c7c | 通过 |
| 9 | BR-001 共享记录序号从 1 连续递增不重复, 每个 value 只出现一次 (审计) | 当前观察 (rev-shared 用本轮实际记录核对) | 对 AC-003-1/2 产生的 runtime/shared/record.jsonl 取全文副本 + sha256 + wc; 解析 seq 列表与 value 计数. 未为测并发另造条目 | 2 行, seqs=[1,2]: 从 1 开始, 连续, 不重复; value_counts={alpha:1, beta:1}; 逐项检查全 True; sha256 0f41eca2…b91bd (记录仍在, 现算相同) | shared/record-copy.jsonl, br001-material.txt, br001-check.txt | 22:15:20 +0800; e398c7c | 通过 |
| 10 | BR-002 共享事件日志只增不改, 只读查看前后文件内容不变 (审计) | 当前观察 (rev-shared 在安静窗口实跑) | 收到"G1/G2/G3 写入结束"通知后: 22:16:55.31 取 events.log sha256/行数/字节/mtime 并复制副本; 22:16:57.96 运行 `python3 app.py log --port 18101` (exit=0, 8 行); 22:16:58.31 再取同样四项; `cmp` 两份副本 | 前后 sha256 均 74230d74…3ab58, 行数 8, 字节 540, mtime 均 22:15:38.746 +0800; cmp exit=0; log 输出 8 行与文件逐行相同 (diff exit=0) | tail/br002-before.txt, br002-log-out.txt, br002-log-log.txt, br002-after.txt, events-before.log, events-after.log, br002-diff.txt, tail/order.md | 前后 22:16:55~22:16:58; 最后写入 22:15:38 (alpha job-end); e398c7c | 通过 |

汇总: 10 项全部 通过; 失败 0 项; 未验证 0 项.

## 派工记录

### 组划分与人数依据
- G1 (rev-alpha): 第 1, 3, 7 项 + alpha 侧截图/report 材料. 独占端口 18101 与 runtime/alpha, 并独自负责 alpha 实例启停.
- G2 (rev-beta): 第 2, 4 项 + beta 侧截图/report 材料. 独占端口 18102 与 runtime/beta, 并独自负责 beta 实例启停.
- G3 (rev-shared 前段): 第 5, 6, 9 项. 是 runtime/shared/record.jsonl 的唯一写者.
- G4 (rev-shared 后段): 第 10, 8 项. 必须在 G1/G2/G3 都停止写入后, 由不承担写入的第三方执行.
- 可用非作者验收者 3 名, 计划 3 名, 实际派 3 名:
  - 三组写目标互不相同 (alpha 实例, beta 实例, 共享记录), 端口与数据目录各自独立, 可同时开工, 有并行收益 (两个 4 秒任务与两次约 1.2 秒写入窗口重叠).
  - 不存在"每开一个会话都要重复同一份准备": 两个实例本来就是各组自己的准备, 没有共同构建或共同启动; 未共用截图.
  - 派 3 人而非 2 人: 第 10 项需要安静窗口, 第 8 项需要两侧材料, 若只有 2 人则 A/B 要互相等待且互相评判材料; 第三方承担尾部只读检查才不拖延前面的组.
  - 未逐条 AC 单开会话: 每名验收者按实例/文件归属承接 2-3 条.

### 验收者名册 (全部为本轮新开子会话)

| 组 | herdr 会话 (name / pane / tab) | pi session id | 创建时间 | 承接标准 |
|----|-------------------------------|---------------|----------|----------|
| G1 | rev-alpha / w1J:p57 / w1J:t55 | 01a15483-3add-74a0-a077-1b434d6cb4d0 | 2026-10-19T22:14:08+0800 (会话文件 2026-10-19T14-14-08-862Z_…) | 第 1, 3, 7 项 + alpha 材料 |
| G2 | rev-beta / w1J:p58 / w1J:t56 | 01a15483-4f6f-70ee-ab4b-8bb426dba77c | 2026-10-19T22:14:14+0800 (14-14-14-127Z_…) | 第 2, 4 项 + beta 材料 |
| G3/G4 | rev-shared / w1J:p59 / w1J:t57 | 01a15483-642c-73fc-8bda-578e542ac6d6 | 2026-10-19T22:14:19+0800 (14-14-19-436Z_…) | 第 5, 6, 9 项, 之后第 10, 8 项 |

选型: 三名均为 pi, model `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `max`. 依据: 任务画像接近 review/vision (需判读截图与逐字比对输出), 该模型 review 1.328 / vision 1.405 为可用候选中最高, 且价格低; 失败代价高 (错判通过) 因此用最深思考档.

### 未参与本次实现与修复的可核对事实
- 实现提交时间为 2026-10-19T22:12:14+0800 (b2d3aed 与 e398c7c 同一时间), 三名验收者的 pi 会话文件创建时间分别为 22:14:08 / 22:14:14 / 22:14:19, 都晚于全部实现提交.
- 三个会话记录中没有对产品文件的写操作: 逐条扫描三个会话 jsonl 的 write/edit 调用, 目标全部落在 evidence-e398c7c-r1/ 之下 (alpha/summary.md; beta 的 5 个 md; shared 与 tail 的 md), 没有一次命中 app.py, README.md, deps.txt, tests/, PRODUCT.md.
- 收尾 `git status --porcelain` 只有证据目录, `git diff` 为空: 产品文件与 tests/ 与目标提交一致.
- 验收者不继承实现会话: 三个会话是独立新会话, 首条任务只含目标提交, 输入路径, 分到的标准原文, 证据目录与核对规则; 没给实现对话或作者的设计理由.

### 共用准备与原始材料归属
- alpha 实例: rev-alpha 独家启动 (PID 4090884, 22:15:07) 与停止 (22:18:31), 材料在 alpha/00-env/ 与 alpha/stop.txt.
- beta 实例: rev-beta 独家启动 (PID 4090715, 22:15:03) 与停止 (22:18:33), 材料在 beta/instance-start.* 与 beta/stop.txt.
- 共享目录 runtime/shared: rev-shared 是 record.jsonl 的唯一写者; 两侧实例启动后由它用 `health` 轮询确认就绪 (shared/wait.log, 22:15:08 两侧 ok).
- 未共用昂贵准备: 没有共同构建; 两张截图各自由 G1/G2 产生, 未复制他人结果.

### 各可隔离组的开始与结束
| 组 | 开始 | 结束 |
|----|------|------|
| G1 alpha | 实例 22:15:07 启动, 首条命令 22:14:58 | 标准验收 22:16:10; 实例停止 22:18:31 |
| G2 beta | 实例 22:15:03 启动 | 标准验收 22:15:37; 实例停止 22:18:33 |
| G3 共享记录 | 22:15:03.7 (就绪轮询起点) | 22:15:20 前后 (前段结论) |
| G4 尾部只读 | 22:16:55.31 (收到通知后) | 22:17:39.71 |

### 争用片段执行顺序记录
| 争用对象 | 顺序事实 | 依据 |
|----------|----------|------|
| runtime/shared/record.jsonl | rev-shared 先 AC-003-1 (22:15:13.13~22:15:14.39, seq=1) 后 AC-003-2 (22:15:16.45~22:15:17.72, seq=2), 同一份记录, 中间无并发, 无他人写入; 第三人从未 append | AC-003-1 假定记录不存在, AC-003-2 假定已有 alpha (plan.md 争用表) |
| runtime/shared/events.log | 三名写者最后写入: beta job-end 22:15:16, rev-shared append 22:15:17.70, alpha job-end 22:15:38.75; rev-shared 在 22:16:55 收到指挥者"G1/G2/G3 写入结束"通知后才做 BR-002, 并用前后哈希/字节/行数/mtime 全同自证窗口内无写者 | BR-002 断言"只读查看前后文件内容不变", 有并发写者时无法归因 |
| 两侧截图与 report | G1 于 22:15:20/23 产出 alpha 材料, G2 于 22:15:20/22 产出 beta 材料, rev-shared 22:17:08 才核对 | AC-005-1 假定两侧材料已由各自负责人产出 |

顺序记录原件: tail/order.md (rev-shared 写: 前一段执行者, 自己起止时间, 依据 plan.md 的哪一条).

### 共享材料的产生者 / 版本 / 位置 / 接收方
| 材料 | 产生者 | 版本 | 位置 | 接收方与其适用性核对 |
|------|--------|------|------|----------------------|
| alpha 状态页截图 | rev-alpha, 22:15:20 | e398c7c / relay-v1 | alpha/04-ac005/alpha-status.png (与 alpha/01-ac001/同哈希) | rev-shared 22:17:08 自行核对: 截图命令记录显示 URL 为 127.0.0.1:18101/status-page, 900x400 有效 PNG, 图像文字与 report 一致; 结论由 rev-shared 自下 |
| alpha report 原文 | rev-alpha, 22:15:23 (另 22:15:47 复跑) | 同上 | alpha/04-ac005/report.txt, report-fresh.txt | 同上 |
| beta 状态页截图 | rev-beta, 22:15:22 | 同上 | beta/ac005-1/beta-status.png | rev-shared 22:17:08 核对: 截图命令 URL 只记录在 beta/ac005-1/notes.md (截图日志本身不含 URL), 故该点按引用旧观察处理; rev-shared 另跑 health/report 两端口做旁证, 并以图像内容判断实例为 beta; 指挥者另有独立复核 (见下) |
| beta report 原文 | rev-beta, 22:15:20 | 同上 | beta/ac005-1/report-and-status.txt | 同上 |

指挥者复核: 我亲自读取两张 PNG, 画面分别为 `instance=alpha` / `instance=beta`, 均含 `state=ready` 与 `version=relay-v1`; 与各自 report 原文一致. 这只是对材料的复核, 不替代验收者结论.

材料类型分布: 10 项结论全部基于当前观察 (本轮实际命令与操作); 无结论依赖推断或未运行. 唯一按引用旧观察处理的辅助信息是 beta 截图命令的 URL (见上), 它不承担任何通过判据, 判据由图像与 report 原件承担.

## 覆盖范围与说明
- 本轮只覆盖提交 e398c7cc7ca4e493d23689bee3cca1a34d306000, 环境为本机 127.0.0.1:18101/18102, runtime/shared 起始为空目录. 未覆盖并发多写者下的记录一致性 (标准里没有这条要求, 未擅自加判).
- 非产品判据事项: 项目没有 TECHNICAL.md / EXECUTION.md; 内部代码结构, 模块划分等不在本轮判定范围, 既未判通过也未判失败.
- 计划勾选状态没有被当作证据; 所有结论都来自本轮实际命令输出或原件核对.
- 实例已在验收结束后停止 (alpha 22:18:31, beta 22:18:33), 两个端口已释放; runtime/shared 保留本轮产生的 record.jsonl 与 events.log, 与证据目录里的副本一致 (sha256 复核相同).

## 收尾
- 除本次证据目录的输出外, 源码与 Spec 未变: `git diff` 为空, `git status --porcelain` 只列 `docs/changes/relay-board/evidence-e398c7c-r1/`. 相对起始提交, 工作区确实多了这个证据目录 (以及被 .gitignore 覆盖的 runtime/ 运行数据), 不声称整个工作区仍然干净.
- 本报告不是正式人工验收结论: 10 项通过仍需用户逐项确认, 并由正式人工验收确认后才算交付; 本轮不宣布正式交付, 也不关闭用户验收.

## 附: 证据目录结构
```
docs/changes/relay-board/evidence-e398c7c-r1/
├── plan.md                 派工计划
├── report.md               本报告
├── alpha/                  rev-alpha: 00-env, 01-ac001, 02-ac002, 03-ac004, 04-ac005, summary.md, stop.txt
├── beta/                   rev-beta: ac001-2, ac002-2, ac005-1, summary.md, stop.txt, instance-start.*
├── shared/                 rev-shared 前段: ac003-1-*, ac003-2-*, br001-*, record-copy.jsonl, wait.log, notes.md, summary.md
├── tail/                   rev-shared 后段: br002-*, events-before/after.log, ac005-1-*, order.md, notes.md
└── _task-alpha.txt / _task-beta.txt / _task-shared.txt   指挥者发给三名验收者的任务原文
```
