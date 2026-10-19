# 独立产品验收复验报告 (round 3)

- 目标提交: `59069130494139f96994f144c1ba09d3b51876d6` (HEAD)
- 修复提交的父提交: `cd087542b4610c49ded0a1278fe8065726b62d9d`
- 基线提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`
- 判据来源: `docs/changes/relay-board/PRODUCT.md` (`验收标准` 节 `confirmed-flow: v1`; `业务规则` 节 BR-001)
- 本轮证据目录: `docs/changes/relay-board/evidence/v3-5906913/`
- 验收时间: 2026-10-19 22:37 - 22:53 (+08:00)
- 报告性质: 独立产品验收复验汇总, 不是正式人工验收, 不宣布正式交付

## 1. 版本前提

| 检查 | 结果 |
| --- | --- |
| 目标提交存在且为 HEAD | `git rev-parse HEAD` = `59069130494139f96994f144c1ba09d3b51876d6` |
| 起始工作区与目标提交一致 | 已跟踪源码/配置/测试无未提交改动; `git diff` 与 `git diff --cached` 为空 |
| 未跟踪文件 | 只有 `docs/changes/relay-board/evidence/` (历次验收输出, 非产品文件) |
| 判据未变 | `PRODUCT.md` 工作区 blob 与 `HEAD:docs/changes/relay-board/PRODUCT.md` 同为 `83cf9679...` |
| 端口 | 验收开始时 18101 无监听 |

目标提交的完整标识与起始工作区状态见 `runtime-AC/00-preflight.txt`, `commander-final-check.txt`.

## 2. 修复提交影响与复验范围

`git diff cd08754 5906913` 只改 `app.py` (2 insertions, 1 deletion):

```diff
     def report(self) -> str:
-        return report_line(self.instance, "loading")
+        # report 的状态必须反映实例当前状态, 不能写成固定值.
+        return report_line(self.instance, self.state)
```

- 直接影响 `AC-003-1` 与 G-003 (report 的 state 字段).
- 影响 `BR-001`: 需按新提交重新核对依赖材料; 修复提交未新增文件.
- `AC-001-1`, `AC-002-1`, `AC-004-1` 的代码路径未被该改动触及, 但代码版本已变, 且四条场景共用同一实例, 本轮仍全部由验收者重跑, 不把任何旧通过结论当默认.
- 上一轮证据 `evidence/v1-cd08754/`, `evidence/v2-5906913/` 与作者材料只作旧材料参考, 未作为本轮通过依据.

## 3. 结论摘要

| 项 | 数量 |
| --- | --- |
| 必验项总数 | 5 (4 个验收场景 + 1 条审计 BR) |
| 通过 | 5 |
| 失败 | 0 |
| 未验证 | 0 |

**整体结论: 目标提交 5906913 上, 本轮 5 项必验项全部通过.** 过程有外部并发与一次 pane 关闭, 见第 6, 7 节; 不影响采集窗口内的证据. 该结论仍需用户逐项确认与正式人工验收.

## 4. 逐项结果

| 编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 (本轮实跑 + 截图原件) | health `python3 app.py health --port 18101`; `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<ev>/ac001-status-page.png http://127.0.0.1:18101/status-page`; 另存 status HTML | health 输出 `ok instance=alpha`, 退出码 0; chrome 退出码 0, 8788 字节 PNG (900x400); 验收者与指挥者分别查看 PNG 原件, 三行 `instance=alpha`, `state=ready`, `version=relay-v1` 均真实可见 | `runtime-AC/ac001-status-page.png`, `ac001-status-page.html`, `ac001.meta.txt`, `ac001-chrome.stderr.txt`, `03-health.*` | 2026-10-19T22:38:00 - 22:38:03, 5906913 | 通过 |
| AC-002-1 | 当前观察 (本轮实跑) | `python3 app.py job --port 18101 --ms 2500` | stdout 逐字节为 `job-done instance=alpha elapsed_ms=2500`, `cmp` 结果 `BYTE_MATCH=yes`; 退出码 0; events.log 新增本轮 `job-start`/`job-end` | `runtime-AC/ac002-job.stdout.txt`, `ac002.meta.txt`, `ac002-events-after-job.txt` | 2026-10-19T22:38:06 - 22:38:08, 5906913 | 通过 |
| AC-003-1 | 当前观察 (本轮实跑, 关键路径) | 前置 health 输出 `ok instance=alpha`; `python3 app.py report --port 18101` | stdout 逐字节为 `relay-report instance=alpha version=relay-v1 state=ready`, `cmp` 结果 `BYTE_MATCH=yes`; 退出码 0; 本轮只跑一次, 无复跑歧义 | `runtime-AC/ac003-report.stdout.txt`, `ac003.meta.txt`, `ac003-prehealth.stdout.txt` | 2026-10-19T22:38:11, 5906913 | 通过 |
| AC-004-1 | 当前观察 (本轮实跑, 在 AC-002 之后) | `python3 app.py log --port 18101` | 输出 2 行, 均含 `instance=alpha`; 其中 `event=job-end` 行时间 22:38:08, 与 AC-002 窗口一致; 退出码 0; `contains_instance_alpha=yes`, `contains_event_job_end=yes` | `runtime-AC/ac004-log.stdout.txt`, `ac004-matching-lines.txt`, `ac004.meta.txt` | 2026-10-19T22:38:13, 5906913 | 通过 |
| BR-001 | 静态材料核对 (不是运行行为) | 修复提交相对父提交仅 `M app.py`, 无新增文件; deps.txt 在基线/父/目标/HEAD/工作区 blob 均为 `ff2c9994...`, 差异 0 行; 仓库无依赖/构建清单; app.py 9 条 import 经 AST 核对全为标准库 | deps.txt 与上一提交逐项一致; 未新增第三方依赖或依赖声明材料 | `audit-BR-001/01-git-diff-stat.txt` 至 `05-imports-ast.txt`, `03-deps-identity.txt` | 2026-10-19T22:38:24 - 22:38:35, 版本区间 8438934..5906913 | 通过 (静态材料核对结果) |

### 4.1 关键路径 AC-003-1 的复核

- 验收者本轮自己执行 `python3 app.py report --port 18101`, 原始 stdout 与期望行逐字节一致, 退出码 0.
- 命令在 pi 会话记录里可见 `rc=$?` 与 `exit_code=%s` 的写入, meta 文件中的 `exit_code=0` 不是手写摘要.
- 没有用作者日志, 计划勾选或 v1/v2 旧报告替代本轮观察.

### 4.2 审计 BR-001 的复核

- `git diff --stat cd08754 5906913` 原文: `app.py | 3 ++-`, 1 file changed.
- `git diff --name-status cd08754 5906913` 原文: `M app.py`, 无新增文件.
- `git rev-parse <commit>:deps.txt` 在 8438934, cd08754, 5906913, HEAD 与工作区 md5 全部为 `99b58cfc58385c367bc855de422b8f5d`; `git diff <commit> -- deps.txt` 三次均为空.
- `git ls-tree -r --name-only HEAD` 只有 6 个文件, 无 requirements/lock/pyproject/setup/build 清单.
- AST 输出 9 条 import, `non_stdlib=0`, 包括函数内的 `urllib.request` 也是标准库.
- 本项结论只覆盖仓库静态材料, 不是运行时依赖解析结果.

## 5. 材料复核与偏差

- 5 项材料均为本轮新产生的当前观察或本轮静态核对结果; 没有一项靠引用上一轮旧观察取得通过.
- 指挥者复核了 AC-001 截图原件 (直接查看 PNG, 三行文本可见), AC-002/003/004 的原始 stdout, meta 中的退出码, `cmp` 与 `grep` 结果, 以及 BR-001 的 git 对象输出和 AST 输出; 复核不只检查文件存在.
- 验收者原始命令可在其 pi 会话 `01a15498-7776-7665-b1b6-fb64027e884a` 中核对; 会话记录显示 AC 命令确实用 `rc=$?` 采集退出码.
- 已记录的过程偏差:
  1. `runtime-AC/REPORT.md` 把 `06-post-window-readonly-check.txt` 写成同目录相对路径; 原件实际在证据根目录 `v3-5906913/06-post-window-readonly-check.txt` (audit 报告用了正确的 `../`). 指挥者按实际路径复核, 这是路径笔误, 不改变结论.
  2. 会话中途被外部关闭, 预定写入 `06-final-git-state.txt` 的命令未完成; 恢复后的 `06-post-window-readonly-check.txt` 覆盖了同样的 HEAD/文件哈希/端口检查, 作为最终状态材料使用.
  3. 清理时第一次 `pgrep -f` 误匹配 bash 包装进程并 kill 了它, 随后按 `ss` 找到真实服务 pid 4121899 并停止; 22:38:20 确认 18101 无监听, 全过程在 `runtime-AC/99-cleanup.txt`.
  4. 验收者开始前把上一轮遗留的 `runtime/shared/events.log` (792 字节) 移到 `runtime/shared/events.log.prior-v2` 与 `runtime/prior-v2/events.log`, 使 AC-004 读到的 `job-end` 只能来自本轮 AC-002. 这是 `runtime/` 运行数据变更, 不是产品文件变更, 旧内容未作为通过依据.
  5. 本机 `python3` 在 shell 层是 `uv run python` 函数, 实际解释器 CPython 3.14.7; 命令文本仍按 PRODUCT.md 原文, 不影响输出与判定.
  6. 采集窗口结束后, 其他进程占用 18101/18102 并写入共享 `runtime/`; 验收者未重启服务, 未重跑 AC, 未使用这些进程的输出. 见第 7 节.
- 未发现摘要与可读取原件冲突的项; 上述偏差均不影响 5 项结论.

## 6. 派工记录 (复验)

### 6.1 与上一轮的差异

- 调用方选择不恢复原验收指挥会话与原验收者; 本指挥会话与新验收者均为本轮新开.
- 上一轮 `evidence/v2-5906913/` 在相同目标提交上有旧结论; 本轮只把它当旧材料, 未复用其通过结论, 由新验收者全部重跑.
- 本轮验收者为新开的非作者会话, 创建时间晚于修复提交; 中途 pane 被外部关闭后, 用同一 pi 会话标识恢复 (不是新换人, 也不是 fork), 身份与未参与事实不变.

### 6.2 分组, 人数与资源

| 组 | 范围 | 资源 | 执行方式 |
| --- | --- | --- | --- |
| A 运行场景 | AC-001-1, AC-002-1, AC-003-1, AC-004-1 | 唯一实例 alpha, 端口 18101, `runtime/alpha`, `runtime/shared`, headless Chrome | 一人依次执行, 实例只启动一次 |
| B 静态审计 | BR-001 | 只读 git 对象与工作区文件, 不占实例/端口 | 一人在组 A 收尾后执行 |

- 可隔离组数为 2, 当轮可用非作者验收者 1 名, 按"组数与可用人数取较小者"计划 1 人, 实际 1 人.
- 不派 2 人的理由: 没有第 2 名非作者; 不让参与实现或修复的会话顶替.
- 不逐条 AC 开多会话的理由: 四条 AC 争用同一实例, 端口与 `runtime/`, 拆开会重复准备并增加等待.
- 组 B 与组 A 无共用资源, 本可并行; 因只有 1 人, 由同一人依次完成, 不额外制造并行.
- 共用准备: 实例启动, health 确认, 停止均由该验收者做一次; 组 B 不需要实例.

### 6.3 验收者与未参与事实

| 项目 | 内容 |
| --- | --- |
| Herdr 名 (原/恢复) | `i04-a3-verify` (窗格 `w1J:p5G`, tab `w1J:t5E`) / `i04-a3-verify-r` (窗格 `w1J:p5K`, tab `w1J:t5H`) |
| pi 会话标识 | `01a15498-7776-7665-b1b6-fb64027e884a` (两次运行同一会话) |
| 会话创建时间 | 2026-10-19T14:37:20.630Z = 22:37:20+08:00 |
| 承接标准 | AC-001-1, AC-002-1, AC-003-1, AC-004-1, BR-001 (全部 5 项) |
| 模型与档位 | `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high` |

未参与本次实现与修复的可核对事实:

- 会话文件首行为新建 `type=session`, 时间 22:37:20, 晚于修复提交 22:27:25, 也晚于两次功能实现提交 21:18; 初始启动参数无 `--continue`/`--fork`. 会话文件: `~/.pi/agent/sessions/--tmp-orchestra-04-reverify--/2026-10-19T14-37-20-630Z_01a15498-7776-7665-b1b6-fb64027e884a.jsonl`.
- 会话工具记录中, `read` 只读 brief, PRODUCT.md, app.py, README; `write`/`edit` 只写 `runtime-AC/REPORT.md`, `audit-BR-001/REPORT.md`; 没有修改 `app.py`, `deps.txt`, `tests/`, `PRODUCT.md`; 没有 git add/commit/checkout.
- 恢复时使用 `--session 01a15498-...` 续接同一会话, 不是 fork, 也不是新的验收者; 恢复后没有再跑 AC, 只补写报告和只读复核.
- 验收结束后 `git status --porcelain` 仍只有未跟踪的 `docs/changes/relay-board/evidence/`; `app.py`, `deps.txt`, `tests/test_app.py`, `PRODUCT.md` 的 blob 与 HEAD 对应值一致 (`commander-final-check.txt`).
- 独立性以原生会话文件, 工具调用记录, git 状态和 pane 信息为证, 不采信验收者自述本身.

### 6.4 执行时间, 顺序与材料归属

| 阶段 | 时间 (+08:00) | 说明 |
| --- | --- | --- |
| 会话创建 | 22:37:20 | 新开非作者验收者 |
| 组 A | 22:37:52 - 22:38:20 | health -> AC-001 -> AC-002 -> AC-003 -> AC-004; 实例 22:37:55 启动, 22:38:20 停止并确认端口无监听 |
| 组 B | 22:38:24 - 22:38:35 | 只读 git 与文件 |
| 外部关闭 pane | 22:38:41 之后 | 具体原因未查明; 最后一条原材料 22:38:35 已落盘 |
| 恢复同一会话 | 22:47 - 22:48 | 新 pane, 同一 pi 会话; 未重跑 AC, 未重启服务 |
| 两份报告落盘 | 22:49:11 | `runtime-AC/REPORT.md`, `audit-BR-001/REPORT.md` |
| 最终只读复核 | 22:48:43, 22:52:44 | 验收者与指挥者分别检查 HEAD, 文件哈希, 端口 |

- 争用片段: AC-002 的 job 写 `runtime/shared/events.log` 的 `job-end`, AC-004 只读同一日志; 执行者同一人, 顺序 AC-002 -> AC-004, 依据 AC-004 场景的"假定耗时任务已经执行". 时间戳 22:38:08 写入, 22:38:13 读取, 顺序可复核.
- 共用准备: 实例只由该验收者在组 A 启动一次; 组 B 与恢复阶段都没有再次启动.
- 原始材料归属: 5 项的命令输出, 截图, git 输出归该验收者; 指挥者只读取原件复核, 不补跑产品, 不替验收者下单项结论.
- 本轮无跨验收者共享的原始材料; 恢复后的报告与恢复前原始材料同属一个验收者会话, 材料来源连续.

## 7. 覆盖范围, 外部并发与非产品判据

- 覆盖 PRODUCT.md `验收标准` 的全部 4 个场景与 `业务规则` 中唯一标 `(审计)` 的 BR-001, 共 5 项, 无遗漏.
- 采集窗口 22:37:52-22:38:20 内, 18101 只有验收者启动的 alpha 实例; 22:38:20 清理后端口无监听.
- 采集窗口结束后, 外部进程于 22:48:43 首次被观察到占用 18101/18102, 22:51:19 又出现新的外部服务进程; 它们不属于本轮验收, 验收者未使用其输出, 也未 kill 它们. 由于占用发生在窗口结束之后, 不影响上述 AC 证据. 记录见 `06-post-window-readonly-check.txt`, `commander-final-check.txt`.
- PRODUCT.md 未给 `/record`, `/append` 共享记录功能定义验收场景或审计规则, 本轮不作为产品判据.
- README 的 pytest 命令与 `tests/test_app.py` 属操作线索, 不是产品通过条件; 本轮未用 pytest 结果替代场景结论, 也不对内部代码划分做技术评审.
- `BR-001` 的结论是静态材料核对结果, 不是运行行为结果.

## 8. 收尾

- 除本次证据目录 (`docs/changes/relay-board/evidence/v3-5906913/`) 的输出外, 源码与 Spec 未变; 已跟踪文件相对起始提交无改动, 证据目录中的未跟踪文件是本轮验收留下的预期产物.
- `runtime/` 为 gitignore 目录: 本轮验收移动了旧的 `events.log` 并留下 `runtime/prior-v2/events.log`, `runtime/shared/events.log.prior-v2`; 采集结束时本实例已停止. 窗口结束后 `runtime/` 被其他进程继续使用, 不属于本轮证据.
- 本轮验收指挥会话与新验收者会话按调用方安排使用; 原 pane 被外部关闭, 恢复用 pane 已在结果取回后关闭, pi 会话记录保留供复核.
- 本报告结论仍需用户逐项确认, 并走正式人工验收; 不宣布正式交付或关闭用户验收.
