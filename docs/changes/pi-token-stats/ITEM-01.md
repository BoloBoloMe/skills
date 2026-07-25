# 状态: 已关闭
# 类型: research
# 阻塞于: 无

## 问题

pi 中 token usage 数据的完整暴露面是什么? 确定哪些维度可以精确获取, 哪些只能估算.

### 考察点

1. **assistant message usage 字段**: 结构是 `{input, output, cacheRead, cacheWrite, totalTokens, cost}` — input 是整个请求的 input tokens, 不拆分 role. 确认这是唯一精确数据源.

2. **ctx.getContextUsage()**: 返回什么结构? 是估算还是精确值? 和 usage 字段的关系?

3. **before_provider_request payload**: 能否在请求发出前拿到完整 messages 数组? 如果能, 可以自己估算 system/user/assistant/tool 各部分的 token 占比. 用 tokenizer 还是字符比例估算?

4. **after_provider_response**: response headers 中是否有更细的 token breakdown? (如 Anthropic 的 `anthropic-*` headers)

5. **provider 特定 token 信息**: 不同 provider (Anthropic, OpenAI) 返回的 usage 是否有额外字段? 是否需要区分 provider?

6. **会话文件中的非 message 条目**: compaction, branch_summary, model_change 等条目是否携带 token 信息?

7. **缓存 token (cacheRead/cacheWrite)**: 这些 token 算不算入统计? 如何呈现?

### 输出

分析文件 `ITEM-01-findings.md`, 覆盖以上所有考察点, 给出精确/估算边界表.
