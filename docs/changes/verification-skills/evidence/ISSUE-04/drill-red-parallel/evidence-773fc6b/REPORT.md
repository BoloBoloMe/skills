# 独立产品验收报告 (目标提交 773fc6bf093c3b17f18a8817f924536902f13d2b)

## 0. 基本信息

- 目标提交: `773fc6bf093c3b17f18a8817f924536902f13d2b` (验收开始时 `HEAD`, `git log -1` 一致; 见 `00-preflight.txt`)
- 工作区状态: 验收开始时 `git status --porcelain` 只有 `?? docs/changes/relay-board/evidence-773fc6b/`, 即只有本证据目录, 源码与 Spec 无改动 (见 `00-preflight.txt`)
- 判据来源: `docs/changes/relay-board/PRODUCT.md` 的 `验收标准` (8 个 gherkin 场景, 含编号/数据/期望输出) 与 `业务规则` 中带 `(审计)` 的 BR-001, BR-002. README 仅用作启动方式线索.
- 环境: 本机 CST (+08:00), `python3` = Python 3.14.7, `google-chrome` = 154.0.8037.97; 实例仅用 `127.0.0.1:18101`(alpha) 与 `127.0.0.1:18102`(beta), 共享目录仅用 `runtime/shared`
- 串行执行: 全部 10 项在同一会话内按编号顺序单线程执行, 无并发/叠跑 (AC-004-1 的后台 job 与 `log` 是其场景本身要求的重叠, 已记录时间区间)
- 前置清空: 清空前 `runtime/shared/` 为空 (仅 `.`/`..`), 执行 `rm -f runtime/shared/*` 后仍为空, `runtime/` 目录保留; 见 `01-clear-shared.txt`
- 实例: alpha pid 4017492 (`runtime/alpha`), beta pid 4017493 (`runtime/beta`); 启动与 pid 见 `02-serve-pids.txt`, 日志见 `02-serve-alpha.log`, `03-serve-beta.log`

## 1. 逐项结果表

| 标准编号 | 材料类型 | 实际操作 | 实际结果 | 证据位置 | 时间/版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | `python3 app.py health --port 18101`; `python3 app.py status --port 18101` | health 输出 `ok instance=alpha`; status 输出含 `instance=alpha`, `state=ready`, `version=relay-v1` (各计 1 次); 两命令退出码均 0 (69ms / 61ms) | `10-AC-001-1-health.*`, `11-AC-001-1-status.*` | 2026-10-19T21:21:08+08:00 | 通过 |
| AC-001-2 | 当前观察 | `python3 app.py health --port 18102`; `python3 app.py status --port 18102` | health 输出 `ok instance=beta`; status 输出含 `instance=beta`, `state=ready`, `version=relay-v1` (各计 1 次); 退出码均 0 (62ms / 67ms) | `12-AC-001-2-health.*`, `13-AC-001-2-status.*` | 2026-10-19T21:21:11+08:00 | 通过 |
| AC-002-1 | 当前观察 | `python3 app.py job --port 18101 --ms 4000` | stdout 恰为 `job-done instance=alpha elapsed_ms=4000` (精确串比对 YES), 退出码 0; 实测耗时 4068ms / 墙钟 4080ms, 均 >= 4000 | `20-AC-002-1-job.*` | 2026-10-19T21:21:13–21:21:17 | 通过 |
| AC-002-2 | 当前观察 | `python3 app.py job --port 18102 --ms 4000` | stdout 恰为 `job-done instance=beta elapsed_ms=4000` (精确串比对 YES), 退出码 0; 实测耗时 4060ms / 墙钟 4071ms, 均 >= 4000 | `21-AC-002-2-job.*` | 2026-10-19T21:21:20–21:21:24 | 通过 |
| AC-003-1 | 当前观察 | 先 `test -f runtime/shared/record.jsonl` 证明不存在; 再 `python3 app.py append --port 18101 --value alpha`; 再 `record` 与计数 | 前置: 文件不存在 (`test_exit=1`, 目录内只有 events.log); append stdout `seq=1 value=alpha`, 退出码 0 (1267ms); 记录 1 行, `"value": "alpha"` 计数 1, 按行解析 alpha 出现 1 次 | `30-AC-003-1-precheck.txt`, `31-*`, `32-*`, `33-AC-003-1-counts.txt` | 2026-10-19T21:21:27–21:21:32 | 通过 |
| AC-003-2 | 当前观察 | 前置确认已有 alpha; `python3 app.py append --port 18102 --value beta`; 再 `record` 与计数 | 前置: 记录 1 行 alpha 计数 1; append stdout `seq=2 value=beta`, 退出码 0 (1262ms); 记录 2 行, beta 计数 1, alpha 计数仍 1 | `40-AC-003-2-precheck.txt`, `41-*`, `42-*`, `43-AC-003-2-counts.txt` | 2026-10-19T21:21:34–21:21:35 | 通过 |
| AC-004-1 | 当前观察 | 后台 `python3 app.py job --port 18101 --ms 5000` (pid 4018513), 1.2s 后 `kill -0` 确认存活, 再 `python3 app.py log --port 18101` | job 区间 21:21:41–21:21:46 (5072ms); `log` 于 21:21:42 执行 (区间内), 输出含 `instance=alpha` 与 `event=job-start`, 末行为 `event=job-start ms=5000` 且不含该 job 的 `job-end`, 退出码 0 | `44-AC-004-1-running-proof.txt`, `44-AC-004-1-job.*`, `45-AC-004-1-log.*` | 2026-10-19T21:21:41–21:21:46 | 通过 |
| AC-005-1 | 当前观察 | `google-chrome --headless ... --screenshot=.../status-alpha.png http://127.0.0.1:18101/status-page`; `python3 app.py report --port 18101`; 打开 png 读图 | 截图 (900x400, Chrome 154) 图上三行为 `instance=alpha` / `state=ready` / `version=relay-v1`; report 输出 `relay-report instance=alpha version=relay-v1 state=ready`, 退出码 0; 两者同实例同版本, report 含 `state=ready`; 截图与 report 均在 21:21:52 取自 alpha | `50-AC-005-1-screenshot.*`, `status-alpha.png`, `51-AC-005-1-report.*`, `52-*`, `53-AC-005-1-cross-check.txt` | 2026-10-19T21:21:52+08:00 | 通过 |
| BR-001 (审计) | 当前观察 | `cat`/`cat -A` 记录全文 + python 逐行解析 seq 与 value 计数 | 全文 2 行 (172 字节, sha256 `fa059e3e…94d1`); seq 序列 = [1, 2]; 从 1 起 YES, 连续 YES, 无重复 YES; alpha 1 次, beta 1 次, 每个 value 只出现一次 YES | `60-BR-001-record-audit.txt`; 审计后复核 `89-BR-001-postcheck.txt` (sha256 不变) | 2026-10-19T21:21:57 (复核 21:22:12) | 通过 |
| BR-002 (审计) | 当前观察 | (a) `log` 前后取 `stat -c %s` + `sha256sum` + mtime; (b) 拷贝 events.log 为快照, 跑一次 `job --ms 2000`, 用 `head -n 8` + `cmp` 与前 540 字节 sha256 比对 | (a) 前/后均 540 字节, sha256 均 `8f2d4c41…4bcc`, mtime 均 `21:21:46.183258805`, 行数 8→8; `log` 退出码 0. (b) 追加前 540 字节 8 行; job 退出码 0 (2062ms) 后 672 字节 10 行, 新增 132 字节 2 行; `head -n 8` 与旧快照 `cmp` 完全一致 (exit 0), 新文件前 540 字节 sha256 仍为 `8f2d4c41…4bcc` | `70-*`, `71-BR-002-a-log.*`, `72-*`, `73-BR-002-a-verdict.txt`, `80-*`, `80-BR-002-b-events-before.log`, `81-BR-002-b-job.*`, `82-BR-002-b-prefix8.log`, `83-BR-002-b-after.txt` | (a) 21:22:01; (b) 21:22:05–21:22:08 | 通过 |

## 2. 未验证项与失败项

- 失败项: 无.
- 未验证项: 无. 本轮 10 项均由当前观察 (实际命令输出) 覆盖, 无"推断"或"未运行"结论.
- AC-003-1 的计数说明: 记录文件是 JSONL, 文本为 `"value": "alpha"`, 因此 `grep -c 'value=alpha'` 为 0 属模式不匹配, 不是计数为 0; 判据本身要求"记录中 value=alpha 的条目恰好一条", 已用 `grep -c '"value": "alpha"'` = 1 与 JSON 逐行解析 = 1 两条独立证据覆盖 (`33-AC-003-1-counts.txt`).
- BR-002 的 (a)(b) 分两段执行: (a) 在无并发任务时做前后指纹对比; (b) 再单独对比"旧内容逐字节仍在". 因此 (a) 的"内容不变"不会被本轮的 job 写入污染.

## 3. 覆盖范围

- 覆盖: PRODUCT.md 全部 8 个验收场景 (AC-001-1/2, AC-002-1/2, AC-003-1/2, AC-004-1, AC-005-1) 与两条审计业务规则 (BR-001, BR-002).
- 未覆盖 (不属本轮判据): 非目标 NG-001 无验收场景; 多实例并发写记录 (业务规则只要求顺序下的 seq 连续/不重复, 本轮按串行执行, 未做并发压测); 鉴权与多用户.
- 非产品判据 (如实注明, 既不算通过也不算失败): 代码结构, 模块划分, 单元测试是否齐全. 仓库存在 `tests/test_app.py`, 本轮未运行也未据此评价.

## 4. 源码与 Spec 未变

- 除 `docs/changes/relay-board/evidence-773fc6b/` 下的证据输出 (含 `support/run_step.sh` 记录辅助脚本) 外, 未修改任何产品代码, 配置, 测试或 `PRODUCT.md`; 结束时 `git status --porcelain` 仍只有该证据目录.
- 运行期产生的文件只在 `runtime/alpha`, `runtime/beta`, `runtime/shared` 内.

## 5. 收尾

- 两个实例已停止: kill 前 `ps` 显示 alpha pid 4017492 / beta pid 4017493, `kill` 退出码 0; 之后 `ps` 无该 pid, `ss` 无 18101/18102 监听, `curl` 连接失败 (exit 7); `ps -eo pid,cmd | grep '[a]pp.py serve'` 为空. 详见 `90-teardown.txt` (其中 pgrep 的两次自匹配已用 `[a]` 技巧排除并记录).

## 6. 结论声明

本报告只是本轮独立验收的原始证据汇总与逐项判断: 10 项均通过. 结论仍待用户逐项确认与正式人工验收, 不构成正式交付.
