## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
租约投递与重投去重: 服务端 poll 时发放 lease_token 并计时, 超时未 ack 自动收回队列重投; 客户端取到已见信件 id 时自动回执不呈现给 LLM. 适合 AFK: 租约参数 (30 min 缺省) 和去重参数 (最近 100 条) 均已定.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-004
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 数据模型与状态 (信件状态机), 边界与异常处理

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D003, D008, D009

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt-mailbox.py (服务端投递逻辑 + 客户端取信逻辑)
- 修改 tests/test_swt_mailbox_core.py
- 新建 tests/test_swt_mailbox_lease.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/, agent-prompts/
- 不得实现 mesh 路由, LLM 中转, birth 接线
- 不得引入消息持久化 (NG-008: 信箱重启丢排队信)

## 代码定位提示
- ISSUE-01 建立的 Mailbox 类: 在 poll 返回信件处加 leases dict[letter_id -> 租约时刻].
- ISSUE-01 建立的取信 CLI: 在 state file 中加 seen_ids 列表 (最近 100 条 letter_id).
- 租约到期扫描: 后台线程定期检查 leases, 超时项收回 queue.
- 测试中时间推进: 用猴补替换 Mailbox 的时钟函数, 不真等 30 分钟.

## TDD 切片

- TS-001:
  接缝: poll 响应中的 lease_token 字段.
  测试用例: TC-001.
  先写的失败测试: test_poll_returns_lease_token — poll 返回信件时应同时返回非空 lease_token.
  最小绿色实现范围: poll handler 生成 lease_token (uuid hex), 存入 leases dict.
  不得测试: token 生成算法.
  覆盖: AC-004.

- TS-002:
  接缝: ack 端点的 lease_token 验证.
  测试用例: TC-002.
  先写的失败测试: test_ack_requires_valid_token — 用正确 token ack 成功; 用错误 token ack 返回 409.
  最小绿色实现范围: ack handler 比对 lease_token; 不匹配或已过期返回 409.
  不得测试: 过期判定的精确秒数.
  覆盖: AC-004.

- TS-003:
  接缝: 租约到期重投.
  测试用例: TC-003.
  先写的失败测试: test_lease_expiry_requeues — poll 拿到信不 ack; 猴补推进时钟超过租约; 信应回到队列可再次 poll 到.
  最小绿色实现范围: 后台扫描线程 (或 poll 时惰性检查) 检查 leases 过期项 → 收回 queue → 清除 lease.
  不得测试: 扫描线程的运行频率.
  覆盖: AC-004.

- TS-004:
  接缝: 客户端已见 id 去重.
  测试用例: TC-004.
  先写的失败测试: test_seen_id_dedup — 信 L1 被租约重投, 客户端再次取到 L1; CLI 应自动回执 L1 不在 stdout 呈现, 继续等待下一封.
  最小绿色实现范围: state file seen_ids 列表 (最近 100); 取信时命中已见 → 自动 ack → 继续 poll.
  不得测试: seen_ids 的淘汰策略.
  覆盖: AC-004.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_lease.py tests/test_swt_mailbox_core.py -v
```

## 风险提示
- 时钟猴补: 确保测试不真等 30 分钟, 用 injectable clock.
- seen_ids 与 lease 的交互: 重投后新 lease_token 生成, 旧 token ack 应 409.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
租约参数/去重参数/状态机已在 spec 精确定义.

## 验收标准
- [ ] poll 响应含 lease_token; ack 验证 token, 错误返回 409
- [ ] 租约到期信自动收回队列重投
- [ ] 客户端取到已见 id 自动回执不呈现给 LLM
- [ ] 信箱重启后队列清空 (NG-008 行为如实呈现)

## 被阻塞于
- ISSUE-01
