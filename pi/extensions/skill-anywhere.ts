import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readFileSync } from "node:fs";
import { dirname } from "node:path";

/**
 * skill-anywhere: 让 /skill:name 在输入框任意位置生效.
 *
 * pi 内置只在整条输入以 "/skill:" 开头时展开 skill 命令; 本扩展补两块:
 *
 * 1. 展开 (input 事件 transform): 扫描文本中所有 "前面是行首或空白" 的
 *    /skill:name token, 原位替换为 <skill> block (格式复刻内置展开).
 *    整条开头的 token 留给内置逻辑, 避免双重处理. 未知 skill 名原样保留
 *    (与内置一致, 交给 LLM).
 *
 * 2. 补全 (addAutocompleteProvider): 空白后输入 "/" 且已打部分 "skill:"
 *    前缀时弹出 skill 命令菜单. 判定用精准前缀 (typed 是 "skill:" 的前缀
 *    或以 "skill:" 开头), 路径输入 ("/tmp" 等) 零干扰. 行首 "/" 场景一律
 *    委托内置 provider, 保持原有全命令菜单不变.
 *
 * 展开 block 与内置 _expandSkillCommand 逐字对齐:
 *   <skill name="..." location="...">
 *   References are relative to <baseDir>.
 *
 *   <body (去 frontmatter)>
 *   </skill>
 */

/** 光标前 "空白后的 /token" (token 内无 / 无空白), 捕获 / 后已打的部分. */
const INLINE_SLASH_RE = /(?:^|\s)\/([^/\s]*)$/;

/** 文本中的 skill token: 前面是行首或空白, 名字到下一个空白. */
const SKILL_TOKEN_RE = /(^|\s)(\/skill:[^\s]+)/g;

export type SkillRef = {
  name: string; // 不含 "skill:" 前缀
  filePath: string; // SKILL.md 绝对路径
  baseDir: string;
  description: string;
};

type CommandLike = {
  name: string;
  description?: string;
  source: string;
  sourceInfo: { path: string; baseDir?: string };
};

/** 从 pi.getCommands() 结果提取 skill 表 (name -> SkillRef).
 * baseDir 取 SKILL.md 所在目录, 对齐内置展开的 skill.baseDir 语义
 * (sourceInfo.baseDir 是资源根的父级, 不是相对路径基准). */
export function collectSkillRefs(commands: CommandLike[]): Map<string, SkillRef> {
  const map = new Map<string, SkillRef>();
  for (const cmd of commands) {
    if (cmd.source !== "skill" || !cmd.name.startsWith("skill:")) continue;
    const name = cmd.name.slice("skill:".length);
    const filePath = cmd.sourceInfo.path;
    map.set(name, {
      name,
      filePath,
      baseDir: dirname(filePath),
      description: cmd.description ?? "",
    });
  }
  return map;
}

/** 去掉 SKILL.md 开头的 YAML frontmatter, 返回正文 (已归一换行).
 * 复刻 pi 内置 stripFrontmatter 的 body 提取, 不引运行时依赖便于单测. */
export function stripSkillFrontmatter(content: string): string {
  const normalized = content.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  if (!normalized.startsWith("---")) return normalized;
  const endIndex = normalized.indexOf("\n---", 3);
  if (endIndex === -1) return normalized;
  return normalized.slice(endIndex + 4).trim();
}

/** 展开 text 中非整条开头的 skill token.
 * readSkill: 注入文件读取便于测试; 默认同步读盘.
 * 返回 [替换后文本, 失败的 skill 名列表]; 无任何有效替换时文本原样返回. */
export function expandSkillTokens(
  text: string,
  skills: Map<string, SkillRef>,
  readSkill: (ref: SkillRef) => string = (ref) => readFileSync(ref.filePath, "utf-8"),
): { text: string; changed: boolean; failed: string[] } {
  const failed: string[] = [];
  let changed = false;
  const result = text.replace(SKILL_TOKEN_RE, (_match, lead: string, token: string) => {
    if (lead.length === 0) return _match; // 整条开头留给内置展开
    const name = token.slice("/skill:".length);
    const ref = skills.get(name);
    if (!ref) return _match; // 未知 skill, 原样 (与内置一致)
    try {
      const body = stripSkillFrontmatter(readSkill(ref)).trim();
      changed = true;
      return (
        `${lead}<skill name="${ref.name}" location="${ref.filePath}">\n` +
        `References are relative to ${ref.baseDir}.\n\n${body}\n</skill>`
      );
    } catch {
      failed.push(name);
      return _match;
    }
  });
  return { text: result, changed, failed };
}

/** 判定光标前文本是否处于 "空白后的 /token" 补全场景 (行首除外).
 * 返回已打的 "/" 后片段 (可为空串); 非场景返回 null. */
export function inlineSlashPrefix(beforeCursor: string): string | null {
  if (atSlashLineStart(beforeCursor)) return null;
  const m = beforeCursor.match(INLINE_SLASH_RE);
  return m ? (m[1] ?? "") : null;
}

/** 简单子序列模糊匹配 (pattern 的字符按序出现在 target 中). */
export function fuzzyMatch(pattern: string, target: string): boolean {
  if (!pattern) return true;
  let i = 0;
  for (const ch of target) {
    if (ch === pattern[i]) i++;
    if (i === pattern.length) return true;
  }
  return false;
}

/** 判定光标前文本是否处于行首命令场景 (忽略缩进的 "/" 开头).
 * 行首属于内置全命令菜单, 本扩展无条件委托. */
export function atSlashLineStart(beforeCursor: string): boolean {
  return beforeCursor.trimStart().startsWith("/");
}

/** 构建补全 provider (包装 current). 导出以便单测覆盖委托/拦截路径. */
export function makeSkillAnywhereProvider(
  current: {
    getSuggestions: (lines: string[], cursorLine: number, cursorCol: number, options: { force?: boolean }) => Promise<unknown>;
    applyCompletion: (...args: unknown[]) => unknown;
    shouldTriggerFileCompletion?: (...args: unknown[]) => boolean;
  },
  getSkills: () => Map<string, SkillRef>,
) {
  return {
    triggerCharacters: ["/"],

    async getSuggestions(lines: string[], cursorLine: number, cursorCol: number, options: { force?: boolean }) {
      const line = lines[cursorLine] ?? "";
      const beforeCursor = line.slice(0, cursorCol);

      // 行首 (含缩进) 命令场景: 无条件委托内置 provider (全命令菜单).
      // 旧逻辑此处误拦: 行首 "/" 同时是 /token, 掉进自然触发的 null 分支, 菜单消失.
      if (atSlashLineStart(beforeCursor)) {
        return current.getSuggestions(lines, cursorLine, cursorCol, options);
      }

      const typed = inlineSlashPrefix(beforeCursor);
      if (typed !== null) {
        // 非行首 /token: 一律弹 skill 菜单, fuzzy 匹配命令全串 ("skill:<name>").
        // 无匹配: 自然触发关菜单 (继续输入即过滤), force 落内置文件补全.
        const skills = getSkills();
        const items = [...skills.values()]
          .filter((s) => fuzzyMatch(typed, `skill:${s.name}`))
          .map((s) => ({
            value: `skill:${s.name}`,
            label: `skill:${s.name}`,
            description: s.description || undefined,
          }));
        if (items.length > 0) return { items, prefix: `/${typed}` };
        if (options.force) return current.getSuggestions(lines, cursorLine, cursorCol, options);
        return null;
      }

      // 不在 /token 内 (如 @): 一律委托内置 provider.
      return current.getSuggestions(lines, cursorLine, cursorCol, options);
    },

    applyCompletion(lines: string[], cursorLine: number, cursorCol: number, item: { value?: unknown }, prefix: string) {
      const line = lines[cursorLine] ?? "";
      const beforeCursor = line.slice(0, cursorCol);
      const isMine =
        typeof item.value === "string" &&
        item.value.startsWith("skill:") &&
        !atSlashLineStart(beforeCursor) &&
        inlineSlashPrefix(beforeCursor) !== null;
      if (!isMine) return current.applyCompletion(lines, cursorLine, cursorCol, item, prefix);

      // 替换 "/<typed>" 为 "/skill:<name> ", 光标落在空格后 (对齐内置命令补全)
      const beforePrefix = line.slice(0, cursorCol - prefix.length);
      const afterCursor = line.slice(cursorCol);
      const newLines = [...lines];
      newLines[cursorLine] = `${beforePrefix}/${item.value} ${afterCursor}`;
      return {
        lines: newLines,
        cursorLine,
        cursorCol: beforePrefix.length + String(item.value).length + 2,
      };
    },

    shouldTriggerFileCompletion(...args: unknown[]) {
      return current.shouldTriggerFileCompletion?.(...args) ?? true;
    },
  };
}

export default function (pi: ExtensionAPI) {
  const getSkills = () => collectSkillRefs(pi.getCommands() as CommandLike[]);

  pi.on("input", async (event, ctx) => {
    if (!event.text.includes("/skill:")) return;
    const skills = getSkills();
    if (skills.size === 0) return;
    const { text, changed, failed } = expandSkillTokens(event.text, skills);
    if (failed.length > 0 && ctx.hasUI) {
      ctx.ui.notify(`[skill-anywhere] 读取 skill 失败: ${failed.join(", ")}`, "error");
    }
    if (!changed) return;
    return { action: "transform", text };
  });

  pi.on("session_start", (_event, ctx) => {
    if (ctx.mode !== "tui") return;
    ctx.ui.addAutocompleteProvider((current) =>
      makeSkillAnywhereProvider(
        current as Parameters<typeof makeSkillAnywhereProvider>[0],
        getSkills,
      ),
    );
  });
}
