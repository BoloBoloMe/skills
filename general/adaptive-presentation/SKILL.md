---
name: adaptive-presentation
description: 按信息形状选择回复形式.
disable-model-invocation: true
---

本 skill 是展示层, 不改变调用方工作流, 决策顺序或确认规则.

## 1. 状态

从当前会话上下文读取:

```text
auto_visualization: enabled | disabled
presentation_session_dir: absolute path | absent
```

- 新会话或状态缺失时默认 `enabled`.
- compaction 后摘要未保留禁用状态时按 `enabled`.
- 状态只存在于会话上下文.

### 状态转换

- 我说 "禁用自动可视化" → 将 `auto_visualization` 设为 `disabled`, 不关闭浏览器.
- 我说 "启用自动可视化" 或 "恢复自动可视化" → 将 `auto_visualization` 设为 `enabled`.
- `disabled` 期间我说 "可视化这个" 或 "展示为 HTML" → 仅执行该次展示, 不改变 `auto_visualization`.

完成标准: `auto_visualization` 值已按我的指令更新, 或已知当前值.

## 2. 路由

按信息形状选择形式:

| 形状 | 形式 |
|------|------|
| 结论, 解释, 问题, 少量选项 | chat 文字或列表 |
| 逐列对齐的多项比较, 参数, 结构化事实 | Markdown 表格 |
| 空间布局, 流程, 层级, 拓扑, 状态关系, 时间关系, UI mockup, 视觉对比 | HTML |
| 我明确要求可视化但未指定载体 | HTML |
| 我明确指定载体 | 使用该载体, 禁止 Mermaid |

不因主题涉及 UI 或架构就生成 HTML. 判断标准: 看见关系是否明显比阅读描述更容易理解. 信息足以判断时自行路由, 不新增确认轮次.

### 禁用时

- `disabled` 且无显式可视化请求 → 不进入 HTML 分支, 信息留在 chat 或 Markdown 表格.
- 我显式要求可视化 → 无论禁用状态都执行该次展示.
- 单次可视化不改变禁用状态, 展示完成后仍为 `disabled`.
- 禁用不关闭已打开的展示浏览器.

### 启用时

按平衡阈值: HTML 大概率更易理解才进入 HTML 分支. 普通解释, 文本选项, 逐列比较留在 chat 或表格.
完成标准: 路由决策仅依赖信息形状或我的显式要求, 不依赖主题标签.

## 3. HTML 分支

选择 chat/列表/表格时, 直接展示并返回原工作流.
选择 HTML 时, 将 `scripts/browser_session.py` 相对本 skill 目录解析为绝对路径, 记为 `<helper>`. 不从调用方工作目录查找脚本.

1. 完整读取 [HTML-GUIDE.md](HTML-GUIDE.md), 按其中规则创建和交付临时页面.
2. `presentation_session_dir` 缺失或目录不存在时, 用 `tempfile.mkdtemp(prefix="pi-presentation-")` 创建.
3. 过滤凭据, 最小化原始日志/业务数据, 写入自包含 HTML 含 `window.__PRESENTATION_STATE__`.
4. 语义化不重复文件名, 新版本不覆盖旧版本.
5. `python <helper> open <session-dir> <html-file>`.
6. 成功时在 chat 给出: 本地绝对路径链接, 一句话说明展示内容, 待我观察/回答的具体问题. 关键结论和待确认决策仍须在 chat 中说明.
7. 失败时提供本地绝对路径链接和 chat 摘要, 继续原工作流.

### 读取页面反馈

收到我的回复后, 只有页面含交互且 DOM 状态对当前反馈有帮助时才调用:

```text
python <helper> state <session-dir>
```

- 合并 DOM 状态和 chat; 冲突时以 chat 为准.
- 最终决策仍按调用方工作流在 chat 中确认.
- 浏览器已关闭时 state 返回 `browser_not_running`, 不重启.

### 检查浏览器存活

```text
python <helper> status <session-dir>
```

- `alive: false` 时不触发浏览器启动.
- 后续视觉展示调用 `open`, access-web 自愈路径清理旧 metadata 并重新启动.

完成标准: 信息已展示; HTML 路径可打开; chat 中保留了目的摘要和待反馈内容.

## 4. 返回

展示不构成新的审批阶段. 处理我的反馈后回到调用前的工作流位置, 沿原有提问, 决策和确认规则继续.
完成标准: 后续动作由原工作流或我的最新指示决定, 本 skill 未改变其状态机.