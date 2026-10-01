/**
 * /list-sandbox pi 扩展 — 纯连接器 (swt-list-sandbox M2, D004/BR-010)
 *
 * 职责 (刻意浅): 子进程调 swt.py list, 解析 LIST 末行, 选择与展示交互,
 * 按 pi 模式分路降级 (D010). 业务零实现 — 一切 podman/runtime/组装
 * 逻辑住在 skill 内 scripts/swt.py, 本文件不重复任何一份.
 *
 * 命令 (D009): /list-sandbox 无参数.
 *   tui  -> ctx.ui.select 列容器 -> ctx.ui.custom 滚动文本展示访问入口
 *           (只给人看, 不进 LLM 上下文, BR-007)
 *   rpc  -> ctx.ui.notify 摘要 (容器数 + 裸命令提示)
 *   print/json -> stderr 一行提示, 不写 stdout (安全策略)
 * 子进程超时 / exit 4 (无 podman) / LIST 解析失败 -> 按所在模式同路降级.
 *
 * 纯函数出口 (模块级导出, 供 tests/pi/list-sandbox.test.mjs):
 *   parseListLine(stdout)  取 stdout 末行 LIST json 解析, 失败返回 null
 *   buildSelectItems(json) 容器条目 -> 选择列表选项 (名字/状态/分支摘要)
 *   modeRoutePlan(mode)    pi 模式 -> 输出通道与文案
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

/** skill 目录 (D001): 扩展与脚本同版本演进. 兼容 jiti (提供 __dirname)
 * 与 node 直跑 (ESM, 仅 import.meta.url) 两种装载形态. */
const SKILL_DIR: string =
	typeof __dirname === "string"
		? path.resolve(__dirname, "..")
		: path.resolve(fileURLToPath(new URL(".", import.meta.url)), "..");

/** swt.py 路径: skillDir 相对推导 (mailbox 先例). */
const SCRIPT = path.join(SKILL_DIR, "scripts", "swt.py");

/** LIST schema v1 (D005, 生产侧为 swt.py list 末行). 扩展只读消费,
 * 字段宽松容忍 (只加不改), 未知字段原样透传. */
export interface ListLanEntry {
	addr?: unknown;
	iface?: unknown;
	kind?: unknown;
	[key: string]: unknown;
}

export interface ListContainerEntry {
	name: string;
	repo?: string | null;
	branch?: string | null;
	"podman-state"?: string | null;
	lifecycle?: string | null;
	"record-state"?: string | null;
	ports?: { ssh?: number | null; vnc?: number | null; web?: number | null } | null;
	"host-display"?: string | null;
	lans?: ListLanEntry[];
	"access-entries"?: string[];
	"collection-errors"?: string[];
	[key: string]: unknown;
}

export interface ListPayload {
	schema: number;
	scope?: { "records-root"?: string; completeness?: string };
	containers: ListContainerEntry[];
	warnings?: string[];
	[key: string]: unknown;
}

/** 选择列表选项: label 给 ctx.ui.select, entry 供选中后取访问入口. */
export interface SelectItem {
	label: string;
	entry: ListContainerEntry;
}

/** pi 运行模式 (extensions.md ctx.mode, 闭集). */
export type PiMode = "tui" | "rpc" | "json" | "print";

/** 输出通道: select/custom 仅 tui, notify 走 tui+rpc, stderr 永远可用且不污染 stdout. */
export type RouteChannel = "select" | "custom" | "notify" | "stderr";

/** 模式分路计划 (D010): 该模式的可用通道 + 提示/降级文案.
 * 文案占位: <skill> 由调用方代入真实 skillDir, {n} 代入容器数. */
export interface ModeRoutePlan {
	mode: PiMode;
	channels: RouteChannel[];
	messages: {
		/** rpc notify 摘要 (容器数 + 裸命令提示). */
		summary: string;
		/** print/json stderr 一行提示 (不写 stdout). */
		bareData: string;
		/** 子进程 exit 4: 无 podman 环境. */
		noPodman: string;
		/** stdout 末行无 LIST 或 json 解析失败. */
		parseFailed: string;
		/** 子进程超时. */
		timeout: string;
	};
}

/** 子进程超时 (M2 接口: 120s). */
const LIST_TIMEOUT_MS = 120_000;

/** 裸数据命令提示 (D010 文案, <skill> 为 skillDir 占位). */
const BARE_COMMAND = "uv run python <skill>/scripts/swt.py list";

/** 生命周期标注 (AC-001/AC-004: retired 标注 仅可终结). */
const LIFECYCLE_LABELS: Record<string, string> = {
	active: "在用",
	retired: "仅可终结",
	unknown: "未知",
};

/** 记录轴标注 (AC-005). */
const RECORD_LABELS: Record<string, string> = {
	matched: "记录匹配",
	missing: "本记录根无记录",
	corrupt: "记录不可解析",
};

/** 解析 swt.py list 的 stdout: 末行 `LIST ` 前缀单行 json (D005).
 * 末行非 LIST 前缀 / json 解析失败 / 非对象 -> null (调用方按所在模式降级). */
export function parseListLine(stdout: string): ListPayload | null {
	const lines = stdout
		.split("\n")
		.map((line) => line.trimEnd())
		.filter((line) => line.length > 0);
	const last = lines[lines.length - 1];
	if (typeof last !== "string" || !last.startsWith("LIST ")) return null;
	let parsed: unknown;
	try {
		parsed = JSON.parse(last.slice("LIST ".length));
	} catch {
		return null;
	}
	if (typeof parsed !== "object" || parsed === null) return null;
	return parsed as ListPayload;
}

/** 容器条目 -> 选择列表选项: 容器名 + podman 状态 + 生命周期标注 +
 * 分支摘要 (M2/AC-001 交互面). 空清单产出空数组. */
export function buildSelectItems(listJson: ListPayload): SelectItem[] {
	const containers = Array.isArray(listJson?.containers) ? listJson.containers : [];
	return containers.map((entry) => {
		const lifecycleLabel =
			(typeof entry.lifecycle === "string" && LIFECYCLE_LABELS[entry.lifecycle]) || "未知";
		const podmanState = entry["podman-state"] || "状态未知";
		const branch = entry.branch || "分支未知";
		return { entry, label: `${entry.name} · podman ${podmanState} · ${lifecycleLabel} · ${branch}` };
	});
}

/** 模式分路 (D010): tui -> select+custom(+notify 降级); rpc -> notify 摘要;
 * print/json -> 仅 stderr 一行提示, 不写 stdout. 未知模式防御性归入
 * stderr 路线 (不污染输出流, 不崩溃). */
export function modeRoutePlan(mode: PiMode): ModeRoutePlan {
	const channels: RouteChannel[] =
		mode === "tui" ? ["select", "custom", "notify"] : mode === "rpc" ? ["notify"] : ["stderr"];
	return {
		mode,
		channels,
		messages: {
			summary: `共 {n} 个沙盒容器; 裸数据: ${BARE_COMMAND}`,
			bareData: `交互展示需 TUI/RPC 模式; 裸数据: ${BARE_COMMAND}`,
			noPodman: "本环境无 podman, 仅 host pi 可用",
			parseFailed: `LIST 输出解析失败; 裸数据: ${BARE_COMMAND}`,
			timeout: `swt.py list 超时 (${LIST_TIMEOUT_MS / 1000}s); 裸数据: ${BARE_COMMAND}`,
		},
	};
}

/** 文案占位代入: <skill> -> 真实 skillDir, {n} -> 容器数. */
function fillMessage(text: string, count?: number): string {
	return text
		.replaceAll("<skill>", SKILL_DIR)
		.replace("{n}", count === undefined ? "?" : String(count));
}

interface RunResult {
	code: number | null;
	stdout: string;
	stderr: string;
	timedOut: boolean;
}

/** BR-010 唯一子进程: `uv run python <skillDir>/scripts/swt.py list`,
 * 超时 120s 杀进程并置 timedOut. */
function runListScript(): Promise<RunResult> {
	return new Promise((resolve) => {
		const child = spawn("uv", ["run", "python", SCRIPT, "list"], {
			stdio: ["ignore", "pipe", "pipe"],
		});
		let stdout = "";
		let stderr = "";
		let timedOut = false;
		let done = false;
		const timer = setTimeout(() => {
			timedOut = true;
			try {
				child.kill("SIGKILL");
			} catch {
				/* 已退出 */
			}
		}, LIST_TIMEOUT_MS);
		child.stdout?.on("data", (d) => (stdout += d.toString()));
		child.stderr?.on("data", (d) => (stderr += d.toString()));
		const finish = (code: number | null) => {
			if (done) return;
			done = true;
			clearTimeout(timer);
			resolve({ code, stdout, stderr, timedOut });
		};
		child.on("error", (err) => {
			stderr += String(err);
			finish(null);
		});
		child.on("close", (code) => finish(code));
	});
}

/** 按所在模式通道降级提示 (D010): tui/rpc 走 notify, print/json 走
 * stderr 一行 (不写 stdout). */
function degradeNotify(ctx: ExtensionContext, plan: ModeRoutePlan, text: string): void {
	const line = fillMessage(text);
	if (plan.channels.includes("notify")) {
		try {
			ctx.ui.notify(line, "warning");
		} catch {
			/* 无 UI 兜底 */
		}
	} else {
		process.stderr.write(line + "\n");
	}
}

/** 选中容器的展示行: 摘要头 + 访问入口 + 采集错误 (AC-002 展示面). */
function entryDetailLines(entry: ListContainerEntry): string[] {
	const lines: string[] = [];
	const lifecycle = LIFECYCLE_LABELS[entry.lifecycle ?? ""] ?? "未知";
	const record = RECORD_LABELS[entry["record-state"] ?? ""] ?? "未知";
	lines.push(`${entry.name} · podman ${entry["podman-state"] ?? "?"} · ${lifecycle} · ${record}`);
	const meta: string[] = [];
	if (entry.repo) meta.push(`仓库 ${entry.repo}`);
	if (entry.branch) meta.push(`分支 ${entry.branch}`);
	if (meta.length > 0) lines.push(meta.join(" · "));
	const access = entry["access-entries"];
	if (Array.isArray(access) && access.length > 0) {
		lines.push("", "── 访问入口 ──", ...access);
	} else {
		lines.push("", "(无访问入口条目)");
	}
	const errors = entry["collection-errors"];
	if (Array.isArray(errors) && errors.length > 0) {
		lines.push("", "── 采集错误 ──", ...errors);
	}
	return lines;
}

/** custom 组件宿主参数的最小结构类型 (extensions.md Custom Components;
 * 不运行时依赖 pi-tui, 宿主耦合压到最小). */
interface CustomTui {
	height?: number;
	requestRender(): void;
}

/** 显示宽 (CJK 记 2 列), 供滚动文本行宽截断 (tui.md Line Width 纪律). */
function charWidth(code: number): number {
	const wide =
		(code >= 0x1100 && code <= 0x115f) ||
		(code >= 0x2e80 && code <= 0xa4cf) ||
		(code >= 0xac00 && code <= 0xd7a3) ||
		(code >= 0xf900 && code <= 0xfaff) ||
		(code >= 0xfe30 && code <= 0xfe4f) ||
		(code >= 0xff00 && code <= 0xff60) ||
		(code >= 0xffe0 && code <= 0xffe6) ||
		(code >= 0x20000 && code <= 0x3fffd);
	return wide ? 2 : 1;
}

function cutToWidth(text: string, width: number): string {
	let used = 0;
	let end = 0;
	for (const ch of text) {
		const w = charWidth(ch.codePointAt(0) ?? 0);
		if (used + w > width) break;
		used += w;
		end += ch.length;
	}
	return text.slice(0, end);
}

/** tui 模式: 滚动文本组件展示选中容器的访问入口 (D009; 只给人看,
 * 不进 LLM 上下文, BR-007). esc/回车/q 关闭, 上下与翻页键滚动. */
async function showEntryViewer(ctx: ExtensionContext, entry: ListContainerEntry): Promise<void> {
	const lines = entryDetailLines(entry);
	await ctx.ui.custom<unknown>((tui: CustomTui, _theme, _keybindings, done) => {
		let offset = 0;
		const viewport = () => Math.max(4, (tui.height ?? 24) - 2);
		const move = (delta: number) => {
			const max = Math.max(0, lines.length - viewport());
			offset = Math.min(max, Math.max(0, offset + delta));
			tui.requestRender();
		};
		return {
			render: (width: number) =>
				lines.slice(offset, offset + viewport()).map((line) => cutToWidth(line, width)),
			handleInput: (data: string) => {
				if (data === "\x1b" || data === "\r" || data === "q") {
					done(undefined);
					return;
				}
				if (data === "\x1b[A" || data === "k") move(-1);
				else if (data === "\x1b[B" || data === "j") move(1);
				else if (data === "\x1b[5~") move(-viewport());
				else if (data === "\x1b[6~") move(viewport());
			},
			invalidate: () => {
				/* 行集不可变, 无缓存需要失效 */
			},
		};
	});
}

export default function (pi: ExtensionAPI) {
	pi.registerCommand("list-sandbox", {
		description: "列出本 host 全部沙盒容器, 选中查看访问入口 (数据经 swt.py list)",
		handler: async (_args: string, ctx: ExtensionContext) => {
			const plan = modeRoutePlan(ctx.mode as PiMode);
			const result = await runListScript();
			if (result.timedOut) {
				degradeNotify(ctx, plan, plan.messages.timeout);
				return;
			}
			if (result.code === 4) {
				degradeNotify(ctx, plan, plan.messages.noPodman);
				return;
			}
			const payload = parseListLine(result.stdout);
			if (!payload) {
				degradeNotify(ctx, plan, plan.messages.parseFailed);
				return;
			}
			if (ctx.mode === "tui") {
				const items = buildSelectItems(payload);
				if (items.length === 0) {
					try {
						ctx.ui.notify("无在用沙盒容器", "info");
					} catch {
						/* 无 UI 兜底 */
					}
					return;
				}
				let chosen: string | undefined;
				try {
					chosen = await ctx.ui.select("选择沙盒容器:", items.map((item) => item.label));
				} catch {
					return;
				}
				const item = items.find((cand) => cand.label === chosen);
				if (!item) return; // 取消选择
				await showEntryViewer(ctx, item.entry);
				return;
			}
			if (ctx.mode === "rpc") {
				try {
					ctx.ui.notify(fillMessage(plan.messages.summary, payload.containers.length), "info");
				} catch {
					/* 无 UI 兜底 */
				}
				return;
			}
			// print/json: stderr 一行提示, 不写 stdout (安全策略)
			process.stderr.write(fillMessage(plan.messages.bareData) + "\n");
		},
	});
}
