# AFK 模式自主决定记录

授权来源: 用户指令 "`@docs/changes/verification-skills/EXECUTION.md` AFK". 每条含 问题/决策/理由/影响/风险.

## D-AFK-001 子代理模型与思考档位

- 问题: 用户未指定子代理的 model 与 thinking, 需按 `llm-select` 选型.
- 决策: 执行者用 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`; 审核者 (code-review 轴) 用 `cli/gpt-6.1-sol`, thinking `xhigh`. 演练内被加载的 pi 会话与执行者同模型, 不单独选型.
- 理由: 评分表里 deepseek-v4.1-flash coding 1.12, speed 2.95, 成本低, 适合长时机械交付; gpt-6.1-sol coding 1.13, knowledge 1.24 为最高, 且与执行者不同厂商, 满足审查选型"尽量不同厂商".
- 影响: 执行者便宜快速; 审核者慢且贵, 但只在评审节点启动.
- 风险: deepseek 稳定性依据弱 (仅用户反馈), 若执行者反复失败, 在同一分支上换 gpt-6.1-sol 重派.

## D-AFK-002 临时演练项目的信任确认

- 问题: 非容器环境下 pi 会对新目录询问项目信任; AFK 期间无法逐次请示.
- 决策: 授权执行者在 `docs/changes/verification-skills/` 说明的临时项目 (`/tmp/**`) 与本次工作树内, 自行用 `pi -a` (一次性信任, 不落盘) 或确认信任提示.
- 理由: 目标目录都是本次任务自建的临时材料, 无生产数据; 不确认则演练无法启动.
- 影响: 演练可无人推进; 不写入全局配置.
- 风险: 若 pi 版本行为变化导致持久写入 `~/.pi/agent/trust.json`, 属违背禁止范围, 执行者须报告, 由合并节点前人工确认清理.

## D-AFK-003 工作树与工作目录位置

- 问题: 并行执行者需要互不干扰的目录.
- 决策: 工作树根为 `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-<NN>/`, 分支 `issue/<NN>`, 均从 `v2` 顶端切出; 演练临时项目放 `/tmp/orchestra-<ISSUE>/`.
- 理由: `tdd-as-orchestra` 的 git-worktree 使用规范固定命名, 且要避免污染主仓库搜索与测试范围.
- 影响: 现场可用 `git worktree list` 恢复.
- 风险: 磁盘占用; 合并后按规范清理.

## D-AFK-004 证据与报告文件的落点

- 问题: 子代理报告需要落盘, 但允许范围只覆盖 `evidence/**` 与 `issues/**`.
- 决策: 所有执行者/审核者报告写 `docs/changes/verification-skills/evidence/ISSUE-<NN>/HANDOFF.md`, 编排日志写 `evidence/ORCHESTRATION.md`, 基线写 `evidence/BASELINE.md`.
- 理由: 不越出全局允许范围; 合并后随分支进入主分支.
- 影响: 评审与收尾可追溯.
- 风险: 无.
