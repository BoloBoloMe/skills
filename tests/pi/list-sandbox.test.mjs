// /list-sandbox pi 扩展测试 (swt-list-sandbox M2, 接缝 A; 用户调整 1: 全屏视图)
// 运行: node tests/pi/list-sandbox.test.mjs
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { pathToFileURL } from "node:url";
import {
	parseListLine,
	buildSelectItems,
	modeRoutePlan,
	spawnGrouped,
	wrapToWidth,
	viewportHeight,
	scrollWindow,
	buildSections,
	summaryLines,
	composeViewerFrame,
	createEntryViewer,
	decodeViewerKey,
	displayWidth,
	officialWidthEngine,
	SECTION_ORDER,
} from "../../workflow/use-sandbox-worktree/pi-extension/index.ts";

/** 扩展源码文本 (静态断言用, 接缝 A: BR-010/BR-007 审计). */
const SRC = readFileSync(
	new URL("../../workflow/use-sandbox-worktree/pi-extension/index.ts", import.meta.url),
	"utf-8",
);

const cases = [];
const test = (name, fn) => cases.push({ name, fn });

/** 轮询等待条件成立 (默认 5s 上限). */
async function waitUntil(fn, ms = 5000, step = 50) {
	const deadline = Date.now() + ms;
	while (Date.now() < deadline) {
		if (fn()) return true;
		await new Promise((resolve) => setTimeout(resolve, step));
	}
	return fn();
}

/** 进程仍在运行 (非僵尸): kill(pid,0) 成功且 /proc 状态非 Z. */
function procRunning(pid) {
	if (!pid) return false;
	try {
		process.kill(pid, 0);
	} catch {
		return false; // ESRCH 等: 已遇出
	}
	try {
		const stat = readFileSync(`/proc/${pid}/stat`, "utf-8");
		const state = stat.split(") ").pop().split(" ")[0];
		return state !== "Z";
	} catch {
		return false;
	}
}

/** 三容器 fixture (两主仓, 形状对齐 tests/test_swt_list.py 的 LIST schema v1). */
const THREE_CONTAINERS = {
	schema: 1,
	scope: {
		"records-root": "/home/u/.agents/sandbox-worktree",
		completeness: "podman-all,records-root-one",
	},
	containers: [
		{
			name: "swt-feature-a",
			repo: "/repos/alpha",
			branch: "feat-x",
			"podman-state": "running",
			lifecycle: "active",
			"record-state": "matched",
			ports: { ssh: 49153, vnc: 49154, web: 49155 },
			"host-display": "ok",
			lans: [],
			"access-entries": ["ssh sandbox@127.0.0.1 -p 49153"],
			"collection-errors": [],
		},
		{
			name: "swt-hotfix-b",
			repo: "/repos/alpha",
			branch: "hotfix",
			"podman-state": "exited",
			lifecycle: "active",
			"record-state": "matched",
			ports: { ssh: null, vnc: null, web: null },
			"host-display": null,
			lans: [],
			"access-entries": ["已停止, resume: uv run python scripts/swt.py resume --name swt-hotfix-b"],
			"collection-errors": [],
		},
		{
			name: "swt-legacy-c",
			repo: "/repos/beta",
			branch: "legacy",
			"podman-state": "exited",
			lifecycle: "retired",
			"record-state": "matched",
			ports: { ssh: null, vnc: null, web: null },
			"host-display": null,
			lans: [],
			"access-entries": [],
			"collection-errors": [],
		},
	],
	warnings: [],
};

// ── TS-041 / TC-041: parseListLine 末行解析与容错 ───────────────────

test("parseListLine 合法 stdout (人话行 + 末行 LIST json) 解析出对象", () => {
	const stdout =
		"[SWT] list: 枚举本 host 沙盒容器 (records-root: /home/u/.agents/sandbox-worktree)\n" +
		"[SWT] list: swt-feature-a: podman running, 在用, 记录匹配\n" +
		"[SWT] list: 共 3 个沙盒容器\n" +
		"LIST " + JSON.stringify(THREE_CONTAINERS) +
		"\n";
	const parsed = parseListLine(stdout);
	assert.ok(parsed, "应解析成功");
	assert.equal(parsed.schema, 1);
	assert.equal(parsed.scope.completeness, "podman-all,records-root-one");
	assert.equal(parsed.containers.length, 3);
	assert.equal(parsed.containers[0].name, "swt-feature-a");
	assert.equal(parsed.containers[0].ports.ssh, 49153);
});

test("parseListLine 末行非 LIST 前缀返回 null", () => {
	const stdout = "[SWT] list: 枚举...\n[SWT] list: 共 3 个沙盒容器\n最后一行是人话";
	assert.equal(parseListLine(stdout), null);
});

test("parseListLine 末行 LIST 前缀但非法 json 返回 null", () => {
	const stdout = "[SWT] list: 枚举...\nLIST {schema: 1, 未加引号的键";
	assert.equal(parseListLine(stdout), null);
});

test("parseListLine 空 stdout 返回 null", () => {
	assert.equal(parseListLine(""), null);
});

// ── TS-041 / TC-041: buildSelectItems 选项构造 ─────────────────────

test("buildSelectItems 三容器 fixture 产出含名字/状态/分支摘要的选项", () => {
	const items = buildSelectItems(THREE_CONTAINERS);
	assert.equal(items.length, 3);
	const byName = {};
	for (const item of items) {
		assert.ok(typeof item.label === "string" && item.label, "选项须为非空字符串");
		byName[item.entry.name] = item;
	}
	assert.deepEqual(
		Object.keys(byName).sort(),
		["swt-feature-a", "swt-hotfix-b", "swt-legacy-c"],
	);
	// 每个选项含: 容器名 + podman 状态 + 分支摘要 (AC-001 交互面)
	assert.ok(byName["swt-feature-a"].label.includes("swt-feature-a"));
	assert.ok(byName["swt-feature-a"].label.includes("running"));
	assert.ok(byName["swt-feature-a"].label.includes("feat-x"));
	assert.ok(byName["swt-hotfix-b"].label.includes("swt-hotfix-b"));
	assert.ok(byName["swt-hotfix-b"].label.includes("exited"));
	assert.ok(byName["swt-hotfix-b"].label.includes("hotfix"));
	// 生命周期标注 (AC-001 retired 场景: 标注 仅可终结)
	assert.ok(byName["swt-legacy-c"].label.includes("swt-legacy-c"));
	assert.ok(byName["swt-legacy-c"].label.includes("仅可终结"));
});

test("buildSelectItems 空清单产出空选项数组", () => {
	assert.deepEqual(buildSelectItems({ ...THREE_CONTAINERS, containers: [] }), []);
});

// ── TS-042 / TC-042: modeRoutePlan 四模式分路 ─────────────────────

test("modeRoutePlan tui 计划含 select+custom 通道", () => {
	const plan = modeRoutePlan("tui");
	assert.ok(plan.channels.includes("select"), "tui 须有 select 通道");
	assert.ok(plan.channels.includes("custom"), "tui 须有 custom 通道");
});

test("modeRoutePlan rpc 计划含 notify 通道与摘要文案键", () => {
	const plan = modeRoutePlan("rpc");
	assert.ok(plan.channels.includes("notify"), "rpc 须有 notify 通道");
	assert.ok(!plan.channels.includes("select"), "rpc 无 select 通道");
	assert.ok(!plan.channels.includes("custom"), "rpc 无 custom 通道");
	assert.ok(typeof plan.messages.summary === "string" && plan.messages.summary.length > 0,
		"rpc 须有摘要文案");
});

test("modeRoutePlan print/json 计划仅 stderr 通道且文案含裸数据命令", () => {
	for (const mode of ["print", "json"]) {
		const plan = modeRoutePlan(mode);
		assert.deepEqual(plan.channels, ["stderr"], `${mode} 仅 stderr 通道 (不写 stdout)`);
		assert.ok(
			plan.messages.bareData.includes("uv run python <skill>/scripts/swt.py list"),
			`${mode} 裸数据提示须含裸命令`,
		);
	}
});

test("modeRoutePlan 降级文案 (exit 4/解析失败/超时) 四模式齐备且复用所在模式通道", () => {
	for (const mode of ["tui", "rpc", "print", "json"]) {
		const plan = modeRoutePlan(mode);
		for (const key of ["noPodman", "parseFailed", "timeout"]) {
			assert.ok(typeof plan.messages[key] === "string" && plan.messages[key].length > 0,
				`${mode} 缺降级文案 ${key}`);
		}
		// 降级复用所在模式通道: tui/rpc 走 notify, print/json 只剩 stderr
		if (mode === "tui" || mode === "rpc") {
			assert.ok(plan.channels.includes("notify"), `${mode} 降级走 notify`);
		} else {
			assert.ok(plan.channels.includes("stderr") && !plan.channels.includes("notify"),
				`${mode} 降级走 stderr`);
		}
	}
	// exit 4 文案识别为无 podman 提示 (AC-006 failure 场景)
	assert.ok(modeRoutePlan("tui").messages.noPodman.includes("本环境无 podman, 仅 host pi 可用"));
});

// ── TS-043 / TC-043: 扩展源码静态断言 (BR-010 纯连接器 / BR-007 无会话注入) ──

test("扩展源码注册 /list-sandbox 命令 (D009)", () => {
	assert.match(SRC, /registerCommand\(\s*"list-sandbox"/);
});

test("子进程仅 swt.py list, 无 podman 直调 (BR-010)", () => {
	const calls = [...SRC.matchAll(/spawn\((.{0,300}?)\)/gs)];
	assert.ok(calls.length >= 1, "应存在子进程调用");
	for (const match of calls) {
		const snippet = match[1];
		assert.ok(
			snippet.includes("command") && snippet.includes("args"),
			"spawn 须收口于通用封装 (参数透传, 不内置命令)",
		);
	}
	// 唯一业务调用点: uv run python <skill>/scripts/swt.py list
	assert.match(
		SRC,
		/spawnGrouped\(\s*"uv",\s*\[\s*"run",\s*"python",\s*SCRIPT,\s*"list"\s*\]/,
	);
	assert.ok(!/["']podman["']/.test(SRC), "源码不得直调 podman");
});

test("源码不含会话注入调用 (BR-007 静态部分)", () => {
	assert.ok(!/sendUserMessage|sendMessage/.test(SRC), "不得调用会话注入 API");
});

// ── review 修复 A (spec-1): 超时杀树 — 进程组整体终止 ───────────────

test("超时杀树: killGroup 后组内全部进程终止 (spec-1)", async () => {
	// 孙进程 pid 由 sh 打到 stdout: sleep 属同组, 直子 sh 任组长
	const { child, killGroup } = spawnGrouped("sh", ["-c", "sleep 300 & echo $!; wait"]);
	let sleepPid = 0;
	try {
		sleepPid = await new Promise((resolve, reject) => {
			let buf = "";
			const timer = setTimeout(() => reject(new Error("未读到孙进程 pid")), 4000);
			child.stdout?.on("data", (d) => {
				buf += d.toString();
				const m = buf.match(/^\s*(\d+)\s*$/m);
				if (m) {
					clearTimeout(timer);
					resolve(Number(m[1]));
				}
			});
		});
		assert.ok(await waitUntil(() => procRunning(sleepPid)), "孙进程应已启动");
		assert.ok(await waitUntil(() => procRunning(child.pid)), "组长 (sh) 应已启动");
		killGroup();
		const allGone = await waitUntil(
			() => !procRunning(child.pid) && !procRunning(sleepPid),
			5000,
		);
		assert.ok(allGone, `杀组后进程应全部退出 (sh=${child.pid}, sleep=${sleepPid})`);
	} finally {
		killGroup(); // 兜底防泄漏
	}
});

// ── review 修复 B (spec-2): 长入口行折行不丢字符 ───────────────────

test("长入口行折行: 全部字符仍在且每行不超宽 (spec-2/AC-002)", () => {
	const longLine =
		"ssh sandbox@192.168.1.10 -p 49153 -i /home/bolo/.agents/sandbox-worktree/keys/swt-feature-a-private-ed25519.key";
	const width = 40;
	const wrapped = wrapToWidth(longLine, width);
	assert.ok(wrapped.length >= 2, "超宽行应折为多行");
	// fixture 纯 ASCII: 显示宽 = 字符数, 逐行验宽 (独立真相源: 纯字符计数)
	for (const line of wrapped) {
		assert.ok(line.length <= width, `折行后仍超宽: ${JSON.stringify(line)}`);
	}
	// 去掉续行缩进后拼回 = 原文 (不丢字符)
	const restored = wrapped.map((l, i) => (i === 0 ? l : l.replace(/^  /, ""))).join("");
	assert.equal(restored, longLine);
});

test("短行/空行原样返回, 不折行", () => {
	assert.deepEqual(wrapToWidth("ssh sandbox@127.0.0.1 -p 49153", 80), ["ssh sandbox@127.0.0.1 -p 49153"]);
	assert.deepEqual(wrapToWidth("", 80), [""]);
});

test("CJK 长行折行: 全部字符仍在 (宽字符不丢)", () => {
	const line = "局域网候选 (未确认可达): ".repeat(12) + "eth0 192.168.2.20";
	const wrapped = wrapToWidth(line, 30);
	assert.ok(wrapped.length >= 2);
	const restored = wrapped.map((l, i) => (i === 0 ? l : l.replace(/^  /, ""))).join("");
	assert.equal(restored, line);
});

// ── review 修复 B 遗留 (spec-2): 折行后滚动上限联动 ────────────────

test("折行后滚动上限联动: 滚到底可见最后一行折行内容 (spec-2 遗留)", () => {
	// 多行长入口 fixture: 每行 ~100 列, width 40 下折成 ~3-4 行
	const lines = [];
	for (let i = 0; i < 12; i++) lines.push(`entry-${i}-` + "x".repeat(100));
	const width = 40;
	const viewport = 8;
	let offset = 0;
	let state;
	// 逐屏滚到底
	for (let i = 0; i < 100; i++) {
		state = scrollWindow(lines, width, viewport, offset, +viewport);
		if (state.offset === offset) break;
		offset = state.offset;
	}
	assert.ok(state.rows.length > lines.length, "fixture 应产生折行续行");
	// 滚到底: 偏移 = 折行后行数 - 视口 (不是逻辑行数 - 视口)
	assert.equal(state.offset, Math.max(0, state.rows.length - viewport));
	// 视口窗口覆盖全部折行行: 最后一行折行内容可见
	assert.equal(state.visible[state.visible.length - 1], state.rows[state.rows.length - 1]);
	// 旧缺陷鉴别: 按逻辑行算上限会够不到底部
	assert.ok(state.offset > Math.max(0, lines.length - viewport));
});

// ── review 修复 C (spec-3): 视口高度走真实 tui.terminal.rows ────────

test("视口高度读 tui.terminal.rows, 缺席/非法回退 (spec-3)", () => {
	assert.equal(viewportHeight({ terminal: { rows: 50 } }), 48);
	assert.equal(viewportHeight({ terminal: { rows: 10 } }), 8);
	assert.equal(viewportHeight({ terminal: { rows: 3 } }), 4); // 下限保护
	assert.equal(viewportHeight({}), 22); // 无 terminal -> 回退 24 行减边距
	assert.equal(viewportHeight({ terminal: {} }), 22); // 无 rows
	assert.equal(viewportHeight({ terminal: { rows: 0 } }), 22); // 非法值
	assert.equal(viewportHeight(null), 22); // 防御
});

// ── 用户调整 1: 全屏访问入口视图 (分区/导航/滚动) ──────────────────────

/** 超长窗口直飞命令, 用于验证折行不截断. */
const LONG_COMMAND =
	"waypipe ssh -p 49153 -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native bolo@192.168.2.20 /home/bolo/.local/bin/swt-headed-browser.sh --disable-gpu --disable-gpu-compositing --no-first-run --no-default-browser-check --start-maximized http://127.0.0.1:8800";

/** 全屏视图 fixture: 覆盖六个分区 + 一条超长命令 + 两条异常行. */
const RICH_ENTRY = {
	name: "swt-feature-a",
	repo: "/repos/alpha",
	branch: "feat-x",
	"podman-state": "running",
	lifecycle: "active",
	"record-state": "matched",
	ports: { ssh: 49153, vnc: 49154, web: 49155 },
	"host-display": "ok",
	lans: [{ addr: "192.168.2.20", iface: "eth0", kind: "candidate" }],
	"access-entries": [
		"ssh 入口 (本机): ssh -p 49153 bolo@127.0.0.1  (用户 bolo, 密码 sandbox)",
		"noVNC (本机): http://127.0.0.1:49154/vnc.html?resize=scale",
		"web 入口 (本机): http://127.0.0.1:49155",
		"herdr remote (host): herdr --remote ssh://bolo@127.0.0.1:49153",
		"Herdr machine: swt-feature-a (宿主侧栏, id=swt-abc123, enabled=True)",
		"noVNC (局域网) [eth0 候选 (未确认可达)]: http://192.168.2.20:49154/vnc.html?resize=scale",
		"web 入口 (局域网) [eth0 候选 (未确认可达)]: http://192.168.2.20:49155",
		"herdr remote (局域网) [eth0 候选 (未确认可达)]: herdr --remote ssh://bolo@192.168.2.20:49153",
		`窗口直飞 (设备侧执行) [eth0 候选 (未确认可达)]: ${LONG_COMMAND}`,
		"窗口直飞前提: 设备须 Linux Wayland 桌面 + waypipe 客户端",
		"本机直通: wayland 已接通, 容器内 headed 窗口直接弹在宿主机桌面",
		"ssh 私钥: /home/u/keys/swt-feature-a-private-ed25519.key",
		"登录密码: sandbox (SSH 登录, noVNC 本身无密码)",
		"容器代码路径: /home/bolo/workspace/swt-feature-a",
		"母体路径: /repos/alpha (只读审阅, 不改跟踪文件)",
		"host 会话 sessionId: 5f3a9c1e-2b7d-4e08-9a6f-1234567890ab",
		"ssh 入口未附发: 容器无 22 端口映射",
		"web 入口未附发: 容器无 8800 端口映射",
	],
	"collection-errors": ["podman port 失败: 权限不足"],
};

/** 多行长入口 fixture (滚动用): ssh 区 40 条超宽行. */
const SCROLL_ENTRY = {
	name: "swt-scroll",
	"podman-state": "running",
	lifecycle: "active",
	"record-state": "matched",
	ports: { ssh: 1, vnc: null, web: null },
	"access-entries": Array.from(
		{ length: 40 },
		(_, i) => `ssh 入口 (本机) #${i}: ssh -p 49153 bolo@127.0.0.1 ${"x".repeat(60)}`,
	),
	"collection-errors": [],
};

/** 造一个只记行数/请求的假 host (真实 pi TUI 结构兼容). */
function fakeHost(rows) {
	return { terminal: { rows }, renders: 0, requestRender() { this.renders++; } };
}

/** 去掉 ANSI 转义 (主题着色断言用). */
function stripAnsi(text) {
	return text.replace(/\x1b\[[0-9;]*m/g, "");
}

test("buildSections 按用途分区: noVNC 归桌面, Web 只指 web-port 展示页, 原因双留", () => {
	const sections = buildSections(RICH_ENTRY);
	assert.deepEqual(sections.map((s) => s.id), [...SECTION_ORDER]);
	const byId = Object.fromEntries(sections.map((s) => [s.id, s.lines]));
	// ssh: 正常入口 + 未附发原因 (原因在主题区可见)
	assert.equal(byId.ssh.length, 2);
	assert.ok(byId.ssh.some((l) => l.startsWith("ssh 入口 (本机)")));
	assert.ok(byId.ssh.some((l) => l.includes("ssh 入口未附发")));
	// herdr: remote 本机/局域网 + Herdr machine
	assert.equal(byId.herdr.length, 3);
	assert.ok(byId.herdr.some((l) => l.startsWith("herdr remote (host)")));
	assert.ok(byId.herdr.some((l) => l.startsWith("Herdr machine")));
	// web: 只指容器 web-port 展示页, 不含 noVNC
	assert.equal(byId.web.length, 3);
	assert.ok(byId.web.every((l) => l.startsWith("web 入口")));
	assert.ok(!byId.web.some((l) => l.startsWith("noVNC")), "noVNC 不归 Web");
	// 桌面: noVNC 本机/局域网双 URL + 直飞/直通
	assert.equal(byId.desktop.length, 5);
	assert.ok(byId.desktop.some((l) => l.startsWith("noVNC (本机)")));
	assert.ok(byId.desktop.some((l) => l.startsWith("noVNC (局域网)")));
	assert.ok(byId.desktop.some((l) => l.startsWith("窗口直飞 (设备侧执行)")));
	assert.ok(byId.desktop.some((l) => l.startsWith("本机直通")));
	// 凭据/路径: 私钥 + 新前缀
	assert.equal(byId.credentials.length, 5);
	for (const prefix of [
		"ssh 私钥",
		"登录密码",
		"容器代码路径",
		"母体路径",
		"host 会话 sessionId",
	]) {
		assert.ok(byId.credentials.some((l) => l.startsWith(prefix)), `凭据区缺 ${prefix}`);
	}
	// 异常区: 汇总两条未附发原因 + 一条采集错误
	assert.equal(byId.issues.length, 3);
	assert.ok(byId.issues.some((l) => l.includes("ssh 入口未附发")));
	assert.ok(byId.issues.some((l) => l.includes("web 入口未附发")));
	assert.ok(byId.issues.some((l) => l.startsWith("采集错误:")));
});

test("新增前缀归类与原因双留: Herdr machine -> Herdr, 登录/路径/sessionId -> 凭据/路径", () => {
	const entry = {
		name: "swt-x",
		"podman-state": "running",
		lifecycle: "active",
		"record-state": "matched",
		ports: { ssh: null, vnc: null, web: null },
		"access-entries": [
			"Herdr machine: 未接线/失败, 重跑 birth/resume; 旧记录尚未登记",
			"登录密码: sandbox (SSH 登录, noVNC 本身无密码)",
			"容器代码路径: /work/x",
			"母体路径: /repos/m (只读审阅)",
			"host 会话 sessionId: 未登记",
			"ssh 入口未附发: 容器无 22 端口映射",
		],
		"collection-errors": [],
	};
	const byId = Object.fromEntries(buildSections(entry).map((s) => [s.id, s.lines]));
	assert.equal(byId.herdr.length, 1);
	assert.ok(byId.herdr[0].startsWith("Herdr machine"));
	assert.equal(byId.credentials.length, 4);
	for (const prefix of [
		"登录密码",
		"容器代码路径",
		"母体路径",
		"host 会话 sessionId",
	]) {
		assert.ok(byId.credentials.some((l) => l.startsWith(prefix)), `凭据区缺 ${prefix}`);
	}
	// 降级/缺席原因既在主题区也在异常汇总
	assert.ok(byId.herdr.some((l) => l.includes("未接线/失败")));
	assert.ok(byId.issues.some((l) => l.includes("Herdr machine")));
	assert.ok(byId.credentials.some((l) => l.includes("未登记")));
	assert.ok(byId.issues.some((l) => l.includes("host 会话 sessionId")));
	assert.ok(byId.ssh.some((l) => l.includes("ssh 入口未附发")));
	assert.ok(byId.issues.some((l) => l.includes("ssh 入口未附发")));
});

test("summaryLines 覆盖容器概要字段", () => {
	const text = summaryLines(RICH_ENTRY).join("\n");
	for (const want of [
		"swt-feature-a",
		"running",
		"在用",
		"记录匹配",
		"/repos/alpha",
		"feat-x",
		"49153",
		"49154",
		"49155",
		"本机直通=ok",
	]) {
		assert.ok(text.includes(want), `概要缺 ${want}`);
	}
});

test("createEntryViewer 全屏渲染: 行数=终端行数, 每行不超宽, 含概要与全部分区", () => {
	const host = fakeHost(30);
	const viewer = createEntryViewer(RICH_ENTRY, host, undefined, () => {});
	const lines = viewer.render(80);
	assert.equal(lines.length, 30, "全屏应铺满 terminal.rows 行");
	for (const line of lines) {
		assert.ok(displayWidth(line) <= 80, `超宽行: ${JSON.stringify(line)}`);
	}
	const text = lines.join("\n");
	assert.ok(text.includes("容器 swt-feature-a"));
	for (const title of ["SSH", "Herdr", "Web", "桌面", "凭据/路径", "异常"]) {
		assert.ok(text.includes(title), `缺少分区 ${title}`);
	}
	assert.ok(text.includes("1-6/Tab"), "应含按键提示");
});

test("createEntryViewer 分区切换: 数字键/Tab/Shift+Tab/左右键", () => {
	const host = fakeHost(30);
	const viewer = createEntryViewer(RICH_ENTRY, host, undefined, () => {});
	assert.equal(viewer.activeSection(), "ssh");
	viewer.handleInput("4");
	assert.equal(viewer.activeSection(), "desktop");
	assert.ok(
		viewer.render(80).join("\n").includes("窗口直飞 (设备侧执行)"),
		"切到桌面区后正文应显示直飞入口",
	);
	viewer.handleInput("\t");
	assert.equal(viewer.activeSection(), "credentials");
	viewer.handleInput("\x1b[Z");
	assert.equal(viewer.activeSection(), "desktop");
	viewer.handleInput("\x1b[C");
	assert.equal(viewer.activeSection(), "credentials");
	viewer.handleInput("\x1b[D");
	assert.equal(viewer.activeSection(), "desktop");
	viewer.handleInput("1");
	assert.equal(viewer.activeSection(), "ssh");
	viewer.handleInput("9"); // 越界数字忽略
	assert.equal(viewer.activeSection(), "ssh");
	assert.ok(viewer.selectSection("issues"));
	assert.equal(viewer.activeSection(), "issues");
	assert.ok(!viewer.selectSection("issues"), "重复选中返回 false");
});

test("createEntryViewer 滚动: j/k 逐行, PgDn/PgUp 逐屏, End/Home 到底/回顶", () => {
	const host = fakeHost(12);
	const viewer = createEntryViewer(SCROLL_ENTRY, host, undefined, () => {});
	viewer.render(40);
	assert.equal(viewer.scrollOffset(), 0);
	viewer.handleInput("\x1b[B");
	assert.equal(viewer.scrollOffset(), 1, "↓ 应加一行");
	viewer.handleInput("k");
	assert.equal(viewer.scrollOffset(), 0, "k 应减一行");
	const frame = composeViewerFrame({
		entry: SCROLL_ENTRY,
		sections: buildSections(SCROLL_ENTRY),
		active: 0,
		offset: 0,
		width: 40,
		rows: 12,
	});
	viewer.handleInput("\x1b[6~");
	assert.equal(viewer.scrollOffset(), frame.bodyHeight, "PgDn 应前进一屏");
	viewer.handleInput("\x1b[5~");
	assert.equal(viewer.scrollOffset(), 0, "PgUp 应回退一屏");
	viewer.handleInput("G");
	const bottom = viewer.scrollOffset();
	assert.equal(bottom, frame.bodyTotal - frame.bodyHeight, "End 应到最大偏移");
	assert.ok(bottom > 0, "fixture 应确实可滚");
	viewer.handleInput("g");
	assert.equal(viewer.scrollOffset(), 0, "Home 应回顶");
});

test("长命令不截断: 组件正文折行拼回原文 (超长窗口直飞命令完整)", () => {
	const sections = buildSections(RICH_ENTRY);
	const commandIndex = sections.findIndex((s) => s.lines.some((l) => l.includes(LONG_COMMAND)));
	assert.ok(commandIndex >= 0, "fixture 应有超长窗口直飞命令");
	const frame = composeViewerFrame({
		entry: RICH_ENTRY,
		sections,
		active: commandIndex,
		offset: 0,
		width: 50,
		rows: 40,
	});
	const restored = frame.bodyLines.map((line) => line.replace(/^ {2}/, "")).join("");
	assert.ok(restored.includes(LONG_COMMAND), "帧正文应含完整窗口直飞命令");

	const viewer = createEntryViewer(RICH_ENTRY, fakeHost(40), undefined, () => {});
	viewer.selectSection(sections[commandIndex].id);
	const lines = viewer.render(50);
	for (const line of lines) assert.ok(displayWidth(line) <= 50, "组件每行不得超宽");
	const rendered = lines.map((line) => line.replace(/^ {2}/, "")).join("");
	assert.ok(rendered.includes(LONG_COMMAND), "组件渲染同样不得截断长命令");
});

test("CJK 折行: 组件每行按显示宽不超宽且字符不丢", () => {
	const cjk = "局域网候选 (未确认可达): " + "很长的中文说明文字".repeat(10);
	const entry = {
		...RICH_ENTRY,
		"access-entries": [`ssh 入口 (局域网): ${cjk}`],
		"collection-errors": [],
	};
	const viewer = createEntryViewer(entry, fakeHost(40), undefined, () => {});
	const lines = viewer.render(30);
	assert.equal(lines.length, 40);
	for (const line of lines) assert.ok(displayWidth(line) <= 30, `超宽: ${JSON.stringify(line)}`);
	const restored = lines.map((line) => line.replace(/^ {2}/, "")).join("");
	assert.ok(restored.includes(cjk), "CJK 原文应完整保留");
});

test("小终端 (18x6) 仍全屏可用: 行数=6, 不超宽, 可切区可关闭", () => {
	const host = fakeHost(6);
	let closed = 0;
	const viewer = createEntryViewer(RICH_ENTRY, host, undefined, () => {
		closed++;
	});
	const lines = viewer.render(18);
	assert.equal(lines.length, 6);
	for (const line of lines) assert.ok(displayWidth(line) <= 18, `超宽: ${JSON.stringify(line)}`);
	viewer.handleInput("\t");
	assert.equal(viewer.activeSection(), "herdr");
	viewer.handleInput("q");
	assert.equal(closed, 1, "q 应关闭一次");
});

test("q/esc/回车关闭回调只发一次且不注入会话", () => {
	for (const key of ["q", "\x1b", "\r"]) {
		let closed = 0;
		const viewer = createEntryViewer(RICH_ENTRY, fakeHost(24), undefined, () => {
			closed++;
		});
		viewer.handleInput(key);
		assert.equal(closed, 1, `${JSON.stringify(key)} 应关闭`);
	}
});

test("主题着色不改变可见宽度与行数", () => {
	const theme = {
		fg: (_color, text) => `\x1b[35m${text}\x1b[0m`,
		bold: (text) => `\x1b[1m${text}\x1b[0m`,
	};
	const viewer = createEntryViewer(RICH_ENTRY, fakeHost(24), theme, () => {});
	const lines = viewer.render(70);
	assert.equal(lines.length, 24);
	assert.ok(lines.join("").includes("\x1b["), "应有 ANSI 着色");
	for (const line of lines) {
		assert.ok(displayWidth(stripAnsi(line)) <= 70, `着色后超宽: ${JSON.stringify(stripAnsi(line))}`);
	}
});

test("空分区显示占位, 组件不崩", () => {
	const entry = { ...RICH_ENTRY, "access-entries": [], "collection-errors": [] };
	const viewer = createEntryViewer(entry, fakeHost(20), undefined, () => {});
	viewer.selectSection("herdr");
	const text = viewer.render(60).join("\n");
	assert.ok(text.includes("(本区无条目)"));
});

// ── 终端宽高动态缩放: 偏移始终合法, 不越界/不消失 ──────────────────

test("终端宽高动态缩放后滚动偏移仍合法 (缩小夹回上限, 放大保持合法)", () => {
	const host = fakeHost(10);
	const viewer = createEntryViewer(SCROLL_ENTRY, host, undefined, () => {});
	viewer.render(40);
	// 小屏滚到底
	viewer.handleInput("G");
	const smallBottom = viewer.scrollOffset();
	assert.ok(smallBottom > 0, "小屏应可滚");
	const frameSmall = composeViewerFrame({
		entry: SCROLL_ENTRY,
		sections: buildSections(SCROLL_ENTRY),
		active: 0,
		offset: smallBottom,
		width: 40,
		rows: 10,
	});
	assert.equal(smallBottom, frameSmall.bodyTotal - frameSmall.bodyHeight);

	// 放大: 可滚空间变小, 偏移必须夹回新上限
	host.terminal.rows = 40;
	const grown = viewer.render(40);
	assert.equal(grown.length, 40);
	const frameLarge = composeViewerFrame({
		entry: SCROLL_ENTRY,
		sections: buildSections(SCROLL_ENTRY),
		active: 0,
		offset: viewer.scrollOffset(),
		width: 40,
		rows: 40,
	});
	assert.equal(viewer.scrollOffset(), frameLarge.bodyTotal - frameLarge.bodyHeight);
	assert.ok(viewer.scrollOffset() < smallBottom, "放大后偏移应被夹小");

	// 变宽: 行集重新折行, 行数=新 rows, 偏移仍在界内
	const wide = viewer.render(120);
	assert.equal(wide.length, 40);
	const frameWide = composeViewerFrame({
		entry: SCROLL_ENTRY,
		sections: buildSections(SCROLL_ENTRY),
		active: 0,
		offset: viewer.scrollOffset(),
		width: 120,
		rows: 40,
	});
	assert.ok(viewer.scrollOffset() >= 0);
	assert.ok(viewer.scrollOffset() <= frameWide.bodyTotal - frameWide.bodyHeight);

	// 缩小后仍能继续滚动且仍合法
	host.terminal.rows = 10;
	viewer.render(40);
	viewer.handleInput("\x1b[6~");
	const frameAgain = composeViewerFrame({
		entry: SCROLL_ENTRY,
		sections: buildSections(SCROLL_ENTRY),
		active: 0,
		offset: 0,
		width: 40,
		rows: 10,
	});
	assert.ok(viewer.scrollOffset() >= 0);
	assert.ok(viewer.scrollOffset() <= frameAgain.bodyTotal - frameAgain.bodyHeight);
});

// ── 按键协议: pi matchesKey 注入路径 + Kitty/修改键语义解码 ────────

test("输入优先走注入 keybindings (pi matchesKey), 未绑定的走语义解码", () => {
	let closed = 0;
	const seen = [];
	const keybindings = {
		matches: (data, binding) => {
			seen.push(binding);
			if (binding === "tui.select.cancel") return data === "CANCEL";
			if (binding === "tui.select.down") return data === "DOWN";
			if (binding === "tui.select.up") return data === "UP";
			if (binding === "tui.input.tab") return data === "TAB";
			return false;
		},
	};
	const host = fakeHost(12);
	const viewer = createEntryViewer(SCROLL_ENTRY, host, undefined, () => {
		closed++;
	}, keybindings);
	viewer.render(40);
	viewer.handleInput("DOWN");
	assert.equal(viewer.scrollOffset(), 1, "注入绑定应触发滚动");
	viewer.handleInput("UP");
	assert.equal(viewer.scrollOffset(), 0);
	viewer.handleInput("TAB");
	assert.equal(viewer.activeSection(), "herdr");
	viewer.handleInput("j");
	assert.ok(seen.length > 0, "应查询过 keybindings");
	viewer.handleInput("CANCEL");
	assert.equal(closed, 1, "注入绑定应触发关闭");
});

test("decodeViewerKey: 传统转义与 Kitty/修改键协议都解成语义键", () => {
	assert.equal(decodeViewerKey("\x1b"), "close");
	assert.equal(decodeViewerKey("q"), "close");
	assert.equal(decodeViewerKey("\t"), "next");
	assert.equal(decodeViewerKey("\x1b[Z"), "prev");
	assert.equal(decodeViewerKey("\x1b[5~"), "pageUp");
	assert.equal(decodeViewerKey("\x1b[6~"), "pageDown");
	assert.equal(decodeViewerKey("\x1b[H"), "top");
	assert.equal(decodeViewerKey("\x1b[F"), "bottom");
	assert.equal(decodeViewerKey("3"), "section:3");
	// SS3 方向键
	assert.equal(decodeViewerKey("\x1bOA"), "up");
	// 带修饰的方向/功能键 (Kitty 风格)
	assert.equal(decodeViewerKey("\x1b[1;2A"), "up");
	assert.equal(decodeViewerKey("\x1b[1;5B"), "down");
	assert.equal(decodeViewerKey("\x1b[5;2~"), "pageUp");
	// CSI-u: Tab/Shift+Tab/Escape/Enter/字母/数字
	assert.equal(decodeViewerKey("\x1b[9u"), "next");
	assert.equal(decodeViewerKey("\x1b[9;2u"), "prev");
	assert.equal(decodeViewerKey("\x1b[27u"), "close");
	assert.equal(decodeViewerKey("\x1b[13u"), "close");
	assert.equal(decodeViewerKey("\x1b[113u"), "close"); // q
	assert.equal(decodeViewerKey("\x1b[106u"), "down"); // j
	assert.equal(decodeViewerKey("\x1b[107u"), "up"); // k
	assert.equal(decodeViewerKey("\x1b[49u"), "section:1"); // 1
	assert.equal(decodeViewerKey("\x1b[71;2u"), "bottom"); // shift+G
	// 按键释放事件忽略; ctrl/alt 可打印键交给 keybindings
	assert.equal(decodeViewerKey("\x1b[9;2:3u"), null);
	assert.equal(decodeViewerKey("\x1b[1;1:3A"), null);
	assert.equal(decodeViewerKey("\x1b[99;5u"), null);
	assert.equal(decodeViewerKey("\x1b[9999z"), null);
});

// ── 宽度边界: 官方 pi-tui 工具注入与 emoji/组合字符/ANSI 防越宽 ────

/** 尝试加载真实 pi-tui: env 指定, 裸名, 或本机 pnpm store (供真实宽度用例). */
async function loadRealPiTui() {
	const candidates = [];
	if (process.env.PI_TUI_MODULE) candidates.push(process.env.PI_TUI_MODULE);
	candidates.push("@earendil-works/pi-tui");
	try {
		const links = `${process.env.HOME}/.local/share/pnpm/store/v11/links/@earendil-works/pi-coding-agent`;
		for (const version of readdirSync(links)) {
			const versionDir = `${links}/${version}`;
			const roots = [`${versionDir}/node_modules`];
			for (const child of readdirSync(versionDir)) {
				if (child !== "node_modules") roots.push(`${versionDir}/${child}/node_modules`);
			}
			for (const root of roots) {
				const candidate = `${root}/@earendil-works/pi-tui/dist/index.js`;
				if (existsSync(candidate)) candidates.push(pathToFileURL(candidate).href);
			}
		}
	} catch {
		/* 无 pnpm store: 跳过真实用例 */
	}
	for (const spec of candidates) {
		try {
			const mod = await import(spec);
			if (typeof mod.visibleWidth === "function" && typeof mod.wrapTextWithAnsi === "function") {
				return mod;
			}
		} catch {
			/* 下一个候选 */
		}
	}
	return null;
}

test("officialWidthEngine: 用注入的官方工具量宽/折行/裁剪, 续行计缩进", () => {
	const calls = { visible: 0, wrap: 0, trunc: 0 };
	const tools = {
		visibleWidth: (text) => {
			calls.visible++;
			return [...text].length;
		},
		wrapTextWithAnsi: (text, width) => {
			calls.wrap++;
			const out = [];
			for (let i = 0; i < text.length; i += width) out.push(text.slice(i, i + width));
			return out.length > 0 ? out : [""];
		},
		truncateToWidth: (text, width) => {
			calls.trunc++;
			return [...text].slice(0, width).join("");
		},
	};
	const engine = officialWidthEngine(tools);
	assert.equal(engine.displayWidth("abc"), 3);
	// 缩进 ".." 宽 2, width 4 -> 折行预算 2
	assert.deepEqual(engine.wrap("abcdefgh", 4, ".."), ["ab", "..cd", "..ef", "..gh"]);
	assert.equal(engine.truncate("abcdef", 3), "abc");
	assert.equal(engine.truncate("ab", 5), "ab"); // 已够宽不改
	assert.ok(calls.visible > 0 && calls.wrap > 0 && calls.trunc > 0, "应实际调官方工具");
});

test("注入引擎兜底: 折行故意不折时, 最终 truncate 仍保每行不越宽", () => {
	const engine = {
		displayWidth: (text) => [...text].length,
		wrap: (text) => [text], // 故意不折行
		truncate: (text, maxWidth) => [...text].slice(0, maxWidth).join(""),
	};
	const entry = {
		...RICH_ENTRY,
		"access-entries": ["ssh 入口: " + "很长的入口文本".repeat(20)],
		"collection-errors": [],
	};
	const frame = composeViewerFrame({
		entry,
		sections: buildSections(entry),
		active: 0,
		offset: 0,
		width: 16,
		rows: 10,
		engine,
	});
	assert.equal(frame.lines.length, 10);
	for (const line of frame.lines) {
		assert.ok(engine.displayWidth(line) <= 16, `越宽: ${JSON.stringify(line)}`);
	}
	// 可见正文同样过防线
	for (const line of frame.bodyLines) {
		assert.ok(engine.displayWidth(line) <= 16, `正文越宽: ${JSON.stringify(line)}`);
	}
});
test("实际 pi-tui visibleWidth 下 emoji/组合字符/ANSI 折行不越宽 (无模块则跳过)", async () => {
	const tui = await loadRealPiTui();
	if (!tui) {
		console.log("  (skipped: pi-tui 不可解析, 可设 PI_TUI_MODULE 启用)");
		return;
	}
	const engine = officialWidthEngine(tui);
	const tricky =
		"ssh 入口: \u{1F600} emoji \u{1F468}\u200D\u{1F469}\u200D\u{1F467} ZWJ 组合 e\u0301 A\u0300 全角 \uFF21\uFF22" +
		" 与 ANSI \x1b[31m红色\x1b[0m http://127.0.0.1:49155/vnc.html?resize=scale " +
		"很长的中文说明文字".repeat(6);
	const entry = { ...RICH_ENTRY, "access-entries": [tricky], "collection-errors": [] };
	for (const width of [12, 20, 31, 47]) {
		const host = { terminal: { rows: 18 }, requestRender() {} };
		const viewer = createEntryViewer(entry, host, undefined, () => {}, undefined, engine);
		const lines = viewer.render(width);
		assert.equal(lines.length, 18);
		for (const line of lines) {
			const w = tui.visibleWidth(line);
			assert.ok(w <= width, `w=${width} 越宽 ${w}: ${JSON.stringify(line)}`);
		}
	}
	// 大表情/组合/ANSI 内容不得被丢掉
	const host = { terminal: { rows: 40 }, requestRender() {} };
	const viewer = createEntryViewer(entry, host, undefined, () => {}, undefined, engine);
	const restored = viewer.render(31).map((line) => line.replace(/^ {2}/, "")).join("");
	assert.ok(restored.includes("\u{1F600}"), "emoji 应保留");
	assert.ok(restored.includes("e\u0301"), "组合字符应保留");
	assert.ok(restored.includes("红色"), "ANSI 内文字应保留");
});

let failed = 0;
for (const { name, fn } of cases) {
	try {
		await fn();
		console.log(`ok - ${name}`);
	} catch (err) {
		failed++;
		console.error(`FAIL - ${name}\n  ${err?.message ?? err}`);
	}
}
console.log(failed === 0 ? `\n全部 ${cases.length} 项通过` : `\n${failed}/${cases.length} 项失败`);
process.exit(failed === 0 ? 0 : 1);
