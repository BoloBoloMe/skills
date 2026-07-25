# ITEM-01: pi token usage 实现细节调查

## 1. `getContextUsage()` 完整实现

**文件:** `pi-coding-agent/dist/core/agent-session.js` (lines 2515-2551)

逻辑流程:
1. 取 `model.contextWindow`, 若 <= 0 返回 `undefined`
2. 找最新 compaction entry (`getLatestCompactionEntry`)
3. 若有 compaction, 向后扫描确认存在 compaction 之后的有效 assistant usage (stopReason != aborted/error, contextTokens > 0)
   - 若不存在, 返回 `{ tokens: null, contextWindow, percent: null }` (表示压缩后未知)
4. 调用 `estimateContextTokens(this.messages)` 估算
5. 计算 `percent = (tokens / contextWindow) * 100`

返回值 `ContextUsage`:
```ts
{ tokens: number | null, contextWindow: number, percent: number | null }
```

---

## 2. `estimateContextTokens()` 实现

**文件:** `pi-coding-agent/dist/core/compaction/compaction.js` (lines 108-126)

算法:
1. 从消息列表末尾反向查找最后一个有效 assistant message 的 usage (`getLastAssistantUsageInfo`)
2. 若找到: `usageTokens = calculateContextTokens(usage)` (精确的 API 返回), 然后对 usage 之后的消息逐条调用 `estimateTokens()` (估算)
3. 若未找到: 对所有消息逐条调用 `estimateTokens()` (纯估算)
4. 返回 `{ tokens, usageTokens, trailingTokens, lastUsageIndex }`

**`calculateContextTokens(usage)`** (line 63):
```js
return usage.totalTokens || usage.input + usage.output + usage.cacheRead + usage.cacheWrite;
```
优先取 API 的 `totalTokens`, 若无则从分量求和. 这是**精确值** (来自 API 响应).

**`estimateTokens(message)`** (lines 165-204): **chars/4 启发式估算**
```js
function estimateTokens(message) {
    let chars = 0;
    switch (message.role) {
        case "user":
            chars = estimateTextAndImageContentChars(message.content);
            return Math.ceil(chars / 4);
        case "assistant":
            // 遍历 content blocks: text/thinking/toolCall
            // text: block.text.length
            // thinking: block.thinking.length
            // toolCall: block.name.length + JSON.stringify(block.arguments).length
            return Math.ceil(chars / 4);
        case "toolResult":
            chars = estimateTextAndImageContentChars(message.content);
            return Math.ceil(chars / 4);
        case "bashExecution":
            chars = message.command.length + message.output.length;
            return Math.ceil(chars / 4);
        case "branchSummary":
        case "compactionSummary":
            chars = message.summary.length;
            return Math.ceil(chars / 4);
    }
    return 0;
}
```
图片内容按 `ESTIMATED_IMAGE_CHARS = 4800` chars 估算 (line 148).

---

## 3. `before_provider_request` 事件

**类型定义:** `pi-coding-agent/dist/core/extensions/types.d.ts` (lines 493-496)
```ts
export interface BeforeProviderRequestEvent {
    type: "before_provider_request";
    payload: unknown;
}
```

**payload 结构:** `unknown` 类型, 是 provider 层的 HTTP 请求体, 结构取决于底层 API (Anthropic Messages / OpenAI Chat Completions 格式). 在 `sdk.js` (lines 198-201) 中通过 `onPayload` 回调传入, 在 `runner.js` (lines 735-754) 中发射给扩展. 扩展可通过 handler 返回修改后的 payload.

典型 payload (Anthropic):
```json
{ "model": "...", "messages": [...], "system": "...", "max_tokens": ..., "stream": true }
```

OpenAI 格式类似 `{ "model": "...", "messages": [...], "stream": true, "stream_options": { "include_usage": true } }`

**注意:** 此事件**不直接暴露** token usage 数据, 只能通过 payload content 间接获取.

---

## 4. `after_provider_response` 事件

**类型定义:** `pi-coding-agent/dist/core/extensions/types.d.ts` (lines 507-512)
```ts
export interface AfterProviderResponseEvent {
    type: "after_provider_response";
    status: number;
    headers: Record<string, string>;
}
```

**headers 中的 token 相关字段:**
- 不含 token usage 数据. usage 在 body/stream 中, 不在 HTTP headers
- headers 包含: 认证、content-type、ratelimit 等元信息
- 对于 AI Gateway (Cloudflare/Vercel), headers 中可能有 `x-ratelimit-*` 头

扩展通过此事件可以:
- 记录 HTTP 状态码
- 注入/读取自定义 header (tracing、session-id 等)
- 但**无法直接获取** token usage (需等 streaming 结束后的 assistant message)

---

## 5. `getSystemPromptOptions()` 返回值

**实现:** `agent-session.js` (line 1926)
```js
getSystemPromptOptions: () => this._baseSystemPromptOptions
```

**填充位置:** `agent-session.js` (lines 735-744)
```js
this._baseSystemPromptOptions = {
    cwd: this._cwd,
    skills: loadedSkills,
    contextFiles: loadedContextFiles,
    customPrompt: loaderSystemPrompt,
    appendSystemPrompt,
    selectedTools: validToolNames,
    toolSnippets,
    promptGuidelines,
};
```

**类型** (`pi-coding-agent/dist/core/system-prompt.d.ts`):
```ts
export interface BuildSystemPromptOptions {
    customPrompt?: string;
    selectedTools?: string[];
    toolSnippets?: Record<string, string>;
    promptGuidelines?: string[];
    appendSystemPrompt?: string;
    cwd: string;
    contextFiles?: Array<{ path: string; content: string }>;
    skills?: Skill[];
}
```

**用途:** 扩展可通过 `before_agent_start` 事件的 `systemPromptOptions` 字段获取这些结构化上下文信息, 无需重新扫描文件系统.

---

## 6. 内置 tokenizer

**结论: 无内置通用 tokenizer.** pi 不使用 tiktoken/cl100k_base 等库.

唯一的 token 计数方式:
- **API 精确值:** 从 provider 响应解析的 `Usage` 对象 (`types.d.ts` lines 252-264 in pi-ai)
- **估算方法:** `chars / 4` 启发式 (`compaction.js` `estimateTokens()`)
- **Google Gemini:** `@google/genai` 包附带 SentencePiece tokenizer (`node_modules/@google/genai/dist/tokenizer/`), 但仅供 Gemini API 内部使用, pi 不主动调用

---

## 7. Usage 数据来源 (API 精确值)

**类型** (`pi-ai/dist/types.d.ts` lines 252-271):
```ts
export interface Usage {
    input: number;
    output: number;
    cacheRead: number;
    cacheWrite: number;
    cacheWrite1h?: number;   // Anthropic 特有: cache_creation.ephemeral_1h_input_tokens
    reasoning?: number;      // 思考/推理 tokens (output 的子集)
    totalTokens: number;
    cost: { input: number; output: number; cacheRead: number; cacheWrite: number; total: number };
}
```

**Anthropic 解析** (`pi-ai/dist/api/anthropic-messages.js`):
- `message_start` 事件: 从 `event.message.usage` 取 `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `cache_creation.ephemeral_1h_input_tokens`
- `message_delta` 事件: 更新 usage, 补充 `output_tokens_details.thinking_tokens` (reasoning tokens)
- `totalTokens` 由分量求和计算 (Anthropic 不直接提供)

**OpenAI 解析** (`pi-ai/dist/api/openai-completions.js` lines 950-975):
- 从 `chunk.usage` 或 `choice.usage` (Moonshot fallback) 获取
- 字段映射: `prompt_tokens → input`, `completion_tokens → output`, `prompt_tokens_details.cached_tokens → cacheRead`, `prompt_tokens_details.cache_write_tokens → cacheWrite`
- `stream_options: { include_usage: true }` 请求确保流式返回 usage (line 463)
- `reasoning_tokens` 来自 `completion_tokens_details.reasoning_tokens`

**`calculateCost()`** (`pi-ai/dist/models.js` lines 371-389):
- 根据 model cost tier (volume-based 阶梯) 计算
- Anthropic cache write 特殊处理: 1h 缓存 2x base input, 5min 缓存按 cacheWrite rate

---

## 8. 压缩条目 (CompactionEntry) 的 token 信息

**类型** (`session-manager.d.ts` lines 36-45):
```ts
export interface CompactionEntry<T = unknown> {
    type: "compaction";
    summary: string;       // LLM 生成的压缩摘要
    firstKeptEntryId: string;
    tokensBefore: number;  // 压缩前的估算 context tokens
    details?: T;           // 扩展自定义数据
    fromHook?: boolean;    // 是否来自扩展 hook
    uuid: string;          // 继承自 SessionEntryBase
    parentUuid: string;
    timestamp: string;
}
```

- `tokensBefore` 是 `estimateContextTokens()` 的结果 (精确 usage + 估算 trailing)
- `BranchSummaryEntry` (lines 46-51) 只有 `summary` 和 `fromId`, **无 token 信息**
- `CustomEntry` (lines 65-68) 有 `customType` 和 `data`, **无 token 信息**

---

## 9. Session Stats 的 token 聚合

**`getSessionStats()`** (`agent-session.js` lines 2460-2512):
- 遍历所有 session entries, 从 assistant messages 的 `usage` 字段累加 `input`, `output`, `cacheRead`, `cacheWrite`
- 累加 `usage.cost.total` 得到总费用
- 这些值全部来自 API 返回的**精确 usage**, 不包含估算

---

## 数据源精度总结

| 数据源 | 精度 | 说明 |
|--------|------|------|
| assistant message `usage` | **精确** | API 返回的实际 token 计数 |
| `getContextUsage().tokens` | **混合** | 最后 assistant usage (精确) + trailing 消息 estimate (chars/4 估算) |
| CompactionEntry `tokensBefore` | **混合** | 同 `estimateContextTokens()`, 精确 + 估算 |
| `estimateTokens()` | **估算** | chars/4 启发式, 对图片用 4800 chars 常数 |
| `getSessionStats().tokens` | **精确** | 仅从 assistant usage 累加, 不含估算 |
| `before_provider_request.payload` | N/A | 不含 usage, 只有请求体 |
| `after_provider_response` | N/A | 只有 HTTP status + headers, 不含 usage |
| `getSystemPromptOptions()` | N/A | 不含任何 token 信息 |
