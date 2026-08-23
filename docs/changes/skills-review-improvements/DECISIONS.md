# 决策账本: skills 仓库审查改进

> 仅供 AI 使用. 改变决策内容/状态/约束性前须取得用户确认.

## 决策

### D001 测试隔离修复为最高优先级

- 状态: 当前有效
- 约束性: 必须遵守
- 决策: 修复 `tests/test_sync_to_pi.py` 的 `Path.home()` 未隔离缺陷 (清空真实 `~/.agents/skills`), 并修正断言位置 (红态与假阳性一并处理).
- 理由: 数据破坏级缺陷, 且当前 CI 红态; 不修则任何测试运行都有风险.
- 依赖事实: F001, F002
- 预计影响: `tests/test_sync_to_pi.py`, 不涉及 sync-to-pi.py 主逻辑.
- 需要调整: 无 (主逻辑无 bug, 是测试隔离问题).

### D002 文档悬空引用一次性清理

- 状态: 当前有效 (其中 docs/handoff 相关部分已被 D007 覆盖)
- 约束性: 可调整
- 决策: 对 docs/changes 与 docs/handoff 中引用已删/已改名 skill (propose, adaptive-presentation) 与旧路径 (`~/.pi/agent/skills/`, `general/adaptive-presentation/`) 的文本, 更正为目标实体; 历史提案类文档附当时命名备注即可.
- 理由: 权威文档 (DECISIONS) 指错方向成本高于一次性文本修正.
- 依赖事实: F003
- 预计影响: `docs/changes/上下文管理优化/DECISIONS.md`, `docs/changes/browser-agent-session-contract/PROPOSAL.md`, `docs/changes/less-is-more-palette/conclusion.md`, `docs/handoff/*.md`.

### D003 deprecated/ 补归档元数据

- 状态: 已被 D007 覆盖 (deprecated/ 整体删除, 补元数据不再需要)
- 约束性: 可调整
- 决策: deprecated/ 下新增 README, 每项一行记录归档日期/原因/替代去向; 不追溯改归档项正文.
- 理由: 归档价值在于未来不复蹈, 无元数据则归档等于删除但留尸.
- 预计影响: `deprecated/README.md` 新建.

### D004 运行时前置声明

- 状态: 当前有效
- 约束性: 可调整
- 决策: access-web/present 补充"首次使用需 uv sync + playwright install chromium"声明; sync 流程补首次使用提示; browser_agent 契约化 (get_session/evaluate_js 公开导出) 按 browser-agent-session-contract 提案推进.
- 理由: 干净环境首次调用必然红且无指引; 契约化已存在既成提案.
- 预计影响: `general/access-web/SKILL.md`, `general/access-web/browse/browse.md`, `general/present/SKILL.md`, `sync-to-pi.py` (提示), `browser_agent/__init__.py` (契约化).

### D005 待决: 结构与术语对齐

- 状态: 当前有效
- 约束性: 可调整
- 决策: README 目标结构与 docs/changes 实际形态对齐二选一 (固化双形态说明 或 收紧单一结构); probe 存量档案按 ADR-0004 补"已关闭 workstream 不追溯"注解.
- 理由: 消除新会话无所适从与新旧术语并存的困惑; 具体形态取舍需用户拍板.
- 待确认: 保留双形态 (spec 流 + probe 流) 还是统一.

### D006 待决: 路由 skill 与契约测试

- 状态: 当前有效
- 约束性: 可调整
- 决策: 新建轻量路由 skill (纯指针, 不承载编排) 或 README 技能地图; 全量 skill 契约机械检查固化为测试.
- 理由: 19 个用户调用 skill 认知负担高, 契约无机械守护; 两项均属增强, 视资源排期.
- 待确认: 路由 skill 是否需要, 还是维持"用户点名"现状.

### D007 用户裁定: 删除 docs/handoff/ 与 deprecated/

- 状态: 已执行 (2026-08-23)
- 约束性: 必须遵守
- 决策: 删除 `docs/handoff/` (2 个历史交接单) 与 `deprecated/` (10 个归档项: code-review-with-me, explore-repo, extensions, hitl, orchestrate, prompts, springboot-hcurl-generator, telegraphic-style, write-a-skill, zoom-out, 共 59 个文件), 两目录合计 61 个 git 跟踪文件 (含 extensions/resolve-skill.ts). handoff/receive-handoff skill 默认落盘/读取位置迁移至 `docs/changes/handoff/`; README 目录树移除 deprecated 行.
- 理由: 历史交接单与归档残留只制造引用噪音; handoff 机制保留并归入 docs/changes/ 结构.
- 覆盖: 替代 D002 中 docs/handoff 相关部分与 D003 (deprecated 补元数据不再需要).
- 预计影响: 已全部落地; git 历史可回溯.

## 事实

### F001 sync-to-pi.py 清空目标是硬编码真实目录

- 状态: 当前有效
- 来源: `sync-to-pi.py` L367 `skills_dir = Path.home() / ".agents" / "skills"`
- 内容: main() 中清空操作作用于该真实目录; 测试仅 mock `detect_pi_dir`, 未隔离 Path.home.

### F002 运行 pytest 已清空真实 ~/.agents/skills

- 状态: 已恢复 (2026-08-23)
- 来源: 本审查运行 `uv run python -m pytest tests/ -q` (2026-08-23); 运行后 `ls ~/.agents/skills` 为 0 项
- 内容: test_clear_only_runs_after_final_confirmation 的确认输入 `"y"` 触发 execute_plan 清空真实目录. 同日已重跑 `uv run python sync-to-pi.py` 恢复 (33 项操作成功, 29 个 skills). 测试修复见 D001.

### F003 仓库命名沿革

- 状态: 当前有效
- 来源: git 提交 f22847e (adaptive-presentation -> present), 9c915a2 (orchestrate 过时), propose 已删除
- 内容: 现存文档仍引用两处旧名: `workflow/propose/SKILL.md`, `general/adaptive-presentation/...`; 现行替代为 `workflow/deliberate/SKILL.md` 与 `general/present/`.

### F004 skills 安装位置约定

- 状态: 当前有效
- 来源: `sync-to-pi.py` L367, `pi/AGENTS.md` (读 `~/.agents/skills/<skill-name>/SKILL.md`)
- 内容: 实际安装目录 `~/.agents/skills/`; `docs/handoff/*.md` 写的是旧路径 `~/.pi/agent/skills/`.

### F005 测试覆盖现状

- 状态: 当前有效
- 来源: 仓库文件清单, `general/present/tests/test_skill_contract.py`
- 内容: 30 个 skill 仅 present 有 skill 契约测试; access-web 有完整代码测试但被 sync 忽略; 无 CI 配置与统一测试任务入口.

### F006 docs/handoff 与 deprecated 已删除

- 状态: 当前有效
- 来源: git rm (2026-08-23)
- 内容: `docs/handoff/` 与 `deprecated/` 已删除; 引用点已更新: README 目录树, `general/handoff/SKILL.md` 与 `general/receive-handoff/SKILL.md` 的默认落盘/读取位改为 `docs/changes/handoff/`; 新增 `docs/changes/handoff/README.md` 占位说明. ADR-0004 对已删单文件的提及属历史叙述, 不构成断链, 未改动.