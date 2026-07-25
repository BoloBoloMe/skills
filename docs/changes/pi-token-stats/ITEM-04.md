# 状态: 已关闭
# 类型: grilling
# 阻塞于: ~~ITEM-02~~

## 问题

设计插件 UI 交互: 命令形式, 输出格式, 历史会话浏览方式. 需要匹配 pi TUI 的能力边界.

## 决策

| # | 决策点 | 结论 |
|---|--------|------|
| 1 | 命令命名 | `/usage` |
| 2 | 交互入口 | 仅 `/usage` 命令, 不注册 LLM 工具, 不做状态栏/Widget/自动通知 |
| 3 | 输出载体 | overlay 弹窗 (`ctx.ui.custom({ overlay: true })`), 简洁卡片 |
| 4 | 默认作用域 | 仅当前会话, 无命令行参数, 不支持历史会话查询 |
| 5 | 卡片内容 | 完整明细, 每行显示 token 数 + 占比 (以 Total 为分母) |
| 6 | 界面语言 | 全中文标签 |
| 7 | 导出 | 不做, 仅 overlay 查看, 无剪贴板/JSON/文件导出 |

## 原型

`/tmp/pi-presentation-aot4se_6/usage-card-v2.html` — overlay 卡片终版原型.

## 卡片布局规范

```
📊 Token 统计 · 当前会话
─────────────────────────
输入
  系统提示      12,400   9.0%
  对话消息      63,960  46.2%
  附件              0   0.0%
缓存
  └ 缓存读取    42,300  30.5%
  └ 缓存写入     8,150   5.9%
输出
  模型输出      11,662   8.4%
─────────────────────────
合计           138,472   100%
─────────────────────────
缓存命中: 52%        8 轮对话
```

## 未决依赖

- ITEM-03 分类体系 — 当前分类 (系统提示/对话消息/附件/缓存读取/缓存写入/模型输出) 为占位骨架, ITEM-03 确定分类维度后替换具体行标签. 三大类 (输入/缓存/输出) 预期不变.

## 能力边界 (pi TUI)

- `ctx.ui.custom()` overlay 模式: 浮动层, 关闭后不持久化 (不写入 JSONL)
- `pi.registerCommand("usage", { handler })` — 注册 `/usage` 命令
- `ctx.sessionManager` 提供当前会话 entries, branch, leafId
- 组件: Text, Box, Container, Spacer, SelectList, SettingsList, BorderedLoader
- 无原生图表组件, 可 ASCII art / Canvas
