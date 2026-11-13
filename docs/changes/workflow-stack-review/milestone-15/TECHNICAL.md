# present 统一局域网交付 Technical Spec

## 模块划分

- `general/present/SKILL.md` (改写) + `general/present/REMOTE.md` (删除): 唯一交付流程文档. 责任: 页面生成要求, 交付前自检, 起或复用常驻展示服务的命令, 地址来源与缺值出口, 生命周期与 stop 影响, 失败出口. 删掉 REMOTE.md 后其宿主/容器规则并入正文同一节, 不再按环境分叉. 改写时保留原有的页面要求: 文件名以当天日期开头且不重复, 新版本另存不覆盖旧文件. 文档模块无删除测试; 删掉 REMOTE.md 后由 `tests/test_skill_contract.py` 固定"只有一条流程"的文本契约. 删除测试判定: 文档不承担实现复杂度, 删掉它不会把复杂度散回调用点, 但会让每个调用会话各自发明交付规则, 所以保留 SKILL.md.
- `general/present/scripts/web_server.py` (改写): 常驻展示服务的唯一实现, 藏住运行时记录与锁, 子进程守护与重建, 端口选择, 对外地址解析, 扁平并集内容面与控制面守卫, 目录校验. 外部接口只是四个子命令加单行 JSON; 调用者不需要知道记录怎么原子写, 子进程怎么回收. 删除测试判定: 删掉它, 起服务/记端口/探活/拼地址的复杂度会散回每个调用会话, 所以保留. 内部结构不变, 只替换地址解析与输出字段: 现行 `_detect_lan_host`/`_url_host` 换成单一解析函数, 其余子模块 (运行时记录, 进程守护, 内容面, 重建) 沿用.
- `general/present/scripts/browser_session.py` (删除): 本地 Chromium 打开与状态回读的实现. 删除后无残留引用 (SKILL.md, 测试, README 一并改).
- `general/present/scripts/check_page.py` (沿用, 不改): 页面静态自检. 已核对它不检查 `__PRESENTATION_STATE__` (milestone-14 F004), 取消状态对象强制要求不需要动它; 本次不为清单虚改.
- `general/present/tests/` (改): 行为与文本契约回归. 删 `test_browser_session.py`, `test_browser_session_integration.py`; 改 `test_skill_contract.py`, `test_web_server_lifecycle.py` 的 TC-027, 以及固化了本地路径失败出口/`__PRESENTATION_STATE__` 的断言; 新增地址来源优先级, 容器映射, 缺值缺口, 重建后 URL 随实际端口的用例, 直接写进现有测试文件, 不新建测试设施.
- `README.md` (改): present 的技能表行改成统一局域网交付的描述.
- 目录边界: `general/present/`, `README.md`. 不碰 `workflow/`, `docs/language/`, 真实安装目录, 其它 skill 的实现.

## 模块接口

### CLI `scripts/web_server.py`

- `start <port> <root> --bind <addr> [--fixed-port] [--lan-host <addr>]`: 起服务或复用存活实例. `--lan-host` 是本次调用明确指定的局域网地址, 优先级最高; 不传则按地址解析顺序取. 成功输出单行 JSON `{success, command, url?, hostname?, lan_ip?, port, bind, roots, reused, address_missing?, candidates?, warning?}`.
  - 地址解析成功: 给 `url`, `lan_ip` 同地址. URL 端口按环境取: 宿主用记录的实际监听端口, 容器用 8800 对应的宿主映射端口 (记录仍写 8800).
  - 地址解析不到: 不给 `url`/`lan_ip`, 给 `address_missing: {code, message}` 和 `candidates` (探测到的候选地址列表, 可能为空), 服务照常运行. `code` 取值: `no_confirmed_address` (宿主无明确指定也无已确认记录), `container_env_missing` (容器缺 `SWT_HOST_LAN_IP` 或 `SWT_HOST_WEB_PORT`). `loopback_bind` 不属于这一族, 见下一条.
  - bind 为 loopback 时: `url` 用 `localhost`, 同时给 `address_missing: {code: loopback_bind}` 与 `warning`. 它是给隔离测试用的既有行为, 调用方不得把它当展示交付结果; status 同样处理.
  - 错误码沿用: `invalid_args`, `port_in_use`, `bind_conflict`, `instance_conflict`, `internal_error`; 退出码 0 成功 / 1 失败, stdout 单行 JSON.
- `status [--lan-host <addr>]`: 探活, 必要时重建. 成功输出 `{success, command, alive, rebuilt, pid, port, bind, roots, started_at, url?, lan_ip?, address_missing?}`. `url`/`lan_ip` 由同一次地址解析实时算出, 不额外持久化地址; URL 端口同样分环境取 (宿主用记录的实际监听端口, 容器用 8800 的宿主映射端口), 记录里的 `port` 永远是监听端口. 同一次展示的 status 与重建必须由调用方传入与 start 相同的 `--lan-host`; 不传时按地址解析顺序退回记录与候选, 因此可能给出与先前交付不同的地址, 调用方不得把两次各自解析的结果混用.
- `stop`: 关闭实例并清运行时文件; 无实例时幂等成功.
- `add-dir <dir>`: 增挂目录, 同目录幂等, 输出当前 `roots` 保序列表.
- 不变式: 同一 uid 单实例; 记录文件 `server.json` 权限 0600, 运行时目录 0700; 所有输出都是 stdout 单行 JSON, 不带额外日志行.

### 地址解析 (脚本内部)

- 输入: `--lan-host` 实参, 进程环境, 宿主已确认地址文件, `/run/.containerenv` 是否存在.
- 宿主顺序: `--lan-host` → 宿主已确认地址文件 `~/.agents/sandbox-worktree/lan-address` (swt 默认 records_root 下的已确认值, 只读, 不新建来源) → 枚举非隧道网卡的全局 IPv4 作候选, 返回 `no_confirmed_address` 由调用会话请用户确认.
- 容器顺序: `/run/.containerenv` 存在即容器场景; 用 `SWT_HOST_LAN_IP` + `SWT_HOST_WEB_PORT` 拼 URL, 缺任一返回 `container_env_missing`; 不使用服务自报的容器地址. 容器分支不接受 `--lan-host` 覆盖: 地址固定取 `SWT_HOST_LAN_IP`, 端口固定取 8800 的宿主映射端口 (D011 把本次明确指定写在宿主规则里, 容器用已确认的注入值).
- `--lan-host` 只属于本次展示的上下文, 不写进运行时记录; 同一展示过程里查询或重建需要再次传入, 由同一个解析入口产出 URL, 调用方不自己拼接两种来源.
- 明确不读 `SSH_CONNECTION`, `SSH_TTY`, 主机名: 它们是旧实现的地址来源, 已确认不能代表用户设备可达.
- 支持范围: 只读默认 records_root 下的已确认地址; swt 使用非默认 records-root 时 present 不扫别处、不另建配置源, 按无已确认地址处理 (候选 + 用户确认), 这一缺口在执行前核实并写进证据.
- 错误模式: 解析失败不是启动失败, 服务继续监听; 缺口信息交给调用会话报给用户.

### 运行时记录 `pi-present-web-<uid>/server.json`

- 字段: `pid`, `port` (实际监听端口), `bind`, `roots` (保序, 重建权威清单), `started_at`, `fixed_port`.
- 写: 子进程启动后原子写; 重建换端口时新子进程重写同一文件, 因此记录始终等于实际监听.
- 读: 记录用 `pid` 指纹探活 (`/__control__/ping`), 残留记录不算存活; 状态重建全程持 flock.
- 覆盖: `PI_PRESENT_WEB_RUNTIME_DIR` 覆盖基目录, 供测试隔离; 生产默认系统临时目录.

### HTTP 面

- 内容面: GET 静态文件与目录 listing, 扁平并集按 `roots` 顺序首个命中; 越界路径 404; 不带认证.
- 控制面: `/__control__/*` 只接受 loopback 来源或源地址等于 `bind` 的请求, 其他 403 且关闭连接.
- 使用方约束: 调用者只通过 CLI 操作, 不直接改运行时文件.

## 接缝与依赖

- 内部接缝: 地址解析函数 (`web_server.py` 内部), 输入是显式参数/环境/文件, 输出是地址或缺口对象. 测试与生产走同一实现, 不注入假模块; 分类: 内部.
- 文件接缝: 宿主已确认地址 `~/.agents/sandbox-worktree/lan-address` (swt 默认 records_root 下的已确认值). 分类: 本地可替换 (测试可用临时 HOME/文件系统替身). 非默认 records-root 不在本次接通范围, 见 模块接口 的支持范围.
- 环境接缝: `SWT_HOST_LAN_IP`, `SWT_HOST_WEB_PORT` 由容器创建流程注入. 分类: 真正外部. 无值时只能报缺口, 不能拿替身值声称已确认.
- 进程接缝: 服务子进程 (`re-exec` 自身). 分类: 进程内/本地可替换, 现有测试已经这样隔离.
- 用户设备访问: 分类: 真正外部, 无法替身. 证据必须是真实客户端请求, 见 非功能要求.
- 跨 skill 依赖 (条件): `workflow/to-spec/tests/test_ac_draft.py` 直接 import `web_server._Handler` 并注入 `roots`/`bind`. 本次若改动 `_Handler` 的类属性或静态服务行为, 该用例纳入直接相关回归; 不触碰时免跑, 并在交付证据写明免跑理由. 不借机重构 to-spec.

## 安全策略

- 传输与访问: 无认证, 无 TLS, 默认监听 0.0.0.0, 已由用户接受; 同网段主体可读全部挂载目录, 因此只挂愿意公开的展示目录, 不挂仓库根或敏感目录, 这是文档与调用纪律, 不靠代码拦截.
- 管理面: 控制面仅本机来源可用 (loopback 或源地址等于 bind); 内容面不带写操作, 不新增远程增挂接口.
- 密钥与数据: 页面不写密钥, Cookie, token 或无关仓库内容; 运行时记录与日志权限 0600, 目录 0700.
- 越界防护: 挂载根必须绝对路径, 存在且是目录; 请求先规范化再判定归属, 逃出任何挂载目录 (含 `../` 与越界 symlink) 返回 404, 落在挂载目录内的规范化路径照常返回, 不把根内的 `sub/../` 也拒掉.
- 隔离: 测试用独立运行时目录与端口, 不停止或接管真实展示实例; 生产实例只通过显式 `stop` 关闭.

## 非功能要求

- 常驻性: 调用结束, 会话断开, 收工均不停止; 不设空闲退出. 验证口径: 闲置超过任何旧 TTL 后服务仍存活且内容可访问 (`test_idle_server_stays_available_until_stop` 保留, 注释说明 `PI_PRESENT_WEB_TTL_SECONDS` 已不再被读取, 该用例是防旧行为复活的保护, 不恢复自退语义).
- 记录与交付一致: 记录里的 `port` 永远等于服务实际监听端口; 宿主交付 URL 用这个 `port`, 容器交付 URL 用 8800 的宿主映射端口且对应监听 8800. 两条一致性分开验证, 不拿交付端口改写记录, 也不建第二份监听端口记录. 验证口径: 宿主重建换端口后 `status` 的 `port`/`url` 与记录、实际请求三者一致; 容器核对记录 `port` 为 8800、交付 URL 端口为映射端口且能打开.
- 两个环境的真实访问证据 (AC-007): 容器场景在容器内 start 后用 `SWT_HOST_LAN_IP` + `SWT_HOST_WEB_PORT` 交付, 宿主场景在宿主侧执行同一命令; 两处都要由用户设备真实打开页面. 计划取证: 用户确认看到内容, 加 `server.log` 中能与本次页面/时间对上的请求行; 若映射或转发改写了来源地址, 用能对上本次展示请求的等价证据并写明口径, 不用本机 curl 或源码推断顶替. 缺哪个环境就记未验证.
- 页面自检: 交付前 `check_page.py` 必须 `success: true`; 该检查只验证页面自身结构, 不验证网络可达.

## 关键流程

status 重建 (服务已死, 记录仍在): 记录存在 → 用 `pid` 指纹探活失败 → 取运行时锁 → 锁内重读记录并重探活 → 按 `roots` 保序重建 → 先试原端口, 非锁定实例被占则从 49152-65534 换端口重试最多 10 次, 锁定实例只试原端口, 被占返回 `port_in_use` → 新子进程写新 `server.json` → 调用方读回 `pid`/`port` 指纹校验 → 用实际监听端口和地址解析结果组成 `url` 返回 (容器场景用 8800 的宿主映射端口, 记录仍写 8800). 交付 URL 随之更新; 旧 URL 失效不再交付; 同一次展示的显式地址由调用方在 status 时带上, 不从记录里反推. 容器锁定实例重建失败时不擅自换口, 报错并在 chat 说明.

## 决策引用

- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D001, D002, D004, D005, D006, D007, D008, D009, D010, D011, D012 (D003 已被 D011 替代).
- `docs/changes/workflow-stack-review/ACCEPTANCE.md`: AC-15-01 至 AC-15-07.
- `docs/changes/workflow-stack-review/milestone-14/OPPOSITION-RESOLUTION.md`: F010-F015, TC-027 与 `_Handler` 条件依赖的处理.
