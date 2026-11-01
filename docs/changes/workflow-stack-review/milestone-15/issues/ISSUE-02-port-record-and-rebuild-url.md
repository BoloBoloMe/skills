## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成

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
执行后填写: 命令, 退出码, 新增用例名与断言要点, 人工核验的命令与脱敏输出, 复跑了哪些既有用例, 记录 `server.json` 的脱敏片段 (含 `port`/`bind`/`roots`/`fixed_port`), 材料位置 `/tmp/m15-02/`; 容器真实映射端口访问与两环境真实设备证据留 ISSUE-05.

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
