// ponytail-config: mode resolution, defaults, deactivation detection.
//
// Default mode resolution order:
//   1. PONYTAIL_DEFAULT_MODE environment variable
//   2. Config file: ~/.config/ponytail/config.json (macOS/Linux)
//                   %APPDATA%\ponytail\config.json (Windows)
//   3. 'full'

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

export const DEFAULT_MODE = "full" as const;
const VALID_MODES = ["off", "lite", "full", "ultra", "review"] as const;
const RUNTIME_MODES = ["off", "lite", "full", "ultra"] as const;

export type ValidMode = (typeof VALID_MODES)[number];
export type RuntimeMode = (typeof RUNTIME_MODES)[number];

export function normalizeMode(mode: string): RuntimeMode | null {
  const normalized = mode.trim().toLowerCase();
  return (RUNTIME_MODES as readonly string[]).includes(normalized)
    ? (normalized as RuntimeMode)
    : null;
}

export function normalizeConfigMode(mode: string): ValidMode | null {
  const normalized = mode.trim().toLowerCase();
  return (VALID_MODES as readonly string[]).includes(normalized)
    ? (normalized as ValidMode)
    : null;
}

export function normalizePersistedMode(mode: string): ValidMode | null {
  return normalizeMode(mode) ?? normalizeConfigMode(mode);
}

// "stop ponytail" / "normal mode" turn ponytail off, but only as a standalone
// command. The whole message must be the command, ignoring case and trailing
// punctuation, to avoid false positives like "add a normal mode toggle".
export function isDeactivationCommand(text: string): boolean {
  const t = text.trim().toLowerCase().replace(/[.!?\s]+$/, "");
  return t === "stop ponytail" || t === "normal mode";
}

function getConfigDir(): string {
  if (process.env.XDG_CONFIG_HOME) {
    return path.join(process.env.XDG_CONFIG_HOME, "ponytail");
  }
  if (process.platform === "win32") {
    return path.join(
      process.env.APPDATA ?? path.join(os.homedir(), "AppData", "Roaming"),
      "ponytail",
    );
  }
  return path.join(os.homedir(), ".config", "ponytail");
}

function getConfigPath(): string {
  return path.join(getConfigDir(), "config.json");
}

export function getDefaultMode(): ValidMode {
  // 1. Environment variable (highest priority)
  const envMode = process.env.PONYTAIL_DEFAULT_MODE;
  if (envMode && (VALID_MODES as readonly string[]).includes(envMode.toLowerCase())) {
    return envMode.toLowerCase() as ValidMode;
  }

  // 2. Config file
  try {
    const configPath = getConfigPath();
    const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
    if (
      config.defaultMode &&
      (VALID_MODES as readonly string[]).includes(config.defaultMode.toLowerCase())
    ) {
      return config.defaultMode.toLowerCase() as ValidMode;
    }
  } catch {
    // Config file doesn't exist or is invalid — fall through
  }

  // 3. Default
  return DEFAULT_MODE;
}

export function writeDefaultMode(mode: string): ValidMode | null {
  const normalized = normalizeConfigMode(mode);
  if (!normalized) return null;

  const configPath = getConfigPath();
  fs.mkdirSync(path.dirname(configPath), { recursive: true });
  fs.writeFileSync(
    configPath,
    JSON.stringify({ defaultMode: normalized }, null, 2),
    "utf8",
  );
  return normalized;
}
