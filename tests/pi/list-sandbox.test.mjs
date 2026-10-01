// /list-sandbox pi 扩展纯函数测试 (swt-list-sandbox M2, 接缝 A).
// 运行: node tests/pi/list-sandbox.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseListLine, buildSelectItems, modeRoutePlan, spawnGrouped, wrapToWidth, viewportHeight, scrollWindow } from "../../workflow/use-sandbox-worktree/pi-extension/index.ts";

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
