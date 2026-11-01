## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要交付什么
端口真值与复用/重建的交付一致性:

- `status` 的 `url`/`lan_ip` 由 ISSUE-01 的同一解析入口按记录里的实际端口实时算出, 支持与 `start` 相同的 `--lan-host`; 不额外持久化地址, 不新增第二份端口记录.
- 运行时记录 `server.json` 的 `port` 永远等于实际监听端口; 容器写 8800, 不把宿主映射端口混写进来; 记录字段仍是 `pid`, `port`, `bind`, `roots`, `started_at`, `fixed_port`.
- 复用存活实例时交付 URL 的端口为实例实际端口 (忽略新请求的端口), 新目录按扁平并集挂上; 同目录重复增挂不产生重复项.
- 宿主非锁定实例在 `status` 重建换端口后, 记录 `port`、`status.port`、`status.url` 里的端口与真实监听四处一致, 交 URL 跟着实际端口走; 锁定实例 (容器) 只试原端口, 被占返回 `port_in_use`, 不换口.
- 只在 `status` 存活/重建两条路径都补齐 url, 两条共用同一载荷构造函数, 不留下一条给地址, 一条不给.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`, AC-003, AC-004; BR-001, BR-005, BR-006, BR-007, BR-010.
- Technical: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`, 模块接口 (CLI `status`, 运行时记录 `pi-present-web-<uid>/server.json`), 关键流程 (status 重建), 非功能要求 (记录与交付一致).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D004, D005, D008, D011, F003.

## 允许范围
同全局, 增量: `general/present/scripts/web_server.py` 的 `_status_alive_payload`/`_rebuild_status`/`run_status` 与 `main()` 的 `status` 参数解析; `general/present/tests/test_web_server_lifecycle.py` 新增的 status URL 用例.

## 禁止范围
- 不改端口选择与重试策略 (49152-65534 选端口, 最多 10 次, 锁定实例只试原端口), 不改记录字段集合与 0600/0700 权限, 不改 flock 范围.
- 不改 `_Handler`, 内容面与控制面; 不改 `test_web_server_content.py`, `test_web_server_control_plane.py`, `test_web_server_fixed_port.py`.
- 不把 `SWT_HOST_WEB_PORT` 或任何宿主发布端口写进 `server.json`, 不新增 `port` 文件或第二份真值.

## 代码定位提示
- `general/present/scripts/web_server.py`: `_serve` 的记录写入 (行 701-745), `_status_alive_payload` (行 900), `_rebuild_spawn` (行 908), `_rebuild_status` (行 978), `run_status` (行 1030), `_check_port_available` (行 312), `main()` 的 `status` 分支.
- 既有测试: `general/present/tests/test_web_server_lifecycle.py` 的 `TestTC006StartReuse` (行 141), `TestTC010StatusRebuild` (行 274), `TestTC011StatusRebuildPortTaken` (行 349), `TestTC025BindConflict` (行 807), `TestTC026FilePermissions` (行 848); `general/present/tests/test_web_server_fixed_port.py` (锁定实例只试原端口); `general/present/tests/test_web_server_content.py` (并集/遮蔽/listing).

## 验证契约
- 变更类型: 行为变更.
- 对应范围: `status` 输出新增/补齐的 `url`/`lan_ip`/`address_missing` 与记录端口的一致性; 监听与端口选择机制不变.
- 验证要求/证据: 覆盖 AC-003 与 AC-004 的场景, 并单独验证非功能要求 的两条一致性 (宿主: 记录端口等于交付端口; 容器: 记录 8800, 交付用映射端口且对应监听 8800), 不把两者合写成一条. 既有重建/锁端口/权限行为用复跑证明未回退, 证据里写明复跑的是哪几个既有用例.

## 验证入口
- `uv run python -m pytest general/present/tests`; 通过标准 退出码 0 且无 failed. 新增用例: TC-003 (复用后交付端口为实例实际端口, 清单含两目录), TC-004 (宿主重建换口后记录/`status`/真实请求三方一致), TC-02-01 (容器记录 8800 与交付映射端口分离, 记录里不出现映射端口), TC-02-02 (同一次展示的 `status --lan-host` 与 `start --lan-host` 给同一地址). 新增用例都用临时 `PI_PRESENT_WEB_RUNTIME_DIR` 与独立端口, 不碰真实实例.
- 人工核验 (宿主重建全过程): 起实例 -> 记 `server.json` 的 `port` -> 杀子进程 -> 占用原端口 -> 跑 `status --lan-host <已确认地址>`; 通过标准 新端口在 49152-65534 且不同于原端口, `status.port` 等于记录里的 `port`, `status.url` 端口等于该端口, 请求该 URL 返回 200, 记录里 `pid` 是新进程. 命令与输出留证据.
- 人工核验 (复用): 在隔离运行时目录挂两个目录后重复 `start` 同一目录; 通过标准 `roots` 不出现重复项, 交付 URL 与之前相同, 端口不变.
- 复跑既有用例: `test_web_server_lifecycle.py` 的复用/重建/bind_conflict/权限用例, `test_web_server_fixed_port.py` 的锁定实例用例, `test_web_server_content.py` 的并集与遮蔽用例; 通过标准 全部通过且未改断言.
- 条件回归: 本 issue 不触碰 `_Handler` 类属性与静态内容服务行为, 依据 `TECHNICAL.md` 接缝与依赖 的跨 skill 依赖条, `uv run python -m pytest workflow/to-spec/tests/test_ac_draft.py` 免跑; 若实现中必须改 `_Handler`, 停下写明并把该用例纳入检查.
- 通过标准 (整体): 上述每条断言成立; 记录里 `port` 与实际监听一致; 容器场景记录不出现宿主映射端口.

## 交付证据

## 交付证据

环境: 容器内 (本会话), Python 3.11.2 / pytest 9.1.1. 原始输出 `/tmp/m15-02/`.
说明: `status` 的 `url`/`lan_ip` 与 `--lan-host` 传递复用 ISSUE-01 的同一解析入口, 该实现与 ISSUE-01 同提交 (`4fa9869`); 本 issue 提交补上端口/记录/交付一致性的专门用例与本节证据.

### 实现要点 (无新增独立代码路径)

- `_status_alive_payload(data, rebuilt, lan_host)` 同时服务存活路径与重建路径, 内部调 `_apply_delivery`, 两条路径都出 `url`/`lan_ip`/`address_missing`, 不留一条缺地址.
- `run_status(lan_host)` -> `_rebuild_status(..., lan_host)` -> `_rebuild_spawn(..., lan_host)` 把同一次展示的显式地址传到重建路径, 不写进 `server.json`.
- 记录字段与写入逻辑 (`_serve`), 端口选择, 重建重试, 锁端口, 0600/0700 权限一律未改.

### 测试命令与结果

- `uv run python -m pytest general/present/tests -q` -> `5 failed, 154 passed, 5 skipped` (改前基线 `5 failed, 137 passed, 1 skipped`; 5 条失败仍是改前既有的 `test_browser_session.py` 环境失败) `/tmp/m15-02/after-issue02-testrun.txt`.
- 本次新增用例 `uv run python -m pytest general/present/tests/test_web_server_lifecycle.py -q` -> `23 passed, 4 skipped` (4 skip = 宿主分支 CLI 用例, 容器内不可复现).
- 既有端口/内容/生命周期套件复跑 `uv run python -m pytest general/present/tests/test_web_server_fixed_port.py general/present/tests/test_web_server_content.py general/present/tests/test_web_server_lifecycle.py -q` -> `41 passed, 4 skipped`, 断言未改动 (`/tmp/m15-02/regression-existing.txt`).

新增用例:

- `TestTC003ReuseDeliveryPort::test_reuse_keeps_instance_port_and_roots` (TC-003): 复用存活实例后 `reused=true`, 交付 URL 端口 = 实例实际端口 (忽略请求端口), `roots` 两目录保序, 同一目录重复增挂不新增项且 URL 不变.
- `TestTC004StatusRebuildDeliveryUrl::test_rebuild_on_new_port_keeps_record_url_and_listener_in_sync` (TC-004): 杀子进程 + 占原端口后 `status` 重建, 新端口在 49152-65534 且不同于原端口, `record.port == status.port == status.url 端口 == 实际监听`, `record.pid` 为新进程, 该 URL 请求 200.
- `TestTC004StatusRebuildDeliveryUrl::test_status_accepts_lan_host_and_matches_start_url` (TC-02-02): 同一次展示的 `start` 与 `status` 给同一交付地址 (容器内用注入 `SWT_HOST_LAN_IP`/`SWT_HOST_WEB_PORT`, 宿主用 `--lan-host`).
- `TestTC001ContainerDelivery::test_container_url_uses_host_address_and_mapped_port` (TC-02-01): 容器分支交付 URL 用映射端口, `server.json` 的 `port` 是监听端口且记录文本里不出现映射端口号.

### 人工核验

- 宿主重建全过程 (容器内用 loopback bind 与隔离运行时目录做同一链路; 交付地址解析差异由 ISSUE-01 用例覆盖): `start 50081 /tmp/m15-02/page --bind 127.0.0.1` -> `server.json` `pid=186552 port=50081`; `kill -9 186552` 并占住 50081 后 `status` -> `rebuilt=true, pid=186602, port=57548, url=http://localhost:57548/`; `server.json` 同步为 `pid=186602 port=57548`; `curl http://127.0.0.1:57548/f.txt` -> `rebuild-probe` 200 (`/tmp/m15-02/manual-rebuild.txt`).
- 复用 + 同目录幂等 + 容器分支交付地址 (注入 `SWT_HOST_LAN_IP=192.0.2.10 SWT_HOST_WEB_PORT=50021`): 1st `start 50084 a` -> `port=50084, url=http://192.0.2.10:50021/`; 2nd `start 50085 b` -> `reused=true, port=50084, roots=[a,b], url` 不变 (带端口差异 warning); 3rd `start 50085 a` -> `roots=[a,b]` 无重复项, `url`/`port` 不变; 顶层 listing 含 `day1.html` 与 `day2.html` (`/tmp/m15-02/manual-reuse.txt`).
- ACL-004 容器场景的 `8800` 字面端口本容器无法实测: 容器内 8800 已被真实 present 实例占用 (pid 14757, 安装版 skill 起的服务), 停止/接管它违反隔离要求, 故用等价的高端口做记录/映射分离验证; 该条按本说明记为"等价端口验证 + 8800 未实测缺口".

### 未验证缺口

- 容器 `8800` 被占时 `port_in_use` 且不换端口: 现状 8800 已被真实实例占用, 不能在不接管真实实例的前提下复现; 锁定实例只试原端口的行为由既有 `test_web_server_fixed_port.py` 复跑承接 (断言未改), 真 8800 占用未实测.
- 宿主 `--lan-host` 在重建路径的 CLI 端到端未在本容器跑 (宿主分支不可复现), 只由 `_rebuild_spawn(..., lan_host)` 传参与显式入参解析用例间接覆盖.
## 风险提示
- `_status_alive_payload` 同时服务存活路径与重建路径, 只补一条会让另一条没有 url; 两条都要走同一解析入口.
- 容器场景有两份端口 (记录 8800 与交付映射端口), 容易在 `status` 里把映射端口写回记录或反过来把 8800 拼进交付 URL, 两侧断言要分开写.
- 改动 `_serve` 的记录写入会牵动 `TestTC026FilePermissions` 与重建指纹校验 (行 415 的 `TestR1RebuildReadyFingerprint`), 非必要不动它.

## 停止条件
需要改变记录字段集合或端口选择规则, 需要新增第二份端口真值, 需要改 PRODUCT/TECHNICAL/决策, 或需要先编造容器映射端口才能继续时停止.

## 验收标准
- [ ] 复用存活实例后交付 URL 端口为实例实际端口, `roots` 同时含两目录且无重复项.
- [ ] 宿主重建换端口后记录 `port`, `status.port`, `status.url` 端口与真实监听四处一致, 该 URL 请求返回 200.
- [ ] 残留记录在服务已死时按原挂载清单保序重建, 新记录 `pid` 为新进程.
- [ ] 容器场景记录 `port` 为 8800 且记录里不出现宿主映射端口, 交付 URL 端口为映射端口.
- [ ] 宿主首启端口被占返回 `port_in_use` 且不换端口自行重试; 锁定实例在原端口被占时只报错不换口.
- [ ] 记录仍含六项字段, 权限仍为 0600, 运行时目录仍为 0700.
- [ ] `uv run python -m pytest general/present/tests` 退出码 0 且无 failed.

## 被阻塞于
- ISSUE-01.
