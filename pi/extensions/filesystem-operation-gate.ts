import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";
import { existsSync } from "node:fs";
import { realpath } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * filesystem-operation-gate: 仅在工具明确写入 ctx.cwd 外时要求用户确认.
 *
 * 不拦截读取操作.
 * 不拦截对当前系统临时目录或其子路径的写入; 但以临时目录根本身为目标的删除类操作仍需确认.
 * 路径感知写入工具 (`write`, `edit`) 仅在目标路径解析到 ctx.cwd 外时拦截.
 * Bash 仅在静态识别出 ctx.cwd 外的明确写入目标时拦截.
 * 对含义不明确的 shell 命令不作保守拦截.
 */

const WRITE_TOOL_NAMES = new Set(["write", "edit"]);
const SEARCH_COMMAND_NAMES = new Set([
  "grep",
  "egrep",
  "fgrep",
  "rg",
  "ripgrep",
  "ag",
  "ack",
  "find",
  "fd",
  "fdfind",
  "locate",
]);
const rememberedOutsideDirectories = new Set<string>();
const fakedNullWrites = new Set<string>();

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    const rawPath = WRITE_TOOL_NAMES.has(event.toolName) ? getToolPath(event.input) : undefined;
    const fakedPath = rawPath && isNullFilename(rawPath)
      ? rawPath
      : isToolCallEventType("bash", event) ? findNullWriteTarget(event.input.command ?? "") : undefined;
    if (fakedPath) {
      fakedNullWrites.add(event.toolCallId);
      return { block: true, reason: `已忽略 Windows NUL 文件写入: ${fakedPath}` };
    }

    if (WRITE_TOOL_NAMES.has(event.toolName)) {
      if (!rawPath) return;

      const target = await resolvePolicyPath(rawPath, ctx.cwd);
      const root = await resolvePolicyPath(ctx.cwd, ctx.cwd);
      if (isInsideOrSame(root, target)) return;
      if (await isTemporaryDirectoryChild(target, ctx.cwd)) return;
      if (await isTemporaryDirectoryRoot(target, ctx.cwd)) return;

      const rememberDirectory = path.dirname(target);
      if (isRememberedOutsideDirectory(rememberDirectory)) return;

      return await confirmOrBlock(ctx, {
        title: "当前工作目录外写入确认",
        subject: `工具: ${event.toolName}\n操作: write\n当前工作目录: ${root}\n目标路径: ${target}\n原始路径: ${rawPath}`,
        reason: "该操作会写入当前工作目录外的内容.",
        blockReason: `用户拒绝 ${event.toolName} 写入当前工作目录外路径: ${target}`,
        rememberDirectory,
      });
    }

    if (isToolCallEventType("bash", event)) {
      const command = event.input.command ?? "";

      const wholeSearches = findWholeFilesystemSearchTargets(command, ctx.cwd);
      if (wholeSearches.length > 0) {
        const root = await resolvePolicyPath(ctx.cwd, ctx.cwd);
        return await confirmOrBlock(ctx, {
          title: "全盘搜索确认",
          subject: `命令: ${command}\n当前工作目录: ${root}\n全盘搜索根:\n${wholeSearches.flatMap((search) => search.roots.map((rootPath) => `- ${search.command}: ${rootPath}`)).join("\n")}`,
          reason: "该命令会在整台电脑的文件系统中搜索内容, 可能耗时很长并产生大量输出.",
          blockReason: `用户拒绝全盘搜索: ${wholeSearches.map((search) => `${search.command} -> ${search.roots.join(", ")}`).join("; ")}`,
        });
      }

      const outsideTargets = findObviousOutsideWriteTargets(command, ctx.cwd);
      if (outsideTargets.length === 0) return;

      const pendingTargets = [] as OutsideWriteTarget[];
      for (const target of outsideTargets) {
        if (isRememberedOutsideDirectory(path.dirname(target.resolved))) continue;
        if (await isTemporaryDirectoryChild(target.resolved, ctx.cwd)) continue;
        if (!target.destructive && await isTemporaryDirectoryRoot(target.resolved, ctx.cwd)) continue;
        pendingTargets.push(target);
      }
      if (pendingTargets.length === 0) return;

      const root = await resolvePolicyPath(ctx.cwd, ctx.cwd);
      const rememberDirectory = getCommonDirectory(pendingTargets.map((target) => path.dirname(target.resolved)));
      return await confirmOrBlock(ctx, {
        title: "bash 当前工作目录外写入确认",
        subject: `命令: ${command}\n当前工作目录: ${root}\n明确识别到的 cwd 外写入目标:\n${pendingTargets.map((target) => `- ${target.raw} -> ${target.resolved}`).join("\n")}`,
        reason: "bash 命令明确包含写入当前工作目录外的目标.",
        blockReason: `用户拒绝 bash 写入当前工作目录外目标: ${pendingTargets.map((target) => target.resolved).join(", ")}`,
        rememberDirectory,
      });
    }
  });

  pi.on("tool_result", (event) => {
    if (!fakedNullWrites.delete(event.toolCallId)) return;
    return {
      content: [{ type: "text", text: "操作成功." }],
      details: {},
      isError: false,
    };
  });
}

function isNullFilename(rawPath: string): boolean {
  return path.basename(normalizePath(rawPath)).toLowerCase() === "nul";
}

function findNullWriteTarget(command: string): string | undefined {
  const tokens = tokenizeShell(command);
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (!token) continue;
    if (!token.quoted && isOutputRedirect(token.text)) {
      const target = tokens[i + 1]?.text;
      if (target && isNullFilename(target)) return target;
    }
  }

  const commandView = unwrapCommand(getCommandWords(tokens));
  if (commandView?.command !== "touch") return undefined;
  return getNonOptionArgs(commandView.args).find((arg) => isNullFilename(arg.text))?.text;
}

function isRememberedOutsideDirectory(directory: string): boolean {
  const normalizedDirectory = normalizeForCompare(path.resolve(directory));
  return [...rememberedOutsideDirectories].some((remembered) => isInsideOrSame(remembered, normalizedDirectory));
}

function rememberOutsideDirectory(directory: string): void {
  rememberedOutsideDirectories.add(normalizeForCompare(path.resolve(directory)));
}

function getCommonDirectory(directories: string[]): string | undefined {
  const [first, ...rest] = directories.map((directory) => path.resolve(directory));
  if (!first) return undefined;

  let common = first;
  for (const directory of rest) {
    while (!isInsideOrSame(common, directory)) {
      const parent = path.dirname(common);
      if (parent === common) return undefined;
      common = parent;
    }
  }
  return common;
}

function getToolPath(input: unknown): string | undefined {
  if (!input || typeof input !== "object") return undefined;
  const value = (input as { path?: unknown; file_path?: unknown }).path ?? (input as { file_path?: unknown }).file_path;
  if (typeof value !== "string" || value.trim() === "") return ".";
  return value;
}

async function confirmOrBlock(
  ctx: {
    hasUI: boolean;
    ui: {
      confirm(title: string, message: string): Promise<boolean>;
      select(title: string, options: string[]): Promise<string | undefined>;
      input(title: string, placeholder?: string): Promise<string | undefined>;
    };
  },
  options: { title: string; subject: string; reason: string; blockReason: string; rememberDirectory?: string },
) {
  if (!ctx.hasUI) {
    return { block: true, reason: `${options.blockReason}. 无 UI 可确认.` };
  }

  const prompt = `${options.title}\n\n${options.subject}\n\n${options.reason}`;

  const withUserReason = async (): Promise<{ block: true; reason: string }> => {
    const detail = await ctx.ui.input(prompt, "输入返回给 AI 的拦截理由 (留空则普通拒绝)");
    const reason = detail?.trim()
      ? `${options.blockReason}\n并给你发来回复: ${detail.trim()}`
      : options.blockReason;
    return { block: true, reason };
  };

  if (!options.rememberDirectory) {
    const choice = await ctx.ui.select(prompt, ["允许", "拒绝", "拒绝并说明理由"]);
    if (choice === "允许") return undefined;
    if (choice === "拒绝并说明理由") return withUserReason();
    return { block: true, reason: options.blockReason };
  }

  const choice = await ctx.ui.select(
    prompt,
    [
      "允许一次",
      `允许并不再询问此目录: ${options.rememberDirectory}`,
      "拒绝",
      "拒绝并说明理由",
    ],
  );

  if (choice === "允许一次") return undefined;
  if (choice?.startsWith("允许并不再询问此目录:")) {
    rememberOutsideDirectory(options.rememberDirectory);
    return undefined;
  }
  if (choice === "拒绝并说明理由") return withUserReason();
  return { block: true, reason: options.blockReason };
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

async function isTemporaryDirectoryChild(target: string, cwd: string): Promise<boolean> {
  const temporaryDirectory = await resolvePolicyPath(tmpdir(), cwd);
  if (isFilesystemRoot(temporaryDirectory)) return false;

  const resolvedTarget = await resolvePolicyPath(target, cwd);
  return !isSamePath(temporaryDirectory, resolvedTarget) && isInsideOrSame(temporaryDirectory, resolvedTarget);
}

async function isTemporaryDirectoryRoot(target: string, cwd: string): Promise<boolean> {
  const temporaryDirectory = await resolvePolicyPath(tmpdir(), cwd);
  if (isFilesystemRoot(temporaryDirectory)) return false;

  const resolvedTarget = await resolvePolicyPath(target, cwd);
  return isSamePath(temporaryDirectory, resolvedTarget);
}

function isFilesystemRoot(value: string): boolean {
  const normalized = normalizeForCompare(path.resolve(value));
  return normalized === normalizeForCompare(path.parse(normalized).root);
}

function isSamePath(left: string, right: string): boolean {
  return normalizeForCompare(path.resolve(left)) === normalizeForCompare(path.resolve(right));
}

function normalizeForCompare(value: string): string {
  const normalized = path.normalize(value);
  return process.platform === "win32" ? normalized.toLowerCase() : normalized;
}

type ShellToken = {
  text: string;
  quoted: boolean;
};

type OutsideWriteTarget = {
  raw: string;
  resolved: string;
  destructive: boolean;
};

type WholeFilesystemSearch = {
  command: string;
  roots: string[];
};

type SegmentInspection = {
  outsideTargets: OutsideWriteTarget[];
  searches: WholeFilesystemSearch[];
  nextCwd?: string;
};

const COMMAND_BOUNDARIES = new Set(["&&", "||", ";", "|", "(", ")"]);
const OUTPUT_REDIRECTS = new Set([">", ">>", "&>", ">|", "<>"]);
const INPUT_REDIRECTS = new Set(["<", "<<", "<<<"]);

function findObviousOutsideWriteTargets(command: string, cwd: string): OutsideWriteTarget[] {
  const root = path.resolve(normalizePath(cwd));
  let currentDir = root;
  const tokens = tokenizeShell(command);
  const outsideTargets = new Map<string, OutsideWriteTarget>();
  let segment: ShellToken[] = [];

  const flushSegment = (allowCwdUpdate: boolean) => {
    const inspection = inspectCommandSegment(segment, currentDir, root);
    for (const target of inspection.outsideTargets) outsideTargets.set(target.resolved, target);
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

  return [...outsideTargets.values()];
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
  const outsideTargets = new Map<string, OutsideWriteTarget>();
  const searches = new Map<string, WholeFilesystemSearch>();

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
  if (!commandView) return { outsideTargets: [...outsideTargets.values()], searches: [...searches.values()] };

  const { command, args } = commandView;
  addCommandWriteTargets(command, args, currentDir, root, outsideTargets);
  addWholeFilesystemSearch(command, args, currentDir, searches);

  if (command === "cd") {
    const nextCwd = resolveCdTarget(args, currentDir);
    return { outsideTargets: [...outsideTargets.values()], searches: [...searches.values()], nextCwd };
  }

  return { outsideTargets: [...outsideTargets.values()], searches: [...searches.values()] };
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
  outsideTargets: Map<string, OutsideWriteTarget>,
): void {
  switch (command) {
    case "rm":
    case "unlink":
    case "rmdir":
      for (const arg of getNonOptionArgs(args)) addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets, true);
      return;

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
      if (args.some((arg) => arg.text === "-delete")) addFindSearchRoots(args, currentDir, root, outsideTargets, true);
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
  outsideTargets: Map<string, OutsideWriteTarget>,
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
  outsideTargets: Map<string, OutsideWriteTarget>,
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
  outsideTargets: Map<string, OutsideWriteTarget>,
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
  outsideTargets: Map<string, OutsideWriteTarget>,
  destructive = false,
): void {
  const roots: ShellToken[] = [];
  for (const arg of args) {
    if (arg.text.startsWith("-")) break;
    roots.push(arg);
  }

  for (const arg of roots.length > 0 ? roots : [{ text: ".", quoted: false }]) {
    addOutsideWriteTarget(arg.text, currentDir, root, outsideTargets, destructive);
  }
}

function addTarArchiveTarget(
  args: ShellToken[], currentDir: string, root: string, outsideTargets: Map<string, OutsideWriteTarget>): void {
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

function findWholeFilesystemSearchTargets(command: string, cwd: string): WholeFilesystemSearch[] {
  const root = path.resolve(normalizePath(cwd));
  let currentDir = root;
  const tokens = tokenizeShell(command);
  const searches = new Map<string, WholeFilesystemSearch>();
  let segment: ShellToken[] = [];

  const flushSegment = (allowCwdUpdate: boolean) => {
    const inspection = inspectCommandSegment(segment, currentDir, root);
    for (const search of inspection.searches) searches.set(search.command, search);
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

  return [...searches.values()];
}

function addWholeFilesystemSearch(
  command: string,
  args: ShellToken[],
  currentDir: string,
  searches: Map<string, WholeFilesystemSearch>,
): void {
  if (!SEARCH_COMMAND_NAMES.has(command)) return;

  if (command === "locate") {
    searches.set("locate", { command, roots: [process.platform === "win32" ? "\\\\" : "/"] });
    return;
  }

  const roots = getSearchRoots(command, args, currentDir);
  const wholeRoots = roots.filter((resolved) => isWholeFilesystemRoot(resolved));
  if (wholeRoots.length > 0) searches.set(command, { command, roots: wholeRoots });
}

function getSearchRoots(command: string, args: ShellToken[], currentDir: string): string[] {
  if (command === "find") {
    const roots: string[] = [];
    for (const arg of args) {
      if (!arg.quoted && arg.text.startsWith("-")) break;
      roots.push(resolveShellPath(arg.text, currentDir));
    }
    return roots.length > 0 ? roots : [resolveShellPath(".", currentDir)];
  }

  const operands = getNonOptionArgs(args);
  return operands.slice(1).map((arg) => resolveShellPath(arg.text, currentDir));
}

function isWholeFilesystemRoot(resolvedPath: string): boolean {
  const normalized = normalizeForCompare(path.resolve(resolvedPath));
  if (process.platform === "win32") return /^[a-z]:\\$/.test(normalized);
  return normalized === "/";
}

function resolveCdTarget(args: ShellToken[], currentDir: string): string | undefined {
  const operands = getNonOptionArgs(args);
  const target = operands[0]?.text ?? "~";
  if (target === "-") return undefined;
  return resolveShellPath(target, currentDir);
}

function addOutsideWriteTarget(
  rawPath: string,
  currentDir: string,
  root: string,
  outsideTargets: Map<string, OutsideWriteTarget>,
  destructive = false,
): void {
  const cleaned = cleanShellPath(rawPath);
  if (!cleaned || isFdTarget(cleaned) || isSpecialDevicePath(cleaned)) return;

  const resolved = resolveShellPath(cleaned, currentDir);
  if (!isInsideOrSame(root, resolved)) {
    const existing = outsideTargets.get(resolved);
    outsideTargets.set(resolved, { raw: cleaned, resolved, destructive: (existing?.destructive ?? false) || destructive });
  }
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
