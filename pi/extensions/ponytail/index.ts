// ponytail pi extension: registers commands, listens to lifecycle events,
// injects ponytail instructions into the system prompt.

import type { ExtensionAPI, ExtensionCommandContext, SessionEntry } from "@earendil-works/pi-coding-agent";
import {
  DEFAULT_MODE,
  getDefaultMode,
  normalizeMode,
  normalizeConfigMode,
  normalizePersistedMode,
  isDeactivationCommand,
  writeDefaultMode,
  type ValidMode,
  type RuntimeMode,
} from "./config.js";
import { getPonytailInstructions } from "./instructions.js";

function resolveSessionMode(
  entries: SessionEntry[] | undefined,
  fallbackMode: ValidMode,
): ValidMode {
  const fallback = normalizePersistedMode(fallbackMode) ?? DEFAULT_MODE;
  if (!Array.isArray(entries)) return fallback;

  for (let i = entries.length - 1; i >= 0; i -= 1) {
    const entry = entries[i];
    if (entry?.type !== "custom" || entry.customType !== "ponytail-mode") continue;
    const mode = normalizePersistedMode((entry.data as { mode?: string } | undefined)?.mode);
    if (mode) return mode;
  }

  return fallback;
}

function parsePonytailCommand(
  text: string,
  defaultMode: ValidMode,
): ParsedCommand {
  const fallback = normalizePersistedMode(defaultMode) ?? DEFAULT_MODE;
  const normalizedText = text.trim().toLowerCase();

  if (!normalizedText) {
    return { type: "set-mode", mode: fallback === "off" ? "full" : fallback };
  }

  const parts = normalizedText.split(/\s+/);
  const primary = parts[0];
  const secondary = parts[1];

  if (primary === "status") return { type: "status" };

  if (primary === "default") {
    const mode = normalizeConfigMode(secondary ?? "");
    return mode
      ? { type: "set-default", mode }
      : { type: "invalid", reason: "invalid-default-mode" };
  }

  const mode = normalizeMode(primary ?? "");
  return mode
    ? { type: "set-mode", mode }
    : { type: "invalid", reason: "invalid-mode", mode: primary ?? "" };
}

type ParsedCommand =
  | { type: "set-mode"; mode: ValidMode }
  | { type: "status" }
  | { type: "set-default"; mode: ValidMode }
  | { type: "invalid"; reason: string; mode?: string };

export default function ponytailExtension(pi: ExtensionAPI) {
  let currentMode: ValidMode = DEFAULT_MODE;
  let configuredDefaultMode = getDefaultMode();

  const setMode = (mode: ValidMode, ctx?: ExtensionCommandContext) => {
    const normalized = normalizePersistedMode(mode);
    if (!normalized) return;
    currentMode = normalized;
    pi.appendEntry("ponytail-mode", { mode: normalized });
    ctx?.ui?.notify?.(`Ponytail mode set to ${normalized}.`, "info");
  };

  const sendAlias = (skillName: string, args: string, ctx: ExtensionCommandContext) => {
    const normalized = args.trim();
    const message = normalized ? `${skillName} ${normalized}` : skillName;

    if (ctx?.isIdle?.() === false) {
      pi.sendUserMessage(message, { deliverAs: "followUp" });
      ctx?.ui?.notify?.(`${skillName} queued as follow-up.`, "info");
      return;
    }

    pi.sendUserMessage(message);
  };

  pi.registerCommand("ponytail", {
    description: "Set or report Ponytail mode",
    handler: async (args, ctx) => {
      const parsed = parsePonytailCommand(args, configuredDefaultMode);

      if (parsed.type === "status") {
        ctx.ui.notify(
          `Ponytail: current ${currentMode} • default ${configuredDefaultMode}`,
          "info",
        );
        return;
      }

      if (parsed.type === "set-default") {
        const written = writeDefaultMode(parsed.mode);
        if (written) {
          configuredDefaultMode = getDefaultMode();
          const message =
            configuredDefaultMode === written
              ? `Default Ponytail mode set to ${written}.`
              : `Saved default ${written}, but env override keeps default at ${configuredDefaultMode}.`;
          ctx.ui.notify(message, "info");
        }
        return;
      }

      if (parsed.type === "set-mode") {
        setMode(parsed.mode, ctx);
        return;
      }

      ctx.ui.notify("Unknown or unsupported /ponytail mode.", "warning");
    },
  });

  pi.registerCommand("ponytail-review", {
    description: "Run /skill:ponytail-review",
    handler: (_args, ctx) => sendAlias("/skill:ponytail-review", "", ctx),
  });

  pi.registerCommand("ponytail-audit", {
    description: "Run /skill:ponytail-audit",
    handler: (_args, ctx) => sendAlias("/skill:ponytail-audit", "", ctx),
  });

  pi.registerCommand("ponytail-gain", {
    description: "Run /skill:ponytail-gain",
    handler: (_args, ctx) => sendAlias("/skill:ponytail-gain", "", ctx),
  });

  pi.registerCommand("ponytail-debt", {
    description: "Run /skill:ponytail-debt",
    handler: (_args, ctx) => sendAlias("/skill:ponytail-debt", "", ctx),
  });

  pi.registerCommand("ponytail-help", {
    description: "Run /skill:ponytail-help",
    handler: (_args, ctx) => sendAlias("/skill:ponytail-help", "", ctx),
  });

  pi.on("input", async (event) => {
    if (event?.source === "extension") return;
    const text = String(event?.text ?? "");
    if (currentMode !== "off" && isDeactivationCommand(text)) {
      setMode("off");
    }
  });

  pi.on("session_start", async (_event, ctx) => {
    const entries =
      ctx?.sessionManager?.getBranch?.() ?? ctx?.sessionManager?.getEntries?.() ?? [];
    configuredDefaultMode = getDefaultMode();
    currentMode = resolveSessionMode(entries as SessionEntry[], configuredDefaultMode);
  });

  pi.on("before_agent_start", async (event) => {
    if (!currentMode || currentMode === "off") return;
    return {
      systemPrompt: `${event.systemPrompt}\n\n${getPonytailInstructions(currentMode)}`,
    };
  });
}
