# 独立产品验收报告 (第 1 轮)

- 目标提交: `773fc6bf093c3b17f18a8817f924536902f13d2b` (HEAD, 提交时间 2026-10-19 21:18:27 +0800)
- 判据来源: `docs/changes/relay-board/PRODUCT.md`, `验收标准` 节 (`<!-- confirmed-flow: v1 -->`) 与 `业务规则` 节
- 证据目录: `docs/changes/relay-board/evidence-773fc6b-r1/` (本轮新建, 未覆盖旧证据; 仓库内无旧证据)
- 证据目录影响判断: 项目无构建脚本, 无 pytest 配置 (无 pyproject.toml / pytest.ini / setup.cfg / tox.ini), pytest 只收集 `test_*.py`,
  证据文件不含该命名, 故不进入测试发现或运行输入; `app.py` 不读 `docs/`. 证据留在仓库内, 未外置.
- 版本绑定: 验收结束时 `git status --porcelain` 只有 `?? docs/changes/relay-board/evidence-773fc6b-r1/`, `git diff --stat` 为空;
  `git hash-object app.py tests/test_app.py docs/changes/relay-board/PRODUCT.md` 分别等于 HEAD tree 中
  `7d2fda8.../app.py`, `165d334.../tests/test_app.py`, `4cdef5d.../docs/changes/relay-board/PRODUCT.md`.
  即被验收的源码, 测试与 Spec 与 773fc6b 完全一致.
- 覆盖面: 8 个验收场景 + 2 条审计业务规则, 共 10 项, 全部有结果. 未验证 0 项, 失败 0 项.

## 逐项结果

材料类型说明: "当前观察" = 本轮验收者在本提交上实跑得到的命令输出/文件/截图; 无一条结论依赖推断或旧观察.

| 标准编号 | 材料类型 | 实际操作 (命令 / 原件) | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 alpha 实例状态页 | 当前观察 | `python3 app.py health --port 18101` 前置; `python3 app.py status --port 18101` | health `ok instance=alpha` exit 0; status 输出 HTML 含 `instance=alpha`, `state=ready`, `version=relay-v1`, exit 0 | `ver-alpha/01b-health-alpha.log`, `ver-alpha/02-ac001-status-alpha.log` | 22:06:07 / 22:06:12, 773fc6b | 通过 |
| AC-001-2 beta 实例状态页 | 当前观察 | `python3 app.py health --port 18102` 前置; `python3 app.py status --port 18102` | health `ok instance=beta` exit 0; status 含 `instance=beta`, `state=ready`, `version=relay-v1`, exit 0 | `ver-beta/01-ac001-2-health.log`, `ver-beta/01-ac001-2-status.log` | 22:06:38, 773fc6b | 通过 |
| AC-002-1 alpha 耗时任务 | 当前观察 | `python3 app.py job --port 18101 --ms 4000`, 同 shell 前后 `date +%s%N` 量耗时 | 输出恰为 `job-done instance=alpha elapsed_ms=4000`, exit 0; 实测 4.071 秒 (>= 4 秒) | `ver-alpha/04-ac002-job-alpha.log` | 22:06:24-22:06:28, 773fc6b | 通过 |
| AC-002-2 beta 耗时任务 | 当前观察 | `python3 app.py job --port 18102 --ms 4000`, 外层记录纳秒起止 | 输出恰为 `job-done instance=beta elapsed_ms=4000`, exit 0; 实测 4063 毫秒 (>= 4000) | `ver-beta/02-ac002-2-job.log` | 22:06:57-22:07:01, 773fc6b | 通过 |
| AC-003-1 追加 alpha 条目 | 当前观察 | 前置 `ls -l runtime/shared/` + `test -e record.jsonl`; `python3 app.py append --port 18101 --value alpha`; 事后解析记录 | 前置 record.jsonl 不存在 (目录 total 0); 输出 `seq=1 value=alpha` exit 0; 记录中 `value=alpha` 恰好 1 条 | `ver-alpha/03a-ac003-precheck.log`, `03b-ac003-append-alpha.log`, `03c-ac003-verify-record.log` | 22:06:15 / 22:06:16-18 / 22:06:20 | 通过 |
| AC-003-2 追加 beta 条目 | 当前观察 | 前置 `cat runtime/shared/record.jsonl` (等 `coord/record-alpha-done.txt` 后); `python3 app.py append --port 18102 --value beta` | 前置记录已有 alpha (seq=1); 输出 `seq=2 value=beta` exit 0; 记录中 `value=beta` 恰好 1 条 | `ver-beta/03-ac003-2-pre-record.log`, `03-ac003-2-append.log`, `04-br001-*.log` | 22:07:13 / 22:07:21-22 | 通过 |
| AC-004-1 只读查看事件日志 | 当前观察 | 后台 `python3 app.py job --port 18101 --ms 6000 &`, 1.5 秒后 `python3 app.py log --port 18101`, 再等后台 job 结束 | log 输出含 `instance=alpha` 与 `event=job-start ms=6000`, exit 0; log 时刻 22:06:33.64 落在 job 窗口 [22:06:32.13, 22:06:38.20] 内, 且当时无对应 job-end | `ver-alpha/05-ac004-log-during-job.log`, `ver-alpha/05a-bgjob.out` | 22:06:32-22:06:38, 773fc6b | 通过 |
| AC-005-1 状态页与 report 一致 | 当前观察 | `google-chrome --headless --screenshot=.../alpha-status.png http://127.0.0.1:18101/status-page`; `curl -s .../status-page`; `python3 app.py report --port 18101`; 取样前后 `ss -ltnp` + `ps` 核对仍是同一 PID 4078331 | 截图显示 `instance=alpha`, `state=ready`, `version=relay-v1`; 原始 HTML 同样内容 (HTTP 200); report `relay-report instance=alpha version=relay-v1 state=ready` exit 0 | `ver-read/alpha-status.png` (我本轮另行打开图像复核, 内容一致), `ver-read/alpha-status-page.html`, `04-alpha-status-shot.log`, `05-alpha-status-html.log`, `06-alpha-report.log`, `03-listener-before.log`, `07-listener-after.log` | 22:06:23-22:06:26, 773fc6b | 通过 |
| BR-001 (审计) 序号从 1 连续不重复, 每个 value 只出现一次 | 当前观察 (运行产物核对, 非静态材料) | 实际写入的 `runtime/shared/record.jsonl`: `nl -ba`, `sha256sum`, 自写解析脚本核对 seq 连续性与 value 计数 | 2 行, seq `[1, 2]` = 1..N 连续, 无重复 seq, value 计数 alpha=1 / beta=1; sha256 `a306d2cf...e6172905`; 我本轮另用 `nl -ba runtime/shared/record.jsonl` 复读一致 | `ver-beta/04-br001-nl.log`, `04-br001-python-check.log`, `04-br001-sha256.log` | 22:07:22-22:07:31, 773fc6b | 通过 |
| BR-002 (审计) 事件日志只增不改, 只读查看前后不变 | 当前观察 (运行过程核对, 安静窗口) | 安静窗口: before `sha256sum`/`wc -l`/`stat` + 复制 `events.log.before` -> `python3 app.py log --port 18101` -> after 快照 + 复制 `events.log.after` + `cmp`; 窗口条件由 `coord/alpha-writes-done.txt` (22:06:41) 与 `coord/beta-writes-done.txt` (22:07:58) 两个标记时间戳加上预检 `ps` 无客户端进程共同支撑 | before/after 均 `04ef8f49...e9152a73`, 8 行 -> 8 行, size 540B, inode 1739220, mtime 未变 22:07:22.579; `cmp` 一致; log exit 0 输出 8 行事件; 我本轮另行 `sha256sum` + `cmp` 复核三份副本一致 | `ver-read/10-br002-quiet-window.log`, `09-settle-check.log`, `08-wait-markers.log`, `11-br002-log-output.txt`, `events.log.before`, `events.log.after`, `12-post-window-recheck.log` | 安静窗口 22:08:12, 窗口后复查 22:08:35 | 通过 |

汇总: 通过 10 / 失败 0 / 未验证 0.

## 派工记录

### 场景组划分与人数依据

- 计划文件: `evidence-773fc6b-r1/PLAN.md` (派工前写定).
- G1 alpha 组 (ver-alpha): AC-001-1, AC-002-1, AC-003-1, AC-004-1.
- G2 beta 组 (ver-beta): AC-001-2, AC-002-2, AC-003-2, BR-001.
- G3 只读交叉核对组 (ver-read): AC-005-1, BR-002.
- 当轮可用非作者验收者 3 名, 计划人数 3, 实际派出 3. 每组资源独立 (各自实例端口/数据目录/证据子目录), 且 G1 的共享记录写入被安排在 G2 之前,
  交叉点只有共享记录那一段, 其余条目并行, 拆开有实际收益.
- 不为凑人数逐条 AC 开会话; 共用准备只有一份 (实例启动), 由 ver-alpha 做, ver-beta 与 ver-read 直接引用.

### 验收者身份与未参与事实

| 组 | 会话标识 | 创建时间 | 承接标准 | 未参与本次实现与修复的可核对事实 |
| --- | --- | --- | --- | --- |
| G1 | pi 会话 `01a15479-c111-7639-97af-09ab10a70808` (agent 名 ver-alpha, 窗格 w1J:p53) | 2026-10-19T14:03:47Z (22:03:47 +08) | AC-001-1, AC-002-1, AC-003-1, AC-004-1 | 创建时间晚于被验提交 21:18:27 +0800; 启动 argv 为 `pi --model cli/deepseek-v4.1-flash-expires-on-0910:high`, 无 `--continue/--resume/--fork`; 会话记录工具调用只有 bash/read/write, 写入目标全部在证据目录与 runtime 数据; 结束时 HEAD 未变 |
| G2 | pi 会话 `01a15479-c106-7200-a9c5-33a97295c7f1` (ver-beta, w1J:p54) | 2026-10-19T14:03:47Z | AC-001-2, AC-002-2, AC-003-2, BR-001 | 同上: 启动 argv `pi --model cli/glm-5.3-flash:high`; 仅 bash/write, 唯一 write 是自己的工作目录 `ver-beta/RESULT.md` |
| G3 | pi 会话 `01a15479-c104-7187-b9fd-2987b5526a88` (ver-read, w1J:p55) | 2026-10-19T14:03:47Z | AC-005-1, BR-002 | 同上: 启动 argv `pi --model cli/deepseek-v4.1-flash-expires-on-0910:high`; 工具调用 bash/read/write, 写入仅在 `ver-read/` 与 `coord/` |

- 三会话均为本轮新开 (我这一轮创建), 与实现/修复会话无继承关系; 实现提交早于三者创建时间约 45 分钟.
- 会话原始记录位置 (仓库外, 供复核): `~/.pi/agent/sessions/--tmp-orchestra-04-parallel--/2026-10-19T14-03-47-845Z_01a15479-c104-7187-b9fd-2987b5526a88.jsonl`,
  `...-857Z_01a15479-c111-7639-97af-09ab10a70808.jsonl`, `...-846Z_01a15479-c106-7200-a9c5-33a97295c7f1.jsonl`.
- 选型: 任务画像是"按既定标准逐条实跑并留原件", 贴近 review 画像. ver-alpha / ver-read 用 `cli/deepseek-v4.1-flash-expires-on-0910`(review 1.328, speed 2.95) + thinking `high`;
  ver-beta 承担 BR-001 审计, 用另一厂商的 `cli/glm-5.3-flash` + thinking `high` 降低共同盲区.
- 派工文本副本: `dispatch-ver-alpha.txt`, `dispatch-ver-beta.txt`, `dispatch-ver-read.txt`.

### 派工过程事实

- 22:04:2x 首次长任务投递未送达 (三个 pi 会话的 TUI 尚在初始化, 会话记录里没有该消息). 发现后 22:05:46 / 22:05:49 / 22:05:52 重新投递,
  以重新投递为准; ver-alpha 与 ver-read 会话里各留了一条我投递前的测试消息 (`测试: 回复一词 ok`, `回复一词: pong`), 与产品无关.
- 派工后按会话记录与产出原件核对了三会话确实在做分到的标准 (22:06 起陆续出现 `00-env.log`, `run.sh`, 实例启动日志, 截图).

### 共用准备与原始材料归属

- 共用准备 (实例启动 18101 alpha / 18102 beta, 数据目录 `runtime/alpha`, `runtime/beta`, 共享目录 `runtime/shared`) 由 ver-alpha 在 22:06:01 一次性完成,
  PID 4078331 / 4078332, health 与启动输出在 `ver-alpha/01a-start-instances.log`, `01b/01c-health-*.log`, `01e-instance-pids.log`, `serve-*.out`;
  22:06:10 写 `coord/instances-up.txt`, ver-beta 与 ver-read 引用同一对实例, 未重启, 未另起第二套.
- 原始材料归属: alpha 组原件在 `ver-alpha/`, beta 组在 `ver-beta/`, 交叉核对组在 `ver-read/`; 每组 `RESULT.md` 是自己标准的结论.
- 实例在报告写成时仍在运行 (PID 4078331 / 4078332, 22:06:01 启动未重启), 未做关闭, 供复核.

### 并行与争用片段

- 三个组同时开工: 任务接收时间 22:05:46 (G1) / 22:05:49 (G2) / 22:05:52 (G3); 证据产出 22:05:56-22:06:03 起.
- 结束时间: G1 22:06:53 (写完 `RESULT.md`), G2 22:08:05, G3 22:08:52 (会话记录最后时间戳).
- 争用片段 1 (共享记录写入): 顺序 = ver-alpha 先 AC-003-1, 22:06:24 写 `coord/record-alpha-done.txt`; ver-beta 轮询到该标记后才做 AC-003-2 (22:07:13 前置核对, 22:07:21 append).
  依据: AC-003-1 假定记录尚不存在, AC-003-2 假定记录已有 alpha 条目 (PLAN.md 第 4 步). 两段各自的执行记录见 `ver-alpha/RESULT.md` 与 `ver-beta/RESULT.md` 的标记与小节.
- 争用片段 2 (BR-002 安静窗口): 顺序 = ver-read 先等 `alpha-writes-done.txt` (22:06:41) 与 `beta-writes-done.txt` (22:07:58) 两个标记, 22:08:02 做稳定性预检, 22:08:12 执行正式窗口.
  依据: 只增不改的核对必须在没有并发写入时归因; ver-read 自己在窗口内只跑只读 `log`/`status`/`report`/`health`. 记录见 `ver-read/RESULT.md` 与 `08-wait-markers.log`, `09-settle-check.log`.
- 只读检查 (AC-001-1/2, AC-005-1, 各组的文件读取) 不受上述两段影响, 全时段并行.

### 材料共享与接收方复核

- `ver-read/events.log.before` / `.after` (产生者 ver-read, 22:08:12, 目标 773fc6b): 我在 22:09 用 `sha256sum` 复算三份 (含当前 `runtime/shared/events.log`) 均 `04ef8f49...e9152a73`, `cmp` 返回一致.
- `ver-read/alpha-status.png` (产生者 ver-read, 22:06:23): 我本轮直接打开图像复核, 见 `relay board`, `instance=alpha`, `state=ready`, `version=relay-v1`.
- `runtime/shared/record.jsonl` (写入者 ver-alpha 22:06:18, ver-beta 22:07:22): ver-beta 核对后, 我在 22:09 用 `nl -ba` 复读, 仍是 seq=1 alpha / seq=2 beta, 与 BR-001 结论一致.
- 共享不转移判断: 三项标准 (AC-005-1, BR-001, BR-002) 的结论各自由承接者给出, 我的复核只用于核对材料是否支撑结论, 不另立结论.

## 覆盖范围与非产品判据

- 本轮对 BR-001 的核对基于本轮真实写入的 2 条记录 (seq 1, 2). 两个实例并发追加不在任何验收场景内, 本轮未验证该情形, 也不据此判通过或失败.
- `TECHNICAL.md` / `EXECUTION.md` 本项目没有; `tests/test_app.py` 存在, 但它属于既有执行验证, 不是产品判据, 本轮不以它作通过依据, 也未据此判失败.
- AC-004-1 只要求"耗时任务正在执行", 未给 `--ms`, 验收者取 6000 毫秒以便 log 完整落在任务窗口内.
- 端口 18101 / 18102 与 `runtime/` 只被本项目使用, 未与其他项目共享.

## 收尾

- 除本次证据目录的输出外, 源码与 Spec 未变: 被跟踪文件 blob 与 HEAD 一致, `git diff --stat` 为空; 证据目录本身是相对 773fc6b 的新增未跟踪文件.
- 三处验收者会话已在结果取回后关闭 (会话原始记录仍保留在 `~/.pi/agent/sessions/` 供复核).
- 本报告是本轮独立验收的汇总, 结论仍需用户逐项确认, 并交由正式人工验收; 不构成本项目正式交付或用户验收关闭.
