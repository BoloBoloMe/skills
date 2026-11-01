## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成

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
执行后填写: 实际命令与退出码, 每个场景的脱敏输出, 改动与新增的用例名, 调整掉的既有断言及理由, 人工核验输出, 材料位置 `/tmp/m15-01/`; 真实容器映射端口与真实设备访问留 ISSUE-05, 在此如实记缺口.

## 风险提示
- 本会话 `SWT_HOST_LAN_IP` 与 `SWT_HOST_WEB_PORT` 都不在环境里, 容器分支只能靠显式入参与临时环境变量证明解析逻辑; 真实映射端口访问属 ISSUE-05, 不得在此记通过.
- `_url_host` 现有调用点口径不一致 (复用路径用 `ex_bind` 加独立 `_detect_lan_host()`, 冷启动路径用 `bind` 加另一份 `_detect_lan_host()`), 只替换一处会留下混用两种来源的路径, 一次改干净.
- 删 `ssh -L` 指引会让 `TestTC005StartSuccess` 的 `lan_ip` 断言与 `TestTC006StartReuse` 的 `ssh -L` 断言失败, 属预期调整; 证据里写明改了哪几条断言及依据 (TECHNICAL.md 模块接口 的 loopback 分支).
- `--lan-host` 在容器分支是否覆盖 `SWT_HOST_LAN_IP` 在 TECHNICAL.md 没写明; 本 issue 按"容器只认环境变量"实现, 需要改口径时停下上报 (见 `../EXECUTION.md` 全局风险和停止条件).

## 停止条件
需要新增地址来源或配置文件, 需要改变 PRODUCT/TECHNICAL/决策内容, 需要改 `_Handler`, 或需要先在容器里编造映射端口才能继续时停止.

## 验收标准
- [ ] `--lan-host` 时交付 URL 用该地址, 端口为实际监听端口, 且落在 49152-65534.
- [ ] 未传 `--lan-host` 且地址文件有已确认值时用记录里的地址.
- [ ] 两者皆无时输出 `address_missing.code=no_confirmed_address` 与 `candidates`, 不给 `url`/`lan_ip`, 服务照常监听.
- [ ] 注入 `SSH_CONNECTION` 或改变主机名不改变交付地址, 输出里不出现 SSH 第三字段, `127.0.0.1`, `localhost` 或页面文件路径.
- [ ] 容器场景交付 `http://<SWT_HOST_LAN_IP>:<SWT_HOST_WEB_PORT>/...`, 不出现容器自报地址; 缺 `SWT_HOST_WEB_PORT` 时给 `container_env_missing` 且不含猜测端口.
- [ ] `--bind 0.0.0.0` 正常监听, 交付 URL 用已确认地址加实际监听端口.
- [ ] `status` 也接受 `--lan-host`, 并按同一解析入口给出 `url`/`address_missing`.
- [ ] loopback bind 只给 `localhost` 加 `loopback_bind` 与 warning, 不当作展示交付.
- [ ] `uv run python -m pytest general/present/tests` 退出码 0 且无 failed.

## 被阻塞于
- 无.
