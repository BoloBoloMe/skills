## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成
- [ ] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.

## 要交付什么
让 `serve` 的输出成为唯一可交付的东西 (调用会话只转述, 不自己拼):

- 地址解析 (逻辑放 `codemap_common.py`, 由 `serve` 消费): 顺序为 `--address` 实参 -> `~/.agents/sandbox-worktree/lan-address` 有值就用 -> 否则枚举非隧道全局 IPv4 作为 `candidates` 并给 `address_missing.code == "no_confirmed_address"`. 明确不采 `SSH_CONNECTION`, 主机名, `localhost`, 服务自报地址. `--address` 只作用于本次调用, 不写 `state.json`, 不新建配置文件, 不回写 swt 的 `lan-address`.
- `serve --json` 补齐字段: `{success, command, url?, base_url?, port, bind, reused, pid?, serve_root, port_changed?, previous_url?, address_source?, keys:[{key, url?, built_at, bytes}], delivery_notes:{level_hint, integrity_note, denominator_note}, address_missing?:{code, message}, candidates:[addr...]}`. 默认人类可读模式给同一份数据.
- 地址解析成功 (含 `--address` 传入的确认值): 给 `url` 与 `base_url`, `keys` 每项带完整可点 URL, `address_source` 标明取自记录文件还是本次参数.
- 地址解析失败且未传 `--address`: 不给 `url`/`base_url`, `keys` 每项只给 `key`; 人类可读模式首行写 `BLOCKED: 缺已确认局域网地址`; 退出码仍为 0 (服务已起, 阻断的是交付而不是启动).
- `keys` = `state.json.data_keys` 与 `serve_root` 里实际 `.cc.json` 文件的交集, 输出前逐个核文件存在; 记录里有而磁盘缺失的键不进 `keys` 并提示; 磁盘上有而记录里没有的 (手工放入) 只提示存在未登记文件, 不自动收编.
- `delivery_notes` 是交付消息的唯一内容来源: `level_hint` = 层号/环/向上依赖在官方依赖视图看; `integrity_note` = 依赖抽取完整性未量化; `denominator_note` = 本次依赖树文件数与分母口径 (来自 ISSUE-03 的统计). 字段语义不得丢.
- `port_changed` 与 `previous_url` 只在本次通过 `serve --port` 显式换端口时出现, 用于报告旧地址已失效.
- 交付一致性: 输出的 `url` 端口等于 `state.json.port` 等于实际监听端口; `keys[].key` 等于磁盘文件名; `keys[].url` 由同一地址与同一键拼成.
- 新测试树补本 issue 用例 (临时 `HOME` 里放或不放 `lan-address`, 隔离运行时目录与临时端口).

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-008 (有确认地址交付局域网 URL; 没有确认地址报阻塞; 确认后 `serve --address` 重新交付), AC-003 (换端口场景里"输出明确报告旧地址已失效"那条), AC-006 (交付消息带三类说明), AC-002 (完整 URL 形状); BR-004 (换端口报告), BR-019, BR-020, BR-023, BR-024 (交付侧), BR-027 (serve/stop 不做网络动作), BR-030 (提示口径), BR-037; G-002, G-005, NG-003.
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 模块接口 (CLI `serve` 一节, `serve --json` 字段, 地址解析 全节), 关键流程 (serve 启动/复用), 非功能要求 (交付一致性), 安全策略 (传输与访问).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D002, D006, D016, D017, D018, D020, F002.
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D007, D011, D012.

## 允许范围
同全局, 增量: `codemap_common.py` 的地址解析, `codemap_service.py` 的输出组装 (只加输出层, 不改 04 的启停与探活), `codemap_analyze.py` 只读取统计值供 `denominator_note`, 本 issue 的测试.

## 禁止范围
- 不改 04 的探活, 端口决策, 锁, stop 语义与 HTTP 面; 若需要改动先停下报告.
- 不猜地址: 不用 `SSH_CONNECTION`, 主机名, `localhost`, 127.0.0.1 或容器 IP 顶替; 不给占位 URL.
- 不把 `--address` 或解析结果落盘, 不新建地址配置文件, 不回写 `~/.agents/sandbox-worktree/lan-address`.
- 不改写 `delivery_notes` 里的数字与判断 (尤其不得改成"分层可信"), 不在调用会话侧自行拼 URL.
- 不自动收编磁盘上未登记的 `.cc.json`, 不删除任何副本.

## 代码定位提示
- 地址解析写在 `codemap_common.py` (与键, 排除集同为共享纯函数), 由 `codemap_service.py` 的 `serve` 输出段消费; 路径规则参照 `workflow/use-sandbox-worktree/scripts/swt.py` 的 `confirmed_lan_address_path` / `read_confirmed_lan_address` (records_root 默认 `~/.agents/sandbox-worktree`), 只读不写.
- 既有形状参照: `general/present/scripts/web_server.py` 的 `_detect_lan_host` / `_url_host` / `_apply_delivery` 三段式 (地址来源优先级与缺口输出), 以及 `workflow/navigate/scripts/web_server.py` 的摘要输出.
- 测试隔离: 用 `monkeypatch` 或 `subprocess` 的 `env` 把 `HOME` 指到 `tmp_path`, 在 `<HOME>/.agents/sandbox-worktree/lan-address` 里放或不放地址; 不新增配置源.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: 地址解析与缺口, `serve` 输出字段与文案, `keys` 交集与提示, `delivery_notes`, 交付一致性.
- 验证要求/证据: 覆盖 AC-008 三条场景与 AC-002 的 URL 形状, 并单独验证非功能要求 交付一致性; 缺地址时退出码必须为 0 (服务已起) 且不出现 `url`; 证据为 pytest 输出加一份手工 `serve` 的 JSON 与人类可读两形态摘录 (放 `/tmp/m25-05/`, 地址用脱敏占位说明).
- BR-027 的 serve/stop 侧不写自动化: 用人工核验 (本容器无出网, `serve` 仍成功且 `keys` 齐全; 加代码核对 `codemap_service.py` 不 import 网络模块, 不调 podman) 承接.

## 验证入口
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 本 issue 新增用例:
  - TC-008 (AC-008 主用例): 临时 `HOME` 里有已确认地址 + 两份数据副本时, `serve` 输出的 `base_url` 与每个 `keys[].url` 用该地址加实际端口拼成, `?file=<键>` 形状正确, 输出里没有回环地址/主机名/文件路径.
  - TC-05-01 (AC-008 缺地址): 临时 `HOME` 里没有 `lan-address` 且不传 `--address`, 退出码 0, 无 `url`/`base_url`, `keys` 每项只有 `key`, `address_missing.code == "no_confirmed_address"`, `candidates` 非空且全为 IPv4 字面量 (不含 `127.0.0.1`/`::1`/`localhost`), 人类可读模式首行含 `BLOCKED`.
  - TC-05-02 (AC-008 确认后): 承上, 再跑 `serve --address <候选地址>`, 输出带完整 URL 且 `address_source` 标明来自本次参数; 断言 `state.json` 里没有该地址, `lan-address` 文件内容未变.
  - TC-05-03: `keys` 交集口径: 记录与磁盘都有的键进 `keys`; 记录有磁盘缺的键不进 `keys` 且有提示; 磁盘有记录没有的 `.cc.json` 只提示"存在未登记文件", 不进 `keys` 且不改 `state.json`.
  - TC-05-04: `delivery_notes` 三类说明齐全且 `denominator_note` 里的文件数等于最近一次 build 统计的依赖树文件数; 显式换端口时 `port_changed == true` 且 `previous_url` 等于停机前记录的 URL, 不带 `--port` 时两者不出现.
  - TC-05-05: 交付一致性: `url` 端口 == `state.json.port` == 实际监听端口; `keys[].key` == `serve_root` 里实际文件名; `keys[].url` 里的键与地址与 `base_url` 同源.
- 人工核验 (BR-027 服务侧): 在无出网的本容器里起 `serve`, 通过标准 服务成功, `keys` 与说明齐全, 全程无网络请求报错; 再核对 `codemap_service.py` 的 import 与调用面不含网络与 podman. 命令与输出留证据.
- 通过标准 (整体): 上述每条成立; 缺地址时服务照常监听 (可用 `GET /` 验证) 且退出码 0.

## 交付证据

## 风险提示
- 用临时 `HOME` 替换地址文件是测试手法, 不是新增配置源; 实现里若为了测试方便读环境变量覆盖地址路径, 就违反了 m14 D011, 会被判为越界.
- `keys` 是交集, 不要用并集或清单原文, 否则删了副本还会交付失效 URL (D020).

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 需要新增地址配置源或让调用会话自拼 URL 时停止并上报.

## 验收标准
- [ ] 有已确认地址时交付局域网基址与每个键的完整 URL, 无回环地址与文件路径.
- [ ] 缺地址时退出码 0, 服务已起, 首行 BLOCKED, 只给键名与候选地址.
- [ ] `--address` 只作用本次, 不落盘, 不回写 swt 记录.
- [ ] `keys` 为清单与磁盘交集, 缺失与未登记两种情况都有提示.
- [ ] `delivery_notes` 三类说明齐全, 数字与判断未改写.
- [ ] `url` 端口与状态记录与实际监听三方一致.

## 被阻塞于
- `ISSUE-03-gate-stats-and-serve-copies.md`
- `ISSUE-04-resident-service-and-state.md`
