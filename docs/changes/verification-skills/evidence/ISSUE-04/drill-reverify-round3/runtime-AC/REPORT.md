# 组 A 运行场景报告 (AC-001-1, AC-002-1, AC-003-1, AC-004-1)

- 验收者身份: 独立验收者, 未参与实现与修复.
- 目标提交: `59069130494139f96994f144c1ba09d3b51876d6` (`git rev-parse HEAD` 一致, 见 `00-preflight.txt`).
- 父提交: `cd087542b4610c49ded0a1278fe8065726b62d9d`.
- 判据原文: `docs/changes/relay-board/PRODUCT.md`, `验收标准` 节 `confirmed-flow: v1`, 与 `业务规则` 节 BR-001 (审计).
- 采集窗口: 2026-10-19T22:37:52+08:00 至 2026-10-19T22:38:20+08:00 (单实例 alpha 只启动一次, 四条场景共用).
- 材料类型说明: 本文件四个 AC 项都是**当前观察** (本轮实跑), 不是旧材料.

## 0. 运行前状态与解释器

- `git diff` / `git diff --cached` 均为空, `git status --porcelain` 只有未跟踪的 `?? docs/changes/relay-board/evidence/`. 证据: `00-preflight.txt`.
- 端口 18101 开始前无监听 (`ss` 匹配计数 0). 证据: `00-preflight.txt`.
- 本机 `python3` 是 shell 函数 `python3 () { uv run python "$@"; }`, 实际解释器为 CPython 3.14.7, 可执行文件 `/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14`. 命令文本仍按 PRODUCT.md 原文记作 `python3`. 证据: `00-preflight.txt`, `audit-BR-001/05-imports-ast.txt`.
- 启动唯一实例的命令 (原文):
  `mkdir -p runtime/alpha && python3 app.py serve --port 18101 --instance alpha --data-dir runtime/alpha --shared-dir runtime/shared &`
  启动时间 22:37:55, 服务 stdout: `listening on 127.0.0.1:18101 instance=alpha`, stderr 为空. 证据: `01-serve-start.txt`, `serve.stdout.txt`, `serve.stderr.txt`, `02-serve-proc.txt`.
- 运行前把上一轮遗留的 `runtime/shared/events.log` (792 字节, md5 `cc408be2f610d475cf86ea9bea3f61d3`) 移到 `runtime/shared/events.log.prior-v2`, 并另存 `runtime/prior-v2/events.log`, 使本轮的 `event=job-end` 只能由本轮 AC-002 产生. 旧内容仅作旧材料参考, 不作为本轮结论. 证据: `runtime/shared/events.log.prior-v2`, `runtime/prior-v2/events.log`, `99-runtime-files.txt`.

## 执行顺序 (按任务书)

health -> AC-001 -> AC-002 (job) -> AC-003 (report) -> AC-004 (log).
AC-002 先写 `runtime/shared/events.log` 的 `job-end`, AC-004 后读同一日志, 满足 AC-004 场景前提"其耗时任务已经执行".

---

## 1. AC-001-1 (状态页截图)

- 标准编号: AC-001-1
- 材料类型: 当前观察 (浏览器实渲染 + 截图, 本轮实跑)
- 前提: 实例 alpha 在 127.0.0.1:18101 运行, health 返回 `ok instance=alpha`.
- 实际操作命令 1 (health, 时间 22:38:00, 退出码 0):
  `python3 app.py health --port 18101`
  原始输出 (逐字节, `cat -A` 为 `ok instance=alpha$`):
  ```
  ok instance=alpha
  ```
  与期望文件 `03-health.expected.txt` 逐字节比对 `cmp` 通过 (`BYTE_MATCH=yes`).
  证据: `03-health.stdout.txt`, `03-health.stderr.txt` (空), `03-health.meta.txt`, `03-health.expected.txt`.
- 实际操作命令 2 (截图, 时间 22:38:02 至 22:38:03, 退出码 0):
  `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<证据目录>/ac001-status-page.png http://127.0.0.1:18101/status-page`
  chrome stderr 原文: `8788 bytes written to file docs/changes/relay-board/evidence/v3-5906913/runtime-AC/ac001-status-page.png`
  PNG 本体: `ac001-status-page.png`, `file` 结果 `PNG image data, 900 x 400, 8-bit/color RGB, non-interlaced`.
  验收者用 read 工具直接查看 png 原件, 画面中三行文本真实可见: `instance=alpha`, `state=ready`, `version=relay-v1`.
- 实际保存的页面 HTML (命令 `python3 app.py status --port 18101`, 时间 22:38:03, 退出码 0):
  ```html
  <!DOCTYPE html>
  <html><head><meta charset="utf-8"><title>relay board</title></head>
  <body><h1>relay board</h1>
  <p>instance=alpha</p>
  <p>state=ready</p>
  <p>version=relay-v1</p></body></html>
  ```
- 证据路径: `ac001-status-page.png`, `ac001-status-page.html`, `ac001.meta.txt`, `ac001-chrome.stdout.txt` (空), `ac001-chrome.stderr.txt`, `ac001-status-cmd.stderr.txt` (空).
- 结论: **通过**. 截图显示 `instance=alpha`, `state=ready`, `version=relay-v1` 三项, 且前提 health 输出正确.

---

## 2. AC-002-1 (耗时任务)

- 标准编号: AC-002-1
- 材料类型: 当前观察 (本轮实跑)
- 实际操作命令 (时间 22:38:06 至 22:38:08, 退出码 0):
  `python3 app.py job --port 18101 --ms 2500`
- 原始 stdout (`cat -A` 为 `job-done instance=alpha elapsed_ms=2500$`):
  ```
  job-done instance=alpha elapsed_ms=2500
  ```
- stderr: 空.
- 判据比对: 与期望文件 `ac002-job.expected.txt` (`job-done instance=alpha elapsed_ms=2500\n`) 用 `cmp` 逐字节比对, 结果 `BYTE_MATCH=yes`, 不是只做包含判断.
- 副作用核对: 任务执行后 `runtime/shared/events.log` 原文 (证明 job-start/job-end 由本轮产生):
  ```
  2026-10-19T14:38:06.365811Z instance=alpha event=job-start ms=2500
  2026-10-19T14:38:08.866200Z instance=alpha event=job-end ms=2500
  ```
- 证据路径: `ac002-job.stdout.txt`, `ac002-job.stderr.txt` (空), `ac002-job.expected.txt`, `ac002.meta.txt`, `ac002-events-after-job.txt`.
- 结论: **通过**. 输出与期望逐字节一致, 退出码 0.

---

## 3. AC-003-1 (report 状态)

- 标准编号: AC-003-1
- 材料类型: 当前观察 (本轮实跑)
- 前提复核 (时间 22:38:11, 退出码 0):
  `python3 app.py health --port 18101`
  原始输出:
  ```
  ok instance=alpha
  ```
  证据: `ac003-prehealth.stdout.txt`.
- 实际操作命令 (时间 22:38:11, 退出码 0):
  `python3 app.py report --port 18101`
- 原始 stdout (`cat -A` 为 `relay-report instance=alpha version=relay-v1 state=ready$`):
  ```
  relay-report instance=alpha version=relay-v1 state=ready
  ```
- stderr: 空.
- 判据比对: 与期望文件 `ac003-report.expected.txt` (`relay-report instance=alpha version=relay-v1 state=ready\n`) 用 `cmp` 逐字节比对, 结果 `BYTE_MATCH=yes`.
- 说明: 本轮只实跑一次 report, 没有复跑, 不存在"以哪次为准"的歧义.
- 证据路径: `ac003-report.stdout.txt`, `ac003-report.stderr.txt` (空), `ac003-report.expected.txt`, `ac003.meta.txt`, `ac003-prehealth.stdout.txt`.
- 结论: **通过**. 输出与期望逐字节一致, 退出码 0.

---

## 4. AC-004-1 (只读查看事件日志)

- 标准编号: AC-004-1
- 材料类型: 当前观察 (本轮实跑, 且 AC-002 已先执行)
- 实际操作命令 (时间 22:38:13, 退出码 0):
  `python3 app.py log --port 18101`
- 原始 stdout:
  ```
  2026-10-19T14:38:06.365811Z instance=alpha event=job-start ms=2500
  2026-10-19T14:38:08.866200Z instance=alpha event=job-end ms=2500
  ```
- stderr: 空.
- 判据比对 (判据是"输出含"): `grep -q 'instance=alpha'` 结果 `contains_instance_alpha=yes`; `grep -q 'event=job-end'` 结果 `contains_event_job_end=yes`; 退出码 0. 命中行原文见 `ac004-matching-lines.txt`.
- 执行顺序说明: 本项在 AC-002 (`job --ms 2500`) 之后运行, 所读 `job-end` 的写入时间为 `2026-10-19T14:38:08.866200Z` (= 本地 22:38:08), 与 AC-002 的执行窗口一致; 日志中无上一轮残留行 (已提前移走旧日志). 证据: `ac002-events-after-job.txt`, `ac004-log.stdout.txt`.
- 证据路径: `ac004-log.stdout.txt`, `ac004-log.stderr.txt` (空), `ac004-matching-lines.txt`, `ac004.meta.txt`.
- 结论: **通过**. 输出含 `instance=alpha` 与 `event=job-end`, 退出码 0.

---

## 5. 清理记录

- 22:38:15 第一次 `kill -TERM` 时 `pgrep -f "app.py serve --port 18101"` 首个匹配到的是执行本次命令的 bash 包装进程 (pid 4121893), 不是服务进程, 因此第一次 kill 无效. 服务真实 pid 由 `ss` 输出确定为 4121899.
- 22:38:19 执行 `kill -TERM 4121899`, 22:38:20 复核: `ss -ltnp | grep 18101` 匹配计数 0, 原始输出为 `(none)`; `pgrep -af 'app.py serve'` 只剩当前命令自身的 bash 包装行, 无真实 `python3 app.py serve` 进程.
- 证据: `99-cleanup.txt` (含错误与更正的完整原文), `serve.stdout.txt`, `serve.stderr.txt` (空), `99-runtime-files.txt`.
- 清理结论: 本实例已停止, 采集窗口结束时 18101 无监听.

## 6. 采集窗口之后的外部变化 (不参与判据)

- 会话在 22:38:28 之后被外部意外关闭, 22:48 左右恢复. 恢复后**没有重跑任何 AC 场景, 没有重启服务**.
- 恢复后只读检查发现 18101 已被另一个进程占用: `python3 app.py serve --port 18101 ... pid=4134574`, 同时 18102 有 beta 实例 pid 4134575. 这些不是本验收者启动的进程, 本验收者未 kill, 未使用其输出. 记录见 `06-post-window-readonly-check.txt`.
- 该外部占用晚于本报告采集窗口 (22:37:52-22:38:20), 与上述 AC 结论无关.

## 7. 未验证项与说明

- 未验证: 无必需项因缺权限或依赖而无法运行.
- 未运行: 本轮未运行 pytest, README 的 pytest 命令只作操作线索, 不作为产品通过依据.
- 未采用: 作者计划 `PLAN.md` 与 `evidence/v1-cd08754/`, `evidence/v2-5906913/` 的旧结论均未作为本轮通过依据.

## 8. 声明

- 除证据目录输出与 `runtime/` 运行数据外, 源码, 配置, 测试与 Spec 未变: 恢复后只读核对 `git hash-object` 与 `git rev-parse HEAD:<file>` 完全一致, `git diff` / `git diff --cached` 为空 (`06-post-window-readonly-check.txt`).
- 本报告结论仍需用户确认和正式人工验收.
