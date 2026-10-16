// D022 mailbox_listen 工具 schema 真实性冒烟.
//
// 目的: mailbox_listen 的 parameters 是普通 JSON Schema 对象 (不用 TypeBox
// import, 以便 node 原生 TS stripping 加载), 需证明 pi 实际使用的校验器
// (typebox/compile 的 Compile, 即 @earendil-works/pi-ai 参数校验底层) 接受
// 该 schema 并正确判定合法/非法输入. 不调用模型, 不连真实 mailbox.
//
// env: PI_SHIM      pi 可执行 shim 路径 (用于定位 pi 包目录 → typebox)
//      LISTEN_EXT   pi-extension/index.ts 绝对路径
import { createRequire } from "node:module";
import { readFileSync, realpathSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const results = [];
function check(name, ok) { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${name}`); }

const shim = process.env.PI_SHIM;
const ext = process.env.LISTEN_EXT;

// pi shim 里的 cmd-shim-target 指向 dist/bundle/cli.js; 包根 = 上三层
const shimSrc = readFileSync(shim, "utf-8");
const target = shimSrc.match(/cmd-shim-target=(.+)/)?.[1]?.trim();
if (!target) { console.error("无法从 pi shim 解析 cmd-shim-target"); process.exit(2); }
const pkgRoot = realpathSync(resolve(dirname(target), "..", ".."));
const req = createRequire(`${pkgRoot}/package.json`);
const compilePath = req.resolve("typebox/compile"); // pi 实际使用的校验器
const { Compile } = await import(pathToFileURL(compilePath).href);

// 加载扩展工厂 (node 原生 TS type stripping), 捕获注册的工具
globalThis.__dirname = dirname(ext);
const tools = {};
const pi = {
  on: () => {},
  registerCommand: () => {},
  registerTool: (def) => { tools[def.name] = def; },
  sendUserMessage: () => {},
};
const mod = await import(ext);
mod.default(pi);

const tool = tools["mailbox_listen"];
check("扩展注册了 mailbox_listen 工具", typeof tool === "object" && tool !== null);
check("工具 name/label/description 齐备", tool.name === "mailbox_listen" && !!tool.label && !!tool.description);
check("工具 execute 是函数", typeof tool.execute === "function");
check("parameters 是普通对象 (非 TypeBox 构造)", typeof tool.parameters === "object" && tool.parameters !== null);

// 真实校验器: pi 用 Compile(schema).Check(args) 判参数
let validator;
try {
  validator = Compile(tool.parameters);
  check("typebox Compile 接受该 schema", true);
} catch (e) {
  check(`typebox Compile 接受该 schema (${String(e)})`, false);
}
if (validator) {
  check("合法 {action:start} 通过", validator.Check({ action: "start" }) === true);
  check("合法 {action:stop} 通过", validator.Check({ action: "stop" }) === true);
  check("非法 action 被拒", validator.Check({ action: "bogus" }) === false);
  check("缺 action 被拒", validator.Check({}) === false);
  check("多余字段被拒 (additionalProperties=false)", validator.Check({ action: "start", x: 1 }) === false);
}

const failed = results.filter((ok) => !ok).length;
console.log(`${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
