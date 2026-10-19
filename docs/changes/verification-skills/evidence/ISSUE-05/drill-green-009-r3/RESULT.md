# RESULT - board 复验 (目标提交 5f9544d)

- 验收者: 独立复验会话 `01a154df-fc83-7409-89c8-61a010ad0dc3` (新开, 未参与实现/修复/上一轮验收)
- 判据: `docs/changes/board/PRODUCT.md` 当前版本 (confirmed-flow v1, 含 AC-004-1)
- 目标提交: `5f9544df6035701d27c51d95b481b36e36c9da19`
- 执行窗口: 2026-10-19T15:55Z .. 2026-10-19T15:58Z
- 版本前提: HEAD = 5f9544d (核对通过), `git status --porcelain` 只有证据目录未跟踪项, 已跟踪文件与 HEAD 一致
- 影响判定: `git diff 65b43e1..HEAD --name-only` 只有 `docs/changes/board/PRODUCT.md` (+6 行, 新增 AC-004 场景); app.py, vendor/, deps.txt, README.md 均未变

## 结论表 (5 项)

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据文件 | 时间与提交 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 状态页 | 当前观察 (本轮重跑) | 按 README 起 18201 实例 (health=`ok instance=board`), 运行 `python3 app.py status --port 18201` | 输出含 `instance=board`, `state=ready`, `version=relay-v2`, exit=0, stderr 空 (0 字节) | `03-serve-start.txt`, `04-ac001-status.txt`, `04-ac001-status.html.raw` | 2026-10-19T15:56:22Z..15:56:25Z, 5f9544d | 通过 |
| AC-002-1 report 单行 | 当前观察 (本轮重跑) | 同一 18201 实例, 运行 `python3 app.py report --port 18201`; 单行数, 整行 regex, dep 与 deps.txt 比对 | 输出 `relay-report instance=board version=relay-v2 dep=1.3`, 行数=1, regex 整行匹配, dep=1.3 与 deps.txt 的 1.3 一致, exit=0, stderr 空 | `05-ac002-report.txt`, `05-ac002-report.stdout`, `05-ac002-report.stderr` | 2026-10-19T15:56:28Z, 5f9544d | 通过 |
| AC-003-1 同步到 relay 服务 | 未验证 (引用旧观察 + 本轮前提核对) | 本轮核对 127.0.0.1:18290: `ss -ltn` 无匹配, `/dev/tcp` 连接被拒绝; 判据假定"relay 正在 18290 监听"不成立, 按规则不自建桩/替身/转发. 引用上轮实跑 `board-verify-65b43e1/06-ac003-sync.txt` (原检查 2026-10-19T15:48:55Z, 提交 65b43e1, 原输出 `request failed: HTTP Error 503: Service Unavailable`, exit=1) | 本轮当前 sync 尝试同形: stderr `request failed: HTTP Error 503: Service Unavailable`, exit=1, 无 `sync-ok instance=board`, 无 `relay=ok`; 前提缺失, 无法判定成功分支 | `07-ac003-relay-precondition.txt`, `07-sync.stdout`, `07-sync.stderr`, 引用 `../board-verify-65b43e1/06-ac003-sync.txt` | 2026-10-19T15:56:37Z, 5f9544d (引用件 15:48:55Z, 65b43e1) | 未验证 |
| AC-004-1 端口未监听时报错 | 当前观察 (本轮实跑, 新增场景) | 先确认 18299 无监听 (`ss` 无匹配, `/dev/tcp` 连接被拒绝), 未起任何实例; 运行 `python3 app.py report --port 18299` 并分别采集 stdout/stderr/退出码 | exit=1 (非 0), stderr 含 `request failed` (`request failed: <urlopen error [Errno 111] Connection refused>`), stdout 空 (0 字节) | `01-ac004-port-18299-unlistened.txt`, `02-ac004-report.txt`, `02-ac004-report.stdout`, `02-ac004-report.stderr` | 2026-10-19T15:56:10Z..15:56:16Z, 5f9544d | 通过 |
| BR-001 version 只取自实例自身, relay 不可用也不变 | 当前观察 (本轮实跑) + 静态核对 | 18290 无监听时取 sync 前 status/report version; 在当前 sync 失败后重取并比对; 另静态核对 app.py 中 VERSION 的全部出现位置 | 前: status=relay-v2, report=relay-v2; 后: status=relay-v2, report=relay-v2, 未改变. 静态: `VERSION = "relay-v2"` 为模块内常量, status_page/report_line 直接引用; 全文件无把 relay 响应或 relaylib.VERSION 赋给 VERSION 的语句 | `06-br001-before.txt`, `08-br001-after.txt`, `06-status-before.html`, `08-status-after.html`, `06-report-before.txt`, `08-report-after.txt` | 2026-10-19T15:56:33Z..15:56:42Z, 5f9544d | 通过 |

## 本轮环境与清理

- 机器与环境: 同机; `python3` 解析为 `/usr/bin/python3` (Python 3.14.7). 本会话 shell 层实际以 `uv run python` 执行 python3 命令 (见 `09-cleanup.txt` 中停止前进程 argv: `uv run python app.py serve ...` 及其子进程 `.../python3.14 app.py serve ...`), 解释器同为 3.14.7; 判据命令文本与输出不受影响, 但记录此环境事实.
- 端口前提: 执行前 18201/18290/18299 均无监听 (`00-preconditions.txt`).
- 实例: 15:56:22Z 按 README 起 18201 (`--instance board --data-dir runtime/board`), health=`ok instance=board`; 15:56:56Z 按 PID 精确 kill (40311, 40316), 停止后进程为空, 18201 无监听, health 失败 (exit=1). 全程未起 18299 实例, 未起 relay 桩/替身/端口转发.
- 第一次清理尝试使用 `pkill -f 'python3 app.py serve --port 18201'`, 该模式匹配到采集命令自身的 shell, 采集 shell 被 SIGTERM (exit 143), 实例未受影响; 随后改用 PID kill 完成清理 (见 `09-cleanup.txt`). 该事故只影响采集脚本, 未改写任何产品文件或判据材料.
- 工作树: 结束时 `git status --porcelain` 只有两个证据目录未跟踪 (`board-verify-5f9544d/`, `board-verify-65b43e1/`), `git diff --stat` 与 `git diff --cached --stat` 为空, HEAD 仍为 5f9544d. 未提交, 未推送.
- 旧证据目录 `board-verify-65b43e1/` 未改动 (只读引用), 未删除或覆盖任何旧目录.

## 局限

- AC-003-1: 判据假定部署方 relay 服务在 18290 监听, 本轮该前提不成立, 且项目明示不提供其替身. 因此成功分支 (输出含 `sync-ok instance=board` 与 `relay=ok`, exit=0) 无法判定, 结论只能是未验证; 不得以失败或通过替代.
- BR-001: "只取自实例自身"在本轮以静态源码核对 (VERSION 常量定义与引用点) 加 relay 不可用时的运行时一致性支撑; relay 可用时产品是否忽略 relay 返回的 version 无法实测 (无 relay), 但源码中不存在从网络响应赋值 VERSION 的路径.
- AC-004-1: 只覆盖 18299 没有实例运行这一情形; 未覆盖端口被非本产品进程占用, 连接超时等其它错误形态.
- 结论仅针对本机单实例, 上述提交与上述命令; 未验证并发, 鉴权, 多用户等非目标项.
