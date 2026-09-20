## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
指令集降级与并发保护: post 时 exec 类型信件过白名单校验, 不在集合内自动降级为 request; 同 session 并发 poll 超上限返回 409, 客户端退避重试; 双会话散落行为测试. 适合 AFK: 白名单语义和并发参数均已定义.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-002, AC-005, AC-012
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 接口契约 (admin/whitelist), 边界与异常处理

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D004, D006, D016

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt-mailbox.py
- 修改 tests/test_swt_mailbox_core.py
- 新建 tests/test_swt_mailbox_whitelist.py
- 新建 tests/test_swt_mailbox_concurrency.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/
- 不得按 session 身份限制消息类型 (NG-002: 不做身份级限制)
- 不得实现 mesh/中转/birth

## 代码定位提示
- ISSUE-01 建立的 post handler: 在信件入队前加 exec 类型校验分支.
- swt-base-server.py 的 _parse_instruction/_pull_window_hit/whitelist 逻辑是直接参考 (搬迁而非重写).
- 并发计数: Mailbox 类加 concurrent_polls dict[session_id -> count], poll 进入时 +1, 退出时 -1.
- 双会话测试: 两个线程分别 poll, 断言同一封信只被一个线程取到.

## TDD 切片

- TS-001:
  接缝: post 响应中的 downgraded 字段.
  测试用例: TC-001.
  先写的失败测试: test_exec_whitelist_downgrade — post 一封 exec 类型信, body 含不在白名单的 tool; poll 到的信应带 downgraded=true 和降级说明.
  最小绿色实现范围: post handler 中 exec 类型 → 解析 body 为 JSON → 查 whitelist → 不在集合 → letter.downgraded = true + note.
  不得测试: 白名单的存储格式.
  覆盖: AC-002.

- TS-002:
  接缝: admin whitelist 注册端点.
  测试用例: TC-002.
  先写的失败测试: test_whitelist_registration — admin 注册指令 → post 匹配的 exec 信 → poll 到的信 downgraded=false + "指令集命中" 标注.
  最小绿色实现范围: POST /admin/whitelist + SQLite whitelist 表.
  不得测试: 指令 JSON 的完整 schema.
  覆盖: AC-002.

- TS-003:
  接缝: poll 的 HTTP 409 响应.
  测试用例: TC-003.
  先写的失败测试: test_concurrent_poll_limit — 同 session 发 5 个并发 poll (全部挂起); 第 6 个 poll 应立即返回 409.
  最小绿色实现范围: Mailbox 类并发计数器 + poll handler 入口检查.
  不得测试: 计数器的线程同步实现.
  覆盖: AC-012.

- TS-004:
  接缝: 取信 CLI 收到 409 后的行为.
  测试用例: TC-004.
  先写的失败测试: test_client_backoff_on_409 — CLI 取信时收到 409; 应退避后重试, 不退出不报错.
  最小绿色实现范围: 取信 CLI 的重试循环中加入 409 处理分支.
  不得测试: 退避间隔精确值.
  覆盖: AC-012.

- TS-005:
  接缝: 两个并发 poll 请求的响应互斥性.
  测试用例: TC-005.
  先写的失败测试: test_dual_session_scatter — 两个不同 session 的 poll 同时挂起; 投一封给其中一个 session 的信; 只有该 session 的 poll 返回信, 另一个继续等待.
  最小绿色实现范围: ISSUE-01 的队列按 session 分隔已天然支持; 只需验证.
  不得测试: 内部队列实现.
  覆盖: AC-005.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_whitelist.py tests/test_swt_mailbox_concurrency.py -v
```

## 风险提示
- 并发 poll 测试的线程协调: 用 threading.Barrier 确保前 5 个 poll 全部挂起后再发第 6 个.
- whitelist 逻辑从 swt-base-server.py 搬迁时注意 pull_window 动态绑定 (swt.pull-window 特例) 的保留.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
白名单语义/并发上限/降级行为均已在 spec 和现有代码中精确定义.

## 验收标准
- [ ] exec 不在白名单 → poll 到的信带 downgraded=true + 降级说明
- [ ] admin 可注册 whitelist; 匹配的 exec 信 downgraded=false
- [ ] 同 session 第 6 个并发 poll 返回 409
- [ ] 客户端收到 409 退避重试不退出
- [ ] 一封信只投给目标 session 的 poll, 其他 session 取不到

## 被阻塞于
- ISSUE-01
