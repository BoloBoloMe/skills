import { sliceByColumn, truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

/**
 * 弹窗正文限行 + 全文入口.
 *
 * 背景: pi 的 select/input 弹窗把整段标题折行后堆在选项上方, 既没有高度上限也没有滚动.
 * 正文一长就把底部的选项挤出屏幕, 用户只能盲操作.
 *
 * 做法: 正文按终端宽度折算展示行, 超过上限时只显示前几行并标注剩余行数,
 * 需要读全文时在 select 选项末尾追加 "查看完整内容", 选中后用可滚动的 editor
 * 打开全文, 关闭后回到原弹窗继续选.
 */

/** 弹窗正文最多占用的展示行数 (按终端宽度折算折行) */
export const MAX_PROMPT_LINES = 8;

/** 额外固定占用: 上下边框 2, 空行 3, 按键提示 1, 加上最多 5 个选项 */
const PROMPT_CHROME_LINES = 12;

/** 在 select 选项末尾追加的全文入口, 只在正文被截断时出现 */
export const VIEW_FULL_OPTION = "查看完整内容";

/** 用到的 UI 方法子集, 便于单测替掉真实 UI */
export interface PromptUi {
  select(title: string, options: string[]): Promise<string | undefined>;
  input(title: string, placeholder?: string): Promise<string | undefined>;
  editor(title: string, prefill?: string): Promise<string | undefined>;
}

export interface BudgetOptions {
  /** 正文行数上限, 默认按终端高度自适应 */
  maxLines?: number;
  /** 截断提示, 参数为被省掉的行数 */
  note?: (omittedLines: number) => string;
}

export interface BudgetResult {
  text: string;
  truncated: boolean;
}

/** select 弹窗的截断提示: 指向全文入口 */
export function makeNote(omittedLines: number): string {
  return `…(还有 ${omittedLines} 行, 选「${VIEW_FULL_OPTION}」查看)`;
}

/** input 弹窗的截断提示: 全文只能在更早的弹窗里看过 */
export function makeInputNote(omittedLines: number): string {
  return `…(还有 ${omittedLines} 行, 全文已在上一弹窗提供)`;
}

/** 弹窗正文可用列数: 弹窗左右各有 1 列内边距 */
function promptColumns(): number {
  return Math.max(20, (process.stdout.columns ?? 80) - 2);
}

/** 按终端高度收窄正文上限, 避免小窗口下选项仍被挤掉 */
function promptMaxLines(): number {
  const rows = process.stdout.rows ?? 24;
  return Math.max(3, Math.min(MAX_PROMPT_LINES, rows - PROMPT_CHROME_LINES));
}

function displayRows(text: string, columns: number): number {
  return Math.max(1, Math.ceil(visibleWidth(text) / columns));
}

/** 把正文压进行数上限; 没超限时原样返回 */
export function budgetPromptText(text: string, options: BudgetOptions = {}): BudgetResult {
  const maxLines = options.maxLines ?? promptMaxLines();
  const columns = promptColumns();
  const lines = text.split("\n");

  // 从开头按折行行数装填, 返回装到哪一行 (nextIndex) 以及用掉的行数
  const fit = (budget: number) => {
    const kept: string[] = [];
    let used = 0;
    for (const line of lines) {
      const rows = displayRows(line, columns);
      if (used + rows > budget) break;
      kept.push(line);
      used += rows;
    }
    return { kept, used, nextIndex: kept.length };
  };

  const full = fit(maxLines);
  if (full.nextIndex === lines.length) return { text, truncated: false };

  // 提示自身可能折行, 且它报的行数取决于最后显示了几行; 迭代两次即可稳定
  const buildNote = options.note ?? ((omitted: number) => `…(还有 ${omitted} 行)`);
  let note = buildNote(lines.length - full.nextIndex);
  let body = full;
  let room = 0;
  for (let pass = 0; pass < 2; pass++) {
    const noteRows = displayRows(note, columns);
    body = fit(Math.max(0, maxLines - noteRows - 1));
    room = maxLines - noteRows - body.used;
    const shown = body.kept.length + (room > 0 && body.nextIndex < lines.length ? 1 : 0);
    note = buildNote(lines.length - shown);
  }

  // 放不下的当前行按剩余行数截断, 保留开头便于判断
  if (room > 0 && body.nextIndex < lines.length) {
    body.kept.push(truncateToWidth(lines[body.nextIndex] ?? "", room * columns - 1, "…"));
  }
  body.kept.push(note);
  return { text: body.kept.join("\n"), truncated: true };
}

/**
 * 正文超限的 select 弹窗: 摘要 + 选项, 正文超限时追加 "查看完整内容".
 * 选中全文入口时打开 editor, 关闭后回到同一个弹窗, 直到用户做出真正的选择.
 */
export async function selectWithFullText(
  ui: PromptUi,
  title: string,
  promptText: string,
  options: string[],
): Promise<string | undefined> {
  const { text, truncated } = budgetPromptText(promptText, { note: makeNote });
  const choices = truncated ? [...options, VIEW_FULL_OPTION] : options;

  for (;;) {
    const choice = await ui.select(text, choices);
    if (choice !== VIEW_FULL_OPTION) return choice;
    await ui.editor(`完整内容 (Esc 关闭后回到选择): ${title}`, promptText);
  }
}

/** 过长的选项文字会把选项列表撑成多行, 只保留可辨认的尾段 (给前半段标签留位) */
export function shortenTail(value: string, maxColumns = Math.max(12, Math.min(40, promptColumns() - 16))): string {
  const width = visibleWidth(value);
  if (width <= maxColumns) return value;
  return `…${sliceByColumn(value, width - maxColumns + 1, maxColumns - 1)}`;
}

/** input 弹窗没有全文入口, 只做限行; 全文应在更早的 select 弹窗里看过 */
export function budgetInputPrompt(promptText: string): string {
  return budgetPromptText(promptText, { note: makeInputNote }).text;
}