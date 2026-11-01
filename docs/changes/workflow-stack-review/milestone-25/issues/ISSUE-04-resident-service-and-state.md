## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成
- [ ] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.

## 要交付什么
让服务真的能起, 复用, 探活, 停, 并且状态可核实:

- `workflow/codebase-map/scripts/codemap_service.py`:
  - 运行时目录与文件锁: `runtime_dir/lock` 的 `flock(LOCK_EX)`, 覆盖 serve 启动/复用, build 的副本复制与 `data_keys` 更新, stop 全过程; 拿不到锁等待上限 30 秒, 超时 `internal_error`. 目录 0700, 文件 0600.
  - `state.json` 字段: `version` (1), `port`, `last_port`, `last_url`, `pid`, `bind` (`0.0.0.0`), `started_at` (UTC ISO8601), `stopped_at`, `command_path`, `serve_root`, `log_path`, `runtime_dir`, `data_keys` (每项 `{key, source_cc_json, built_at, bytes}`). 原子写 (临时文件 + rename).
  - 三步探活 (全过才算存活): `os.kill(pid, 0)` 不抛错 -> 能连 `127.0.0.1:<port>` -> `GET /` 返回 200. `state.json` 存在本身不算存活.
  - 判定分支: `pid` 为 null 且有 `stopped_at` = 已知停机, 按目标端口起; 探活通过 = 复用 (不起进程); `pid` 存活但端口无人应答, 或端口上的监听者不是本服务 = `state_mismatch` (报错, 不接管, 不重起); `pid` 不存在 = 旧实例已死, 目标端口空闲就重起并报告, 被别的程序占用则 `port_in_use` (不静默顺延).
  - 端口决策: `--port` 实参, 否则 `state.last_port`, 否则 8090. 换端口成功时算好 `port_changed` 与 `previous_url` (由 `last_url` 或旧端口加当前地址拼出) 交输出层, 并把新端口写进 `port` 与 `last_port`.
  - HTTP 面: `ThreadingHTTPServer` 绑 `0.0.0.0:<port>`, 只读静态服务 `serve_root`; 路径先 `resolve()` 再判 `relative_to(serve_root)`, 根外路径与根外软链一律 404; 不做目录 listing; 不做 HTML5 回退; 不提供上传/写接口.
  - 子进程: `python3 <脚本> _serve-daemon` 加 `start_new_session=True`, stdout/stderr 追加到 `logs/service.log`; 父进程轮询端口就绪 (上限 10 秒) 后写 `state.json`. `_serve-daemon` 是内部隐藏入口, 不写进文档用法.
  - `stop`: 锁 -> 读 state -> 探活 -> `SIGTERM` -> 等 10 秒 -> 仍在则 `stop_failed` (不自动 SIGKILL) -> `pid` 置 null, 写 `stopped_at`, 保留 `port`/`last_port`/`last_url`, 清锁文件; 保留 `serve-root/` 与 `cache/`.
  - `serve` 前置: `data_keys` 与 `serve_root` 里实际 `.cc.json` 的交集为空则 `no_data_keys`, 两类文案 ("还没 build 过" 与 "副本已删, 建议重新 build"), 不起空服务.
- `codebase-map.py` 注册 `serve` 与 `stop` 两个子命令, `--json` 字段: `stop` 为 `{success, command, stopped, pid?, port?}`; `serve` 的完整字段见 ISSUE-05, 本 issue 先给 `success`/`command`/`port`/`bind`/`reused`/`pid`/`serve_root`/`port_changed`/`previous_url`.
- 新测试树补本 issue 用例 (临时 `CODEMAP_RUNTIME_DIR`, 独立端口, 假 `serve-root` 里放 `index.html` 与伪 `.cc.json`).

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-003 (存活复用, 并发单例, 端口被占, 显式换端口, 换端口后沿用, `instance_running`, 绑 0.0.0.0), AC-004 (状态记录齐全, 残留记录判死, 两种不一致报错, 不自行退出, stop 停整个服务, 重复 stop, 删运行时目录复原, 两类 `no_data_keys`); BR-001 至 BR-009, BR-013 (serve/stop 落地), BR-029 (HTTP 面), BR-030; G-003, G-004, NG-007, NG-009.
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 模块接口 (常驻服务与状态 全节, `stop --json` 字段, CLI 全局环境变量, 错误码), 关键流程 (serve 启动/复用, stop), 非功能要求 (单例与并发, 常驻性, 状态真实性), 安全策略 (传输与访问, 越界防护, 停止与清理).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D015, D016, D018, D020, F003.
- `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`: D003, D022, D024.
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D007.

## 允许范围
同全局, 增量: `codemap_service.py` 全节, `codebase-map.py` 的 `serve`/`stop` 接线 (不含地址与交付输出, 那部分归 ISSUE-05), 本 issue 的测试.

## 禁止范围
- 不做地址解析与 URL 组装, 不输出 `url`/`base_url`/`keys[].url`/`delivery_notes`/`address_missing` (归 ISSUE-05); 本 issue 的 `serve` 只保证端口, 状态, 复用与监听.
- 不换端口顺延, 不在有存活实例时偷偷起第二个, 不接管端口上的其它程序, 不自动 SIGKILL.
- 不清 `serve-root` 与 `cache`, 不清 `state.json` 里的端口记录 (`port`/`last_port`/`last_url`).
- 不做目录 listing, 不做 HTML5 回退, 不开写接口, 不加认证与 TLS.
- 不把 `--address` 或任何地址写进 `state.json`.
- 不在测试里占用 8090; 不碰其它 skill 的运行实例.

## 代码定位提示
- 从零新建 `workflow/codebase-map/scripts/codemap_service.py`; 子命令接线在 `codebase-map.py`.
- 既有形状参照: `workflow/navigate/scripts/web_server.py` 的 `flock` (行 96-99, 664, 745), `ThreadingHTTPServer` 与 `_Handler` (行 43, 502), 越界判定先 `resolve()` 再 `relative_to` (同 m13 F012 已验证的 present 口径), 守护子进程与 `start_new_session` 的收尾做法; `workflow/navigate/tests/conftest.py` 与 `nav_helpers.py` 的"起服务-断言-收尾 stop 加强杀"夹具写法 (新树自己写一份唯一定名 helper, 不 import 它们).
- 测试隔离: `CODEMAP_RUNTIME_DIR` 指临时目录, `--port` 用高位临时端口, `CODEMAP_PORT` 只作测试用首选端口覆盖.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: 状态文件与锁, 三步探活与判定分支, 端口决策与换端口, 守护子进程, HTTP 静态服务与越界, stop 语义.
- 验证要求/证据: 覆盖 AC-003 与 AC-004 的全部可观察结果, 并单独验证非功能要求的三条 (单例与并发, 常驻性, 状态真实性); 每条失败分支都要看到稳定错误码. 证据为 pytest 输出加一次手工全流程的命令与输出摘录 (临时运行时目录, 放 `/tmp/m25-04/`).
- 时间常量 (锁 30 秒, 就绪 10 秒, stop 10 秒) 不写用例: 会把时长变成测试博弈, 改按实现常量核对一次并记入交付证据 (理由见 EXECUTION 验证策略).

## 验证入口
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 本 issue 新增用例:
  - TC-003 (AC-003 主用例): 起服务后再次 `serve`, 两次 `port` 与 `url` 相同, 第二次 `reused == true`, `pid` 不变, 进程数不变.
  - TC-004 (AC-004 主用例): 首次 `serve` 成功后 `state.json` 字段齐全 (逐字段核对), 文件权限 0600, 目录权限 0700, `bind == "0.0.0.0"`.
  - TC-04-01: 两个线程/进程同时对同一运行时目录 `serve`, 结束时 `state.json` 只有一个 `pid`, 两次输出同 `port` 同 `url`, `reused` 一次 false 一次 true.
  - TC-04-02: 先用一次性 socket 占住目标端口且无生效实例, `serve` 返回 `port_in_use`, 退出码非 0, 该端口仍被原程序持有, 不去试其它端口.
  - TC-04-03: 起服务 -> `stop` -> `serve --port <新端口>`, 新端口 `GET /` 200, `port_changed == true`, `previous_url` 等于停机前的 URL, 旧端口不再响应.
  - TC-04-04: 承上, 再 `stop` 后不带 `--port` 执行 `serve`, 服务起在上一回的端口, 不回到 8090.
  - TC-04-05: 存活实例上用 `--port` 指定别的端口, 返回 `instance_running`, 存活实例仍在原端口 200, 新端口无人监听.
  - TC-04-06: 手工把 `state.json` 的 `pid` 改成一个不存在的值, `serve` 输出说明旧实例已死并按记录端口重起, 新 `pid` 与端口可用.
  - TC-04-07: 两种不一致各一次: `pid` 活着但端口无人应答; 端口被别的程序占着而 `state` 记着本服务的 `pid`. 两次都返回 `state_mismatch`, 退出码非 0, 不接管端口, 不重起.
  - TC-04-08: `stop` 后 `GET /` 失败, `state.json` 的 `pid` 为 null 且 `stopped_at` 有值, `port`/`last_port`/`last_url` 保留; 重复 `stop` 退出码 0 且输出说明当前没有在跑的服务.
  - TC-04-09: 根外路径 (`../`), 根外软链 `.cc.json`, 目录路径 (无 `index.html`) 都 404 且不列目录; `POST`/`PUT` 不被接受.
  - TC-04-10: 两类 `no_data_keys`: 清单与磁盘都空 -> 文案说明还没 build; 清单有条目但副本全缺 -> 文案说明副本已删并建议重新 build. 两次都不起服务 (端口无监听).
  - TC-04-11: 常驻性短时验证, `serve` 成功后隔真实等待 (不少于 2 秒) 并跨另一次 CLI 调用, `GET /` 仍 200 且再 `serve` 复用同一 `pid`.
- 手工核验 (时间常量与子进程): 起一次真实服务后核对 `_serve-daemon` 子进程的父进程已退出而服务仍活, `logs/service.log` 有内容, 实现里的 30/10/10 秒常量与 TECHNICAL 一致; 命令与输出留证据.
- 通过标准 (整体): 每条断言成立; 任何失败都带稳定错误码; 测试全程用临时运行时目录与临时端口, 结束后无残留进程.

## 交付证据

## 风险提示
- 测试会起真实子进程, 收尾必须 stop 加强杀兜底, 否则残留进程会让后续用例的端口与状态互相污染 (先例: `workflow/navigate/tests/conftest.py`).
- 换端口与 `stop` 都要保留 `last_url`, 否则 `previous_url` 会退化成假定旧端口 8090 (D018 明确禁止).

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 需要新增状态字段或改端口判定顺序时停止并上报.

## 验收标准
- [ ] 并发两次 `serve` 只留一个实例, 状态里只有一个 pid, 两次同端口同 URL.
- [ ] 存活判定三步全过才算活, 伪造的 `state.json` 三种死法都判死.
- [ ] 端口被占报 `port_in_use` 不顺延, 有存活实例时换端口报 `instance_running`.
- [ ] `stop` 后旧 URL 失效, 端口记录保留, 重复 `stop` 幂等成功.
- [ ] 静态服务只放 `serve_root` 内的文件, 根外路径与根外软链 404, 无 listing 与写接口.
- [ ] 交集为空时拒绝起空服务并给出两类不同文案.

## 被阻塞于
- `ISSUE-01-shared-rules-and-cli-contract.md`
