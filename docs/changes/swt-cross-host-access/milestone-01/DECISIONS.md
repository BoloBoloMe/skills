# MILESTONE-01 信箱通道设计 决策账本

盘问日期: 2026-09-13. 依据: [recon/01](../recon/01-llm-channel.md) + 用户方向修正 (web 服务单体) + 反方攻击 (子代理 opposing-viewpoint, 结论见 D005/D007).

2026-09-14 使用方补充: [M04 D012](../milestone-04/DECISIONS.md#d012-当前设备由工作会话确定-发信明确指定目标) 要求展示相关信件明确指定本次工作使用的设备. 本文 D004 的最近取信设备只适用于未指定目标的通用消息, 不代表用户当前所在设备. 队列默认语义未改; M05 实施使用方的设备选择, 不据此修改 M03 的基础协议.

## 决策

### D001 信箱形态: 合并 llm-proxy 为 host 中心化 web 服务单体
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 信箱不做"容器内文件队列 + 设备 ssh 拉取" (recon 原主候选), 而是与 llm-proxy 合并为一个 web 服务单体 `swt-base-server.py`, 放 `workflow/use-sandbox-worktree/scripts/` (不放 use-worktree, 那是纯 worktree 工具, 与容器无关 — 用户确认系笔误), host 上 Quadlet 常驻, 定位为 sandbox-worktree 基础服务. llm-proxy 代码可参考/直接搬用. 理由: (1) llm-proxy 反正要常驻, 合并零新增进程; (2) 中心化天然解决多容器并存与多设备路由 (原"设备轮询 N 容器"与"宿主汇聚"之争消解); (3) 消息存 host SQLite, 容器删除不丢信, 比文件队列的 at-most-once 更强; (4) 用户明确看重"局域网内所有机器天然可达 + all in one". 推翻的 recon 结论: "宿主汇聚打破 host agent 只管生命周期的角色边界" — 用户拍板基础服务是合法新角色.
- 预计影响: workflow/use-sandbox-worktree/scripts/ 新增 swt-base-server.py; ~/Workspace/llm-proxy/ 功能被吸收 (是否保留独立项目用户未定, 实施时问)

### D002 端口: 冷门区间 + 身份探测 + 宿主机约定
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 对外服务端口不用常见端口也不硬阻断. (1) 区间 `38417-38426`, 启动时从 38417 起绑首个空闲端口; (2) 无认证 `GET /__identity__` 端点返回服务名/版本/能力 (中转/信箱), 发送方与接收方连上端口先调它确认"是 swt 基础服务", 区间内逐个扫即可发现服务; (3) 实际绑定端口写入 host 固定路径的状态文件, 同机组件读文件免扫描; (4) admin 端口 (发 key) 永远只听 127.0.0.1, 不参与区间, 固定可配; (5) 约定写死: 容器的基础服务永远搭建在它所在的宿主机上, 容器内地址恒为 `host.containers.internal` + 上述区间. 理由: 端口写死硬阻断会让基础服务起不来; 自动漂移则容器注入的地址失效 — 区间+探测两全.
- 预计影响: swt-base-server.py 启动逻辑; SKILL.md 与 swt.py birth 注入地址处

### D003 队列纯单向: 容器投, 设备取; 无回程队列
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 消息队列只服务容器→设备方向. 设备要回话给容器, 走既有 ssh 入口 + herdr 委派配方 (查 idle → send-text → 键位提交 → wait/read), 零新组件. 信封因此删除 `reply_to` 字段 (冗余). 依据 F003 的不对称事实. 附带效果: recon 遗留疑问"容器内侧 reply 注入的进程生命周期"整个消解 — 容器侧不从队列收消息.
- 预计影响: swt-base-server.py 只有单方向队列; 设备侧取信扩展

### D004 消息协议: 纯文本, 4 类型, 不传文件
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 消息体只允许文本字符串. 类型枚举: `notify` (纯通知, 转 herdr notification 弹给用户) / `open_url` (开 URL, 直批) / `exec` (见 D005) / `request` (需回应, 设备 LLM 能答自答, 涉用户决策/改本地状态问用户, 回应走 D003 的 ssh 通道). `file` 类型删除 — 文件由接收方经 ssh 直接从容器拉取 (容器本来就能被设备访问). 信封字段: `{ id: uuid, ts, from: <容器名>, to: <设备名>, type, ttl?, body }`. 路由: `to` 缺省 = 最近活跃的设备 (服务记录各设备最近取信时间), 全单播, 不广播 (用户明确拒绝通知广播). 冷启动: 从无设备活跃时缺省信先攒着, 第一台来取信的设备成为最近活跃并收走全部缺省信. 投递语义: host SQLite 持久 (取代文件队列的 at-most-once), 已处理消息保留 7 天滚动删除.
- 预计影响: swt-base-server.py 信箱路由与存储; 设备侧扩展的消息渲染

### D005 exec 授权: 服务端最小指令集白名单, 之外降级 request
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: exec 不是任意 shell 直批. 消息内容是结构化指令 — 文本写明调用哪个工具+参数; 指令集是预定义的最小集合 (首个成员: 直通 GUI 窗口的 waypipe 拉起命令, 服务 M08). 白名单存服务端 (host 可信持久, 不住容器里), 服务校验: 命中白名单 → 设备直批执行; 不在集合 → 降级为 request, 由设备侧 LLM 走 pi 既有权限流程 (该问用户问用户). 理由: 反方攻击成立 — (1) HMAC 防外人伪造防不了持钥者, 容器被提示注入操纵时任意命令直批 = 设备代码执行无人过目, 而"容器不可信"恰是沙箱立身前提; (2) 取信会话全手动首启 (D008), 消息到达时人就在场, 直批只省一次确认键; (3) llm-proxy 对同批容器限模型/限额/限时可吊销, 信箱却放行任意命令是自相矛盾. 用户裁决: 选折中 C 方案并加严 — 严格控制内容格式, 指令集保持最小. 设备侧 pi 门禁 hooks 是 request 路径的补充防线, 不是主防线 (F005).
- 预计影响: swt-base-server.py 指令集注册表+校验; 设备侧扩展的指令分发器; SKILL.md 记录指令集成员

### D006 认证: 设备 HMAC 签名密钥, 容器 key 带作用域
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不引入额外身份概念. 设备身份 = 设备名: 每台设备登记一对 (设备名, 签名密钥), 取信时报设备名并附 HMAC 请求签名 (key 不上线), 服务验签认出设备, 只发给它自己的信, 不能冒充/取错. 容器 key (沿用 llm-proxy sk-key 体系) 只能投信不能取信; 发容器 key 时声明可投的消息类型与目标设备, 缺省拒绝 (与 llm-proxy 模型白名单同一心智). 签名密钥分发: 发 key 时用户手工复制到设备配置, 一次性操作.
- 预计影响: swt-base-server.py keys 表加角色/作用域字段; admin 发 key 接口扩展

### D007 传输加固: 双向签名 + 防重放; 跨机走 ssh -L
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 请求和响应都签名 (响应方向携带消息正文, 不签则局域网中间人可伪造长轮询响应直接向设备投信 — 反方攻击确认的漏洞); 请求带时间戳, 服务端校验时间窗并缓存已见消息 id 拒绝重放. 跨机取信推荐路径: 设备经 ssh 本地转发 (`ssh -L`) 访问 host 服务, 全程加密, 复用设备既有 ssh 凭证 — 明文嗅探问题消解 (注意: 被排除的是 ssh -R 反向隧道, -L 从未被排除); 裸连局域网+签名保留为降级路径. HTTP 明文本身接受 — 签名管真实性与完整性, ssh -L 管机密性.
- 依赖事实: F004
- 预计影响: swt-base-server.py 验签/签名中间件, 已见 id 缓存; 设备侧扩展的 ssh -L 通道管理

### D008 取信: 长轮询阻塞脚本 + pi 扩展后台驱动; 会话形态分本机/远程
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: (1) 设备取信用长轮询 (请求 hold 住, 有信立刻返回), 超时重发的循环封装在脚本里 — 只要没消息脚本就一直阻塞, 不由 LLM 重新发起, 空转零 token; (2) 脚本由取信会话的 pi 扩展在后台拉起, 来信经 sendMessage(triggerTurn) 唤醒 LLM (file-trigger.ts 骨架形态), 不作为 LLM 的阻塞工具调用 (挂几小时有超时被杀风险); (3) 取信会话形态: 在 host 上 = 用户当前会话所在 tab 的一个窗格 (pane); 在其他设备上 = 固定命名 tab (`S-swt-relay-1`, 名字即 herdr 发现机制); 全部手动首启, 不开机自启 (人不在场时开着也没人看). 附带效果: Roadmap 迷雾"信箱实时性"关闭 — 长轮询天然秒级, 无需 inotifywait/ssh -R 升级.
- 预计影响: 设备侧 pi 扩展 (新写); 阻塞取信脚本

### D009 容器网络放行: birth --allow 宿主网关, 接受 IP 级粒度
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: swt birth 时自动 `--allow` 宿主网关 IP (host.containers.internal 映射地址) 并注入容器 key 与服务地址. 明示接受的取舍: nft 白名单是 IP 级粒度, 放行后容器可达宿主机所有 0.0.0.0 端口 (cockpit 9090 等), 各服务自有认证兜底; 端口级放行需改 net-firewall.py, 不做 (若要收紧单独立项).
- 依赖事实: F002
- 预计影响: swt.py birth 流程

### D010 测试: 沿用 llm-proxy e2e 风格
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 沿用 llm-proxy test_e2e.py 形态 (假上游/假客户端 + 全流程断言), 信箱覆盖: 投信/阻塞取信/双向签名验签/防重放/按设备路由/白名单降级/7 天清理/端口区间绑定与身份探测. 附带纪律: 服务代码在 workflow 仓库, 切换分支会无声改变运行中的安全策略 — e2e 测试是必过门禁.
- 预计影响: swt-base-server 的 test_e2e.py

## 事实

### F001 llm-proxy 现状
- 状态: 当前有效
- 来源: ~/Workspace/llm-proxy/ (README.md, main.py, Containerfile, config.example.yaml, 2026-09-13 读取)
- 内容: ~250 行 FastAPI+SQLite 单体. relay 端口 (默认 3000, 绑 0.0.0.0) 提供 OpenAI 兼容 /v1/chat/completions 与 /v1/models, sk-xxx key 认证; admin 端口 (默认 3001, 硬编码只听 127.0.0.1) 发 key/吊销/查用量 (X-Admin-Token). keys 表: 模型白名单/quota/用量/过期/吊销. 容器经 `http://host.containers.internal:3000/v1` 访问. 已有 Quadlet 驻留路径与 test_e2e.py (11 项断言). 未接入 swt — swt 代码无任何 llm-proxy 引用.

### F002 swt 白名单 IP 级粒度与宿主可达面
- 状态: 当前有效
- 来源: workflow/use-sandbox-worktree/scripts/net-firewall.py, swt.py (2026-09-13 读取)
- 内容: whitelist 模式默认断容器全部出向, 只放行网关 DNS + `--allow` 条目 (只收 IP/CIDR, 无端口粒度) + 已建连接回程. 容器内 `host.containers.internal` 解析到 pasta 映射的宿主网关 (缺省 169.254.1.2). 放行该 IP 后容器可达宿主机全部 0.0.0.0 监听端口; 绑 127.0.0.1 的服务容器够不着.

### F003 设备→容器通信现成, 容器→设备缺失
- 状态: 当前有效
- 来源: ROADMAP.md 笔记 + recon/01
- 内容: 设备侧→容器侧有 ssh 入口 + herdr 委派配方 (get idle → send-text → alt+\ 提交 → wait/read; pi 专属键位坑见 herdr-pi.md); 容器侧→设备侧原本三无: 白名单挡出向/无凭证/设备无常驻接收端. D001 之后: 容器→host 基础服务方向由 --allow 打开 (F002), 三无全部消解.

### F004 反方攻击结论 (子代理, 2026-09-13)
- 状态: 当前有效
- 来源: opposing-viewpoint 子代理分析 (M01 盘问会话)
- 内容: 成立并已吸收 — (1) exec 直批信任倒置 (签名不约束持钥者, 容器注入=设备 RCE; llm-proxy 对同批容器限额与信箱直批自相矛盾; 手动首启下人本来在场, 直批收益≈一次按键) → D005; (2) 响应未签名+无防重放 → D007; (3) 容器 key 无作用域 → D006; (4) ssh -L 加密路径未被排除过 → D007. 已舍弃 — 静态端口优于区间 (低置信, 用户已拍区间); "零新增进程不成立但结论仍对"; 代码在 workflow 仓库的安全策略漂移风险 (靠 e2e 门禁+仓库纪律, 记入 D010).

### F005 设备侧门禁 hooks 对 bash 任意命令的覆盖范围未验证
- 状态: 当前有效
- 来源: 盘问自扫 (M01 会话)
- 内容: filesystem-operation-gate/git-operation-gate/python-operation-hook 拦对应工具的越权操作, 对 bash 工具里任意危险命令 (如 rm -rf ~) 的拦截能力未实测. D005 下 hooks 只是 request 路径补充防线; 若未来要扩大指令集, 先实测 hooks 覆盖再扩.

### F006 pi 扩展能力面 (信箱可用)
- 状态: 当前有效
- 来源: recon/01 考察点 1 (pi 官方 extensions.md/sdk.md)
- 内容: 扩展可在 session_start 起 setInterval/子进程等后台资源 (session_shutdown 清理); `sendMessage(msg, {triggerTurn:true})` 空闲即触发 LLM 轮, `agent_settled`+`ctx.isIdle()` 防重入; `pi.exec` 跑本地命令; 官方 file-trigger.ts 为"外部系统递消息"现成骨架. 轮询放 Node 层则空转零 token.
