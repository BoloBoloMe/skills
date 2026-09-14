# 状态: 已关闭
# 类型: prototype
# 阻塞于: 无

## 问题

信箱通道粗糙原型 (形态已按 M01 账本 D001-D008 改为 web 服务单体): 最小版基础服务信箱接口 (投信/长轮询取信/签名验签) + 阻塞取信脚本 + pi 扩展 triggerTurn 唤醒 + herdr 咬合 (host 上 pane / 远程固定 tab 两种会话形态), 与用户做一轮真跑, 验证 "来信→唤醒→处理" 常驻循环的实际手感 (延迟/成本/会话形态), 提升后续实施保真度.

依据: [M01 决策账本](../milestone-01/DECISIONS.md) + [recon/01](../recon/01-llm-channel.md) 考察点 1 (能力面).

## 结论 (2026-09-14 用户真跑 + 脚本冒烟)

问题: "来信 → 唤醒 → 处理" 常驻单向通道的状态模型是否成立, 实际手感如何. 答案: 成立.

- **延迟**: 长轮询链路即时. 用户真跑唤醒 2ms; 脚本冒烟 41/38/2ms — 来信即醒, 无需任何实时性升级.
- **成本**: hold 20s 空转只是 HTTP 超时重发, 零 token; 只有来信才消耗 LLM 轮 (唤醒数 = LLM 轮数). 常驻循环的待机成本可忽略.
- **状态模型**: queued → delivered → processed 三段流转顺畅; 缺省路由 (to 缺省 = 最近活跃设备) 冷启动可用.
- **安全链路符合设计**: exec 白名单命中直批 / 白名单外降级 request 问用户 (D005); ct-evil 越权类型 403 (D006); 重放同 id 被拦, 取信响应签名+nonce 验签 (D007).
- **会话形态**: host pane 形态真跑通过; 远程固定 tab 形态本次仅演示说明, 真机验证留给 M07.

### 移交 M03 实施的事实

- 原型简化不进正式版: 投信方向的错误响应未签名, 正式版按 D007 全响应签名.
- 未成文约定: 身份探测 (`/__identity__`) 等生命周期事件也写触发文件, 取信扩展必须忽略非 message 事件, 只对 message 事件 triggerTurn.
- 端口区间 38417-38426 本机实测首个空闲 = 38417 (D002).
- 未覆盖: SQLite 持久化与 7 天滚动清理 (D004 存续语义), 由 M03 实施.

### 归档指针

原型四文件保留在 `docs/changes/swt-cross-host-access/prototypes/mailbox-loop/` (commit `858dafa`, r2 单键版):
`mailbox_logic.py` = 纯状态模型, **正式 swt-base-server 的参考答案**; `server.py` / `fetch_loop.py` = 最小 HTTP 载体与阻塞取信脚本, 供对照; `tui.py` = 一次性外壳, 合并主干前由人清理. 运行: `uv run python tui.py`.
