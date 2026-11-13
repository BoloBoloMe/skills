# milestone-17 实施报告: navigate 展示页固定端口与复原入口

任务标识: NAV-17. 分支 `m17-navigate-stability` (起点 50eb649), 只在本 worktree 改动.
实施依据: `docs/changes/workflow-stack-review/milestone-16/FINDINGS.md` 第 5 节改动点与第 6 节 R1-R8 用例, 未重复侦查.

结论先说: 展示服务现在有固定端口与可重复的复原命令. `web_server.py start` 支持 env `NAVIGATE_WEB_PORT` 显式锁端口 (被占不漂移), 新增 `display_serve.sh ensure` 一条命令把死掉的展示实例复原回固定端口 39300 (转发桥零操作自愈); 测试套件不再与生产在真实 39271 上互斥; 顺手做了运行中日志滚动与 roadmap 锁文件目录隔离. milestone-16 的 R1-R8 用例全部落地为自动化测试或实跑验证, 全套 37 个测试在"39271 被真实实例占用"与"39271 空闲"两种现场下均通过. 现役展示服务 (39300, pid 117626) 与 8801 桥全程未动.

## 1 改动点

| 文件 | 改动 | 对应 FINDINGS |
| --- | --- | --- |
| `workflow/navigate/scripts/web_server.py` | start 增加显式端口入口 env `NAVIGATE_WEB_PORT` (选了 env 方案, 未加 CLI 参数, 见 4.1): 设了只试该端口 -- 存活实例复用, 自家旧实例 (ping 指纹 + 本脚本路径匹配, server.json 已丢) 收编复用, 陌生进程占用报 `port_in_use` 且不漂移; 未设时保持 39271 + 随机回退, 兼容既有调用方. 另做 `_log` 运行中滚动 (超 10MB 截断重开, 常量 `_LOG_MAX_BYTES`) | 5.2.1, 5.2.1b |
| `workflow/navigate/scripts/display_serve.sh` (新增, 可执行) | 展示编排/复原入口: 固定 `NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-display-<uid>` + `NAVIGATE_WEB_PORT=39300`; `ensure` 为首选入口 (活着且端口对则复用, 死了拉起, 活着但端口错则 stop+start 重建), `start` 后校验 port == 39300 否则报错退出; stdout 单行 JSON 供调用方解析, 诊断走 stderr; 桥不在管辖内 | 5.2.2 |
| `workflow/navigate/scripts/roadmap.py` | `_lock_file_path` 尊重 `NAVIGATE_WEB_RUNTIME_DIR` (未设仍用系统临时目录, 行为不变), save 前确保目录存在 | 5.2.6 |
| `workflow/navigate/tests/nav_helpers.py` | 加 `ENV_PORT` 常量; `run_cli` 支持 `script=` 换脚本路径 (R4 用) | 5.2.3 |
| `workflow/navigate/tests/test_web_server_lifecycle.py` | TC-008/TC-009 改用 `free_port()` + `NAVIGATE_WEB_PORT`, 脱离真实 39271; TC-010 保留为真实默认端口漂移回归并加固 (39271 绑不上时借既有占用验证漂移, 不与生产互斥); 新增 R1/R2/R3/R4/R7 用例 | 5.2.3, R1-R4, R7 |
| `workflow/navigate/tests/test_web_server_soak.py` (新增) | R5: 2000 请求后 fd/线程回落基线, 0 个 5xx, 0 次连接错误 | R5 |
| `workflow/navigate/tests/test_roadmap_cli.py` | R8: 锁文件落在受控运行时目录, 同目标重复 save 复用同一锁 | R8 |
| `workflow/navigate/SKILL.md` | 制图 step 4 起展示服务改用 `display_serve.sh ensure`; 新增 "展示服务" 节: 展示实例归属 display 目录 + 固定端口 39300, 其他会话不在该目录 start/stop, 收工不 stop 展示服务, 实验/测试用独立目录与一次性端口 | 5.2.5 |
| `workflow/navigate/web/index.html` | network 错误文案补一句: 指向 `display_serve.sh ensure` 复原与转发桥端口检查 | 5.2.4 (可选项) |

入口口径 (按任务要求写清): 显式端口入口只做了 env `NAVIGATE_WEB_PORT` 一种, 未加 CLI 参数. 理由: 与既有的 `NAVIGATE_WEB_RUNTIME_DIR` 测试隔离机制同构, 组合使用自然; 子进程经 `env=os.environ.copy()` 继承, `__serve__` 子命令签名与现役实例的进程命令行形状 (`web_server.py __serve__ <port>`) 不变, 对 stop 的 ps 指纹校验零影响.

## 2 复原流程实跑验证 (display_serve.sh)

真实展示实例 (39300) 与 8801 桥未触碰. 演练用覆盖变量 `NAVIGATE_DISPLAY_RUNTIME_DIR=/tmp/navigate-m17/display` + `NAVIGATE_DISPLAY_PORT=39311` (一次性端口) 跑完整复原流程, 四个分支全部实测:

1. **冷启动**: `ensure` -> `{"port": 39311, "pid": 161633, "reused": false}`, `curl` 200.
2. **复用**: 再跑 `ensure` -> `ensure ok: 复用存活实例 port=39311 pid=161633`, 无第二进程.
3. **死后复原 (主场景)**: `kill -9` 服务进程, `status` -> `{"alive": false}` (ping 探活兜底, 不被骗); `ensure` -> 重建回 39311 (`pid 161702`), `curl` 200. 固定端口不变, 指向 39311 的桥 (同现网 8801 -> 39300) 零操作恢复 -- 这就是"服务死了能复原回 39300"的实跑证据.
4. **陌生占用不漂移**: 用普通 python socket 占住 39311 后 `ensure` -> 退出码 1, 报 `port_in_use` ("occupied by a foreign process; refusing to drift"), 未产生任何实例 (server.json 不在); 占用撤离后 `ensure` 复原回 39311.
5. **自家旧实例收编**: 删掉存活实例的 `server.json` 再 `start` -> `{"reused": true, "adopted": true, "pid": 161791}`, 旧进程原样保留 (ps 确认), 运行时文件写回.
6. **别的 checkout 的 navigate 占端口**: 用本脚本副本 (不同路径) 占 39312, 再从本 worktree `start` 同端口 -> 报 `port_in_use` 且明确指出 "another navigate-web instance (pid 168912, different script path)".

## 3 自动化回归 (R1-R8 落地对照)

实跑命令与结果 (均在仓库根, `NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-17`):

```
uv run python -m pytest workflow/navigate/tests -q
-> 37 passed, 2 subtests passed in 16-17s   (两种现场各跑一轮, 见下)
uv run python general/writing-for-llm/check_skill.py workflow/navigate/SKILL.md
-> workflow/navigate/SKILL.md: OK
```

R6 现场对照: 先用 scratch 运行时目录在默认模式 (未设 `NAVIGATE_WEB_PORT`) 起一个真实 navigate 实例占住 39271, 全套测试跑一轮 -> 37 passed; 停掉后再跑一轮 -> 37 passed. 即"生产实例占真实默认端口时全套测试仍全绿"已实测, 不再互斥.

| 用例 | 落地 | 结果 |
| --- | --- | --- |
| R1 固定端口复用/重建同端口 | `test_fixed_port_reuse_and_rebuild_same_port` | 已实测通过 |
| R2 固定端口被陌生占 -> port_in_use 不漂移 | `test_fixed_port_refuses_foreign_occupant` (断言无实例产生, 进程数差值为 0) | 已实测通过 |
| R3 SIGKILL 残留 -> status 报死 -> 重建回同端口 | `test_fixed_port_rebuild_after_sigkill` | 已实测通过 |
| R4 跨脚本路径 stop 拒绝 | `test_stop_refuses_foreign_script_copy` (脚本副本 stop 被拒, 实例存活, 本路径 stop 正常) | 已实测通过 |
| R5 soak 2000 请求 fd/线程回落, 0 个 5xx | `test_web_server_soak.py::test_soak_fds_and_threads_settle_no_5xx` | 已实测通过 |
| R6 测试与生产在默认端口并存 | TC-008/009 改 free_port 结构性解除互斥 + 上述双现场实跑 | 已实测通过 |
| R7 运行中日志滚动 | `test_log_rotates_during_run` (预填 11MB, 一次请求后 < 1MB) | 已实测通过 |
| R8 锁文件落受控目录 | `test_lock_files_land_in_runtime_dir` | 已实测通过 |

既有回归: TC-008/009/010, TC-015/016, 持续运行与 stdlib-only 静态检查全部保留且通过; TC-010 即"真实默认端口漂移"回归 (39271 被占 -> 漂移到随机端口且服务可用).

开发中修正一处: R2/TC-009 最初用 `count_serve_processes() == 0/1` 绝对计数, 在 R6 现场 (同脚本路径的并存实例) 误报, 改为操作前后进程数差值后双现场全绿.

## 4 未做项与理由

1. **display_serve.sh 不带常驻自愈巡检守护**: 常驻巡检是又一个无主单例, 正是 milestone-16 根因 (H2) 的同款结构; `ensure` 幂等且已足够复原, 需要巡检时挂 cron/人工重复执行即可. 脚本头注释已写明. (FINDINGS 5.2.2 标注自愈巡检为可选)
2. **端口入口未做 CLI 参数**: 见第 1 节口径, env 单入口.
3. **ensure 遇"活着但端口错"自动重建** (stop+start): 这是超出 FINDINGS 原文的小决策, 依据是 display 目录归展示脚本专属 (SKILL.md 已写), 目录内不该有别的端口的实例; 陌生占用场景 (不可自动修复) 仍只报错, 不杀占用者, 不换端口. 此项未经用户确认, 列入待决问题.
4. **roadmap.py 锁文件未做"用完即删"**: unlink 持锁文件有经典竞态 (另一进程可能持着已 unlink inode 的锁, 第三个进程新建同名文件再持锁, 互斥失效), 选了目录隔离方案 (5.2.6 的另一选项), 行为等价安全.

## 5 已实测通过 / 未验证 / 证据缺口

**已实测通过** (本会话实跑): 第 2 节复原流程全部分支; 第 3 节全部测试与双现场 R6; check_skill.py; `uv run python workflow/navigate/scripts/roadmap.py query docs/changes/workflow-stack-review/roadmap/ROADMAP.json milestones.milestone-17.question` 全程可用 (锁文件改动后 save/query 正常).

**未验证**:
- 真实 39300 展示实例上的端到端复原 (需要 stop/重启现役服务, 属 milestone-08 验收与宿主决策, 本轮硬约束禁止): 已验证的是同构演练 (独立目录 + 一次性端口 39311), 机制完全同一条代码路径.
- 8801 桥零操作自愈的浏览器实测: 桥未动也未重启, 本轮只验证了"复原回同端口则桥目标不变"的服务侧前提 (39311 演练同构).
- `web/index.html` 新文案的实际渲染: 页面改动未起浏览器查看 (前端无构建, 改动为单行字符串字面量, 语法风险极低).

**证据缺口**:
- 无. milestone-16 FINDINGS 第 7 节的缺口 (85094 死因追认等) 属侦查阶段, 本轮不涉及.

## 6 待决问题 (交宿主/用户)

1. 第 4.3 节 ensure 的错端口自动重建是否接受.
2. SKILL.md 新增的展示服务纪律 (归属 display 目录, 收工不 stop) 需各会话遵守, 是否还要写进别的完成定义/收工清单位置, 由宿主定.
3. 现役展示实例是手工 `__serve__ 39300` 起的, 未经新入口; 下次需要重启时可换用 `display_serve.sh ensure` (会带上 server.json 记录), 是否切换由宿主在验收时决定, 本轮未动它.
