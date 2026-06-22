// ponytail-instructions: reads SKILL.md, filters by intensity level,
// generates instructions for system prompt injection.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_MODE,
  normalizeMode,
  normalizePersistedMode,
  type RuntimeMode,
  type ValidMode,
} from "./config.js";

const INDEPENDENT_MODES = new Set<ValidMode>(["review"]);

// SKILL.md 位于同仓库的兄弟目录 ponytail/ponytail/SKILL.md.
// 部署时 extension 可能在任意位置, 因此同时尝试多个候选路径.
const __dirname = path.dirname(fileURLToPath(import.meta.url));

function resolveSkillPaths(): string[] {
  const candidates: string[] = [];

  // 源码布局: ponytail/pi-extension/ → ponytail/ponytail/
  candidates.push(path.resolve(__dirname, "../ponytail/SKILL.md"));

  // pi 安装布局: ~/.pi/agent/extensions/ponytail/ → ~/.pi/agent/skills/ponytail/
  candidates.push(path.resolve(__dirname, "../../skills/ponytail/SKILL.md"));

  return candidates;
}

const SKILL_PATHS = resolveSkillPaths();

export function filterSkillBodyForMode(body: string, mode: RuntimeMode): string {
  const withoutFrontmatter = body.replace(/^---[\s\S]*?---\s*/, "");

  // Only the intensity table rows and worked examples are mode-specific.
  // A line whose label is not a mode (e.g. a normal rule bullet) is kept verbatim.
  return withoutFrontmatter
    .split(/\r?\n/)
    .filter((line) => {
      const tableLabel = line.match(/^\|\s*\*\*(.+?)\*\*\s*\|/);
      if (tableLabel) {
        const labelMode = normalizeMode(tableLabel[1].trim());
        if (labelMode) return labelMode === mode;
      }

      const exampleLabel = line.match(/^-\s*([^:]+):\s*/);
      if (exampleLabel) {
        const labelMode = normalizeMode(exampleLabel[1].trim());
        if (labelMode) return labelMode === mode;
      }

      return true;
    })
    .join("\n");
}

function readSkillContent(): string | null {
  for (const skillPath of SKILL_PATHS) {
    try {
      return fs.readFileSync(skillPath, "utf8");
    } catch {
      // Try next candidate
    }
  }
  return null;
}

function getFallbackInstructions(mode: RuntimeMode): string {
  return (
    `PONYTAIL MODE ACTIVE — level: ${mode}\n\n` +
    "You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.\n\n" +
    "## Persistence\n\n" +
    'ACTIVE EVERY RESPONSE. No drift back to over-building. Still active if unsure. Off only: "stop ponytail" / "normal mode".\n\n' +
    `Current level: **${mode}**. Switch: \`/ponytail lite|full|ultra\`.\n\n` +
    "## The ladder\n\n" +
    "Before any code, stop at the first rung that holds:\n" +
    "1. Does this need to be built at all? (YAGNI)\n" +
    "2. Does the standard library do this? Use it.\n" +
    "3. Does a native platform feature cover it? Use it.\n" +
    "4. Does an already-installed dependency solve it? Use it.\n" +
    "5. Can this be one line? Make it one line.\n" +
    "6. Only then: write the minimum code that works.\n\n" +
    "## Rules\n\n" +
    "No abstractions that were not requested. No avoidable dependencies. No boilerplate nobody asked for. " +
    "Deletion over addition. Boring over clever. Fewest files possible. " +
    "Ship the lazy version and question the complex request in the same response — never stall. " +
    "Between two same-size stdlib options, pick the one correct on edge cases. " +
    "Mark intentional simplifications with a `ponytail:` comment — a shortcut with a known ceiling names the ceiling and the upgrade path in the comment.\n\n" +
    "## Output\n\n" +
    "Code first. Then at most three short lines: what was skipped, when to add it. " +
    "If the explanation is longer than the code, delete the explanation. " +
    "Explanation the user explicitly asked for is not debt, give it in full.\n\n" +
    "## When NOT to be lazy\n\n" +
    "Never simplify away: input validation at trust boundaries, error handling that prevents data loss, " +
    "security measures, accessibility basics, the calibration real hardware needs (the platform is never the spec ideal), anything the user explicitly asked to keep. " +
    "Lazy code without its check is unfinished: non-trivial logic leaves ONE runnable check behind (assert-based demo/self-check or one small test file; no frameworks). Trivial one-liners need no test.\n\n" +
    "## Boundaries\n\n" +
    'Ponytail governs what you build, not how you talk. "stop ponytail" or "normal mode": revert. Level persists until changed or session end.'
  );
}

export function getPonytailInstructions(mode: ValidMode): string {
  const configuredMode = normalizePersistedMode(mode) ?? DEFAULT_MODE;

  if (INDEPENDENT_MODES.has(configuredMode)) {
    return `PONYTAIL MODE ACTIVE — level: ${configuredMode}. Behavior defined by /ponytail-${configuredMode} skill.`;
  }

  const effectiveMode = normalizeMode(configuredMode) ?? DEFAULT_MODE;

  const content = readSkillContent();
  if (content) {
    return (
      `PONYTAIL MODE ACTIVE — level: ${effectiveMode}\n\n` +
      filterSkillBodyForMode(content, effectiveMode)
    );
  }

  return getFallbackInstructions(effectiveMode);
}
