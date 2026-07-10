# Spec 工作区: 本地 Markdown

每个 feature 的 Spec Pack, decisions, issues 和 AFK 证据存放在 `docs/changes/`. 这些文件供 AI 使用; 影响产品, API, 架构, 范围, 风险或验证的决定必须在盘问会话中向我解释并确认, 不以让我阅读文件作为审批步骤.

## 约定

- 每个 feature 一个目录: `docs/changes/<feature-slug>/`.
- Product Spec: `PRODUCT.md`.
- Technical Spec: `TECHNICAL.md`.
- Execution Spec: `EXECUTION.md`.
- 功能决策账本: `DECISIONS.md` (有决策时).
- issues: `issues/ISSUE-<NN>-<slug>.md`, 从 `ISSUE-01` 连续编号.
- AFK 运行产物: `afk-running/`.
- 每个 issue 包含 `## 执行(Execution)`, 用 `- [ ] 已实现` 或 `- [x] 已实现` 记录结果.
- issue 不使用 `Status:`. 静态依赖写在 `## 被阻塞于`.
- 评论固定追加到文件底部的 `## 评论(Comments)`.

## 发布到议题跟踪器

在 `docs/changes/<feature-slug>/` 下创建对应文件或目录.

## 获取相关工单

读取引用路径的完整正文和评论. issue key 必须唯一定位一个 `issues/ISSUE-*.md` 文件.
