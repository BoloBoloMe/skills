# M03 AFK 自主决定记录

## UD-01 llm-proxy 原码不可达 → 中转面按规格重写
- 问题: D001 说 "llm-proxy 代码可参考/直接搬用", 但 F001 记录的 `~/Workspace/llm-proxy/` 是宿主机路径, 容器内不存在.
- 决策: 按 F001 规格 (~250 行 FastAPI+SQLite 形态, relay/admin 双端口, sk- key, 模型白名单/quota/过期/吊销) 在 swt-base-server.py 内重写中转面.
- 理由: 规格描述完整; 原型已证明 stdlib 足以承载信箱面.
- 影响: ISSUE-03 工作量为重写而非搬用.
- 风险: 行为细节可能与原 llm-proxy 有出入; 由 ISSUE-07 e2e 门禁兜底, 真机验证归 M09.

## UD-02 服务端零新增依赖, 用 Python 标准库
- 问题: 中转面参考对象 llm-proxy 用 FastAPI, 是否引入 FastAPI/uvicorn?
- 决策: 不引入, 用 stdlib http.server (原型 server.py 同款).
- 理由: 仓库脚本一贯零依赖 (`uv run python` 直跑); llm-proxy 的 FastAPI 能力 (OpenAI 兼容转发) stdlib 可实现; host 常驻服务少依赖少故障面.
- 影响: swt-base-server.py 单文件自包含.
- 风险: 手写 HTTP 层代码量略增; 上游流式响应 (SSE) 若需要需手写转发.

## UD-03 指令集只落注册表与校验机制, 首个成员待 M08
- 问题: D005 说首个成员是 waypipe 拉起命令, 但 waypipe 命令形态依赖 M06 盘问, 现在写死会返工.
- 决策: 落地指令集注册表 (服务端持久, 规范形比对) 与命中/降级校验; 不预填 waypipe 成员, e2e 用测试专用成员验证机制.
- 理由: 机制是 M03 范围, 具体成员是 M08 范围; ADR 0011 要求成员变动过 e2e 门禁.
- 影响: SKILL.md 记录指令集为空集起步, M08 填充.
- 风险: 低; M08 开工时须记起此约定.

## UD-04 D009 网络面零改动, birth 只验证 + 注入
- 问题: D009 要求 birth 时 `--allow` 宿主网关.
- 决策: 不改 net-firewall/apply_network — 它已在 whitelist 模式自动放行 `gateway/32` (swt.py:1397-1406). birth 集成只做: 探测服务/申领容器 key/注入 env/登记.
- 理由: 现状代码已满足 D009 的放行语义, 重复加 --allow 是冗余.
- 影响: ISSUE-06 范围缩小; e2e/单元测试验证 auto-allow 在场即可.
- 风险: 若未来 net-firewall 改默认行为, 容器会断基础服务通路; 测试断言兜底.

## UD-05 缺省路由也须过目标作用域 (评审裁决 D006 vs 原型冲突)
- 问题: Spec 评审发现 3 — 原型与现实现中, to 缺省的信路由到最近活跃设备时不查投信 key 的目标作用域, 限 dev-a 的 key 所投缺省信可被 dev-b 收走, 违 D006 "缺省拒绝".
- 决策: StoredMessage 落库时记录投信 key 的 allow_targets 快照; try_deliver 对 to 缺省的消息要求当前取信设备在快照内 (或快照含 "*"). 显式 to 的校验维持 post 时进行.
- 理由: D006 是约束性决策, 原型该行为是简化非有意; D006 优先于原型.
- 影响: Mailbox 消息表加一列; 固化旧行为的测试 `test_to缺省不受目标作用域限制` 须改写为新语义.
- 风险: 快照语义 = 投递时 key 作用域后被 admin 改不影响在途消息, 属可接受取舍.

## UD-06 post 方向响应签名用投信容器 key (评审裁决)
- 问题: ISSUE-02 实现的 post 响应 (含错误响应) 用 response_key 签名, 但 response_key 只随设备凭证分发, 容器拿不到, 签名对接收方不可验, 只满足 M02 硬约束的字面.
- 决策: post 响应 (成功与已知 key 的错误) 改用投信容器自己的 key 签名, party = 容器名, 容器侧持同 key 可验; 未知容器 key 的认证失败响应无法用该 key 签, 用 response_key 留形式, 协议注明此种响应容器不可验 (等同无签名, 仅证明服务在运行).
- 理由: 容器 key 是容器与服务间的共享密钥, 用它签名才真正防住 D007 的局域网中间人伪造响应; response_key 给容器等于授予伪造设备侧响应的能力, 不能分发.
- 影响: post 响应签名式改为 sign(container_key, container_name, nonce, canonical(payload)); ISSUE-05 容器侧投信代码与 ISSUE-07 e2e 按此验签.
- 风险: 无新增; 共享密钥模型与请求签名同源.

## UD-07 admin HTTP 面统一归 ISSUE-04; /v1/models 回白名单模型
- 问题: EXECUTION.md 把 relay key 的 admin 管理写进 ISSUE-03 范围, 但 ISSUE-04 才是 admin 管理面 (独立 127.0.0.1 端口), 两面分离会产生两个 admin 面; 另 /v1/models 返回 key 白名单模型而非上游全量列表, 执行者未申报.
- 决策: (1) relay key 的发 key/吊销/查用量 admin HTTP 端点移入 ISSUE-04, ISSUE-03 只留 RelayStore 内部接缝; (2) /v1/models 回白名单模型列表的行为确认采纳 (D006 同一心智: key 持有者只见自己被授权的模型).
- 理由: admin 单端口单管理面符合 D002(4); 白名单裁剪与缺省拒绝一致.
- 影响: EXECUTION.md ISSUE-04 范围扩为 "relay key 管理 + 信箱凭证管理"; ISSUE-03 实际交付不变.
- 风险: 无.

## UD-08 响应签名密钥每设备一份; 吊销设备拒投
- 问题: ISSUE-04 实现把 response_key 做成全局唯一, 每台设备分发同一份 — 任一持钥设备可伪造发往其他设备的取信响应, 背离 D006 "每台设备登记一对 (设备名, 签名密钥)" 的语义. 另: 显式 to 已吊销设备的投信仍入队 (永不投递), 语义含糊.
- 决策: (1) response_key 改为每设备一份, 落 devices 表, 发设备凭证时返回三元组 (设备名/签名密钥/该设备专属响应签名密钥); poll 方向签名验签均用该设备自己的 response_key. (2) post 时显式 to 指名已吊销设备 → 403 拒绝入队.
- 理由: (1) 每设备一份后, 泄露一台设备的密钥不波及其他设备, 且与 D006 成对语义对齐; 原型全局 response_key 是简化. (2) 显式目标已吊销时 fail-fast 比攒死信清晰.
- 影响: devices 表加 response_key 列; Mailbox.sign_response 签名密钥按设备取; ISSUE-05 取信脚本配置 = 每设备三元组; ISSUE-07 e2e 按每设备验签.
- 风险: 无; 服务未真部署, 无旧凭证迁移问题.

## UD-09 设备处理回报: POST /mailbox/ack 端点
- 问题: D004 存续语义 queued→delivered→processed + 已处理 7 天清理, 原型 processed 由 in-process TUI 直接标记; 正式版设备与服务分离, 无回报通道则消息永卡 delivered, 清理永不生效.
- 决策: 服务端加 `POST /mailbox/ack`: 设备签名 (同 poll 验签式), 体 `{device, ts, sig, id, outcome}`, 把 delivered 消息转 processed 记 outcome; 已 processed 幂等 200; 未验签/未知设备 403; 对 queued/未知 id 409 不转. 设备侧 ack 时机: 取信扩展在来信触发的 LLM 轮 agent_settled 后发 ack.
- 理由: 补全 D004 生命周期闭环的最小面; 签名与 poll 同式, 无新凭证.
- 影响: 服务端 +1 端点; ISSUE-05 扩展在 settle 后回 ack; e2e 覆盖.
- 风险: processed 语义实为 "已交 LLM 且该轮收尾", 不等于 "用户已读"; 可接受 (清理只依赖 processed, 语义文档注明).

## UD-10 取信脚本用 Node .mjs 而非 Python
- 问题: D008 定的是 "阻塞取信脚本由扩展拉起", 原型 fetch_loop.py 是 Python; 设备侧 (host/远程 Linux) 不保证有 python/uv, 但必然有 Node (pi 本体就跑在 Node 上).
- 决策: 正式版取信脚本写 Node .mjs (`pi/extensions/swt-mailbox-fetch.mjs`), 扩展 spawn `node` 拉起; 协议字段与签名式与服务端对齐 (UD-06/UD-08).
- 理由: 运行时是设备侧唯一硬保证; 消除 python 依赖问题.
- 影响: fetch_loop.py 仅作协议对照参考; SKILL.md 记录脚本形态.
- 风险: 无; 协议已在原型验证.

## UD-11 取信配置路径/格式 + 触发文件事件分类 (ISSUE-05)
- 问题: 设备三元组与服务地址的落盘位置 D006 只说 "手工复制到设备配置", 未定路径与格式; 原型验签失败也写 message 事件 (verify:"FAIL"), 与 M02 "扩展只对 message 事件 triggerTurn" 相碰.
- 决策: (1) 配置 `~/.config/swt/mailbox.json` (env `SWT_MAILBOX_CONFIG` 覆盖, 脚本 argv 优先), 字段 `{server, device, signing_key, response_key, trigger_file?}`, trigger_file 缺省 `~/.local/state/swt/mailbox-trigger.jsonl`, 日志 = 触发文件去扩展名 + `.log`; 配置缺失/缺字段退出码 2 并报缺哪个字段. (2) 触发文件 JSONL 事件分类: `identity` (D002 探测) / `verify_fail` (验签失败或 nonce 重放, 原型 verify:"FAIL" 改为此, message 事件因此恒为已验签) / `message` (带 id/from/type/body/ts/downgraded/note/latency_ms/nonce 全字段). (3) 扩展 ack 的 outcome 固定 "handled"; 扩展防滥用 = 按消息 id 去重 + 两次 triggerTurn 最小间隔 1s 退避 + agent_settled 且 isIdle 才补发/回报.
- 理由: 配置路径沿用 XDG 惯例, 与服务端状态文件 (`~/.local/state/swt-base-server/`) 同族; verify_fail 单列事件让 "只对 message triggerTurn" 的判定无歧义; 验签失败的信不注入会话是安全默认 (D007).
- 影响: ISSUE-08 文档按此配置样例写; 扩展与脚本共用同一配置文件.
- 风险: pyJsonDumps (python json.dumps sort_keys 等价) 对整数值浮点丢 ".0" 是已知边角 — 投信方 ts 用 time.time() 带小数即不触发.

## UD-11 补记 (评审后)
- deliverAs: "followUp" (当前轮干完再投递) 为扩展 triggerTurn 的投递模式, 官方骨架同款, 评审确认良性, 补申报.
- 触发文件只增不删无轮转: 信箱量级 (条/天) 下可接受, 记录在案; drain 逻辑已加截断守卫 (见 ISSUE-05 修复).
- loadConfig 在 .mjs 脚本与 .ts 扩展双写: 跨进程运行时边界 (pi 只加载 .ts, 脚本由 node 直接跑) 无法共享 import, 两文件互加交叉引用注释防协议漂移.
