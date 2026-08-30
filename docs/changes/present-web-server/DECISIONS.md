# present-web-server 决策账本

变更标题: present skill 新增常驻 web 服务器脚本 (`general/present/scripts/web_server.py`), 远程 (ssh) 场景经 web 服务交付展示内容, 完全替代本地 Chromium 浏览器路径; `general/present/SKILL.md` 同步增加远程模式描述.

## 决策

### D001 绑定地址必填, ssh 场景默认 0.0.0.0, 明确无认证无 TLS
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `start` 的绑定地址 (`--bind`) 是必填参数, 无默认值. SKILL.md 指导 LLM 在 ssh 场景默认选 `0.0.0.0` 并直接向用户交付可点击 URL. 明确非目标: 无认证, 无 TLS, 不做跨机访问控制. 用户明确接受的取舍: 绑定开放时, 网段内任何主体可读全部已挂载目录. 理由: 使用场景是用户本人 ssh 上机后从自己设备的浏览器回看内容, 网段信任是该场景的前提; 认证/TLS 的成本对临时展示工具不成比例.
- 预计影响: `general/present/scripts/web_server.py`, `general/present/SKILL.md`

### D002 用户级单例, 运行时目录带 uid, 文件 0600
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 同一主机同一用户 (uid) 只常驻一个服务实例, 同一用户的多个 ssh 会话共用它, 目录经控制端点动态挂载, 运行时信息文件固定一份. 运行时目录为 `<系统临时目录>/pi-present-web-<uid>/`, 内含固定文件名的 `server.json`/`server.log`/`.lock`; `server.json` 与 `server.log` 权限 0600. start 发现已有实例属主非本人时不复用, 报冲突错误. 理由: 原决策为主机级单例+固定目录名, 反方攻击指出多用户共享主机时会撞车 — B 用户可"幂等复用"A 用户的实例并互挂目录, 或权限拒绝导致完全无法启动; 修正为用户级单例, 这正是原决策 "多 ssh 会话共用" 的本意 (同用户).
- 预计影响: `web_server.py` 运行时状态簇, 命令核心 start

### D003 远程模式完全替代浏览器路径, 远程降级为纯展示
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 检测到远程场景时, present skill 完全不起 Chromium, 生成 HTML 后挂载/复用 web 服务并直接交付 URL. 远程模式明确降级为纯展示: 无 `__PRESENTATION_STATE__` 回读通道, 页面交互反馈与最终确认全部在 chat 完成 (对齐既有原则 "最终确认必须在 chat 中完成"); web server 不加状态回传端点. 页面仍须写 `__PRESENTATION_STATE__` (本地模式与未来兼容需要). 理由: 远程无浏览器可控; 反方攻击指出"完全替代"会使 SKILL.md 现有的 state 回读反馈链断裂, 故显式降级而非静默缺失.
- 预计影响: `general/present/SKILL.md` 远程模式段

### D004 远程检测: 环境变量优先, 用户明示可覆盖
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `SSH_TTY` 或 `SSH_CONNECTION` 任一存在即判定远程 (agent 进程继承 ssh 环境); 用户明示可覆盖检测结果; 检测不到但用户提到远程时按远程处理. 已知限制 (接受, 不防): `su`/`sudo -i`/容器入口可能清洗这两个变量造成漏检, 兜底是用户明示; 漏检后果是走了本地浏览器路径而用户看不到, 可恢复.
- 预计影响: `general/present/SKILL.md`

### D005 运行时信息文件与 status 重建语义
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 运行时信息文件 `server.json` = {pid, port, bind, roots[], 启动时间}, roots 顺序即遮蔽优先级, 重建时保序. `status` = 读运行时文件 + 真实探活 (ping 端点); 服务已死则按原挂载清单重建; 重建先试原端口, 原端口被占时脚本自行在 49152-65534 随机换端口, 上限 10 次, 成功后更新 `server.json` 的 port 并向调用方报告新端口 (交付 URL 随之变化); 运行时文件缺失视为未启动, 不重建. 理由: 原决策为"重建恢复原端口, 被占则报错不换端口", 用户在验收标准环节修订为"脚本程序自行更换端口", 覆盖原决策; 已知限制 (接受, 不防): 系统临时目录被第三方清理 (systemd-tmpfiles 等) 删掉 server.json 时, 存活服务会变幽灵 — status 认为未启动, 重建出第二个实例且老实例脱离管理, 概率低, 无法简单防, 记入风险.
- 预计影响: `web_server.py` 运行时状态簇, 命令核心 status

### D006 命令面: start / status / stop / add-dir
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 四个命令. `start <port> <root> --bind <addr>`: 三参缺一即报错不启动; 实例已存活且 bind 一致时幂等复用 — 忽略端口差异仅告警, 把 `<root>` 走 add-dir 挂载, 返回现有实例信息; bind 不一致时报错并提示先 stop 再起新实例 (不静默复用); 复用时挂载失败则整体 success=false 并注明服务仍存活. `status`: 默认含死则重建 (语义见 D005). `stop`: 终止服务并删除运行时文件, 不经 HTTP (服务半死时仍可终止). `add-dir <dir>`: 走本机 HTTP 控制端点挂载. 不加目录时服务照常提供已挂载内容. 理由: stop 走信号是因为无需服务进程配合改内存状态; bind 不一致报错是反方攻击发现 — 两个方向都爆炸 (想要开放得到 loopback / 想要收敛维持开放), 不能沿用端口差异的"仅告警".
- 预计影响: `web_server.py` 命令核心, HTTP 服务簇控制端点

### D007 允许目录 listing
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 请求目录路径时返回该目录条目 listing; 顶层路径返回各挂载目录条目的并集 (见 D008). 用户明确拍板允许.
- 预计影响: `web_server.py` HTTP 服务簇

### D008 URL 命名空间 = 扁平并集
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 请求路径依次在各挂载目录查找, 首个命中返回; 同名冲突按挂载先后静默遮蔽, 无提示; 顶层 listing 为各目录条目并集, 去重, 无提示. 被拒绝的替代方案: 每挂载目录一个 URL 前缀 — 用户质疑其必要性 (生成的 HTML 文件名不重复, 存储路径本就不同), 前缀只徒增 URL 复杂度, 故作废.
- 预计影响: `web_server.py` HTTP 服务簇

### D009 端口选择分工: LLM 选, 脚本不自动选 (重建例外)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: start 端口由 LLM 在 49152-65534 随机选取; 遇端口被占 (脚本返回机器可读错误码 `port_in_use`, 见 D025) 由 LLM 换端口重试, 上限 10 次 (用户把建议的 3 次改为 10 次); 脚本自身不提供自动选端口. 唯一例外: status 重建时脚本自行换端口 (D005).
- 预计影响: `general/present/SKILL.md`, `web_server.py` 错误码

### D010 不承诺跨重启
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 运行时信息写系统临时目录, OS 重启后服务与挂载全部归零, 不做任何恢复. 对齐 ADR 0003 的临时目录边界取舍.
- 预计影响: `web_server.py` 运行时状态簇

### D011 URL 交付与 host 探测优先级
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: start/复用成功时脚本输出主机名, 局域网 IP 及完整入口 URL, LLM 原样转述给用户. host 值探测优先级定死: `SSH_CONNECTION` 第 3 字段 (sshd 看到的本端地址, 即客户端实际连进来的地址, 可达性有构造保证) > 默认路由接口 IP > 主机名. 绑定 127.0.0.1 时输出 `ssh -L` 端口转发指引. 理由: 反方攻击指出默认路由法在多网卡/VPN/跳板机/NAT 拓扑下常给出客户端不可达的地址, 而可达答案就在 `SSH_CONNECTION` 里.
- 预计影响: `web_server.py` 命令核心 start

### D012 目录参数校验: 绝对路径 + 存在 + 是目录
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: start 与 add-dir 的目录参数必须是绝对路径, 存在且为目录, 否则一律报错拒绝, 不自动创建, 不改变挂载表. 对齐 `browser_session.py` 的路径校验契约.
- 预计影响: `web_server.py` 命令核心, 控制端点

### D013 验收标准 (产品层收口)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 八条, 终版 (第 2 条为用户修订版, 覆盖初版"报错不换端口"):
  1. `start <port> <root> --bind <addr>` 三参缺一即报错不启动; 成功后守护进程化, ssh 断连服务存活; stdout 输出含入口 URL (主机名/局域网 IP), 端口, 挂载信息的 JSON.
  2. `status`: 读临时目录运行时文件 + 真实探活; 已死则按原挂载清单重建, 端口被占时脚本程序自行更换端口; 文件缺失视为未启动. 直接影响: 重建后运行时文件 port 字段更新, 交付 URL 随之变化, status/重建结果须报告新端口.
  3. `stop`: 终止服务并删除运行时文件.
  4. `add-dir` 经本机专用控制端点挂载, 成功后内容立即可访问; 同目录幂等; 非本机来源的控制调用一律拒绝.
  5. 内容访问: 扁平并集首挂载命中; 顶层 listing 并集去重; `../` 等路径遍历不能逃逸出任何挂载目录.
  6. 运行时文件位于系统临时目录, 含 pid/port/bind/roots[]/启动时间.
  7. SKILL.md: 检测到 `SSH_TTY`/`SSH_CONNECTION` 或用户明示远程时走 web 服务器路径, 不起 Chromium; LLM 在 49152-65534 随机选端口, 被占重试 ≤10 次; 成功后 chat 给出可点 URL; 全部失败走现有失败出口 (本地路径+摘要).
  8. 非目标兑现: 无认证, 无 TLS, 重启后一切归零.
- 预计影响: `web_server.py`, `general/present/SKILL.md`, 测试用例集

### D014 空闲 TTL 24h 自退, 不设 remove-dir
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 服务进程 24h 无任何请求则自行退出 (每次请求刷新计时); 不提供 remove-dir 端点 (TTL 已兜底, YAGNI). TTL 值支持环境变量 `PI_PRESENT_WEB_TTL_SECONDS` 覆盖 (默认 86400, 即 24h), 供测试缩到秒级. 理由: 反方攻击发现 — 用户接受的取舍是"使用期间网段可读", 而常驻+挂载只增不减交付的是"走后永远可读"的永久暴露, TTL 直接终结该二阶后果.
- 预计影响: `web_server.py` HTTP 服务簇

### D015 成功指标: 不设
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 本变更不设成功指标. 已确认理由: 内部工具型变更, 无观测渠道, 无指标采集面.

### D016 纯标准库实现, 零第三方依赖
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 用 `http.server.ThreadingHTTPServer` + 自定义 handler 实现, 不引入任何第三方依赖, 对齐 `general/present/pyproject.toml` 零依赖现状, `sync-to-pi.py` 分发后无安装步骤. 被拒绝的替代方案: Flask/FastAPI — 开发体验好但引入依赖与安装步骤, 与 ssh 临时场景和仓库现状相悖.
- 预计影响: `web_server.py`

### D017 后台化: 父 Popen(start_new_session) 起子进程, 单文件双角色
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 单脚本双角色 — 父 (CLI) 进程 `start` 内部以隐藏子命令 `__serve__` 经 `subprocess.Popen(start_new_session=True)` re-exec 自身起子进程; 子进程脱离会话首进程组 (ssh 断连不收 SIGHUP), 自行绑端口/写运行时文件/就绪后开服务; 父进程等就绪信号 (本机 ping 端点) 再输出 JSON 返回; 启动失败由父直接报错; 就绪等待超时 10s, 超时杀子进程报错. 被拒绝的替代方案: double-fork+setsid — 守护化更彻底但调试难, 错误难回传. 被拒绝的替代方案: 拆两个脚本文件 — 分发多一件, 父须定位兄弟文件.
- 预计影响: `web_server.py` 后台化簇

### D018 仅支持 POSIX
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 仅 Linux/macOS; `start_new_session`, 临时目录语义, `fcntl.flock`, `ps` 均按 POSIX 假设; Windows 检测到即报错不支持. 被拒绝的替代方案: 兼做 Windows — 后台化/临时目录/进程探活全部双路径, 测试成本翻倍, 而目标场景几乎必然 POSIX.
- 预计影响: `web_server.py`

### D019 模块划分: 单文件内 4 簇 deep module
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 单文件内部按职责分 4 簇, 每簇是小 interface 的 deep module, 实现细节 (文件格式/锁/就绪等待/路径遍历防护) 藏内部: (1) 命令核心 `run_start/run_status/run_stop/run_add_dir` 返回 dict 不碰 stdout, `main()` 薄 CLI 适配器; (2) 运行时状态簇 — server.json 读写, 探活, 单例文件语义; (3) 后台化簇 — spawn 子进程+等就绪+失败回收; (4) HTTP 服务簇 — server+handler: 扁平并集查找, listing 并集, 路径遍历防护, 控制端点, 仅子进程内运行. 测试 seam 位于 run_* 与真实 HTTP 两层.
- 预计影响: `web_server.py`

### D020 控制面协议与防护
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `add-dir` = CLI 进程经 `POST /__control__/add-dir` (JSON body `{"dir": ...}`) 调本机服务. `/__control__/*` 全簇仅 loopback 来源, 非 loopback 一律拒绝 (含 ping — ping 指纹含 pid, 不对网段暴露). 探活/就绪信号 = `GET /__control__/ping`, 响应含固定标识 `{"service": "pi-present-web", "pid": N}`, status/stop 先 ping 比对 server.json 的 pid, 防端口被无关服务占用时误判存活. `stop` 不走 HTTP: 读 pid 发 SIGTERM, 发前用 `ps -o args= -p <pid>` 校验命令行含本脚本路径, 不匹配则不杀并报错 (防 pid 复用误杀; `ps` 跨平台, 替代最初选的 `/proc/<pid>/cmdline` — macOS 无 /proc, 反方攻击发现的硬矛盾). `/__control__/*` 为保留命名空间, 优先于静态文件查找, 挂载目录下同路径文件被静默遮蔽.
- 预计影响: `web_server.py` HTTP 服务簇, 命令核心 stop/status

### D021 挂载表并发: 锁保护可变 list
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: ThreadingHTTPServer 多线程并发读 roots, add-dir 同时追加; 用锁保护的可变 list — add-dir 持锁 append, 查找时持锁取快照遍历. 被拒绝的替代方案: 不可变 tuple 整体替换 — 读无锁更函数式, 但 add-dir 低频, 锁路径最短, 替换法对本脚本不增益.
- 预计影响: `web_server.py` HTTP 服务簇

### D022 路径安全: resolve + containment, 越界一律 404
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: URL decode → 规范化 → 命中文件 resolve 后必须位于至少一个挂载目录内, 否则 404; symlink 指向挂载目录外同样 404; `../` 不能逃逸任何挂载目录. 越界一律 404 而非 403, 不泄露路径存在性. 对齐 `browser_session.py` 的 resolve+containment 风格.
- 预计影响: `web_server.py` HTTP 服务簇

### D023 单例互斥: flock 串行化
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `start`/`stop`/`add-dir`/status 重建的入口经 `fcntl.flock(<运行时目录>/.lock)` 串行化, 防两个 CLI 进程并发 start 起双实例 (D002 单例的实现保障).
- 预计影响: `web_server.py` 运行时状态簇

### D024 质量属性与日志
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 文件流式发送 (`shutil.copyfileobj`, 不整读入内存); start 就绪等待超时 10s; ping 超时 2s; `protocol_version = "HTTP/1.1"` (默认 HTTP/1.0 无长连接, 多资源页加载差), 不实现 Range; 访问日志与错误日志同入 `server.log` 追加, start 时若已有 log 超 10MB 则截断, 无轮转 (临时目录重启即清, 对齐 ADR 0003; 截断是反方攻击发现的 /tmp 缓慢泄漏的最低成本修复).
- 预计影响: `web_server.py`

### D025 输出与错误契约
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 复用 `browser_session.py` 结构: `run_*` 核心返回 dict 不碰 stdout/sys.exit; `main()` 薄 CLI 适配器负责 argv 解析/JSON 序列化/凭据脱敏 (`_sanitize_error` 同款模式)/退出码; stdout 单行 JSON 含 `success` 字段, exit 0/1. 端口被占返回机器可读错误码 `port_in_use` — SKILL.md 让 LLM "被占重试 ≤10 次" 依赖此码区分端口占用与其他启动失败.
- 预计影响: `web_server.py`

### D026 测试设计与用例集
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `unittest.TestCase` (仓库惯例, pytest.ini 已含 `general/present/tests`, 零配置接入); 起真实服务子进程+真实 HTTP 请求, 不用 mock; 仅两个注入点例外: 运行时目录环境变量覆盖 (`PI_PRESENT_WEB_RUNTIME_DIR`, 测试用独立临时目录隔离, 不与真实实例互杀) 与 TTL 环境变量覆盖 (`PI_PRESENT_WEB_TTL_SECONDS`, D014); 平台模拟 (非 POSIX 报错用例) 属允许的环境边界 fake. 已确认用例 28 条自动化 + 1 条人工验证, 逐条见 TECHNICAL.md TC-001 至 TC-029 (账本不重复抄写, 权威清单在 TECHNICAL.md).
- 预计影响: `general/present/tests/test_web_server*.py`, `general/present/tests/test_skill_contract.py`

### D027 代码允许/禁止范围
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 允许: 新增 `general/present/scripts/web_server.py`, 新增 `general/present/tests/test_web_server*.py`, 修改 `general/present/SKILL.md`, 修改 `general/present/tests/test_skill_contract.py` (增补远程条款断言), 写 `docs/changes/present-web-server/` 产物, 写领域语言/ADR. 禁止: 改 `browser_session.py` 与 access-web, 引入第三方依赖, 动真实 agent skills 目录, 改其他 skill.
- 预计影响: 全变更

### D028 已接受不防的限制清单
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 两项经评估接受为已知限制, 不投入防护: (1) 系统临时目录被第三方清理导致 server.json 丢失时, 存活服务变幽灵 (status 报未启动, 重建出第二实例, 老实例脱离 stop 管理) — 低概率, 无简单防法; (2) `su`/`sudo` 后 SSH_TTY/SSH_CONNECTION 被清洗造成远程漏检 — 兜底是用户明示覆盖 (D004). 两项均记入 TECHNICAL.md 风险与待验证事实.
- 预计影响: TECHNICAL.md

## 事实

### F001 browser_session.py 契约结构
- 状态: 当前有效
- 来源: `general/present/scripts/browser_session.py` (313 行)
- 内容: 核心 `run_open/run_state/run_status` 返回 dict 不碰 stdout/exit; `main()` 是薄 CLI 适配器; stdout 单行 JSON 含 `success` 字段, exit 0/1; 错误消息过凭据脱敏 (`_sanitize_error`, token/api_key/secret/password/auth/credential/bearer 模式); 路径校验要求绝对路径+存在+containment (resolve 后 relative_to 检查). 新脚本复用此结构 (D025).

### F002 测试惯例与 SKILL.md 文本契约先例
- 状态: 当前有效
- 来源: `general/present/tests/` (含 `test_skill_contract.py`)
- 内容: 仓库测试用 `unittest.TestCase`; `test_skill_contract.py` 对 SKILL.md 做文本契约断言 (关键条款存在性), 是 D026 Seam 5 用例的先例.

### F003 pytest.ini 已含 present 测试目录
- 状态: 当前有效
- 来源: 仓库根 `pytest.ini`
- 内容: testpaths 已含 `general/present/tests`, 新测试文件零配置接入.

### F004 sync-to-pi.py 分发规则
- 状态: 当前有效
- 来源: 仓库根 `sync-to-pi.py`
- 内容: 同步时忽略 `tests/`/`__pycache__`/`uv.lock` 等; `scripts/` 下新脚本自动随同步分发到 pi agent 目录, 无额外接线.

### F005 pyproject 零依赖
- 状态: 当前有效
- 来源: `general/present/pyproject.toml`
- 内容: present skill 项目零第三方依赖, `requires-python >= 3.9`. D016 的对齐对象.

### F006 ADR 0003 临时目录边界
- 状态: 当前有效
- 来源: `docs/adr/0003-artifacts-in-temp-no-cross-reboot-login.md`
- 内容: 浏览器产物全部存放系统临时目录, 不保证跨重启登录态 — 有意取舍: session 级语义, 不污染 home. D010/D024 的对齐对象.

### F007 仓库领域文档现状
- 状态: 当前有效
- 来源: `docs/` 目录探测
- 内容: 变更前仓库无 `docs/language/`; ADR 在 `docs/adr/`, 编号 0001-0004. 本次固化新建领域语言文件与 ADR 0005/0006.

### F008 SSH_CONNECTION 字段语义
- 状态: 当前有效
- 来源: OpenSSH 协议事实 + 反方攻击报告 (2026-08-30 盘问会话)
- 内容: `SSH_CONNECTION` 为空格分隔 4 字段: 客户端 IP, 客户端端口, 服务端 IP (sshd 看到的本端地址), 服务端端口. 第 3 字段是客户端实际连进来的地址, 对本客户端可达性有构造保证, 是 D011 host 探测的最高优先级来源.
