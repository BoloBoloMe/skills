## 父级
- `../EXECUTION.md`

## 执行
- [x] 已实现

## 要构建什么
旧机制退役与文档更新: 删除旧文件 (pi/extensions/swt-mailbox-relay.ts + swt-mailbox-fetch.mjs + scripts/swt-base-server.py + scripts/swt-base-server.service), 更新 sync-to-pi.py 同步列表, 更新 agent-prompts 三母本取信指引, 更新 SKILL.md 基础服务节. 适合 AFK: 删除清单和文档更新点已在决策中明确定义.

## 覆盖依据
- Product: `docs/changes/swt-mailbox-mesh/PRODUCT.md`, AC-011
- Technical: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`, 架构与组件 (模块/目录边界)

## 相关决策
- `docs/changes/swt-mailbox-mesh/DECISIONS.md`: D017

## 允许范围
- 删除 pi/extensions/swt-mailbox-relay.ts
- 删除 pi/extensions/swt-mailbox-fetch.mjs
- 删除 workflow/use-sandbox-worktree/scripts/swt-base-server.py
- 删除 workflow/use-sandbox-worktree/scripts/swt-base-server.service
- 删除 tests/test_swt_base_server*.py, tests/test_swt_birth_mailbox.py (旧测试)
- 修改 sync-to-pi.py (同步列表不再含已删文件)
- 修改 workflow/use-sandbox-worktree/agent-prompts/pi_AGENTS.md
- 修改 workflow/use-sandbox-worktree/agent-prompts/codex_AGENTS.md
- 修改 workflow/use-sandbox-worktree/agent-prompts/kimi-code_AGENTS.md
- 修改 workflow/use-sandbox-worktree/SKILL.md

## 禁止范围
- 不得删除 tests/test_swt_mailbox_*.py (新测试)
- 不得修改 DECISIONS.md / PRODUCT.md / TECHNICAL.md
- 不得修改 swt-mailbox.py 或 swt.py (ISSUE-01~08 的产物)

## 代码定位提示
- sync-to-pi.py 行 418-423: pi/extensions/ 同步逻辑, 确认删除后不再同步已删文件.
- agent-prompts 三母本: 通用核中提及取信的部分改为新指令 (调 swt-mailbox.py); 三母本通用核逐字相同, 改一处同步三处.
- SKILL.md "基础服务" 节: 重写为 mesh 架构 (serve 手动启动, 取信靠脚本, 无 systemd).
- SKILL.md "设备侧怎么收取信会话" 段: 重写为脚本口径.
- SKILL.md "分发与生效" 节: 更新为 swt-mailbox.py 的同步路径.

## TDD 切片

- TS-001:
  接缝: sync-to-pi.py 同步后的目标目录.
  测试用例: TC-001.
  先写的失败测试: test_sync_no_old_extensions — sync-to-pi 后 ~/.pi/agent/extensions/ 不含 swt-mailbox-relay.ts 和 swt-mailbox-fetch.mjs.
  最小绿色实现范围: 删除源文件即可 (sync 只复制存在文件).
  不得测试: sync 的完整流程 (已有 test_sync_to_pi.py).
  覆盖: AC-011.

- TS-002:
  接缝: 仓库文件系统.
  测试用例: TC-002.
  先写的失败测试: test_old_files_deleted — 断言 git ls-files 不含 swt-base-server.py / .service / relay.ts / fetch.mjs.
  最小绿色实现范围: git rm 已删文件.
  不得测试: 无.
  覆盖: AC-011.

- TS-003 (人工验证):
  接缝: 升级后的新 pi 会话.
  测试用例: TC-003.
  先写的失败测试: 手动开新 pi 会话 (sync-to-pi 后), 用 ps/netstat 观察无信箱相关后台进程和网络连接.
  最小绿色实现范围: 删除扩展后新会话不再加载.
  不得测试: 无.
  覆盖: AC-011.

## 验证入口
```bash
cd /home/bolo/Workspace/skills
git ls-files | grep -c "swt-base-server\|swt-mailbox-relay\|swt-mailbox-fetch"  # 应为 0
uv run pytest tests/ -v --ignore=tests/test_swt_base_server*.py --ignore=tests/pi  # 新测试全绿
uv run python sync-to-pi.py  # 同步后手动验证 AC-011
```

## 风险提示
- 删除旧测试文件时确认新测试 (test_swt_mailbox_*.py) 不被误删.
- 三母本通用核同步: 改一处后 diff 三处确认逐字相同.
- SKILL.md 改动幅度大, 保留 birth/resume/terminate/显示栈等未变章节.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
删除清单/文档更新点已在决策定义; AC-011 的人工验证部分需 HITL.

## 验收标准
- [ ] 旧文件全部从 git 追踪中移除
- [ ] sync-to-pi 后扩展目录不含旧扩展
- [ ] 新 pi 会话无后台取信活动 (人工验证)
- [ ] 三母本取信指引统一更新
- [ ] SKILL.md 基础服务节反映 mesh 架构

## 被阻塞于
- ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, ISSUE-05, ISSUE-06, ISSUE-07, ISSUE-08
