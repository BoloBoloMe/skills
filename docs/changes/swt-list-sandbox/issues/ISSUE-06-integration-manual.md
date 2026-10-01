## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

集成验证与人工验证承接 (非代码 issue): 跑全量快层回归确认整体绿色; 在 host pi 真机装载扩展 (sync-to-pi 或手工登记) 执行人工清单: TUI select/custom 实际渲染 (AC-006 渲染面, AC-001/002 交互展示), rpc/print/json 三模式真机行为, 无 podman 容器内降级, 子进程超时降级 (挂起 fake), BR-007 运行态审查 (执行 /list-sandbox 后会话文件无新增模型可见条目, 代码确认无 sendUserMessage/sendMessage). 本 issue 为人工验证特例, 无 TDD 切片.

## 覆盖依据

- Product: `docs/changes/swt-list-sandbox/PRODUCT.md`, AC-006 (渲染面), BR-007
- Technical: `docs/changes/swt-list-sandbox/TECHNICAL.md`, 测试接缝 (接缝 C: 无自动化替身, 手动验证), 模块接口 (M2 超时错误模式)

## 相关决策

- `docs/changes/swt-list-sandbox/DECISIONS.md`: D009, D010

## 允许范围

- 无代码改动; 仅执行验证与 (如登记机制异常时的) 问题上报.
- 允许在 host 上临时登记扩展路径用于验证.

## 禁止范围

- 一切代码修改 (发现问题回投对应 issue, 不在本 issue 内修).

## 代码定位提示

- 验证对象: `workflow/use-sandbox-worktree/pi-extension/index.ts` (装载), `scripts/swt.py` list 子命令 (真机).
- 会话文件位置: pi 会话 jsonl (检查 /list-sandbox 执行前后条目数).

## TDD 切片

- 无 — 人工验证特例 (接缝 C 无测试替身, TECHNICAL.md 测试接缝节明示).

## 验证入口

- `tests/run --fast` 全绿.
- 人工清单 (host 真机):
  1. TUI 执行 /list-sandbox: 选择列表出现全部在用容器, 选中后看到访问入口滚动文本, 退出后编辑器恢复.
  2. rpc 模式: 收到 notify 摘要.
  3. print 模式 (`pi -p` 场景): stdout 无交互内容, stderr 一行提示.
  4. 容器内 pi (无 podman): 收到 仅 host pi 可用 提示, 不崩.
  5. 超时降级: 以 `LIST_PYTHON=... ` 类环境钩子或临时 PATH 注入挂起脚本 (不改代码, 用 shell 包装), 确认 120s 后按模式降级提示.
  6. BR-007: 执行前后会话文件对比, 无新增模型可见条目.
- 通过标准: 清单 6 项全部符合, 快层全绿.

## 风险提示

- 真机 host 与本仓库开发容器环境不同: podman/records-root 差异属预期, 验证以 host 实况为准.
- 清单 5 的挂起注入不得改动扩展代码, 用外部包装实现.

## 停止条件

- 任一项不符合且定位到代码缺陷时停止, 回投对应 issue; 需要改 Spec/决策时停止.

## 适合 AFK 的原因

不适合 AFK — 需要人在 host 真机逐项执行清单 (HITL).

## 验收标准

- [ ] `tests/run --fast` 全绿.
- [ ] 人工清单 6 项逐项通过并留痕 (勾选记录或截图/日志摘录).

## 被阻塞于

- ISSUE-01 (`issues/ISSUE-01-list-skeleton.md`)
- ISSUE-02 (`issues/ISSUE-02-running-entries.md`)
- ISSUE-03 (`issues/ISSUE-03-stopped-unmatched.md`)
- ISSUE-04 (`issues/ISSUE-04-pi-extension.md`)
- ISSUE-05 (`issues/ISSUE-05-sync-reconcile.md`)
