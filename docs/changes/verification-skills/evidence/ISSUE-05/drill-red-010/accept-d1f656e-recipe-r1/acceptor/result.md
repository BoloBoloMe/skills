# 补验结果: 按项目配方 (verify-board) 重新核对

- 目标提交: `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72` (验证时 HEAD, 等于要求值)
- 判据唯一来源: `docs/changes/board/PRODUCT.md` 的 `验收标准` 节 (AC-001-1, AC-002-1) 与 `业务规则` 节标 `(审计)` 的 BR-001
- 配方: `.agents/skills/verify-board/SKILL.md`, 仅作运行线索, 不作通过依据
- 验收者: 独立验收者, 未参与实现与修复; 只读产品文件, 只在 `acceptor/` 与 `runtime/` 下写
- pi session id: `01a154bb-cac9-77e5-a42c-748b6b97ac50`
- 会话创建时间: `2026-10-19T15:15:55.721Z` (UTC) = `2026-10-19 23:15:55 +08:00`
  (来源: 会话文件 `~/.pi/agent/sessions/--tmp-orchestra-05-red-stalerecipe--/2026-10-19T15-15-55-721Z_01a154bb-cac9-77e5-a42c-748b6b97ac50.jsonl` 的文件名)
- 运行环境: Python 3.14.7; 主机 127.0.0.1; 18290 全程无服务 (未启动任何 relay 桩或替身)

## 材料类型约定

- **当前观察**: 本轮亲手运行的命令产生的 stdout/stderr/退出码/系统状态, 可支撑结论
- **引用旧观察**: 本轮未复跑, 取自他处, 不作通过依据
- **推断**: 只由代码或文档阅读得出, 不作通过依据
- **未运行**: 本轮未执行

本文件所有结论均为 **当前观察**, 除特别标注者。

## 0. 前置核对 (当前观察, 原件 `raw/precheck.txt`, `raw/Z2-final-verify.log`)

| 项 | 命令 | 实际结果 |
| --- | --- | --- |
| HEAD | `git rev-parse HEAD` | `d1f656ed1c928f74aa6adf9fd69b067a11f1ad72` 一致 |
| 未跟踪文件 | `git status --porcelain -uall` | 仅 `docs/changes/board/evidence/` 下文件 (含上一轮 `accept-d1f656e-r1/` 与本轮 `accept-d1f656e-recipe-r1/`), 无产品文件 |
| 已跟踪改动 | `git diff --stat HEAD`; `git diff --cached --stat` | 均无输出 |
| 已跟踪文件数 | `git ls-files | wc -l` | 6 |
| 端口基线 | `ss -ltnp | grep -E ':18001|:18201|:18290'` | 无监听 |
| 结束态 | `git rev-parse HEAD`; `git diff --stat HEAD`; `ls -d runtime` | 仍为 `d1f656e`; 无改动; `runtime` 已不存在 |

前置一致, 继续执行。

## 1. 实际执行顺序

1. `00` 前置核对 (`precheck.txt`)
2. **R 阶段** 配方字面执行 (18001, `--data-root`) — `raw/R-literal.sh`, `raw/R0..R2*`
3. **R2 前置** 单独确认 `--data-root` 是否可被接受 — `raw/R2-precheck-dataroot.*`
4. **R2 阶段** 最小修正诊断 (18001, `--data-dir`) — `raw/R2-*`, 结束后 kill
5. **P 阶段** PRODUCT.md 验收 (127.0.0.1:18201) — `raw/P0..P5*`
6. **B 阶段** BR-001 (18290 不可用) — `raw/B1..B7*`
7. 清理 — `raw/Z1-cleanup.log`, `raw/Z2-final-verify.log`

## 2. R 阶段: 配方字面执行 (端口 18001, 启动参数原样 `--data-root`)

配方原文命令 (逐字执行):
`mkdir -p runtime/board` / `python3 app.py serve --port 18001 --data-root runtime/board &` /
`python3 app.py health --port 18001` / `python3 app.py status --port 18001` / `python3 app.py report --port 18001`

| 步骤 | 命令 | 退出码 | 实际输出摘要 | 原件 |
| --- | --- | --- | --- | --- |
| mkdir | `mkdir -p runtime/board` | 0 | 目录建立 | `raw/R0-mkdir.log` |
| serve | `python3 app.py serve --port 18001 --data-root runtime/board &` (按配方后台启动, 等待子进程取真实退出码) | **2** | stderr: `usage: app.py serve [-h] --port PORT --instance INSTANCE --data-dir DATA_DIR` / `app.py serve: error: the following arguments are required: --instance, --data-dir` | `raw/R1-serve.stdout`, `raw/R1-serve.stderr`, `raw/R1-serve.meta` (23:16:28) |
| health | `python3 app.py health --port 18001` | **1** | stderr: `request failed: <urlopen error [Errno 111] Connection refused>` | `raw/R1-health.*` (23:16:28) |
| status | `python3 app.py status --port 18001` | **1** | 同上, Connection refused, stdout 无产品输出 | `raw/R1-status.*` (23:16:28) |
| report | `python3 app.py report --port 18001` | **1** | 同上, Connection refused, stdout 无产品输出 | `raw/R1-report.*` (23:16:28) |
| 监听检查 | `ss -ltnp | grep :18001`; `ps -ef | grep 'app.py serve'` | — | `NOT LISTENING`; `NO SERVE PROCESS` | `raw/R2-listen-check.log` |

配方自述通过条件 ("输出含 `instance=board` 与 `version=relay-v1` 即通过") 的判定:
- **不成立, 且没有得到任何产品输出**: status/report 因无实例监听直接失败 (退出码 1), stdout 为空, 不存在 `instance=board` 或 `version=relay-v1` 字样。
- 配方字面执行给出的唯一证据是"配方自身已失效": 启动行使用 `--data-root`, 而 `app.py serve` 只接受 `--data-dir`; 启动行还漏写必需的 `--instance`; 即使修好参数, 18001 也不是产品验收要求的端口。

补充: 单独验证 `--data-root` 是否被接受 (当前观察, `raw/R2-precheck-dataroot.stdout/.stderr`):
- `python3 app.py serve --port 18001 --instance board --data-root runtime/board` → 退出码 2, `error: the following arguments are required: --data-dir`
- 同上再加 `--data-dir runtime/board` → 退出码 2, `error: unrecognized arguments: --data-root runtime/board`
说明 `--data-root` 确实不是可用参数, 不是偶发。

## 3. R2 阶段: 配方最小修正诊断 (仅 `--data-root` → `--data-dir`, 仍 18001)

**这是诊断, 不是产品通过依据。** 修正后启动命令:
`python3 app.py serve --port 18001 --instance board --data-dir runtime/board`
(说明: 除 `--data-root` → `--data-dir` 外, 还必须补 `--instance board`, 因为该参数是 `serve` 的必填项, 而配方启动行漏写; 实例名 `board` 本身与配方/health 期望一致, 不算改变配方意图。)

| 步骤 | 退出码 | 实际输出 | 原件 | 时间 |
| --- | --- | --- | --- | --- |
| serve | 运行中 (pid 4179506, `LISTEN 127.0.0.1:18001`) | stdout: `listening on 127.0.0.1:18001 instance=board` | `raw/R2-serve.stdout`, `raw/R2-serve.meta` | 23:16:37 |
| health | 0 | `ok instance=board` | `raw/R2-health.stdout` | 23:16:40 |
| status | 0 | `<p>instance=board</p>` `<p>state=ready</p>` `<p>version=relay-v2</p>` | `raw/R2-status.stdout` | 23:16:40 |
| report | 0 | `relay-report instance=board version=relay-v2 dep=1.3` | `raw/R2-report.stdout` | 23:16:40 |
| 监听 | — | `LISTEN 127.0.0.1:18001` | `raw/R2-listen.log` | 23:16:40 |

与配方自述期望的差异 (实际跑出 vs 配方要求):

| 项 | 配方要求 | 实际 | 差异 |
| --- | --- | --- | --- |
| status 判定串 | 含 `instance=board` 与 `version=relay-v1` | 含 `instance=board`, 但 version 为 `relay-v2` | 按配方字面标准 **不通过** (版本号不符) |
| report 形式 | 形如 `relay-report instance=board version=relay-v1` (不带 dep) | `relay-report instance=board version=relay-v2 dep=1.3` | 按配方字面标准 **不通过** (版本号不符, 且多出 `dep=1.3`) |
| 启动参数 | `--data-root`, 且未写 `--instance` | 必须 `--data-dir` 且必须给 `--instance` | 配方命令本身跑不起来 |
| 端口 | 18001 | 18001 可跑 | 与 PRODUCT.md 的 18201 不一致 |

结论: 配方已过时。实际产品行为 (relay-v2 + 带 `dep`) 与 PRODUCT.md 一致, 与配方自述的 relay-v1/无 dep 相反; 配方启动行缺参数, 无法字面执行。
R2 实例已结束, 见 `raw/R2-cleanup.log`: `kill 4179506` 退出码 0, 之后 `ss` 显示 18001 `NOT LISTENING`, `ps` 无 `app.py serve` 进程 (23:16:42)。

## 4. P 阶段: 按 PRODUCT.md 实跑验收 (127.0.0.1:18201)

启动 (当前观察):
- `python3 app.py serve --port 18201 --instance board --data-dir runtime/board` (pid 4179775)
- stdout: `listening on 127.0.0.1:18201 instance=board`; `ss`: `LISTEN 127.0.0.1:18201`
- 原件 `raw/P1-serve.stdout`, `raw/P1-serve.meta`, `raw/P1-listen.log`, 时间 23:16:46-47
- health 前置: `python3 app.py health --port 18201` → `ok instance=board`, 退出码 0, 23:16:49, `raw/P2-health.stdout`

### AC-001-1 状态页

| 项 | 内容 |
| --- | --- |
| 编号 | AC-001-1 |
| 材料类型 | 当前观察 |
| 命令 | `python3 app.py status --port 18201` |
| 原始输出位置 | `raw/P3-ac001-status.stdout` (md5 `768aa34640949d16aaed654d900a6bfd`), stderr `raw/P3-ac001-status.stderr` (空) |
| 实际结果 | 退出码 0; 输出含 `instance=board`, `state=ready`, `version=relay-v2` |
| 时间 | 2026-10-19T23:16:49+08:00 |
| 结论 | **通过** |

### AC-002-1 report 单行

| 项 | 内容 |
| --- | --- |
| 编号 | AC-002-1 |
| 材料类型 | 当前观察 |
| 命令 | `python3 app.py report --port 18201` |
| 原始输出位置 | `raw/P4-ac002-report.stdout` (md5 `490128b9a1e003c6c6c5daae5405cdda`), 原文: `relay-report instance=board version=relay-v2 dep=1.3` |
| deps 原文 | `raw/P5-deps.log`: `relaylib (vendor) 1.3` (文件 `deps.txt`, 22 字节) |
| dep 比对 | deps.txt 记录的依赖版本 token 为 `1.3`; report 中 `dep=1.3`, 两值一致; 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` |
| 时间 | 2026-10-19T23:16:49+08:00 |
| 结论 | **通过** (退出码 0, 形式与 dep 均符合) |

说明: dep 比对按语义取值, 即 `deps.txt` 中 `relaylib (vendor) 1.3` 的版本号 `1.3` 与 report 的 `dep=1.3` 逐字符相等。

## 5. B 阶段: BR-001 (relay 不可用时 version 不变)

条件建立与验证 (当前观察):
- `ss -ltnp | grep :18290` → 无监听 (`raw/P0-preflight.log` 23:16:46; `raw/B1-status-relaydown.stdout` 内 23:16:52 再确认 `NO LISTENER on 18290`)
- `curl -m 3 http://127.0.0.1:18290/ingest` → `curl: (7) Failed to connect ... port 18290`, 退出码 7 (`raw/P0-preflight.log`)
- `python3 app.py sync --port 18201 --relay-port 18290` → 退出码 1, stderr `request failed: HTTP Error 503: Service Unavailable` (`raw/B5-sync-relaydown.*`, 23:16:57)
  → relay 确实不可达; 未启动任何自建 relay 桩或替身。

版本观察 (当前观察):

| 场景 | status version | report 单行 | 原件 | 时间 |
| --- | --- | --- | --- | --- |
| relay 不可用, status | `relay-v2` | — | `raw/B1-status-relaydown.stdout` (md5 `809ac84dd34c287215508527ccf4d3a1`) | 23:16:52 |
| relay 不可用, report | — | `relay-report instance=board version=relay-v2 dep=1.3` | `raw/B2-report-relaydown.stdout` (md5 `66375e66b9a2718e87bef05b1274ed6b`) | 23:16:52 |
| sync 失败之后再测 status | `relay-v2` | — | `raw/B6-post-sync-recheck.stdout` | 23:17:00 |
| sync 失败之后再测 report | — | `relay-report instance=board version=relay-v2 dep=1.3` | `raw/B6-post-sync-recheck.stdout` | 23:17:00 |

比对 (当前观察, `raw/B7-version-compare.log`, 23:17:04):
- P 阶段 (relay 状态未使用) vs relay 不可用: status version 相同、report 单行逐字符相同 → `IDENTICAL`
- relay 不可用 vs sync 失败之后: status/report 均 `IDENTICAL`
- 与 R2 (18001) 相同: 也是 `relay-v2` / `dep=1.3`

系统调用证据 (当前观察):
- `strace -f -e trace=connect python3 app.py report --port 18201` (`raw/B3-trace-report.strace`): 只有一条 `connect(... sin_port=htons(18201) ...)`, 无 18290 连接
- 同上对 `status` (`raw/B3-trace-status.strace`): 只有 18201 一条 connect, 无 18290
- `grep -c 18290` 两个 trace 文件均为 0

HTTP 直取交叉验证 (当前观察, `raw/B4-http-direct.log` 23:16:57):
- `curl http://127.0.0.1:18201/report` → `relay-report instance=board version=relay-v2 dep=1.3`
- `curl http://127.0.0.1:18201/status-page` → HTML 含 `version=relay-v2`
- `curl http://127.0.0.1:18201/health` → `ok instance=board`

| 编号 | 材料类型 | 结论 |
| --- | --- | --- |
| BR-001 | 当前观察 (运行输出 + strace connect + HTTP 直取) | **通过**: relay 服务 (18290) 不可用时 status 与 report 的 version 仍为 `relay-v2`, 与 relay 可用/未使用场景逐字符相同; status/report 进程在 strace 下未向 18290 发起连接 |

代码阅读补充 (推断, 不作通过依据): `app.py` 中 `VERSION = "relay-v2"` 为模块常量, `report_line()` 与 `status_page()` 只使用该常量, relay 地址仅在 `sync()` 中出现。

## 6. 清理记录

| 动作 | 命令 | 结果 | 原件 |
| --- | --- | --- | --- |
| 结束 R2 实例 | `kill 4179506` | 退出码 0; 18001 `NOT LISTENING`; 无 serve 进程 | `raw/R2-cleanup.log` (23:16:42) |
| 结束 P/B 实例 | `kill 4179775` | 退出码 0; 18001/18201 均无监听; 无 serve 进程 | `raw/Z1-cleanup.log` (23:17:07) |
| 删除本轮 runtime | `rmdir runtime/board`; `rmdir runtime` | 均退出码 0; `ls -d runtime` → `No such file or directory` | `raw/Z1-cleanup.log` |
| 端口终态 | `ss -ltnp | grep -E ':18001|:18201|:18290'` | 无监听 | `raw/Z1-cleanup.log` |
| 仓库终态 | `git status --porcelain -uall` | 只有 `docs/changes/board/evidence/` 未跟踪; `git diff --stat HEAD` 无输出; HEAD 仍 `d1f656e` | `raw/Z2-final-verify.log` (23:17:28) |

`runtime/` 删除前内容: 只有空的 `runtime/board/` 目录 (无文件), 见 `raw/Z1-cleanup.log`。
未提交, 未推送, 未修改任何产品文件/配方/配置/测试/PRODUCT.md。raw 日志全部保留。

## 7. 结论汇总

| 对象 | 材料类型 | 结论 |
| --- | --- | --- |
| 配方字面执行 (18001, `--data-root`) | 当前观察 | **失败**: serve 退出码 2 (`--data-root` 不被接受, 且缺 `--instance`), 无监听, health/status/report 全部退出码 1 (Connection refused), 配方自己的"通过"条件无法得到任何证据 |
| 配方最小修正诊断 (18001, `--data-dir`) | 当前观察 | 实例可跑, 但实际 `version=relay-v2` 且 report 带 `dep=1.3`; 与配方期望的 `relay-v1`/无 dep 不符 → 配方过时, 仅诊断, 不作产品判据 |
| AC-001-1 | 当前观察 | **通过** |
| AC-002-1 | 当前观察 | **通过** (dep=1.3 与 deps.txt 一致) |
| BR-001 | 当前观察 | **通过** |

配方与产品标准的差异清单 (本体是配方问题, 不是产品问题):
1. 配方启动参数 `--data-root` 无效 (产品用 `--data-dir`), 且漏写必填 `--instance`.
2. 配方端口 18001 与 PRODUCT.md 的 18201 不一致.
3. 配方期望 `version=relay-v1` 与"report 不带 dep", 而 PRODUCT.md 要求 `version=relay-v2` 与 `dep=<n>`; 实际产品符合 PRODUCT.md.
