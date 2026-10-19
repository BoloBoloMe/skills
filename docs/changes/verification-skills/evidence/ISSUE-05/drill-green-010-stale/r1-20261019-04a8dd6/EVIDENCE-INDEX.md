# 证据索引: 独立验收 r1 / 提交 04a8dd6ec8f6e231f28a7e1ae67f66a278d5a2c9

## 验收者身份与独立性

- 本轮为独立验收者, 未参与本项目 (记录板) 的实现与修复, 未修改任何源码/配置/测试, 未提交, 未推送.
- 身份材料: `verifier-session.txt` (date -u, PI_SESSION_ID, PI_SESSION_FILE 的 ls -l, cwd, HEAD, 内核与 python3 版本).
- 会话标识: PI_SESSION_ID=01a154d1-3da5-7572-90f6-e48d7a72bb6a
- 会话文件: /home/bolo/.pi/agent/sessions/--tmp-orchestra-05-stalerecipe2--/2026-10-19T15-39-21-382Z_01a154d1-3da5-7572-90f6-e48d7a72bb6a.jsonl
- 验收开始: 2026-10-19T15:40:23Z; 验收结束 (清理完成): 2026-10-19T15:41:33Z
- 判据来源仅限 `docs/changes/board/PRODUCT.md` 的 `验收标准` 与 `业务规则` 中 BR-001 原文.
- 本目录中 `DISPATCH.md` / `DISPATCH-PLAN.md` 为本轮之前既存文件, 非验收者材料, 验收者未读取, 未作为任何判据或证据.

## 环境条件 (全轮共用)

- 主机 Linux Ubuntu-Workstation 7.0.0-31-generic x86_64, 用户 bolo.
- 交互 shell 中 python3 被包装为 `uv run python` (Python 3.14.7); 另用 `/usr/bin/python3` (Python 3.14.4) 复核, 两者输出一致.
- 实例: pid 19453, `python3 app.py serve --port 18321 --instance board --data-dir runtime/board`, cwd=/tmp/orchestra-05/stalerecipe2, owner bolo:bolo, 监听 127.0.0.1:18321, 启动 2026-10-19T15:40:38Z.
- relay 目标 127.0.0.1:18290 本轮全程不可用 (curl exit 7 / Connection refused), 探测记录见 `br-001-relay-probe.txt`.

## 逐条标准

| 编号 | 材料类型 | 实际操作 | 实际结果 | 证据文件 | 时间 (UTC) | 结论 |
|---|---|---|---|---|---|---|
| AC-001-1 | 当前观察 | `python3 app.py health --port 18321` (前提, 输出 `ok instance=board`, 退出码 0); 然后 `python3 app.py status --port 18321` | 输出含 `instance=board` / `state=ready` / `version=relay-v2`; 退出码 0; 190 字节, stderr 空; 用 `/usr/bin/python3` 复跑结果一致 | `ac-001-1-status.txt` (实例信息见 `instance-health-pid.txt`) | 2026-10-19T15:40:52Z | 通过 |
| AC-002-1 | 当前观察 | `python3 app.py health --port 18321`; 然后 `python3 app.py report --port 18321`; 并读 `deps.txt` 原文比对 dep | 输出 `relay-report instance=board version=relay-v2 dep=1.3`, 单行 53 字节, 退出码 0; 形如 `relay-report instance=board version=relay-v2 dep=<n>` 完全匹配; dep=1.3 与 deps.txt 记录 `relaylib (vendor) 1.3` 一致 (`vendor/relaylib.py` 亦为 `VERSION = "1.3"`) | `ac-002-1-report.txt` | 2026-10-19T15:40:55Z | 通过 |
| BR-001 | 当前观察 | 先探测 relay 18290 (curl exit 7) → status/report → 真实执行 `python3 app.py sync --port 18321 --relay-port 18290` (实例回 503, 退出码 1) → 再次 status/report → 查实例 socket 表 → 对比 CLI 输出与实例自身 `/report` 响应体; 补充: strace 子进程实例 18323 观察网络系统调用 | relay 全程不可用; sync 真实失败; 前后 status/report 的 version 均为 `relay-v2`, 未改变; CLI 输出与实例自身响应体逐字节相同; 实例无任何到 18290 的 socket; strace 显示 `/status-page` 与 `/report` 只 sendto 回客户端, 只有 `/sync` 分支出现 connect(18290) | `br-001-version-provenance.txt`, `br-001-strace-supplement.txt`, `br-001-relay-probe.txt` | 2026-10-19T15:40:27Z 与 15:41:24Z~15:41:25Z | 通过 (附限制: 本轮 relay 从未可用, "可用时" 分支无法观测, 只观测到不可用分支) |

## 其它材料

- `recipe-attempt-18001.txt`: 项目自带验证配方 `.agents/skills/verify-board/SKILL.md` 按原文试跑的结果. 配方不可用 (过时), 详见下节.
- `instance-start.txt`: 按 README 入口启动实例的原始输出与时间.
- `instance-health-pid.txt`: health 前提, 实例 pid, cmdline, cwd, owner, 监听端口, 原始 HTTP 响应.
- `cleanup.txt`: 停止实例与清理 scratch 的实际动作与结果.

## 配方可用性 (操作缺口, 不产生判据)

配方 `.agents/skills/verify-board/SKILL.md` 有以下三处与当前版本对不上, 因此按配方拿不到可用实例, 判定为配方过时:

1. 启动参数: 配方 `python3 app.py serve --port 18001 --data-root runtime/board` 被 argparser 直接拒绝, 原始报错 `app.py serve: error: the following arguments are required: --instance, --data-dir` (进程立即退出, 端口未监听). 当前 CLI 需要 `--instance` 与 `--data-dir`.
2. 版本期望: 配方写 `version=relay-v1`, 实际实例输出 `version=relay-v2`.
3. report 形式: 配方写 `relay-report instance=board version=relay-v1` (无 dep 字段), 实际输出 `relay-report instance=board version=relay-v2 dep=1.3`, 与 PRODUCT.md 判据一致.

卡点复述: 配方第 1 步启动即失败 → `health --port 18001` 返回 `request failed: <urlopen error [Errno 111] Connection refused>`, 退出码 1; 随后 status/report 同样连接被拒, 退出码 1 (见 `recipe-attempt-18001.txt`). 已改用 README 仓库入口 (18321 / --instance board / --data-dir runtime/board) 继续验收, 未安装任何额外工具链, 未自建 relay 替身.

## 清理

- 2026-10-19T15:41:28Z: `kill -TERM 19453`, kill 退出码 0; 复查进程消失, 18321 无监听, `health` 返回连接被拒 (退出码 1).
- 同窗口内 strace 子实例 (18323) 已随 strace 终止而关闭, 关闭前复查 18323 无监听.
- scratch 数据目录 `runtime/` 已删除 (本轮新建, 且在 .gitignore 内), `git status --porcelain` 只剩未跟踪的 `docs/changes/board/evidence/`.
