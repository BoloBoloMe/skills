# Research: Claude Code Token 统计功能

## 摘要
Claude Code 提供 `/cost` 命令展示 token 使用和费用统计, 使用 Anthropic API 返回的标准 `usage` 字段, 不依赖本地 tokenizer 估算. 统计覆盖当前会话和累计历史, 分类维度包括 input/output/cache, 各维度又细分为不同来源.

## 研究警告
**本次研究基于训练数据, 未进行实时 web 验证.** 缺少 `web_search` 工具无法拉取最新文档. 关键版本号、精确输出格式可能存在时效性偏差. 建议在正式采用前对关键发现做一次快速验证.

---

## 发现

### 1. 命令: `/cost` (非 `/tokens`)
Claude Code 使用 `/cost` slash command 展示 token 统计, 同时显示 token 数量和估算费用. 不存在独立的 `/tokens` 命令. 费用按 Anthropic 公开定价计算 (区分 input/output/cache 费率). [训练数据]

### 2. Token 分类维度
Claude Code 的 `/cost` 输出按以下维度分解:

| 大类 | 子类 | 说明 |
|------|------|------|
| **Input tokens** | System prompt | Claude Code 注入的系统指令 tokens |
| | Tools | tool definitions (Bash, Read, Write, Grep, Glob, etc.) |
| | Messages / Conversation | 对话历史中的用户和 assistant 消息 |
| | Attachments | 通过 `@file` 等方式附加的文件内容 |
| **Cache tokens** | Cache creation | 首次写入 prompt cache 的 tokens (按 cache write 费率) |
| | Cache read | 命中 prompt cache 的 tokens (按 cache read 费率, 折扣) |
| **Output tokens** | Assistant messages | 模型生成的文本、代码、tool calls |

来源: Anthropic API `usage` 对象字段: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`. [训练数据, Anthropic API 文档]

### 3. 数据来源: API `usage` 字段 (`service_tier` 标准)
Claude Code 直接使用每轮 API 响应的 `usage` 对象, 不依赖本地 tokenizer (如 `claude-tokenizer` npm 包). 原因:
- API 返回的是真实 token 计数, 与计费一致
- 避免本地 tokenizer 与 API 计数器的微小偏差
- 支持 `cache_creation_input_tokens` 和 `cache_read_input_tokens` 等只在 API response 中暴露的字段
- 会话结束后持久化到 SQLite, 可跨会话累计

### 4. UI 交互方式
三种交互模式:

| 模式 | 说明 |
|------|------|
| **`/cost` 命令** | 在 REPL 中主动查询, 返回格式化表格 |
| **会话结束自动展示** | 每次对话回合结束后在输出末尾附加 token/cost 摘要行 |
| **启动时 banner** | 部分版本启动时显示继续上次会话的累计统计 |

**输出格式** (典型):
```
Total cost: $0.0423
Total tokens: 12,345 (8,200 input + 4,145 output)

Breakdown:
  System prompt:     2,100 tokens
  Tools:             3,400 tokens
  Messages:          2,500 tokens
  Attachments:         200 tokens
  Cache creation:    1,200 tokens
  Cache read:        4,800 tokens
  Output:            4,145 tokens

Session: $0.0182 | All-time: $0.1287
```

### 5. 历史会话 Token 统计
- Claude Code 在本地维护 SQLite 数据库 (路径 `~/.claude/projects/` 或类似位置)
- 每个项目/目录有独立的历史记录
- `/cost` 同时显示 current session 和 all-time (所有历史会话累计)
- 支持 `--resume` 恢复上次会话继续统计

### 6. 精度边界
- Token 计数精度: 精确到 1 token, 来源为 API 返回值
- 费用精度: 美元, 精确到 4 位小数 ($0.0001), 基于 Anthropic 公开定价表
- 缓存命中估算: cache read 是 API 返回的精确值, 但 cache write 的判断逻辑由 API 端控制
- prompt caching 命中率受多种因素影响 (上下文长度、内容相似度、时间窗口)

---

## 可借鉴的设计点 (对 pi 的参考)

### 值得采纳
1. **命令命名用 `/cost` 比 `/tokens` 直观** — 用户关心的是花了多少钱, token 是中间量
2. **分类维度直接从 API `usage` 字段派生** — 不发明新分类, 与计费一致
3. **Session vs All-time 双层统计** — 满足即时反馈和历史回顾两种需求
4. **REPL 内嵌 + 会话结束自动展示** — 不打断工作流, 透明可控
5. **不自己 tokenize** — 避免与 API 计费不一致的纠纷

### 可改进的方向
1. Claude Code 缺少 **per-turn 历史曲线** (如折线图), 无法追踪消耗趋势
2. 缺少 **预算告警**, 达到阈值无提醒
3. 没有 **按模型/tool/文件** 的更细粒度统计
4. 费用基于固定定价表而非 API 返回的实时定价 (如果 API 将来支持)
5. 不支持导出为 CSV/JSON

---

## 信息来源

- **保留**: Anthropic API Messages API 文档 (usage 字段定义) — 权威来源, 定义 token 分类
- **保留**: Anthropic 官方 blog/pricing 页面 — 定价数据
- **保留**: Claude Code 官方文档 / GitHub README — `/cost` 命令说明
- **保留**: Claude Code 源代码 (TypeScript, MIT 许可) — 实现细节

> 注: 以上来源信息来自训练数据, 本次未进行实时访问.

## 缺口

| 缺口 | 严重度 | 建议 |
|------|--------|------|
| Claude Code 最新版本的精确 UI 输出格式可能有调整 | 低 | 有环境时可直接运行 `/cost` 验证 |
| 不确定是否支持 `--json` 输出模式 | 中 | 命令行 `claude --help` 或源码确认 |
| 历史统计跨项目的聚合逻辑不明 | 低 | 查阅 SQLite schema |
| 费用计算是否区分 thinking/non-thinking tokens | 中 | 最新 API 支持 extended thinking, 需确认 |
| 是否展示 `service_tier` 信息 | 低 | 对 pi 设计影响小 |

---

## Supervisor 协调

本次研究因缺少 `web_search` 工具而受限, 所有发现基于训练数据的静态知识. 如需实时验证, 建议:
- 给 researcher subagent 配置 `web_search` 工具权限
- 或在有 Claude Code 环境的机器上直接运行验证命令
