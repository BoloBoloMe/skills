# swt 信箱 mesh 化重设计 Execution Spec

## 权威输入与决策引用
- Product Spec: `docs/changes/swt-mailbox-mesh/PRODUCT.md`
- Technical Spec: `docs/changes/swt-mailbox-mesh/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/swt-mailbox-mesh/DECISIONS.md`

## 全局允许范围
- workflow/use-sandbox-worktree/scripts/swt-mailbox.py (新建)
- workflow/use-sandbox-worktree/scripts/swt.py (birth 接线部分)
- workflow/use-sandbox-worktree/scripts/swt-base-server.py (删除)
- workflow/use-sandbox-worktree/scripts/swt-base-server.service (删除)
- workflow/use-sandbox-worktree/agent-prompts/ (三母本)
- workflow/use-sandbox-worktree/SKILL.md
- pi/extensions/swt-mailbox-relay.ts (删除)
- pi/extensions/swt-mailbox-fetch.mjs (删除)
- sync-to-pi.py (同步列表)
- tests/test_swt_mailbox_*.py (新建)
- tests/test_swt_base_server*.py (删除)
- tests/test_swt_birth_mailbox.py (删除)

## 全局禁止范围
- 不得修改: docs/language/, docs/adr/, docs/changes/swt-mailbox-mesh/ (Spec/决策产物)
- 不得修改: workflow/use-sandbox-worktree/reference/ (errors.md, ops.md, risks.md — ISSUE-09 SKILL.md 更新时可附带更新引用)
- 不得修改: general/ 下其他 skill
- NG-001: 不做取信会话唯一性强制
- NG-002: 不做消息类型按身份限制
- NG-003: 不做密钥分离
- NG-004: 不做自动首启
- NG-005: 不追溯存量
- NG-006: 容器→设备协议语义不变
- NG-007: 不做自启/守护
- NG-008: 不保证信箱重启不丢信
- NG-009: 不做转发持久化

## 完成定义
- `uv run pytest tests/ -v` 全绿 (新测试通过, 旧已删测试不存在)
- `uv run python sync-to-pi.py` 正常完成且扩展目录无旧文件
- 手动验证 AC-011 (新 pi 会话无后台取信活动) — HITL
- 手动验证 D018 (三 agent 超时实测) — HITL

## 测试策略
测试接缝映射表见 TECHNICAL.md 测试接缝 节, 为接缝唯一来源. 每个 issue 的 TDD 切片在 issue 文件中定义, 全部以 HTTP 端点或 CLI 子进程为接缝 (不测内部类). 测试命名: tests/test_swt_mailbox_<topic>.py.

## 任务图
- ISSUE-01: `issues/ISSUE-01-core-mailbox-loop.md`; 覆盖: AC-001, AC-003; 依赖: 无; 含 D019 数据库迁移
- ISSUE-02: `issues/ISSUE-02-lease-redelivery.md`; 覆盖: AC-004; 依赖: ISSUE-01
- ISSUE-03: `issues/ISSUE-03-whitelist-concurrency.md`; 覆盖: AC-002, AC-005, AC-012; 依赖: ISSUE-01
- ISSUE-04: `issues/ISSUE-04-cli-tools-migration.md`; 覆盖: AC-006, AC-010; 依赖: ISSUE-01
- ISSUE-05: `issues/ISSUE-05-mesh-routing.md`; 覆盖: AC-013 (mesh); 依赖: ISSUE-01
- ISSUE-06: `issues/ISSUE-06-llm-relay.md`; 覆盖: AC-013 (relay); 依赖: ISSUE-01
- ISSUE-07: `issues/ISSUE-07-pullwindow-gate.md`; 覆盖: AC-009; 依赖: ISSUE-01
- ISSUE-08: `issues/ISSUE-08-birth-wiring.md`; 覆盖: AC-007, AC-008; 依赖: ISSUE-01
- ISSUE-09: `issues/ISSUE-09-retire-cleanup-docs.md`; 覆盖: AC-011; 依赖: ISSUE-01~08 全部
- ISSUE-10: `issues/ISSUE-10-agent-timeout-verification.md`; 覆盖: D018; 依赖: 无 (可并行)

## 覆盖矩阵
- AC-001 -> ISSUE-01 -> TC (test_swt_mailbox_core/cli) -> uv run pytest
- AC-002 -> ISSUE-03 -> TC (test_swt_mailbox_whitelist) -> uv run pytest
- AC-003 -> ISSUE-01 -> TC (test_swt_mailbox_cli retry) -> uv run pytest
- AC-004 -> ISSUE-02 -> TC (test_swt_mailbox_lease) -> uv run pytest
- AC-005 -> ISSUE-03 -> TC (test_swt_mailbox_concurrency scatter) -> uv run pytest
- AC-006 -> ISSUE-04 -> TC (test_swt_mailbox_cli_tools send) -> uv run pytest
- AC-007 -> ISSUE-08 -> TC (test_swt_mailbox_birth) -> uv run pytest
- AC-008 -> ISSUE-08 -> TC (test_swt_mailbox_birth revoke) -> uv run pytest
- AC-009 -> ISSUE-07 -> TC (test_swt_mailbox_pullwindow) -> uv run pytest
- AC-010 -> ISSUE-04 -> TC (test_swt_mailbox_cli_tools config/status/migration) -> uv run pytest
- AC-011 -> ISSUE-09 -> 人工验证: sync-to-pi 后新 pi 会话无后台活动
- AC-012 -> ISSUE-03 -> TC (test_swt_mailbox_concurrency 409) -> uv run pytest
- AC-013 -> ISSUE-05 + ISSUE-06 -> TC (test_swt_mailbox_mesh + relay) -> uv run pytest
- BR-001 -> ISSUE-02 -> TC (test_swt_mailbox_lease) -> uv run pytest
- BR-002 -> ISSUE-01 -> TC (test_swt_mailbox_cli stdout) -> uv run pytest
- BR-003 -> ISSUE-01 + ISSUE-08 -> TC -> uv run pytest
- BR-004 -> ISSUE-05 -> TC (test_swt_mailbox_mesh seen-id) -> uv run pytest
- BR-005 (审计) -> ISSUE-01 -> TC (test_swt_mailbox_cli idle zero output) -> uv run pytest
- BR-006 (审计) -> ISSUE-04 -> TC (test_swt_mailbox_cli_tools masked) -> uv run pytest
- BR-007 (审计) -> ISSUE-01 -> 人工验证: swt-mailbox.py import 列表无第三方
- BR-008 (审计) -> ISSUE-09 -> 人工验证: git ls-files 无 .service 文件
- BR-009 (审计) -> ISSUE-01 -> TC (test_swt_mailbox_core SQLite schema) -> uv run pytest
- D019 数据库迁移 -> ISSUE-01 -> TC (test_swt_mailbox_core credential persistence) -> uv run pytest
- 非功能要求/空闲等待零 LLM 调用 -> ISSUE-01 -> TC -> uv run pytest
- 非功能要求/取信延迟 -> ISSUE-01 + ISSUE-05 -> TC (e2e 断言) -> uv run pytest
- D018 三 agent 超时实测 -> ISSUE-10 -> 人工验证: agent-timeout-findings.md

## 全局风险和停止条件
- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止.
- 需要扩大允许范围或触碰禁止范围时停止.
- Spec 与代码事实冲突或无法提供完成证据时停止.
- swt.py 修改波及非接线功能 (birth/resume/terminate 核心流程) 时停止.
