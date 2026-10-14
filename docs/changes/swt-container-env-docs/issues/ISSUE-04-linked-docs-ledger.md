## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已实现
## 要构建什么
非代码联动: SKILL.md 三处 (母本与分发节重写为拼装制, base 层描述 pi CLI → pi/codex/kimi 三 CLI, 交付包 "容器内路径契约" 行加环境文本位置与 ~/docs/), reference/ops.md 挂载示例行更新, reference/agent-templates.md "不替代三份公共 AGENTS.md 母本" 措辞更新, DECISIONS.md 各条 实际影响 回填.
## 覆盖依据
- Product: `../PRODUCT.md`, 无直接 AC (文档一致性, 支撑全部 AC 的可理解性)
- Technical: `../TECHNICAL.md`, 无对应节 (写 "无")
## 相关决策
- `../DECISIONS.md`: D004, D013, D016, D019
## 允许范围
- `workflow/use-sandbox-worktree/SKILL.md` (三处), `workflow/use-sandbox-worktree/reference/ops.md`, `workflow/use-sandbox-worktree/reference/agent-templates.md`, `docs/changes/swt-container-env-docs/DECISIONS.md` (仅 实际影响 字段)
## 禁止范围
- 引入新决策内容 (回填只记录已实现事实); PRODUCT/TECHNICAL/EXECUTION; F007 已完成的 UBIQUITOUS_LANGUAGE.md (固化阶段已改, 只核对)
## 代码定位提示
- SKILL.md: "母本与分发" 节 (P1-6 三母本描述, 全节重写), "镜像管理" 节 base 层括注, "诞生 (birth)" 第四步 容器内路径契约行
- ops.md: "生命周期" 节命令模板中 `<f>_AGENTS.md:<agent 配置路径>/AGENTS.md:ro` 段
- agent-templates.md: "不替代三份公共 AGENTS.md 母本" 句
- 账本: DECISIONS.md 各决策条目的 实际影响 字段 (未实现 (待实施) → 实现摘要)
- 阅读顺序: EXECUTION.md 完成定义 → SKILL.md 三处 → ops.md/agent-templates.md → 账本
## TDD 切片
- 非代码特例, 无 TDD 切片. 验证 = 文件内容断言与人工通读 (见 验证入口).
## 验证入口
- `grep -n "三母本\|_AGENTS.md" workflow/use-sandbox-worktree/SKILL.md workflow/use-sandbox-worktree/reference/ops.md workflow/use-sandbox-worktree/reference/agent-templates.md` 输出中不再有三母本旧形态描述 (新形态描述在)
- 人工通读: SKILL.md 母本与分发节与 D013/D004/D016 描述一致, 无残留 "三份逐字同步" 纪律
- `uv run /home/bolo/.agents/skills/to-spec/check-ac.py ../PRODUCT.md` 与 `check-tech.py ../TECHNICAL.md` 仍退出码 0 (证明未误触 spec)
- 账本每条 实际影响 非空且与代码事实一致 (抽查 D004/D013/D018)
## 风险提示
- SKILL.md 是宿主侧 agent 的操作手册: 措辞错会误导后续 birth/resume 操作; 改完对照 DECISIONS.md D013/D004/D016 逐条核
- 回填 账本实际影响 时禁止顺手改决策内容 (账本变更规则)
## 停止条件
- 发现实现与账本冲突 (需改决策) 时停止, 回 deliberate
## 适合 AFK 的原因
- 全部改动点由 F008 清单与账本固定, 只做忠实描述与回填, 无决策
## 验收标准
- [ ] 三处联动文档与账本一致, 无旧形态残留; 账本实际影响全部回填; 机检保持 0
## Integration 特例
- 不适用 (非代码, 无共享分支)
## 被阻塞于
- ISSUE-01, ISSUE-03 (回填 实际影响 需实现完成; 文档描述最终形态)
