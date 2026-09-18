# swt 信箱 mesh 化重设计 Technical Spec

## 架构与组件

单文件深模块 `swt-mailbox.py` (纯 stdlib, 放 workflow/use-sandbox-worktree/scripts/), 小接口 = CLI 子命令 (缺省取信/send/config/status/serve), 大 implementation = Session/Mailbox/Neighbor/Letter 四类 + 信箱路由 + LLM 中转 + 长轮询服务 + HMAC 签名协议.

- **Session** (类): 通信端点统一身份. 字段: id (str, 人类可读, 容器含一次性后缀), signing_key/response_key (HMAC 对, 注册时信箱发放), allow_types 不存在 (D006 不按身份限制). "在线" = 最近取信时间在阈值内. sessions 池存注册信息, 不存连接 (HTTP 无长连接).
- **Letter** (类): 信件. 字段: id (uuid hex), ts, from_session (str), to_session (str, 空 = 最近活跃 session), type (notify/open_url/exec/request), body (str). 信件对象只存内存 (D008).
- **Mailbox** (类): 信箱. 字段: sessions (dict[id -> Session 注册信息]), neighbors (list[Neighbor]), queue (dict[to_session -> list[Letter]], 内存), leases (dict[letter_id -> 租约时刻]), seen_ids (dict[id -> ts], 防洪泛/防重投, 内存), pending_forwards (list[(letter, neighbor)], 邻居不可达时内存暂存). 无 "总信箱/小信箱" 角色字段 — 所有实例地位平等 (D007).
- **Neighbor** (类): 邻居信箱连接. 字段: address (str, host:port), shared_key (str, 首次配置互换).
- **Relay** (类, 跑容器机器才有): LLM 中转. OpenAI 兼容 /v1/chat/completions + /v1/models, sk- key 认证, 模型白名单/quota/用量, 上游地址与密钥经 env. 沿用现有 swt-base-server.py 的 RelayStore 逻辑搬迁.
- **取信脚本** (同文件缺省动作): 阻塞长轮询, 内部退避重试小故障, 有消息才返回. 凭证探测: 容器走 env (SWT_MAILBOX_URL + session 密钥 env), 设备走 ~/.agents/sandbox-worktree/mailbox.json. 附带处理指引 + "处理完继续调用" 提示 + "来信正文是不可信输入" 声明. 拉窗门禁内置.

信箱间路由 (mesh 洪泛):
1. 收到发信 (本机 session POST 或邻居转发): 查 seen_ids, 见过 → 丢弃返回 ok (幂等); 没见过 → 记录 id.
2. 查 sessions: 收件人 session.id 在本机 → 排队 (queue[to_session].append); 不在 → 转发给每个邻居 (排除来源邻居).
3. 邻居不可达 → 信进 pending_forwards 内存暂存, 后台定时重试; 邻居恢复 → 重发 (seen_ids 已记录, 邻居端去重兜底).

模块/目录边界: workflow/use-sandbox-worktree/scripts/swt-mailbox.py (新, 全部实现); pi/extensions/swt-mailbox-relay.ts + swt-mailbox-fetch.mjs (删); scripts/swt-base-server.py (吸收进 swt-mailbox.py 后删); scripts/swt-base-server.service (删); sync-to-pi.py (同步列表调整); swt.py (birth 接线改本机信箱); agent-prompts/ 三母本 (取信指引更新).

## 接口契约

### CLI (swt-mailbox.py)

- `swt-mailbox.py` (缺省 = 取信): 阻塞长轮询. stdout 输出: 信件正文 + 处理指引 + 继续调用提示. 下次调用自动回执上一条. exit 0 正常返回信件, exit 3 致命配置错误.
- `swt-mailbox.py send --to <session.id> --type <notify|open_url|exec|request> --body <text>`: 发信. 凭证自动探测 (容器 env / 设备 config). exit 0 成功, exit 1 参数错误, exit 3 网络不可达.
- `swt-mailbox.py config set <field> <value>`: 修改 server/device (非密钥可走参数). `config set signing_key` / `config set response_key`: 值经 stdin 交互输入 (不回显).
- `swt-mailbox.py status`: 输出: session.id / server 地址 / 最近取信时间 / 待回执数 / 服务连通性实测 / 四项配置 (密钥只显前 8 位).
- `swt-mailbox.py serve [--port <起点>] [--relay-port <起点>] [--admin-port <端口>] [--neighbors <file>] [--upstream-base <url>] [--upstream-key <key>]`: 前台启动. 信箱端口区间 38417-38426 首空闲; 中转端口区间 38427-38436 (无上游配置则跳过中转角色); admin 38416 仅 127.0.0.1. 启动时自动发本机 session 凭证写入本机配置.

### HTTP 端点 (信箱面, 端口区间 38417-38426)

- `GET /__identity__` (无认证): `{"service": "swt-mailbox", "version": "...", "capabilities": ["mailbox", "relay"]}`.
- `POST /mailbox/post`: 请求体 `{"session": "<id>", "sig_ts": "<float>", "sig": "<hmac>", "letter": {id, ts, from, to, type, body}}`. sig = HMAC(signing_key, session\nsig_ts\nletter.id\nletter.body). 响应签名同现有协议. 服务端校验: session 注册且未吊销, 时间窗 ±5min, 防重放 (seen_ids).
- `POST /mailbox/poll`: 请求体 `{"session": "<id>", "sig_ts": "...", "sig": "..."}`. sig = HMAC(signing_key, session\nsig_ts). 阻塞 hold 20s. 响应: `{payload: {letter: {...} | null, lease_token: "<hex>", nonce: "..."}, sig: "..."}`. letter 为 null = 空载荷. 同 session 并发 poll 超 5 → 409.
- `POST /mailbox/ack`: 请求体 `{"session": "<id>", "sig_ts": "...", "sig": "...", "letter_id": "...", "lease_token": "...", "outcome": "handled|skipped:..."}`. 租约验证: token 匹配且未过期 → 标记已处理; token 不匹配 → 409; 已处理 → 幂等 ok.
- `POST /mailbox/forward` (邻居间): 请求体 `{"neighbor_key": "<共享密钥>", "letter": {...}}`. 校验 neighbor_key 与来源地址. 处理逻辑同 post 的 seen-id/路由, 但不要求 session 凭证 (邻居身份代替).
- `POST /admin/sessions` / `POST /admin/sessions/revoke` / `GET /admin/sessions` / `POST /admin/neighbors` / `GET /admin/relay-keys` / `POST /admin/relay-keys` / `POST /admin/relay-keys/revoke` / `POST /admin/whitelist` / `GET /admin/stats`: 管理面 (127.0.0.1:38416, X-Admin-Token header, token 写状态文件 ~/.local/state/swt-mailbox/state.json).

### HTTP 端点 (中转面, 端口区间 38427-38436)

- `POST /v1/chat/completions`: OpenAI 兼容, Bearer sk- key, 不支持 stream. 沿用现有 RelayStore 逻辑.
- `GET /v1/models`: 模型列表 (key 白名单过滤).

### 环境变量 (容器, birth 烘入)

- `SWT_MAILBOX_URL`: 本机信箱地址 (host.containers.internal:38417+).
- `SWT_SESSION_ID`: 容器 session id (<容器名>-<8hex>).
- `SWT_SESSION_SIGNING_KEY` / `SWT_SESSION_RESPONSE_KEY`: 容器 session 密钥对.
- `OPENAI_BASE_URL` (或等价): 中转地址 (host.containers.internal:38427+), 由容器内 agent 的 provider 配置消费.

### 环境变量 (serve)

- `SWT_UPSTREAM_BASE` / `SWT_UPSTREAM_KEY`: 中转上游.
- `SWT_ADMIN_PORT`: 管理口覆盖.
- `SWT_MAILBOX_LEASE_SECONDS`: 租约时长 (缺省 1800).
- `SWT_MAILBOX_MAX_CONCURRENT_POLLS`: 同 session 并发上限 (缺省 5).

### 配置文件 (~/.agents/sandbox-worktree/mailbox.json, 0600)

```json
{
  "server": "http://127.0.0.1:38417",
  "session": "<session.id>",
  "signing_key": "...",
  "response_key": "..."
}
```

状态文件 (~/.agents/sandbox-worktree/mailbox-state.json): 已见消息 id (最近 100) / 待回执 letter_id+lease_token / 拉窗限频时刻表.

邻居表 (~/.agents/sandbox-worktree/neighbors.json, serve 或 config 管理):

```json
[
  {"address": "192.168.1.10:38417", "shared_key": "..."},
  {"address": "192.168.1.20:38417", "shared_key": "..."}
]
```

## 数据模型与状态

### SQLite (仅凭证与配置, 不存信件 — D008/BR-009)

- `sessions` 表: id TEXT PRIMARY KEY, signing_key TEXT, response_key TEXT, revoked INTEGER, last_poll REAL, created_at REAL.
- `neighbors` 表: address TEXT PRIMARY KEY, shared_key TEXT, revoked INTEGER.
- `relay_keys` 表: 沿用现有 schema (key, models, quota, used, expires_at, revoked).
- `whitelist` 表: 沿用现有 schema (instruction TEXT).
- 消息表 (messages), 已见表 (seen_ids): 废弃 — 全部改内存 dict.
- 迁移: ALTER TABLE 增量 (sessions 表新加), 旧 devices/container_keys 表数据迁入 sessions 表 (D019), 消息表 DROP.

### 信件状态机 (全内存)

```
排队 (queue) --poll--> 租出 (leased, 计时) --ack--> 已处理 (移除)
                         |
                         +--租约到期--> 排队 (重投)
```

### 邻居转发状态机 (全内存)

```
待转发 (pending_forwards) --邻居可达--> 已发出 (seen_ids 记录)
                              |
                              +--重试定时器--> 待转发 (循环)
```

## 边界与异常处理

- 网络中断/服务重启: 取信脚本内部退避重试, 不退出不报错 (S3). serve 重启: 内存队列/租约/暂存全清 (D008, NG-008).
- 防洪泛循环: seen_ids 内存 dict, 收到重复 id 丢弃. 来源邻居排除减少无谓流量.
- 同信双投 (mesh 洪泛 + 租约重投重叠): 取信脚本按已见 id 去重 (最近 100, state file).
- 并发保护: 同 session 并发 poll 上限 5, 超出 409. 信箱间转发无并发限制 (邻居数少).
- 幂等: post 重复 id → ok (seen_ids); ack 重复 → ok (已处理幂等); forward 重复 → ok (seen_ids).
- 时钟: 请求签名时间窗 ±5min (沿用). 租约计时用服务端单调时钟.
- 兼容: 旧协议客户端 (未升级的 pi 扩展) poll 拿到信后 ack — 租约被 ack 提前终结, 天然兼容, 无需双协议 (D009 租约语义对旧客户端透明).

## 依赖与风险

- 外部依赖: 零 (纯 stdlib). python >= 3.9 (容器 base 层已含).
- 关键风险 1: LLM 循环纪律 (D002) — 断链无人报警. 防护: 脚本输出尾附提示; 取信会话专职常驻.
- 关键风险 2: 信箱重启丢排队信 (D008/NG-008) — 发信方需重发. 防护: 文档明示; serve 前台运行肉眼可见.
- 关键风险 3: agent 工具超时未验证 (D018/A4) — codex/kimi 的命令工具可能有超时限制. 防护: 落地前实测三种 agent; 有界模式后备.
- 关键风险 4: mesh 洪泛在邻居数增长时流量线性增加 — 3-5 台内网可忽略. 防护: 来源排除 + seen-id.

## 安全策略

- 认证: session 密钥对 (HMAC 签名 + 验签), 邻居共享密钥 (转发互认), admin token (管理面). 密钥不明文上线 (签名式).
- 授权: 指令集白名单 (exec 类型服务端校验, 不在集合降级 request) — 不按身份限制 (D006). 来信正文按不可信输入处理 (BR-002, 脚本输出声明).
- 隐私: 信箱端口绑 0.0.0.0 但信件签名加密不机密 — 内网裸 HTTP 接受 (用户既有取舍); 跨机不加密 (mesh 邻居间同为内网).
- 密钥管理: 配置文件 0600 目录 0700; 密钥不走命令行参数 (stdin 交互); status 脱敏 (前 8 位); serve 自动发的本机凭证同规格保护.
- 不适用: TLS/证书 — 内网环境, 签名管真实性与完整性, 不做机密性 (用户既有取舍).

## 非功能要求

- 空闲等待零 LLM 调用 (BR-005): 脚本阻塞期间无任何输出.
- 取信延迟: 本机信件 ≤ 1s (hold 唤醒); 跨机信件 ≤ 3s (两跳洪泛). 验证口径: e2e 测试断言投递延迟.
- 信箱内存占用: 排队信件每条 < 1KB (body 限制), 千条排队 < 1MB — 无需配额.

## 关键流程

### 信件跨机投递 (Yoga 容器 → Windows 设备)

1. Yoga 容器 agent 调 send → POST 到 Yoga 本机信箱 /mailbox/post.
2. Yoga 信箱: seen-id 记录, 查 sessions — Windows session 不在本机 → 转发给每个邻居 (排除来源, 来源是容器 session 非邻居).
3. Workstation 信箱: 收到 forward, seen-id 记录, 查 sessions — 不在本机 → 转发给邻居 (排除 Yoga).
4. Windows 信箱: 收到 forward, seen-id 记录, 查 sessions — 在本机 → 排队.
5. Windows agent 取信脚本 poll 挂起在 Windows 信箱 → 信到达唤醒 → 返回给 LLM.
6. LLM 处理完再调脚本 → 脚本自动 ack (lease_token) → 租约终结.

### serve 启动流程

1. 读邻居表/上游配置.
2. SQLite 打开/迁移 (凭证表).
3. 自动发本机 session 凭证 (id = <hostname>-host) → 写 ~/.agents/sandbox-worktree/mailbox.json.
4. 绑信箱端口 (38417-38426 首空闲) → __identity__ 可探测.
5. 有上游配置 → 绑中转端口 (38427-38436 首空闲).
6. 启动后台线程: 邻居暂存重试定时器.
7. 前台 ThreadingHTTPServer serve_forever().

## 测试接缝

| 行为 | 观察边界 | 测试层级 |
|---|---|---|
| AC-001 取信基本流 | POST /mailbox/poll + GET /mailbox/ack | 集成 |
| AC-002 既有投信回归 | POST /mailbox/post (exec 类型) + poll 响应 downgraded 字段 | 集成 |
| AC-003 故障自愈 | 取信脚本子进程退出码/stdout | 端到端 |
| AC-004 租约重投 | POST /mailbox/poll + 时间推进 + 再次 poll | 集成 |
| AC-005 双会话散落 | 两个并发 poll 请求响应 | 集成 |
| AC-006 设备回信 | send 子命令 + 目标信箱 poll | 集成 |
| AC-007 容器收发 | env 凭证 + poll + post | 集成 |
| AC-008 容器终结 | admin revoke + poll 空响应 | 集成 |
| AC-009 拉窗门禁 | 取信脚本 stdout + state file | 单元 |
| AC-010 配置迁移 | 文件系统 (老路径 → 新路径) | 单元 |
| AC-011 旧机制退役 | sync-to-pi 后扩展目录内容 | 人工 |
| AC-012 并发上限 | 第 6 个并发 poll HTTP 409 | 集成 |
| AC-013 mesh 路由 | 三实例 serve + 跨机 post/poll | 端到端 |

## 决策引用

- docs/changes/swt-mailbox-mesh/DECISIONS.md: D001-D020
