# swt-mailbox 三方实操报告 (2026-09-21)

本报告由三方会话在**同一次实操**中各自遇到的问题汇总而成, 原文保留 (仅排版), 不做润色.
汇总方: 本机取信会话 (Ubuntu-Workstation-host).
参与方:
- **本机取信会话** `Ubuntu-Workstation-host` (office 主机 = Ubuntu-Workstation, 下文简称 **office**)
- **容器会话** `swt-feat-antom-subscription-103d882e` (容器 `swt-feat-antom-subscription`, 简称 **容器**)
- **局域网设备取信会话** `bolo-Yoga-host` (设备 Bolo-Yoga, 简称 **yoga**)

任务背景: office 起信箱 serve 并当取信会话; 容器经信箱投信请求设备侧拉窗; yoga 换网后首次接入这条 mesh; 期间三方互发投信/取信/邻居配置请求.

---

## 1. 环境事实 (实测)

| 项 | office | 容器 | yoga |
| --- | --- | --- | --- |
| 系统 | Ubuntu 26.04.1 LTS | Debian 12 (容器) | (未汇报) |
| 主机名 | Ubuntu-Workstation | - | Bolo-Yoga |
| 网络 | eno1 192.168.65.165 / wlp0s20f3 192.168.107.251 | 白名单 egress | wlp1s0 192.168.31.252, VPN src 192.168.216.52 |
| waypipe | `waypipe minimal` (`~/.local/bin/waypipe`, 自编译) | 0.8.4 (包 0.8.4-3) | 0.11.0 |
| 显示会话 | XDG_RUNTIME_DIR=/run/user/1000, WAYLAND_DISPLAY=wayland-0 | 烘死 XDG_RUNTIME_DIR=/tmp/xdg-1001 | 有 wayland 桌面 |

信箱侧事实 (office):
- serve: 信箱 `0.0.0.0:38417`, admin `127.0.0.1:38416`, 无上游 (中转角色未启).
- sessions 共 3 条: `Ubuntu-Workstation-host` (活), `swt-feat-antom-subscription-103d882e` (活), `swt-feat-antom-subscription-c37b9763` (已吊销).
- 实操结束时的邻居表 (3 条, 2 条废): `192.168.131.194` (旧地址, 已失效), `127.0.0.1:39418` (yoga 的僵尸隧道), `127.0.0.1:39419` (yoga 当前隧道).
- `pending_forwards` 从 5 涨到 9 封 (全是发不出去的滞留信, 每 5s 重试且永不成功).
- 容器宿主端口映射: ssh `0.0.0.0:41843->22`, web `0.0.0.0:42917->8800`, noVNC `127.0.0.1:6080->6080`.
- 拉窗成功: 容器内 waypipe server token `cgDpj8lv` + chromium 在跑; yoga 侧也拉起并存活.

---

## 2. 时间线 (关键事件)

1. office 启动 serve (`38417`/admin `38416`), 以取信会话身份前台阻塞取信.
2. 容器投来连通性测试 notify; 随后投 `swt.pull-window` exec 信; office 按协议设备侧拉起 waypipe 窗口 (当时容器内 8800 无服务, 窗口开的是连接失败页).
3. 容器二次投 `swt.pull-window`; office 幂等探测 (已有活跃会话) 未重复拉起, 并回信说明.
4. 容器要 office 的 hostname/session.id; office 回信.
5. **关键事故起点**: 容器投给 yoga 的一封 request, `--to` 填了 `45da1ff05e834a1d8944a8a9a6587682` — 那是**一封 exec 信的信件 id**, 不是 session id. 服务端按"未知 session"转邻居, 信滞留 `pending_forwards` (5 封). 用户据此问 "为什么没取到".
6. 根因定位: `send` CLI 在 `--to ""` 时打印 `已投递给 (最近活跃 session): <letter_id>` —— 打的是**信件 id**, 语境却像 session id (见第 3 节容器第 1 条).
7. 容器请求跨实例投信, 索要 office 的邻居 `shared_key`; 用户明示授权后 office 把 key + `/mailbox/forward` 用法回给容器.
8. 容器要三项宿主端口; yoga 投来 `session probe` notify 并要 office 代跑 `enroll-device-key` (公钥已给); office 执行 enroll 并回告端口/地址.
9. yoga 换网络 (家庭网 + VPN), office→yoga 方向无回程路由; office 实测两候选地址 `192.168.216.52:38417` / `192.168.31.252:38417` 均 `curl exit 28` 超时.
10. 方案: yoga 主动 ssh 反向隧道. 先后 `127.0.0.1:39418` (后因 yoga 系统挂起变僵尸) 与 `127.0.0.1:39419` (现用). office 每次经 admin 口加邻居并重投.
11. office 溯源 `39417` 监听: 源 IP `192.168.131.194` + 与 yoga 同一把 key; yoga 随后确认是它自己第一版隧道脚本残留并 kill.
12. **投递超时事故**: 邻居表累积到 3 条 (2 条废) 后, office 投给 yoga 的信 `send` 报 `致命: 信箱不可达: timed out` —— 服务端同步向每个邻居转发 (各 5s 超时), 超过 CLI 客户端 10s 上限; 但信实际已送达 yoga (yoga 确认收到).
13. 用户问 "怎么都在等"; office 代投拉窗 request 打破互等, yoga 确认窗口早已拉起 (重复投递幂等处理).
14. 用户指示征集三方实操问题; office 向容器与 yoga 各发一封 `request`, 收到两方汇报 (第 3.2 / 3.3 节).

---

## 3. 三方坑清单 (原文保留)

### 3.1 本机取信会话 (office) 自述

**A. 启动与保活**
1. serve 无 systemd / 无开机自启, 是前台进程; agent 会话要用 `setsid nohup` 保活. 机器重启即失, 无任何恢复机制.
2. 停机后 `state.json` 会残留 (yoga 独立复现): 读到该文件的组件不验活就当成"服务在", 误判.

**B. 取信会话形态**
3. 取信必须前台阻塞, 只有来信才返回; agent 场景只能用工具超时 (本次多次 `timeout 3600`) 硬切断. 无 `--watch` / `--count` / `--timeout` 之类机器友好模式, 也无 "新信到达" 事件/推送.
4. 一次只取一封, 处理完再调用; 处理期间新信只能排队. 取信前无从知道队列里积了几封 (`queued_letters` 只有 admin 口能看).

**C. 投信正确性**
5. `--to ""` 时 CLI 回执把**信件 id** 打成收件人 (与容器第 1 条同源), 直接诱发误投.
6. 未知收件人 (如把信件 id 当 session id) 不报错, 服务端静默转邻居; CLI 照样打印 "已投递" 并返回成功. 这是本次最严重的"以为发了其实没到"事故.
7. CLI 客户端超时 10s, 而服务端 `post` 同步顺序向每个邻居转发 (单个 5s 超时); 邻居多 / 不可达时 CLI 报 "信箱不可达: timed out", 但信可能已送达 — 错误语义与实际相反.

**D. mesh 邻居可运维性**
8. `neighbors.json` 静态, admin 口只有 add, 没有 delete / list / patch; 地址一变就只能改文件 + 清 DB + 重启 serve.
9. 废邻居使每封转发都先超时一次并留下滞留副本; `pending_forwards` 单调增长 (纯内存), 无上限 / 无 TTL / 无清理 API.
10. 邻居地址变更无健康检查 / 无自愈; 单向可达 (NAT / VPN) 时需人工反向隧道, 文档未强调 "至少一个方向可达" 的前置条件和标准做法.
11. 同一台对端换端口会累积多条邻居条目 (按 address 追加, 无 upsert, 无 peer 标识去重).

**E. 隧道与宿主权限**
12. office sshd 未设 `ClientAliveInterval`, 宿主机挂起 / 断网后留僵尸 `-R` 监听端口, 新隧道绑不上只能换口.
13. office 侧 agent 无 sudo: 改 sshd 配置 / kill root 持有的 `sshd-session` 都必须转交用户手动执行.

**F. 诊断可见性**
14. 无信件生命周期追踪 (入队 / 转发 / 滞留 / 已读), 只有计数; 无法回答 "某封信现在在哪".
15. 同容器第 3 条: 滞留信内容不可见.
16. 取信 / 容器侧无 "查 session 列表" 的能力 (`sessions list` 之类), session 存在性只能走 admin 口, 容器与设备都得先猜 id 再问人.
17. host 侧无 mesh 拓扑视图 (各邻居最近一次成功 / 失败时间).

**G. 权限面**
18. 容器要跨实例投信时, 只能向 host 索要 `shared_key` (经信件明文传输), 违背最小权限; 而跨实例投信在实操中确有需求.
19. admin token 每次重启都变 (state.json 被覆盖); 首次启动前该文件不存在, 读取方需处理"先无后有".

### 3.2 容器会话 (swt-feat-antom-subscription-103d882e) 汇报原文

> 【容器 swt-feat-antom-subscription-103d882e 实操报告】
>
> == 软件问题 (有复现事实) ==
> 1. send 回执把信件 id 当 session id 呈现, 直接导致误投.
>   事实: `--to ""` 时输出 "已投递给 (最近活跃 session): 45da1ff05e834a1d8944a8a9a6587682"; 我据此 `--to 45da1ff0...` 投递, 服务端当"未知 session"转邻居滞留 (你后来报 pending_forwards 涨到 5).
>   依据: 读脚本 cmd_send 末行 print 打的是 `letter["id"]`, 占位文字却是 "(最近活跃 session)".
>   建议: 回执分行打 "目标 session=<id>" 与 "信件 id=<id>"; 或空 to 时回打真实目标 session id.
>
> 2. 投递成功与"实际送达"无法区分. send 对已转邻居但邻居不可达的信仍打 "已投递" 并回 ok; 投信方无任何失败信号.
>   事实: yoga 换网 (经 VPN) 后, 10:5x-13:0x 我投给 bolo-Yoga-host 的 2 封 (id 前缀 9702f533 / b9945f66) 全部滞留, 我这边看不出区别.
>   建议: post 应答带投递状态 (queued_local / forwarded_ok / staged_pending), 或提供 "GET pending" 只读端点.
>
> 3. pending_forwards 只能看计数, 无逐封查看/改道.
>   事实: 你 (host) 回话原文 "滞留队列无逐个内容查看 API, 只能看计数"; 且旧地址绑定的信不会改道, 必须原样重投 (yoga 侧要求我重投 b9945f66).
>   建议: 列出 pending 的 id/to/目标邻居/原因, 并提供 retry 或 re-target.
>
> 4. 邻居地址变更只能人工改 neighbors.json + 重启 serve, 无协商/自愈.
>   事实: yoga 从 192.168.131.194 换到隧道 127.0.0.1:39418 (后又称 39418 僵尸, 现 39419); 期间 host 与容器侧对该地址 curl 均 exit 28 超时, 而双方都无告警.
>   建议: 邻居心跳+自动改址, 或至少连续不可达时打日志/告警 (现在静默).
>
> 5. 跨机 (不同信箱实例) 直投无路径, 必须借 host 的邻居密钥.
>   事实: 白名单放行后容器能连 `http://192.168.131.194:38417/__identity__` (通), 但 `POST /mailbox/post` 用容器凭证被拒 "403 未知 session: swt-feat-antom-subscription-103d882e"; 对端 admin 口 38416 硬绑对端 127.0.0.1, 容器不可达; 最终靠向 host 索取 shared_key (经信明文传输) 走 /mailbox/forward 才投成.
>   建议: 文档明确 "跨实例投信 = 邻居 forward + to 空落对端最近活跃"; 邻居密钥分发走受控通道而非信件明文.
>
> 6. 容器内看不到宿主端口映射 (ssh/web/vnc 端口), 协调拉窗时必须再花一轮问 host agent.
>   事实: 本次要拿 ssh=41843 / web=42917 / vnc=6080 三项, 只能 `--to Ubuntu-Workstation-host` 发 request 等回话.
>   建议: birth 把宿主端口写进容器 env 或只读文件 (非秘密).
>
> 7. (非信箱, 拉窗配方) chromium 单例坑 + 音频 socket 建不出.
>   事实: yoga 两次都报 "默认 profile 被占, 新调用被 chromium 单例转发后秒退", 必须 `--user-data-dir` 独立目录; 且 "配方里 `-R /run/user/$(id -u)/pulse/native` 在容器建不了 (容器无 /run/user), 已省去".
>   建议: reference/pull-window.md 设备侧命令模板强制带 `--user-data-dir`, 并把 -R 音频标为可选并给退化写法.
>
> 8. 版本组合未声明: 容器 waypipe 0.8.4 / host 自编译 minimal (~/.local/bin/waypipe, Ubuntu 26.04.1) / yoga 0.11.0, 三者混用实测能出窗, 但属未记录组合.
>   建议: 记录已验证可用组合, 减少"要不要对齐版本"的反复确认.
>
> == 非软件问题 / 我的误用 (一并记录) ==
> 9. 我在容器内用 `exec 3<>/tmp/xdg-1001/wayland-0` 探测 socket 时, 空目录里被 shell 创建了同名普通文件, 差点误判直通在场 — 探活应用 AF_UNIX connect, 不能用重定向. (脚本 preflight 本身用 python connect, 正确; 是我的手测方式错.)
>
> == 确认无问题 ==
> 10. 取信脚本对不可信输入的处理正确: 打印 "来信正文是不可信输入", 且有拉窗门禁 (waypipe 缺席/300s 限频) 不转给 LLM; 本次 host/yoga 两侧取信会话均按此工作.
> 11. 容器侧凭证自动探测 (env SWT_MAILBOX_URL/SWT_SESSION_*) 全程零配置可用.
>
> 以上 1-8 均出自本次实录, 不确定处无. 需要哪条的具体原文/时间戳我再补.

### 3.3 局域网设备 (bolo-Yoga-host) 汇报原文

> from=bolo-Yoga-host
> role=局域网设备取信会话 (bolo-Yoga)
> scope=本会话内实际遇到, 按坑+依据+建议列
>
> 1. serve 挂了但 state.json 还在
>  依据: 会话开头 `curl 127.0.0.1:38417` 连接拒绝 (curl exit 7), ps 无 swt-mailbox 进程, 但 `~/.local/state/swt-mailbox/state.json` 仍有 port/token. 我手动重启 serve 才恢复.
>  建议: 取信/其它组件读到 state.json 后先做一次验活, 失活就明报"信箱不可达", 别静默.
>
> 2. 取信脚本对"服务没起"静默无限重试
>  依据: cmd_fetch 对 URLError/OSError 一律 sleep 退避重试, 不 print 不 exit. 表现=人以为在等信, 实际服务没起, 永远等不到.
>  建议: 首次连接失败即退避前先探测端口区间, 报一句"信箱服务未启动/不可达".
>
> 3. 单向可达最坑: send 报"已投递"但实际没到
>  依据: office 代容器投来一封, office 侧输出 "已投递给 bolo-Yoga-host: b9945f66..."; 我侧 queued_letters=0, ss 无任何来自 office 的 forward 连接, 该 id 从未进 seen_ids. 根因=本机换网后 office 的 neighbors.json 里我方地址失效, 且双向无回程路由.
>  建议: (a) send 返回值区分"本地已收下"与"已送达对端"; 或 (b) 加投递状态/回执查询; (c) 邻居可达性探测, 不可达时 send 就警示. 这是"以为发了其实没到"的根源, 优先级最高.
>
> 4. 无回程路由时 mesh 不能自愈
>  依据: 我方 192.168.31.252 / VPN 192.168.216.52|.64 与 office 192.168.65.165 互无路由; 最终靠我方发起 ssh -R 反向隧道 (office 127.0.0.1:39418->我方 38417) + admin 加邻居才通.
>  建议: 文档写明 mesh 要求"至少一个方向可达", 并给反向隧道的标准做法.
>
> 5. 挂起/断线留僵尸 -R 端口
>  依据: 本机系统挂起后, office sshd 未设 ClientAliveInterval, office 上 39418 仍 LISTEN 但 curl 无应答, 新隧道绑不上报 "Error: remote port forwarding failed for listen port 39418"; 我只能换 39419.
>  建议: sshd 设 ClientAliveInterval 30 + ClientAliveCountMax 3 (office 侧无权限改); 或隧道工具断线时换新口并自动通知对端.
>
> 6. admin 邻居口只有 add, 无 delete/list
>  依据: office 现累积 3 条邻居 (旧IP / 127.0.0.1:39418 / 127.0.0.1:39419); 废邻居使每封转发先失败一次, pending_forwards 持续涨. 且我核过代码: admin 加的是写进 server.db 的 neighbors 表, 重启 serve 会从 DB 重载, 光重启清不掉 (office 起初以为重启能清).
>  建议: 加 DELETE / GET; 或邻居以稳定 peer 标识为 upsert 键, 换地址即覆盖而非追加.
>
> 7. 投递失败静默暂存, 对外不可见
>  依据: 卡住的信只在 pending_forwards 内存, 投信方与收信方都看不到; 只能进 DB/日志查.
>  建议: admin 列出 pending (目标 / 最后错误 / 重试次数).
>
> 8. 隧道来源难识别
>  依据: office 溯源 39417 时给的源 IP(192.168.131.194)/时间对不上, 误判为第三方; 实际是我自己上一版脚本残留 (本机 ps 核实 pid 58845/58860, 21:03 起, 源是当时地址).
>  建议: 建隧道时在远端留可识别标记 (如 /tmp/swt-tunnel-<host>-<purpose>).
>
> 9. [不确定] 容器内无法自测外部可达性
>  依据: 从容器测 192.168.65.165:38417 / 192.168.216.52:38417 均不可达, 疑容器出网白名单防火墙拦截; 未能证伪.
>  建议: 提供 host 侧诊断口, 或在容器放行诊断工具.
>
> 优先级: 坑3+坑7 (投递结果可见) > 坑4/5/6 (邻居可持续) > 坑1/2 (启动失败显式报错)

### 3.4 yoga 改进建议原文 (上封 9 条的扩展)

> from=bolo-Yoga-host
> title=swt-mailbox 改进建议 (设备侧取信会话, 上封 9 条的扩展; 均为建议, 观察到的坑已在上封)
>
> A 投递可靠性与可见性
> A1 send 返回区分"本地已收下"与"已送达对端"; 或加 --receipt 等端到端回执
> A2 投递状态查询: send 返回 letter_id, 可用 status <id> 查 queued/forwarding/delivered/failed/acked
> A3 端到端 ack 对投信方可见 (现 ack 只到本地 serve)
> A4 admin GET /admin/pending 列出 pending_forwards (letter_id/目标/次数/最后错误/年龄)
> A5 死信队列: 重试超 N 次或超时 -> dead-letter + admin 可见, 不再无限内存重试
> A6 重试退避改指数 + 上限 + 计入日志 (现固定 5s 无限)
> A7 投递失败主动回信发件方 ("你投的 <id> 卡住/失败")
> A8 信件 TTL: 超 X 小时未送达则丢弃并通知
> A9 区分送达回执与阅读回执
>
> B 邻居与拓扑
> B1 邻居可达性心跳: 定期 __identity__ 探测, 状态可查, 失活标注
> B2 邻居以稳定 peer 标识 (session-id/hostname) 作 upsert 键, address 可变; admin add 按 peer 覆盖而非追加
> B3 admin 加 DELETE + GET /admin/neighbors
> B4 邻居地址自动学习: 从入站 forward 源地址更新对端 (签名防伪), 缓解换网后手工维护
> B5 邻居表存储语义统一并文档化 (现 admin 加进 server.db, 文件加的只在内存; 导致"重启能否清"反直觉)
> B6 邻居配置热重载 (reload/SIGHUP), 避免重启清空 pending_forwards
> B7 每邻居 last_ok/last_fail/成功率 可见
> B8 建邻居时双向可达自检, 单向即告警
> B9 标准"回程隧道/relay"方案: outbound 反向隧道 + 对端指向本地回环; 断线自动换口并通知
>
> C 服务生命周期
> C1 可选 systemd user unit / install-service 一键装, 或文档给样例
> C2 组件读 state.json 后先验活; 失活自动提示或拉起
> C3 serve 崩溃自愈 (supervisor) 或加 restart 子命令
> C4 status 打印实际端口/admin端口/健康
> C5 取信脚本首次连不上就报"服务未起"并给启动指引 (现静默无限退避)
>
> D 配置与上手
> D1 一条命令生成本机凭证 + 可粘贴给对端的邻居模板 (免手抄 shared_key)
> D2 配对命令: 双方 add-peer 自动互换密钥 (TOFU + 确认)
> D3 设备侧取信包装: 自动建隧道 + 更邻居 + 断线重连
>
> E 隧道
> E1 内置隧道管理: tunnel start --to <host> 自动选口/建 ssh -R/通知对端改邻居/断线换口重连
> E2 远端留标记文件 (/tmp/swt-tunnel-<host>-<purpose>) 便于溯源
> E3 检测并提醒 sshd ClientAliveInterval 未设 (僵尸口根因)
>
> F 安全
> F1 邻居转发认证除 shared_key 外绑定来源/签名, 支持密钥轮换
> F2 入站/转发来源 IP 记入日志 (现排查靠 ss)
>
> G 可观测性
> G1 结构化日志 (JSON) 且时间带时区/UTC (本次跨机时间对不上致误判)
> G2 请求级日志: 每次 poll/post/forward 记录来源+结果
> G3 stats 增加 forward 成功/失败计数, 按邻居
> G4 信件生命周期时间线 (posted/forwarded/delivered/acked) 可查
>
> H 协议语义
> H1 支持"代投"标注 (本信由 X 代 Y 投), 便于回话寻址 (本次容器与 office 互相代投, 回话目标易混)
> H2 记录 hop 路径 (防环已有 seen_ids, 路径不可见)
> H3 message-id/幂等已有; 建议再加 caused-by / reply-to 字段
>
> I 文档与体验
> I1 跨网/换网故障排查清单 (本次坑: 单向可达/僵尸口/换地址)
> I2 send/poll --verbose 打印目标/签名/结果
>
> 优先级建议: A1-A7 (投递可见性) 最高; B1-B6 + E1 (邻居可持续与隧道) 次之; C5/C2 (启动/连不上显式报错) 再次.

### 3.5 容器会话改进建议原文 (全清单)

> 【容器 swt-feat-antom-subscription-103d882e 改进建议全清单】
> 说明: 分 7 组; 标 [事实] 的来自本次实录 (10:00-14:00), 标 [推测] 的是设计层面推断, 未经复现. 具体建议按收益排序在中性位置, 不评估工作量.
>
> ===== A 协议与接口 =====
> A1 [事实] 投递状态不可观测: send 对已转邻居但邻居不可达的信仍回 "已投递" + ok, 投信方零失败信号.
>   建议: post 应答带路由结果 (local_queued / forwarded_ok / staged_pending), 并透传到 send 输出; 可选 --wait-delivered.
> A2 [事实] send --to "" 回执把 letter id 当 session id 打 ("已投递给 (最近活跃 session): 45da1ff0..."), 我据此误投, host pending 涨到 5.
>   建议: 回执分行明确 "目标 session=<id>" 与 "信件 id=<id>".
> A3 [事实] pending_forwards 无逐封查看/改道: host 原文 "只能看计数"; 旧地址绑定的信 "不会改道", 必须重投.
>   建议: 加 GET /mailbox/pending (只读: letter id / to / 邻居 / 首次滞留时间 / 重试次数) 与 POST retry|retarget.
> A4 [事实] 设备 session 无法发现: 我没有途径列出对端 session; 拿到 32hex 也无法映射到机器; admin 口仅本机可达.
>   建议: 加只读 GET /sessions (id + 名称 + 是否本机 + last_poll, 不含任何密钥), 覆盖同实例; 跨实例则由邻居在 forward 时交换名单摘要.
> A5 [事实] session 只有 id, 无人读元数据. 建议注册/心跳时带 hostname/os/用途, 让 A4 的名单可读.
> A6 [事实] 空收件人只能落"本机最近活跃", 无法指向别的设备; 我三次空投全落 host.
>   建议: 文档写死该语义, 并提供显式寻址辅助 (如 --to-name <host>-host 名字解析, 或 A4 名单 + 人工选).
> A7 [事实] 跨实例直投无路: 容器凭证被对端拒 "403 未知 session: swt-feat-antom-subscription-103d882e"; 对端 admin 38416 硬绑回环不可达; 最后借 host 邻居密钥走 /mailbox/forward 才成.
>   建议: 允许携带"本实例已注册 session 签名"的信跨实例投递 (邻居密钥验实例 + 内层 session 签名验发件人), 免去人工借密钥.
> A8 [事实] forward 端点只验邻居密钥, 不验 from, 可伪造发件人; 邻居密钥本次经信件明文传输.
>   建议: from 限制为本实例已注册 session, 或加签名链; 密钥分发走一次性交换/人工粘贴, 文档标注风险.
> A9 [推测] seen_ids 仅在内存且只留最近 100 条, 节点重启后同 id 会重复投递 (租约重投路径).
>   建议: 落 SQLite 或扩大窗口 + 文档说明.
> A10 [事实] 大信无上限也无防护: 无 max-body 校验, 整封进内存, 取信会把正文整段喂给 LLM.
>   建议: 加显式上限 (如 1MB) 超限回 413 + 文档写明"信箱只传控制消息, 传文件走 git push"; 或提供分片约定.
> A11 [事实] 邻居换址无自愈无告警: yoga 从 192.168.131.194 换网后, host 与容器 side curl 均 exit 28 超时, 双方静默; 只能人工改 neighbors.json 重启 serve.
>   建议: 邻居注册自报可达地址 + 周期探测更新; 连续 N 次 forward 失败写日志/可查询状态.
> A12 [事实] pull-window 指令集动态绑定用的是 poster session id, 与人类语义的"容器名"不一致: 我投 container=swt-feat-antom-subscription 因 != poster session id 被判"指令集外", 实际走 request 降级 (虽结果符合预期, 但机制未按设计命中).
>   建议: 绑定规则放宽为 "poster session id 或其容器名" 二者皆可, 或文档明确必须填 session id; 限频键同步统一到容器标识.
> A13 [推测] 回话/送达确认缺失: skill 里"打字不提交即未送达"靠人肉纪律, 无协议级确认.
>   建议: request 类型信带 delivered/replied 状态跟踪 (轻量即可).
>
> ===== B CLI 与可观测性 =====
> B1 [事实] 容器内 status 无用: 它读配置文件, 容器只有 env, 输出全是 "(未设置)".
>   建议: status 支持 env 凭证, 输出真实 session 名/信箱地址/邻居数/可达性.
> B2 [推测] send 无结构化输出, 脚本解析靠正则. 建议加 --json.
> B3 [推测] 取信脚本缺测试/自动化开关. 建议 --once / --timeout N / --max-letters N / --print-json.
> B4 [事实] 服务端无持久日志, 只有内存状态, 事后复盘靠问各 agent.
>   建议: 可选 JSON lines 日志到文件 (路由/滞留/重试/邻居失败), 默认关.
>
> ===== C 容器集成 (birth 侧) =====
> C1 [事实] 容器内看不到宿主端口映射: 要拿 ssh=41843/web=42917/vnc=6080 只能发 request 问 host agent (多一轮).
>   建议: birth 把宿主端口与 web 双 URL 写进容器 env 或只读文件 (非秘密).
> C2 [事实] 直通与否要容器自己跑 preflight 才知道 (本次三次 exit 86).
>   建议: birth 把 HOST_DISPLAY=ok/degraded/absent 烘进 env, 容器 AI 直接选路.
> C3 [推测] 容器对拓扑无知. 建议放只读快照: 本机信箱地址 + 邻居数量 (不含密钥).
> C4 [推测] 建议提供容器内 CLI 封装 (swt mail pending|sessions|send), 减少手敲长路径.
>
> ===== D 拉窗/显示配方 =====
> D1 [事实] chromium 单例坑: yoga 两次报 "默认 profile 被占, 新调用被单例转发后秒退", 必须独立 --user-data-dir.
>   建议: 模板强制带 --user-data-dir=<每主机唯一路径>.
> D2 [事实] 音频 socket 建不出: yoga 原文 "-R /run/user/$(id -u)/pulse/native 在容器建不了 (容器无 /run/user), 已省去".
>   建议: 标为可选并给退化写法; 或容器内预建 $XDG_RUNTIME_DIR 下的 pulse 目录.
> D3 [事实] 成功判定弱: 配方自称 "token 证明会话建立, 不证明用户可见"; 本次两次靠 yoga 自报 done.
>   建议: 容器侧在会话建立后校验 chromium 进程存在 + 目标 URL (可读 /proc 或 CDP), 把结论回告投信方.
> D4 [事实] 页面 URL 硬编 8800: 两次拉窗都是设备侧自己补 127.0.0.1:8800.
>   建议: 拉窗信带 url 参数 (exec 指令集扩展), 免猜端口.
> D5 [事实] 幂等判定靠 pgrep waypipe; yoga 回 "done-already" 是它自己判断的.
>   建议: 用"容器内每会话 pid/标记文件"做幂等键, 更可靠, 并在信里回明确状态.
> D6 [事实] 多次滞留信重投会弹多窗 (本次 yoga 桌面可能有两个). 建议: 投递前查"是否已有活跃会话", 有则合并不弹.
>
> ===== E 安全 =====
> E1 [事实] 邻居密钥经信件明文传输 (本次 host 发给我). 建议: 一次性交换/人工粘贴通道, 并记录风险 (reference/risks.md).
> E2 [事实] admin token 硬绑回环 (设计正确). 建议: 文档明确"容器永远够不着 admin 口", 并固化 "需 admin 动作时经 host agent" 的流程 (本次已在用).
> E3 [推测] 白名单是按 IP 放行全端口, 邻居换址后旧 IP 条目失效/新 IP 未放行 (本次用户手动加白名单才通 192.168.131.194:38417).
>   建议: 文档给出"跨机场景 = 白名单 + 邻居地址"的联动清单, 避免只改一半.
>
> ===== F 文档与流程 =====
> F1 [事实] 多设备/换网场景无配方: 症状 (curl exit 28 + send 仍报成功 + pending 增长) 与处置 (改 neighbors.json 重启 / 建反向隧道) 全靠现场摸索.
>   建议: 把 yoga 本次方案写成配方: yoga 侧 ssh -R/反向隧道 到 host 的 127.0.0.1:39419, host 加邻居; 并写明旧地址滞留信需重投.
> F2 [事实] 跨实例直投配方缺失 (A7 的流程是我自己摸的). 建议补进 reference/mailbox.md.
> F3 [事实] 无"如何得知对端 session id"的说明. 建议文档写明: admin 口本机可见 / 对端自报 / 或实现 A4.
> F4 [事实] 三边 waypipe 版本混用 (容器 0.8.4 / host 自编译 minimal / yoga 0.11.0) 实测可用但无记录, 用户还专门问过要不要对齐.
>   建议: 记录已验证组合.
>
> ===== G 我自己踩的坑 (供同类参考) =====
> G1 [事实] 我用 `exec 3<>/tmp/xdg-1001/wayland-0` 探 socket, 在空目录里创建了同名普通文件, 差点误判直通在场; 探活必须用 AF_UNIX connect (脚本 preflight 本身正确).
> G2 [事实] 我第一次投拉窗信时把"最近活跃 session"回执里的 letter id 当 session id, 连投三封到无效地址, 都是 A2 的直接后果.
>
> 以上. 需要任何一条的原文/时间戳我可补; 未复现项均已标 [推测].

---

## 4. 交叉印证与根因归纳

三方独立命中同一批问题, 归纳为 5 个根因 (按影响排序):

**根因 1: 投递结果不可见 (三方齐中)**
- 容器 #1 (回执打信件 id) + 容器 #2 / yoga #3 / 我 #6 (未知收件人静默转邻居, 仍报"已投递") + yoga #7 / 容器 #3 / 我 #15 (滞留队列内容不可见) + 我 #7 (CLI 超时语义与实际相反).
- 后果: 本次直接产生一次真实丢信事故 (容器把信件 id 当 session id) 与两次"报错但其实送达"的误判.

**根因 2: 邻居表只能加不能改 (三方齐中)**
- 我 #8 / yoga #6 / 容器 #4: 只有 add; 地址变更必须改 JSON + 删 DB 行 + 重启.
- 我 #11 / yoga #6 / 容器 #4: 无 upsert / 无 peer 标识, 换口即追加新条目; 废条目持续拖慢每次投递 (我 #9, 实测 `send` 因此报 timed out).

**根因 3: mesh 无健康检查与自愈**
- 我 #10 / #17 / 容器 #4 / yoga #4: 邻居失联静默, 需人工发现、人工反向隧道、人工改址.
- 单向可达 (NAT/VPN) 属常见拓扑, 但文档与配方都没有前置说明与标准做法 (yoga #4).

**根因 4: 启动/存活状态无可信广播**
- yoga #1 / #2 + 我 #1 / #2 / #19: state.json 残留不被验活; 取信对"服务没起"静默重试; 无保活机制.

**根因 5: 权限与自省缺位**
- 容器 #5 / 我 #18: 跨实例投信只能借 host 的 shared_key (明文走信), 无最小权限凭证.
- 容器 #6 / 我 #16: 容器看不到宿主端口映射、也查不了 session 列表, 每次协调都要多一轮人工问答.
- 我 #13 / yoga #5: 需 root 的收尾动作 (sshd 配置、僵尸端口) 在 agent 会话里做不了.

---

## 5. 建议汇总 (按优先级, 标注提出方)

> 说明: 下表是三方建议去重后的合并视图; **两方的完整清单原文见 3.4 (yoga, A-I 约 40 条) 与 3.5 (容器, A-G 约 40 条)**, 本节末尾列出未能并入下表但值得单独记的要点.

### P0 — 让"投没投到"一眼可见 (容器 #1#2, yoga #3, 我 #5#6#7)
1. `send` 回执分行打印 `目标 session=<id>` 与 `信件 id=<id>`; 空 `to` 时回打**服务端实际解析出的目标 session**.
2. `post` 应答带投递态: `queued_local` / `forwarded_ok` / `staged_pending` / `unknown_recipient`; CLI 按态打印, 不再一律"已投递".
3. 未知收件人默认**拒绝** (要转发须显式开关, 如 `--allow-forward`).
4. CLI 超时 (客户端) 与服务端实际结果解耦: 转发异步化, 或 CLI 超时后提示"信可能已发出, 结果未知", 并给查询路径.

### P1 — 让邻居可持续 (我 #8#9#11, yoga #6, 容器 #3#4)
5. admin 邻居口补 `GET` / `DELETE` / `PATCH`; 邻居以**稳定 peer 标识** (如 shared_key 指纹或显式 name) 为 upsert 键, 换地址即覆盖.
6. 邻居健康状态: 最近成功/失败时间、连续失败退避、失效条目自动暂停 (不再每封都去撞一次).
7. `pending_forwards` 可查可控: admin 列出 (id / to / 目标邻居 / 最后错误 / 重试次数), 提供 retry / drop; 加**上限 + TTL 自动丢弃**.
8. 文档写明 mesh 前置 "至少一个方向可达", 给反向隧道的标准做法 (含端口选择、保活、对端通知); 隧道启用时在远端留可识别标记 (yoga #8).

### P2 — 启动与取信的显式化 (yoga #1#2, 我 #1#3#4)
9. 任一组件读到 `state.json` 先做一次 `__identity__` 验活, 失活明报"信箱不可达", 不静默 (yoga #1).
10. 取信在连接失败时**立即**报一句 "信箱服务未启动/不可达" (可先探测端口区间), 再进入退避 (yoga #2).
11. 提供可选保活形态: systemd **user** unit 模板 (或 `serve --daemon` + pidfile), 并在 state.json 记 pid 供存活判定.
12. 取信补机器友好参数: `--timeout` / `--count` / `--watch`, 取信前提示待取数量, 或提供新信事件/通知.

### P3 — 权限与自省 (容器 #5#6, 我 #16#18#19)
13. 加只读 `sessions list` 子命令 (走 admin 口), 供容器/设备查 session 存在性, 免猜 id.
14. 跨实例投信给**受控凭证** (per-device key, 而非 host 的 `shared_key`); 密钥分发走受控通道, 不走信件明文.
15. birth 把非秘密的宿主端口 (ssh/web/vnc) 写进容器 env 或只读文件, 免去每轮人工询问 (容器 #6).

### P4 — 拉窗配方加固 (容器 #7#8, yoga #9)
16. 设备侧命令模板强制带 `--user-data-dir` (chromium 单例坑, yoga 两次实测); `-R` 音频 socket 标为可选并给退化写法 (容器无 `/run/user`).
17. 记录已验证的 waypipe 版本组合 (容器 0.8.4 / host minimal / yoga 0.11.0 三者混用实测出窗).
18. 提供 host 侧网络诊断口或容器内放行诊断工具, 便于自测外部可达性 (yoga #9, 待证伪).

### 需人工 (用户) 执行的清单
- office sshd 加 `ClientAliveInterval 30` + `ClientAliveCountMax 3` 后 `reload` (消除僵尸 `-R` 端口, yoga #5 / 我 #12).
- 清理 office 邻居表: 编辑 `~/.agents/sandbox-worktree/neighbors.json` 去掉 `192.168.131.194` 行; 删 DB 废行 (`DELETE FROM neighbors WHERE address IN ('192.168.131.194','127.0.0.1:39418')`); 重启 serve (yoga #6 / 我 #8).
- 如需根治, kill 残留的 root `sshd-session` (39418 僵尸监听的持有者).

### 两方建议中未并入上表的要点 (原文见 3.4 / 3.5)

- **指令集绑定语义 bug** (容器 A12, 事实): `swt.pull-window` 的动态绑定键是 **poster session id**, 而人类语义写的是容器名; 容器按容器名投递时被判 "指令集外" 走 request 降级 (结果符合预期但机制未命中). 需放宽为二者皆可, 或文档写明必须填 session id, 并统一限频键.
- **拉窗成功判定与幂等** (容器 D3/D5/D6, yoga #8): 目前靠 `pgrep waypipe` + 对端自报 done; 建议容器内以 pid/标记文件做幂等键, 会话建立后校验 chromium + 目标 URL 并把结论回告投信方; 重投前查已有活跃会话, 避免弹多窗.
- **拉窗信应携带 url** (容器 D4): 两次都由设备侧自己补 `127.0.0.1:8800`, 建议 exec 指令集加 url 参数.
- **代投标注与回话寻址** (yoga H1/H3, 事实): 本次容器与 office 互相代投, 回话目标容易混; 建议信里带 caused-by / reply-to, 或显式 "由 X 代 Y 投".
- **大信无上限** (容器 A10, 事实): 无 max-body 校验, 整封进内存且取信会整段喂给 LLM; 建议加上限 (如 1MB) + 文档写明"信箱只传控制消息".
- **forward 端点不验 from** (容器 A8, 事实): 只验邻居密钥即可伪造发件人; 建议 from 限本实例已注册 session 或加签名链.
- **邻居表存储语义混乱** (yoga B5, 事实): admin 加的进 `server.db`, 文件加的只在内存, 导致"重启能否清"的直觉错误 (本次双方都判断错过).
- **白名单与邻居地址联动** (容器 E3, 事实): 跨机换址要同时改白名单放行 IP 与邻居地址, 只改一半就不通; 建议文档给联动清单.
- **容器内 `status` 无用** (容器 B1, 事实): 它读配置文件而容器只有 env, 输出全是 "(未设置)"; 建议支持 env 凭证输出真实状态.
- **结构化日志/时间时区** (yoga G1/G2/G4, 容器 B4, 事实): 本次跨机时间对不上直接导致一次误判 (39417 溯源); 建议 JSON 日志 + UTC/带时区时间戳 + 请求级记录.
- **一键配对与隧道管理** (yoga D1-D3, E1, 推测/建议): 生成本机凭证 + 可粘贴邻居模板, `add-peer` TOFU 互换密钥, `tunnel start` 自动选口/建反向隧道/通知对端改邻居/断线重连.
- **死信队列与 TTL** (yoga A5/A6/A8, 事实/建议): 重试超限入 dead-letter 并被 admin 可见, 退避改指数, 信件 TTL 到期丢弃并通知.

---

## 6. 未验证 / 存疑项 (如实标注)

- yoga #9: 容器内测外部可达性失败, 怀疑容器 egress 白名单拦截, **未证伪**.
- 我 #12 / yoga #8 的隧道溯源: office 给出的源 IP (192.168.131.194) 与时间 (14:02) 与 yoga 侧视角对不上 (yoga 说"估计看串了会话"); 双方均未进一步核对, 结论"是 yoga 自身残留"由 yoga 侧 `ps` 确认.
- 拉窗窗口在本机桌面是否真正可见, 由软件渲染参数保障, 本次未做视觉确认 (协议本身说明 token 只证明会话建立, 不证明可见).
- office 侧 `waypipe minimal` 为自编译版本, `--version` 只回 `waypipe minimal`, 无版本号 — 与容器/yoga 的版本对照不完整.
- 容器建议清单 (3.5) 中标注 **[推测]** 的条目 (A9 seen_ids 内存窗口, A13 送达确认, B2/B3 CLI 结构化输出与自动化开关, C3/C4 容器拓扑快照与 CLI 封装, E3 白名单联动) 均为设计层推断, 未经本次复现; 标注 **[事实]** 的条目均有实录支撑.
- yoga 建议清单 (3.4) 属"建议"性质, 未在报告中逐条复现验证; 与其上封 9 条坑的对应关系由编号引用 (A1-A3 对应坑 3 等).
