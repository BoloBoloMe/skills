# 状态: 已关闭
# 类型: research
# 阻塞于: 无

## 问题

Claude Code (claude.ai 的 CLI 工具) 的 token 统计功能是怎么做的? 提取可参考的分类维度和交互方式.

### 考察点

1. **分类维度**: Claude Code 把 token 分成哪些类别? (系统提示词, 工具定义, 对话历史, 附件, skill 等)

2. **数据来源**: Claude Code 用的是 API 返回的 usage, 还是自己估算? 用的是 Anthropic 特有的 token breakdown API 吗?

3. **UI 交互**: 是命令 (`/tokens`), 持续状态栏显示, 还是会话结束后展示? 输出格式是什么?

4. **历史会话**: Claude Code 支持统计历史会话的 token 吗? 如何实现?

5. **可视化**: 有没有图表或分类占比展示? 是纯文本还是 TUI 组件?

6. **精度说明**: Claude Code 如何向用户说明分类统计的精度边界?

### 输出

分析文件 `ITEM-02-findings.md`, 覆盖以上考察点, 附截图或引用.
