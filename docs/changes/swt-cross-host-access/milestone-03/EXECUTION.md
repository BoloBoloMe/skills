# MILESTONE-03 信箱实施 EXECUTION

任务书: [MILESTONE-03.md](../roadmap/MILESTONE-03.md). 权威输入: [M01 决策账本](../milestone-01/DECISIONS.md) (D001-D010/F001-F006), [M02 结论节](../roadmap/MILESTONE-02.md) (四条移交硬约束), ADR [0010](../../../adr/0010-mailbox-centralized-web-monolith.md)/[0011](../../../adr/0011-mailbox-exec-instruction-allowlist.md), 原型 [mailbox_logic.py](../prototypes/mailbox-loop/mailbox_logic.py) (参考答案, 非直接复用) / [server.py](../prototypes/mailbox-loop/server.py) / [fetch_loop.py](../prototypes/mailbox-loop/fetch_loop.py), [recon/01](../recon/01-llm-channel.md) (pi 扩展能力面), [词汇表](../../../language/UBIQUITOUS_LANGUAGE.md).

工作模式: AFK 自主推进 (用户已授权), 自主决定逐条落 [UNAUTHORIZED_DECISIONS.md](UNAUTHORIZED_DECISIONS.md).

## 全局约束

- 服务端零新增第三方依赖, 只用 Python 标准库 (原型同款, 仓库脚本一贯零依赖).
- 服务端单文件 `workflow/use-sandbox-worktree/scripts/swt-base-server.py` (D001 单体), llm-proxy 原码在容器内不可达, 按 F001 规格重写中转面.
- M02 四条移交硬约束: 投信错误响应也签名 (D007 全响应签名) / 取信扩展只对 message 事件 triggerTurn / 端口区间 38417-38426 首空闲绑定 / SQLite 持久化 + 7 天滚动清理.
- 测试设计已由决策账本回答 (D010 覆盖清单即验收清单), 不再逐条回问用户; 接缝 = 公开 HTTP 端点与 Mailbox 类公开方法, 不测内部实现.
- 交付链路: 要用户真跑的东西先 commit+push 再交付命令, 交付物带版本标记.
- 测试用 `uv run pytest`, 服务端 e2e 纯本机回环, 不依赖 podman.

## ISSUE 列表

- [x] ISSUE-01: 信箱核心状态模型 + SQLite 持久化
  - 范围: Mailbox 类 (投信判定/容器 key 作用域/时间窗/防重放/exec 指令集分类降级/缺省路由冷启动/设备验签/try_deliver/process) + SQLite 存储 (消息 queued→delivered→processed, 设备/容器 key/已见 id 持久, 重启恢复, 已处理 7 天滚动清理).
  - 依据: D003/D004/D005/D006/D007 + mailbox_logic.py. 接缝: Mailbox 公开方法.
- [x] ISSUE-02: HTTP 服务面与生命周期
  - 范围: 端口区间 38417-38426 首空闲绑定 (D002) / `GET /__identity__` / `POST /mailbox/post` (错误响应也签名) / `POST /mailbox/poll` (长轮询 hold 20s) / 全响应签名 + nonce / 实际绑定端口写 host 固定路径状态文件.
  - 依据: D002/D007/D008 + server.py 对照. 接缝: HTTP 端点.
- [ ] ISSUE-03: llm 中转面 (吸收 llm-proxy)
  - 范围: OpenAI 兼容 `POST /v1/chat/completions` + `GET /v1/models`, sk- key 认证, keys 表 (模型白名单/quota/用量/过期/吊销), 假上游测试. admin 侧发 key/吊销/查用量.
  - 依据: F001 (原码不可达, 按规格重写). 接缝: HTTP /v1 端点 + admin 端点.
- [ ] ISSUE-04: admin 管理面 (信箱凭证)
  - 范围: 独立端口硬绑 127.0.0.1 (固定可配, 不参与区间) + X-Admin-Token; 发设备凭证 (设备名 + 签名密钥 + 响应签名密钥一并分发) / 发容器 key (声明可投类型与目标设备, 缺省拒绝) / 吊销 / 查队列与统计.
  - 依据: D002(4)/D006. 接缝: admin HTTP 端点 + 拒绝非 loopback 来源.
- [ ] ISSUE-05: 设备侧取信 (阻塞脚本 + pi 扩展)
  - 范围: 正式版阻塞取信脚本 (请求签名/响应验签/nonce 去重/触发文件: message 事件 + 生命周期事件, 空转零 token, 断线重试) + pi 扩展 `pi/extensions/` 新增 (session_start 后台拉起脚本, 监听触发文件, 忽略非 message 事件, message → sendMessage(triggerTurn), agent_settled + ctx.isIdle() 防重入, 自带去重退避, session_shutdown 清理).
  - 依据: D008/F006 + fetch_loop.py + recon/01 考察点 1 + file-trigger.ts 骨架. 接缝: 脚本对假服务的端到端行为; 扩展按 tests/pi/ 既有约定测试.
- [ ] ISSUE-06: swt.py birth 集成
  - 范围: birth 探测基础服务 (读状态文件, 缺席扫区间 __identity__) → 经 admin 申领容器 key (作用域按容器名) → 注入容器 env (服务地址/key/容器名, 含 ssh 面 environment 通道) → runtime 登记. 网络面零改动: apply_network 已自动放行 gateway/32 (D009 天然满足), 只验证.
  - 依据: D002(5)/D009/F002 + swt.py create_and_start_container/apply_network. 接缝: birth 单元级 (mock podman 边界按 tests/ 既有约定).
- [ ] ISSUE-07: e2e 门禁测试
  - 范围: `tests/test_swt_base_server.py`, llm-proxy test_e2e 风格 (假上游/假客户端 + 全流程断言). 覆盖 D010 清单: 投信/阻塞取信/双向签名验签/防重放/按设备路由/白名单降级/7 天清理/端口区间绑定与身份探测.
  - 依据: D010. 必过门禁, 指令集成员变动即安全策略变动.
- [ ] ISSUE-08: 文档与驻留件
  - 范围: use-sandbox-worktree SKILL.md 增补 (基础服务/信箱/取信会话用法, 术语对齐词汇表) + Quadlet 单元文件 (host 部署件, 真机部署验证归 M09) + 指令集成员记录处 (首个 waypipe 成员待 M08 填充) + 交付说明.
  - 依据: D001/D005/SKILL.md 现状.

## 顺序与依赖

ISSUE-01 → 02 → 04 → 05 → 06 → 07 → 08 主线串行 (单文件服务端, 并行必撞). ISSUE-03 (llm 中转) 与信箱面独立, 可插在 04 之后任一位置.

## 已知风险

- llm-proxy 原码不可达 → 中转面按 F001 规格重写, 行为细节以 e2e 门禁兜底 (已记 UNAUTHORIZED_DECISIONS).
- Quadlet 驻留与真机部署在容器内无法验证 → 交付件 + 文档, 真机验证归 M09.
- 首个指令集成员 (waypipe 拉起命令) 形态依赖 M06 盘问 → M03 只落注册表与校验机制.
