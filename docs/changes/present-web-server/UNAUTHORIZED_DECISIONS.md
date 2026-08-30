# AFK 自主决定记录 (present-web-server 实现)

格式: 问题/决策/理由/影响/风险. 全部待用户确认.

## U-001 自建 EXECUTION.md

- 问题: tdd-as-orchestra 要求权威输入含 EXECUTION.md (任务拆分为 ISSUE), 仓库中缺失; 用户 AFK 无法补充.
- 决策: 总指挥依据 TECHNICAL.md 的 6 个 Seam 与 TC-001..TC-028 权威清单机械拆分 ISSUE-01..ISSUE-09, 写入 `docs/changes/present-web-server/EXECUTION.md`.
- 理由: 拆分不产生新需求, 只对已确认决策做执行分组; 红线不含此项.
- 影响: 执行顺序按 Seam 依赖排列 (CLI 骨架 → 生命周期 → 内容 → 控制面 → TTL → SKILL.md).
- 风险: 分组粒度与用户意图有出入; 缓解: 每组可独立提交, 逐组可审查.

## U-002 测试执行方式

- 问题: present 项目 venv 无 pytest, 测试如何运行 TECHNICAL.md 未写死.
- 决策: 从仓库根执行 `uv run python -m pytest general/present/tests` (仓库根环境有 pytest, pytest.ini 已含该 testpath, 基线 64 passed).
- 理由: F003 已确认 pytest.ini 零配置接入, 仓库根是 pytest 的自然入口.
- 影响: 子代理提示词统一此命令.
- 风险: 无.

## U-003 执行者调度粒度

- 问题: tdd-as-orchestra 字面上每测试切片起一个全新执行者, 28 条用例成本过高.
- 决策: 每个 ISSUE 一个执行者 (串行), 执行者内部严格遵守逐 TC 先红后绿, 一次一个切片; 每个 ISSUE 完成后由审核者 review, 只采纳明确发现项再交还修复.
- 理由: 保持小任务/证据清楚/上下文干净的精神不变 — 单 ISSUE 内用例同构, 执行者上下文不超载; review 仍独立.
- 影响: 子代理调用次数从 ~28+ 降为 ~9+9.
- 风险: 单执行者上下文在长 ISSUE 中膨胀; 缓解: ISSUE 最大 6 条用例, 超大则拆.
