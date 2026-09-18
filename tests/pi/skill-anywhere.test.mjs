// skill-anywhere.ts 扩展测试: 展开 / 补全场景判定 / 模糊匹配 / frontmatter 剥离.
// 运行: node --test tests/pi/skill-anywhere.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  collectSkillRefs,
  expandSkillTokens,
  fuzzyMatch,
  inlineSkillPrefix,
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
test("补全场景判定", () => {
  assert.equal(inlineSkillPrefix("帮我 /"), "");
  assert.equal(inlineSkillPrefix("帮我 /s"), "s");
  assert.equal(inlineSkillPrefix("帮我 /skill"), "skill");
  assert.equal(inlineSkillPrefix("帮我 /skill:"), "skill:");
  assert.equal(inlineSkillPrefix("帮我 /skill:ac"), "skill:ac");
  // 行首命令场景: 不接管
  assert.equal(inlineSkillPrefix("/skill:ac"), null);
  assert.equal(inlineSkillPrefix("  /skill:ac"), null);
  assert.equal(inlineSkillPrefix("/mo"), null);
  // 非场景
  assert.equal(inlineSkillPrefix("帮我 /t"), null);
  assert.equal(inlineSkillPrefix("帮我 /tmp/x"), null);
  assert.equal(inlineSkillPrefix("帮我 @file"), null);
  assert.equal(inlineSkillPrefix("普通文本"), null);
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
