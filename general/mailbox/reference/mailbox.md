# 信箱配置与排障

首次配置非 pi 端点, 管理服务/邻居或排查通信失败时读本文件. 日常收发规则在 [SKILL.md](../SKILL.md); pi 会话身份在 [pi.md](pi.md); 展示页查询/代开在 [web.md](web.md); 拉窗在 [pull-window.md](pull-window.md). 下文命令使用主文件定义的 `<脚本>`.

## 服务与凭据

脚本为单文件标准库实现. 先查相应子命令的 `--help`, 按已装版本操作, 不另写签名/路径推算或取信实现.

- **本机服务**: `uv run python <脚本> serve` 前台运行, 不自带 systemd 或开机启动. 首次缺配置时会注册 `<hostname>-host` 并写本机凭据, 这是机器端点, 不是某个 pi 会话.
- **设备端点**: 在服务所在机器用 `register-session <已确定的设备 session id>` 注册, 将返回凭据安全交给设备. 设备用 `config set server/session/signing_key/response_key` 配置; 密钥从 stdin 输入, 不放命令行或回话正文. 以 `status` 核实配置与服务可达, 只转述必要的脱敏状态.
- **容器接线**: 调用 `use-sandbox-worktree` skill 管理 birth/terminate 接线. birth 为容器注册带随机后缀的接线 session 并注入 `SWT_MAILBOX_URL`/`SWT_SESSION_*`; 容器内 pi 用它认证注册各自的 pi 会话 id, 不将接线 id 当 pi 收件地址. terminate 注销接线及其名下所有 pi session. 接线缺席会告警, 不等于 birth 失败; 在接线恢复前报告不能投信. 现存容器重入不重写注入凭据.

默认数据位于 home 下 `.agents/mailbox/`, 路径覆盖以运行配置/脚本为准; 用已有命令取得实际路径与端口. 显式 `MAILBOX_CONFIG` 优先且失败不回退容器身份; 未显式选配置的非 pi 裸 CLI 保留容器 env 优先的兼容行为. 凭据文件按 0600, 所在目录按 0700 保护; `discover`/注册应答可能含 admin token 或密钥, 仅供自动化或安全配置消费, 不粘贴到公开输出. 旧路径迁移由脚本处理, 无需手动维护两套配置.

## 非 pi 手动收信

已有凭据后, `uv run python <脚本>` 缺省取信: 长轮询等一封, 输出正文与处理指引后返回. 处理完再次调用会自动回执上一封并取下一封. 需要有限等待/批量取信时查 `--timeout`/`--count`, 分清"到时无信"和失败.

同一收件人只用一个预期的收信端; 独立 CLI 端点使用各自的凭据和取信状态. pi 用守护分支, 不把本节的阻塞循环搬进 pi.

## 排障顺序与状态含义

先核对实际 session/配置, 再用 `status` 查可达性, `presence` 查目标在线, 最后查邻居/滞留与服务日志. 保留信件 id 追踪同一封信, 不因没有回信直接重发任务. 完成标准: 能说明失败在身份, 服务, 对端收信还是跨机转发, 或给出尚未确认的环节及所需协助.

- **命令/接口不匹配**: 文件已更新不代表运行中的 serve 或 pi 扩展已更新. `ensure-session` 缺接口, 或 `presence` 查询失败时先核对实际版本/错误, 不把查询失败当离线或 `unknown`. 按已有维护授权同步对应版本, 重启 serve/重载 pi 后重试; 重启会丢信, 先说明影响. 没有维护入口或权限则报告阻塞.
- **在线快照**: 服务按取信/心跳判断在线, 状态不持久. 心跳/过期参数及邻居查询预算在脚本中定义; `presence --json` 可供程序消费. 邻居都不认识目标才返回 `unknown`; 在线只说明近期有接收活动, 不证明业务已处理.
- **离线拒发**: `send` 自带预查及本机并发兜底, 但不能代替写正文前的显式查询. `--force` 跳过在线限制, 不修复地址或路由; 是否使用按主文件的投信纪律决定.
- **空目标**: 服务优先选择在线的最近取信 session, 都不在线才退回历史最近取信者. 它不代表我当前设备或原会话.

| 观测 | 能证明什么 |
| --- | --- |
| send 返回入队/转发/暂存 | 命令报告的那一跳已受理, 不保证最终送达 |
| 送达回执 | 信进入收件方本机队列 |
| 已读回执 | 取信端已 ack, 不是业务验收 |
| 失败回执 | 信因 TTL 到期被丢弃 |

回执的边界是 **收到 = 确定发生, 缺席 = 未知**. 回执由服务生成, 取信端自动处理, 无需人工再发确认. 信件/租约/滞留全在内存, serve 重启即丢; 租约超时可重投, TTL 超时或滞留队列超限会丢弃. 回执自身也可能丢失, 重启丢信时失败回执发不出. 对任务是否完成, 仍以业务反馈与必要查验为准.

## 跨机连通与邻居

跨机路由由各机器的信箱服务按共享密钥互认并转发, 不要求取信端直接连接对端机器. 从本机取信服务探测实际端口; 远端访问按已确认网络条件选择加密通道. admin 口只监听服务机器的 loopback, 容器内不能直接使用.

**单机取远端信**: 可建立 SSH 本地转发, 让本机配置的 server 指向转发端口. **信箱之间建邻居**: 每个投信方向都需可达的邻居地址; 单向能连不等于双向互投已通. 双方无直达路线时, 由能访问对端 SSH 的一方建立反向转发, 将对端一个已确认空闲端口接回本端信箱, 再把邻居地址指向隧道落点:

```text
ssh -N -R <对端隧道端口>:127.0.0.1:<本端实际信箱端口> <对端 SSH 目标>
```

隧道端口取合法空闲值且避开信箱扫描区间. 在落点端信箱配置目录的 `tunnels/` 下留标记文件, 记录发起 session, 端口和时间, 撤除时移除, 避免重复占用. 曾遇到发起设备挂起遗留远端监听, 长期隧道需检查 SSH `ClientAliveInterval`/`ClientAliveCountMax` 保活与失活回收. 完成标准: 两端实际投信可达, 不是只有 DNS 解析或 SSH 连接成功.

**邻居持久性**: admin 写入的邻居存入 DB; `neighbors.json` 只在启动时导入, 不会自动回写. 文件来源的邻居要永久删除, 同时删文件种子; 已由 admin 修改的同名邻居重启时以 DB 为准. 换址时同步核对防火墙许可和邻居地址, 再补投滞留信.

**同网段自动组网**: `join-fleet <已入群设备 SSH 目标>` 经 SSH 取共享的 fleet key. 服务用它认证发现的邻居并派生独立链路密钥. 未配置 key 时 serve 可能自动生成本机 key, 不代表与其他设备属于同组; 跨网段也不能依赖 UDP 发现. 已有邻居可用认证换址更新地址, 无路由时仍需网络通道. 拉窗的设备前提与历史兼容性见 [pull-window.md](pull-window.md).

## 管理接口与协议维护

优先用 `discover`/`register-session`/`ensure-session`/`revoke-session` 完成已有机械操作. 手动管理无 CLI 覆盖的资源时, 从本机状态取得实际 admin 地址和 token, 用 `X-Admin-Token` 认证. 资源入口:

| 资源 | 接口 |
| --- | --- |
| 邻居 | `GET/POST/PATCH/DELETE /admin/neighbors` |
| 滞留信 | `GET /admin/pending`, `POST /admin/pending/retry`, `POST /admin/pending/drop` |
| session 与在线 | `GET /admin/sessions`, `GET /admin/presence` |
| 指令集 | `POST /admin/whitelist` |

容器注册 pi 信箱另走信箱口 `POST /mailbox/sessions/ensure`, 不开放 admin 口. 请求用接线签名密钥签 `session\nsig_ts\nensure-session\n目标pi-id`, 响应用接线响应密钥验签. 已有 id 只能由原接线身份重取, 冲突/已吊销均拒绝; 子会话不能再注册子会话. 父子归属随凭据入库, 重启保留, 注销父身份会级联注销子会话.

具体请求/响应以 `<脚本>` 对应 handler 为准, 不手工重实现 HMAC, 重投或去重. 排障看 stderr 中 `forward-failed`, `address-updated`, `address-update-rejected`, `letter-expired` 等事件及其信件/目标字段.

`exec` 只在指令集范围内直批, 集外信保留原类型并标记 `downgraded`, 收信提示须按 `request` 呈现. `swt.pull-window` 的形状与绑定规则单源于 [pull-window.md](pull-window.md). 仓库维护时变更这些安全规则需跑 `tests/test_mailbox_whitelist.py` 与对应收信测试; 不将提示词审读当作协议验证.
