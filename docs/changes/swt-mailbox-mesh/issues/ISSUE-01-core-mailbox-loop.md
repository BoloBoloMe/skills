## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
最小信箱端到端闭环: 单实例 serve 启动 → session 注册 → 信件投递 (post) → 阻塞取信 (poll) → 回执 (ack) → 取信 CLI 自动回执上一条. 包含 HMAC 签名协议, 内存队列, 故障自愈 (网络断重试不退出), serve 自动发本机凭证. 适合 AFK: 全部行为已在 spec 中精确定义, 无需进一步决策.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-001, AC-003
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 架构与组件, 接口契约, 数据模型与状态

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D001, D002, D003, D005, D008, D010, D012, D019

## 允许范围
- 新建 workflow/use-sandbox-worktree/scripts/swt-mailbox.py
- 新建 tests/test_swt_mailbox_core.py
- 新建 tests/test_swt_mailbox_cli.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/, agent-prompts/, SKILL.md
- 不得实现 mesh 路由 (ISSUE-05), 租约 (ISSUE-02), 指令集降级 (ISSUE-03), 拉窗门禁 (ISSUE-07), LLM 中转 (ISSUE-06), birth 接线 (ISSUE-08)
- NG-001 (不设唯一性强制), NG-004 (不自动首启), NG-007 (无自启)

## 代码定位提示
- 新文件, 无既有代码. 参考 swt-base-server.py 的 HMAC 签名/长轮询/ThreadingHTTPServer 形态 (只参考协议形状, 不照搬单体结构).
- swt-base-server.py 中 sign()/verify 相关函数和 try_deliver/empty_payload 是协议实现的直接参考.
- poll 的 hold 机制: threading.Condition + wait(timeout=20), post 时 notify_all 唤醒.
- pytest 惯例: tests/ 下命名 test_swt_mailbox_*.py, 用 urllib.request 做真实 HTTP 客户端.

## TDD 切片

- TS-001:
  接缝: serve 子进程的 HTTP 端点 (__identity__).
  测试用例: TC-001.
  先写的失败测试: test_identity_probe — 启动 serve 后 GET /__identity__ 应返回 200 + JSON 含 "swt-mailbox".
  最小绿色实现范围: argparse 解析 serve 子命令 + ThreadingHTTPServer 绑定 38417-38426 首空闲 + __identity__ handler.
  不得测试: 内部类结构, 端口选择算法细节.
  覆盖: AC-001.

- TS-002:
  接缝: serve 子进程的 admin 端点 + 信箱面 post/poll.
  测试用例: TC-002.
  先写的失败测试: test_post_and_poll — 经 admin 注册 session, 用签名 post 投一封 notify 信, poll 应阻塞后返回该信.
  最小绿色实现范围: Session/Letter/Mailbox 类 + HMAC 签名验证 + admin POST /admin/sessions + POST /mailbox/post + POST /mailbox/poll (hold + 唤醒).
  不得测试: 内部队列数据结构, 签名计算内部步骤.
  覆盖: AC-001.

- TS-003:
  接缝: serve 子进程的 ack 端点.
  测试用例: TC-003.
  先写的失败测试: test_ack — poll 拿到信后 ack, 信不再可取.
  最小绿色实现范围: POST /mailbox/ack + 信件从内存队列移除.
  不得测试: ack 内部状态转换细节.
  覆盖: AC-001.

- TS-004:
  接缝: swt-mailbox.py 缺省动作 (取信 CLI 子进程).
  测试用例: TC-004.
  先写的失败测试: test_fetch_cli — subprocess 运行 swt-mailbox.py (缺省取信), poll 挂起; 另一线程投信; CLI stdout 应输出信件正文 + 处理指引 + 继续调用提示.
  最小绿色实现范围: 凭证探测 (env/config) + 阻塞 poll + stdout 格式化 + 信件类型语义指引 + 不可信输入声明.
  不得测试: stdout 格式的逐字节匹配 (只断言关键子串).
  覆盖: AC-001.

- TS-005:
  接缝: 取信 CLI 的自动回执.
  测试用例: TC-005.
  先写的失败测试: test_auto_ack — 第一次取到信 L1; 第二次调用取信 CLI (此时无新信, 投一封 L2); CLI 应先自动 ack L1 再阻塞; 服务端侧 L1 不再可取.
  最小绿色实现范围: state file (mailbox-state.json) 记录待回执 letter_id; 取信启动时先 POST ack 上一条.
  不得测试: state file 的 JSON 结构细节.
  覆盖: AC-001.

- TS-006:
  接缝: 取信 CLI 的故障自愈.
  测试用例: TC-006.
  先写的失败测试: test_retry_on_network_error — serve 未启动时取信 CLI 应静默重试不退出 (测试内在超时窗口内子进程仍存活); serve 启动后投信, CLI 正常返回.
  最小绿色实现范围: 内部退避重试循环 (连接拒绝/超时 → sleep backoff → 重试), 不 print 不 exit.
  不得测试: 退避间隔精确值.
  覆盖: AC-003.

- TS-007:
  接缝: serve 启动时的自动凭证发放.
  测试用例: TC-007.
  先写的失败测试: test_auto_credential — serve 启动后 ~/.agents/sandbox-worktree/mailbox.json 应存在且含 session/signing_key/response_key; 用该凭证 poll 应成功.
  最小绿色实现范围: serve 启动序列中检测配置缺失 → admin 自动注册 <hostname>-host session → 写配置文件 (0600, 目录 0700).
  不得测试: session id 的精确格式 (只断言非空).
  覆盖: AC-001.

- TS-008:
  接缝: SQLite 凭证持久化.
  测试用例: TC-008.
  先写的失败测试: test_credential_persistence — serve 启动注册 session, 重启 serve, session 仍可 poll.
  最小绿色实现范围: SQLite sessions 表 (id/signing_key/response_key/revoked/last_poll/created_at), 启动时加载, 注册时写入. 不存信件.
  不得测试: SQLite 文件路径.
  覆盖: AC-001.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_core.py tests/test_swt_mailbox_cli.py -v
```

## 风险提示
- poll hold 机制的线程安全: post 的 notify_all 必须能唤醒所有等待中的 poll (Condition 而非 Event).
- 端口冲突: 测试中用 --port 参数指定独立端口, 不与生产 38417 冲突.
- serve 自动写配置文件: 测试环境用 env SWT_MAILBOX_CONFIG 覆盖路径, 不污染真实配置.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
全部端点/协议/文件路径/输出格式已在 TECHNICAL.md 精确定义; 无需产品或架构决策.

## 验收标准
- [ ] serve 启动后 __identity__ 可探测, admin 可注册 session
- [ ] 签名 post → 阻塞 poll → 返回信件 → ack → 不再可取
- [ ] 取信 CLI 输出信件正文+处理指引+继续调用提示+不可信声明, 自动回执上一条
- [ ] serve 未启动时 CLI 静默重试不退出, 启动后正常返回
- [ ] serve 自动发本机凭证并写入 0600 配置文件
- [ ] serve 重启后 session 凭证从 SQLite 恢复
- [ ] 空闲等待期间 stdout 零输出 (BR-005)
- [ ] 脚本零第三方依赖 (BR-007)

## 被阻塞于
- 无
