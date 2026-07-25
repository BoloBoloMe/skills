# ITEM-03: 分类体系设计 — 交接文档

## 路线图

**我的真实意图**: 为 pi 开发一个 token 统计插件, 按内容分类统计任意会话 (含历史) 的 token 使用.

**里程碑**:
1. Probe 绘制 Backlog, 识别 6 个 Item, 阻塞链: `ITEM-01/02 → ITEM-03/04 → ITEM-05 → ITEM-06`
2. ITEM-01 完成 — pi token usage 完整暴露面已调查, 数据源精度边界表已建立
3. ITEM-02 完成 — Claude Code `/cost` 分类维度和交互方式已参考
4. **当前位置**: ITEM-03 (分类体系设计) 解除阻塞, 待 grilling 盘问

**距离目的地**: 还剩 4 步 — 分类设计 (ITEM-03) → 原型 (ITEM-05) → 实现 (ITEM-06); ITEM-04 并行进行中.

## 必读推荐

1. `docs/changes/pi-token-stats/BACKLOG.md` — 项目全貌, 阻塞关系, 前沿, 未决迷雾
2. `docs/changes/pi-token-stats/ITEM-01-findings.md` — pi token usage 数据面完整分析 (精确/估算边界, Usage 结构, API 事件, 内置统计函数)
3. `docs/changes/pi-token-stats/ITEM-02-findings.md` — Claude Code `/cost` 分类维度和交互参考
4. `docs/changes/pi-token-stats/ITEM-03.md` — 本 Item 的问题描述
5. `~/.pi/agent/skills/grilling/SKILL.md` — grilling 盘问流程 (本 Item 类型)
6. `~/.pi/agent/skills/probe/SKILL.md` — Probe 遍历规则 (本次会话最多关一个非 research Item)

## 当前认知上下文

### ITEM-03 核心问题

基于数据可用性和参考对象, 设计 token 统计插件的分类体系和数据模型. 确定能实现哪些分类维度, 精度取舍, 估算策略.

### 数据面硬约束 (来自 ITEM-01)

- **唯一精确数据源**: `AssistantMessage.usage` = `{input, output, cacheRead, cacheWrite, cacheWrite1h?, reasoning?, totalTokens, cost}`
- **input 不拆分 by role** — API 不区分 system/user/tool 各自的 input tokens
- **reasoning** 是 output 的子集 (仅部分 provider 报告)
- **cacheWrite1h** 仅 Anthropic 报告
- **估算方式**: pi 内置 `chars/4` 启发式, 无 tokenizer
- **`before_provider_request`** 暴露完整 messages 数组 + system prompt 字符串, 可自行按 role 拆分估算 input tokens
- **实时统计可行**: 扩展监听 `message_end`/`turn_end` 事件, 从助理消息中提取 usage
- **历史统计可行**: 读取 session JSONL 文件, 遍历 `AssistantMessage` 条目累加 usage
- **CompactionEntry**: 有 `tokensBefore` (估算), 无精确值

### 参考分类 (来自 ITEM-02)

Claude Code 分类: System prompt / Tools / Messages (Conversation) / Attachments / Cache creation / Cache read / Output

### 需要盘问的关键决策

1. **分类粒度 — 精确 vs 估算的取舍**: 哪些分类从 usage 字段直接映射 (output, cacheRead/WRite, reasoning)? 哪些需要从 payload 估算 (system prompt, tools, user messages 各自的 input 占比)?
2. **是否引入 `before_provider_request` 实时拆分 input**: 成本 vs 收益? 只在历史统计做估算?
3. **Compaction 的处理**: `tokensBefore` 是估算值, 是否纳入统计? 如何呈现?
4. **跨 provider 差异**: Anthropic 的 `cacheWrite1h` 和 `reasoning`, OpenAI 的不同字段映射. 统一抽象 vs provider 特定展示?
5. **费用计算**: 用 pi 内置 cost (已含阶梯定价) vs 自己重算?
6. **分类命名**: 沿用 Claude Code 惯例还是自定?
