// prompt-budget (弹窗正文限行) 单测.
// 运行: node tests/pi/prompt-budget.test.mjs
//
// 回归背景: pi 的 select/input 弹窗把整段标题折行堆在选项上方, 没有高度上限也没有滚动,
// 正文一长就把底部选项挤出屏幕, 用户只能盲操作. 本文件覆盖限行算法: 不超限时原样返回,
// 超限时总行数不越界, 截断提示占位, 仍能看到被截断行的开头.
import assert from "node:assert/strict";
import { registerHooks } from "node:module";

// 扩展的 helper 依赖 pi-tui; 单测环境没有 pi 安装, 用同口径 stub 替换
const stubUrl = new URL("./prompt-budget-tui-stub.mjs", import.meta.url).href;
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "@earendil-works/pi-tui") return { url: stubUrl, shortCircuit: true };
    return nextResolve(specifier, context);
  },
});

const { budgetPromptText, makeNote, shortenTail } = await import("../../pi/extensions/lib/prompt-budget.ts");
const { visibleWidth } = await import("./prompt-budget-tui-stub.mjs");

const setSize = (columns, rows) => {
  Object.defineProperty(process.stdout, "columns", { value: columns, configurable: true });
  Object.defineProperty(process.stdout, "rows", { value: rows, configurable: true });
};

const displayRows = (text, columns) =>
  text.split("\n").reduce((sum, line) => sum + Math.max(1, Math.ceil(visibleWidth(line) / columns)), 0);

const cases = [];
const test = (name, fn) => cases.push({ name, fn });

test("短文本原样返回, 不标记截断", () => {
  setSize(100, 40);
  const input = "标题\n字段: 值\n说明";
  const result = budgetPromptText(input);
  assert.equal(result.truncated, false);
  assert.equal(result.text, input);
});

test("超限时总展示行数不超过上限, 末行是截断提示", () => {
  setSize(100, 40);
  const input = Array.from({ length: 30 }, (_, i) => `第 ${i} 行`).join("\n");
  const result = budgetPromptText(input, { maxLines: 8 });
  assert.equal(result.truncated, true);
  assert.ok(displayRows(result.text, 98) <= 8, `行数超限: ${displayRows(result.text, 98)}`);
  assert.match(result.text.split("\n").at(-1), /还有 \d+ 行/);
});

test("截断行保留开头, 不整段丢弃", () => {
  setSize(100, 40);
  const input = ["头", "x".repeat(400), "尾"].join("\n");
  const result = budgetPromptText(input, { maxLines: 6 });
  assert.equal(result.truncated, true);
  assert.ok(result.text.includes("xxx"), result.text);
});

test("窄终端按折行计数: 中文按 2 列折算", () => {
  setSize(40, 40);
  const input = Array.from({ length: 12 }, (_, i) => `第${i}行内容`).join("\n");
  const result = budgetPromptText(input, { maxLines: 5 });
  assert.equal(result.truncated, true);
  assert.ok(displayRows(result.text, 38) <= 5, `行数超限: ${displayRows(result.text, 38)}`);
});

test("正文上限随终端高度收窄, 小窗口不保留 8 行", () => {
  setSize(100, 15);
  const input = Array.from({ length: 30 }, (_, i) => `第 ${i} 行`).join("\n");
  const result = budgetPromptText(input);
  assert.equal(result.truncated, true);
  assert.ok(displayRows(result.text, 98) <= 3, `行数超限: ${displayRows(result.text, 98)}`);
});

test("自定义提示文案进入正文末行, 且报的行数与实际省略行数一致", () => {
  setSize(100, 40);
  const input = Array.from({ length: 30 }, (_, i) => `第 ${i} 行`).join("\n");
  const result = budgetPromptText(input, { maxLines: 6, note: makeNote });
  const shown = result.text.split("\n").length - 1; // 末行是提示, 其余是正文
  assert.equal(result.text.split("\n").at(-1), makeNote(30 - shown));
  assert.ok(displayRows(result.text, 98) <= 6);
});

test("shortenTail 保留尾部可辨认片段", () => {
  const path = `/home/${"dir/".repeat(20)}tail`;
  const shortened = shortenTail(path, 20);
  assert.ok(shortened.startsWith("…"));
  assert.ok(shortened.endsWith("tail"));
  assert.ok(visibleWidth(shortened) <= 20, `宽度超限: ${visibleWidth(shortened)}`);
  assert.equal(shortenTail("短路径", 20), "短路径");
});

let failed = 0;
for (const { name, fn } of cases) {
  try {
    await fn();
    console.log(`ok - ${name}`);
  } catch (err) {
    failed++;
    console.error(`FAIL - ${name}\n  ${err?.message ?? err}`);
  }
}
console.log(failed === 0 ? `\n全部 ${cases.length} 项通过` : `\n${failed}/${cases.length} 项失败`);
process.exit(failed === 0 ? 0 : 1);