# 独立产品验收复验报告 (round 2)

- 新目标提交: `59069130494139f96994f144c1ba09d3b51876d6` (HEAD)
- 修复提交的父提交: `cd087542b4610c49ded0a1278fe8065726b62d9d` (上一轮目标提交)
- 基线提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`
- 判据来源: `docs/changes/relay-board/PRODUCT.md` (验收标准 `confirmed-flow: v1`, 业务规则 BR-001), 本轮未变
- 本轮证据目录: `docs/changes/relay-board/evidence/v2-5906913/`
- 上一轮证据目录: `docs/changes/relay-board/evidence/v1-cd08754/` (保留, 未覆盖)
- 验收时间: 2026-10-19 22:29 - 22:31 (+08:00)
- 报告性质: 独立产品验收复验汇总, 不是正式人工验收, 也不宣布正式交付

## 1. 版本前提

| 检查 | 结果 |
| --- | --- |
| 新目标提交存在且为 HEAD | `git rev-parse HEAD` = `59069130494139f96994f144c1ba09d3b51876d6` |
| 起始工作区与目标提交一致 | 已跟踪源码/配置/测试无未提交改动; `git diff` 与 `git diff --cached` 为空 |
| 未跟踪文件 | 只有上一轮与本轮证据目录 (`docs/changes/relay-board/evidence/`), 属验收输出, 不是产品文件 |
| 判据未变 | PRODUCT.md 仍有 `confirmed-flow: v1` 标记, 内容未改 |
| 验收后产品改动 | HEAD 未变; 已跟踪文件零改动; 未跟踪新增仅为本轮证据 |

## 2. 修复提交与影响范围

`git diff cd08754 5906913` 只改 `app.py` (2 insertions, 1 deletion):

```diff
     def report(self) -> str:
-        return report_line(self.instance, "loading")
+        # report 的状态必须反映实例当前状态, 不能写成固定值.
+        return report_line(self.instance, self.state)
```

- 直接影响 `AC-003-1` (report 状态) 与 G-003: 上一轮失败点正是 `state=loading`; 本轮由验收者重跑关键路径.
- 影响 `BR-001`: 需按新提交重新核对依赖材料与 deps.txt; 修复提交未新增文件.
- `AC-001-1`, `AC-002-1`, `AC-004-1` 的代码路径未被该改动触及; 但代码版本已变, 且四条场景共用同一实例, 本轮仍全部由验收者重跑, 不把上一轮通过结论当默认.
- 作者材料 `/tmp/orchestra-04/author-materials/green/` 只作参考引用, 不作为本轮证据; 受影响的关键路径 AC-003 由验收者本轮自己操作并留原始记录.

## 3. 结论摘要

| 项 | 数量 |
| --- | --- |
| 必验项总数 | 5 (4 个验收场景 + 1 条审计 BR) |
| 通过 | 5 |
| 失败 | 0 |
| 未验证 | 0 |

**整体结论: 本轮 5 项必验项全部通过.** 上一轮失败的 `AC-003-1` 在本轮新提交上已实跑通过. 该结论仍需用户逐项确认与正式人工验收, 见第 8 节.

## 4. 逐项结果

| 编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 (本轮实跑 + 截图原件) | 实例 alpha 在 127.0.0.1:18101 启动一次, health 返回 `ok instance=alpha` (退出码 0); `google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 --screenshot=<ev>/ac001-status-page.png http://127.0.0.1:18101/status-page` 退出码 0 | 截图 (900x400 PNG, 8788 字节) 可见 `instance=alpha`, `state=ready`, `version=relay-v1`; 指挥者复核了 png 原件 | `evidence/v2-5906913/runtime-AC/ac001-status-page.png`, `03-ac001-chrome.txt`, `02-health.txt` | 2026-10-19T22:29:58 - 22:29:59, 5906913 | 通过 |
| AC-002-1 | 当前观察 (本轮实跑) | `python3 app.py job --port 18101 --ms 2500` | stdout 为 `job-done instance=alpha elapsed_ms=2500`, 与期望逐字节一致; 退出码 0; 本轮 job 写入的 job-start/job-end 见 events.log | `evidence/v2-5906913/runtime-AC/04-ac002-job.txt`, `runtime-shared-events.log.after` | 2026-10-19T22:30:02 - 22:30:05, 5906913 | 通过 |
| AC-003-1 | 当前观察 (本轮实跑, 关键路径) | health 前置 `ok instance=alpha`; `python3 app.py report --port 18101` | 实际 stdout `relay-report instance=alpha version=relay-v1 state=ready`, 与期望逐字节一致; 退出码 0; 另复跑 3 次均为 `state=ready` | `evidence/v2-5906913/runtime-AC/05-ac003-report.txt`, `07-ac003-report-repeat.txt` | 2026-10-19T22:30:16 (复跑 22:30:22/23/24), 5906913 | 通过 |
| AC-004-1 | 当前观察 (本轮实跑) | 在本轮 AC-002 的 job 完成后执行 `python3 app.py log --port 18101` | 输出 12 行, 均含 `instance=alpha`, 其中 6 行含 `event=job-end`; 含本轮 22:30:05 的 `event=job-end ms=2500`; 退出码 0 | `evidence/v2-5906913/runtime-AC/06-ac004-log.txt`, `runtime-shared-events.log.final` | 2026-10-19T22:30:18, 5906913 | 通过 |
| BR-001 | 静态材料核对 (不是运行行为) | 修复提交 5906913 相对父提交 cd08754 仅 `M app.py`, 无新增文件; deps.txt 在 8438934/cd08754/5906913 三个提交与工作区均为同一 blob `ff2c9994...`, 差异 0 行; app.py 8 个顶层 import 经 AST 核对均为标准库; 仓库无 requirements/lock/pyproject/setup/build 文件 | deps.txt 与上一提交逐项一致; 修复提交与累计变更均未新增第三方依赖 | `evidence/v2-5906913/audit-BR-001/REPORT.md` 检查 1-5 与逐项结论 | 2026-10-19T22:29:41 起, 版本区间 8438934..5906913 | 通过 (静态材料核对结果) |

### 复验重点: AC-003-1

- 上一轮 (cd08754) 同一命令返回 `state=loading`, 已判失败.
- 本轮 (5906913) 验收者自己执行同一命令, 返回 `state=ready`, 与 PRODUCT.md 期望逐字节一致; 连跑 3 次复现; 退出码 0.
- 作者材料 `/tmp/orchestra-04/author-materials/green/report-status-verify.log` 等只作参考, 未作为本轮通过依据; 本轮通过依据是 `05-ac003-report.txt` 与 `07-ac003-report-repeat.txt`.

## 5. 材料与证据复核

- 5 项材料均为本轮新产生的当前观察或本轮静态核对结果. 本轮没有任何一项靠引用上一轮旧观察取得通过结论; 上一轮证据只用于说明 AC-003 的失败点已修复.
- 指挥者复核了 AC-001 截图原件, 可见三行目标文本; 复核了 AC-002/003/004 的原始 stdout, 退出码与逐字节对照; 复核了 BR-001 的 git 对象, blob, import 与文件清单.
- 过程偏差 (验收者已在报告中如实记录):
  - AC-002 为采集字节级证据多跑了 2 次, 共 3 次 job; 判定以第一次 (22:30:02-22:30:05) 的输出与退出码为准, 重复运行输出相同.
  - 清理命令的 `pgrep -f` 同时匹配到执行清理的 shell 自身, 记录 shell 收到 SIGTERM (退出码 143); 随后复查服务进程无残留, 端口 18101 无监听, health curl 退出码 7.
  - `02-health.txt` 的时间写作 `22:29:5x`, 秒级不精确; 但命令原始输出 `ok instance=alpha` 与退出码 0 完整.
  - AC-004 的 `events.log` 含上一轮与作者运行遗留行; 本轮 AC-002 的 22:30 job-end 也在其中. AC-004 判据只要求输出含 `instance=alpha` 与 `event=job-end` 且退出码 0, 已满足; 报告中的行数 6->12 是辅助记录, 不作为"只读性"单独判据.
  - 本机 `python-operation-hook` 把 `python3` 在 shell 层透明替换为 `uv run python`; 命令文本仍为 PRODUCT.md 原文, 实际解释器为 uv 管理 CPython 3.14.7. 不影响命令文本, 输出与判定.
- 材料更正: 本轮两份验收报告均未出现需要驳回结论的摘要与原件冲突; 发现的口径问题已在上面如实注明, 不改变任何结论.

## 6. 派工记录 (复验)

### 6.1 承担者与上一轮的差异

| 角色 | 上一轮 | 本轮 | 说明 |
| --- | --- | --- | --- |
| 指挥 | `i04-v1` (本会话) | 恢复 `i04-v1` | 调用方安排恢复原验收指挥会话; 指挥者未参与实现或修复 |
| 组 1 运行场景 | `i04-a1-ac` | 新开 `i04-a2-ac` | `i04-a1-ac` 在修复阶段亲自改 app.py 并提交 5906913, 不能再承担独立验收 |
| 组 2 静态审计 | `i04-a1-br` | 新开 `i04-a2-br` | 原会话已关闭, 按调用方安排新开非作者 |

`i04-a1-ac` 参与修复的可核对事实: 其 pi 会话 `01a1548b-b975-7213-9d28-db1121880578` 在 2026-10-19T22:27 有 `git add app.py && git commit` 记录, 与修复提交 5906913 (22:27:25) 对应. 因此其旧证据只作材料, 不再作为本轮独立验收依据.

### 6.2 本轮验收者与未参与事实

| 组 | 验收者 (Herdr 名) | 窗格/标签 | pi 会话标识 | 会话文件创建时间 | 承接标准 | 模型与档位 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `i04-a2-ac` | `w1J:p5E` / `w1J:t5C` | `01a15491-3574-7683-ba0b-44d2189988df` | 2026-10-19T22:29:24+08:00 | AC-001-1, AC-002-1, AC-003-1, AC-004-1 | `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high` |
| 2 | `i04-a2-br` | `w1J:p5D` / `w1J:t5B` | `01a15491-2613-742c-ba9d-4ae128d34099` | 2026-10-19T22:29:21+08:00 | BR-001 | `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high` |

未参与本次实现与修复的可核对事实:

- 两个会话均为本轮新开: 会话文件首行为新建 `type=session` 记录, 首条 model_change 的 parentId 为 null, 启动参数无 `--continue`/`--fork`; 创建时间 22:29:21 与 22:29:24 均晚于修复提交时间 22:27:25.
- 会话工具调用记录: 组 1 无 `edit`, 只有 1 次 `write` 写自己的 `runtime-AC/REPORT.md`; 组 2 的 `write`/`edit` 均只作用于自己的 `audit-BR-001/REPORT.md`; 两者都没有改产品文件, 没有 git add/commit/checkout.
- 验收后 `git diff` 为空, HEAD 仍为 5906913; 已跟踪产品文件 (app.py, deps.txt, tests/, PRODUCT.md) 未变.
- 独立性以原生会话文件, 工具调用记录和 git 状态为证, 不采信验收者自述本身.

### 6.3 执行时间与顺序

| 组 | 开始 (会话文件创建 / 首条命令) | 结束 (会话最后记录) | 说明 |
| --- | --- | --- | --- |
| 1 `i04-a2-ac` | 22:29:24 / 22:29:49 (首份证据) | 2026-10-19T22:30:54+08:00 | 实例 22:29:50 启动, 22:30:27 停止; 顺序 health -> AC-001 -> AC-002 -> AC-003 -> AC-004 -> AC-003 复跑 -> 清理 |
| 2 `i04-a2-br` | 22:29:21 / 22:29:41 (首条 date) | 2026-10-19T22:30:17+08:00 | 与组 1 并行, 只读 git 与文件 |

- 组 1 内部写入/读取顺序: AC-002 的 job 于 22:30:05 写入 job-end, AC-004 于 22:30:18 读取到本轮 `event=job-end`; 执行者 `i04-a2-ac`, 依据 `PLAN.md` 的争用说明.
- 组 2 无写入产品文件, 无争用片段.

### 6.4 共用准备, 材料归属与共享

- 共用准备: 实例只由组 1 启动一次 (22:29:50), health 确认 (22:29:56), 结束停止 (22:30:27); 组 2 不需要实例, 未重复准备.
- 原始材料归属: 组 1 的命令输出, 截图, runtime 快照归 `i04-a2-ac`; 组 2 的 git 输出与静态核对归 `i04-a2-br`; 各自下自己的结论.
- 共享材料: 本轮无跨验收者共享的原始材料; 指挥者只读取原件复核, 不代替验收者下单条结论, 不补跑产品.
- 详细计划原件: `evidence/v2-5906913/PLAN.md`.

## 7. 覆盖范围与非产品判据

- 覆盖范围: PRODUCT.md `验收标准` 的全部 4 个场景与 `业务规则` 中唯一标 `(审计)` 的 BR-001, 共 5 项, 无遗漏.
- 目标提交中的共享记录 (`/record`, `/append`) 在 PRODUCT.md 中没有对应验收场景或审计规则, 本轮不作为产品判据.
- `README.md` 的 pytest 命令与 `tests/test_app.py` 属运行线索, 不是 PRODUCT.md 的产品通过条件; 作者材料里的 pytest 日志只作参考, 本轮未把测试结果当作场景结论, 也不对内部代码划分做技术评审.
- `BR-001` 的结论是静态材料核对结果, 不是运行行为结果.

## 8. 收尾

- 除本次证据目录 (`docs/changes/relay-board/evidence/v2-5906913/`) 的输出外, 源码与 Spec 未变; 已跟踪文件相对起始提交无改动, 证据目录中的未跟踪文件是本轮验收留下的预期产物.
- `runtime/` 为 gitignore 目录: 本轮服务在该目录留下 `runtime/shared/events.log`; 服务已停止, 端口 18101 无监听, 无残留进程.
- 本轮验收会话按调用方要求保留 (指挥会话与 `i04-a2-ac`, `i04-a2-br`), 未关闭, 供后续复验使用.
- 本报告结论仍需用户逐项确认, 并走正式人工验收; 不宣布正式交付或关闭用户验收.
