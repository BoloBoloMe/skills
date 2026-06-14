import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";
import { existsSync } from "node:fs";
import { realpath } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * outside-cwd-consent: require user consent only before tools clearly write outside ctx.cwd.
 *
 * Read operations are not gated.
 * Path-aware write tools (write, edit) are gated only when the target path resolves outside ctx.cwd.
 * Bash is gated only when an obvious write target outside ctx.cwd is statically identified.
 * Ambiguous shell commands are allowed instead of being conservatively blocked.
 */

const WRITE_TOOL_NAMES = new Set(["write", "edit"]);

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (WRITE_TOOL_NAMES.has(event.toolName)) {
      const rawPath = getToolPath(event.input);
      if (!rawPath) return;

      const target = await resolvePolicyPath(rawPath, ctx.cwd);
      const root = await resolvePolicyPath(ctx.cwd, ctx.cwd);
      if (isInsideOrSame(root, target)) return;

      return await confirmOrBlock(ctx, {
        title: "当前工作目录外写入确认",
        subject: `工具: ${event.toolName}\n操作: write\n当前工作目录: ${root}\n目标路径: ${target}\n原始路径: ${rawPath}`,
        reason: "该操作会写入当前工作目录外的内容.",
        blockReason: `用户拒绝 ${event.toolName} 写入当前工作目录外路径: ${target}`,
      });
    }

    if (isToolCallEventType("bash", event)) {
      const command = event.input.command ?? "";
      const outsideTargets = findObviousOutsideWriteTargets(command, ctx.cwd);
      if (outsideTargets.length === 0) return;

      const root = await resolvePolicyPath(ctx.cwd, ctx.cwd);
      return await confirmOrBlock(ctx, {
        title: "bash 当前工作目录外写入确认",
        subject: `命令: ${command}\n当前工作目录: ${root}\n明确识别到的 cwd 外写入目标:\n${outsideTargets.map((target) => `- ${target}`).join("\n")}`,
        reason: "bash 命令明确包含写入当前工作目录外的目标.",
        blockReason: `用户拒绝 bash 写入当前工作目录外目标: ${outsideTargets.join(", ")}`,
      });
    }
  });
}

function getToolPath(input: unknown): string | undefined {
  if (!input || typeof input !== "object") return undefined;
  const value = (input as { path?: unknown; file_path?: unknown }).path ?? (input as { file_path?: unknown }).file_path;
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

type ShellToken = {
  text: string;
  quoted: boolean;
};

type SegmentInspection = {
  outsideTargets: string[];
  nextCwd?: string;
};

const COMMAND_BOUNDARIES = new Set(["&&", "||", ";", "|", "(", ")"]);
const OUTPUT_REDIRECTS = new Set([">", ">>", "&>", ">|", "<>"]);
const INPUT_REDIRECTS = new Set(["<", "<<", "<<<"]);

function findObviousOutsideWriteTargets(command: string, cwd: string): string[] {
  const root = path.resolve(normalizePath(cwd));
  let currentDir = root;
  const tokens = tokenizeShell(command);
  const outsideTargets = new Set<string>();
  let segment: ShellToken[] = [];

  const flushSegment = (allowCwdUpdate: boolean) => {
    const inspection = inspectCommandSegment(segment, currentDir, root);
    for (const target of inspection.outsideTargets) outsideTargets.add(target);
    if (allowCwdUpdate && inspection.nextCwd) currentDir = inspection.nextCwd;
    segment = [];
  };

  for (const token of tokens) {
    if (!token.quoted && COMMAND_BOUNDARIES.has(token.text)) {
      flushSegment(token.text !== "|" && token.text !== "(" && token.text !== ")");
      continue;
    }
    segment.push(token);
  }
  flushSegment(true);

  return [...outsideTargets];
}

function tokenizeShell(command: string): ShellToken[] {
  const tokens: ShellToken[] = [];
  let current = "";
  let quoted = false;
  let quote: "'" | '"' | "`" | undefined;

  const flush = () => {
    if (current === "") return;
    tokens.push({ text: current, quoted });
    current = "";
    quoted = false;
  };

  for (let i = 0; i < command.length; i++) {
    const ch = command[i];

    if (quote) {
      if (ch === "\\" && quote !== "'" && i + 1 < command.length) {
        current += command[i + 1];
        quoted = true;
        i++;
        continue;
      }
      if (ch === quote) {
        quote = undefined;
        quoted = true;
        continue;
      }
      current += ch;
      quoted = true;
      continue;
    }

    if (ch === "'" || ch === '"' || ch === "`") {
      quote = ch;
      quoted = true;
      continue;
    }

    if (/\s/.test(ch)) {
      flush();
      continue;
    }

    const three = command.slice(i, i + 3);
    if (three === "<<<") {
      flush();
      tokens.push({ text: three, quoted: false });
      i += 2;
      continue;
    }

    const two = command.slice(i, i + 2);
    if (["&&", "||", ">>", "&>", ">|", "<>", "<<", ";;"].includes(two)) {
      flush();
      tokens.push({ text: two, quoted: false });
      i++;
      continue;
    }

    if ([";", "|", ">", "<", "(", ")"].includes(ch)) {
      flush();
      tokens.push({ text: ch, quoted: false });
      continue;
    }

    current += ch;
  }

  flush();
  return tokens;
}

function inspectCommandSegment(segment: ShellToken[], currentDir: string, root: string): SegmentInspection {
  const outsideTargets = new Set<string>();

  for (let i = 0; i < segment.length; i++) {
    const token = segment[i];
    if (!token) continue;
    if (token.quoted || !isOutputRedirect(token.text)) continue;

    const target = segment[i + 1];
    if (target) addOutsideWriteTarget(target.text, currentDir, root, outsideTargets);
    i++;
  }

  const words = getCommandWords(segment);
  const commandView = unwrapCommand(words);
  if (!commandView) return { outsideTargets: [...outsideTargets] };

  const { command, args } = commandView;
  addCommandWriteTargets(command, args, currentDir, root, outsideTargets);

  if (command === "cd") {
    const nextCwd = resolveCdTarget(args, currentDir);
    return { outsideTargets: [...outsideTargets], nextCwd };
  }

  return { outsideTargets: [...outsideTargets] };
}

function getCommandWords(segment: ShellToken[]): ShellToken[] {
  const words: ShellToken[] = [];

  for (let i = 0; i < segment.length; i++) {
    const token = segment[i];
    if (!token) continue;

    if (!token.quoted && isAnyRedirect(token.text)) {
      i++;
      continue;
    }

    if (words.length === 0 && isEnvAssignment(token.text)) continue;
    words.push(token);
  }

  return words;
}

function unwrapCommand(words: ShellToken[]): { command: string; args: ShellToken[] } | undefined {
  let index = 0;

  while (index < words.length) {
    while (words[index] && isEnvAssignment(words[index].text)) index++;
    const token = words[index];
    if (!token) return undefined;

    const command = normalizeCommandName(token.text);
    if (command === "env") {
      index++;
      while (words[index] && (isEnvAssignment(words[index].text) || words[index].text.startsWith("-"))) index++;
      continue;
    }

    if (command === "sudo" || command === "doas") {
      index++;
      while (words[index]?.text.startsWith("-")) {
        const option = words[index]?.text;
        index++;
        if (option === "-u" || option === "-g" || option === "-h" || option === "-p") index++;
      }
      continue;
    }

    if (["command", "builtin", "exec", "nohup", "time"].includes(command)) {
      index++;
      continue;
    }

    return { command, args: words.slice(index + 1) };
  }

  return undefined;
}

function normalizeCommandName(command: string): string {
  return path.basename(command).replace(/\.exe$/i, "").toLowerCase();
}

function isAnyRedirect(token: string): boolean {
  return isOutputRedirect(token) || INPUT_REDIRECTS.has(token);
}

function isOutputRedirect(token: string): boolean {
  return OUTPUT_REDIRECTS.has(token) || /^\d*(?:>>?|>\||<>|&>)$/.test(token);
}

function isEnvAssignment(token: string): boolean {
  return /^[A-Za-z_][A-Za-z0-9_]*=.*/.test(token);
}

function addCommandWriteTargets(
  command: string,
  args: ShellToken[],
  currentDir: string,
  root: string,
  outsideTargets: Set<string>,
): void {
  switch (command) {
    case "rm":
    case "unlink":
    case "rmdir":
    case "touch":
    case "mkdir":
      for (const arg of getNonOptionArgs(args)) addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets);
      return;

    case "mv":
      addOptionValueTargets(args, currentDir, root, outsideTargets, new Set(["-t", "--target-directory"]));
      for (const arg of getNonOptionArgs(args, new Set(["-t", "--target-directory"]))) {
        addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets);
      }
      return;

    case "cp":
    case "install":
      addOptionValueTargets(args, currentDir, root, outsideTargets, new Set(["-t", "--target-directory"]));
      addLastOperandTarget(args, currentDir, root, outsideTargets, new Set(["-t", "--target-directory"]));
      return;

    case "tee":
      for (const arg of getNonOptionArgs(args)) addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets);
      return;

    case "chmod":
    case "chown":
    case "chgrp": {
      const operands = getNonOptionArgs(args);
      for (const arg of operands.slice(1)) addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets);
      return;
    }

    case "sed":
      if (hasSedInPlaceOption(args)) addExistingPathOperands(args, currentDir, root, outsideTargets);
      return;

    case "perl":
      if (hasPerlInPlaceOption(args)) addExistingPathOperands(args, currentDir, root, outsideTargets);
      return;

    case "find":
      if (args.some((arg) => arg.text === "-delete")) addFindSearchRoots(args, currentDir, root, outsideTargets);
      return;

    case "dd":
      for (const arg of args) {
        if (arg.text.startsWith("of=")) addOutsideWriteTarget(arg.text.slice(3), currentDir, root, outsideTargets);
      }
      return;

    case "zip": {
      const operands = getNonOptionArgs(args);
      if (operands[0]) addOutsideWriteTarget(operands[0].text, currentDir, root, outsideTargets);
      return;
    }

    case "tar":
      addTarArchiveTarget(args, currentDir, root, outsideTargets);
      return;
  }
}

function getNonOptionArgs(args: ShellToken[], optionValueNames: Set<string> = new Set()): ShellToken[] {
  const result: ShellToken[] = [];
  let endOfOptions = false;

  for (let i = 0; i < args.length; i++) {
    const text = args[i]?.text ?? "";
    if (!endOfOptions && text === "--") {
      endOfOptions = true;
      continue;
    }

    if (!endOfOptions && text.startsWith("-") && text !== "-") {
      const optionName = text.includes("=") ? text.slice(0, text.indexOf("=")) : text;
      if (optionValueNames.has(optionName) && !text.includes("=")) i++;
      continue;
    }

    const arg = args[i];
    if (arg) result.push(arg);
  }

  return result;
}

function addOptionValueTargets(
  args: ShellToken[],
  currentDir: string,
  root: string,
  outsideTargets: Set<string>,
  optionValueNames: Set<string>,
): void {
  for (let i = 0; i < args.length; i++) {
    const text = args[i]?.text ?? "";
    const equalIndex = text.indexOf("=");
    const optionName = equalIndex >= 0 ? text.slice(0, equalIndex) : text;
    if (!optionValueNames.has(optionName)) continue;

    const target = equalIndex >= 0 ? text.slice(equalIndex + 1) : args[i + 1]?.text;
    if (target) addOutsideWriteTarget(target, currentDir, root, outsideTargets);
    if (equalIndex < 0) i++;
  }
}

function addLastOperandTarget(
  args: ShellToken[],
  currentDir: string,
  root: string,
  outsideTargets: Set<string>,
  optionValueNames: Set<string> = new Set(),
): void {
  const operands = getNonOptionArgs(args, optionValueNames);
  const last = operands[operands.length - 1];
  if (last) addOutsideWriteTarget(last.text, currentDir, root, outsideTargets);
}

function hasSedInPlaceOption(args: ShellToken[]): boolean {
  return args.some((arg) => arg.text === "-i" || arg.text.startsWith("-i") || arg.text === "--in-place" || arg.text.startsWith("--in-place="));
}

function hasPerlInPlaceOption(args: ShellToken[]): boolean {
  return args.some((arg) => arg.text === "-i" || arg.text.startsWith("-i") || /^-[A-Za-z]*i/.test(arg.text));
}

function addExistingPathOperands(
  args: ShellToken[],
  currentDir: string,
  root: string,
  outsideTargets: Set<string>,
): void {
  for (const arg of getNonOptionArgs(args)) {
    const resolved = resolveShellPath(arg.text, currentDir);
    if (existsSync(resolved)) addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets);
  }
}

function addFindSearchRoots(
  args: ShellToken[],
  currentDir: string,
  root: string,
  outsideTargets: Set<string>,
): void {
  const roots: ShellToken[] = [];
  for (const arg of args) {
    if (arg.text.startsWith("-")) break;
    roots.push(arg);
  }

  for (const arg of roots.length > 0 ? roots : [{ text: ".", quoted: false }]) {
    addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets);
  }
}

function addTarArchiveTarget(
  args: ShellToken[], currentDir: string, root: string, outsideTargets: Set<string>): void {
  const writesArchive = args.some((arg) => {
    const text = arg.text;
    return (
      text === "--create" ||
      text === "--append" ||
      text === "--update" ||
      (/^-[^-]/.test(text) && /[cru]/.test(text))
    );
  });
  if (!writesArchive) return;

  for (let i = 0; i < args.length; i++) {
    const text = args[i]?.text ?? "";
    if (text === "-f" || text === "--file") {
      const target = args[i + 1]?.text;
      if (target) addOutsideWriteTarget(target, currentDir, root, outsideTargets);
      return;
    }
    if (text.startsWith("--file=")) {
      addOutsideWriteTarget(text.slice("--file=".length), currentDir, root, outsideTargets);
      return;
    }
    if (/^-[^-]*f/.test(text)) {
      const target = args[i + 1]?.text;
      if (target) addOutsideWriteTarget(target, currentDir, root, outsideTargets);
      return;
    }
  }
}

function resolveCdTarget(args: ShellToken[], currentDir: string): string | undefined {
  const operands = getNonOptionArgs(args);
  const target = operands[0]?.text ?? "~";
  if (target === "-") return undefined;
  return resolveShellPath(target, currentDir);
}

function addOutsideWriteTarget(rawPath: string, currentDir: string, root: string, outsideTargets: Set<string>): void {
  const cleaned = cleanShellPath(rawPath);
  if (!cleaned || isFdTarget(cleaned) || isSpecialDevicePath(cleaned)) return;

  const resolved = resolveShellPath(cleaned, currentDir);
  if (!isInsideOrSame(root, resolved)) outsideTargets.add(`${cleaned} -> ${resolved}`);
}

function resolveShellPath(rawPath: string, currentDir: string): string {
  return path.resolve(currentDir, normalizePath(rawPath));
}

function cleanShellPath(rawPath: string): string {
  let cleaned = rawPath.trim();
  if (cleaned.startsWith("--")) return "";
  if (cleaned.endsWith(",") || cleaned.endsWith(";")) cleaned = cleaned.slice(0, -1);
  return cleaned;
}

function isFdTarget(value: string): boolean {
  return /^&?\d+$/.test(value) || value === "-";
}

function isSpecialDevicePath(value: string): boolean {
  const normalized = value.replace(/\\/g, "/").toLowerCase();
  return (
    normalized === "nul" ||
    normalized === "/dev/null" ||
    normalized === "/dev/stdout" ||
    normalized === "/dev/stderr" ||
    normalized.startsWith("/dev/fd/")
  );
}
