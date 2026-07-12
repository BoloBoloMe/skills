# Handoff: Superpowers Brainstorming 探索

## 概要

探索了 `obra/superpowers` 仓库的 `brainstorming` skill, 重点分析了其 visual-companion (视觉伴侣) 机制, 并评估了将其轻量化融入本地工作流 `grill-with-docs` 的方案.

## 现状

### 已完成

- `obra/superpowers` 仓库 (GitHub: https://github.com/obra/superpowers) 已探索, `skills/brainstorming/` 为分析目标
- `brainstorming` skill 目录结构: SKILL.md, visual-companion.md, spec-document-reviewer-prompt.md, scripts/ (server.cjs/start-server.sh/stop-server.sh/helper.js/frame-template.html)
- `visual-companion.md` 全文已翻译为中文 (未落盘, 仅在会话中展示)
- 本地工作流 skill 架构已确认: `orchestrate → grill-with-docs → to-product-spec → to-technical-spec → to-execution-spec → afk`
- 待改进的本地 skill 文件: `grill-with-docs/SKILL.md`, `to-product-spec/SKILL.md`, `to-technical-spec/SKILL.md` (路径相对于工作区根目录, 具体位置因机器而异)
- **brainstorming vs 本地工作流对比分析已完成**: 全维度优缺对比, 提炼出 3 个优先级的借鉴项

### 已分析但未落地

- **视觉伴侣轻量化方案已讨论但未实现**: 在 `grill-with-docs` 技术分支中, 按逐问题判断原则, 视觉问题 agent 写静态 HTML 模型文件到 `docs/changes/<feature>/visual/`, 你本地 `file://` 打开; 概念问题保持终端. 反馈全部走 chat, 不引入服务器/WebSocket/事件管道.
- **[P0] 「2-3 种方案 + 推荐」嵌入 grill-with-docs**: 在技术分支关键决策点 (架构方案/API 风格/数据模型) 先展开 2-3 种选项及 trade-offs, 给出推荐理由, 再关闭决策. 防止隧道效应. 低改动成本, 高收益.
- **[P1] 「Spec 自审 4 点清单」嵌入 to-product-spec / to-technical-spec**: 在生成 spec 后增加 4 步可执行检查 (占位符扫描/内部一致性/范围检查/歧义检查). 低改动成本.
- **[P2] 「这太简单不需要设计」反模式嵌入 grill-with-docs**: 拦截 agent 最常见的自我合理化借口. 一段文字即可.
- **未修改任何文件** — 方案停留在讨论阶段.

## 必读推荐

| 来源 | 必读理由 |
|---|---|
| https://github.com/obra/superpowers/blob/main/skills/brainstorming/visual-companion.md | superpowers 视觉伴侣完整原文, 含 CSS 类体系, 工作循环, 服务器启动参数等参考 |
| https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md | brainstorm skill 完整定义 (9-step checklist, HARD GATE 规则, 流程与 writing-plans 衔接) |
| 本地工作区: `workflow/grill-with-docs/SKILL.md` | 本地等价 skill, P0/P2 改动目标文件 |
| 本地工作区: `workflow/orchestrate/SKILL.md` | 本地工作流入口, 了解全局编排 |

## 路线图

**真实意图**: 调研 superpowers 的 brainstorming skill, 提取其 visual companion 的适用思想, 以最小侵入代价融入本地工作流, 使 `grill-with-docs` 阶段能处理视觉类设计问题 (架构图/UI 布局/流程对比), 而不局限于纯文字盘问.

**关键里程碑**:
1. ✅ 定位仓库 — 找到 `obra/superpowers`, 确认 `skills/brainstorming` 存在
2. ✅ 读取 SKILL.md — 理解 9-step checklist / HARD GATE / 与 writing-plans 衔接
3. ✅ 读取 visual-companion.md — 理解浏览器伴侣的工作循环和决策框架
4. ✅ 翻译 visual-companion.md — 全文汉化 (会话展示, 未落盘)
5. ✅ 分析本地工作流 — 确认 `grill-with-docs` 是视觉能力的最佳嫁接点
6. ✅ 提出改进方案 — 轻量化: 静态 HTML 模型 + file:// 浏览 + chat 反馈, 零基础设施
7. ✅ 全维度对比 — brainstorming vs 本地工作流优缺分析, 提炼 3 个优先级借鉴项
8. ❌ [P0] `grill-with-docs` 技术分支嵌入「2-3 方案 + 推荐」规则
9. ❌ [P1] `to-product-spec` / `to-technical-spec` 嵌入「Spec 自审 4 点清单」
10. ❌ [P2] `grill-with-docs` 嵌入「这太简单不需要设计」反模式
11. ❌ 视觉伴侣静态 HTML 方案落地

**距离终点**: 方案已清晰但未编码. 下一步是决定是否落地到 `grill-with-docs`.

## 补充备注

- visual-companion 中文翻译在会话中, 未保存文件. 如需落盘可从 GitHub raw URL 获取原文翻译: https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/skills/brainstorming/visual-companion.md
- 会话中已完成的中文翻译可通过 `translate-a-skill` skill 的流程重新生成.
