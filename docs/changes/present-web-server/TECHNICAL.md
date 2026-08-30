# present-web-server Technical Spec

## 技术目标

- TG-001: `web_server.py` 以纯标准库实现 start/status/stop/add-dir 四命令, 单行 JSON 契约, exit 0/1. 覆盖: AC-001, AC-002, AC-003, AC-004.
- TG-002: 常驻服务经扁平并集提供多挂载目录静态内容, 路径遍历不可逃逸, 控制面仅 loopback. 覆盖: AC-004, AC-005.
- TG-003: 用户级单例状态管理: 运行时文件固定一份, flock 互斥, 死则重建, 空闲 24h 自退. 覆盖: AC-002, AC-006, AC-008.
- TG-004: SKILL.md 远程模式契约可被文本断言, 且与脚本行为一致. 覆盖: AC-007.

## 架构与组件

单文件 `general/present/scripts/web_server.py`, 双角色 (CLI 父进程 / `__serve__` 隐藏子命令的服务子进程). 单文件内 4 簇 deep module, seam 位于 run_* 函数层与真实 HTTP 层:

1. **命令核心** `run_start/run_status/run_stop/run_add_dir` — 返回 dict, 不碰 stdout/sys.exit; `main()` 薄 CLI 适配器 (argv/JSON 序列化/凭据脱敏/退出码). 结构复用 `browser_session.py`.
2. **运行时状态** — `server.json` 读写, ping 探活, flock 互斥; interface = load/save/probe 级别, 文件格式与锁细节藏内部.
3. **后台化** — `subprocess.Popen(start_new_session=True)` spawn 子进程 + 等 ping 就绪 (超时 10s) + 失败回收报错.
4. **HTTP 服务** — `http.server.ThreadingHTTPServer` + 自定义 handler: 扁平并集查找, 顶层 listing 并集去重, resolve+containment 路径防护, `/__control__/*` 控制端点 (仅 loopback), 空闲 TTL 自退 (默认 24h, `PI_PRESENT_WEB_TTL_SECONDS` 可覆盖); 仅子进程内运行. 挂载表 = 锁保护可变 list, 查找持锁取快照.

## 接口契约

### CLI (stdout 单行 JSON, 含 `success` 字段, exit 0/1)

- `web_server.py start <port> <root> --bind <addr>` → 成功 `{"success": true, "command": "start", "url", "hostname", "lan_ip", "port", "bind", "roots", "reused": bool, "warning"?}`; 失败 `{"success": false, "code", "error"}`. 错误码含 `invalid_args` (缺参/目录非法), `port_in_use` (端口被占), `bind_conflict` (与存活实例 bind 不一致), `instance_conflict` (实例属主非本人), `not_supported` (非 POSIX), `internal_error`.
- `web_server.py status` → `{"success": true, "alive": bool, ...运行时信息, "rebuilt": bool, "port"}`; 未启动 `alive: false`.
- `web_server.py stop` → `{"success": true}`; 进程校验不匹配时报错不杀.
- `web_server.py add-dir <dir>` → 成功 `{"success": true, "roots"}`; 服务未存活/目录非法/端点拒绝时 `success: false`.
- 错误消息经凭据脱敏 (`_sanitize_error` 同款模式).

### HTTP (仅子进程)

控制面 (`/__control__/*` 保留命名空间, 仅 loopback, 优先于静态查找, 遮蔽同路径文件):

- `GET /__control__/ping` → `{"service": "pi-present-web", "pid": N}`.
- `POST /__control__/add-dir`, body `{"dir": "<绝对路径>"}` → 200 `{"success": true, "roots"}` / 4xx `{"success": false, "error"}`.

内容面 (静态访问面, 绑定开放时对网段可见, D001 取舍):

- `GET <路径>` → 扁平并集静态内容或目录 listing; 越界/不存在一律 404 (不泄露存在性).
- `protocol_version = "HTTP/1.1"`, 不实现 Range.

## 数据模型与状态

`<tmpdir>/pi-present-web-<uid>/` (权限 0700 目录), 内含:

- `server.json` (0600): `{"pid": int, "port": int, "bind": str, "roots": [str 绝对路径, 顺序即遮蔽优先级], "started_at": ISO-8601 str}`. 单例固定文件名. 写入方: 子进程启动时; 重建时更新 port/pid/started_at.
- `server.log` (0600): 访问+错误日志追加; start 时已有 log 超 10MB 则截断; 无轮转.
- `.lock`: flock 互斥文件, start/stop/add-dir/status 重建入口串行化.

状态机: 未启动 (无 server.json) → 存活 (server.json + ping 指纹匹配) → 已死 (ping 失败) → status 触发重建 → 存活 (端口沿用或更换). 服务空闲 24h (TTL, `PI_PRESENT_WEB_TTL_SECONDS` 可覆盖) 自退 → 已死.

## 关键流程

- **start (冷启动)**: 参数校验 → flock → probe 排除存活 → Popen `__serve__` → 子进程绑端口/写 server.json/开服务 → 父轮询 ping (≤10s) → 输出 JSON. 绑端口失败子进程退出, 父报 `port_in_use`.
- **start (复用)**: probe 存活 → 校验属主本人 + bind 一致 → add-dir 挂载 root → 返回现有信息 (+端口差异告警). 挂载失败 → success=false 注明服务仍存活.
- **status 重建**: server.json 在但 ping 失败 → flock → 按 roots 保序重 spawn: 先试原端口, 被占则 49152-65534 随机换 ≤10 次 → 更新 server.json → 报告新端口.
- **stop**: 读 server.json → ping 比对 pid → `ps -o args= -p <pid>` 校验含本脚本路径 → SIGTERM → 等退出 → 删 server.json.
- **add-dir**: 校验目录 → POST 控制端点 → 服务进程持锁 append roots → 立即可访问; 同目录幂等.

## 边界与异常

- 非法输入: 缺参/相对路径/目录不存在/非目录 → `invalid_args`, 不启动不改挂载表; 未知命令报错 exit 1; 非 POSIX 平台 `not_supported`.
- 超时: start 就绪 10s, 超时杀子进程报错; ping 2s.
- 并发: flock 串行化命令入口; 挂载表锁保护.
- 幂等: start 复用, add-dir 同目录, status 重建保序.
- 降级: 远程模式无 state 回读, 反馈在 chat; 展示全失败走既有失败出口 (本地路径+摘要).
- 兼容: 文件权限 0600, 目录带 uid, 属主非本人的实例不复用.

## 安全策略

- 认证/授权/加密: 无 (非目标, 用户接受网段信任, D001); 控制面收窄 loopback 是该取舍下的最小可控面.
- 越界防护: URL decode → 规范化 → resolve → 命中文件须位于至少一个挂载目录内, 否则 404; symlink 越界 404; 不区分 403/404.
- 进程防护: stop 前 ping 指纹比对 + `ps` 命令行校验, 防 pid 复用误杀.
- 隐私: 运行时文件 0600 属主可读; ping 指纹 (含 pid) 不对非 loopback 暴露.
- 脱敏: 错误消息过 `_sanitize_error` 同款凭据模式.

## 非功能要求

- NFR-001: 文件流式发送 (`shutil.copyfileobj`), 大文件不整读入内存. 验证: 代码审查+大文件请求用例隐含覆盖.
- NFR-002: start 就绪 ≤10s, ping ≤2s. 验证: 生命周期用例在 CI 常规耗时内完成.
- NFR-003: 日志单点 `server.log`, start 时超 10MB 截断. 验证: 用例 TC-015 扩展断言或代码审查.
- NFR-004: 空闲 24h 自退. 验证: TC-028 (TTL 注入缩短).

## 测试接缝与用例

总体方式: `unittest.TestCase`, 起真实服务子进程 + 真实 HTTP 请求; 不用 mock, 例外仅: 平台模拟 (TC-004), 运行时目录注入 (`PI_PRESENT_WEB_RUNTIME_DIR`), TTL 注入 (TC-028). 预期值来源均为已确认决策/规格字面量.

Seam 1 - CLI 契约 (公开接口: `main()` argv/stdout JSON/exit code, 单元级):

- TC-001: Given 缺 port/root/bind 任一, When start, Then success=false, exit 1, 无子进程残留. 正常/异常: 异常. 覆盖: AC-001, TG-001.
- TC-002: Given root 不存在, When start, Then `invalid_args`, 不启动. 异常. 覆盖: AC-001.
- TC-003: Given 未知命令, When 执行, Then success=false, exit 1. 异常. 覆盖: TG-001.
- TC-004: Given 模拟非 POSIX 平台 (patch 平台判定, 环境边界 fake), When 任意命令, Then `not_supported`. 异常. 覆盖: D018.

Seam 2 - 生命周期 (公开接口: run_* + server.json + 真实 URL, 集成/端到端):

- TC-005: Given 合法三参, When start 成功, Then JSON 含 url/port/roots, server.json 含 pid/port/bind/roots/started_at, 入口 URL 可访问到 root 内容. 正常. 覆盖: AC-001, AC-006.
- TC-006: Given 实例存活且 bind 一致, When 以不同端口 start 新 root, Then 复用成功, 含端口差异告警, 新 root 立即可访问. 正常. 覆盖: AC-001, BR-002.
- TC-007: Given 端口被无关进程占用, When start 该端口, Then 错误码 `port_in_use`, 脚本不自行换端口. 异常. 覆盖: BR-001.
- TC-008: Given 实例存活, When status, Then alive=true 且含运行时信息. 正常. 覆盖: AC-002.
- TC-009: Given 无 server.json, When status, Then alive=false (未启动), 不重建. 正常. 覆盖: AC-002.
- TC-010: Given 进程被杀 (server.json 残留), When status, Then 按原 roots 重建, 端口可用则沿用, 重建后内容可访问. 正常. 覆盖: AC-002.
- TC-011: Given 进程已死且原端口被占, When status, Then 换端口 (49152-65534, ≤10) 重建, 报告新端口, server.json 已更新. 边界. 覆盖: AC-002.
- TC-012: Given 实例存活, When stop, Then 进程终止, server.json 删除, 后续请求失败. 正常. 覆盖: AC-003.
- TC-013: Given 实例存活, When add-dir 存在的目录, Then 内容立即可访问; 再次 add-dir 同目录 Then 幂等 (roots 不重复). 正常. 覆盖: AC-004.
- TC-014: Given 实例存活, When add-dir 不存在的目录, Then 报错且挂载表不变. 异常. 覆盖: AC-004.
- TC-015: Given 服务运行并有请求发生, When 检查运行时目录, Then server.log 存在且有记录. 正常. 覆盖: NFR-003.

Seam 3 - 内容访问 (公开接口: 真实 HTTP GET, 端到端):

- TC-016: Given 两挂载目录, 文件只在后挂载目录, When GET 该路径, Then 返回该文件. 正常. 覆盖: AC-005.
- TC-017: Given 两挂载目录含同名文件, When GET, Then 返回先挂载的那份. 边界. 覆盖: AC-005.
- TC-018: Given 两挂载目录顶层有同名与异名条目, When GET `/`, Then listing 并集且去重. 正常. 覆盖: AC-005.
- TC-019: Given 服务已挂载目录, When GET 含 `../` 的逃逸路径, Then 404, 不暴露挂载目录外内容. 异常. 覆盖: AC-005.
- TC-020: Given 命中文件是指向挂载目录外的 symlink, When GET, Then 404. 边界. 覆盖: AC-005.
- TC-021: Given 挂载目录内存有子目录, When GET 一个目录路径, Then 返回该目录 listing. 正常. 覆盖: BR-004 (listing 允许).

Seam 4 - 控制面安全 (公开接口: 真实 HTTP, 经本机 LAN IP 模拟非 loopback 来源, 端到端):

- TC-022: Given 服务绑定 0.0.0.0, When 经本机 LAN IP 请求 `/__control__/ping` 或 add-dir, Then 一律拒绝. 异常. 覆盖: AC-004, BR-006.
- TC-023: Given 服务绑定 0.0.0.0, When 经本机 LAN IP 请求静态内容, Then 正常返回. 正常. 覆盖: D001 取舍兑现.

Seam 5 - SKILL.md 文本契约 (公开接口: SKILL.md 文本, 单元级, 对齐 test_skill_contract.py 先例):

- TC-024: Given SKILL.md 已写入远程模式段, When 校验 SKILL.md, Then 含: 远程检测 (SSH_TTY/SSH_CONNECTION+用户明示覆盖), web 服务器路径替代 Chromium, 端口范围 49152-65534 与重试 ≤10 及 `port_in_use` 依据, 失败出口 (本地路径+摘要), 远程降级纯展示无 state 回读条款. 正常. 覆盖: AC-007, TG-004.

Seam 6 - 盲区修复增补 (接口同上):

- TC-025: Given 实例存活且 bind 不同, When start, Then `bind_conflict` 报错, 不复用. 异常. 覆盖: BR-002.
- TC-026: Given start 成功, When 检查文件, Then server.json 与 server.log 权限为 0600. 正常. 覆盖: AC-006.
- TC-027: Given 设置 `SSH_CONNECTION="cip cport sip sport"`, When start 成功, Then 输出 URL 的 host 为 `sip`. 正常. 覆盖: D011 (env 注入模拟).
- TC-028: Given `PI_PRESENT_WEB_TTL_SECONDS` 缩到秒级, When 空闲超过 TTL, Then 服务自退 (进程退出). 边界. 覆盖: AC-008, NFR-004.
- TC-029 (人工验证): Given 共享主机上用户 A 的实例存活, When 用户 B 执行 start, Then 报 `instance_conflict` 不复用 A 的实例. 需异 uid 环境, 不自动化. 覆盖: AC-006.

允许的 mock/fake: 平台判定 patch (TC-004), 环境变量注入 (`PI_PRESENT_WEB_RUNTIME_DIR`/`PI_PRESENT_WEB_TTL_SECONDS`/`SSH_CONNECTION`). 无其他.

## 技术决策引用

- `DECISIONS.md`: D016-D028 (技术层全部), 及 D005/D006/D011/D012 (产品决策的技术承载).
- ADR: 0003 (临时目录边界), 0005 (远程 web 服务替代浏览器), 0006 (扁平并集命名空间).

## 依赖与风险

- 外部依赖: 无 (纯标准库, Python ≥3.9).
- 风险 1: 临时目录被第三方清理 → 幽灵服务 (D028). 影响: 单例语义暂时失效, 老实例脱离管理. 防护: 无 (已接受), 使用观察验证.
- 风险 2: `su`/`sudo` 清洗 SSH_* 环境变量 → 远程漏检 (D004/D028). 防护: 用户明示覆盖兜底.
- 风险 3: 绑定开放时网段可读全部挂载目录 (D001 取舍). 防护: TTL 24h 自退兜底永久暴露; 控制面 loopback-only.

## 代码边界提示

- 新增: `general/present/scripts/web_server.py`, `general/present/tests/test_web_server*.py`.
- 修改: `general/present/SKILL.md` (远程模式段), `general/present/tests/test_skill_contract.py` (增补远程条款断言).
- 禁止: `browser_session.py`, access-web, 第三方依赖, 其他 skill, 真实 agent skills 目录.

## 待验证事实

- 事实: 系统临时目录清理导致 server.json 丢失时存活服务变幽灵.
  影响: 单例失效, 老实例暴露不可见.
  验证方式: 真实环境长周期使用观察 (已接受, D028).
- 事实: TC-022/TC-023 依赖测试环境有可用非 loopback 接口 (本机 LAN IP).
  影响: 无网卡的极简容器/CI 中该两用例无法构造来源, 需 skip 而非 fail.
  验证方式: 实现时探测, 无接口则 unittest.skip.
