// skill-anywhere.ts 扩展测试: 展开 / 补全场景判定 / 模糊匹配 / frontmatter 剥离.
// 运行: node --test tests/pi/skill-anywhere.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  atSlashLineStart,
  collectSkillRefs,
  expandSkillTokens,
  fuzzyMatch,
  inlineSlashPrefix,
  makeSkillAnywhereProvider,
  stripSkillFrontmatter,
} from "../../pi/extensions/skill-anywhere.ts";

// ---- 测试夹具: 临时目录里造两个 SKILL.md ----
function makeFixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "skill-anywhere-"));
  const refs = new Map();
  for (const [name, body] of [
    ["present", "# Present\n\n可视化展示.\n"],
    ["access-web", "# Access Web\n\n网页访问.\n"],
  ]) {
    const skillDir = path.join(dir, name);
    fs.mkdirSync(skillDir);
    const filePath = path.join(skillDir, "SKILL.md");
    fs.writeFileSync(
      filePath,
      `---\nname: ${name}\ndescription: skill ${name} for test\n---\n${body}`,
      "utf-8",
    );
    refs.set(name, {
      name,
      filePath,
      baseDir: skillDir,
      description: `skill ${name} for test`,
    });
  }
  return { dir, refs };
}

const fx = makeFixture();
const readSkill = (ref) => fs.readFileSync(ref.filePath, "utf-8");
const block = (ref) => {
  const content = fs.readFileSync(ref.filePath, "utf-8");
  const body = content.replace(/^---\n[\s\S]*?\n---\n/, "").trim(); // 与 stripSkillFrontmatter 等价 (fixture 无嵌套 fence)
  return `<skill name="${ref.name}" location="${ref.filePath}">\nReferences are relative to ${ref.baseDir}.\n\n${body}\n</skill>`;
};

// ---- stripSkillFrontmatter ----
test("frontmatter 剥离: 正常/缺失/坏 fence", () => {
  assert.equal(stripSkillFrontmatter("---\nname: x\n---\nbody"), "body");
  assert.equal(stripSkillFrontmatter("no frontmatter"), "no frontmatter");
  assert.equal(stripSkillFrontmatter("---\nunclosed"), "---\nunclosed");
  assert.equal(stripSkillFrontmatter("---\r\nname: x\r\n---\r\nCRLF body"), "CRLF body");
});

// ---- expandSkillTokens ----
test("中间 token 原位展开, 前后文保留", () => {
  const out = expandSkillTokens("帮我 /skill:present 做个图", fx.refs, readSkill);
  assert.ok(out.changed);
  assert.equal(out.text, `帮我 ${block(fx.refs.get("present"))} 做个图`);
});

test("整条开头留给内置, 不动", () => {
  const out = expandSkillTokens("/skill:present 做个图", fx.refs, readSkill);
  assert.equal(out.changed, false);
  assert.equal(out.text, "/skill:present 做个图");
});

test("第二行行首展开 (换行算空白边界)", () => {
  const out = expandSkillTokens("第一行\n/skill:present", fx.refs, readSkill);
  assert.ok(out.changed);
  assert.equal(out.text, `第一行\n${block(fx.refs.get("present"))}`);
});

test("缩进行首展开", () => {
  const out = expandSkillTokens("  /skill:present", fx.refs, readSkill);
  assert.ok(out.changed);
  assert.equal(out.text, `  ${block(fx.refs.get("present"))}`);
});

test("未知 skill 原样保留", () => {
  const out = expandSkillTokens("用 /skill:nope 试试", fx.refs, readSkill);
  assert.equal(out.changed, false);
  assert.equal(out.text, "用 /skill:nope 试试");
});

test("URL 与路径中的 /skill: 不误伤", () => {
  for (const text of [
    "看 https://example.com/skill:present",
    "路径 a/skill:present 不展开",
  ]) {
    const out = expandSkillTokens(text, fx.refs, readSkill);
    assert.equal(out.changed, false, text);
    assert.equal(out.text, text);
  }
});

test("多个 token 全部展开", () => {
  const out = expandSkillTokens(
    "先 /skill:access-web 再 /skill:present",
    fx.refs,
    readSkill,
  );
  assert.ok(out.changed);
  assert.equal(
    out.text,
    `先 ${block(fx.refs.get("access-web"))} 再 ${block(fx.refs.get("present"))}`,
  );
});

test("名字带斜杠不展开 (与内置行为一致)", () => {
  const out = expandSkillTokens("x /skill:present/y z", fx.refs, readSkill);
  assert.equal(out.changed, false);
});

test("读文件失败: 原样保留并报告", () => {
  const out = expandSkillTokens("x /skill:present y", fx.refs, () => {
    throw new Error("boom");
  });
  assert.equal(out.changed, false);
  assert.deepEqual(out.failed, ["present"]);
  assert.equal(out.text, "x /skill:present y");
});

test("整条开头 + 中间 token 混合: 中间的展开, 开头的留给内置", () => {
  const out = expandSkillTokens("/skill:present 参数 /skill:access-web", fx.refs, readSkill);
  assert.ok(out.changed);
  assert.equal(
    out.text,
    `/skill:present 参数 ${block(fx.refs.get("access-web"))}`,
  );
});

// ---- inlineSkillPrefix ----
test("非行首 /token 场景判定", () => {
  assert.equal(inlineSlashPrefix("帮我 /"), "");
  assert.equal(inlineSlashPrefix("帮我 /s"), "s");
  assert.equal(inlineSlashPrefix("帮我 /skill"), "skill");
  assert.equal(inlineSlashPrefix("帮我 /skill:"), "skill:");
  assert.equal(inlineSlashPrefix("帮我 /skill:ac"), "skill:ac");
  // 任意 /token 都算 (不再要求 skill: 前缀), fuzzy 过滤交给菜单
  assert.equal(inlineSlashPrefix("帮我 /t"), "t");
  assert.equal(inlineSlashPrefix("帮我 /pr"), "pr");
  // 行首命令场景: 不接管
  assert.equal(inlineSlashPrefix("/skill:ac"), null);
  assert.equal(inlineSlashPrefix("  /skill:ac"), null);
  assert.equal(inlineSlashPrefix("/mo"), null);
  // 非场景
  assert.equal(inlineSlashPrefix("帮我 /tmp/x"), null); // token 内含 /
  assert.equal(inlineSlashPrefix("帮我 @file"), null);
  assert.equal(inlineSlashPrefix("普通文本"), null);
});

// ---- fuzzyMatch ----
test("子序列模糊匹配", () => {
  assert.equal(fuzzyMatch("", "anything"), true);
  assert.equal(fuzzyMatch("ac", "access-web"), true);
  assert.equal(fuzzyMatch("aw", "access-web"), true);
  assert.equal(fuzzyMatch("web", "access-web"), true);
  assert.equal(fuzzyMatch("xyz", "access-web"), false);
});

// ---- collectSkillRefs ----
test("collectSkillRefs 从命令表提取 skill", () => {
  const commands = [
    {
      name: "my-cmd",
      source: "extension",
      sourceInfo: { path: "/x/my-cmd.ts" },
    },
    {
      name: "skill:present",
      description: "展示",
      source: "skill",
      sourceInfo: { path: "/skills/present/SKILL.md", baseDir: "/skills/present" },
    },
    {
      name: "skill:no-basedir",
      source: "skill",
      sourceInfo: { path: "/skills/nb/SKILL.md" },
    },
  ];
  const refs = collectSkillRefs(commands);
  assert.equal(refs.size, 2);
  // baseDir 始终是 SKILL.md 所在目录 (对齐内置 skill.baseDir), 不用 sourceInfo.baseDir (资源根父级)
  assert.equal(refs.get("present").baseDir, "/skills/present");
  assert.equal(refs.get("no-basedir").baseDir, "/skills/nb");
});

// ---- provider 路由 (回归: 行首曾误拦, 内置命令菜单消失) ----
function setupProvider() {
  const calls = { current: 0 };
  const current = {
    async getSuggestions(_lines, _l, _c, _options) {
      calls.current++;
      return { items: [{ value: "BUILTIN", label: "BUILTIN" }], prefix: "x" };
    },
    applyCompletion: (..._args) => "CURRENT",
  };
  const skills = new Map([
    ["present", { name: "present", filePath: "/s/p/SKILL.md", baseDir: "/s/p", description: "d" }],
  ]);
  const provider = makeSkillAnywhereProvider(current, () => skills);
  return { provider, calls };
}

const suggest = (provider, line, options = {}) => provider.getSuggestions([line], 0, line.length, options);

test("行首 / 场景委托内置 (命令菜单不受影响)", async () => {
  const { provider, calls } = setupProvider();
  for (const line of ["/", "/m", "/skill:", "/skill:pr", "  /sk"]) {
    const out = await suggest(provider, line);
    assert.deepEqual(out.items.map((i) => i.value), ["BUILTIN"], line);
  }
  assert.equal(calls.current, 5);
});

test("非行首 skill 匹配返回 skill 菜单, 不碰内置", async () => {
  const { provider, calls } = setupProvider();
  for (const [line, prefix] of [
    ["帮我 /", "/"],
    ["帮我 /s", "/s"],
    ["帮我 /skill:pr", "/skill:pr"],
    ["帮我 /pr", "/pr"], // fuzzy: p-r 命中 s-k-i-l-l-:-p-r-e-s-e-n-t
  ]) {
    const out = await suggest(provider, line);
    assert.deepEqual(out.items.map((i) => i.value), ["skill:present"], line);
    assert.equal(out.prefix, prefix, line);
  }
  assert.equal(calls.current, 0);
});

test("无 skill 匹配: 自然触发无菜单, force 委托内置文件补全", async () => {
  const { provider, calls } = setupProvider();
  assert.equal(await suggest(provider, "帮我 /tm"), null); // t-m 不命中任何 skill 命令
  const forced = await suggest(provider, "帮我 /tm", { force: true });
  assert.deepEqual(forced.items.map((i) => i.value), ["BUILTIN"]);
  assert.equal(calls.current, 1);
});

test("不在 /token 内 (如 @) 一律委托", async () => {
  const { provider, calls } = setupProvider();
  const out = await suggest(provider, "帮我 @fil");
  assert.deepEqual(out.items.map((i) => i.value), ["BUILTIN"]);
  assert.equal(calls.current, 1);
});

test("applyCompletion: 自己的场景替换并加空格, 其余委托", () => {
  const { provider } = setupProvider();
  // 自己的场景: “帮我 /skill:pr" 光标在末尾, prefix=/skill:pr
  const mine = provider.applyCompletion(
    ["帮我 /skill:pr"],
    0,
    "帮我 /skill:pr".length,
    { value: "skill:present" },
    "/skill:pr",
  );
  assert.deepEqual(mine.lines, ["帮我 /skill:present "]);
  assert.equal(mine.cursorCol, "帮我 /skill:present ".length);
  // 行首场景 (内置命令补全) 委托
  assert.equal(
    provider.applyCompletion(["/skill:pr"], 0, 9, { value: "skill:present" }, "/skill:pr"),
    "CURRENT",
  );
});

test("atSlashLineStart 判定", () => {
  assert.equal(atSlashLineStart("/"), true);
  assert.equal(atSlashLineStart("  /sk"), true);
  assert.equal(atSlashLineStart("帮我 /"), false);
});
