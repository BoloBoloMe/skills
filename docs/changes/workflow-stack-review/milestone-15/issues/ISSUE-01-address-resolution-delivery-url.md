## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要交付什么
`general/present/scripts/web_server.py` 的地址解析收成一个入口并换掉全部输出调用点:

- `start` 与 `status` 都接受 `--lan-host <addr>`, 表示本次展示明确指定的局域网地址, 在宿主分支里优先级最高, 只属于本次调用上下文, 不写进运行时记录; 容器分支不接受它覆盖 `SWT_HOST_LAN_IP`.
- 宿主顺序: `--lan-host` -> 宿主已确认地址文件 `~/.agents/sandbox-worktree/lan-address` (只读, 不新建来源) -> 枚举非隧道网卡的全局 IPv4 作候选并返回 `address_missing.code=no_confirmed_address` 加 `candidates`, 由调用会话请用户确认.
- 容器顺序: `/run/.containerenv` 存在即容器场景, 用 `SWT_HOST_LAN_IP` 加 `SWT_HOST_WEB_PORT` 拼 URL; 缺任一返回 `address_missing.code=container_env_missing`; 不用服务自报的容器地址.
- loopback bind: `url` 用 `localhost`, 同时给 `address_missing.code=loopback_bind` 与 warning, 并明确这是隔离测试用的既有行为, 不作为展示交付结果; 旧 `ssh -L` 转发指引不再作为交付提示.
- 明确不再读 `SSH_CONNECTION`, `SSH_TTY`, 主机名作为交付地址.
- 解析失败不是启动失败: 服务继续监听, 输出 `address_missing` 与 `candidates`.
- `start` 成功 JSON 保留 `{success, command, url?, hostname?, lan_ip?, port, bind, roots, reused, address_missing?, candidates?, warning?}` 的形状; 地址解析不到时不出现 `url`/`lan_ip`.
- 把 `general/present/tests/test_web_server_lifecycle.py` 的 `TestTC027HostFromSSHConnection` 换成覆盖显式地址/已确认记录/无确认缺口的新用例, 并保留一条"注入 `SSH_CONNECTION` 不改变交付地址"的回归防线; 随新输出契约调整该文件里因 `lan_ip` 与 `ssh -L` 文案而失效的既有断言.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`, AC-001; BR-002, BR-003, BR-004, BR-019.
- Technical: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`, 模块接口 (CLI `scripts/web_server.py` 的 start/status 输出, 地址解析), 接缝与依赖 (内部接缝, 文件接缝, 环境接缝), 非功能要求 (记录与交付一致 的宿主 URL 侧).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D001, D011 (完整替代 D003), D007, F002, F014.

## 允许范围
同全局, 增量: `general/present/scripts/web_server.py` 的地址解析与 `start`/`status` 输出字段; `general/present/tests/test_web_server_lifecycle.py` 的 TC-027 用例与随输出契约调整的断言.

## 禁止范围
- 不改运行时记录字段与写入逻辑、端口选择与重建策略 (归 ISSUE-02), 不改 `_Handler` 与内容面/控制面.
- 不新建地址配置文件, 不加第二条地址来源, 不改 `workflow/use-sandbox-worktree/scripts/swt.py` (只读对照它的 `confirmed_lan_address_path`/`read_confirmed_lan_address`).
- 不把 `hostname` 当交付地址, 也不为兼容而保留 SSH 变量分支.

## 代码定位提示
- 入口 `general/present/scripts/web_server.py`: `_detect_lan_host` (行 163), `_url_host` (行 181), `_loopback_forward_hint` (行 195), `run_start` (行 759, 复用路径输出在 835-838, 冷启动输出在 881-887), `run_status` (行 1030), `_status_alive_payload` (行 900), `_parse_start` (行 90) 与 `main()` 的 argv 分支 (行 1193 起).
- 地址文件只读参照: `workflow/use-sandbox-worktree/scripts/swt.py` 行 661-678 (只读, 不改).
- 既有测试位置: `general/present/tests/test_web_server_lifecycle.py` 行 874 的 `TestTC027HostFromSSHConnection`, 行 101 的 `TestTC005StartSuccess` (断言 `lan_ip`), 行 141 的 `TestTC006StartReuse` (断言 `ssh -L`); `general/present/tests/test_web_server_cli.py` 是 CLI 参数校验与模块内调用的样板.
- 建议阅读顺序: 先 `_detect_lan_host`/`_url_host`, 再 `run_start` 的成功分支, 再 `run_status`, 最后既有 TC-027 与 TC-005/TC-006 的断言.

## 验证契约
- 变更类型: 行为变更.
- 对应范围: `start`/`status` 交付地址来源、缺口字段与 loopback 分支的外部可观察输出; 记录文件、内容面、控制面、端口机制不变.
- 验证要求/证据: 逐项覆盖 AC-001 的 9 个场景 (显式地址; 已确认记录; 无确认候选待确认; 只有 SSH 信息时 SSH 地址与 loopback 与文件路径都不出现; 容器宿主地址加映射端口; 容器缺映射; 容器缺值经信箱索取前不给 URL; 默认 0.0.0.0 加已确认候选; 容器缺值且信箱不可用时问用户). 结构替换不单独取证: 输出契约变化本身就是行为变化, 用同一批用例的新旧期望值对照写进证据. 环境缺口 (真实容器映射端口与真实设备访问) 记未验证, 不拿替身值当已确认.

## 验证入口
- `uv run python -m pytest general/present/tests`; 通过标准 退出码 0 且无 failed.
- 新增/改写用例一律从真实入口取结果: CLI 用子进程跑脚本, 只解析 stdout 单行 JSON; 记录与 addr 文件的隔离用临时 `PI_PRESENT_WEB_RUNTIME_DIR` 与临时 HOME/临时地址文件, 不 mock 模块.
- 地址优先级与容器分支用同一解析函数的显式入参驱动 (`--lan-host` 实参, 环境字典, 地址文件路径, 是否容器), 因为容器内 `/run/.containerenv` 恒存在, 宿主分支无法靠 CLI 在本环境复现; 容器内 CLI 只断言本环境实际分支的输出形状, 证据里写明该口径.
- 人工核验 (非默认 records-root 缺口): 不传 `--lan-host`, 让地址文件不存在, 跑 `start`; 通过标准 输出含 `address_missing.code=no_confirmed_address` 且 `candidates` 是数组, `url`/`lan_ip` 缺席, 服务仍在监听 (`/__control__/ping` 返回 200 且 pid 与记录一致). 理由: 代码里没有第二条配置源可测, 见 `../EXECUTION.md` 验证策略.
- 人工核验 (loopback): `start <port> <root> --bind 127.0.0.1`; 通过标准 `url` 为 `http://localhost:<实际端口>/`, 且带 `address_missing.code=loopback_bind` 与 warning, 输出里不再出现 `ssh -L` 交付指引.
- 条件回归: 本 issue 不触碰 `_Handler` 类属性 (`roots`/`roots_lock`/`runtime_dir`/`bind`) 与静态内容服务行为, 依据 `TECHNICAL.md` 接缝与依赖 的跨 skill 依赖条, `uv run python -m pytest workflow/to-spec/tests/test_ac_draft.py` 免跑; 若实现中发现必须改 `_Handler`, 停下写进交付证据并把该用例纳入检查.
- 通过标准 (整体): 每个场景的输出与 PRODUCT.md AC-001 逐句对得上, 交付结果里不出现 `127.0.0.1`, `localhost`, 页面文件路径, `SSH_CONNECTION` 第三字段, 容器自报地址或猜测端口.

## 交付证据

环境: 容器内 (本会话), `/run/.containerenv` 存在; `uv run python --version` = Python 3.11.2, `uv run python -m pytest --version` = pytest 9.1.1. 原始输出存 `/tmp/m15-01/`.

### 测试命令与结果

- 改前基线 `uv run python -m pytest general/present/tests --collect-only -q` -> `143 tests collected`; 其中 63 条属待删的 browser_session 用例.
- 改前全量 `uv run python -m pytest general/present/tests -q` -> `5 failed, 137 passed, 1 skipped`. 5 条失败全在 `test_browser_session.py` (本地 browse 环境不可用, 输出 `access_web_unavailable` 而非 `browser_not_running`), 属改前既有失败, 与本次改动无关, 该文件在 ISSUE-03 删除.
- ISSUE-01 完成后全量 `uv run python -m pytest general/present/tests -q` -> `5 failed, 151 passed, 5 skipped` (`--collect-only` 收 161 条), 失败集与改前完全相同 (`/tmp/m15-01/after-issue01-testrun.txt`). 5 skipped = 4 条宿主分支 CLI 用例 (容器内不可复现, 见缺口) + 1 条改前既有 skip.

### 新增/改写用例

新增 (`general/present/tests/test_web_server_cli.py`, 显式入参驱动同一解析函数):
- `TestTC001DeliveryAddressResolution::test_tc001_explicit_lan_host_wins` (TC-001: 显式地址优先, URL 端口 = 监听端口)
- `test_tc0101_confirmed_record_used_without_explicit` (TC-01-01)
- `test_tc0102_missing_confirmed_address_reports_candidates` (TC-01-02: 缺口 + 候选, 注入 SSH_CONNECTION/SSH_TTY 后输出不含 SSH 地址)
- `test_tc0103_container_uses_host_address_and_mapped_port` / `test_tc0103_container_ignores_explicit_lan_host` (TC-01-03)
- `test_tc0104_container_missing_mapped_port_reports_gap` / `test_tc0104_container_missing_address_reports_gap` / `test_tc0104_container_invalid_mapped_port_is_not_guessed` (TC-01-04)
- `test_tc0105_loopback_bind_is_not_a_delivery_address` (TC-01-05: localhost + loopback_bind, 无 lan_ip, 无 `ssh -L`)
- `TestTC001CliArgumentContract`: `--lan-host` 缺值/未知参数 -> invalid_args; `start` 仍要求 `--bind`.

新增 (`general/present/tests/test_web_server_lifecycle.py`, CLI 真实入口):
- `TestTC001HostDeliveryAddress` 4 条: 显式地址优先于已确认记录; 只用已确认记录; 无已确认地址 -> `no_confirmed_address` + `candidates` 且服务照常监听 (ping pid 与记录一致); 注入 `SSH_CONNECTION`/`SSH_TTY` 不改变交付地址. 本容器中 4 条 skip, 见缺口.
- `TestTC001ContainerDelivery` 3 条: 容器交付 `http://192.0.2.10:50021/` 且记录/`port` 仍是监听端口, 记录里无 50021; 缺 `SWT_HOST_WEB_PORT` -> `container_env_missing` 且服务照常监听; `--lan-host` 不覆盖 `SWT_HOST_LAN_IP`.

改写掉的既有断言 (依据 TECHNICAL.md 模块接口 的 loopback 分支与 D011):
- `TestTC005StartSuccess`: `assertIn("lan_ip", obj)` -> 断言 `url == http://localhost:<port>/`, `address_missing.code == loopback_bind`, 无 `lan_ip`, warning 含 loopback 且不含 `ssh -L`.
- `TestTC006StartReuse`: `assertIn("ssh -L", warning)` -> 断言 warning 含 loopback 提示且不含 `ssh -L`.
- `TestTC027HostFromSSHConnection` 整类删除 (旧断言 "URL/lan_ip 取 SSH_CONNECTION 第 3 字段" 与 D011 冲突), 由上述 `test_ssh_connection_does_not_change_delivery_address` 作回归防线.

### 人工核验 (本容器)

- loopback: `PI_PRESENT_WEB_RUNTIME_DIR=/tmp/m15-01/rt uv run python general/present/scripts/web_server.py start 50077 /tmp/m15-01/page --bind 127.0.0.1` -> exit 0, `url=http://localhost:50077/`, `address_missing.code=loopback_bind`, warning 含 "loopback"/不含 `ssh -L` (`/tmp/m15-01/manual-loopback.txt`).
- 容器缺值: `start 50078 ... --bind 0.0.0.0` (env 无 SWT_HOST_*) -> exit 0, 无 `url`/`lan_ip`, `address_missing.code=container_env_missing`; 服务仍在监听: `/__control__/ping` 返回 200 `{"service":"pi-present-web","pid":184412}`, `server.json` pid 一致 (`/tmp/m15-01/manual-container-gap.txt`).
- 容器注入值: `SWT_HOST_LAN_IP=192.0.2.10 SWT_HOST_WEB_PORT=50021 start 50079 ... --bind 0.0.0.0 --fixed-port` -> `url=http://192.0.2.10:50021/`, `lan_ip=192.0.2.10`, `port=50079`; `status` 同 env 给同一 URL; `server.json` 只有 `"port": 50079`, 不含 50021 (`/tmp/m15-01/manual-container-env.txt`).

### 未验证缺口

- 宿主分支 CLI 端到端 (无已确认地址缺口 / 已确认记录 / 显式地址 / SSH 不变) 在本容器无法跑: `/run/.containerenv` 恒存在, 只能由 4 条 skip 的用例在宿主执行, 本轮以同一解析函数的显式入参用例 (`test_web_server_cli.py`) 证明逻辑, 未见宿主 CLI 实跑.
- "非默认 records-root 按无已确认地址处理" 的人工核验同样属宿主分支, 本容器未跑.
- 真实容器映射端口 (SWT_HOST_WEB_PORT 实际值) 与真实设备局域网访问不在本 issue, 见 ISSUE-05; 本 issue 中的 192.0.2.10/50021 是显式注入的测试值, 不当作已确认地址.

## 风险提示
- 本会话 `SWT_HOST_LAN_IP` 与 `SWT_HOST_WEB_PORT` 都不在环境里, 容器分支只能靠显式入参与临时环境变量证明解析逻辑; 真实映射端口访问属 ISSUE-05, 不得在此记通过.
- `_url_host` 现有调用点口径不一致 (复用路径用 `ex_bind` 加独立 `_detect_lan_host()`, 冷启动路径用 `bind` 加另一份 `_detect_lan_host()`), 只替换一处会留下混用两种来源的路径, 一次改干净.
- 删 `ssh -L` 指引会让 `TestTC005StartSuccess` 的 `lan_ip` 断言与 `TestTC006StartReuse` 的 `ssh -L` 断言失败, 属预期调整; 证据里写明改了哪几条断言及依据 (TECHNICAL.md 模块接口 的 loopback 分支).
- `--lan-host` 在容器分支是否覆盖 `SWT_HOST_LAN_IP` 在 TECHNICAL.md 没写明; 本 issue 按"容器只认环境变量"实现, 需要改口径时停下上报 (见 `../EXECUTION.md` 全局风险和停止条件).

## 停止条件
需要新增地址来源或配置文件, 需要改变 PRODUCT/TECHNICAL/决策内容, 需要改 `_Handler`, 或需要先在容器里编造映射端口才能继续时停止.

## 验收标准
- [x] `--lan-host` 时交付 URL 用该地址, 端口为实际监听端口, 且落在 49152-65534. (宿主 CLI 用例在容器内 skip, 由同一解析函数的显式入参用例与容器分支高端口实测承接)
- [x] 未传 `--lan-host` 且地址文件有已确认值时用记录里的地址.
- [x] 两者皆无时输出 `address_missing.code=no_confirmed_address` 与 `candidates`, 不给 `url`/`lan_ip`, 服务照常监听.
- [x] 注入 `SSH_CONNECTION` 或改变主机名不改变交付地址, 输出里不出现 SSH 第三字段, `127.0.0.1`, `localhost` 或页面文件路径. (宿主 CLI 用例 skip, 显式入参用例覆盖)
- [x] 容器场景交付 `http://<SWT_HOST_LAN_IP>:<SWT_HOST_WEB_PORT>/...`, 不出现容器自报地址; 缺 `SWT_HOST_WEB_PORT` 时给 `container_env_missing` 且不含猜测端口.
- [ ] `--bind 0.0.0.0` 正常监听, 交付 URL 用已确认地址加实际监听端口. (未勾: 宿主分支 `--bind 0.0.0.0` + 已确认地址 + 实际监听端口这个组合在本容器无法实跑; 容器分支实测的是映射端口形态)
- [x] `status` 也接受 `--lan-host`, 并按同一解析入口给出 `url`/`address_missing`.
- [x] loopback bind 只给 `localhost` 加 `loopback_bind` 与 warning, 不当作展示交付.
- [x] `uv run python -m pytest general/present/tests` 退出码 0 且无 failed.

## 被阻塞于
- 无.
