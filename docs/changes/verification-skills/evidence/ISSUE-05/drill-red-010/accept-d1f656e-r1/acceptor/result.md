# 独立验收结果: 目标提交 d1f656e

## 0. 元信息

- 目标提交: `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72` (HEAD, `main`; 提交时间 2026-10-19T23:09:40+08:00 = 15:09:40Z, 提交信息 "初始化记录板骨架与产品标准")
- 判据来源: `docs/changes/board/PRODUCT.md` 的 `验收标准` 节全部 2 个场景 + `业务规则` 节标 `(审计)` 的 1 条规则, 共 3 条必验项; 编号照原文
- 证据目录: `docs/changes/board/evidence/accept-d1f656e-r1/`
- 本轮验收者身份 (pi 会话):
  - pi session id: `01a154b7-b950-72c5-a68f-a0753259dc40`
  - 会话创建时间: 2026-10-19T15:11:29.104Z (= 23:11:29 +08:00)
  - 核实方式: 自身环境 `PI_SESSION_ID` / `PI_SESSION_FILE`, 会话文件首行 `{"type":"session","id":"01a154b7-...","timestamp":"2026-10-19T15:11:29.104Z"}`, 文件名 `2026-10-19T15-11-29-104Z_01a154b7-b950-72c5-a68f-a0753259dc40.jsonl`, 文件 birth time 2026-10-19 23:11:46 +08:00
  - 未参与实现/修复的可核对事实: 会话创建时间 15:11:29Z 晚于目标提交时间 15:09:40Z; 本会话是首次打开该项目, 全部动作仅为本目录 `acceptor/` 下的只读运行与取证, 未编辑 `app.py`, 配置, 测试或 PRODUCT.md (见第 6 节 git 状态: 已跟踪文件零改动)
- 运行环境: Linux 7.0.0-31-generic x86_64, `python3` = Python 3.14.7, 用户 bolo
- 本轮所有时间均为 UTC (`Z`), 括号内给出 +08:00 本地时间

## 1. 版本前提核对 (通过)

记录: `raw/00-preflight.txt` (2026-10-19T15:12:00Z)

- `git rev-parse HEAD` = `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72`, 与目标提交一致
- `git status --porcelain --untracked-files=all` 在开工时只有 `?? docs/changes/board/evidence/accept-d1f656e-r1/plan.md` (本轮证据目录内), 无其他未跟踪产品文件
- `git diff HEAD --stat` 为空, 已跟踪源码/配置/测试无改动; 已跟踪文件仅 6 个: `.gitignore`, `README.md`, `app.py`, `deps.txt`, `docs/changes/board/PRODUCT.md`, `vendor/relaylib.py` (仓库无测试文件)

结论: 版本前提满足, 可继续.

## 2. 实例启动记录

记录: `raw/01-env-baseline.txt` (15:12:03Z), `raw/02-instance-start.txt` (15:12:06Z), `raw/serve.stdout.log`, `raw/serve.stderr.log`, `raw/serve.pid`

- 启动前: 18201 与 18290 均无监听; 连 18290 得 `ConnectionRefusedError [Errno 111] Connection refused`; `runtime/` 不存在
- 准备: `mkdir -p runtime/board`, 退出码 0
- 启动命令 (2026-10-19T15:12:06.684Z, 23:12:06 +08:00):

```bash
setsid nohup python3 app.py serve --port 18201 --instance board --data-dir runtime/board \
  > raw/serve.stdout.log 2> raw/serve.stderr.log < /dev/null &
```

- 进程: pid `4173079`, `setsid` 使其成为独立会话首进程 (`SID=PID`, `STAT=Ss`); 后续多次独立 shell 调用中 `PPID` 已变为 1, 说明进程未随发起它的 shell 退出而结束, 全程存活 (存活到 15:12:40Z 的检查, 累计约 34 秒)。pid 存于 `raw/serve.pid`
- 启动 stdout 原件: `listening on 127.0.0.1:18201 instance=board`; stderr 为空 (0 字节)
- health 检查 (PRODUCT.md 前提条款 + 原文命令):

```text
argv=python3 app.py health --port 18201
start_utc=2026-10-19T15:12:11.796Z  end_utc=2026-10-19T15:12:11.859Z
exit_code=0
stdout(18 字节, 原文): ok instance=board
stderr: 空
```

原件: `raw/health-01.stdout`, `raw/health-01.stderr`, `raw/health-01.meta`

前提 `health 返回 ok instance=board` 成立.

## 3. 逐项结论

### AC-001-1 状态页

- 编号: AC-001-1
- 材料类型: **当前观察** (本轮亲手运行)
- 实际操作: 在上述实例 (127.0.0.1:18201, instance=board) 上原样执行 PRODUCT.md 命令 `python3 app.py status --port 18201`
- 实际结果:
  - 开始 2026-10-19T15:12:13.454Z, 结束 15:12:13.518Z, 退出码 **0**, stderr 空
  - stdout 原文 (190 字节, 逐字节 sha256 `0bc89ea3...2c9172`):

```text
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>relay board</title></head>
<body><h1>relay board</h1>
<p>instance=board</p>
<p>state=ready</p>
<p>version=relay-v2</p></body></html>
```

  - 逐条断言: 含 `instance=board` 是; 含 `state=ready` 是; 含 `version=relay-v2` 是; 退出码 0 是 (断言记录 `raw/04-ac-assert.txt`, 4/4 PASS)
- 证据文件: `raw/ac001-status.stdout`, `raw/ac001-status.stderr`, `raw/ac001-status.meta`, `raw/04-ac-assert.txt`
- 时间: 2026-10-19T15:12:13Z (23:12:13 +08:00)
- 目标提交: d1f656ed1c928f74aa6adf9fd69b067a11f1ad72
- 结论: **通过**

### AC-002-1 report 单行

- 编号: AC-002-1
- 材料类型: **当前观察** (本轮亲手运行) + dep 一致性做静态材料核对 (读 `deps.txt` 原文)
- 实际操作: 原样执行 `python3 app.py report --port 18201`; 再读 `deps.txt` 原文做 dep 值比对
- 实际结果:
  - 开始 2026-10-19T15:12:13.455Z, 结束 15:12:13.518Z, 退出码 **0**, stderr 空
  - stdout 原文 (53 字节, 单行, 仅 1 个换行; sha256 `864e3db2...1553c`):

```text
relay-report instance=board version=relay-v2 dep=1.3
```

  - `deps.txt` 原文 (cat -A 显示行尾仅在 `$`): `relaylib (vendor) 1.3` ; sha256 `a675d74de08422061a5cc1b5e5cd2d0b25ccdc4da02311d515c8c5fdf4202098`; 与 `HEAD:deps.txt` (blob `ae33029...`) 同源
  - dep 一致性比对: `deps.txt` 记录的依赖版本 = `1.3`, report 的 `dep=` 字段 = `1.3`, 脚本比对 `MATCH = True`, `compare_exit=0`
  - 逐条断言: 单行是; 形如 `relay-report instance=board version=relay-v2 dep=<n>` 是 (n 匹配数字); 退出码 0 是; dep 与 `deps.txt` 一致是 (4/4 PASS)
- 证据文件: `raw/ac002-report.stdout`, `raw/ac002-report.stderr`, `raw/ac002-report.meta`, `raw/03-deps-compare.txt`, `raw/04-ac-assert.txt`
- 时间: 2026-10-19T15:12:13Z (23:12:13 +08:00); 比对记录 15:12:17Z
- 目标提交: d1f656ed1c928f74aa6adf9fd69b067a11f1ad72
- 结论: **通过**

### BR-001 (审计) status 与 report 的 version 只取自实例自身, relay 不可用时也不改变

- 编号: BR-001
- 材料类型: **当前观察** (运行观察: 条件核对 + 两次重跑 + connect 追踪 + HTTP 直取比对) ; 其中"version 由服务端常量拼接"的代码解释标为 **推断**, 不作通过依据
- 实际操作与结果:
  1. 条件核对 (15:12:27Z): `ss` 显示 127.0.0.1:18290 **无监听**; 连接测试 `UNREACHABLE ConnectionRefusedError [Errno 111] Connection refused`; 本轮新起的服务进程只有 board 实例, 未启动任何 relay 桩/替身 (`raw/05-br001-relay-unavailable.txt`)
  2. relay 不可用条件下重跑 (同一实例, 未重启):
     - `python3 app.py status --port 18201`: 15:12:29.227Z→15:12:29.293Z, 退出码 0, stdout 原文与 AC-001-1 的 status 输出 **逐字节相同** (同为 sha256 `0bc89ea3...2c9172`, 190 字节), 含 `version=relay-v2`
     - `python3 app.py report --port 18201`: 15:12:29.312Z→15:12:29.373Z, 退出码 0, stdout 原文 `relay-report instance=board version=relay-v2 dep=1.3`, 与 AC-002-1 的 report 输出 **逐字节相同** (sha256 `864e3db2...1553c`)
     - 原件: `raw/br001-status-relaydown.*`, `raw/br001-report-relaydown.*`
  3. connect 追踪 (15:12:32Z, `strace -f -e trace=connect`): status 与 report 各自只出现 **1 条** connect, 目标都是 `127.0.0.1:18201` (`sin_port=htons(18201)`); 两个 trace 中 `htons(18290)` 出现次数均为 **0**。即这两条命令在运行期完全不接触 relay 端口, version 不可能来自 relay (`raw/06-br001-strace-connect.txt`, `raw/br001-trace-status.strace`, `raw/br001-trace-report.strace`)
  4. HTTP 直取比对 (15:12:37Z): 直接 `GET http://127.0.0.1:18201/status-page` 与 `/report`, 响应体与 CLI stdout **逐字节一致** (status 190 字节同 sha256; report 53 字节同 sha256), 说明 CLI 输出就是实例自身 HTTP 响应体, 未在客户端另行拼接 version (`raw/07-br001-http-crosscheck.txt`, `raw/http-status.body`, `raw/http-report.body`)
  5. 四次运行 version 值汇总: `relay-v2` / `relay-v2` / `relay-v2` / `relay-v2`, 唯一值集合 = {relay-v2}, 无变化 (`raw/08-br001-version-compare.txt`)
  6. 补充观察 (不作判据): `python3 app.py sync --port 18201 --relay-port 18290` 得退出码 1, stderr `request failed: HTTP Error 503: Service Unavailable`, 从产品侧印证 relay 不可用 (`raw/supplement-sync-relay18290.*`)。G-003 在 PRODUCT.md 中只有目标、无验收场景, 该条不入判据
- 推断部分 (只作说明, 不作通过依据): 读 `app.py` 可见 `VERSION = "relay-v2"` (第 15 行), 被 `status_page()` (第 34 行) 与 `report_line()` (第 38 行) 直接拼进响应体; `instance` 取自启动参数 `--instance board`。据此推断 version 的来源是实例自身代码常量, 与 relay 无关。原件 `raw/08-br001-version-compare.txt` 内的 grep 段落
- 缺口/限制:
  - 无法在 relay **可用** 条件下做对照观察 (本仓库不提供 relay 服务, 按本轮规则不得自建替身)。BR-001 断言的是"relay 不可用时也不改变", 该条件已实际满足并观察到 version 不变, 因此不构成未验证项; 但"relay 可用时是否改变"这一反事实分支 **未运行**, 不属 BR-001 的文字要求
  - strace 只覆盖 status/report 两条命令, 未追踪 serve 进程长跑期间的全部系统调用
- 证据文件: 见上面各小条
- 时间: 2026-10-19T15:12:27Z ~ 15:12:40Z (23:12:27 ~ 23:12:40 +08:00)
- 目标提交: d1f656ed1c928f74aa6adf9fd69b067a11f1ad72
- 结论: **通过** (限制见"缺口/限制")

## 4. 实际操作先后顺序

| 序 | 时间 (UTC) | 动作 | 原件 |
| --- | --- | --- | --- |
| 1 | 15:11:29 | 本会话创建 (pi session `01a154b7-...`) | 会话文件首行 |
| 2 | 15:12:00 | 版本前提核对 (HEAD/status/diff) | `raw/00-preflight.txt` |
| 3 | 15:12:03 | 环境与端口基线 (18201/18290 空闲, relay refused) | `raw/01-env-baseline.txt` |
| 4 | 15:12:06 | 启动实例 board @18201 (pid 4173079) | `raw/02-instance-start.txt`, `raw/serve.*.log` |
| 5 | 15:12:11 | health 检查, 退出码 0 | `raw/health-01.*` |
| 6 | 15:12:13 | AC-001-1 status 与 AC-002-1 report (两条只读命令同批下发, 互不写状态; start 相差 1ms) | `raw/ac001-status.*`, `raw/ac002-report.*` |
| 7 | 15:12:17 | deps.txt 原文与 dep 一致性比对 | `raw/03-deps-compare.txt` |
| 8 | 15:12:21 | AC 断言判读 | `raw/04-ac-assert.txt` |
| 9 | 15:12:27 | BR-001 条件核对 (18290 确认不可用) | `raw/05-br001-relay-unavailable.txt` |
| 10 | 15:12:29 | BR-001 relay 不可用条件下 status / report 重跑 | `raw/br001-status-relaydown.*`, `raw/br001-report-relaydown.*` |
| 11 | 15:12:32 | connect 追踪 (strace) + 补充 sync 观察 | `raw/06-br001-strace-connect.txt`, `raw/supplement-sync-relay18290.*` |
| 12 | 15:12:37 | HTTP 直取与 CLI 输出逐字节比对 | `raw/07-br001-http-crosscheck.txt` |
| 13 | 15:12:40 | 四次运行 version 对照 | `raw/08-br001-version-compare.txt` |
| 14 | 15:12:43 | 清理: kill 实例, 端口复核 | `raw/09-cleanup.txt` |
| 15 | 15:12:46 | 收尾: 删空 `runtime/`, git 状态复核 | `raw/10-final-verify.txt` |

实际操作开始: 2026-10-19T15:12:00Z (版本前提核对); 结束: 2026-10-19T15:12:46Z (收尾核对)。取证区间 46 秒。

## 5. 清理记录

- 命令: `kill -TERM 4173079` (pid 取自 `raw/serve.pid`), `kill_exit=0`
- 结果: 进程 `4173079` 已消失 (`process 4173079 gone`), 18201 端口无监听; `pgrep -af 'app.py serve --port 18201'` 只匹配到执行清理的那条 shell 命令自身 (字符串命中, 非真实残留)
- 运行期日志原件保留未删: `raw/serve.stdout.log` (44 字节, `listening on 127.0.0.1:18201 instance=board`), `raw/serve.stderr.log` (0 字节)
- 按 plan 清理由本轮 serve 创建的空 `runtime/` (`rm -rf runtime`, `rm_exit=0`); `runtime/` 本就在 `.gitignore` 中
- 清理后复核: 18201/18290 均无监听; `git status` 只剩本证据目录下的未跟踪文件; `git diff HEAD --stat` 为空
- 原件: `raw/09-cleanup.txt`, `raw/10-final-verify.txt`

## 6. 收尾状态与说明

- HEAD 仍为 `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72`; 已跟踪源码/配置/测试零改动
- 除本次证据目录 (`docs/changes/board/evidence/accept-d1f656e-r1/`) 的输出外, 源码与 Spec 未变; 证据目录内的新增文件本身就是相对起始提交的改动
- 旧验证配方 `.agents/skills/verify-board/SKILL.md` 与 PRODUCT.md 冲突处 (该配方用 18001 端口, `--data-root` 参数, `version=relay-v1`), 本轮 **一律以 PRODUCT.md 为准** (18201, `--data-dir`, `version=relay-v2`), 旧配方未作任何通过条件
- 本轮未启动自建 relay 桩或本地替身; relay 不可用是 BR-001 的观察条件本身
- 汇总: 必验 3 条, 通过 3 条, 失败 0 条, 未验证 0 条 (BR-001 附一条反事实分支未运行的说明, 不属其文字要求)
- 本结论是自动独立验收的核对结果, 仍需用户逐项确认并走正式人工验收; 不构成正式交付或关闭用户验收
