## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
三 agent 工具超时实测: 在 pi / codex / kimi 三种 agent 的交互会话中各跑一次无限阻塞长轮询, 记录行为 (是否被超时杀掉, 是否可继续操作, 输出是否被截断). 有超时限制的 agent 需确认 swt-mailbox.py 加 --wait 参数的可行性. 非 coding issue — 人工验证 + 记录结果.

## 覆盖依据
- Product: 无直接 AC; TECHNICAL.md 依赖与风险 (关键风险 3)
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 依赖与风险

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D018

## 允许范围
- 记录文件: docs/changes/swt-mailbox-mesh/agent-timeout-findings.md (新建)

## 禁止范围
- 不得修改任何代码
- 不得修改 Spec/决策

## 代码定位提示
- 测试命令: `sleep 600 && echo done` 或直接 `uv run python workflow/use-sandbox-worktree/scripts/swt-mailbox.py` (阻塞长轮询).
- pi: 交互会话中让 agent 跑上述命令, 观察是否被杀.
- codex: 同上.
- kimi: 同上.
- 记录: 每 agent 一节 — 工具默认超时 (有/无/秒数), 超时后行为 (杀进程/返回错误/可中断), 对阻塞长轮询的影响.

## TDD 切片

无 coding 切片. 人工验证 issue:
- 在三种 agent 中各实测一次, 结果记入 findings 文件.
- 有超时的 agent: 记录超时值, 并建议 --wait 参数缺省值.

## 验证入口
人工验证. 产出文件 docs/changes/swt-mailbox-mesh/agent-timeout-findings.md, 内容含三种 agent 的实测记录.

## 风险提示
- agent 可能无法精确报告超时值: 记录 "行为观察" 而非精确参数.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
不适用: 需要在三种真实 agent 中人工操作, HITL 必需.

## 验收标准
- [x] pi: 实测记录 (2026-09-20 本会话实测, sleep 600 跑满未被杀)
- [x] codex: 不适用 (用户裁决 2026-09-20: 取信只用 pi)
- [x] kimi: 不适用 (同上)
- [x] 有超时的 agent 附 --wait 参数建议 (无超时 agent, 无需建议)

## 被阻塞于
- 无 (可与 ISSUE-01~08 并行)
