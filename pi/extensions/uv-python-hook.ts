/**
 * uv-python-hook.ts
 *
 * 将 `python`、`python3`、`python3.x` 命令转换为 `uv run python`
 * 适用于 LLM bash 工具调用和用户 `!`/`!!` 命令。
 *
 * 当 LLM 或用户编写 `python script.py` 时，钩子会
 * 透明地执行 `uv run python script.py` 作为替代。
 *
 * 存放位置：~/.pi/agent/extensions/uv-python-hook.ts
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType, createLocalBashOperations } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // Intercept LLM bash tool calls
  pi.on("tool_call", async (event, ctx) => {
    if (!isToolCallEventType("bash", event)) return;

    const original = event.input.command;
    const transformed = transformPythonCmd(original);
    if (transformed !== original) {
      ctx.ui.notify(`[uv-python-hook] python -> uv run python`, "info");
      event.input.command = transformed;
    }
  });

  // Intercept user ! / !! commands
  pi.on("user_bash", (event, ctx) => {
    const original = event.command;
    const transformed = transformPythonCmd(original);
    if (transformed === original) return;

    ctx.ui.notify(`[uv-python-hook] python -> uv run python`, "info");

    const local = createLocalBashOperations();
    return {
      operations: {
        exec(command, cwd, options) {
          return local.exec(transformPythonCmd(command), cwd, options);
        },
      },
    };
  });
}

function transformPythonCmd(cmd: string): string {
  // Protect heredoc content from false matches on lines starting with python
  const heredocs: string[] = [];
  const withPlaceholders = cmd.replace(
    /<<\s*(\w+).*?\r?\n[\s\S]*?\r?\n\s*\1(?=\s|$)/gm,
    (match) => {
      heredocs.push(match);
      return `__HEREDOC_${heredocs.length - 1}__`;
    },
  );

  // Transform python commands (^ with m flag covers newline-separated lines)
  const transformed = withPlaceholders.replace(
    /(?:^|&&|\|\||;|\|)\s*\bpython(?:3(?:\.\d+)?)?(?=\s|$)/gm,
    (match) => {
      const pythonStart = match.search(/\bpython/);
      return match.slice(0, pythonStart) + "uv run python";
    },
  );

  // Restore heredocs
  return transformed.replace(
    /__HEREDOC_(\d+)__/g,
    (_, idx) => heredocs[parseInt(idx as string)],
  );
}