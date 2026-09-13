# 方向侦查: 容器侧 → 设备侧 LLM 传话通道

日期: 2026-09-13
性质: 调研分析, 不含实现. 事实底座: 跨机 GUI 调研报告 (waypipe 实测) + swt SKILL.md + pi 官方文档 (extensions.md / sdk.md, 含示例源码) + 本机 herdr 实测 (v0.7.5, protocol 17).

## 结论先行

**主候选可行**: pi 扩展具备全部必要能力 — 后台定时器/文件监听可起 (Node 层, 零 token), 队列有消息时能自动发起一轮 LLM 处理 (triggerTurn), 能跑本地命令 (pi.exec), 而 ssh 拉取不新增任何网络面, 不新增凭证, 白名单一字不动.

## 考察点 1: pi 扩展能力面

### 1a. 后台定时器/轮询钩子

**判定: 需变通 (方案已明).** pi 没有内置的 "注册定时器" API, 但扩展就是 TypeScript 模块, 可用 Node 的 `setInterval`/`fs.watch`. 文档明文认可此形态: "Long-lived resources and shutdown" 节列出 "processes, sockets, file watchers, or timers" 是可在 `session_start` 里启动的后台资源, 要求配 `session_shutdown` 清理 (extensions.md). 先例: 官方示例 `mac-system-theme.ts` 就是扩展里 setInterval 周期检测系统主题; `file-trigger.ts` 就是扩展里 fs.watch 监听触发文件, 变化即注入会话.

### 1b. 无用户输入时自动发起一轮 LLM 处理 (自循环)

**判定: 支持.** 两条注入通道都有文档明文:

- `pi.sendUserMessage(content)` — "Always triggers a turn" (extensions.md ExtensionAPI Methods 节).
- `pi.sendMessage(msg, { triggerTurn: true })` — agent 空闲时立即触发 LLM 响应; 忙时按 `deliverAs` 排队 (steer = 当前轮工具跑完就插队, followUp = 干完再说).

自循环闭环: `session_start` 起 watcher/timer → 队列有消息 → sendMessage(triggerTurn) → LLM 处理 → `agent_settled` 事件里再查队列 → 有则再注入. `agent_settled` 语义明确: "no retry/compaction/follow-up left", 配 `ctx.isIdle()` 防重入. 官方 `file-trigger.ts` 是现成骨架, 它就是 "外部系统给 agent 递消息" 的参考实现. 需要的变通只有一条: 循环要自带退避/去重, 防队列异常时无限自触发.

### 1c. 扩展/工具执行本地 shell 命令

**判定: 支持.** `pi.exec(command, args, { signal, timeout })` 是 ExtensionAPI 一等方法 (extensions.md), 返回 stdout/stderr/code. 官方示例大量使用 (git-checkpoint, auto-commit-on-exit, dirty-repo-guard 等). 自定义工具的 execute 里同样可调. 跑 ssh 拉队列没有任何障碍.

### 1d. 常驻会话挂 herdr 空转的成本

**判定: 可行, 前提是轮询放扩展层, 不放 LLM 层.**

- 空 转 = pi TUI 开着但 LLM 无请求: 零 token. herdr 的 agent 状态检测 (idle/working/blocked) 是解析终端输出, 不经过 LLM, 零 token.
- 轮询逻辑 (定时 ssh 取队列) 在扩展的 Node 事件循环里跑, 每次 ssh 是普通进程, 零 token.
- 只有真实消息到达触发的 LLM 轮烧 token — 这是必要成本, 不是空转成本.
- 反面教材: 若把 "检查一下队列" 当提示词周期发给 LLM, 每次检查 = 一次完整 LLM 请求, 队列空也烧钱, 还污染会话上下文. 必须避免.
- 长会话自身上下文增长会触发自动 compaction (烧 token), 属会话固有成本; 接收端会话建议用固定短任务的系统提示, 必要时定期 /new 重置.

## 考察点 2: 队列实现设计选项 (容器内文件队列, ssh 拉取)

**目录布局** (容器内, 放 `~/.local/state/swt-queue/<对端>/`, 不进 git 仓):

```
pending/   待取消息: <UTC时间戳>-<序号>-<uuid>.json (文件名排序即顺序)
replies/   回程: 设备侧写回给容器 LLM 的消息 (同命名)
done/      已处理归档, 按天分目录, 保留 N 天滚动清理
```

**pop 原子性**: 靠 `rename(2)` — 同一文件系统内 mv 是原子的. 单一消费者 (设备侧常驻会话独占) 时两步即可: 取走 (mv 到本地副本) + 容器内归档; 多消费者才需要先 `mv pending/x.json inflight/` 抢占, 抢失败者跳过. 消费者唯一时不必引入 inflight 层.

**消息生命周期**: 写 pending → 设备拉取 (拉取=复制+容器内 mv done, 或严格点先 mv inflight 再转 done) → 处理 → 若需回复写回 replies/ → done 滚动清理. 投递语义是 at-most-once (容器一 terminate 队列整个消失, 未取消息即丢) — 这与 swt "容器即弃" 心智一致, 但协议里必须显式标注, 请求方自己决定要不要重发.

**传输层两种做法**:
1. 定时拉: 扩展里 setInterval + `pi.exec("ssh", [..., "cat 待取文件"])`, 间隔 5-10s, ssh 走交付包密钥 BatchMode. 简单, 实时性 = 间隔.
2. 长连推: 设备侧挂一条常驻 `ssh 容器 inotifywait -m -m pending/` (或容器内简易流式脚本), 消息一落盘就推过 ssh, 扩展的本地 watcher 收到即注入. 秒级实时, 复用同一条 ssh 通道, 断线重连由扩展管理. 主候选落地可先做 1, 无缝升 2.

**多容器并存: 设备侧轮询 N 个容器 vs 宿主侧汇聚**:

| | 设备侧轮询 N 容器 | 宿主侧汇聚 |
|---|---|---|
| 新增组件 | 无 | 宿主上常驻聚合进程 (新角色) |
| 凭证/端口 | 各容器已有的, 零新增 | 同左 + 宿主聚合口 |
| 实现量 | 小 (循环 N 次 ssh) | 大 (聚合进程 + 生命周期管理) |
| 故障面 | 一容器挂不影响其他 | 聚合进程单点 |
| 角色边界 | 符合 (host agent 只管生命周期) | 打破 (宿主多了常驻业务组件) |

N 实际 ≤ 3, **建议先设备侧直连轮询**, 容器规模大了再议汇聚. 注意 SKILL.md 角色边界: "你 (host 侧 agent) 只管理生命周期, 不进容器干活" — 宿主汇聚组件和这条立场有张力, 需用户拍板才做.

## 考察点 3: 三形态对比

| 维度 | a. 容器内队列 + 设备常驻会话拉 (主候选) | b. 容器直驱设备 herdr (容器推) | c. 设备侧接收端 + ssh -R 反带 socket (容器推) |
|---|---|---|---|
| 安全面 | 零新增. 复用 ssh 入向通道, 白名单不动 | **负面**: 白名单须放行容器→B:22 (IP 级, B 换 IP 即失效); 容器被攻破可横向到 B, 违背 sandbox 初意 | 零新增. ssh -R 走既有入向 ssh, 容器侧只见本地 unix socket |
| 凭证 | 零新增. B 已持容器密钥 (herdr remote 在用) | **负面**: B 的 ssh 私钥要塞进容器, "真远端对容器不暴露" 立场被破 | 零新增 |
| 网络改动 | 无 | nft 白名单加条目 + B 端 sshd 暴露 | 无 (前提: 容器内 sshd 允许 StreamLocalForwarding, pasta 下未实测) |
| 实现量 | 中: 双端各一个 pi 扩展 + 队列目录约定 | 小 (脚本直调), 但见可靠性列 | 中: B 端常驻接收端 (生命周期管理) + 容器侧 socket 客户端 (socat 已在 base 层, P0-1) |
| 可靠性 | 拉模式抗断线 (失败重试即可); 实时性 = 轮询间隔, 可升长连推; at-most-once | 推模式要自处 B 不可达重试; IP 漂移是长期故障源; herdr agent prompt 对 pi 有键位坑 (见考察点 5), 远程裸用更脆 | 实时性最好; 通道绑一条 ssh 会话, 断线写 socket 即失败 (ECONNREFUSED), 协议须定义回落到文件队列 |

## 考察点 4: 消息协议草案

**信封**: `{ id: uuid, ts, from: <容器名>, type, reply_to?, ttl?, body }`, 单文件单消息.

**类型枚举与审批边界** (固定偏好 "容器之外用户说了算" 的落地):

| type | 含义 | 设备侧 LLM 可直接执行? |
|---|---|---|
| notify | 纯通知 (完成/失败/进度) | 是 — 转 herdr notification show 弹给用户, 不打扰 |
| open_url | 开 URL (展示/present URL, noVNC, 容器 web 服务) | 是 — 低风险读操作; 若指向容器服务, 先确认隧道/端口在场再开 |
| file | 传文件 (容器→设备交付产物; 设备→容器塞材料) | 入方向小文件: 是, 落指定目录+通知; 出方向 (用户数据离开设备) 和覆盖冲突: 问用户 |
| exec | 在设备上跑 shell 命令 | **默认必问用户**; 仅显式白名单的只读诊断命令 (查端口/查进程类) 可配置直批 |
| request | 需回复的请求 | 设备侧 LLM 能自答 (答容器问题, 报状态) 则自答; 涉及用户决策/花钱/改本地状态: 问用户 |

**请求-回复关联**: request 必带 `expect: reply`; 回复以新消息 `type=reply, reply_to=<原id>` 走对向队列. 容器侧非阻塞: 写完 request 继续干活, reply 到达后由容器内侧对称部署的 watcher 扩展 sendMessage 注入容器内会话 (同一份扩展代码两端用, D043 扩展全量复制机制天然支持). 死信: ttl 过期未回复, 容器侧 LLM 自行决定重发或放弃.

**原则句**: 设备侧 LLM 是门卫不是全权代理 — 拿不准即问用户.

## 考察点 5: herdr 咬合 (本机实测 v0.7.5)

- `herdr notification show <TITLE> [--body --position --sound none|done|request]` — 设备侧把容器消息转成用户可见通知的最短路径, 底层走 socket API 的 `notification.show`.
- `herdr agent` 子命令: list / get / read / send-keys / prompt / rename / focus / wait / attach / start / explain. 委派配方 (SKILL.md: get 确认 idle → send-text → 键位提交 → wait/read) 原样适用.
- **发现与复用常驻会话**: `herdr agent list` 自动发现所有 pi 会话, 字段含 agent kind, agent_status (idle/working/blocked/done), cwd, name (命名会话), pane/tab 归属. 约定设备侧常驻接收会话用固定名字 (用户默认格式 `S-<名>-<序号>`), 接收端按 `agent list` 过滤 name 定位, `agent get` 验 idle 再发 — 名字就是发现机制.
- **pi 专属坑 (herdr-pi.md, 实测沉淀)**: pi 提交键是 alt+\, `agent prompt` 默认发的 enter 只把文本留在输入框 — 必须两步: send-text + send-keys "alt+\\". 且 `--wait` 会误报 `agent_prompt_stalled` (pi 干完回 idle 太快或快照滞后), 重发前先 `agent read` 看屏幕. 设备侧自动化必须内置此配方, 裸用 agent prompt 会打出两遍任务.
- `herdr api` (unix socket `~/.config/herdr/herdr.sock`, protocol 17): 方法面含 `notification.show, agent.*, pane.send_text, events.subscribe, events.wait, pane.wait_for_output` — 需要事件订阅或更低延时时可直连 socket, CLI 够用则不必. **socket 只听本机, 三形态里只有 a/c 的设备侧组件与它同机, b 形态够不着 (这正是 b 需要容器 ssh 到 B 再本地执行 herdr 的原因).**
- 形态 c 的接收端与 herdr 的咬合点: 接收端就在设备本机, 收到容器消息后可直接 `herdr agent prompt` 投给常驻会话, 或 `notification show` 直弹用户.

## 推荐排序与理由

1. **a (主候选) 先行** — 唯一零安全增量的形态: 不碰白名单, 不动凭证, 不加常驻组件; pi 扩展能力面四项全过 (1a/1b/1c 支持, 1d 可行); 先定时拉后长连推, 分两步走.
2. **c 作为实时性升级项叠加** — 传输层从轮询换 ssh -R 反带 socket (容器内 socat 已在 base 层), 协议与扩展不变, 设备侧加一个常驻接收端. 前置验证: pasta 下 ssh -R 绑 unix socket 可用性, B 端接收端的开机自启.
3. **b 淘汰** — 白名单与凭证双违背 swt 安全立场, IP 漂移是长期故障源, 且 herdr API socket 不听网络, 远程驱动绕一圈回到 ssh, 没有别人给不了的好处.

## 遗留疑问

1. **容器内侧 reply 注入的进程生命周期**: herdr remote "容器无需预启 server, remote attach 按需拉起" — 设备 detach 后容器内 herdr server 与 pi 会话是否常驻 (决定容器内侧 watcher 扩展能否常驻收 reply). 实施前必须实测; 若不常驻, 容器侧 LLM 只能下轮自取 replies/ (协议已兼容此退化).
2. B 端常驻会话/接收端的开机自启与注销存活 (systemd user unit vs herdr 自启 vs 人工).
3. file 类大文件走信封 base64 还是路径引用+scp 直传 (通道效率).
4. 容器内多 pi 会话共用一个队列还是按会话分队列 (from 字段够不够区分).
5. 形态 c 的 sshd StreamLocalForwarding 在 base 层 sshd_config 的放行与 pasta 下的实测.
