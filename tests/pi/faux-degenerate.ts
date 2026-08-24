/**
 * 临时验证扩展: 注册 faux provider, 脚本化输出含退化重复的 thinking 流.
 * 用法:
 *   退化场景: pi --mode json --model faux-degenerate/degenerate-1 -p "测试"
 *   正常对照: FAUX_CLEAN=1 pi --model faux-degenerate/degenerate-1 -p "测试"
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { createFauxCore, fauxAssistantMessage, fauxText, fauxThinking } from "@earendil-works/pi-ai";

const normalThinking =
  "<thinking>\nLet me analyze the task step by step.\nFirst, check the sync script behavior.\nThen verify extension loading paths.\nFinally, summarize findings.\n</thinking>\n查同步位置: ";

const clean = process.env.FAUX_CLEAN === "1";
const junk = "　<br>".repeat(4000); // 20K 字符退化重复 (实测同款单元)
const thinking = clean ? normalThinking + "正常收尾, 一切顺利.".repeat(50) : normalThinking + junk;

const faux = createFauxCore({
  provider: "faux-degenerate",
  models: [
    {
      id: "degenerate-1",
      name: "Degenerate Test 1",
      reasoning: true,
      input: ["text"],
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      contextWindow: 100000,
      maxTokens: 65536,
    },
  ],
  tokensPerSecond: 20000,
});

const modelDef = {
  id: "degenerate-1",
  name: "Degenerate Test 1",
  reasoning: true,
  input: ["text"],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  contextWindow: 100000,
  maxTokens: 65536,
};

faux.setResponses([
  fauxAssistantMessage([fauxThinking(thinking), fauxText(clean ? "正常完成." : "不该走到这里")]),
]);

export default function (pi: ExtensionAPI) {
  pi.registerProvider("faux-degenerate", {
    name: "faux-degenerate",
    baseUrl: "http://localhost:9/v1", // 不会真实调用 (streamSimple 接管)
    apiKey: "faux-local-key",
    api: faux.api as never,
    models: [modelDef],
    streamSimple: faux.streamSimple,
  });
}
