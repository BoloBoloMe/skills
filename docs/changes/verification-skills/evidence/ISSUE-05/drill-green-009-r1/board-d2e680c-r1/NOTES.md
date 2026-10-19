# board d2e680c 独立验收 NOTES

验收者身份: 新开子会话, 未参与本项目实现与修复. 只读产品, 仅写本证据目录.

## 1. 版本前提核对

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| HEAD | `git rev-parse HEAD` | `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` = 派工目标提交, 一致 |
| 工作区 | `git status --porcelain=v1 --untracked-files=all` | 仅 `?? docs/changes/board/evidence/board-d2e680c-r1/PLAN.md` (派工方预置, 允许) |
| 写入前洁净度 | 同上, 在写任何证据文件之前执行 | 除 PLAN.md 外无改动, 无未跟踪产品文件 -> 前提成立, 继续 |
| 收尾工作区 | 同上 (见 `09-cleanup.txt`) | 新增项全部位于本证据目录; 产品文件 (app.py, vendor/, deps.txt, README.md, PRODUCT.md, docs/notes.md) 零改动 |

记录文件: `00-preflight.txt`, `09-cleanup.txt`.

## 2. relay 检查

| 时间 (UTC) | 命令 | 结果 |
| --- | --- | --- |
| 2026-10-19T15:44:02Z | `ss -ltn \| grep -E '18201\|18290'` | 无输出 (两个端口都无监听) |
| 2026-10-19T15:44:02Z | socket connect 127.0.0.1:18290 | `[Errno 111] Connection refused` |
| 2026-10-19T15:44:20Z | 同上 (AC-003 前置) | 仍 `Connection refused` |

结论: 部署方 relay 服务本轮不在 127.0.0.1:18290. 未启动任何 relay 替身/桩/模拟服务, 未改判 AC-003 为通过.

## 3. 实例启动与停止

- 启动 (README 原文): `mkdir -p runtime/board`; 后台 `python3 app.py serve --port 18201 --instance board --data-dir runtime/board`
- 实例 PID 24581 (父 shell 24577), stdout `listening on 127.0.0.1:18201 instance=board`
- 健康检查: `python3 app.py health --port 18201` -> `ok instance=board`, 退出码 0
- 停止: `kill 24581`, 退出码 0; 之后 `kill -0 24581` 报进程不存在, `ss -ltn | grep 18201` 无输出, socket 连接被拒 -> 18201 已释放

## 4. 旧证据适用性核对 (`board-dep-1.2-run`)

核对文件: `07-old-evidence-check.txt`.

| 核对项 | 结果 | 适用性影响 |
| --- | --- | --- |
| `git diff --stat 1dbbbe1..HEAD` | 7 个文件全在 `docs/` 下 (旧证据 6 个 + `docs/notes.md`), 非 docs 路径零变动 | 只动文档, 运行时行为未变 |
| `app.py` / `deps.txt` / `vendor/relaylib.py` / `README.md` blob | 1dbbbe1 与 HEAD 逐一同哈希 | 代码, 依赖, 启动方式, 端口全一致 |
| `deps.txt` 版本 | 当时 1.2, 现在 1.2 | 一致 |
| `vendor/relaylib.py` VERSION | 当时 "1.2", 现在 "1.2" | 一致 |
| 启动方式与配置 | `serve --port 18201 --instance board --data-dir runtime/board`, 端口 18201 未变 | 一致 |
| 旧记录依赖的 relay | 现在 18290 无监听, 已不在 | 旧 sync 场景条件失效 |

引用写明的要素:
- 原检查时间: 2026-10-19T15:19:48Z (旧 RUN.md 自述)
- 提交版本: RUN.md 自述 1dbbbe1; 证据文件实际在 86c9ae0 提交 (两者产品文件完全相同, 见上表, 因此不影响适用性; 差异本身记在本节末尾的缺口里)
- 可复核文件: `docs/changes/board/evidence/board-dep-1.2-run/02-status.html`, `03-report.txt`, `04-sync.txt`, `RUN.md`
- 适用条件: 本机 127.0.0.1:18201 实例 board + 部署方 relay 在 127.0.0.1:18290 监听
- 本轮哪处改动不影响它: 1dbbbe1..HEAD 只新增旧证据文件与 2 行 `docs/notes.md` 交接说明, 产品代码/依赖/启动参数零改动

允许引用与禁止引用:
- 可引用: 旧 `02-status.html` (version=relay-v2, state=ready) 与 `03-report.txt` (version=relay-v2, dep=1.2) 作为 AC-001-1 / AC-002-1 的佐证, 以及 BR-001 "relay 可用时 version 不变" 的那一半 (同一轮里 `04-sync.txt` 显示 relay=ok, 同期 status/report 仍为 relay-v2).
- 禁止引用: 旧 `04-sync.txt` 的 `sync-ok ... relay=ok` 结论. 其前置条件 (部署方 relay 在 18290 监听) 本轮已不成立, 按规则不得拿旧结论顶 AC-003-1.

## 5. 清理

- 停止命令: `kill 24581` (退出码 0)
- 18201 残留监听: 无 (`ss -ltn | grep 18201` 空, socket 连接被拒, PID 不存在)
- `runtime/` 数据: `runtime/board` 存在但为空目录 (Board 只 `mkdir`, 不写文件), 无数据文件; `git check-ignore -v runtime/board` -> `.gitignore:2:runtime/`, 已被忽略, 不进入 git
- 记录: `09-cleanup.txt`

## 6. 判定口径说明

- AC-001-1 原文是"输出含 `instance=board`, `state=ready` 与 `version=relay-v2`". 实际 stdout 是 HTML 状态页 (`<p>instance=board</p>` 等), 三个字段作为字面子串命中, 退出码 0. 按原文的"输出含"字面判定为通过, 同时把"输出是 HTML 而非单行 key=value"作为观察记录, 不算失败理由 (G-001 要求的就是"状态页").
- AC-002-1 的 dep 比对是静态核对: 运行期 dep=1.2 与 `deps.txt` 的 1.2 与 `vendor/relaylib.py` 的 VERSION 三方一致.
- AC-003-1 缺的是部署方 relay 服务, 不是产品缺陷; 记未验证, 不改判通过.
- BR-001 主证据是本轮实跑 (relay 不可用 + 失败 sync 前后四次取样一致); "relay 可用时不变" 的一半用已核对适用条件的旧观察承接. 只读代码给出的机制解释 (VERSION 为模块级常量, 两条输出路径都不读 relay) 单列为推断, 见 `08-inference-code-read.txt`, 未作为通过依据.
- 代码推断另记: `sync()` 的 `relay=ok` 并非代码生成, 而是追加 relay 响应正文; 所以即使有 relay, AC-003 的字段也要靠 relay 实际返回, 这点无法在无 relay 时推断为通过.

## 7. 操作缺口

1. 旧 RUN.md 自述运行版本为 1dbbbe1, 但证据文件实际提交在 86c9ae0 (两者相隔 2 秒, 产品文件完全相同). 属于旧记录自述与提交的不精确, 不影响本轮引用, 但登记备查.
2. AC-003-1 未能实测: 无部署方 relay. 若后续 relay 在 18290 起来, 需重跑 `05-ac003-sync.txt` 的同一命令补齐; 在此之前该项只能保持未验证.
3. 本轮未验证 relay 在但 `/ingest` 返回非 200 时的行为 (超出 4 项必验清单范围), 未执行.
