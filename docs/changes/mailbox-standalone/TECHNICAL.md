# mailbox 信箱: 独立 skill, pi 连接器与无感自组网 Technical Spec

## 模块划分

- **服务端核心** (mailbox.py 内 `Mailbox` 类, 改动): 会话注册表/内存队列/租约/seen_ids/邻居/滞留/TTL 清扫/回执生成. 藏路由判定, 幂等, 计时与指令集校验.
- **HTTP 面** (mailbox.py 内三个 handler, 改动): 信箱口 (post/poll/ack/forward + 新增 sessions 只读端点 + hello 握手端点), admin 口 (邻居 CRUD/滞留管理), 中端口 (不动). 藏验签, 应答签名, JSON 编解码与 HTTP 状态映射.
- **CLI 面** (mailbox.py, 改动): serve/send/config/status/取信 + 新增机器子命令 (discover/register-session/revoke-session) 与 join-fleet. 藏凭证探测, 路径迁移, 输出格式. 删除测试判定: 删掉它 swt 与用户各自重实现签名与凭证读写 — 复杂度散回调用点, 模块有价值.
- **取信客户端** (mailbox.py 内 cmd_fetch, 改动): per-listener cli-state, 拉窗门禁, 回执紧凑单行, --timeout/--count. 藏回执时序与去重.
- **自组网** (mailbox.py 内, 新增): 信标收发 (UDP 广播), 舰队密钥互证握手, 认证换址宣告, join-fleet (ssh 拉取). 藏发现时序与密钥协商. 删除测试判定: 删掉它手工配对流程整套回归 — 复杂度消失的是自动化, 调用点无此能力, 模块有价值.
- **pi 扩展** (pi-extension/index.ts, 新增): /mail /mail-listen /mail-send 三命令, 取信守护循环, 来信注入, 回执降噪, listen.json. 藏 pi 生命周期与会话注入时序. 删除测试判定: 删掉它用户退回手敲脚本 — 优雅层消失但能力不丢, 复杂度不散回脚本; 模块价值在体验不在能力.
- **swt.py 信箱接线** (改动): 删除自带 probe/admin 实现 (~150 行), 改调机器子命令.
- **sync-to-pi.py** (改动): settings.json extensions 数组合并.

边界: `workflow/mailbox/` (scripts/mailbox.py, pi-extension/, reference/, SKILL.md), `workflow/use-sandbox-worktree/` (swt.py, SKILL.md, agent-prompts/), `sync-to-pi.py`, `tests/` 留仓库根.

## 模块接口

**机器子命令** (swt.py 唯一依赖面):
- `discover` → stdout JSON `{"port", "admin_port", "admin_token"}`; 信箱未发现 exit 3, stderr 人话. 语义 = 现 probe_mailbox (状态文件验活优先, 区间扫描兜底).
- `register-session <id>` → stdout JSON `{"id","signing_key","response_key"}`; 已存在/admin 不可达 exit 3.
- `revoke-session <id>` → stdout JSON `{"id","revoked":true}`; 未知 session exit 3.
- 不变量: JSON 只走 stdout; 内部 HTTP 超时 5s; 调用方零配置 (路径经 `__file__` 相对定位).

**投信应答** (post, 改动): payload 增 `route`: `queued_local` (本机排队) / `forwarded` (预算内全部邻居确认) / `forwarded_partial` (部分确认) / `staged_pending` (预算内无确认, 转后台重试). 洪泛判定预算 2s, 超时邻居记 pending 由后台重试, 不再拖住应答. send CLI 按 route 打人话, 回执分行打 `目标 session=` 与 `信件 id=`. 顺序约束: 无. 幂等: 重复 letter id 仍幂等收下.

**取信 CLI** (改动): `--timeout <秒>` (到时无信退出码 0 并报无信), `--count <n>` (取满即退), `--cli-state <路径>` (per-listener 状态文件, env `MAILBOX_CLI_STATE` 同义); 首次连接失败立即打 "信箱服务未启动/不可达" 再退避. status 认 env 凭证并验活, 输出增本机会话待取数 (经信箱口 `GET /mailbox/queued`, session 签名, 返回队列深度). 回执信打印紧凑单行不触发处理指引.

**信件 schema** (改动): 增 `expires_at` (epoch, 缺省 = ts+24h) 与 `from` 验签 (post 校验 `from == 签名 session`, 不符 403); body 超 1MB 413. 回执信: type=notify, from=`mailbox@<hostname>`, body JSON `{"receipt":"delivered"|"read"|"failed","letter_id":<原id>}`, id 确定化 (`<原id>.delivered`/`.read`/`.delivery-failed`), 回执不生成回执.

**admin 口** (改动): 邻居 `GET/DELETE/PATCH /admin/neighbors` (邻居增 `name` 字段, 同名 upsert 覆盖地址); 滞留 `GET /admin/pending` (id/to/邻居/最后错误/重试次数/年龄), `POST /admin/pending/retry|drop`; 滞留上限 (缺省 100, env 可调), 超限丢最老.

**信箱口** (改动): `GET /mailbox/sessions` (session 签名认证, 回 id+last_poll, 不泄密钥); `GET /mailbox/queued` (session 签名, 回本机会话队列深度); `POST /mailbox/hello` (自组网握手: 舰队密钥 HMAC 挑战应答).

**自组网** (新增): 信标 UDP 广播端口 38437, 载荷 `{address, hostname, fingerprint}`; 握手成功后自动建邻居 (两两链路密钥协商); 换址宣告 = 旧链路密钥签名的邻居间消息; `join-fleet <老设备ssh地址>` 从新设备主动 ssh 拉取 fleet.key (0600). 配置: `~/.agents/mailbox/fleet.key`, env `MAILBOX_FLEET_KEY` 覆盖.

**pi 扩展** (新增): `/mail-listen start|stop|status`, `/mail`, `/mail-send`. 守护 = 后台循环子进程调取信脚本 (逐封), 来信 `pi.sendUserMessage(deliverAs:"followUp", triggerTurn:true)` 注入, `agent_settled` 后取下一封 (回执时序=处理后); 回执信不注入, 汇入 /mail 与 widget; 脚本 exit 3 → notify 并停守护. listen 状态落 `~/.agents/mailbox/listen.json`, session_start 自动恢复; 检测到他会话守护在跑 → 警告仍启动.

**sync-to-pi.py** (改动): 合并 `"extensions"` 数组加 `~/.agents/skills/mailbox/pi-extension`, 幂等去重, 写前 .bak.

## 接缝与适配器

- swt.py ↔ 机器子命令 (跨模块, 本地可替换): 生产适配器 = subprocess 调 `../mailbox/scripts/mailbox.py`; 测试适配器 = 假脚本输出罐头 JSON / 真脚本 + 临时目录 env 隔离.
- 扩展 ↔ 取信脚本 (跨模块, 本地可替换): 生产 = subprocess 逐封取; 测试 = 假脚本吐罐头信.
- 时间 (模块内部): `now`/`monotonic` 注入 (沿用现有先例), TTL/租约/退避测试快进.
- 信标 socket (模块内部): 生产 = UDP 广播 socket; 测试 = 注入 socket 对/回环.
- ssh (join-fleet, 真正外部): 生产 = subprocess ssh; 测试 = 假 ssh 命令.
- HTTP 客户端 (模块内部): `http_post` 可注入 (沿用先例).
- settings.json (本地可替换): 生产 = `~/.pi/agent/settings.json`; 测试 = 临时文件.
- LLM 中转上游 (真正外部): 沿用现有, 不动.

## 测试接缝

- AC-001..005 (取信守护/注入/恢复/软提示/降噪) -> pi 扩展 -> 扩展↔脚本接缝 -> 假取信脚本 + pi 扩展测试宿主
- AC-006..010 (回执分行/投递态/未知报错/异步不拖垮) -> CLI 面+服务端核心 -> post 应答 -> 内存 Mailbox + 假邻居 http
- AC-011..013 (邻居 CRUD/upsert, 滞留列出/重投/丢弃/上限) -> admin 口 -> HTTP -> 内存 Mailbox + admin token
- AC-014..017 (验活/明报/timeout/count/status env) -> CLI 面 -> 路径与凭证 env 覆盖 -> 临时目录 + 假 serve
- AC-036 (待取数量) -> CLI 面+信箱口 -> /mailbox/queued -> 内存 Mailbox + 假签名
- AC-018..020 (三回执/幂等/不递归) -> 服务端核心 -> 时间注入 + 内存路由 -> 双 Mailbox 实例内存互联
- AC-021 (1MB 413), AC-022 (from 验签 403) -> HTTP 面 -> 请求构造 -> handler 级测试
- AC-023..024 (独立可用/旧路径迁移) -> CLI 面 -> env 路径覆盖 -> 临时 HOME 端到端
- AC-025..026 (birth 接线/机器子命令) -> swt.py 接线 -> swt↔脚本接缝 -> 假 mailbox 脚本
- AC-027 (宿主信息 env) -> swt.py birth -> 既有 birth 测试 -> 假 podman
- AC-028 (sessions 只读端点) -> 信箱口 -> 签名构造 -> handler 级测试
- AC-037 (关键事件 UTC 日志) -> 服务端核心 -> 日志输出捕获 -> 内存 Mailbox 事件触发
- AC-029..030 (拉窗绑定放宽/url 参数) -> 服务端核心+取信客户端 -> 指令集校验 -> 沿用 whitelist 测试夹具
- AC-031..035 (自发现/拒入/换址自愈/伪造拒/join-fleet) -> 自组网 -> 信标 socket 注入 + 假 ssh + 临时 fleet.key -> 双实例互联
- BR-001 (纯 stdlib) -> 审计: 静态扫描 import (测试断言无第三方 import)
- BR-002 (0600/密钥不回显) -> 审计: 落盘权限测试 + 输出 grep
- BR-003 (session 命名无地址) -> 审计: 命名函数单测
- BR-004 (回执语义措辞) -> 审计: 文档 grep
- BR-005 (容器 env 名不变) -> 审计: swt.py 常量 grep 测试
- BR-006 (1MB) -> 已转行为场景 AC-021
- BR-007 (扩展不重实现) -> 审计: pi-extension 源码扫描 (只允许 subprocess 调脚本, 无协议重实现)
- BR-008 (文档存在性) -> 审计: reference/ grep
- BR-009 (fleet.key 0600/ssh 分发) -> 审计: 落盘权限测试 + join-fleet 仅走 ssh 的源码扫描

## 安全策略

- 认证: session HMAC 签名 (±5min 窗) 沿用; post 新增 `from == 签名 session` 校验; 邻居 shared_key 沿用; 舰队密钥 HMAC 挑战应答入群; admin 口硬绑回环 + token.
- 授权: exec 指令集白名单沿用, pull-window 绑定放宽为 session id 或容器名; sessions 只读端点不泄密钥.
- 密钥: 一切密钥/凭证落盘 0600; 舰队密钥只经 ssh 分发; 链路密钥两两独立; admin 列表不回显密钥.
- 隐私/脱敏: status/列表脱敏; 来信不可信输入声明保留.
- 边界: 单信 1MB 上限; 零确认入群明确不做.

## 非功能要求

- 投信应答: 洪泛判定预算 2s, 任何邻居组合下 CLI 10s 内必有结论 (验证口径: AC-008/AC-010 场景).
- 长轮询 hold 20s 沿用; 取信退避上限 5s 沿用.
- 可观测性: serve 关键事件 (转发失败/邻居不可达/滞留丢弃/换址) 打 UTC 时间戳日志行.

## 关键流程

**投递状态机**: 投信 → 本机排队 (queued_local, 送达回执) / 洪泛邻居 (2s 预算内 forwarded/forwarded_partial, 否则 staged_pending 后台 5s 重试) → 邻居不可达滞留 (上限/TTL 清扫) → TTL 到期丢弃 + 失败回执; 取信 ack → 已读回执. 回执反向走同一路由, 确定性 id 去重, 不递归.

**取信守护时序**: 扩展子进程取信 (阻塞) → 来信注入 followUp+triggerTurn → agent_settled → 再取 (自动回执上一封) → 循环; stop/会话关闭杀子进程.

**自组网时序**: serve 起 → 周期发信标 + 听信标 → 新指纹 → hello 握手 (舰队密钥互证) → 协商链路密钥建邻居 (同名 upsert); 本机地址变化 → 旧链路密钥签名宣告 → 邻居验签更新.

## 决策引用

- docs/changes/mailbox-standalone/DECISIONS.md: D001-D017
- docs/changes/swt-mailbox-mesh/DECISIONS.md: D001-D020 (其中 D001/D002 经本变更部分修订)
