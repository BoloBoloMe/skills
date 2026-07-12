/**
 * uv-python-hook.ts
 *
 * 让 shell 中的 `python`、`python3` 命令通过 `uv run python` 执行
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

const PYTHON_COMMAND =
  /(?:^|[;&|(){}\n]|\b(?:if|then|elif|else|while|until|do|time|!)\s+)\s*(?:\w+=\S+\s+)*(?:python|python3)(?=\s|$)/m;
const UV_PYTHON_FUNCTIONS =
  'python() { uv run python "$@"; }; python3() { uv run python "$@"; };';

export function transformPythonCmd(cmd: string): string {
  if (cmd.startsWith(`${UV_PYTHON_FUNCTIONS}\n`)) return cmd;
  return PYTHON_COMMAND.test(cmd) ? `${UV_PYTHON_FUNCTIONS}\n${cmd}` : cmd;
}