import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";

/**
 * git-push-guard: 拦截 agent 发起的 git push, 向用户确认后才放行.
 *
 * 匹配逻辑:
 *   - 命令包含 "git push" (简单子串匹配, 兼顾 flag/remote/branch 等变体)
 *   - 排除 "git pushd", "git push-url" 等非 push 操作
 */

const PUSH_PATTERN = /\bgit\s+push\b/;

export default function (_pi: ExtensionAPI) {
  _pi.on("tool_call", async (event, ctx) => {
    if (!isToolCallEventType("bash", event)) return;
    const cmd = event.input.command ?? "";

    if (PUSH_PATTERN.test(cmd)) {
      const ok = await ctx.ui.confirm(
        "git push 拦截",
        `agent 正在执行:\n\n${cmd}\n\n是否允许?`,
      );
      if (!ok) {
        return { block: true, reason: "用户拒绝 git push" };
      }
    }
  });
}
