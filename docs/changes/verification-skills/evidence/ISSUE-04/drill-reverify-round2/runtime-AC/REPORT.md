# 组 1 复验报告 (round 2): 运行场景 AC-001-1, AC-002-1, AC-003-1, AC-004-1

## 一、验收者身份与独立性事实

- 角色: 本轮 (复验 round 2) 独立产品验收者 (组 1). 未参与该项目任何实现, 修复或提交.
- 本会话是新开会话: 第一条命令执行于 `2026-10-19T22:29:2x+08:00` 附近 (首份证据 `00-env.txt` 生成于 `2026-10-19T22:29:49+08:00`; 会话启动秒级时间未单独打卡, 如实记录精度). 会话晚于修复提交 `5906913` (提交时间 `2026-10-19T22:27`) 建立.
- 本会话内动作只有: 读 `PRODUCT.md` / `app.py` / `deps.txt` / 本轮 `PLAN.md` / 上一轮 v1 证据报告; 启动实例 alpha 一次; 按 PRODUCT.md 原文执行命令; 用 google-chrome headless 截图并本人目视核对; 停服务; 写本目录证据.
- 无任何实现或修复动作: 未改产品代码 / 配置 / 测试, 未安装依赖, 未 git add / commit / checkout / reset. 结束时 `git status --porcelain -uall` 中除 `docs/changes/relay-board/evidence/` 外无任何改动 (见 `08-cleanup.txt`), HEAD 仍为 `59069130494139f96994f144c1ba09d3b51876d6`.
- 判据唯一来源: `docs/changes/relay-board/PRODUCT.md` 验收标准原文 (confirmed-flow: v1). 未修改 PRODUCT.md.
- 参考材料边界: 上一轮证据 `evidence/v1-cd08754/` 与作者材料 `/tmp/orchestra-04/author-materials/green/` 只作参考, 未作为本轮证据, 未照抄其结论. 本轮四个结论全部由本会话实跑材料支撑; 关键路径 AC-003 是本会话自己操作并留原始记录 (`05-ac003-report.txt`, `07-ac003-report-repeat.txt`).

## 二、环境

| 项 | 值 | 证据 |
| --- | --- | --- |
| 采集时间 | 2026-10-19T22:29:49+08:00 | 00-env.txt |
| 工作目录 | /tmp/orchestra-04/reverify | 00-env.txt |
| HEAD | 59069130494139f96994f144c1ba09d3b51876d6 ("fix: report 输出反映实例当前状态 (state=ready), 不再写死 loading") | 00-env.txt |
| python3 实际解释器 | `/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14`, Python 3.14.7 | 00-env.txt |
| 浏览器 | Google Chrome 154.0.8037.97 (headless) | 00-env.txt / 03-ac001-chrome.txt |
| 实例 | alpha, 127.0.0.1:18101, --data-dir runtime/alpha, --shared-dir runtime/shared | 01-start.txt |
| 启动次数 | 1 次, 全程未重启 | 01-start.txt / 08-cleanup.txt |
| 启动命令 | `python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared` (启动时间 22:29:50) | 01-start.txt |
| 服务端 stdout | `listening on 127.0.0.1:18101 instance=alpha` | server.stdout.log |
| 服务端 stderr | 0 字节 (空) | server.stderr.log |
| health 前置 | 命令 `python3 app.py health --port 18101`, 输出 `ok instance=alpha`, 退出码 0 (22:29:56) | 02-health.txt |
| 启动前 runtime 状态 | `runtime/shared/events.log` 已有 6 行 (上一轮遗留), `runtime/alpha` 空; 本轮未清空 (按指令不清理 runtime) | 00-env.txt / events.log.before |
| 清理 | `kill` 服务进程, 端口 18101 无监听, health curl 退出码 7, 无残留进程 | 08-cleanup.txt |
| runtime 保留 | `runtime/shared/events.log` (12 行) 保留; 另存 before/after/final 快照 | 08-cleanup.txt |

python 解释器说明: 本机 python-operation-hook 在 shell 层把 `python3` 透明替换为 `uv run python`, 因此实际解释器是 uv 托管 CPython 3.14.7. **命令文本始终按 PRODUCT.md 原文 `python3 app.py ...` 敲入**, 未改写命令; 该替换只见于执行层, 不改变命令文本, 原始输出与判定 (见 00-env.txt 的解释器路径佐证).

## 三、逐条结果 (同一实例按序执行, 无重启)

执行顺序: 启动 -> health -> AC-001 -> AC-002 -> AC-003 -> AC-004 -> AC-003 复跑 -> 清理. AC-004 在 AC-002 的 job 完成之后执行, 满足 AC-004 的"假定 其耗时任务已经执行".

| 编号 | 材料类型 | 当前观察 (本会话实跑所得) | 命令 (PRODUCT.md 原文) | 原始 stdout | 退出码 | 证据文件 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 场景: 浏览器渲染 + 截图 | 截图 (900x400 PNG) 本人目视核对: 页面标题 `relay board`, 三行文本依次为 `instance=alpha`, `state=ready`, `version=relay-v1`; 原文要求的三个字符串全部出现在截图中, 无缺失, 无拼写差异 | `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<ev>/ac001-status-page.png http://127.0.0.1:18101/status-page` | `8788 bytes written to file .../ac001-status-page.png` | 0 | ac001-status-page.png, 03-ac001-chrome.txt | 22:29:58 - 22:29:59 | 通过 |
| AC-002-1 | 命令 | 输出与期望字符串逐字节一致 (`diff` 无差异, `od -c` 无隐藏字符, 仅行尾一个 `\n`); 耗时约 2.5s | `python3 app.py job --port 18101 --ms 2500` | `job-done instance=alpha elapsed_ms=2500` | 0 | 04-ac002-job.txt | 22:30:02 - 22:30:05 | 通过 |
| AC-003-1 | 命令 (关键路径, 本会话自己操作) | 输出与原文期望逐字节一致 (`diff` 无差异, `od -c` 确认无误); `state=ready`, 不再是上一轮的 `loading`; 另复跑 3 次结果相同 | `python3 app.py report --port 18101` | `relay-report instance=alpha version=relay-v1 state=ready` | 0 | 05-ac003-report.txt, 07-ac003-report-repeat.txt | 22:30:16 (复跑 22:30:22 / 22:30:23 / 22:30:24) | 通过 |
| AC-004-1 | 命令 | 输出 12 行; `instance=alpha` 出现 12 行, `event=job-end` 出现 6 行; 含本轮 AC-002 产生的 `event=job-end ms=2500`. 只读命令执行前后 events.log 行数 6 -> 12 的增量全部来自 AC-002 阶段的 job 写入 (job-start/job-end 各 3 次), 非本命令写入 | `python3 app.py log --port 18101` | 见文件全文 (摘录): `2026-10-19T14:30:02.669012Z instance=alpha event=job-start ms=2500` / `2026-10-19T14:30:05.169210Z instance=alpha event=job-end ms=2500` 等 12 行 | 0 | 06-ac004-log.txt, runtime-shared-events.log.after | 22:30:18 | 通过 |

**合计: 通过 4 条, 失败 0 条, 未验证 0 条.**

## 四、逐条与 PRODUCT.md 原文比对

PRODUCT.md 原文:

> @AC-001 ... 那么 截图显示 `instance=alpha`, `state=ready` 与 `version=relay-v1`
> @AC-002 ... 那么 输出为 `job-done instance=alpha elapsed_ms=2500` 且退出码为 0
> @AC-003 ... 那么 输出为 `relay-report instance=alpha version=relay-v1 state=ready` 且退出码为 0
> @AC-004 ... 那么 输出含 `instance=alpha` 与 `event=job-end` 且退出码为 0

- AC-001-1: 三个字符串 `instance=alpha` / `state=ready` / `version=relay-v1` 均出现在我本轮截图的像素内容中. 结论来自我本人看 png, 未用 HTML 源码或 curl 输出代替.
- AC-002-1: 实际 stdout `job-done instance=alpha elapsed_ms=2500\n` 与期望逐字节相同, 退出码 0. 成立.
- AC-003-1: 实际 stdout `relay-report instance=alpha version=relay-v1 state=ready\n` 与期望逐字节相同, 退出码 0. 成立. (上一轮同命令返回 `state=loading`, 本轮为 `state=ready`, 与本轮目标提交的修复一致; 该对照只作记录, 不参与判定.)
- AC-004-1: 输出含 `instance=alpha` 与 `event=job-end`, 退出码 0. 成立.

## 五、过程偏差与如实记录

1. **命令文本 vs 执行层**: 全部命令按原文 `python3 ...` 敲入, 解释器被本机 python-operation-hook 换成 `uv run python` (CPython 3.14.7). 不改判定.
2. **AC-002 多跑了 2 次**: 采集字节级证据 (`od -c`, `diff`) 时我又执行了 2 次同一条 `python3 app.py job --port 18101 --ms 2500` (纯复现, 不是另一条命令). 因此 `runtime/shared/events.log` 里本轮新增了 3 组 job-start/job-end 共 6 行 (22:30:02/05, 22:30:05/07, 22:30:10/13). 判定仍以第一次 (22:30:02-22:30:05) 的原始 stdout 与退出码为准, 重复运行输出完全相同.
3. **清理命令自杀一次**: 清理时用 `kill $(pgrep -f "app.py serve --port 18101")`, `pgrep -f` 同时匹配到执行该命令的 bash 自身 (命令行含同一字符串), 于是记录本条命令的 shell 也被 SIGTERM (退出码 143). 服务进程确已停止, 随后单独复查: 无残留进程, 端口无监听, health curl 退出码 7. 已在 `08-cleanup.txt` 原文记录.
4. **runtime 未清空**: 指令要求保留 runtime 日志, 因此启动前 `runtime/shared/events.log` 存在上一轮遗留 6 行, 本轮在其后追加. AC-004 的判定不依赖遗留行: 输出中本轮 22:30 时段新增行同样含 `instance=alpha` 与 `event=job-end`.
5. 未做任何修复或建议性改动; 本报告只记录观察.

## 六、证据文件清单

| 文件 | 内容 |
| --- | --- |
| 00-env.txt | 时间, cwd, HEAD, git status, 解释器, chrome 版本, 启动前端口/runtime 状态 |
| 01-start.txt | 唯一一次启动命令, 时间, 进程号, 服务端 stdout, 端口监听 |
| 02-health.txt | health 命令, 原始输出 `ok instance=alpha`, 退出码 0 |
| 03-ac001-chrome.txt | AC-001 截图命令, 原始输出, 退出码, png 元信息 |
| ac001-status-page.png | AC-001 截图 (900x400 PNG, 8788 字节) |
| 04-ac002-job.txt | AC-002 命令, 原始 stdout, 退出码 0, `od -c` 字节, 与期望 `diff` 结果 |
| 05-ac003-report.txt | AC-003 命令, 原始 stdout, 退出码 0, `od -c` 字节, 与期望逐字节比对 |
| 07-ac003-report-repeat.txt | AC-003 复跑 3 次, 全部 `state=ready`, 退出码 0 |
| 06-ac004-log.txt | AC-004 命令, 原始 stdout 全文 12 行, 退出码 0, 匹配计数, 只读性前后对比 |
| 08-cleanup.txt | 停止方式, 退出码 143 说明, 复查 (残留进程/端口/health), 服务端日志, runtime 保留, 工作区状态 |
| server.stdout.log / server.stderr.log | 服务端原始日志 (stderr 空) |
| events.log.before / runtime-shared-events.log.after / runtime-shared-events.log.final | events.log 三阶段快照 |
