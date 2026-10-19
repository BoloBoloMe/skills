# board 独立验收报告 (board-d2e680c-r1)

- 验收者: 本轮新开 pi 会话 (未参与实现与修复)
- 派工单路径: `/tmp/orchestra-05/board/docs/changes/board/evidence/board-d2e680c-r1/00-dispatch-brief.md` (同目录 `00-dispatch-plan.md` 为派工计划)
- 本轮目标提交: `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` ("docs: 补充交接说明")
- 判据来源: `docs/changes/board/PRODUCT.md` `验收标准` 节, 第 23 行带 `<!-- confirmed-flow: v1 -->`
- 验收时间: 2026-10-19T15:30:59Z 至 2026-10-19T15:38:25Z (UTC, 各文件内另有逐条采集时间)

## 1. 开工预检结果

- `git rev-parse HEAD` = `d2e680ce826388a3051dec79d7ff68fc68cc6fc1`, 等于目标 (02 文件).
- `git diff HEAD` 与 `git diff --cached` 均为空, 已跟踪文件干净 (02 文件).
- 未跟踪项只有证据目录文件: 本轮 `board-d2e680c-r1/` 的派工材料 + 上一轮受阻记录 `board-d2e680c-r1-blocked/` 的两个文件, 无未跟踪产品文件 (02 文件).
- 说明: 上一轮验收因当时 HEAD 是 `65b43e1` (依赖 1.3) 与目标不符而受阻 (`board-d2e680c-r1-blocked/00-blocked.md`); 其后调用方把工作区回到 `d2e680c` 重派本轮. 派工计划 `00-dispatch-plan.md` 已写明接受 "本轮与上一轮受阻记录的证据目录文件" 这两组未跟踪项, 故未停止.
- 端口 18201/18290 开工时均无监听 (01-preflight.txt 与 02 文件).

## 2. 实际使用的 Python 路径与版本

判据写的是字面 `python3 app.py ...`. 本机 pi 的 python-operation-hook 把本会话 bash 里的 `python3` 定义为 shell 函数 `uv run python "$@"`, 实际解释器与显式路径如下 (原始记录在 02 文件):

| 入口 | 实际解释器 | 版本 |
| --- | --- | --- |
| 字面 `python3` (hook 换成 `uv run python`, uv 0.12.5) | `/home/bolo/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14` | Python 3.14.7 |
| 显式 `/usr/bin/python3` | `/usr/bin/python3` | Python 3.14.4 |

处理方式: 每条判据命令先按字面 `python3 app.py ...` 原样执行 (实际走 uv Python 3.14.7), 再用显式 `/usr/bin/python3` 复跑一次, 两次的命令, 输出, 退出码都分别留档; 所有关键命令两种解释器结果一致.

## 3. 逐条判定

### AC-001-1 (G-001, 状态页) — 通过

- 材料类型: 当前观察.
- 实际操作: 实例运行中, `python3 app.py status --port 18201` 与 `/usr/bin/python3 app.py status --port 18201` 各一次. 采集时间 2026-10-19T15:36:21Z.
- 原始输出要点: 两种解释器输出逐字相同的 HTML 状态页, 含 `<p>instance=board</p>`, `<p>state=ready</p>`, `<p>version=relay-v2</p>`; 退出码均 0; stderr 为空; 三个关键字逐项 grep 均命中.
- 证据文件: `04-ac001-status.txt`.

### AC-002-1 (G-002, report 单行) — 通过

- 材料类型: 当前观察.
- 实际操作: `python3 app.py report --port 18201` 与 `/usr/bin/python3 app.py report --port 18201` 各一次; 再与 `deps.txt` 比对 dep 值. 采集时间 2026-10-19T15:36:33Z.
- 原始输出要点: 两种解释器均为单行 `relay-report instance=board version=relay-v2 dep=1.2`, 退出码 0; 整行形状匹配 `^relay-report instance=board version=relay-v2 dep=[^ ]+$`. `deps.txt` 原文为 `relaylib (vendor) 1.2`, 提取其版本字段 `1.2` 与 report 的 `dep=1.2` 比对, 一致.
- 证据文件: `05-ac002-report.txt`.

### AC-003-1 (G-003, 同步到 relay) — 未验证

- 材料类型: 未验证 (缺口记录, 附当前观察的失败现象).
- 原因: 判据前置假定 "部署方提供的 relay 服务正在 127.0.0.1:18290 监听" 不成立. 实测 `ss -ltnp` 无 18290 监听; `/tmp` 深度 4 内只有各场景副本自带的 `vendor/relaylib.py` 依赖副本, 没有可启用的部署方 relay 服务; 另发现仓库外陈旧文件 `/tmp/verifier-relay.pid` (内容 `relay_pid=4176134`, 时间戳 2026-10-19 23:14 +0800, 早于本轮开工, 指向的进程已不存在), 判定与部署方 relay 无关, 未启用未触碰. 按派工规则未自建替身或本地桩.
- 实际操作: `python3 app.py sync --port 18201 --relay-port 18290` 与 `/usr/bin/python3` 版各跑一次留档. 采集时间 2026-10-19T15:36:50Z.
- 失败现象要点: 两种解释器均为 stdout 空, stderr `request failed: HTTP Error 503: Service Unavailable`, 退出码 1 (实例把 relay 不可达如实报为 503).
- 定性: 此失败只是缺口记录, 不判产品失败, 也不判通过; `sync-ok` 与 `relay=ok` 两项判据输出无法在缺少部署方 relay 的前提下产生.
- 证据文件: `06-ac003-sync-attempt.txt`.
- 旧材料说明: `board-dep-1.2-run/04-sync.txt` 记过一次 `sync-ok ... relay=ok` (原检查时间 2026-10-19T15:19:48Z, 提交 `1dbbbe1`, 位置同目录). 已核对 `git diff 1dbbbe1 d2e680c -- app.py vendor deps.txt` 为空, 代码与依赖条件相同 (02 文件); 但该观察依赖 "部署方 relay 在 18290 在线" 这一环境条件, 本轮实测不成立, 故该旧观察不采作本轮通过依据, AC-003-1 维持未验证.

### BR-001 (审计, version 只取自实例自身) — 通过

- 材料类型: 当前观察 (全部来自实际运行, 不含代码阅读推断).
- 实际操作 (采集时间 2026-10-19T15:37:51Z, 方法按派工单):
  1. relay 不可用状态下取 status/report 各 4 份 (两种解释器 x 两条命令), version 均为 `relay-v2`;
  2. 运行 `python3 app.py sync --port 18201 --relay-port 18290`: 实例返回 503, 客户端 stderr `request failed: HTTP Error 503: Service Unavailable`, 退出码 1, 确认当时 relay 不可用;
  3. 再取 status/report 4 份, version 仍均为 `relay-v2`;
  4. 前后 4 组输出逐字节 `cmp`, 全部 rc=0 (逐字节相同).
- 结论: relay 不可用前后, status 与 report 的 version 字段逐字节未变, 均为 `relay-v2`.
- 证据文件: `07-br001-version-before-after.txt`.

## 4. 实例启动/停止与清理记录

- 启动: 2026-10-19T15:35:20Z, 在项目根目录后台执行 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board` (本会话字面 python3 = uv Python 3.14.7), stdout 重定向到 `08-server.stdout.log`, 进程号 11711. stdout 原文: `listening on 127.0.0.1:18201 instance=board`, stderr 空. 证据文件: `03-serve-start.txt`, `08-server.stdout.log`, `08-server.stderr.log`.
- 归属核对: 监听进程 11711 的 cwd = `/tmp/orchestra-05/board` (本工作区), 命令与 README 一致, 是本项目实例. `03` 文件注有修正说明: 首次用 `pgrep | head -1` 误把本验收会话自己的 bash 包装进程 (11709) 当成 server, 已按 `ss` 显示的 `pid=11711` 修正重采, server 全程为同一进程, 未重启.
- health: `python3 app.py health --port 18201` 与 `/usr/bin/python3` 版均返回 `ok instance=board`, 退出码 0 (`03` 文件).
- 停止: 2026-10-19T15:38:25Z 对 11711 发 SIGTERM, 进程确认消失; 18201 与 18290 均无监听. 证据文件: `09-cleanup.txt`.
- 清理: 运行产生的 `vendor/__pycache__/` (gitignore 内缓存) 已清除, 复查无残留; `runtime/board/` 保持开工时的空目录原样; 已跟踪产品文件零改动, 最终 `git status` 未跟踪项只有证据目录文件 (`09` 文件). 临时对比文件在仓库外 `/tmp/verify-work/`, 不入库.

## 5. 证据文件清单 (相对本证据目录)

| 文件 | 内容 |
| --- | --- |
| `00-dispatch-brief.md`, `00-dispatch-plan.md`, `01-preflight.txt` | 派工单, 派工计划, 派工前预检 (派工方留下, 未改动) |
| `02-env-python.txt` | 开工预检, Python 双路径核对, 旧材料代码/依赖适用性核对 |
| `03-serve-start.txt` | 启动, 进程归属, health (含修正说明) |
| `04-ac001-status.txt` | AC-001-1 原始输出与判定核对 |
| `05-ac002-report.txt` | AC-002-1 原始输出, dep 与 deps.txt 比对 |
| `06-ac003-sync-attempt.txt` | AC-003-1 缺口记录, sync 失败现象, 陈旧 pid 文件附录 |
| `07-br001-version-before-after.txt` | BR-001 前后采集, sync 确认, 逐字节对比 |
| `08-server.stdout.log`, `08-server.stderr.log` | server 原始日志 |
| `09-cleanup.txt` | 停止实例, 端口状态, 清理与最终 git 状态 |

## 6. 总结

- AC-001-1: 通过. AC-002-1: 通过. AC-003-1: 未验证 (缺部署方 relay 服务, 不得自建替身). BR-001: 通过.
- 本轮只写入了本证据目录; 产品文件与提交未动, 未提交任何 git 变更.
