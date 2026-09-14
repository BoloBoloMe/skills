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
