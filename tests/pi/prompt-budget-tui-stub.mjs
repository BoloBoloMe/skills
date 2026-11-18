// 供 prompt-budget 单测替换 @earendil-works/pi-tui: 只保留被测逻辑用到的三个函数.
// 行宽口径与真实实现一致的部分: ANSI 无关的可见列表, 全宽字符计 2 列.
const WIDE =
  /[\u1100-\u115F\u2E80-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60\uFFE0-\uFFE6]/;

export function visibleWidth(text) {
  let width = 0;
  for (const char of text) width += WIDE.test(char) ? 2 : 1;
  return width;
}

export function truncateToWidth(text, maxWidth, ellipsis = "...") {
  if (visibleWidth(text) <= maxWidth) return text;
  let out = "";
  let used = 0;
  const budget = Math.max(0, maxWidth - visibleWidth(ellipsis));
  for (const char of text) {
    const w = WIDE.test(char) ? 2 : 1;
    if (used + w > budget) break;
    out += char;
    used += w;
  }
  return out + ellipsis;
}

export function sliceByColumn(text, startCol, length) {
  const chars = [...text];
  let col = 0;
  let out = "";
  for (const char of chars) {
    const w = WIDE.test(char) ? 2 : 1;
    if (col >= startCol && col < startCol + length) out += char;
    col += w;
  }
  return out;
}