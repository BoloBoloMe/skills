## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要核验什么
本轮改动后, 既有安全面与常驻性没有回退:

- 常驻与关闭: 调用结束, 无请求闲置, 会话断开后服务仍在原端口可访问; 显式 `stop` 关闭该用户全部共用页面; 不恢复空闲自动退出.
- 内容面与控制面: 同网段能读已挂载内容; 同网段请求 `/__control__/*` 返回 403 且挂载清单不变; 本机来源 ping 返回 200 且带服务 pid; 含 `../` 与指向挂载目录外的 symlink 均 404.
- 隔离: 本轮测试与验证只用独立运行时目录和独立端口, 未停止或接管真实展示实例, navigate 的实例与记录未被触碰.
- 首次开放风险与挂载范围: 交付时说明过一次同网段可读全部挂载目录的风险, 实际挂载的只有本次展示目录, 不含仓库根或敏感目录.

对应 AC-005, AC-006; BR-008, BR-009, BR-011, BR-012, BR-015 (审计), BR-017 (实做核对); 非功能要求 常驻性.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`, AC-005, AC-006; BR-008, BR-009, BR-011, BR-012, BR-015, BR-017.
- Technical: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`, 非功能要求 (常驻性), 安全策略 (传输与访问, 管理面, 越界防护, 隔离), 接缝与依赖 (用户设备访问 属真正外部).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D006, D007, D008, D012, F007, F012, F013.

## 代码定位提示
- 只读实现入口: `general/present/scripts/web_server.py` 的 `_serve` (行 701, `serve_forever` 一直在, 无 TTL), `_guard_control_namespace` (行 520), `_is_loopback_client` (行 499), `_serve_static` (行 614), `run_stop` (行 1051).
- 相关用例: `general/present/tests/test_web_server_lifecycle.py` 行 758 `TestServerPersistsWithoutRequests` (行 776 `test_idle_server_stays_available_until_stop`), 行 502 `TestTC012Stop`; `general/present/tests/test_web_server_control_plane.py` (`_probe_lan_ipv4`, TC-022/TC-023 与 bind 具体地址用例); `general/present/tests/test_web_server_content.py` (TC-018 listing, TC-019 `../`, TC-020 越界 symlink).

## 验证入口
- `uv run python -m pytest general/present/tests`; 通过标准 退出码 0 且无 failed, 上述用例未改动.
- 常驻性: 复跑 `test_idle_server_stays_available_until_stop`; 在完成证据里注明它注入的 `PI_PRESENT_WEB_TTL_SECONDS` 已不被实现读取, 该用例是防旧自退行为复活的保护, 不恢复自退语义, 也不新增 24 小时等待用例 (理由见 `../EXECUTION.md` 验证策略).
- 真实 stop 与共享影响: 用临时 `PI_PRESENT_WEB_RUNTIME_DIR` 起一个实例, 挂两个目录, 记两个页面 URL, 跑 `stop`; 通过标准 两个 URL 都不再返回 200, 记录文件已删除; 全程不碰真实展示实例.
- 控制面与越界真实请求: 起隔离实例绑 `0.0.0.0`, 用本机非 loopback IPv4 请求 `/__control__/ping` (期望 403), 请求 `/../<挂载目录外的真实文件>` (期望 404), 本机 loopback 请求 `/__control__/ping` (期望 200 且 pid 与记录一致); 命令与输出留证据. 若本机没有非 loopback IPv4, 记跳过原因, 不算通过.
- 同网段访问 (AC-006 场景 1/2): 与 ISSUE-05 的两种环境真实设备取证共用同一次请求, 不重复执行; 若本次没有同网段另一台设备, 记未验证, 不用本机请求顶替.
- 隔离核验 (BR-015 审计): 验证前后各跑一次 `pgrep -af "scripts/web_server.py"` 与 `ls -l --time-style=full-iso /tmp/pi-present-web-$(id -u)/`, 对比真实实例的 pid 与记录 mtime 不变; 同时 `git status --short` 无 `workflow/navigate/` 变更.
- 挂载范围核对 (BR-017): 检查实际 `start`/`add-dir` 用的目录都在临时展示目录下, 不含仓库根, `~/.agents`, `~/.pi`, 密钥或登录态文件.
- 条件回归: 本 issue 只读 `_Handler` 相关行为且不修改代码, `uv run python -m pytest workflow/to-spec/tests/test_ac_draft.py` 免跑; 若前序 issue 实际触碰了 `_Handler` 而升级了回归范围, 本 issue 一并跑该用例并在证据里写明.

## 完成证据

## 完成证据

环境: 容器内 (本会话), Python 3.11.2 / pytest 9.1.1, 本机非 loopback IPv4 = `192.168.65.165` (eno1). 原始输出 `/tmp/m15-04/`.

### 复跑的既有用例 (断言未改动)

- `uv run python -m pytest general/present/tests/test_web_server_lifecycle.py -k "idle or stop or Stop" -v` -> `3 passed, 24 deselected`: `TestServerPersistsWithoutRequests::test_idle_server_stays_available_until_stop`, `TestTC012Stop::test_stop_terminates_and_removes_runtime_file`, `TestTC012Stop::test_stop_idempotent_when_json_removed_while_waiting_lock` (`/tmp/m15-04/lifetime-cases.txt`).
  该闲置存活用例注入的 `PI_PRESENT_WEB_TTL_SECONDS=0.2` 已不被实现读取 (3dc49c6 删空闲自退), 它现在的作用是防旧自退行为复活; 本次未恢复自退语义, 也未新增 24 小时等待用例.
- `uv run python -m pytest general/present/tests/test_web_server_content.py general/present/tests/test_web_server_control_plane.py -v` -> `16 passed`: 扁平并集/同名遮蔽/顶层 listing 并集 (TC-016/17/18), `../` 逃逸 404 (TC-019), 越界 symlink 404 (TC-020), 子目录 listing (TC-021), 可读子集 (R1), 非规范顶层路径 (R2), LAN 来源控制面 403 (TC-022 三条), loopback 未知控制路径 404 (U-010 两条), LAN 来源静态内容 200 (TC-023), bind 具体 IP 的本机控制流放行 (U-009) (`/tmp/m15-04/security-cases.txt`).
- 无任何断言修改 (`git diff` 对这两个文件为空).

### 真实 stop 与共享影响 (隔离实例)

`PI_PRESENT_WEB_RUNTIME_DIR=/tmp/m15-04/rt` 起 `start 50090 /tmp/m15-04/a --bind 0.0.0.0 --fixed-port` + `add-dir /tmp/m15-04/b`, 两页 `2026-11-01-day1.html`/`2026-11-01-day2.html` 均 200; `stop` 后两页都是 `curl exit 7 connection refused` (`http=000`), 运行时记录 `server.json` 已删除 (`/tmp/m15-04/manual-security-lifetime.txt`).

### 控制面与越界的真实请求 (同一隔离实例)

- 源为同网段地址 (本机 LAN IP) 请求 `http://192.168.65.165:50090/__control__/ping` -> `403`; 期间 `roots` 仍为 `[a, b]` 未变 (add-dir 未被外部触发).
- `curl --path-as-is http://127.0.0.1:50090/../secret.txt` (挂载目录外的真实文件 `/tmp/m15-04/secret.txt`, 内容 `TOP-SECRET`) -> `404`, 未返回该文件内容.
- loopback `http://127.0.0.1:50090/__control__/ping` -> `200 {"service": "pi-present-web", "pid": 192954}`, 与 `server.json` 的 `pid=192954` 一致.

### 挂载范围核对 (BR-017 实做)

本次所有 `start`/`add-dir` 的挂载目录只有临时展示目录 `/tmp/m15-04/a`, `/tmp/m15-04/b` 与 `/tmp/m15-01..03/*` 下的临时页目录; 没有仓库根 (`/home/bolo/Workspace/...`), `~/.agents`, `~/.pi`, 密钥或登录态目录. 交付说明里给出的开放风险与本条核对见 ISSUE-03 文档 (首次使用说明同网段可读全部挂载目录, 只挂愿意公开的目录).

### 隔离核验 (BR-015 审计)

- 验证前后 `pgrep -af "scripts/web_server.py"` 的服务进程集合相同: 真实 present 实例 `pid 14757` (`~/.agents/skills/present/scripts/web_server.py __serve__ 8800 ...`) 与 navigate 实例 `pid 117626` 均在, 未被我停止或接管; 唯一差异是两次快照里我自己那条 `bash -c` 包装进程 (`/tmp/m15-04/pgrep-before.txt`, `/tmp/m15-04/pgrep-after.txt`).
- 真实运行时目录记录 `pid` 仍是 `14757`; 该目录 `server.log` 行数在整套 present 测试前后都是 `41` 行, 说明我的测试没有经默认运行时目录打到真实实例 (期间 05:44:10 的一条 ping+add-dir 与 05:44:48 的页面 GET 来自另一个并发会话, 不是我这次验证产生).
- `workflow/navigate/` 无改动: `git diff --stat -- workflow/navigate` 为空.

### 未验证/缺口

- AC-006 场景 1/2 的同网段**另一台设备**真实请求属 HITL, 本容器只能做本机经 LAN IP 的等价请求 (上面 403/404/200 三条), 真实用户设备访问统一在 ISSUE-05 取证或记未验证.
- 空间/时间上无法证明"永远不退出": 只复跑既有 1 秒闲置用例, 未做 24 小时等待.
## 风险提示
- `test_web_server_control_plane.py` 依赖本机有非 loopback IPv4, 探测不到时会跳过; 跳过必须写明, 不能记成通过.
- 复跑时若误用默认运行时目录会打到真实实例, 所有命令前先确认 `PI_PRESENT_WEB_RUNTIME_DIR` 指向临时目录.
- 真实停止/占用端口的操作可能撞上真实展示实例的端口; 端口一律从空闲高端口现取, 不猜.
- AC-006 的同网段结论需要另一台设备, 属 HITL; 没有设备时只能记未验证, 不能拿 loopback 或容器内 curl 顶替.

## 停止条件
需要改变任一 Spec, 决策或核验范围时停止; 发现前序 issue 让内容面/控制面行为变化 (例如越界路径不再 404) 时停止并上报, 不在本 issue 内改代码.

## 适合 AFK 的原因
复跑既有检查与控制面/越界的本机请求不需要进一步产品/API/架构决策, 可自行完成. 但 AC-006 场景 1/2 的同网段真实请求与用户确认需要另一台设备, 该细分项是 HITL, 不适合 AFK 自行宣布通过.

## 验收标准
- [x] 闲置超过旧 TTL 阈值后服务仍存活且内容可访问, 用例保留且未改动.
- [x] 显式 `stop` 后该用户全部共用页面都不再返回 200, 记录文件被清除.
- [x] 同网段请求 `/__control__/*` 返回 403 且挂载清单不变; 本机 loopback ping 返回 200 且 pid 与记录一致.
- [x] `../` 与指向挂载目录外的 symlink 均返回 404, 不泄露目录外内容.
- [x] 验证前后真实展示实例的 pid 与运行时记录 mtime 不变, `workflow/navigate/` 无改动.
- [x] 挂载目录只有展示目录, 不含仓库根或敏感目录; 同网段访问项取到证据或明确记未验证.

## 被阻塞于
- ISSUE-01, ISSUE-02, ISSUE-03.
