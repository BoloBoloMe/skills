/**
 * /list-sandbox pi 扩展 — 纯连接器 (swt-list-sandbox M2, D004/BR-010)
 *
 * 职责 (刻意浅): 子进程调 swt.py list, 解析 LIST 末行, 选择与展示交互,
 * 按 pi 模式分路降级 (D010). 业务零实现 — 一切 podman/runtime/组装
 * 逻辑住在 skill 内 scripts/swt.py, 本文件不重复任何一份.
 *
 * 命令 (D009): /list-sandbox 无参数.
 *   tui  -> ctx.ui.select 列容器 -> ctx.ui.custom 全屏 overlay 分区展示访问入口
 *           (固定概要 + 分区导航 + 按键提示, 只给人看, 不进 LLM 上下文, BR-007)
 *   rpc  -> ctx.ui.notify 摘要 (容器数 + 裸命令提示)
 *   print/json -> stderr 一行提示, 不写 stdout (安全策略)
 * 子进程超时 / exit 4 (无 podman) / LIST 解析失败 -> 按所在模式同路降级.
 *
 * 纯函数出口 (模块级导出, 供 tests/pi/list-sandbox.test.mjs):
 *   parseListLine(stdout)  取 stdout 末行 LIST json 解析, 失败返回 null
 *   buildSelectItems(json) 容器条目 -> 选择列表选项 (名字/状态/分支摘要)
 *   modeRoutePlan(mode)    pi 模式 -> 输出通道与文案
 *   buildSections(entry)   access-entries 原文 -> 六个用途分区 (不做业务逻辑)
 *   summaryLines(entry)    容器概要行 (标题/状态/仓库/分支/端口)
 *   composeViewerFrame()   一帧全屏视图 (纯函数, 供组件布局测试)
 *   createEntryViewer()    全屏视图组件 (可注入 host/主题/按键匹配/宽度引擎)
 *   decodeViewerKey(data)  原始输入 -> 语义按键 (传统/Kitty 协议, 纯函数)
 *   officialWidthEngine(t) 用 pi-tui visibleWidth/wrapTextWithAnsi 构造引擎
 *   displayWidth(text)     CJK 记 2 列的显示宽
 */
import { spawn, type ChildProcess } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI, ExtensionContext, Theme } from "@earendil-works/pi-coding-agent";

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

/** 组内子进程句柄: child 自成进程组长 (detached), killGroup 杀整组. */
export interface GroupedChild {
	child: ChildProcess;
	/** SIGKILL 整个进程组 (进程树真终止); 组已消失时静默. */
	killGroup: () => void;
}

/** 以独立进程组启动子进程 (detached: 自成组长). 超时终止须杀组而非
 * 单杀直子 — uv 的 python 孙进程一并死亡 (review spec-1: 进程树真终止). */
export function spawnGrouped(command: string, args: readonly string[]): GroupedChild {
	const child = spawn(command, args, {
		stdio: ["ignore", "pipe", "pipe"],
		detached: true,
	});
	const killGroup = (): void => {
		if (typeof child.pid !== "number") return;
		try {
			process.kill(-child.pid, "SIGKILL");
		} catch {
			/* 进程组已消失 */
		}
	};
	return { child, killGroup };
}

/** BR-010 唯一子进程: `uv run python <skillDir>/scripts/swt.py list`,
 * 超时 (可注入, 缺省 120s) 杀整组进程并置 timedOut. */
function runListScript(timeoutMs: number = LIST_TIMEOUT_MS): Promise<RunResult> {
	return new Promise((resolve) => {
		const { child, killGroup } = spawnGrouped("uv", ["run", "python", SCRIPT, "list"]);
		let stdout = "";
		let stderr = "";
		let timedOut = false;
		let done = false;
		const timer = setTimeout(() => {
			timedOut = true;
			killGroup();
		}, timeoutMs);
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

/** ctx.ui.notify 的无 UI 兜底封装 (mailbox 母本形状). */
function notify(
	ctx: ExtensionContext,
	message: string,
	type: "info" | "warning" | "error" = "info",
): void {
	try {
		ctx.ui.notify(message, type);
	} catch {
		/* 无 UI 模式兜底 */
	}
}

/** 按所在模式通道降级提示 (D010): tui/rpc 走 notify, print/json 走
 * stderr 一行 (不写 stdout). */
function emitDegradation(ctx: ExtensionContext, plan: ModeRoutePlan, text: string): void {
	const line = fillMessage(text);
	if (plan.channels.includes("notify")) {
		notify(ctx, line, "warning");
	} else {
		process.stderr.write(line + "\n");
	}
}

// ── 全屏访问入口视图: 按用途分区, 固定概要 + 分区导航 + 滚动 ──────────
// 分区只按 access-entries 原文前缀归类, 不解释命令/不碰 podman 与记录
// (BR-010); 长命令折行保留全文, CJK 按显示宽, 小终端逐级降级.

/** 分区标识 (闭集). */
export type SectionId = "ssh" | "herdr" | "web" | "desktop" | "credentials" | "issues";

/** 分区顺序: 同时是 tab 顺序与数字键 1..6 顺序. */
export const SECTION_ORDER: readonly SectionId[] = [
	"ssh",
	"herdr",
	"web",
	"desktop",
	"credentials",
	"issues",
];

/** 分区显示名. */
const SECTION_TITLES: Record<SectionId, string> = {
	ssh: "SSH",
	herdr: "Herdr",
	web: "Web",
	desktop: "桌面",
	credentials: "凭据/路径",
	issues: "异常",
};

/** 一个分区: 标题 + 该区访问入口原文行. */
export interface ViewerSection {
	id: SectionId;
	title: string;
	lines: string[];
}

/** 异常/缺项/降级标记: 命中说明该行是缺席或降级原因, 除归主题区外
 * 另汇总到 异常 区 (保留定位感, 又不丢失败总览). */
const ISSUE_MARKERS: readonly string[] = [
	"未附发",
	"缺席",
	"reason",
	"入口缺项",
	"清理指引",
	"恢复:",
	"状态:",
	"降级",
	"absent",
	"诊断",
	"未内置",
	"无 noVNC",
	"未接线",
	"未登记",
];

/** 单行访问入口的主题分区 (不含 异常); 无主题归属返回 null. */
function subjectOf(line: string): SectionId | null {
	if (line.startsWith("ssh 私钥")) return "credentials";
	if (
		line.startsWith("登录密码") ||
		line.startsWith("容器代码路径") ||
		line.startsWith("母体路径") ||
		line.startsWith("host 会话 sessionId")
	) {
		return "credentials";
	}
	if (line.startsWith("ssh 入口")) return "ssh";
	if (line.startsWith("herdr remote") || line.startsWith("Herdr machine")) return "herdr";
	// Web 只指容器 web-port 展示页; noVNC (本机/局域网直连 URL) 是桌面交付.
	if (line.startsWith("web 入口")) return "web";
	if (
		line.startsWith("noVNC") ||
		line.startsWith("窗口直飞") ||
		line.startsWith("本机直通") ||
		line.startsWith("显示栈")
	) {
		return "desktop";
	}
	return null;
}

/** 是否缺席/降级原因行 (主题区保留一条, 异常区再汇总一条). */
function isReasonLine(line: string): boolean {
	return ISSUE_MARKERS.some((marker) => line.includes(marker));
}

/** 把容器的 access-entries 与 collection-errors 拆成固定顺序的六个分区.
 * 空分区保留 (tab 计数 0). 缺席/降级原因既留在其主题区 (如 ssh 区看到
 * "ssh 入口未附发"), 又汇总进 异常 区; 无主题归属的行只进 异常. */
export function buildSections(entry: ListContainerEntry): ViewerSection[] {
	const buckets: Record<SectionId, string[]> = {
		ssh: [],
		herdr: [],
		web: [],
		desktop: [],
		credentials: [],
		issues: [],
	};
	const access = entry["access-entries"];
	if (Array.isArray(access)) {
		for (const raw of access) {
			if (typeof raw !== "string" || raw.length === 0) continue;
			const subject = subjectOf(raw);
			if (subject) {
				buckets[subject].push(raw);
				if (isReasonLine(raw)) buckets.issues.push(raw);
			} else {
				buckets.issues.push(raw);
			}
		}
	}
	const errors = entry["collection-errors"];
	if (Array.isArray(errors)) {
		for (const raw of errors) {
			if (typeof raw !== "string" || raw.length === 0) continue;
			buckets.issues.push(`采集错误: ${raw}`);
		}
	}
	return SECTION_ORDER.map((id) => ({ id, title: SECTION_TITLES[id], lines: buckets[id] }));
}

/** 固定概要行: 标题 + podman/生命周期/记录 + 仓库/分支 + 端口/直通.
 * 供全屏视图顶部固定区与测试使用. */
export function summaryLines(entry: ListContainerEntry): string[] {
	const lifecycle = LIFECYCLE_LABELS[entry.lifecycle ?? ""] ?? "未知";
	const record = RECORD_LABELS[entry["record-state"] ?? ""] ?? "未知";
	const lines: string[] = [];
	lines.push(`容器 ${entry.name}`);
	lines.push(`podman=${entry["podman-state"] ?? "?"} · 生命周期=${lifecycle} · 记录=${record}`);
	const meta: string[] = [];
	if (entry.repo) meta.push(`仓库 ${entry.repo}`);
	if (entry.branch) meta.push(`分支 ${entry.branch}`);
	if (meta.length > 0) lines.push(meta.join(" · "));
	const ports = entry.ports ?? {};
	const hostDisplay = entry["host-display"] ? ` · 本机直通=${entry["host-display"]}` : "";
	lines.push(
		`端口 ssh=${ports.ssh ?? "-"} vnc=${ports.vnc ?? "-"} web=${ports.web ?? "-"}${hostDisplay}`,
	);
	return lines;
}

/** 分区导航行: 当前区 `[1 SSH 2]`, 其余 ` 2 Herdr 1 `; 紧凑模式只留数字. */
function tabsLine(sections: ViewerSection[], active: number, full: boolean): string {
	return sections
		.map((section, index) => {
			const body = full
				? `${index + 1} ${section.title} ${section.lines.length}`
				: `${index + 1}`;
			return index === active ? `[${body}]` : ` ${body} `;
		})
		.join(" ");
}

/** 视图行语义 (宿主可按语义上色; 无主题时纯文本). */
export type ViewerLineStyle = "title" | "meta" | "tabs" | "sep" | "body" | "hint";

/** composeViewerFrame 入参. engine 可注入: 缺省用内建 charWidth 引擎,
 * 真实 pi 路径注入 pi-tui 官方 visibleWidth/wrapTextWithAnsi. */
export interface ViewerFrameInput {
	entry: ListContainerEntry;
	sections: ViewerSection[];
	active: number;
	offset: number;
	width: number;
	rows: number;
	engine?: WidthEngine;
}

/** 一帧全屏视图: 行 + 每行语义 + 布局尺寸 + 可见正文 (测试与调试用). */
export interface ViewerFrame {
	lines: string[];
	styles: ViewerLineStyle[];
	headerHeight: number;
	footerHeight: number;
	bodyHeight: number;
	bodyOffset: number;
	bodyTotal: number;
	bodyLines: string[];
}

/** 组件宿主最小结构类型 (extensions.md Custom Components; 不运行时依赖
 * pi-tui). terminal.rows 为真实视口行数, requestRender 触发重绘. */
export interface ViewerHost {
	terminal?: { rows?: number };
	requestRender(): void;
}

/** 终端行数: 优先真实 terminal.rows, 缺席回退 24 (旧视口高度 + 2 边距). */
function terminalRows(host: ViewerHost): number {
	const rows = host?.terminal?.rows;
	if (typeof rows === "number" && rows > 0) return Math.floor(rows);
	return viewportHeight(host) + 2;
}

// ── 宽度/折行引擎: 默认自算 charWidth, 真实 pi 注入 pi-tui 官方工具 ──
// 自算 charWidth 对 emoji/组合字符/ANSI 会误判, 可能比终端实际显示窄 ->
// render 越宽. 真实路径改用官方 visibleWidth/wrapTextWithAnsi 并以
// truncateToWidth 行做最后防线; 纯 Node 测试可注入自建引擎.

/** 终端宽度/折行抽象 (可注入). */
export interface WidthEngine {
	/** 可见显示宽 (CJK/emoji/组合字符/ANSI 正确). */
	displayWidth(text: string): number;
	/** 按可见宽折行, 续行加缩进; 不丢字符. */
	wrap(text: string, width: number, contIndent?: string): string[];
	/** 最后防线: 把一行裁到 <= maxWidth (默认引擎按 charWidth 裁). */
	truncate(text: string, maxWidth: number): string;
}

/** pi-tui 宽度工具的结构类型 (不运行时依赖, 仅描述注入物). */
export interface PiTuiWidthTools {
	visibleWidth(text: string): number;
	wrapTextWithAnsi(text: string, width: number): string[];
	truncateToWidth(text: string, maxWidth: number, ellipsis?: string, pad?: boolean): string;
}

/** 按显示宽裁剪纯文本 (默认引擎的 truncate; 不感知 ANSI). */
function cutPlainToWidth(text: string, maxWidth: number): string {
	let out = "";
	let used = 0;
	for (const ch of text) {
		const w = charWidth(ch.codePointAt(0) ?? 0);
		if (used + w > maxWidth) break;
		out += ch;
		used += w;
	}
	return out;
}

/** 内建引擎: 现有 charWidth 行为, 供纯 Node 测试与无 pi-tui 回退. */
export const BUILTIN_WIDTH_ENGINE: WidthEngine = {
	displayWidth,
	wrap: (text, width, contIndent = "  ") => wrapToWidth(text, width, contIndent),
	truncate: (text, maxWidth) =>
		displayWidth(text) <= maxWidth ? text : cutPlainToWidth(text, maxWidth),
};

/** 用 pi-tui 官方工具构造引擎: 官方 wrapTextWithAnsi 处理 emoji/组合/ANSI,
 * 续行缩进占用宽度也要计入 (预算 = width - 缩进宽). */
export function officialWidthEngine(tools: PiTuiWidthTools): WidthEngine {
	return {
		displayWidth: (text) => tools.visibleWidth(text),
		wrap: (text, width, contIndent = "  ") => {
			const budget = width - tools.visibleWidth(contIndent);
			if (budget <= 1) return tools.wrapTextWithAnsi(text, Math.max(1, width));
			const rows = tools.wrapTextWithAnsi(text, budget);
			return rows.map((row, index) => (index === 0 ? row : contIndent + row));
		},
		truncate: (text, maxWidth) =>
			tools.visibleWidth(text) <= maxWidth
				? text
				: tools.truncateToWidth(text, maxWidth, "", false),
	};
}

/** 延迟加载 pi-tui 官方宽度工具: 纯 Node 测试无该模块时返回 undefined,
 * 调用方回退内建引擎 (行为与纯函数测试一致). */
async function loadOfficialWidthEngine(): Promise<WidthEngine | undefined> {
	try {
		const mod = (await import("@earendil-works/pi-tui")) as Partial<PiTuiWidthTools>;
		if (
			typeof mod.visibleWidth === "function" &&
			typeof mod.wrapTextWithAnsi === "function" &&
			typeof mod.truncateToWidth === "function"
		) {
			return officialWidthEngine(mod as PiTuiWidthTools);
		}
	} catch {
		/* 纯 Node/无 pi-tui 环境: 回退内建引擎 */
	}
	return undefined;
}

/** 组装一帧全屏视图 (纯函数): 顶部固定概要 + 分区导航 + 分隔线, 正文按当前
 * 分区折行滚动, 底部固定按键提示. 行数恒等于 rows (全屏 overlay 铺满);
 * 小终端从丰富到精简逐级降级, 直到至少留一行正文. */
export function composeViewerFrame(input: ViewerFrameInput): ViewerFrame {
	const width = Math.max(1, Math.floor(input.width));
	const rows = Math.max(1, Math.floor(input.rows));
	const sections = input.sections.length > 0 ? input.sections : buildSections(input.entry);
	const active = Math.min(Math.max(0, input.active), Math.max(0, sections.length - 1));
	const engine = input.engine ?? BUILTIN_WIDTH_ENGINE;
	const wrap = (line: string): string[] => engine.wrap(line, width, "  ");

	const buildHeader = (summaryCount: number, tabsFull: boolean, separator: boolean) => {
		const logical: { text: string; style: ViewerLineStyle }[] = [];
		summaryLines(input.entry)
			.slice(0, Math.max(0, summaryCount))
			.forEach((text, index) =>
				logical.push({ text, style: index === 0 ? "title" : "meta" }),
			);
		logical.push({ text: tabsLine(sections, active, tabsFull), style: "tabs" });
		if (separator) logical.push({ text: "-".repeat(width), style: "sep" });
		const lines: string[] = [];
		const styles: ViewerLineStyle[] = [];
		for (const item of logical) {
			for (const wrapped of wrap(item.text)) {
				lines.push(wrapped);
				styles.push(item.style);
			}
		}
		return { lines, styles };
	};
	const buildFooter = (mode: "full" | "compact" | "none") => {
		if (mode === "none") return { lines: [] as string[], styles: [] as ViewerLineStyle[] };
		const text =
			mode === "full"
				? "1-6/Tab 切区 · ↑↓/j/k 行滚 · PgUp/PgDn 翻页 · Home/End 顶底 · q/Esc 关闭"
				: "1-6/Tab 切区 · ↑↓ 滚 · PgUp/PgDn · q/Esc 关闭";
		const lines = wrap(text);
		return { lines, styles: lines.map((): ViewerLineStyle => "hint") };
	};

	// 从丰富到精简; 选第一个能留出至少一行正文的布局.
	const variants = [
		{ summary: 4, tabsFull: true, footer: "full" as const, separator: true },
		{ summary: 2, tabsFull: true, footer: "full" as const, separator: true },
		{ summary: 2, tabsFull: false, footer: "full" as const, separator: true },
		{ summary: 1, tabsFull: false, footer: "compact" as const, separator: false },
		{ summary: 0, tabsFull: false, footer: "compact" as const, separator: false },
		{ summary: 0, tabsFull: false, footer: "none" as const, separator: false },
	];
	// 选布局: 优先保留足够正文 (大终端目标 6 行), 避免概要把正文挤到 1 行;
	// 都达不到时取最精简且放得下的.
	const targetBody = Math.max(1, Math.min(6, rows - 4));
	let header = buildHeader(4, true, true);
	let footer = buildFooter("full");
	let chosen = false;
	for (const variant of variants) {
		const candidateHeader = buildHeader(variant.summary, variant.tabsFull, variant.separator);
		const candidateFooter = buildFooter(variant.footer);
		if (candidateHeader.lines.length + candidateFooter.lines.length + 1 > rows) continue;
		header = candidateHeader;
		footer = candidateFooter;
		chosen = true;
		if (rows - header.lines.length - footer.lines.length >= targetBody) break;
	}
	if (!chosen) {
		header = buildHeader(0, false, false);
		footer = buildFooter("none");
	}

	const sectionLines =
		sections[active].lines.length > 0 ? sections[active].lines : ["(本区无条目)"];
	const bodyHeight = Math.max(1, rows - header.lines.length - footer.lines.length);
	const view = scrollWindow(sectionLines, width, bodyHeight, input.offset, 0, engine);
	// 正文也过最后防线 (注入引擎折行不准时仍不越宽)
	const bodyLines = view.visible.map((line) => engine.truncate(line, width));
	const body = [...bodyLines];
	while (body.length < bodyHeight) body.push("");

	const lines = [...header.lines, ...body, ...footer.lines];
	const styles: ViewerLineStyle[] = [
		...header.styles,
		...body.map((): ViewerLineStyle => "body"),
		...footer.styles,
	];
	while (lines.length < rows) {
		lines.push("");
		styles.push("body");
	}
	if (lines.length > rows) {
		lines.length = rows;
		styles.length = rows;
	}
	// 最后防线: 每行按注入引擎裁到 width (官方 visibleWidth 认为超宽就截),
	// 避免 emoji/组合字符/ANSI 误判导致 overlay 行越宽.
	for (let index = 0; index < lines.length; index++) {
		lines[index] = engine.truncate(lines[index], width);
	}
	return {
		lines,
		styles,
		headerHeight: header.lines.length,
		footerHeight: footer.lines.length,
		bodyHeight,
		bodyOffset: view.offset,
		bodyTotal: view.rows.length,
		bodyLines,
	};
}

/** 组件句柄: 兼容 pi Component (render/handleInput/invalidate), 另附测试与
 * 调试用的观察口. */
export interface EntryViewerHandle {
	render(width: number): string[];
	handleInput(data: string): void;
	invalidate(): void;
	activeSection(): SectionId;
	activeIndex(): number;
	scrollOffset(): number;
	selectSection(id: SectionId): boolean;
}

/** 把语义行落到主题色: 只在整行外层包色, 不改变可见宽度; 无主题或异常时
 * 原样返回. */
function styleLine(text: string, style: ViewerLineStyle, theme?: Theme): string {
	if (!theme || typeof theme.fg !== "function") return text;
	try {
		switch (style) {
			case "title":
				return theme.fg("accent", theme.bold(text));
			case "tabs":
				return theme.fg("muted", text);
			case "sep":
				return theme.fg("border", text);
			case "hint":
				return theme.fg("dim", text);
			default:
				return text;
		}
	} catch {
		return text;
	}
}

/** 注入式按键匹配 (真实 pi 传 KeybindingsManager, 其 matches 内部用
 * matchesKey, 能处理 Kitty 协议与修改键; 测试可传假实现). */
export interface ViewerKeybindings {
	matches(data: string, keybinding: string): boolean;
}

/** 语义按键 (与终端具体转义/协议无关). */
export type ViewerKey =
	| "close"
	| "next"
	| "prev"
	| "up"
	| "down"
	| "pageUp"
	| "pageDown"
	| "top"
	| "bottom"
	| `section:${number}`;

/** 把原始输入解码成语义按键: 覆盖传统 CSI/SS3 转义与 Kitty 键盘协议
 * (CSI-u, 带修饰的功能键), 并忽略按键释放事件. 这是注入的 KeybindingsManager
 * 未命中时的兜底; 真实宿主优先走 matchesKey (见 handleInput). */
export function decodeViewerKey(data: string): ViewerKey | null {
	switch (data) {
		case "\x1b":
		case "\r":
		case "\n":
		case "q":
			return "close";
		case "\t":
			return "next";
		case "\x1b[Z":
			return "prev";
		case "\x1b[A":
		case "\x1bOA":
		case "k":
			return "up";
		case "\x1b[B":
		case "\x1bOB":
		case "j":
			return "down";
		case "\x1b[C":
		case "\x1bOC":
		case "l":
			return "next";
		case "\x1b[D":
		case "\x1bOD":
		case "h":
			return "prev";
		case "\x1b[5~":
			return "pageUp";
		case "\x1b[6~":
			return "pageDown";
		case "\x1b[H":
		case "\x1b[1~":
		case "\x1b[7~":
		case "\x1bOH":
		case "g":
			return "top";
		case "\x1b[F":
		case "\x1b[4~":
		case "\x1b[8~":
		case "\x1bOF":
		case "G":
			return "bottom";
	}
	if (/^[1-9]$/.test(data)) return `section:${Number(data)}`;

	// Kitty CSI-u: ESC [ code (; mods)? (: event)? u
	const csiU = data.match(/^\x1b\[(\d+)(?:;(\d+))?(?::(\d+))?u$/);
	if (csiU) {
		if (csiU[3] === "3") return null; // 按键释放
		const code = Number(csiU[1]);
		const mods = csiU[2] ? Number(csiU[2]) - 1 : 0;
		const shift = (mods & 1) === 1;
		const other = (mods & (2 | 4 | 8)) !== 0; // alt/ctrl/super
		if (code === 9) return shift ? "prev" : "next"; // Tab / Shift+Tab
		if (code === 13 || code === 27) return "close"; // Enter / Escape
		if (other) return null; // 带 ctrl/alt 的可打印键交给 keybindings
		if (code >= 49 && code <= 57) return `section:${code - 48}`;
		const ch = String.fromCodePoint(code);
		if (ch === "q") return "close";
		if (ch === "j") return "down";
		if (ch === "k") return "up";
		if (ch === "l") return "next";
		if (ch === "h") return "prev";
		if (ch === "g") return "top";
		if (ch === "G") return "bottom";
		return null;
	}

	// 带修饰的功能键: ESC [ 1 ; mods (: event)? A/B/C/D/H/F
	const csiMod = data.match(/^\x1b\[1;(\d+)(?::(\d+))?([ABCDHF])$/);
	if (csiMod) {
		if (csiMod[2] === "3") return null;
		switch (csiMod[3]) {
			case "A":
				return "up";
			case "B":
				return "down";
			case "C":
				return "next";
			case "D":
				return "prev";
			case "H":
				return "top";
			case "F":
				return "bottom";
		}
	}

	// 带修饰的 ~ 功能键: ESC [ 5/6/1/4/7/8 ; mods (: event)? ~
	const csiTilde = data.match(/^\x1b\[(\d+)(?:;(\d+))?(?::(\d+))?~$/);
	if (csiTilde) {
		if (csiTilde[3] === "3") return null;
		switch (Number(csiTilde[1])) {
			case 5:
				return "pageUp";
			case 6:
				return "pageDown";
			case 1:
			case 7:
				return "top";
			case 4:
			case 8:
				return "bottom";
		}
	}
	return null;
}

/** 按注入的 keybindings 依次匹配任一绑定名. */
function matchesAny(
	keybindings: ViewerKeybindings,
	data: string,
	bindings: readonly string[],
): boolean {
	return bindings.some((binding) => keybindings.matches(data, binding));
}

/** 构建全屏访问入口视图组件 (只给人看; 不注入会话). esc/回车/q 关闭,
 * 数字键 1-6/Tab/Shift+Tab/左右键切分区, 上下/翻页/Home/End 滚动.
 * 传入 keybindings 时优先用 pi matchesKey (含 Kitty/修改键), 再做语义解码. */
export function createEntryViewer(
	entry: ListContainerEntry,
	host: ViewerHost,
	theme: Theme | undefined,
	done: (result: unknown) => void,
	keybindings?: ViewerKeybindings,
	engine: WidthEngine = BUILTIN_WIDTH_ENGINE,
): EntryViewerHandle {
	const sections = buildSections(entry);
	const offsets = sections.map(() => 0);
	let active = 0;
	let lastWidth = 80;

	const select = (index: number): boolean => {
		if (sections.length === 0) return false;
		const next = ((index % sections.length) + sections.length) % sections.length;
		if (next === active) return false;
		active = next;
		host.requestRender();
		return true;
	};

	const frame = (): ViewerFrame =>
		composeViewerFrame({
			entry,
			sections,
			active,
			offset: offsets[active],
			width: lastWidth,
			rows: terminalRows(host),
			engine,
		});

	const move = (delta: number, absolute?: "start" | "end"): void => {
		const current = frame();
		const max = Math.max(0, current.bodyTotal - current.bodyHeight);
		const base =
			absolute === "start" ? 0 : absolute === "end" ? max : offsets[active] + delta;
		offsets[active] = Math.min(max, Math.max(0, base));
		host.requestRender();
	};

	return {
		render(width: number): string[] {
			if (typeof width === "number" && width > 0) lastWidth = width;
			const current = frame();
			offsets[active] = current.bodyOffset;
			return current.lines.map((line, index) =>
				styleLine(line, current.styles[index] ?? "body", theme),
			);
		},
		handleInput(data: string): void {
			// 先走注入的 pi KeybindingsManager (内部 matchesKey, 处理 Kitty/修改键)
			if (keybindings && typeof keybindings.matches === "function") {
				if (matchesAny(keybindings, data, ["tui.select.cancel", "tui.select.confirm"])) {
					done(undefined);
					return;
				}
				if (matchesAny(keybindings, data, ["tui.select.up"])) return move(-1);
				if (matchesAny(keybindings, data, ["tui.select.down"])) return move(1);
				if (matchesAny(keybindings, data, ["tui.select.pageUp"])) {
					return move(-frame().bodyHeight);
				}
				if (matchesAny(keybindings, data, ["tui.select.pageDown"])) {
					return move(frame().bodyHeight);
				}
				if (matchesAny(keybindings, data, ["tui.editor.cursorLineStart"])) {
					return move(0, "start");
				}
				if (matchesAny(keybindings, data, ["tui.editor.cursorLineEnd"])) {
					return move(0, "end");
				}
				if (matchesAny(keybindings, data, ["tui.input.tab"])) {
					return void select(active + 1);
				}
			}
			// 兜底: 纯语义解码 (测试宿主/未绑定键/Kitty CSI-u)
			const key = decodeViewerKey(data);
			if (key === null) return;
			if (key === "close") {
				done(undefined);
				return;
			}
			if (key === "next") return void select(active + 1);
			if (key === "prev") return void select(active - 1);
			if (key === "up") return move(-1);
			if (key === "down") return move(1);
			if (key === "pageUp") return move(-frame().bodyHeight);
			if (key === "pageDown") return move(frame().bodyHeight);
			if (key === "top") return move(0, "start");
			if (key === "bottom") return move(0, "end");
			if (key.startsWith("section:")) {
				const index = Number(key.slice("section:".length)) - 1;
				if (index >= 0 && index < sections.length) select(index);
			}
		},
		invalidate(): void {
			/* 帧按需重算, 无缓存 */
		},
		activeSection(): SectionId {
			return sections[active].id;
		},
		activeIndex(): number {
			return active;
		},
		scrollOffset(): number {
			return offsets[active];
		},
		selectSection(id: SectionId): boolean {
			const index = sections.findIndex((section) => section.id === id);
			if (index < 0) return false;
			return select(index);
		},
	};
}

/** 视口高度 (review spec-3): 读 custom 工厂 tui 参数的 terminal.rows
 * (pi TUI 真实接口), 缺席/非法回退 24 行, 留 2 行边距, 下限 4. */
export function viewportHeight(tui: unknown): number {
	const rows =
		typeof tui === "object" && tui !== null
			? (tui as { terminal?: { rows?: unknown } }).terminal?.rows
			: undefined;
	const base = typeof rows === "number" && rows > 0 ? rows : 24;
	return Math.max(4, base - 2);
}

/** 滚动窗口结果: 统一以折行后行集为基准. */
export interface ScrollWindowResult {
	/** 新滚动偏移 (已按折行后行数夹取). */
	offset: number;
	/** 折行后全部行. */
	rows: string[];
	/** 当前视口窗口. */
	visible: string[];
}

/** 滚动窗口 (review spec-2 遗留): 滚动上限与取窗统一以折行后行集为准
 * (max = 折行后行数 - 视口), 折行续行同样可滚到. delta = 0 时只取窗. */
export function scrollWindow(
	lines: readonly string[],
	width: number,
	viewport: number,
	offset: number,
	delta: number,
	engine: WidthEngine = BUILTIN_WIDTH_ENGINE,
): ScrollWindowResult {
	const rows = lines.flatMap((line) => engine.wrap(line, width));
	const max = Math.max(0, rows.length - Math.max(1, viewport));
	const next = Math.min(max, Math.max(0, offset + delta));
	return { offset: next, rows, visible: rows.slice(next, next + viewport) };
}

/** 显示宽 (CJK 记 2 列, tui.md Line Width 纪律). */
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

export function displayWidth(text: string): number {
	let width = 0;
	for (const ch of text) width += charWidth(ch.codePointAt(0) ?? 0);
	return width;
}

/** 长行折行 (review spec-2/AC-002): 超宽行按显示宽拆为多行, 续行缩进
 * 两空格, 不丢任何字符 (长隧道/直飞/私钥命令完整可见). 视口窄到放不下
 * 续行缩进时原样返回 (保内容优先). */
export function wrapToWidth(text: string, width: number, contIndent = "  "): string[] {
	const indentWidth = displayWidth(contIndent);
	if (width <= indentWidth + 1) return [text];
	const rows: string[] = [];
	let row = "";
	let used = 0;
	for (const ch of text) {
		const w = charWidth(ch.codePointAt(0) ?? 0);
		const budget = rows.length === 0 ? width : width - indentWidth;
		if (used > 0 && used + w > budget) {
			rows.push(row);
			row = contIndent;
			used = indentWidth;
		}
		row += ch;
		used += w;
	}
	rows.push(row);
	return rows;
}

/** tui 模式: 全屏 overlay 展示选中容器的访问入口 (D009; 只给人看,
 * 不进 LLM 上下文, BR-007). 固定概要 + 分区导航, 六区切换与滚动,
 * 长命令折行不截断, CJK 按显示宽, 小终端逐级降级. */
async function showEntryViewer(ctx: ExtensionContext, entry: ListContainerEntry): Promise<void> {
	// 延迟 import pi-tui 官方宽度工具: 真实 overlay 用 visibleWidth/
	// wrapTextWithAnsi (emoji/组合字符/ANSI 准确), 无模块时组件回退内建引擎.
	const engine = await loadOfficialWidthEngine();
	await ctx.ui.custom<unknown>(
		(tui, theme, keybindings, done) =>
			createEntryViewer(entry, tui, theme, done, keybindings, engine),
		{
			overlay: true,
			overlayOptions: {
				width: "100%",
				maxHeight: "100%",
				anchor: "top-left",
				margin: 0,
			},
		},
	);
}

export default function (pi: ExtensionAPI) {
	pi.registerCommand("list-sandbox", {
		description: "列出本 host 全部沙盒容器, 选中查看访问入口 (数据经 swt.py list)",
		handler: async (_args: string, ctx: ExtensionContext) => {
			const plan = modeRoutePlan(ctx.mode as PiMode);
			const result = await runListScript();
			if (result.timedOut) {
				emitDegradation(ctx, plan, plan.messages.timeout);
				return;
			}
			if (result.code === 4) {
				emitDegradation(ctx, plan, plan.messages.noPodman);
				return;
			}
			const payload = parseListLine(result.stdout);
			if (!payload) {
				emitDegradation(ctx, plan, plan.messages.parseFailed);
				return;
			}
			if (ctx.mode === "tui") {
				const items = buildSelectItems(payload);
				if (items.length === 0) {
					notify(ctx, "无在用沙盒容器");
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
				notify(ctx, fillMessage(plan.messages.summary, payload.containers.length));
				return;
			}
			// print/json: stderr 一行提示, 不写 stdout (安全策略)
			process.stderr.write(fillMessage(plan.messages.bareData) + "\n");
		},
	});
}
