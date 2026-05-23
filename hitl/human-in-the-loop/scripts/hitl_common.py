#!/usr/bin/env python3
"""Shared helpers for HITL 0.0.1 scripts.

Contract: this module intentionally implements a small YAML subset so the MVP
scripts run without external dependencies. Assets should use plain mappings,
lists, strings, booleans, numbers, and null values; advanced YAML features are
rejected by convention rather than silently interpreted.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
ASSET_REF_RE = re.compile(r"^(planning/(facts|design|blueprint|implementation-package|reassessment)|checks/asset-check|execution/(plan|runbook|ledger|unit-summary|verification|close))@v([1-9][0-9]*)$")
HUMAN_VIEW_REF = "human-view@current"
HISTORICAL_STATES = {"superseded", "retired", "failed", "closed"}
VALID_STATES = {"draft", "ready-for-approval", "approved", "ready-for-confirmation", "confirmed", "in-progress", "blocked", "completed", "failed", "superseded", "retired", "closed"}
VALID_STAGES = {"intake", "facts", "design", "blueprint", "implementation-package", "asset-check", "plan", "runbook", "execute", "verify", "close", "reassessment"}
VALID_ROLES = {"content-asset", "approval-target", "confirmation-target", "check-record", "execution-record", "evidence-record", "close-record", "audit-record", "derived-human-view"}
VALID_KINDS = {"agent-asset", "derived-human-view"}
FORBIDDEN_AGENT_ASSET_FIELDS = {"lifecycle_state", "record_role", "owner_skill", "owner_protocol", "approval", "confirmation", "human_view", "agent_view"}
PLACEHOLDER_RE = re.compile(r"<[^>]+>|@vN\b|TBD|TODO|待补充", re.IGNORECASE)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
CHANGE_DIR_RE = re.compile(r"^[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaffA-Za-z0-9][\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaffA-Za-z0-9_-]{0,80}$")


def now_utc() -> str:
    """Return a stable UTC timestamp string for persisted audit fields."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    """Hash an existing file as bytes; callers surface OSError as validation failure."""
    return sha256(path.read_bytes()).hexdigest()


def canonical_json(data: Any) -> str:
    """Serialize payload deterministically while preserving source mapping order.

    Contract: human-view rendering relies on insertion order from manifest and
    agent YAML assets; callers build payloads in stable order before hashing.
    """
    return json.dumps(data, ensure_ascii=False, sort_keys=False, separators=(",", ":"))


def hash_text(text: str) -> str:
    """Hash UTF-8 text with no platform newline normalization."""
    return sha256(text.encode("utf-8")).hexdigest()


def strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value[1:-1]
    return value


def parse_scalar(value: str) -> Any:
    """Parse the scalar subset used by HITL fixtures and generated manifests."""
    value = value.strip()
    if value == "" or value == "null" or value == "~":
        return None
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    if re.fullmatch(r"-?[0-9]+", value):
        try:
            return int(value)
        except ValueError:
            pass
    return strip_quotes(value)


def _clean_lines(text: str) -> list[tuple[int, str]]:
    rows = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        rows.append((indent, raw.strip()))
    return rows


def _parse_block(rows: list[tuple[int, str]], idx: int, indent: int) -> tuple[Any, int]:
    if idx < len(rows) and rows[idx][0] == indent and rows[idx][1] in {"[]", "{}"}:
        return ([] if rows[idx][1] == "[]" else {}), idx + 1
    is_list = idx < len(rows) and rows[idx][0] == indent and (rows[idx][1] == "-" or rows[idx][1].startswith("- "))
    if is_list:
        out = []
        while idx < len(rows) and rows[idx][0] == indent and (rows[idx][1] == "-" or rows[idx][1].startswith("- ")):
            item = rows[idx][1][1:].strip()
            idx += 1
            if not item:
                val, idx = _parse_block(rows, idx, indent + 2)
                out.append(val)
            elif ":" in item and not item.startswith(('"', "'")):
                key, raw = item.split(":", 1)
                obj = {key.strip(): parse_scalar(raw)}
                if raw.strip() == "" and idx < len(rows) and rows[idx][0] > indent:
                    obj[key.strip()], idx = _parse_block(rows, idx, rows[idx][0])
                while idx < len(rows) and rows[idx][0] == indent + 2 and not rows[idx][1].startswith("- "):
                    k, v = rows[idx][1].split(":", 1)
                    idx += 1
                    obj[k.strip()] = parse_scalar(v)
                    if v.strip() == "" and idx < len(rows) and rows[idx][0] > indent + 2:
                        obj[k.strip()], idx = _parse_block(rows, idx, rows[idx][0])
                out.append(obj)
            else:
                out.append(parse_scalar(item))
        return out, idx
    out = {}
    while idx < len(rows) and rows[idx][0] == indent and not rows[idx][1].startswith("- "):
        if ":" not in rows[idx][1]:
            raise ValueError(f"invalid YAML line: {rows[idx][1]}")
        key, raw = rows[idx][1].split(":", 1)
        idx += 1
        if raw.strip() == "" and idx < len(rows) and rows[idx][0] > indent:
            out[key.strip()], idx = _parse_block(rows, idx, rows[idx][0])
        elif raw.strip() == "" and idx < len(rows) and rows[idx][0] == indent + 2 and rows[idx][1] in {"[]", "{}"}:
            out[key.strip()] = [] if rows[idx][1] == "[]" else {}
            idx += 1
        else:
            out[key.strip()] = parse_scalar(raw)
    return out, idx


def parse_yaml_subset(text: str) -> Any:
    """Parse a conservative YAML subset; JSON input is accepted as well."""
    stripped = text.strip()
    if not stripped:
        return {}
    if stripped[0] in "[{":
        return json.loads(stripped)
    rows = _clean_lines(text)
    if not rows:
        return {}
    data, idx = _parse_block(rows, 0, rows[0][0])
    if idx != len(rows):
        raise ValueError("unparsed YAML tail")
    return data


def load_yaml_document(path: Path) -> dict[str, Any]:
    """Load raw YAML or the first YAML fence that contains a mapping."""
    text = path.read_text(encoding="utf-8")
    blocks = FENCE_RE.findall(text) or [text]
    for block in blocks:
        data = parse_yaml_subset(block)
        if isinstance(data, dict):
            return data
    raise ValueError(f"no mapping YAML found: {path}")


def require_manifest_yaml_path(path: Path) -> None:
    """Enforce the only supported manifest filename.

    Contract: HITL 0.0.1 intentionally rejects alternate manifest names;
    callers must pass the package root's exact manifest.yaml path.
    """
    if path.name != "manifest.yaml":
        raise ValueError("HITL manifest path must be manifest.yaml")


def load_manifest(path: Path) -> dict[str, Any]:
    """Return the raw manifest.yaml mapping.

    Contract: HITL 0.0.1 uses `manifest.yaml` directly as the sole fact source;
    Markdown wrappers and alternate manifest filenames are not accepted.
    """
    require_manifest_yaml_path(path)
    data = parse_yaml_subset(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("protocol") == "HITL":
        return data
    raise ValueError("manifest.yaml must contain a HITL manifest mapping")


def yaml_quote(value: str) -> str:
    if value == "" or any(ch in value for ch in ":#[]{}\n") or value.strip() != value or value in {"true", "false", "null"}:
        return json.dumps(value, ensure_ascii=False)
    return value


def dump_yaml(data: Any, indent: int = 0) -> str:
    """Dump the small YAML subset used by generated HITL assets."""
    sp = " " * indent
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{sp}{key}:")
                lines.append(dump_yaml(value, indent + 2))
            else:
                lines.append(f"{sp}{key}: {dump_yaml(value, 0).strip()}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{sp}[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{sp}-")
                lines.append(dump_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{sp}-")
                lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{sp}- {dump_yaml(item, 0).strip()}")
        return "\n".join(lines)
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "true" if data else "false"
    if isinstance(data, int):
        return str(data)
    return yaml_quote(str(data))


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Persist the raw manifest.yaml as the only business fact source."""
    require_manifest_yaml_path(path)
    path.write_text(dump_yaml(manifest) + "\n", encoding="utf-8")


def write_manifest_and_refresh(path: Path, manifest: dict[str, Any]) -> None:
    """Persist manifest mutations and refresh the derived reviewer view.

    Contract: HITL human-view payload contains manifest state, so gate,
    workflow, pointer, and decision changes must not leave stale HTML hashes.
    """
    write_manifest(path, manifest)
    refresh_human_view(path)


def registry(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    items = manifest.setdefault("asset_registry", [])
    if not isinstance(items, list):
        raise ValueError("manifest.asset_registry must be a list")
    return items


def find_registry_item(manifest: dict[str, Any], ref: str) -> dict[str, Any] | None:
    for item in registry(manifest):
        if isinstance(item, dict) and item.get("asset_ref") == ref:
            return item
    return None


def registry_item_by_ref(manifest: dict[str, Any], ref: str) -> dict[str, Any]:
    """Return a registered asset or fail fast for ref-driven script APIs."""
    item = find_registry_item(manifest, ref)
    if not item:
        raise ValueError(f"asset_ref not registered: {ref}")
    return item


def is_historical_state(state: str | None) -> bool:
    """Classify archive-only states; completed remains a current state."""
    return str(state) in HISTORICAL_STATES


def asset_ref_parts(ref: str) -> tuple[str, str, int]:
    """Parse a semantic HITL asset ref and derive its globally unique artifact.

    Boundary: physical paths are not encoded in asset_ref; registry.path remains
    the source of the asset's current location.
    """
    match = ASSET_REF_RE.match(ref)
    if not match:
        raise ValueError(f"invalid HITL asset_ref: {ref}")
    prefix, version = ref.rsplit("@v", 1)
    artifact = prefix.rsplit("/", 1)[1]
    return prefix, artifact, int(version)


def expected_asset_path(asset_ref: str, artifact: str, lifecycle_state: str) -> str:
    """Return the only valid physical path for an agent asset state."""
    _, ref_artifact, version = asset_ref_parts(asset_ref)
    if artifact != ref_artifact:
        raise ValueError(f"artifact {artifact} does not match asset_ref {asset_ref}")
    root = "agent/archive" if is_historical_state(lifecycle_state) else "agent"
    return f"{root}/{artifact}.v{version}.yaml"


def resolve_asset_path(manifest_path: Path, manifest: dict[str, Any], asset_ref: str) -> Path:
    """Resolve a semantic ref through manifest.asset_registry.path.

    Contract: scripts must not accept agent asset paths from users; this helper
    is the only supported bridge from ref to current physical file.
    """
    item = registry_item_by_ref(manifest, asset_ref)
    path = item.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError(f"registry path missing for {asset_ref}")
    return manifest_path.parent / path


def validate_latest_asset_check_binding(
    manifest_path: Path,
    manifest: dict[str, Any],
    target_ref: str,
    check_mode: str,
    workspace: str | None = None,
) -> list[str]:
    """Validate the current asset-check audit record for a gate transition.

    Contract: asset-check records bind target path/hash/state and the check mode.
    Reviewer-view hashes are recorded as evidence, while the caller still reruns
    `transform_human_view.py --check` because the current view includes the
    asset-check record itself and is therefore self-referential.
    """
    errors: list[str] = []
    pointers = manifest.get("current_pointers") or {}
    check_ref = pointers.get("latest_asset_check")
    if not isinstance(check_ref, str) or not check_ref.startswith("checks/asset-check@"):
        return ["current_pointers.latest_asset_check must point to checks/asset-check@vN"]
    check_item = find_registry_item(manifest, check_ref)
    if not check_item:
        return [f"latest asset-check not registered: {check_ref}"]
    if check_item.get("lifecycle_state") != "completed":
        errors.append("latest asset-check state must be completed")
    try:
        record = load_yaml_document(resolve_asset_path(manifest_path, manifest, check_ref))
        target_item = registry_item_by_ref(manifest, target_ref)
        target_path = manifest_path.parent / str(target_item.get("path"))
        _validate_asset_check_record(record, target_ref, check_mode, target_item, target_path, workspace, errors)
    except Exception as exc:
        errors.append(str(exc))
    return errors


def _validate_asset_check_record(
    record: dict[str, Any],
    target_ref: str,
    check_mode: str,
    target_item: dict[str, Any],
    target_path: Path,
    workspace: str | None,
    errors: list[str],
) -> None:
    """Check a completed/pass asset-check record against current target facts."""
    if record.get("artifact") != "asset-check":
        errors.append("latest asset-check artifact must be asset-check")
    if record.get("result") != "pass":
        errors.append("latest asset-check result must be pass")
    if record.get("check_mode") != check_mode:
        errors.append(f"latest asset-check check_mode must be {check_mode}")
    if record.get("target_ref") != target_ref:
        errors.append(f"latest asset-check target_ref must be {target_ref}")
    if record.get("target_path") != target_item.get("path"):
        errors.append("latest asset-check target_path drift")
    if record.get("target_lifecycle_state") != target_item.get("lifecycle_state"):
        errors.append("latest asset-check target_lifecycle_state drift")
    if not target_path.exists() or record.get("target_sha256") != sha256_file(target_path):
        errors.append("latest asset-check target_sha256 drift")
    if check_mode == "final" and workspace is not None:
        expected_workspace = str(Path(workspace).resolve()).replace("\\", "/")
        if record.get("workspace") != expected_workspace:
            errors.append("latest asset-check workspace drift")
    view_hashes = record.get("reviewer_view_hashes")
    if not isinstance(view_hashes, dict) or not view_hashes.get("html_sha256") or not view_hashes.get("payload_sha256"):
        errors.append("latest asset-check reviewer_view_hashes required")


def forbidden_asset_field_errors(data: dict[str, Any], label: str = "agent asset") -> list[str]:
    """Return fields that would move manifest-owned facts into agent YAML.

    Contract: lifecycle, role, approval, confirmation, and human-view facts are
    manifest boundaries. Agent assets may describe work, but must never persist
    decision authority or derived-view state in their own body.
    """
    forbidden = sorted(FORBIDDEN_AGENT_ASSET_FIELDS & set(data))
    return [f"{label} must not contain manifest-owned field: {name}" for name in forbidden]


def validate_forbidden_asset_fields(data: dict[str, Any], label: str = "agent asset") -> None:
    """Reject manifest-owned fields in an agent YAML mapping before writing."""
    errors = forbidden_asset_field_errors(data, label)
    if errors:
        raise ValueError("; ".join(errors))


def validate_asset_header_matches(data: dict[str, Any], asset_ref: str, artifact: str) -> None:
    """Check immutable YAML header fields before registration or validation."""
    if data.get("asset_ref") != asset_ref:
        raise ValueError("asset_ref header does not match argument")
    if data.get("artifact") != artifact:
        raise ValueError("artifact header does not match argument")
    if str(data.get("schema_version")) != "0.0.1":
        raise ValueError("schema_version must be 0.0.1")


def current_registry_items_for_artifact(manifest: dict[str, Any], artifact: str) -> list[dict[str, Any]]:
    """Find non-archive entries for one artifact to enforce one current version."""
    out = []
    for item in registry(manifest):
        if not isinstance(item, dict) or item.get("asset_ref") == HUMAN_VIEW_REF:
            continue
        try:
            _, item_artifact, _ = asset_ref_parts(str(item.get("asset_ref")))
        except ValueError:
            continue
        if item_artifact == artifact and not is_historical_state(item.get("lifecycle_state")):
            out.append(item)
    return out


def write_agent_asset_data(
    manifest_path: Path,
    asset_ref: str,
    artifact: str,
    state: str,
    role: str,
    text: str,
    replace_draft: bool = False,
) -> Path:
    """Write/register an agent asset using the canonical flat layout.

    Preconditions: `text` is raw YAML containing matching asset_ref/artifact and
    schema_version 0.0.1. Incompatible boundary: legacy phase-specific
    asset directories are never created or accepted.
    """
    manifest = load_manifest(manifest_path)
    data = parse_yaml_subset(text)
    if not isinstance(data, dict):
        raise ValueError("agent asset YAML must be a mapping")
    validate_forbidden_asset_fields(data)
    validate_asset_header_matches(data, asset_ref, artifact)
    if state not in VALID_STATES:
        raise ValueError(f"invalid lifecycle state: {state}")
    if is_historical_state(state):
        raise ValueError("write_agent_asset.py cannot create historical assets; use archive_asset.py")
    if role not in VALID_ROLES - {"derived-human-view"}:
        raise ValueError(f"invalid record role: {role}")
    target_rel = expected_asset_path(asset_ref, artifact, state)
    target = manifest_path.parent / target_rel
    existing = find_registry_item(manifest, asset_ref)
    if replace_draft and not existing:
        raise ValueError("--replace-draft requires an existing registered draft")
    if existing:
        _check_replace_allowed(existing, replace_draft)
        if replace_draft and existing.get("path") != target_rel:
            raise ValueError("registered draft path does not match canonical target")
    _check_single_current(manifest, asset_ref, artifact, state, replace_draft)
    _check_interrogation_gate_for_write(manifest, asset_ref, state)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not replace_draft:
        raise ValueError(f"asset already exists: {target_rel}")
    if replace_draft and not target.exists():
        raise ValueError(f"registered draft file missing: {target_rel}")
    target.write_text(text.rstrip() + "\n", encoding="utf-8")
    _upsert_agent_registry(manifest, asset_ref, target_rel, state, role, sha256_file(target), existing)
    write_manifest(manifest_path, manifest)
    refresh_human_view(manifest_path)
    return target


def refresh_human_view(manifest_path: Path) -> None:
    """Regenerate the derived human view after every agent asset mutation.

    Contract: agent YAML and manifest changes must never leave a stale reviewer
    view. Initialization is the only flow that may leave human-view.html absent.
    """
    script = Path(__file__).with_name("transform_human_view.py")
    result = subprocess.run([sys.executable, str(script), "--manifest", str(manifest_path)], text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError("human-view refresh failed: " + (result.stdout + result.stderr).strip())


def _check_replace_allowed(existing: dict[str, Any], replace_draft: bool) -> None:
    """Protect evidence by allowing overwrite only for registered drafts."""
    if not replace_draft:
        raise ValueError(f"asset_ref already registered: {existing.get('asset_ref')}")
    if existing.get("lifecycle_state") != "draft":
        raise ValueError("--replace-draft requires existing lifecycle_state draft")


def _check_single_current(manifest: dict[str, Any], asset_ref: str, artifact: str, state: str, replace_draft: bool) -> None:
    """Prevent two current versions of the same artifact."""
    if is_historical_state(state):
        return
    for item in current_registry_items_for_artifact(manifest, artifact):
        same_ref = item.get("asset_ref") == asset_ref
        if not same_ref or not replace_draft:
            raise ValueError(f"current {artifact} already exists: {item.get('asset_ref')}")


def _gate_for_asset(asset_ref: str) -> str | None:
    """Map assets with pre-write interrogation requirements to their gate."""
    if asset_ref.startswith("planning/design@"):
        return "pre_design"
    if asset_ref.startswith("planning/blueprint@"):
        return "pre_blueprint"
    if asset_ref.startswith(("execution/plan@", "execution/runbook@")):
        return "pre_execution_plan"
    return None


def _check_interrogation_gate_for_write(manifest: dict[str, Any], asset_ref: str, state: str) -> None:
    """Allow unresolved gate assets only as draft; non-draft needs closed gate.

    Technical boundary: checks/asset-check records are audit assets and have no
    interrogation gate. Planning and execution assets that can be reviewed or
    executed must not appear non-draft before their corresponding gate closes.
    """
    if state == "draft":
        return
    gate = _gate_for_asset(asset_ref)
    if not gate:
        return
    from validate_interrogation_gate import validate_gate  # local import avoids cycle

    errors = validate_gate(manifest, gate, asset_ref)
    if errors:
        raise ValueError("; ".join(errors))


def _upsert_agent_registry(
    manifest: dict[str, Any],
    asset_ref: str,
    path: str,
    state: str,
    role: str,
    digest: str,
    existing: dict[str, Any] | None,
) -> None:
    """Synchronize registry path/hash/state after a canonical asset write."""
    now = now_utc()
    item = {
        "asset_ref": asset_ref,
        "asset_kind": "agent-asset",
        "path": path,
        "lifecycle_state": state,
        "record_role": role,
        "sha256": digest,
        "created_at": (existing or {}).get("created_at") or now,
        "last_state_change_at": now,
    }
    upsert_registry_item(manifest, item)
    manifest.setdefault("current_pointers", {})["active_agent_asset"] = asset_ref
    manifest["last_updated_at"] = now


def upsert_registry_item(manifest: dict[str, Any], item: dict[str, Any]) -> None:
    items = registry(manifest)
    for idx, existing in enumerate(items):
        if isinstance(existing, dict) and existing.get("asset_ref") == item.get("asset_ref"):
            items[idx] = item
            return
    items.append(item)


def normalize_manifest_for_human_view(manifest: dict[str, Any]) -> dict[str, Any]:
    """Remove self-referential current human-view hashes before payload hashing."""
    normalized = deepcopy(manifest)
    item = find_registry_item(normalized, HUMAN_VIEW_REF)
    if item:
        item["html_sha256"] = None
        item["payload_sha256"] = None
    return normalized


def safe_package_root(root: str, change_slug: str) -> Path:
    """Validate a Chinese one-segment change slug and return the target root."""
    if not CHANGE_DIR_RE.fullmatch(change_slug) or not CJK_RE.search(change_slug):
        raise SystemExit("invalid change_slug: use one safe directory segment containing Chinese characters")
    base = Path(root).resolve()
    target = (base / change_slug).resolve()
    if target != base and base not in target.parents:
        raise SystemExit("target escapes --root")
    return target


def validate_rel_path(value: Any, label: str, allow_glob: bool = False) -> str | None:
    """Validate POSIX workspace-relative path values used by HITL gates."""
    if not isinstance(value, str) or not value.strip() or value.strip() != value:
        return f"{label} invalid empty or padded path: {value}"
    if "\\" in value:
        return f"{label} must use POSIX relative path: {value}"
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:
        return f"{label} must not be absolute or contain parent traversal: {value}"
    if value in {".", ""}:
        return f"{label} must not target workspace root"
    if not allow_glob and any(ch in value for ch in "*?["):
        return f"{label} file path must not contain glob characters: {value}"
    return None


def norm_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        return [value]
    return []


def segment_glob_match(path: str, pattern: str) -> bool:
    """Match POSIX paths where * stays in-segment and ** spans segments."""
    path_parts = tuple(PurePosixPath(path).parts)
    pat_parts = tuple(PurePosixPath(pattern).parts)

    def rec(pi: int, gi: int) -> bool:
        if gi == len(pat_parts):
            return pi == len(path_parts)
        pat = pat_parts[gi]
        if pat == "**":
            return rec(pi, gi + 1) or (pi < len(path_parts) and rec(pi + 1, gi))
        if pi >= len(path_parts):
            return False
        return fnmatchcase(path_parts[pi], pat) and rec(pi + 1, gi + 1)

    return rec(0, 0)


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(path == pat or segment_glob_match(path, pat) for pat in patterns)


def contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(PLACEHOLDER_RE.search(value))
    if isinstance(value, list):
        return any(contains_placeholder(v) for v in value)
    if isinstance(value, dict):
        return any(contains_placeholder(v) for v in value.values())
    return False
