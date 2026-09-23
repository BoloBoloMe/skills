## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
取信与服务状态显式: (1) 组件读状态文件先 `__identity__` 验活, 失活明报 "信箱不可达"; (2) 取信首次连接失败立即输出 "信箱服务未启动/不可达" 再进退避, 不静默; (3) 取信加 `--timeout <秒>` (到时无信退出码 0 报无信) 与 `--count <n>` (取满即退); (4) 信箱口新增 `GET /mailbox/queued` (session 签名, 回本机会话队列深度), status 输出含待取数; (5) status 重写: 认 env 凭证, 验活, 报真实 session/地址/存活. 适合 AFK: 参数与输出语义已定.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-014, AC-015, AC-016, AC-017, AC-036
- Technical: `../TECHNICAL.md`, 模块接口 (取信 CLI/信箱口)

## 相关决策
- `../DECISIONS.md`: D011 (C1/C2/C3/C5)

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (cmd_fetch/cmd_status, 信箱口 handler)
- `tests/test_mailbox_cli.py`, `test_mailbox_admin.py` (或新 test_mailbox_queued)

## 禁止范围
- 取信守护注入逻辑 (ISSUE-07, pi 扩展)
- per-listener `--cli-state` 由 ISSUE-07 实现, 本 issue 不动
- 回执信呈现 (ISSUE-06)

## 代码定位提示
- mailbox.py: `cmd_fetch` (退避循环段), `cmd_status`, `load_credentials`, `_Handler.do_GET` (现只有 __identity__)
- swt.py 的 probe 验活已走 discover (ISSUE-02 后), 本 issue 管 CLI 侧
- 测试: test_mailbox_cli.py 现成 CLI 夹具

## TDD 切片
- TS-001:
  接缝: CLI stderr/退出行为.
  测试用例: TC-024.
  先写的失败测试: `test_stale_state_file_reports_unreachable` — serve 停 + 状态文件残留时组件报不可达; 现直接当真或静默, 失败.
  最小绿色实现范围: 读状态文件后验活分支.
  覆盖: AC-014.
- TS-002:
  接缝: cmd_fetch stderr.
  测试用例: TC-025.
  先写的失败测试: `test_fetch_reports_service_down_immediately` — 服务未起时立即打明报行再退避; 现静默, 失败.
  最小绿色实现范围: 首次连接失败打印一次.
  覆盖: AC-015.
- TS-003:
  接缝: CLI 参数.
  测试用例: TC-026.
  先写的失败测试: `test_fetch_timeout_exits_and_reports` — `--timeout 5` 无信到时退出码 0 报无信; 参数不存在, 失败.
  最小绿色实现范围: --timeout 实现.
  覆盖: AC-016 (timeout 行).
- TS-004:
  接缝: 同上.
  测试用例: TC-027.
  先写的失败测试: `test_fetch_count_exits_after_n` — `--count 2` 取满 2 封即退; 失败.
  最小绿色实现范围: --count 实现.
  覆盖: AC-016 (count 行).
- TS-005:
  接缝: status stdout + env 凭证.
  测试用例: TC-028.
  先写的失败测试: `test_status_env_credentials_and_liveness` — 仅 env 凭证时输出真实 session/地址/存活; 现全 "(未设置)", 失败.
  最小绿色实现范围: status 重写.
  覆盖: AC-017.
- TS-006:
  接缝: `/mailbox/queued` 端点.
  测试用例: TC-029.
  先写的失败测试: `test_queued_returns_depth` — 3 封排队返回 3, 无签名 403; 端点不存在, 失败.
  最小绿色实现范围: 端点 + status 集成.
  覆盖: AC-036.

## 验证入口
`uv run pytest tests/ -k "fetch or status or queued" -q` 全绿.

## 风险提示
--count 与 pending_ack 自动回执的交互: 取满即退时最后一封的 pending_ack 留在 cli-state, 下次调用正常回执, 不丢; 明报行只打一次不刷屏.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
参数语义/退出码/输出文案方向已定, 无自由裁量.

## 验收标准
- [ ] 残留状态文件验活失活明报
- [ ] 取信连不上立即明报
- [ ] --timeout/--count 按场景工作
- [ ] status 认 env 凭证 + 验活 + 待取数
- [ ] 相关测试全绿

## 被阻塞于
- ISSUE-01
