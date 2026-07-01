# 问题跟踪器:本地 Markdown

此仓库的执行契约和 issue 存放为 `docs/changes/` 中的 Markdown 文件. PRD 是可选团队汇报文档, 不属于执行流约定.

## 约定

- 每个功能(feature)一个目录:`docs/changes/<feature-slug>/`
- 执行契约是 `docs/changes/<feature-slug>/contract.md`
- 实施 issues 位于 `docs/changes/<feature-slug>/issues/<NN>-<slug>.md`,从 `01` 开始编号
- 每个 issue 在正文中包含 `## 执行(Execution)` 章节, 用 `- [ ] 已实现` 或 `- [x] 已实现` 记录是否已经执行
- issue 不使用 `Status:` 或等价状态行. issue 之间的依赖关系写在 `## 被阻塞于` 中, 这是静态拓扑信息, 不是执行状态
- 评论和对话历史追加到文件底部的 `## 评论(Comments)` 标题下. 读取和追加时兼容 `## Comments`,`## 评论`,`## 评论(Comments)`.

## 当某个技能说"发布到问题跟踪器(publish to the issue tracker)"时

在 `docs/changes/<feature-slug>/` 下创建新文件(必要时创建目录).

## 当某个技能说"获取相关工单(fetch the relevant ticket)"时

读取所引用路径处的文件.用户通常会直接传入路径或 issue 编号.
