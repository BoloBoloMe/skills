import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";
import { existsSync } from "node:fs";
import { realpath } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * outside-cwd-consent: require user consent before tools access paths outside ctx.cwd.
 *
 * Covered path-aware tools:
 * - read, ls, grep, find: read access
 * - write, edit: write access
 *
 * Bash is guarded conservatively by default because a shell command can read or write
 * arbitrary paths that cannot be proven from the command string. Set
 * PI_OUTSIDE_CWD_GUARD_BASH=0 to only warn on obvious outside path tokens.
 */

const PATH_TOOL_ACTION: Record<string, "read" | "write"> = {
  read: "read",
  ls: "read",
  grep: "read",
  find: "read",
  write: "write",
  edit: "write",
};

const STRICT_BASH = process.env.PI_OUTSIDE_CWD_GUARD_BASH !== "0";

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    const pathAction = PATH_TOOL_ACTION[event.toolName];
    if (pathAction) {
      const rawPath = getToolPath(event.input);
      if (!rawPath) return;

      const target = await resolvePolicyPath(rawPath, ctx.cwd);
      const root = await resolvePolicyPath(ctx.cwd, ctx.cwd);
      if (isInsideOrSame(root, target)) return;

      return await confirmOrBlock(ctx, {
        title: "当前工作目录外访问确认",
        subject: `工具: ${event.toolName}\n操作: ${pathAction}\n当前工作目录: ${root}\n目标路径: ${target}\n原始路径: ${rawPath}`,
        reason: "该操作会访问当前工作目录外的内容.",
        blockReason: `用户拒绝 ${event.toolName} 访问当前工作目录外路径: ${target}`,
      });
    }

    if (isToolCallEventType("bash", event)) {
      const command = event.input.command ?? "";
      const outsideTokens = findObviousOutsidePathTokens(command, ctx.cwd);
      if (!STRICT_BASH && outsideTokens.length === 0) return;

      return await confirmOrBlock(ctx, {
        title: "bash 访问确认",
        subject: STRICT_BASH
          ? `命令: ${command}\n当前工作目录: ${ctx.cwd}`
          : `命令: ${command}\n当前工作目录: ${ctx.cwd}\n疑似外部路径: ${outsideTokens.join(", ")}`,
        reason: STRICT_BASH
          ? "bash 命令可能读写当前工作目录外的内容, 静态检查无法可靠证明其访问范围."
          : "bash 命令包含疑似当前工作目录外的路径.",
        blockReason: "用户拒绝 bash 访问确认",
      });
    }
  });
}

function getToolPath(input: unknown): string | undefined {
  if (!input || typeof input !== "object") return undefined;
  const value = (input as { path?: unknown }).path;
  if (typeof value !== "string" || value.trim() === "") return ".";
  return value;
}

async function confirmOrBlock(
  ctx: { hasUI: boolean; ui: { confirm(title: string, message: string): Promise<boolean> } },
  options: { title: string; subject: string; reason: string; blockReason: string },
) {
  if (!ctx.hasUI) {
    return { block: true, reason: `${options.blockReason}. 无 UI 可确认.` };
  }

  const ok = await ctx.ui.confirm(
    options.title,
    `${options.subject}\n\n${options.reason}\n是否允许?`,
  );
  if (!ok) return { block: true, reason: options.blockReason };
  return undefined;
}

async function resolvePolicyPath(rawPath: string, cwd: string): Promise<string> {
  const absolutePath = path.resolve(normalizePath(cwd), normalizePath(rawPath));
  return await realpathNearest(absolutePath);
}

function normalizePath(input: string): string {
  let normalized = input.replace(/[\u00A0\u2000-\u200A\u202F\u205F\u3000]/g, " ");
  if (normalized.startsWith("@")) normalized = normalized.slice(1);
  if (normalized === "~") return homedir();
  if (normalized.startsWith("~/") || (process.platform === "win32" && normalized.startsWith("~\\"))) {
    return path.join(homedir(), normalized.slice(2));
  }
  if (normalized.startsWith("file://")) return fileURLToPath(normalized);
  return normalized;
}

async function realpathNearest(absolutePath: string): Promise<string> {
  const missingParts: string[] = [];
  let current = path.resolve(absolutePath);

  while (!existsSync(current)) {
    const parent = path.dirname(current);
    if (parent === current) return path.resolve(absolutePath);
    missingParts.push(path.basename(current));
    current = parent;
  }

  const realBase = await realpath(current).catch(() => current);
  return missingParts.reverse().reduce((base, part) => path.join(base, part), realBase);
}

function isInsideOrSame(root: string, target: string): boolean {
  const normalizedRoot = normalizeForCompare(path.resolve(root));
  const normalizedTarget = normalizeForCompare(path.resolve(target));
  const relative = path.relative(normalizedRoot, normalizedTarget);
  return (
    relative === "" ||
    (!!relative && relative !== ".." && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative))
  );
}

function normalizeForCompare(value: string): string {
  const normalized = path.normalize(value);
  return process.platform === "win32" ? normalized.toLowerCase() : normalized;
}

function findObviousOutsidePathTokens(command: string, cwd: string): string[] {
  const root = path.resolve(normalizePath(cwd));
  const tokens = command.match(/(?:[A-Za-z]:[\\/][^\s"'`]+|~(?:[\\/][^\s"'`]+)?|\.\.[\\/][^\s"'`]*|\/[A-Za-z0-9._~+-][^\s"'`]*)/g) ?? [];
  const outside = new Set<string>();

  for (const token of tokens) {
    const resolved = path.resolve(root, normalizePath(token));
    if (!isInsideOrSame(root, resolved)) outside.add(token);
  }

  return [...outside];
}
