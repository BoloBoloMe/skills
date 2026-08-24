import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * repetition-guard: 检测并中断 assistant 流式输出中的退化死循环.
 *
 * 背景: 中转站 ai-work.changzhi.top 在 reasoning 流上偶发无限重放重复单元
 * (实测 `　<br>` ×1460), 烧 token 直到用户手动 Esc. 详见
 * docs/changes/handoff/2026-08-24-repetition-loop.md.
 *
 * 三层防线:
 *   L1 位置: thinking 与正文 (text) block 都做周期检测.
 *   L2 长度: 周期检测按重复单元长度分级要求次数 (短单元多次, 长单元少次).
 *   L3 总量: thinking 累积超过硬上限 (128K 字符) 直接熔断, 兜非周期退化.
 *
 * 触发后: ctx.abort() 中断当前 run + notify; message_end 时裁掉已积累的
 * 重复尾巴并留标记行, 防止垃圾进入后续上下文.
 *
 * 检测算法 (纯 code unit 级, 不做字符边界特判): 取累积文本尾部窗口,
 * 对每个候选周期 p 先用块尾字符锚点快筛, 通过后向前扩展求最大重复次数,
 * 次数达到分级阈值即判定退化. 有比较预算防止病态输入拖慢流.
 */

// ---- 可调参数 ----
const TAIL_WINDOW = 65536; // 周期检测窗口 (UTF-16 code unit)
const THINKING_HARD_LIMIT = 131072; // thinking 总量熔断阈值 (字符)
const DETECT_STRIDE = 256; // 同一 block 两次周期检测的最小增量 (字符)
const MAX_UNIT = 16384; // 最大可检测重复单元长度 (字符)
const SCAN_BUDGET = 200000; // 单次检测的比较预算

const BLANK_CHARS = new Set([
  " ",
 "\t",
 "\n",
 "\r",
 "\u00a0",
 "\u2028",
 "\u2029",
 "\u3000",
 "\ufeff",
]);

export type RepetitiveTail = {
  unit: string; // 重复单元
  count: number; // 完整重复次数
  start: number; // 重复段起点在原文中的偏移
};

/** 分级阈值: 达到该次数才判定退化 (未含纯空白单元的加倍). */
function baseNeed(unitLen: number): number {
  if (unitLen <= 1) return 200; // 单字符: 豁免正常分隔线/填充
  if (unitLen <= 64) return 16; // 短单元 (如 `　<br>`)
  if (unitLen <= 1024) return 8; // 中单元
  return 4; // 长单元 (≤ 64KB/4)
}

function isBlankUnit(unit: string): boolean {
  if (unit.length === 0) return false;
  for (const ch of unit) {
    if (!BLANK_CHARS.has(ch)) return false;
  }
  return true;
}

/**
 * 检测文本尾部是否存在达标周期性重复.
 * 返回重复单元/次数/起点, 无退化则返回 undefined.
 */
export function findRepetitiveTail(s: string): RepetitiveTail | undefined {
  const total = s.length;
  if (total < 4) return undefined;

  const window = total > TAIL_WINDOW ? s.slice(total - TAIL_WINDOW) : s;
  const L = window.length;
  const offset = total - L;
  let budget = SCAN_BUDGET;

  for (let p = 1; p <= MAX_UNIT; p++) {
    const need = baseNeed(p);
    if (p * need > L) continue;

    // 快筛: 以最后一字符为锚, 检查前 need-1 个块的块尾字符
    const anchor = window.charCodeAt(L - 1);
    let pass = true;
    for (let k = 1; k < need; k++) {
      if (--budget < 0) return undefined;
      if (window.charCodeAt(L - 1 - k * p) !== anchor) {
        pass = false;
        break;
      }
    }
    if (!pass) continue;

    // 扩展: 从最后一个块向前验证并扩展最大重复段
    const unit = window.slice(L - p);
    let start = L - p;
    while (start - p >= 0 && window.slice(start - p, start) === unit) {
      start -= p;
      if (--budget < 0) break;
    }

    // 归约最小周期单元: p 的重复段可能是更小单元的倍数切法
    // (如 `--`x40 实为 `-`x80), 阈值必须按最小单元的长度与总次数判定.
    let vlen = p;
    for (let q = 1; q * 2 <= p; q++) {
      if (p % q !== 0) continue;
      let isRepeat = true;
      for (let i = 0; i < p; i++) {
        if (--budget < 0) return undefined;
        if (window.charCodeAt(L - p + i) !== window.charCodeAt(L - p + (i % q))) {
          isRepeat = false;
          break;
        }
      }
      if (isRepeat) {
        vlen = q;
        break;
      }
    }
    const v = vlen === p ? unit : window.slice(L - vlen);
    const count = (L - start) / vlen;

    const required = isBlankUnit(v) ? baseNeed(vlen) * 2 : baseNeed(vlen);
    if (count >= required) {
      return { unit: v, count, start: offset + start };
    }
  }
  return undefined;
}

function preview(unit: string): string {
  const shown = unit.length > 48 ? `${unit.slice(0, 48)}…` : unit;
  return JSON.stringify(shown);
}

type GuardState = {
  fired: boolean;
  reason: string | undefined;
  checkedAt: Map<number, number>; // contentIndex -> 上次检测时的文本长度
};

function newState(): GuardState {
  return { fired: false, reason: undefined, checkedAt: new Map() };
}

export default function (pi: ExtensionAPI) {
  let state = newState();

  const reset = () => {
    state = newState();
  };

  const fire = (ctx: { abort(): void; hasUI: boolean; ui: { notify(msg: string, kind: "info" | "error"): void } }, reason: string) => {
    if (state.fired) return;
    state.fired = true;
    state.reason = reason;
    try {
      ctx.abort();
    } catch {
      // abort 不可用时仅提示
    }
    ctx.ui.notify(`[repetition-guard] ${reason}; 已中断, 可直接重试.`, "error");
  };

  pi.on("session_start", reset);
  pi.on("message_start", (event) => {
    const message = event.message as { role?: string } | undefined;
    if (message?.role === "assistant") reset();
  });

  pi.on("message_update", async (event, ctx) => {
    const ev = event.assistantMessageEvent as
      | { type: string; contentIndex: number; delta: string }
      | undefined;
    if (!ev || (ev.type !== "thinking_delta" && ev.type !== "text_delta")) return;

    const message = event.message as
      | { role?: string; content?: Array<{ type?: string; thinking?: string; text?: string }> }
      | undefined;
    if (message?.role !== "assistant") return;
    const block = message.content?.[ev.contentIndex];
    if (!block || (block.type !== "thinking" && block.type !== "text")) return;

    const text = block.type === "thinking" ? block.thinking : block.text;
    if (typeof text !== "string" || text.length === 0) return;
    const kind = block.type === "thinking" ? "思考" : "正文";

    // L3: thinking 总量熔断
    if (block.type === "thinking" && text.length >= THINKING_HARD_LIMIT) {
      fire(ctx, `${kind}长度 ${text.length} 已达硬上限 ${THINKING_HARD_LIMIT}`);
      return;
    }

    // L1/L2: 尾部周期检测 (频控)
    const last = state.checkedAt.get(ev.contentIndex) ?? 0;
    if (text.length - last < DETECT_STRIDE) return;
    state.checkedAt.set(ev.contentIndex, text.length);

    const rep = findRepetitiveTail(text);
    if (rep) {
      fire(ctx, `${kind}退化循环: 单元 ${preview(rep.unit)} ×${rep.count}`);
    }
  });

  pi.on("message_end", async (event) => {
    const message = event.message as
      | {
          role?: string;
          content?: Array<Record<string, unknown> & { type?: string }>;
          [key: string]: unknown;
        }
      | undefined;
    if (message?.role !== "assistant" || !Array.isArray(message.content)) return;

    let changed = false;
    const content = message.content.map((block) => {
      if (!block || (block.type !== "thinking" && block.type !== "text")) return block;
      const key = block.type === "thinking" ? "thinking" : "text";
      const text = block[key];
      if (typeof text !== "string") return block;

      const rep = findRepetitiveTail(text);
      if (!rep) return block;

      const removed = text.length - rep.start;
      const note =
        `\n\n[repetition-guard: 截断退化重复 ${rep.count}x ${rep.unit.length} 字符单元, ` +
        `移除 ${removed} 字符]`;
      changed = true;
      return { ...block, [key]: `${text.slice(0, rep.start).replace(/\s+$/, "")}${note}` };
    });

    if (changed) {
      return { message: { ...message, content } };
    }
  });
}
