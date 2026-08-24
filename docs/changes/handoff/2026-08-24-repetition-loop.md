# 无限重复故障 (中转站 reasoning 退化)

## 现象

pi 会话中, assistant 的 thinking 流正常显示一段后, 陷入 `　<br>` 无限重复, 直到用户 Esc 中断. 重复单元 = U+3000 全角空格 + 字面 `<br>` (4 ASCII 字符). 跨模型 (glm-5.3/5.2, qwen3.8-max, deepseek-v4-flash) 在同一中转站均复现, 重复单元完全相同.

## 根因

**中转站 `ai-work.changzhi.top` 是共同根因.** 三条依据:

1. **pi 已排除**: 流处理 `block.thinking += delta` 原样追加 reasoning_content, 无改写; pi dist 无 `<br>` 字面量 (仅 export-html marked vendor, 无关); 3 个扩展不碰 thinking; zai 格式仅设 `clear_thinking:false`, 不产生 `<br>`.
2. **`<br>` 非模型自然输出**: HTML 标签, 模型不会自发当换行. 唯一合理来源是中转站对 reasoning 做 HTML 化 (换行→`<br>`, 为其 web 前端).
3. **跨模型重复单元完全相同**: 各模型独立退化则单元应各异 (词表/训练数据不同). 都重复 `　<br>` → 中转站对所有 reasoning 施加同一套处理, 在某流式边界统一产生或重放该单元.

用户确认: 不同模型在该供应商都有相同问题.

## 具体机制 (两种, 未定论)

- **(a) 流式重放 bug**: 模型停止后中转站未正确关闭 SSE, 反复重发最后 chunk (恰好是 HTML 化后的 `　<br>` 分隔/填充).
- **(b) HTML 化放大退化**: 中转站 `\n`→`<br>` 后, 模型在思考边界退化成空行循环, 被中转站统一放大成 `　<br>` 循环.

两者都以中转站为必要条件. 决定性观察: 正常部分换行是 `\n` (未被转), 重复段是字面 `　<br>` —— 若中转站全局 `\n`→`<br>`, 正常部分也该变, 但没有. 故 `<br>` 是流里本来就有的原始字节, 非渲染产物.

## 取证

- **会话 jsonl**: `~/.pi/agent/sessions/--home-bolo-Workspace-skills--/2026-08-24T05-15-22-607Z_01a03231-d86f-780f-99e0-49dc7e346772.jsonl` index 11
  - model `glm-5.3`, provider `ai-work-zai`, stopReason `aborted`, usage 全 0
  - `content[0].thinking` len=7716, 含 1459 个 `<br>`
  - 结构: `<thinking>\n正常英文思考(~400B)…\n</thinking>\n中文正文"查同步位置: "` + 1460 × `　<br>`
- **pi 流处理源码**: pi-ai 包 `dist/api/openai-completions.js` 第 366–380 行 (reasoning_content delta 原样追加到 thinking block)
- **展示页面 (诊断可视化, 临时)**: `file:///tmp/pi-present-repetition/2026-08-24-repetition-loop-diagnosis.html` — 五节诊断 + 责任链图. 临时目录, 可能被系统清理.

## 配置事实

- 所有 provider 走同一中转站 `https://ai-work.changzhi.top/v1`, api `openai-completions`, key 环境变量 `$CHANG_ZHI_AI_WORK` (已遮蔽, 不含值).
- pi 配置: `~/.pi/agent/settings.json` (defaultProvider `ai-work-zai`, defaultModel `glm-5.2`, defaultThinkingLevel `max`).
- provider/model 定义: `/home/bolo/Workspace/skills/pi/models.json` (ai-work-zai/qwen/deepseek/moonshot/openai, 各有 thinkingFormat: zai/qwen/deepseek).
- enabledModels: `ai-work-zai/glm-5.3`, `ai-work-zai/glm-5.2`, `ai-work-qwen/qwen3.8-max`, `ai-work-deepseek/deepseek-v4-flash-0731`.

## 修复方向

**治本在中转站**, 但中转站代码不在当前工作区, 修复者需先确认对其是否有代码访问权:

- **若有中转站代码权**: 排查 SSE 流式转发逻辑. 重点: 模型停止后是否正确关闭流 (机制 a); reasoning HTML 化 (`\n`→`<br>`) 是否在退化空行上放大 (机制 b). 加重复检测 (连续 N 个相同短 delta → 截断) 或 reasoning max tokens.
- **若无中转站代码权**: 退而在 pi 侧加防护 (增强, 非 bug 修复): reasoning 流中连续 N 个相同短 delta 时自动 abort 并提示 "检测到退化循环". 实现位置: pi-ai `openai-completions.js` 流处理 (第 366–380 行附近), 在 `block.thinking += delta` 前加重复检测. 注意 pi 是 pnpm store 里的包, 改动方式需确认 (fork/patch/上游 PR).
- **即时绕过**: Esc 重试 (退化随机, 重试通常不再触发).

## 确定机制的方法

直接 curl 中转站原始流 (不经 pi), 观察 SSE chunk 序列:

```bash
curl -N https://ai-work.changzhi.top/v1/chat/completions \
  -H "Authorization: Bearer $CHANG_ZHI_AI_WORK" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-5.3","messages":[{"role":"user","content":"<易触发长 thinking 的 prompt>"}],"stream":true,"thinking":{"type":"enabled","clear_thinking":false}}'
```

看 `delta.reasoning_content` 是否出现 `　<br>` 重复, 及重复起始点是否对应模型 stop. 退化随机, 可能需多次或用高压 prompt 提高触发率. 此步可区分机制 a/b 并确认中转站是否为 `<br>` 引入者.

## 必读推荐

1. **会话 jsonl index 11** (`~/.pi/agent/sessions/--home-bolo-Workspace-skills--/2026-08-24T05-15-22-607Z_*.jsonl`) — 原始证据, 修复后回归比对. 用 `python3 -c "import json;..."` 取 `message.content[0].thinking` 头/尾.
2. **`pi/extensions/repetition-guard.ts`** — 防护本体 (含检测算法与阈值).
3. **`tests/pi/repetition-guard.test.mjs`** — 检测逻辑单测 (14 项).
4. **`tests/pi/faux-degenerate.ts`** — 端到端验证工具 (faux provider 脚本化退化流). 用法见文件头注释: `pi --mode json --model faux-degenerate/degenerate-1 -e tests/pi/faux-degenerate.ts -p 触发测试`; 正常对照加 `FAUX_CLEAN=1`.

## 路线图

- **起点**: 测试 access-web skill 功能 (已完成, scrape/browse 两模式均正常).
- **转折**: 测试中途出现 `　<br>` 无限刷屏, 转向诊断.
- **取证**: 从会话 jsonl 提取 thinking 原始字节, 确认重复单元与结构.
- **排除 pi**: 查 pi-ai 流处理源码 + 全 dist `<br>` 扫描 + 扩展排查 + zai 格式分析, 四条独立线排除.
- **定位**: 跨模型相同单元 + `<br>` 非模型自然输出 → 锁定中转站为共同根因.
- **现状**: 根因明确指向中转站; 具体机制 (流式重放 / HTML 化放大) 两种未定论; 诊断展示页面已生成.
- **pi 侧防护已实施** (2026-08-24, 扩展方式): `pi/extensions/repetition-guard.ts` (已 sync 到 `~/.pi/agent/extensions/`). 三层防线: L1 thinking+正文尾部周期检测; L2 单元长度分级阈值 (最小周期判定: 1 字符≥200次 / ≤64字符≥16次 / ≤1KB≥8次 / 更长≥4次, 纯空白单元×2); L3 thinking 128K 字符总量熔断. 触发即 `ctx.abort()` + notify; `message_end` 裁剪重复尾并留标记. 单测: `tests/pi/repetition-guard.test.mjs` (14 项全过, `node tests/pi/repetition-guard.test.mjs`).
- **端到端已验证** (2026-08-24, faux provider): 退化流 (实测同款 `　<br>` 单元) 下 thinking_delta 第 18 个 chunk 即自动中断, stopReason=aborted, 裁剪标记入消息, abort 后无 auto-retry; 正常长思考对照亦通过. 注: 对照实验中「正常收尾, 一切顺利.」×31 邻界误裁属预期 (短单元×31>阈值, 有意保守); 真实正常思考几乎不会连写同一短语 31 次. 权衡记录: 宁可极低概率误裁, 不漏真实死循环.
- **剩余**: ① curl 中转站原始流确定机制 a/b (可选, 治本需要) → ② 确认修复者对中转站代码访问权 → ③ ~~实施 pi 侧防护~~ 已完成 → ④ ~~回归验证~~ 已完成 (faux provider 端到端, 见下) . 距离目的地约 95% (防护已验证, 仅剩治本可选).
