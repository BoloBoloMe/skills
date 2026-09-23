## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
投信可见性: (1) send 回执分行打 `目标 session=` 与 `信件 id=`, 空 to 回打服务端实际解析出的目标; (2) post 应答带 `route` 五态 (`queued_local`/`forwarded`/`forwarded_partial`/`staged_pending`/`unknown_recipient`), send 按态打人话; (3) 转发异步化 — post 洪泛判定预算 2s, 超时邻居进后台重试, 任何邻居组合下 CLI 10s 内有结论; (4) post 校验 `from == 签名 session`, 不符 403; (5) 正文超 1MB 拒收 413. 适合 AFK: 行为已在 PRODUCT 场景与 TECHNICAL 接口节钉死.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-006..AC-010, AC-021, AC-022
- Technical: `../TECHNICAL.md`, 模块接口 (投信应答/信件 schema)/非功能要求/关键流程 (投递状态机)

## 相关决策
- `../DECISIONS.md`: D011 (A1/A2/A4/D3), D013

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (post 路由/应答, send CLI, 校验)
- `tests/test_mailbox_core.py`, `test_mailbox_mesh.py`, `test_mailbox_cli.py` 等

## 禁止范围
- 租约/poll/ack 语义 (ISSUE-06 才动回执)
- 邻居管理端点 (ISSUE-04)
- 指令集校验逻辑 (ISSUE-09)

## 代码定位提示
- mailbox.py: `Mailbox.post`/`_route`/`_flood` (384-465 行附近), `_handle_post`, `cmd_send` (1308 行附近), `send_forward`, `_retry_loop`
- 现事故根源行: `cmd_send` 末行 print 打的是 `letter["id"]`
- 测试先例: 双 Mailbox 内存互联在 test_mailbox_mesh.py

## TDD 切片
- TS-001:
  接缝: send CLI stdout.
  测试用例: TC-011.
  先写的失败测试: `test_send_receipt_two_lines` — 输出含分行 `目标 session=` 与 `信件 id=`; 现为单行, 失败.
  最小绿色实现范围: cmd_send 打印改造.
  不得测试: 内部变量名.
  覆盖: AC-006.
- TS-002:
  接缝: 同上 (空 to).
  测试用例: TC-012.
  先写的失败测试: `test_send_empty_to_echoes_resolved_target` — 空 to 时回执含服务端解析出的目标; 现打 letter id, 失败.
  最小绿色实现范围: post 应答带回 resolved to, CLI 展示.
  覆盖: AC-007.
- TS-003:
  接缝: post 应答 payload.
  测试用例: TC-013.
  先写的失败测试: `test_post_route_states` — 本机/邻居可达/邻居不可达/部分可达 四种布局下 route 分别为 queued_local/forwarded/staged_pending/forwarded_partial; 现无 route 字段, 失败.
  最小绿色实现范围: route 判定 + 异步洪泛预算 2s.
  覆盖: AC-008.
- TS-004:
  接缝: send CLI 退出码.
  测试用例: TC-014.
  先写的失败测试: `test_unknown_recipient_no_neighbors_fails` — 无邻居时投未知 session 退出码非零; 现 404 已报错 (回归锚, 可能直接绿).
  最小绿色实现范围: 确认并保持.
  覆盖: AC-009.
- TS-005:
  接缝: 时间注入 + 假邻居.
  测试用例: TC-015.
  先写的失败测试: `test_send_returns_within_budget_with_dead_neighbor` — 不可达邻居投信 <10s 返回且报暂存; 现同步 5s/邻居, 多死邻居超时, 失败.
  最小绿色实现范围: 异步洪泛 + 2s 预算.
  不得测试: 重试线程内部.
  覆盖: AC-010 + 非功能要求.
- TS-006:
  接缝: post HTTP 状态码.
  测试用例: TC-016.
  先写的失败测试: `test_body_over_1mb_413`; 现无上限, 失败.
  最小绿色实现范围: 请求体大小校验.
  覆盖: AC-021.
- TS-007:
  接缝: 同上.
  测试用例: TC-017.
  先写的失败测试: `test_from_mismatch_403` — letter.from != 签名 session 拒收; 现 from 未验签, 失败.
  最小绿色实现范围: post 加 from 校验.
  覆盖: AC-022.

## 验证入口
`uv run pytest tests/ -k "send or post or mesh" -q` 全绿.

## 风险提示
异步洪泛改变 `_flood` 调用时序 (锁外执行已有先例); 预算等待不得持有 cond 锁; from 验签影响 forward 路径 (邻居转发不验 from, 仅 post 验).

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
五态枚举/预算值/拒绝码全部已定, 无自由裁量.

## 验收标准
- [ ] send 回执分行, 空 to 回打实际目标
- [ ] post 应答五态且 CLI 按态打印
- [ ] 死邻居投信 <10s 返回
- [ ] from 伪造 403, 超 1MB 413
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-01
