# 问题跟踪器：本地 Markdown

此仓库的 issue 和 PRD 存放为 `docs/changes/` 中的 Markdown 文件。

## 约定

- 每个功能（feature）一个目录：`docs/changes/<feature-slug>/`
- PRD 是 `docs/changes/<feature-slug>/PRD.md`
- 实施 issues 位于 `docs/changes/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 开始编号
- Triage 状态记录为每个 issue 文件顶部附近的一行 `Status:`（角色字符串见 `triage-labels.md`）
- 评论（Comments）和对话历史追加到文件底部的 `## Comments` 标题下

## 当某个技能说“发布到问题跟踪器（publish to the issue tracker）”时

在 `docs/changes/<feature-slug>/` 下创建新文件（必要时创建目录）。

## 当某个技能说“获取相关工单（fetch the relevant ticket）”时

读取所引用路径处的文件。用户通常会直接传入路径或 issue 编号。
