# 路线图展示页失效根因分析 (milestone-16)

任务标识: NAV-16
性质: 只分析与实验, 未改任何产品代码; 实验脚本与副本全部在 `/tmp/nav16-exp/`, 实验用一次性端口 (39301/39302/39303 段) 与独立运行时目录, 未触碰现役展示服务 (39300, pid 117626) 与其桥 (8801).

结论先说: 页面打不开的直接原因始终是同一个 -- **socat 桥指向的端口上没有服务在听**. 它有两条触发路径, 2026-10-31 15:15 的事件两条都涉及:

1. **服务被单方面停止 (主因, H2)**: 展示实例是按 uid 全局共享的默认运行时目录 (`/tmp/navigate-web-1001`) 里的无主单例, 任何同 checkout 会话按完成定义跑 `web_server.py stop`, 或人为把占 39271 的守护当外来占用 kill, 都会杀掉它; 桥与浏览器毫不知情, 页面 refused 直到有人重建 (本次断了 30 分钟).
2. **重建端口静默漂移 (放大器, H1)**: `start` 在默认端口 39271 被占时静默回退到随机端口, 唯一事实源 `server.json` 不推送任何通知, 固定桥永久失联; 此时 `status` 仍报 `alive: true`, 直连新端口一切正常, 排查时"服务明明活着"极有迷惑性.

H3 (线程/fd 泄漏), H4 (日志增长), H5 (幽灵实例) 经实测**都不是根因**: 泄漏不成立, 日志与锁文件只是卫生问题.

---

## 1 现象与现场取证 (已查证)

用户报: 每次更新路线图后, 路线图访问页容易打不开. 已知事实 (任务给定): 10-31 15:15 后展示服务 (pid 85094, 端口 39271) 消失, 容器 8801 的 socat 桥仍指 39271; 非 OOM; 运行时文件还在.

本次取到的现场证据:

| # | 证据 | 位置 | 内容 |
| --- | --- | --- | --- |
| P1 | 桥日志 | `/tmp/socat-8801.log` | 770 条 `E connect(5, AF=2 127.0.0.1:39271, 16): Connection refused`, 从 15:15:13 到 15:45:07, 频率约每 2 秒 1 次 (两个浏览器标签在 4 秒轮询) |
| P2 | 旧实例日志 | `/tmp/navigate-web-1001/server.log` (3.5MB) | 共 9 条 `server started on 0.0.0.0:39271`; 关键序列: 05:27:53 pid=85094 起 → 15:15:10.096 最后一笔正常 200 → (无任何 error) → 15:45:10 pid=106316 重建, 仍在 39271 |
| P3 | 现网锁文件 | `/tmp/navigate-roadmap-1001-*.lock` | 581 个 0 字节文件 (10-30: 53 个, 10-31: 527 个) |
| P4 | 现役服务 | `/tmp/navigate-display-1001/navigate-web-1001/` | pid 117626, 端口 39300, 17:03:45 起, 9.5 小时无重启; 8759 次前端轮询 (4 秒间隔), 6 次页面加载, 0 error, 0 次 ping (即无任何巡检/自愈在跑) |
| P5 | 现役服务命令行 | `ps` | `web_server.py __serve__ 39300` -- **直接调隐藏子命令**, 未经 `start` (start 的候选端口只有 39271 + 随机, 根本不含 39300), 说明临时缓解是手工人肉起的服务, 复原步骤没有脚本入口 |
| P6 | 时间线缺口 | P1/P2 交叉 | 85094 死亡窗口 = 15:15:10~15:15:13, 死前最后请求正常, 无 OOM, 无 error 日志; 死后 `/tmp/navigate-web-1001/server.json` 不在 (见 4.2 死因分析); 106316 于 16:59:20 后同样消失且 server.json 同样被清 |
| P7 | 凌晨重启潮 | P2 | 10-31 03:26~04:06 之间 5 次 `server started` (pid 66416/69946/73496/73634/73839/75138), 印证"反复消失-重建"早已发生 |

## 2 门槛清楚的复现步骤 (已实测)

实验环境: 复制 `workflow/navigate/scripts/web_server.py` 到 `/tmp/nav16-exp/copyA/` 与 `/tmp/nav16-exp/copyB/`, 仅改一行 `DEFAULT_PORT = 39301` (一次性端口, 等价复现默认端口语义); 每个实验用独立 `NAVIGATE_WEB_RUNTIME_DIR`. 仓库测试 TC-010 (`test_port_conflict_falls_back`) 已覆盖真实 39271 的漂移分支, 故真实 39271 无需占用复现 (见 7 未核实).

### E1 漂移与固定桥脱钩 (H1, 完整复现用户现象)

```bash
export NAVIGATE_WEB_RUNTIME_DIR=/tmp/nav16-exp/rt-h1
# 1. 实例 A 起在"默认端口" 39301
uv run python copyA/exp_web_server.py start        # -> port 39301, pid 156183
# 2. 固定桥模拟: 39302 -> 39301 (同现网 8801 -> 39271)
socat TCP-LISTEN:39302,fork,reuseaddr TCP:127.0.0.1:39301
curl http://127.0.0.1:39302/                        # -> 200
# 3. A 被 stop (模拟会话收工 stop)
uv run python copyA/exp_web_server.py stop
curl http://127.0.0.1:39302/                        # -> 空回复; socat 日志:
#   E connect(5, AF=2 127.0.0.1:39301, 16): Connection refused   (与 P1 同款)
# 4. 陌生进程占住 39301, 另一会话 (独立 runtime dir) 重建
#    (python: bind 39301 listen) 然后:
NAVIGATE_WEB_RUNTIME_DIR=/tmp/nav16-exp/rt-h1-b uv run python copyA/exp_web_server.py start
#    -> {"port": 62766, ...}  静默漂移到随机端口
uv run python copyA/exp_web_server.py status        # -> alive: true, port 62766
curl http://127.0.0.1:62766/                        # -> 200 (服务完全健康)
curl http://127.0.0.1:39302/                        # -> 失败 (桥仍指 39301)
```

结果: 服务活着 + status 正常 + 直连 200, 但页面 (经桥) 打不开. 与 15:15 事件现象一致; 15:45 能恢复纯属侥幸 (当时 39271 恰好空闲, 重建回同端口).

### E2 服务死后重建 (幽灵文件与自愈边界, H1/H5)

```bash
export NAVIGATE_WEB_RUNTIME_DIR=/tmp/nav16-exp/rt-e2
uv run python copyA/exp_web_server.py start          # -> 39301, pid 156700
kill -9 156700                                       # SIGKILL 模拟崩溃/误杀
cat rt-e2/navigate-web-1001/server.json              # 残留 (SIGKILL 不执行清理, 实证)
uv run python copyA/exp_web_server.py status         # -> alive: false (ping 探活兜底, 不被骗)
uv run python copyA/exp_web_server.py start          # -> 回到 39301, pid 156723 (重建成功)
```

结果: 默认端口空闲时, 死后重建**回同一端口**, 桥不需要动 (端口不变即自愈); 漂移只发生在默认端口被别的进程占用时.

### E3 跨脚本路径 stop 的指纹保护 (H2)

```bash
export NAVIGATE_WEB_RUNTIME_DIR=/tmp/nav16-exp/rt-fp
uv run python copyA/exp_web_server.py start          # pid 156804
uv run python copyB/exp_web_server.py stop
# -> {"success": false, "error": "pid 156804 command line does not contain
#     this script; refuse to stop"}                      拒绝误杀
uv run python copyA/exp_web_server.py stop           # -> success (同路径合法)
```

结果: 代码层 stop 有 ping 指纹 + `ps` 命令行路径双重校验, **别的 checkout 的 stop 杀不掉本 checkout 的服务**; 同一 checkout 路径的任何会话都能合法 stop 它.

### E4 轮询压测 (H3)

```bash
# soak.py: 8 并发, 5000 请求 (2500 次 /api/roadmap + 2500 次 /), 采 /proc/<pid> 指标
uv run python soak.py http://127.0.0.1:39301 5000 <pid>
# baseline: fds=4,  threads=1, rss=21640KB
# midpoint: fds=9,  threads=7, rss=22856KB   (9/7 为在途连接/线程)
# final:    fds=4,  threads=1, rss=22796KB   (全部回落)
# codes: {"api:403": 2500, "page:200": 2500}  (0 次 5xx, 0 次连接错误)
```

结果: 5000 请求 (约等于 85094 生前 9.8 小时 ~8800 次轮询的量级) 后 fd/线程完全回落, 内存稳定, 无错误. 泄漏不存在.

### E5 日志 10MB 截断 (H4)

```bash
# 预填 11MB server.log 后 start:
ls -la rt-log/navigate-web-1001/server.log           # 预填 10800000 字节
uv run python copyA/exp_web_server.py start
ls -la rt-log/navigate-web-1001/server.log           # -> 257 字节 (启动时截断生效)
```

结果: 截断只发生在启动时 (`_serve` 入口检查一次); 运行中 `_log` 直接 append, 无任何大小检查 -- 服务不重启就无限增长. 增长率实测 (P4): 约 190KB/小时 ≈ 4.7MB/天, 到 10MB 约需 2 天, 之后缓慢无限增长, 但写失败被 `except` 吞掉, 不会导致服务失效.

### E6 roadmap 锁文件 (H5)

```bash
B=$(ls /tmp/navigate-roadmap-1001-*.lock | wc -l)    # 581
uv run python workflow/navigate/scripts/roadmap.py save /tmp/nav16-exp/rm1.json title '"..."'
uv run python workflow/navigate/scripts/roadmap.py save /tmp/nav16-exp/rm1.json notes '["..."]'
# 同一文件 save 两次 -> 只留 1 个锁文件 (按目标路径 sha256 前 16 位区分, 复用)
uv run python workflow/navigate/scripts/roadmap.py save /tmp/nav16-exp/rm2.json title '"..."'
# -> 第 2 个锁文件; 两个都从不删除
# 跑一次测试子集:
NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-16 uv run python -m pytest workflow/navigate/tests/test_roadmap_cli.py -q   # 5 passed
# 锁文件 583 -> 588 (delta=5): 测试每次运行都在真实 /tmp 留新锁文件
```

结果: `roadmap.py` 的锁文件路径用真实 `tempfile.gettempdir()` (不受 `NAVIGATE_WEB_RUNTIME_DIR` 隔离), `open("w")` 创建后从不清理; 测试用 `tmp_path` 唯一路径 → 每跑一次留一批. 现网 581 个 = 历史测试累积. 副作用仅 0 字节文件堆积, flock 语义正常, 无功能影响.

## 3 假设逐条裁决

| 假设 | 裁决 | 核心证据 |
| --- | --- | --- |
| H1 端口漂移与固定桥脱钩 | **成立 (根因放大器)** | 代码 `run_start` 候选 = 39271 + 10 个随机端口, 被占静默回退; E1 完整复现"服务 alive + 直连 200 + 桥哑"; E2 证明默认端口空闲时重建回同端口 (自愈), 漂移仅在被占时; TC-010 覆盖真机端口分支; P1/P2 显示 15:45 恢复是侥幸 |
| H2 会话收工 stop / 测试抢端口 / 误杀 | **成立 (根因主路径)** | stop 对同 checkout 会话合法且幂等清理 (E3 + 代码); P6: 85094 死后 server.json 被清 -- SIGKILL/SIGTERM 都会残留 server.json (E2 实证), 只有 `run_stop` 或手动 rm 才会清掉, 指向"经 stop 停止"而非崩溃; navigate 测试隔离了 runtime dir 但**绑真实 39271** (`nav_helpers.DEFAULT_PORT`, TC-008 断言 `port == DEFAULT_PORT`), 测试与生产在默认端口上互斥 (生产占着 → 测试挂, 测试占着 → 生产 start 漂移), 但测试不误杀 (conftest 只清自己 dir + 指纹校验); "把 39271 守护当外来占用 kill"是绕过代码保护的手动操作, 只能靠端口归属清晰化降低诱因 |
| H3 无界线程与 fd 泄漏 | **不成立** | E4: 5000 请求 fd/线程全回落, 0 错误; `ThreadingHTTPServer.daemon_threads = True` (Python 3.11), 线程用完即退; 每请求日志 open/append/close 有锁; 85094 死前无任何 `serve error` (代码在 serve_forever 异常时会写日志), 与"骤死=被杀"吻合, 与"泄漏耗尽"不符 |
| H4 server.log 无上限增长 | **部分成立 (卫生问题, 非根因)** | E5: 11MB 启动即截断; 但截断只在启动时, 运行中不轮转; 实测增速 ~4.7MB/天, 长跑会无限涨; 写失败被吞, 不会杀进程; 事发时 log 仅 3.5MB, 与页面失效无因果关系 |
| H5 幽灵实例 / 锁文件堆积 | **一半不成立, 一半成立 (卫生问题, 非根因)** | 幽灵实例: E2 实证 status/start 都发真实 ping, 残留 server.json 不造成误判, 重建正常 -- 不成立; "运行时文件被系统清理": 容器内无 /tmp 清理守护 (P3 文件 mtime 均保留), rm 重置容器时进程同死 -- 不成立; 锁文件堆积: E6 实证成立 (581 个, 测试每次新增), 但无功能副作用 |

## 4 根因结论

### 4.1 结构性根因

事故不是单点 bug, 而是三个设计缺口叠加:

1. **服务生命周期与使用者脱钩** (H2): 展示实例是共享目录里的无主单例 -- 谁都能起, 谁都能停, 没有归属, 没有巡检, 没有自愈. 桥和浏览器是它的长期使用者, 但服务的死活对它们完全不可见. P4 显示现役服务 9.5 小时内 0 次 ping: 当前"稳定"只是因为碰巧没人再碰它.
2. **端口隐式协商, 事实源不推送** (H1): 真实端口只存在于 `server.json` 和一次性的 `start` stdout 里; 桥配置 (127.0.0.1:39271/39300) 是另一份静态事实, 两者之间没有任何同步机制. `start` 静默漂移时没有任何信号提醒"端口变了".
3. **测试与生产共享真实默认端口**: 测试隔离了运行时目录却没隔离端口, `TC-008` 必须绑到真实 39271 -- 多会话并行时测试与生产互斥, 这既让测试变脆, 也制造了"39271 被神秘进程占用"的迷惑现场 (历史上诱发人工误杀).

### 4.2 85094 死因的最佳解释 (推断)

已查证: 死亡窗口 15:15:10~15:15:13; 死前无 error; 非 OOM; 死后 `server.json` 不在.
推断链: SIGKILL 与 SIGTERM 默认处理都不执行 `_serve` 的 finally (E2 实证 SIGKILL 残留 server.json), 所以"server.json 消失"只能由 `run_stop` (显式 unlink) 或手动 rm 造成; `run_stop` 的 ps 指纹要求调用方脚本与 85094 同路径 (主检出), 即**同一主检出里的另一会话按收工流程跑了 stop**, 或有人在 stop/rm 配合下手动清理. 与"同期有其他会话在同一 checkout 工作"的事实吻合. 精确到哪个会话无法追认 (stop 不写日志), 见第 7 节.

### 4.3 与"每次更新路线图后打不开"的对应

更新路线图本身 (`roadmap.py save`) 不重启服务, 与页面失效**无因果** (前端 4 秒轮询会自动读到新内容). 因果在时间上相邻: 更新路线图的操作发生在会话收工/开工边界, 而收工按完成定义 stop 展示服务、开工又可能与其他实例/测试撞端口 -- 所以用户感知为"每次更新后容易打不开". 15:15 事件正是收工 stop (30 分钟后 15:45 由下一次开工重建恢复).

## 5 修复建议与影响面 (供 milestone-17 实施)

### 5.1 临时缓解 (39300 + /tmp/navigate-display-1001 + 桥指 39300) 的评估

- **有效成分**: 独立运行时目录使其他会话在默认目录上的 start/stop 不再触碰展示实例, 直接切断 H2 主触发路径; 桥已对准 39300, 当前链路通 (P4 实证 9.5h 稳定).
- **不够的地方**: (a) 无自愈 -- 服务若死, 没有任何东西重建它; (b) 复原没有可重复入口 -- 现役实例是 `__serve__ 39300` 手工起的 (P5), `start` 的候选端口根本不含 39300, 带着display 目录跑 `start` 也只会试 39271+随机, **照现有手段无法把服务复原回 39300**, 桥就不可能自愈.
- **判断**: 缓解方向正确 (独立目录 + 固定端口), 但缺"可重复复原"这一环, 不足以只靠它收尾; milestone-17 应补齐 5.2 后把它固化, 而不是回到共享默认目录.

### 5.2 具体改动点

1. **`workflow/navigate/scripts/web_server.py`**:
   - `start` 增加显式端口入口 (env `NAVIGATE_WEB_PORT` 或 CLI 参数): 设了就只试该端口 -- 被自己旧实例占 (ping 指纹匹配) 则复用, 被陌生进程占则报错 `port_in_use` 并**不漂移**; 未设时保持现状 (39271+随机回退), 兼容既有测试与调用方. 这是把"固定端口 + 桥自愈"从口头约定变成产品保证的最小改动.
   - (低优先) `_log` 运行中滚动: 每写 N 行检查 size 超 10MB 时截断重开, 约 3 行改动; 不做也不影响稳定性.
2. **展示编排脚本** (新增, 如 `workflow/navigate/scripts/display_serve.sh` 或并入现有启动约定): 固定 `NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-display-1001` + `NAVIGATE_WEB_PORT=39300`, `start` 后校验返回 `port == 39300` 否则报错; 可选 while 循环 `status || start` 做自愈巡检. 桥保持 `8801 -> 127.0.0.1:39300` 不动 (E2 证明: 只要复原回固定端口, 桥零操作自愈).
3. **tests**:
   - `nav_helpers.py` 支持按 env 指定端口, `TC-008`/`TC-010` 改用 `free_port()`, 消除测试-生产在真实 39271 上的互斥; 保留一条真实默认端口漂移的回归用例.
   - 新增固定端口模式用例 (见 6 节 R1-R4).
4. **`web/index.html`**: 无需改 (轮询/错误提示/后台标签页处理已健全); 可选: network 错误文案补一句"检查展示服务与 8801 桥".
5. **端口与运行时身份策略 (写进文档/约定)**: 展示实例唯一归属 display 目录 + 39300, 其他会话不在该目录 start/stop; 收工流程不 stop 展示服务 (需从完成定义中移除该动作或加豁免).
6. **`roadmap.py` 锁文件** (顺手, 低优先): `_lock_file_path` 尊重 `NAVIGATE_WEB_RUNTIME_DIR` 或在用完后清理, 消除 /tmp 堆积; 不改也无功能危害.

### 5.3 影响面清单

| 文件/组件 | 改动 | 风险 |
| --- | --- | --- |
| `workflow/navigate/scripts/web_server.py` | start 显式端口 + 不漂移语义 | 未设 env 时行为不变; 设了 env 的旧调用方 (无) 不受影响 |
| `workflow/navigate/scripts/display_serve.sh` (新) | 复原/自愈入口 | 无; 纯新增 |
| `workflow/navigate/tests/nav_helpers.py` + `test_web_server_lifecycle.py` | 测试脱离真实 39271 + 固定端口用例 | TC-008/TC-010 断言需随端口注入调整 |
| `socat 8801` 桥 | 不动 (指 39300 固定) | 复原回 39300 即自愈 |
| 展示约定文档 | 归属 + 收工豁免 | 需要各会话遵守 |
| `workflow/navigate/scripts/roadmap.py` | 锁文件目录/清理 (可选) | 极低 |

## 6 可自动化回归用例 (供 milestone-17 直接落地)

- R1 固定端口复用: `NAVIGATE_WEB_PORT=P start` → `port == P`; stop; 再 start → 复用同端口 (E2 语义固化).
- R2 固定端口被陌生进程占: start 报 `port_in_use`, **不产生**随机端口实例 (防 H1 回归).
- R3 SIGKILL 后 server.json 残留: status 报 `alive: false`; start 重建回 P (现行为, 回归保护).
- R4 跨脚本路径 stop 拒绝: E3 行为补成用例 (防误杀回归).
- R5 soak: 2000 请求后 fd/线程回落基线, 0 个 5xx (H3 回归).
- R6 测试与生产并存: nav_helpers 改造后, 生产实例占默认端口时全套 web_server 测试仍全绿.
- R7 (若做 5.2.1b) 伪造大 log 运行中滚动.
- R8 (若做 5.2.6) save 后锁文件落在受控目录.

## 7 已查证 / 推断 / 未核实

**已查证** (本会话实测或有直接文件/命令行证据): 第 1 节 P1-P7 全部现场事实; E1-E6 全部实验结果; 测试基线 8/8 通过 (`test_web_server_lifecycle` + `test_web_server_endpoints` + `test_web_server_persistence`, `NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-16`); 代码事实 (start 候选端口表, stop 指纹链, 日志截断时机, 前端 POLL_MS=4000, ThreadingHTTPServer daemon_threads).

**推断** (证据充分但非直接观测): 85094/106316 死于同 checkout 会话的 `run_stop` 或配套手动清理 (4.2); "每次更新后打不开"与收工/开工边界的对应关系 (4.3); 临时缓解不足以只靠自身收尾 (5.1).

**未核实** (证据缺口): 85094 与 106316 死亡瞬间的具体执行者 (哪个会话, stop 还是手动 kill) -- stop/kill 不写日志, 无法追认; 桥 8801 的创建者与创建时间; 真实 39271 上的漂移未在本会话实测 (为避免占用共享默认端口干扰并行会话, 用一次性端口 39301 等价复现, 机制同一行常量之差, 且 TC-010 已覆盖真机分支); 10-31 凌晨 03:26~04:06 五次重启的直接原因; 用户主观感受的失效频率无法与日志逐一对应.
