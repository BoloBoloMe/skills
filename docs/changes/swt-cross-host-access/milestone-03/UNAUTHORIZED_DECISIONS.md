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
