# RESULT.md — board 独立验收 (目标提交 65b43e1)

- 目标提交: `65b43e1268bf029f199f7782a2185a670a4eef7f` (`feat: 依赖升级到 1.3`)
- 判据来源: `docs/changes/board/PRODUCT.md`, 验收标准节 `<!-- confirmed-flow: v1 -->`
- 验收会话: 本会话新开, 未参与实现与修复 (见 SESSION-NOTES.md)
- 全部材料时间基准: UTC; 执行区间 2026-10-19T15:48:26Z .. 2026-10-19T15:49:08Z

## 结论表

| 标准编号 | 材料类型 | 实际操作 | 实际结果 | 证据文件 | 时间与提交 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 | 当前观察 | `python3 app.py status --port 18201` (实例 board 在 127.0.0.1:18201 运行, 前置 health 返回 `ok instance=board`) | 输出含 `instance=board`, `state=ready`, `version=relay-v2`, 三条 grep 各命中 1 次; 退出码 0 | `02-health.txt`, `03-ac001-status.html.raw`, `01-serve-start.txt`, `server.stdout.log` | 2026-10-19T15:48:36Z..15:48:40Z @ 65b43e1 | 通过 |
| AC-002-1 | 当前观察 | `python3 app.py report --port 18201`, 并用 `awk '{print $NF}'` 从 `deps.txt` 取版本号比对 | 输出 `relay-report instance=board version=relay-v2 dep=1.3`, 单行 (`wc -l`=1), 形状 regex 完全匹配; `deps.txt` 内容 `relaylib (vendor) 1.3` → 版本号 `1.3`; 与 report 的 `dep=1.3` 一致; 退出码 0 | `04-ac002-report.txt` | 2026-10-19T15:48:43Z @ 65b43e1 | 通过 |
| AC-003-1 | 未验证 | 先记录 18290 无监听 (`ss` 计数 0, `/dev/tcp` 连接被拒绝), 再实跑 `python3 app.py sync --port 18201 --relay-port 18290` | 输出 `request failed: HTTP Error 503: Service Unavailable`, 退出码 1; 无 `sync-ok instance=board`, 无 `relay=ok`; 实例侧 HTTP 响应为 `503` + `relay-unreachable: <urlopen error [Errno 111] Connection refused>`. 缺部署方 relay 服务 (127.0.0.1:18290), 本仓库不提供也不能代起替身 | `06-ac003-sync.txt`, `05-br001-before.txt` | 2026-10-19T15:48:48Z..15:48:55Z @ 65b43e1 | 未验证 |
| BR-001 | 当前观察 | 记录 18290 监听状态 (无监听), 在失败的 sync 之前与之后各取一次 status/report 的 version 值并比对 | relay 不可用期间: sync 前 status `version=relay-v2`, report `version=relay-v2 dep=1.3`; sync 失败后复取完全相同 (`version=relay-v2`, `dep=1.3`), 未改变; 18290 全程无监听 (`ss` 计数 0) | `05-br001-before.txt`, `07-br001-after.txt`, `06-ac003-sync.txt` | 2026-10-19T15:48:48Z..15:48:59Z @ 65b43e1 | 通过 |

## 本轮环境与清理

- 环境: Linux Ubuntu-Workstation 7.0.0-31-generic x86_64; 该 shell 里 `python3` 是包装函数 `uv run python` (`type python3` 原文见 `08-environment.txt`).
- 实例: `board` 于 127.0.0.1:18201, pid 30789, 按 README 命令起 (`01-serve-start.txt`), server stdout 保留在 `server.stdout.log`.
- relay: 127.0.0.1:18290 本轮全程无监听 (`05-br001-before.txt` 第 1/2 项, `07-br001-after.txt` 第 1 项). 未起任何桩/替身/端口转发.
- 清理: `kill 30789` (kill_exit=0) → `pgrep -af 'app.py serve'` 无匹配, `ss -ltn | grep :18201` 无匹配, `health` 复核返回 `Connection refused` 且 exit=1 (`09-cleanup.txt`).
- 工作树: 结束时 `git status --porcelain` 仅 `?? docs/changes/board/evidence/board-verify-65b43e1/`, `git diff --stat` 为空; 未改产品文件, 未提交未推送 (`09-cleanup.txt`).
- 副作用: 创建了 gitignored 的 `runtime/board/` (README 指定数据目录) 与 `vendor/__pycache__/` (import relaylib 产生), 两者均在 `.gitignore` 内, 不属已跟踪改动.
- 旧证据目录 `board-dep-1.2-run/` 未改动 (mtime 仍为 2026-10-19T23:41:43 +0800).

## 局限

1. AC-003-1 只做到"实际尝试并记录真实现象": 判据的假定 (部署方 relay 在 18290 监听) 不成立, 因此无法观察到 `sync-ok instance=board` 与 `relay=ok`。该条记未验证, 缺的是部署方提供的 relay 服务本身, 不是仓库内任何东西。
2. AC-003-1 的失败输出形态 (`request failed: HTTP Error 503`) 只说明 relay 不可达这一当前条件, 不构成对 relay 可用时行为的判断。
3. BR-001 只在"relay 不可用"这一支上做了实观察 (恰是规则点名的分支): version 值在失败 sync 前后一致且取自实例自身 (`relay-v2`)。relay 可用时的对照支本轮无法观察, 未使用代码阅读顶替。
4. 判据要求的三条命令均按原文以 `python3 app.py ...` 执行; 本机该名字被 shell 函数包装成 `uv run python`, 因此实际解释器由 uv 提供 (CLI 自报 3.14.7, serve 进程 HTTP 头自报 Python/3.14.4)。此差异属环境, 未影响任何判据字面。
5. 项目无自动化测试 (README 明示), 本轮结论全部来自上述单命令实跑, 无重复抽样; AC-001/AC-002/BR-001 各只跑一次主判据命令 (BR-001 取值为两组时刻各一次, AC-002 比对时额外取了两次相同命令)。
6. 端口 18201 在起实例前为空 (00-preconditions.txt 的 ss 全量输出中无 18201), 故本轮实例是本会话唯一实例; 不排除环境里其他与本判据无关的端口占用。
