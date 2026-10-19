# SESSION-NOTES - board 复验 (5f9544d)

- 会话 id (PI_SESSION_ID): `01a154df-fc83-7409-89c8-61a010ad0dc3`
- 角色: 独立验收者. 本会话新开, 未参与该项目的实现与修复, 也未参与上一轮验收.
- 起止: 2026-10-19T15:55Z (首次版本核对) .. 2026-10-19T15:58Z (交付物写完)
- 工作目录: /tmp/orchestra-05/board-r2
- 证据目录 (唯一写入位置): docs/changes/board/evidence/board-verify-5f9544d/

## 独立性事实说明

- 本会话在复验开始前不存在于该项目; 未写过 app.py, vendor/, deps.txt, README.md, PRODUCT.md 等产品文件.
- 上一轮证据 (`board-verify-65b43e1/`) 只作为材料读取, 未写入, 未改动, 未删除; 本轮只新增 `board-verify-5f9544d/` 下的文件.
- 结束时 `git diff --stat` 与 `git diff --cached --stat` 为空, 未提交, 未推送; `git status --porcelain` 只有两个证据目录未跟踪.
- 未参考实现者或上一轮验收者的口头结论; 结论只由本轮实跑输出与源码静态核对得出.

## 操作时间线 (UTC)

| 时间 | 动作 | 产物 |
| --- | --- | --- |
| 约 15:55Z | 读 PRODUCT.md (判据), README.md, deps.txt, app.py, vendor/relaylib.py, PLAN.md, 上一轮证据; 核对 HEAD 与工作树 | 无 |
| 15:56:07Z | 记录前提与环境: HEAD=5f9544d, status 只有证据目录未跟踪, diff 65b43e1..HEAD 只有 PRODUCT.md +6, Python 3.14.7, deps 1.3, 18201/18290/18299 无监听 | `00-preconditions.txt` |
| 15:56:10Z | 确认 18299 无监听: ss 无匹配, /dev/tcp 连接被拒绝; 严格核对无 app.py 进程 | `01-ac004-port-18299-unlistened.txt` |
| 15:56:16Z | AC-004-1 实跑: `python3 app.py report --port 18299`; stdout 空, stderr 含 request failed, exit=1 | `02-ac004-report.txt` 等 |
| 15:56:22Z | 按 README 起 18201 实例 (board), health=ok | `03-serve-start.txt` |
| 15:56:25Z | AC-001-1 实跑 status | `04-ac001-status.txt` 等 |
| 15:56:28Z | AC-002-1 实跑 report, 单行/regex/dep 比对 | `05-ac002-report.txt` 等 |
| 15:56:33Z | BR-001 前半: 18290 无监听, 取 sync 前 version | `06-br001-before.txt` 等 |
| 15:56:37Z | AC-003-1 前提核对 (18290 无监听) + 当前 sync 尝试 (仅补充观察) | `07-ac003-relay-precondition.txt` 等 |
| 15:56:42Z | BR-001 后半: sync 失败后重取 version 并比对 + 静态核对 VERSION 来源 | `08-br001-after.txt` 等 |
| 15:56:44Z | 第一次清理尝试: pkill -f 自匹配到采集 shell, 采集 shell 被杀 (exit 143), 实例未停 | 部分 `09-cleanup.txt` (后被完整版覆盖) |
| 15:56:56Z | 按 PID 精确停止 40311/40316; 端口与进程核对无残留, health 失败, 工作树干净 | `09-cleanup.txt` |
| 15:57Z..15:58Z | 写 RESULT.md 与本文件 | 本目录 |

## 命令与采集方式说明

- 所有判据命令按 PRODUCT.md 原文执行: `python3 app.py status|report|sync --port ...`; stdout/stderr 分别重定向到独立文件, 退出码单独记录.
- 环境事实: 本会话 shell 层把 python3 命令实际执行为 `uv run python ...` (Python 3.14.7, 与 /usr/bin/python3 同版本), 见 `09-cleanup.txt` 进程 argv; 命令文本与判据一致, 输出因此可直接对照判据.
- 判据核对一律用原文逐项检查: AC-001 检查三个字段与 exit=0; AC-002 检查整行 regex, 行数与 dep=deps.txt; AC-004 检查 exit 非 0 与 stderr 含 request failed; BR-001 检查前后 version 值与源码来源.
