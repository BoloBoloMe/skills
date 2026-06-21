import { CONFIG_DIR_NAME, type ExtensionAPI, type ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { readdir, readFile, stat } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";

const SKILL_NAME_PATTERN = /^[a-z0-9-]{1,64}$/;

const RESOLVE_SKILL_PARAMS = Type.Object({
	name: Type.String({
		description: "Skill frontmatter name",
		pattern: "^[a-z0-9-]{1,64}$",
	}),
});

type ResolveSkillParams = {
	name: string;
};

type SkillRoot = {
	dir: string;
	includeRootMarkdown: boolean;
};

type SkillMetadata = {
	name?: string;
	description?: string;
	disableModelInvocation?: boolean;
};

type SkillMatch = {
	filePath: string;
	root: string;
	metadata: SkillMetadata;
};

export default function resolveSkillExtension(pi: ExtensionAPI) {
	pi.registerTool({
		name: "resolve_skill",
		label: "Resolve Skill",
		description: "根据 frontmatter name 查询未知 skill 的 SKILL.md 路径",
		promptSnippet: "根据 frontmatter name 查询未知 skill 的 SKILL.md 路径.",
		promptGuidelines: [
			"使用 resolve_skill(skillFrontmatterName) 查询未知的 skill 的 SKILL.md 路径,拿到 filePath 后用 read(filePath) 读取.",
		],
		parameters: RESOLVE_SKILL_PARAMS,
		async execute(_toolCallId, params: ResolveSkillParams, signal, _onUpdate, ctx) {
			const name = params.name.trim();
			if (!SKILL_NAME_PATTERN.test(name)) {
				const payload = { error: "invalid_name", expected: "^[a-z0-9-]{1,64}$" };
				return jsonToolResult(payload);
			}

			const roots = await getSkillRoots(ctx);
			const matches = await findSkillMatches(name, roots, signal);

			if (matches.length === 0) {
				const payload = { error: "not_found", searchedRoots: roots.map((root) => root.dir) };
				return jsonToolResult(payload);
			}

			if (matches.length > 1) {
				const payload = { error: "ambiguous", matches: matches.map((match) => match.filePath) };
				return jsonToolResult(payload);
			}

			return jsonToolResult({ filePath: matches[0].filePath });
		},
	});
}

function jsonToolResult(payload: unknown) {
	return {
		content: [{ type: "text" as const, text: JSON.stringify(payload) }],
		details: payload,
	};
}

async function getSkillRoots(ctx: ExtensionContext): Promise<SkillRoot[]> {
	const roots: SkillRoot[] = [
		{ dir: path.join(homedir(), CONFIG_DIR_NAME, "agent", "skills"), includeRootMarkdown: true },
		{ dir: path.join(homedir(), ".agents", "skills"), includeRootMarkdown: false },
	];

	if (ctx.isProjectTrusted()) {
		roots.push({ dir: path.join(ctx.cwd, CONFIG_DIR_NAME, "skills"), includeRootMarkdown: true });
		for (const ancestor of await getAncestorsUntilGitRoot(ctx.cwd)) {
			roots.push({ dir: path.join(ancestor, ".agents", "skills"), includeRootMarkdown: false });
		}
	}

	return dedupeRoots(roots);
}

async function getAncestorsUntilGitRoot(cwd: string): Promise<string[]> {
	const ancestors: string[] = [];
	let current = path.resolve(cwd);

	while (true) {
		ancestors.push(current);
		if (await pathExists(path.join(current, ".git"))) break;

		const parent = path.dirname(current);
		if (parent === current) break;
		current = parent;
	}

	return ancestors;
}

function dedupeRoots(roots: SkillRoot[]): SkillRoot[] {
	const seen = new Set<string>();
	const deduped: SkillRoot[] = [];

	for (const root of roots) {
		const key = normalizeForCompare(path.resolve(root.dir));
		if (seen.has(key)) continue;
		seen.add(key);
		deduped.push({ ...root, dir: path.resolve(root.dir) });
	}

	return deduped;
}

async function findSkillMatches(name: string, roots: SkillRoot[], signal: AbortSignal | undefined): Promise<SkillMatch[]> {
	const matches: SkillMatch[] = [];
	const seenFiles = new Set<string>();

	for (const root of roots) {
		throwIfAborted(signal);
		const skillFiles = await discoverSkillFiles(root, signal);
		for (const filePath of skillFiles) {
			throwIfAborted(signal);
			const key = normalizeForCompare(path.resolve(filePath));
			if (seenFiles.has(key)) continue;
			seenFiles.add(key);

			const metadata = await readSkillMetadata(filePath);
			if (metadata.name !== name) continue;
			matches.push({ filePath, root: root.dir, metadata });
		}
	}

	return matches;
}

async function discoverSkillFiles(root: SkillRoot, signal: AbortSignal | undefined): Promise<string[]> {
	if (!(await isDirectory(root.dir))) return [];

	const files = new Set<string>();

	if (root.includeRootMarkdown) {
		for (const entry of await safeReaddir(root.dir)) {
			throwIfAborted(signal);
			if (!entry.isFile()) continue;
			if (path.extname(entry.name).toLowerCase() !== ".md") continue;
			files.add(path.join(root.dir, entry.name));
		}
	}

	await walkForSkillMarkdown(root.dir, files, signal);
	return [...files];
}

async function walkForSkillMarkdown(dir: string, files: Set<string>, signal: AbortSignal | undefined): Promise<void> {
	throwIfAborted(signal);
	const entries = await safeReaddir(dir);

	if (entries.some((entry) => entry.isFile() && entry.name === "SKILL.md")) {
		files.add(path.join(dir, "SKILL.md"));
	}

	for (const entry of entries) {
		throwIfAborted(signal);
		if (!entry.isDirectory()) continue;
		if (entry.name === ".git") continue;
		await walkForSkillMarkdown(path.join(dir, entry.name), files, signal);
	}
}

async function readSkillMetadata(filePath: string): Promise<SkillMetadata> {
	const text = await readFile(filePath, "utf8").catch(() => "");
	const frontmatter = parseFrontmatter(text);
	if (!frontmatter) return {};

	return {
		name: frontmatter.name,
		description: frontmatter.description,
		disableModelInvocation: frontmatter["disable-model-invocation"] === "true",
	};
}

function parseFrontmatter(text: string): Record<string, string> | undefined {
	const match = /^---\s*\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(text);
	if (!match) return undefined;

	const values: Record<string, string> = {};
	for (const rawLine of match[1].split(/\r?\n/)) {
		const line = rawLine.trim();
		if (!line || line.startsWith("#")) continue;

		const keyValue = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
		if (!keyValue) continue;

		const key = keyValue[1];
		let value = keyValue[2].trim();
		value = stripMatchingQuotes(value);
		values[key] = value;
	}

	return values;
}

function stripMatchingQuotes(value: string): string {
	if (value.length < 2) return value;
	const first = value[0];
	const last = value[value.length - 1];
	if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
		return value.slice(1, -1);
	}
	return value;
}

async function safeReaddir(dir: string) {
	return await readdir(dir, { withFileTypes: true }).catch(() => []);
}

async function pathExists(targetPath: string): Promise<boolean> {
	return await stat(targetPath)
		.then(() => true)
		.catch(() => false);
}

async function isDirectory(targetPath: string): Promise<boolean> {
	return await stat(targetPath)
		.then((value) => value.isDirectory())
		.catch(() => false);
}

function throwIfAborted(signal: AbortSignal | undefined): void {
	if (!signal?.aborted) return;
	throw new Error("resolve_skill cancelled");
}

function normalizeForCompare(value: string): string {
	const normalized = path.normalize(value);
	return process.platform === "win32" ? normalized.toLowerCase() : normalized;
}
