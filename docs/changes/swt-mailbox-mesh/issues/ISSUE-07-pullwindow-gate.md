## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
拉窗门禁: 取信 CLI 内置 waypipe 在场检查 + 同容器 300s 限频 + skipped 立即回执, 限频状态落设备本地文件跨取信循环生效. 适合 AFK: 门禁参数与行为从旧 pi 扩展平移, 无新设计.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-009
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 架构与组件 (取信脚本), 接口契约 (状态文件)

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D014

## 允许范围
- 修改 workflow/use-sandbox-worktree/scripts/swt-mailbox.py (取信逻辑)
- 新建 tests/test_swt_mailbox_pullwindow.py

## 禁止范围
- 不得修改 swt.py, sync-to-pi.py, pi/extensions/
- 不得把门禁逻辑放服务端 (D014: 在脚本)

## 代码定位提示
- pi/extensions/swt-mailbox-relay.ts 的 gatePullWindow 函数: 行为参考 (waypipe 检查/限频/skipped 回执/去重提示).
- waypipe 检查: subprocess 跑 "command -v waypipe", 退出码判定.
- 限频状态: state file (mailbox-state.json) 中 lastPullWindowAt dict[容器名 -> 时间戳].
- 取信 CLI 收到 exec 类型 pull-window 信 → 门禁 → skipped 回执 → 不输出到 stdout → 继续 poll.

## TDD 切片

- TS-001:
  接缝: 取信 CLI 收到 pull-window exec 信时的 stdout 与 ack.
  测试用例: TC-001.
  先写的失败测试: test_waypipe_missing_skipped — waypipe 不在场 (mock command -v 返回非零); 投一封 pull-window exec 信; CLI 应立即 ack skipped:waypipe-missing, stdout 不含该信正文, 输出安装提示.
  最小绿色实现范围: 取信循环中 exec/pull-window 分支 → waypipe 检查 → skipped ack → 提示.
  不得测试: 安装提示的精确文案.
  覆盖: AC-009.

- TS-002:
  接缝: 同容器 300s 限频.
  测试用例: TC-002.
  先写的失败测试: test_rate_limit — waypipe 在场 (mock 返回零); 投第一封 pull-window 信 → 正常呈现; 300s 内投第二封 → 自动 ack skipped:rate-limited, 不呈现.
  最小绿色实现范围: state file 限频时刻表 + 窗口判定.
  不得测试: 300s 的精确边界.
  覆盖: AC-009.

- TS-003:
  接缝: 限频状态跨取信循环重启生效.
  测试用例: TC-003.
  先写的失败测试: test_rate_limit_persists — 第一次取信处理了 pull-window 信; 模拟取信循环重启 (新 CLI 进程); 300s 内同容器再投 → 仍被限频.
  最小绿色实现范围: 限频时刻写 state file, 新进程读取.
  不得测试: state file 的 JSON 结构.
  覆盖: AC-009.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
uv run pytest tests/test_swt_mailbox_pullwindow.py -v
```

## 风险提示
- waypipe mock: 测试环境可能真的没有 waypipe, 用 monkeypatch subprocess 结果而非依赖真实环境.
- pull-window 信的 body 格式: JSON 含 tool=swt.pull-window 和 container 字段, 沿用现有格式.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
门禁行为/参数/回执格式均沿用旧 pi 扩展已实现逻辑, 本 issue 是平移.

## 验收标准
- [ ] waypipe 缺席 → pull-window 信自动 ack skipped + 安装提示, 不呈现给 LLM
- [ ] 300s 窗口内同容器重复 → 自动 ack skipped:rate-limited
- [ ] 限频状态落文件, 取信循环重启后仍生效
- [ ] 非 pull-window 的 exec 信不走此门禁 (走 ISSUE-03 的白名单)

## 被阻塞于
- ISSUE-01
