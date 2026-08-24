// repetition-guard 检测逻辑单测.
// 运行: node tests/pi/repetition-guard.test.mjs
import assert from "node:assert/strict";
import { findRepetitiveTail } from "../../pi/extensions/repetition-guard.ts";

const cases = [];
const test = (name, fn) => cases.push({ name, fn });

test("正常文本不触发", () => {
  const s = "先分析问题, 再拆解步骤, 然后逐项验证, 最后总结结论.";
  assert.equal(findRepetitiveTail(s), undefined);
});

test("实测案例: 前缀 + `　<br>` ×50 触发, 起点在正常前缀后", () => {
  const prefix = "正常思考内容若干字";
  const s = prefix + "　<br>".repeat(50);
  const rep = findRepetitiveTail(s);
  assert.ok(rep, "应检出");
  assert.equal(rep.unit, "　<br>");
  assert.equal(rep.count, 50);
  assert.equal(rep.start, prefix.length);
  assert.equal(s.slice(rep.start), "　<br>".repeat(rep.count));
});

test("分隔线 80 个 '-' 不触发 (单字符需 200 次)", () => {
  assert.equal(findRepetitiveTail("-".repeat(80)), undefined);
});

test("单字符 300 次 a 触发", () => {
  const rep = findRepetitiveTail("正常开头" + "a".repeat(300));
  assert.ok(rep);
  assert.equal(rep.unit, "a");
  assert.equal(rep.count, 300);
});

test("纯空白单元阈值加倍: 换行 300 次不触发, 401 次触发", () => {
  assert.equal(findRepetitiveTail("\n".repeat(300)), undefined);
  const rep = findRepetitiveTail("\n".repeat(401));
  assert.ok(rep);
  assert.equal(rep.count, 401);
});

test("短单元按最小周期判定: `是的`x30 (即 `是的是的`x15) 触发, x15 不触发", () => {
  assert.equal(findRepetitiveTail("是的是的".repeat(7) + "是的是的".slice(0, 2)), undefined); // 是的x15
  const rep = findRepetitiveTail("是的".repeat(30));
  assert.ok(rep);
  assert.equal(rep.unit, "是的");
  assert.equal(rep.count, 30);
});

test("中单元 (最小周期 65..1024) 7 次不触发, 8 次触发", () => {
  const unit = Array.from({ length: 100 }, (_, i) => String.fromCharCode(0x4e00 + i)).join(""); // 100 个互异字符, 最小周期 100
  assert.equal(findRepetitiveTail(unit.repeat(7)), undefined);
  const rep = findRepetitiveTail(unit.repeat(8));
  assert.ok(rep);
  assert.equal(rep.count, 8);
});

test("长单元 (最小周期 >1024) 3 次不触发, 4 次触发", () => {
  const unit = Array.from({ length: 1100 }, (_, i) => String.fromCharCode(0x4e00 + i)).join(""); // 最小周期 1100
  assert.equal(findRepetitiveTail(unit.repeat(3)), undefined);
  const rep = findRepetitiveTail(unit.repeat(4));
  assert.ok(rep);
  assert.equal(rep.count, 4);
});

test("正常文本 + 尾部垃圾: 只裁垃圾段", () => {
  const normal = "这是一段正常的分析过程, 包含换行\n和空格 . ".repeat(20);
  const s = normal + "AB".repeat(100);
  const rep = findRepetitiveTail(s);
  assert.ok(rep);
  assert.equal(rep.unit, "AB");
  assert.equal(rep.start, normal.length);
});

test("重复段不足窗口截断时仍可检测 (文本远大于窗口)", () => {
  const junk = "填".repeat(70000); // 超过 64K 窗口, 单字符达标
  const rep = findRepetitiveTail(junk);
  assert.ok(rep);
  assert.equal(rep.unit, "填");
  assert.equal(rep.count, 65536); // 窗口内次数
  assert.equal(rep.start, 70000 - 65536);
});

test("相似但不完全相同的块不触发 (JSON 数组项渐变)", () => {
  const items = Array.from({ length: 40 }, (_, i) => `{"index":${i},"value":"some constant tail text here"}`);
  assert.equal(findRepetitiveTail(items.join("\n")), undefined);
});

test("过短文本不触发", () => {
  assert.equal(findRepetitiveTail("ab"), undefined);
  assert.equal(findRepetitiveTail(""), undefined);
});

test("性能: 64KB 病态混合输入在预算内出结果", () => {
  const s = "abcd".repeat(16000); // 周期 4, 达标
  const t0 = Date.now();
  const rep = findRepetitiveTail(s);
  const ms = Date.now() - t0;
  assert.ok(rep);
  assert.ok(ms < 200, `耗时 ${ms}ms`);
});

test("锚点陷阱: 块尾字符相同但块不同, 不误报", () => {
  // 每 8 字符一块, 块尾都是 'z' 但块内不同
  const blocks = Array.from({ length: 64 }, (_, i) => `${String(i % 7).padStart(7, "0")}z`);
  assert.equal(findRepetitiveTail(blocks.join("")), undefined);
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
