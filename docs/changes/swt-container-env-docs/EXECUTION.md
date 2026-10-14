# swt-container-env-docs Execution Spec

## 权威输入与决策引用

- Product Spec: `docs/changes/swt-container-env-docs/PRODUCT.md`
- Technical Spec: `docs/changes/swt-container-env-docs/TECHNICAL.md`
- 决策引用 (只读, 非意图来源): `docs/changes/swt-container-env-docs/DECISIONS.md`

## 全局允许范围

- `sync-to-pi.py` (宿主拼接项); 仓库根 `agent-prompts/` (新建, 仅 PUBLIC.md/PI.md); `pi/AGENTS.md` (删除)
- `workflow/use-sandbox-worktree/agent-prompts/` (五份母本, 删旧三份 *_AGENTS.md); `workflow/use-sandbox-worktree/scripts/env_docs.py` (新建); `workflow/use-sandbox-worktree/scripts/swt.py` (拼装/挂载/验收段); `workflow/navigate/SKILL.md` (删一节)
- `tests/` (新增 test_sync_to_pi_compose.py, test_env_docs.py, test_swt_stage_env.py; 改 test_swt_m12.py)
- `workflow/use-sandbox-worktree/SKILL.md`, `workflow/use-sandbox-worktree/reference/{ops,agent-templates}.md` (联动措辞), `docs/changes/swt-container-env-docs/DECISIONS.md` (仅回填 实际影响 字段)

## 全局禁止范围

- NG-001..NG-006 (PRODUCT.md 非目标): 不迁移运行中容器, 不改镜像三层与 agent-template 初始化结构, 不做启动时存在性检查, 不做宿主/容器提示词一致性校验, 不写 allow 清单与 create 后事实, 不做可写观察区
- `workflow/use-sandbox-worktree/scripts/agent_config/` (模板初始化契约), 镜像 Containerfile/层结构, mailbox skill, 客户端凭据通道 (stdin/600 文件), `docs/changes/swt-container-env-docs/{PRODUCT,TECHNICAL}.md` 的决策内容

## 完成定义

- 快层: `uv run python -m unittest tests.test_sync_to_pi_compose tests.test_env_docs tests.test_swt_stage_env -v` 全过; 既有受影响套件 (含 tests/test_swt_m12.py 快层部分) 不回归
- 机检: check-ac.py 与 check-tech.py 保持退出码 0
- 真容器: tests/test_swt_m12.py 的真容器验收项按既有审批流程单独执行 (需 rootless podman), 通过标准 = 该文件断言全过
- 账本: DECISIONS.md 各条 实际影响 已回填

## 测试策略

- AC 与标 (审计) 的 BR 断言: 纯函数单测 (env_docs), 拼装单测 (stage), 文件断言 (sync-to-pi/navigate), 真容器断言 (m12 ro 写与 born 路径). 接缝与测试适配器以 TECHNICAL.md 测试接缝映射为唯一来源
- 每个 issue 至少一个可执行 TDD 切片; ISSUE-04 为非代码特例 (文档与账本回填, 验证 = 内容断言 + 通读)

## 任务图

- ISSUE-01: `issues/ISSUE-01-host-agents-concat.md`; 覆盖: AC-001, AC-008; 依赖: 无
- ISSUE-02: `issues/ISSUE-02-env-docs-generator.md`; 覆盖: AC-004, AC-007; 依赖: 无
- ISSUE-03: `issues/ISSUE-03-swt-assembly-acceptance.md`; 覆盖: AC-002, AC-003, AC-005, AC-006, AC-009; 依赖: ISSUE-02
- ISSUE-04: `issues/ISSUE-04-linked-docs-ledger.md`; 覆盖: 非代码联动; 依赖: ISSUE-01, ISSUE-03
- ISSUE-05: `issues/ISSUE-05-env-docs-missing-key-contract.md`; 覆盖: 评审发现 (TECHNICAL 接口契约: 缺键按缺席文案渲染不抛); 依赖: ISSUE-02

## 覆盖矩阵

- AC-001 -> ISSUE-01 -> TC-001/TC-101/TC-102 -> tests/test_sync_to_pi_compose.py
- AC-002 -> ISSUE-03 -> TC-002/TC-103/TC-104 -> tests/test_swt_stage_env.py
- AC-003 -> ISSUE-03 -> TC-003 -> tests/test_swt_stage_env.py
- AC-004 -> ISSUE-02 -> TC-004/TC-105/TC-106/TC-107 -> tests/test_env_docs.py
- AC-005 -> ISSUE-03 -> TC-005/TC-108 -> tests/test_swt_m12.py (真容器)
- AC-006 -> ISSUE-03 -> TC-006/TC-109 -> tests/test_swt_stage_env.py + tests/test_swt_m12.py
- AC-007 -> ISSUE-02 -> TC-007/TC-110 -> tests/test_env_docs.py
- AC-008 -> ISSUE-01 -> TC-008 -> tests/test_sync_to_pi_compose.py
- AC-009 -> ISSUE-03 -> 无新 TC -> 既有 m12 挂载断言 (挂载随 create 固定, TECHNICAL.md 测试接缝已标注)
- BR-003 (审计) -> 人工验证: 对 env_docs.py 做结构审计 (纯函数, 无 IO, 无 llm 调用, 生成内容无运行时撰写), 通过标准 = 四项审计清单全过
- 安全策略 (TECHNICAL.md 节锚) -> ISSUE-03 -> TC-005/TC-108 (ro 拒写) + 全局禁止范围 (凭据通道不触碰)

## 全局风险和停止条件

- 需要改变 PRODUCT/TECHNICAL/DECISIONS 时停止
- 需要扩大允许范围或触碰禁止范围时停止
- Spec 与代码事实冲突或无法提供完成证据时停止
- 真容器验收环境缺失 (无 podman/镜像) 时, 快层完成后停止并报告, 不跳过不伪造
- 宽重构 (refactor-expand-contract.md): 不适用 — 无跨库机械改动, 各切片可独立保持绿色
