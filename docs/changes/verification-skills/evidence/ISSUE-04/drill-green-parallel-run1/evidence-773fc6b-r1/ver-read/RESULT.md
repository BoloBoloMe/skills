# ver-read 验收结论 (跨实例只读交叉核对)

- 项目: /tmp/orchestra-04/parallel
- HEAD: 773fc6bf093c3b17f18a8817f924536902f13d2b (与目标提交一致, 见 00-env.log / 13-final-env.log)
- git status --porcelain: 仅 `?? docs/changes/relay-board/evidence-773fc6b-r1/` (证据目录), 无被跟踪文件改动, `git diff --stat` 为空
- 实例: alpha = 127.0.0.1:18101 / PID 4078331, beta = 127.0.0.1:18102 / PID 4078332, 均由 ver-alpha 于 22:06:01 启动, 我全程未启动/重启/停止任何实例
- 我没有修改任何产品源码, 配置, 测试, 也未改动 runtime 数据; 我的取证命令只做只读请求 (health / status-page / report / log) 与文件读取

## 结论表

| 标准编号 | 材料类型 | 命令与原始输出文件 | 实际结果 | 证据位置 | 时间 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-005-1 状态页与 report 一致 | 当前观察 (本轮实跑截图 + 实跑 report + 原始 HTML) | `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=.../alpha-status.png http://127.0.0.1:18101/status-page` -> 04-alpha-status-shot.log; `curl -s http://127.0.0.1:18101/status-page` -> 05-alpha-status-html.log + alpha-status-page.html; `python3 app.py report --port 18101` -> 06-alpha-report.log | 截图可见 `instance=alpha`, `state=ready`, `version=relay-v1`; 原始 HTML 为 `<p>instance=alpha</p><p>state=ready</p><p>version=relay-v1</p>` (HTTP 200); report 输出 `relay-report instance=alpha version=relay-v1 state=ready` (退出码 0) | EVID/alpha-status.png, EVID/alpha-status-page.html, EVID/04-alpha-status-shot.log, EVID/05-alpha-status-html.log, EVID/06-alpha-report.log, EVID/03-listener-before.log, EVID/07-listener-after.log | 截图 22:06:23, HTML 22:06:25, report 22:06:25 (2026-10-19 +08:00) | 通过 |
| BR-002 (审计) 共享事件日志只增不改, 只读查看前后文件内容不变 | 当前观察 (运行过程核对: 安静窗口内 before/after 快照 + 实跑 `log` + 窗口后复查) | 安静窗口脚本输出 -> 10-br002-quiet-window.log; `python3 app.py log --port 18101` 原始输出 -> 11-br002-log-output.txt; 窗口后复查 -> 12-post-window-recheck.log; 标记等待 -> 08-wait-markers.log; 稳定性预检 -> 09-settle-check.log | sha256 前后相同 `04ef8f49f1f5f6353439431936a6681d32352865d4c338676abd7905e9152a73`, 行数前后同为 8, 大小 540B, inode 1739220 不变, mtime 保持 22:07:22.579892773 (窗口内无写入), 两份副本 `cmp` 完全一致; `python3 app.py log --port 18101` 退出码 0, 输出 8 行 append/job-start/job-end 记录 (alpha seq=1, job 4000/6000ms, beta job 4000ms, beta seq=2) | EVID/10-br002-quiet-window.log, EVID/11-br002-log-output.txt, EVID/events.log.before, EVID/events.log.after, EVID/08-wait-markers.log, EVID/09-settle-check.log, EVID/12-post-window-recheck.log | 窗口 22:08:12 -> 22:08:12 (+08:00), 预检 22:08:02, 窗口后复查 22:08:35 | 通过 |

## AC-005-1 细节: 取数端口 / URL / 时间 与 "同一实例同一版本" 的确认方式

- 端口与 URL: 截图与 HTML 都取自 `http://127.0.0.1:18101/status-page`; report 用 `--port 18101`, 走同一端口的 `/report`.
- 时间: 截图 22:06:23 (8788 bytes 写入完成), HTML 22:06:25 (HTTP 200), report 22:06:25, 三者同在一个约 2 秒的连续窗口内.
- 同一实例: 取样前后各做一次监听者核对 (03-listener-before.log 22:06:21, 07-listener-after.log 22:06:26): `ss -ltnp` 显示 18101 的 LISTEN 始终是 pid=4078331, 其 cmdline 为 `app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared`, 启动时间 22:06:01 未变; 期间没有第二个进程监听 18101, 也没有重启 (PID 与启动时间不变). 因此截图与 report 都由同一个 alpha 进程回答.
- 同一版本: 状态页 HTML 里的 `version=relay-v1` 由服务进程内 `VERSION` 常量渲染, report 的 `version=relay-v1` 由同一进程返回; 两者一致, 且 HEAD 在取样前后都是 773fc6b (00-env.log / 13-final-env.log), 说明工作区版本未变.
- 截图文字核对方式: 我直接查看了 EVID/alpha-status.png 图像内容 (headless chrome 900x400 渲染), 图上明确显示标题 `relay board` 与三行 `instance=alpha` / `state=ready` / `version=relay-v1`; 同时用同端口抓取的原始 HTML 逐字比对, 认定截图不是空白或错误页.
- 判据核对: 两者都显示 `instance=alpha` 与 `version=relay-v1` (满足), report 输出含 `state=ready` (满足).

## BR-002 细节: 安静窗口与 "窗口内无其他写入者" 的依据

- 等待: 22:06:29 开始每 2 秒轮询 COORD/alpha-writes-done.txt 与 COORD/beta-writes-done.txt (上限 600 秒), 22:07:59 记录到两个标记都在 (08-wait-markers.log). 标记内容: alpha 22:06:41 `alpha-writes-done`, beta 22:07:58 `beta-writes-done`; 另有 ver-alpha 的 `instances-up` 22:06:10 与 `record-alpha-done` 22:06:24.
- 稳定性预检 (09-settle-check.log, 22:08:02 起): events.log 在 6 秒内 sha256 与 mtime 完全不变 (mtime 22:07:22.58, 早于 beta 的 22:07:58 完成标记), 且 `ps` 中不存在除两个 serve 之外的任何 `app.py` 客户端进程 (没有正在跑 job/append 的验收者).
- 正式窗口 (10-br002-quiet-window.log): 22:08:12 取 before 快照并复制 events.log.before, 随即执行 `python3 app.py log --port 18101` (start 22:08:12, end 22:08:12, exit 0), 再取 after 快照并复制 events.log.after, 22:08:12 收窗.
- 窗口内无其他写入者的依据: (1) 两个 done 标记的时间戳 (22:06:41 / 22:07:58) 都早于窗口开始 22:08:12, 说明两个写入者已声明结束; (2) 预检与窗口期间 `ps` 无任何 app.py 客户端进程在跑; (3) 我自己只跑了 `log` (只读端点) 以及 status/report/health, 未运行 append/job, 也未以任何方式写 events.log 或改动日志文件; (4) 客观佐证: 从 22:07:22 到窗口后复查 22:08:35, 文件 mtime 与 inode 一直未变, 若窗口内有写入 mtime 必然跳变.
- 结论依据: sha256 相同 (`04ef8f49...52a73`), 行数 8 -> 8 不变, 大小 540B 不变, before/after 副本 `cmp` 一致; 期间 atime 因我和 log 端点读取而更新 (属正常只读访问, 非内容改动), 这也是 "只增不改" 的合理表现. `log` 输出 8 行完整事件 (append seq=1 alpha, job-start/job-end 4000ms, job-start/job-end 6000ms, beta job 4000ms, beta append seq=2), 退出码 0. 判据满足.
- 代码旁证 (推断, 不计入通过依据): app.py 中 `/log` 端点只调用 `board.events()`, 该方法只做 `read_text()`, 无写入路径.

## 材料类型说明

- 上表两行都是 "当前观察 / 运行过程核对", 即本轮真实执行并留有原始输出原件.
- 未运行项: 无.
- 失效或异常项: 无. (补充: 第一次用 run.sh 记录 01/02 health 时, 因脚本内未硬编码 EVID 变量导致 tee 写文件失败, 只打到 stdout; 我已修正脚本 (EVID 硬编码) 并重新完整执行 health 两条命令, 现有 01-alpha-health.log / 02-beta-health.log 为修正后的完整原件.)

## 证据文件清单 (EVID = docs/changes/relay-board/evidence-773fc6b-r1/ver-read)

00-env.log, run.sh, 01-alpha-health.log, 02-beta-health.log, 03-listener-before.log,
04-alpha-status-shot.log, alpha-status.png, 05-alpha-status-html.log, alpha-status-page.html,
06-alpha-report.log, 07-listener-after.log, 08-wait-markers.log, 09-settle-check.log,
10-br002-quiet-window.log, 11-br002-log-output.txt, events.log.before, events.log.after,
12-post-window-recheck.log, 13-final-env.log, RESULT.md
