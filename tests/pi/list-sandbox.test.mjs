// /list-sandbox pi 扩展纯函数测试 (swt-list-sandbox M2, 接缝 A).
// 运行: node tests/pi/list-sandbox.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseListLine, buildSelectItems, modeRoutePlan } from "../../workflow/use-sandbox-worktree/pi-extension/index.ts";

/** 扩展源码文本 (静态断言用, 接缝 A: BR-010/BR-007 审计). */
const SRC = readFileSync(
	new URL("../../workflow/use-sandbox-worktree/pi-extension/index.ts", import.meta.url),
	"utf-8",
);

const cases = [];
const test = (name, fn) => cases.push({ name, fn });

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
		assert.ok(snippet.includes("SCRIPT"), "子进程参数须引用 skill 内 swt.py 路径");
		assert.ok(snippet.includes('"list"'), "子进程参数须为 list 子命令");
	}
	assert.ok(!/["']podman["']/.test(SRC), "源码不得直调 podman");
});

test("源码不含会话注入调用 (BR-007 静态部分)", () => {
	assert.ok(!/sendUserMessage|sendMessage/.test(SRC), "不得调用会话注入 API");
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
