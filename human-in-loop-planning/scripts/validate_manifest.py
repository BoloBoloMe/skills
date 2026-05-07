#!/usr/bin/env python3
"""Validate a canonical HILP planning manifest.

Hardening added after v2.24 audit:
- load enum/required-field truth from references/shared/canonical-protocol-schema.yaml
- require owner fields on registry entries
- require current_assets.reapproval_log key and enforce phase-04 invalidation semantics
- reject unsafe manifest paths (absolute paths and parent traversal)
"""
import argparse
import re
import sys
from pathlib import Path, PurePosixPath

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
CANON_PATH = ROOT / "references/shared/canonical-protocol-schema.yaml"
FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
ASSET_REF_RE = re.compile(r"^(phase-\d{2})/([A-Za-z0-9_-]+)@v(\d+)$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def load_canonical():
    if CANON_PATH.exists():
        return yaml.safe_load(CANON_PATH.read_text(encoding="utf-8")) or {}
    return {}

CANON = load_canonical()
VALID_STATES = set(CANON.get("lifecycle_state_values", [])) or {"draft", "ready-for-review", "approved", "blocked", "superseded", "retired", "closed-record"}
VALID_ROLES = set(CANON.get("record_role_values", [])) or {"working-asset", "approval-record", "reapproval-record", "handoff-record", "archive-index"}
ROLE_STATE = {k: set(v or []) for k, v in (CANON.get("role_state_matrix") or {}).items()}
VALID_MODES = set(CANON.get("mode_values", [])) or {"preflight-scaffold", "standard", "strict"}
VALID_OWNER_SKILLS = set(CANON.get("owner_skill_values", [])) or {"human-in-loop-planning", "human-in-loop-execution"}
VALID_OWNER_PROTOCOLS = set(CANON.get("owner_protocol_values", [])) or {"HILP", "HILE"}
REQUIRED_CURRENT_ASSETS = CANON.get("current_assets_required_fields") or ["requirements_facts", "design_choice", "implementation_blueprint", "execution_handoff", "reapproval_log", "archive_index", "audit_trail"]
REQUIRED_POINTERS = CANON.get("current_pointers_required_fields") or ["human_review", "agent_directory", "latest_approved_design", "latest_approved_blueprint", "latest_handoff"]
REGISTRY_REQUIRED = CANON.get("asset_registry_required_fields") or ["asset_ref", "path", "human_view", "agent_view", "phase_id", "lifecycle_state", "record_role", "version", "owner_skill", "owner_protocol", "created_at", "last_state_change_at"]
EXPECTED_ASSET_TYPES = {
    "requirements_facts": ("phase-01", "requirements-facts"),
    "design_choice": ("phase-02", "design-choice"),
    "implementation_blueprint": ("phase-03", "implementation-blueprint"),
    "reapproval_log": ("phase-04", "reapproval"),
    "execution_handoff": ("phase-05", "execution-handoff"),
    "archive_index": ("phase-06", "archive-index"),
}
EXPECTED_POINTER_TYPES = {
    "latest_approved_design": ("phase-02", "design-choice", "approved", "approval-record"),
    "latest_approved_blueprint": ("phase-03", "implementation-blueprint", "approved", "approval-record"),
    "latest_handoff": ("phase-05", "execution-handoff", "closed-record", "handoff-record"),
}

# Phase/artifact-level semantic rules. These rules intentionally duplicate the
# human-readable workflow contract so impossible approval/handoff states cannot
# pass merely because they are not the current pointer.
ARTIFACT_ROLE_STATE_RULES = {
    ("phase-02", "design-choice", "approved"): "approval-record",
    ("phase-03", "implementation-blueprint", "approved"): "approval-record",
    ("phase-05", "execution-handoff", "closed-record"): "handoff-record",
}
ARTIFACT_ALLOWED_ROLES = {
    ("phase-01", "requirements-facts"): {"working-asset"},
    ("phase-02", "design-choice"): {"working-asset", "approval-record"},
    ("phase-03", "implementation-blueprint"): {"working-asset", "approval-record"},
    ("phase-04", "reapproval"): {"reapproval-record"},
    ("phase-05", "execution-handoff"): {"handoff-record"},
    ("phase-06", "archive-index"): {"archive-index"},
}

ARTIFACT_OWNER_PROTOCOL = {
    ("phase-01", "requirements-facts"): ("human-in-loop-planning", "HILP"),
    ("phase-02", "design-choice"): ("human-in-loop-planning", "HILP"),
    ("phase-03", "implementation-blueprint"): ("human-in-loop-planning", "HILP"),
    ("phase-04", "reapproval"): ("human-in-loop-planning", "HILP"),
    ("phase-05", "execution-handoff"): ("human-in-loop-execution", "HILE"),
    ("phase-06", "archive-index"): ("human-in-loop-planning", "HILP"),
}


def load_manifest(path: Path):
    text = path.read_text(encoding="utf-8")
    matches = FENCE_RE.findall(text)
    if not matches:
        raise ValueError("manifest must contain a yaml fenced block")
    for block in matches:
        data = yaml.safe_load(block)
        if isinstance(data, dict) and isinstance(data.get("manifest"), dict):
            return data["manifest"]
    raise ValueError("yaml block must contain top-level manifest mapping")


def require(cond, msg, errors):
    if not cond:
        errors.append(msg)


def parse_ref(ref):
    if not isinstance(ref, str):
        return None
    m = ASSET_REF_RE.match(ref)
    if not m:
        return None
    phase, artifact, version = m.groups()
    return {"phase": phase, "artifact": artifact, "version": int(version)}


def item_type(item):
    parsed = parse_ref(item.get("asset_ref")) if isinstance(item, dict) else None
    if parsed:
        return parsed["phase"], parsed["artifact"]
    return None, None


def resolve_pointer(value, refs_by_ref, refs_by_path):
    if not value:
        return None
    if value in refs_by_ref:
        return refs_by_ref[value]
    return refs_by_path.get(value)


def unsafe_path(value):
    if not isinstance(value, str) or not value or URL_RE.match(value) or ASSET_REF_RE.match(value):
        return False
    if "\\" in value:
        return True
    p = PurePosixPath(value)
    return p.is_absolute() or ".." in p.parts or value.strip() != value


def validate_path_value(label, value, errors):
    if unsafe_path(value):
        errors.append(f"unsafe path for {label}: {value}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--check-paths", action="store_true", help="Require non-null manifest paths to exist relative to the manifest directory")
    ap.add_argument("--allow-draft-paths", action="store_true", help="Permit missing paths only for draft/preflight scaffolds")
    args = ap.parse_args()
    path = Path(args.manifest)
    errors = []
    try:
        m = load_manifest(path)
    except Exception as exc:
        print(f"INVALID manifest parse: {exc}")
        sys.exit(1)

    require(str(m.get("schema_version")) == str(CANON.get("schema_version", "2.24")), "schema_version must match canonical schema", errors)
    require(str(m.get("protocol_version")) == str(CANON.get("protocol_version", "2.24")), "protocol_version must match canonical schema", errors)
    require(m.get("protocol") == "HILP", "protocol must be HILP", errors)
    mode = m.get("mode")
    require(mode in VALID_MODES, f"mode must be {'|'.join(sorted(VALID_MODES))}", errors)
    require(bool(m.get("change_slug")), "change_slug required", errors)
    ca = m.get("current_assets")
    cp = m.get("current_pointers")
    registry = m.get("asset_registry")
    require(isinstance(ca, dict), "current_assets must be mapping", errors)
    require(isinstance(cp, dict), "current_pointers must be mapping", errors)
    require(isinstance(registry, list), "asset_registry must be list", errors)
    if isinstance(ca, dict):
        for key in REQUIRED_CURRENT_ASSETS:
            require(key in ca, f"current_assets.{key} required", errors)
        if mode == "strict":
            require(bool(ca.get("audit_trail")), "strict mode requires current_assets.audit_trail", errors)
        for key, value in ca.items():
            validate_path_value(f"current_assets.{key}", value, errors)
    if isinstance(cp, dict):
        for key in REQUIRED_POINTERS:
            require(key in cp, f"current_pointers.{key} required", errors)
        require(bool(cp.get("agent_directory")), "current_pointers.agent_directory must be non-null", errors)
        for key, value in cp.items():
            validate_path_value(f"current_pointers.{key}", value, errors)

    refs_by_path, refs_by_ref = {}, {}
    paths, refs = set(), set()
    registry_path_values = []
    phase04_seen = False
    invalidation_seen = False
    if isinstance(registry, list):
        for i, item in enumerate(registry):
            prefix = f"asset_registry[{i}]"
            require(isinstance(item, dict), f"{prefix} must be mapping", errors)
            if not isinstance(item, dict):
                continue
            for key in REGISTRY_REQUIRED:
                require(key in item, f"{prefix}.{key} required", errors)
            for key in ["path", "human_view", "agent_view"]:
                validate_path_value(f"{prefix}.{key}", item.get(key), errors)
                require(bool(item.get(key)), f"{prefix}.{key} required for dual-view contract", errors)
            ref = item.get("asset_ref")
            parsed = parse_ref(ref)
            if ref:
                require(ref not in refs, f"duplicate asset_ref: {ref}", errors)
                refs.add(ref)
                refs_by_ref[ref] = item
                require(parsed is not None, f"{prefix}.asset_ref must match phase-nn/artifact@vN: {ref}", errors)
                if parsed:
                    require(item.get("phase_id") == parsed["phase"], f"{prefix}.phase_id must match asset_ref phase", errors)
                    require(item.get("version") == parsed["version"], f"{prefix}.version must match asset_ref @vN", errors)
                    if parsed["phase"] == "phase-04" or parsed["artifact"] == "reapproval":
                        phase04_seen = True
                        require(parsed["artifact"] == "reapproval", f"{prefix}: phase-04 asset must be reapproval", errors)
                        require(item.get("record_role") == "reapproval-record", f"{prefix}: phase-04/reapproval must use record_role=reapproval-record", errors)
            p = item.get("path")
            if p:
                paths.add(p)
                registry_path_values.append((f"{prefix}.path", p))
                refs_by_path[p] = item
            for view_key in ["human_view", "agent_view"]:
                view_path = item.get(view_key)
                if view_path:
                    registry_path_values.append((f"{prefix}.{view_key}", view_path))
            if item.get("human_view") and item.get("agent_view") and item.get("human_view") == item.get("agent_view"):
                errors.append(f"{prefix}: human_view and agent_view must be distinct files")
            state = item.get("lifecycle_state")
            role = item.get("record_role")
            require(state in VALID_STATES, f"{prefix}.lifecycle_state invalid: {state}", errors)
            require(role in VALID_ROLES, f"{prefix}.record_role invalid: {role}", errors)
            if role in ROLE_STATE:
                require(state in ROLE_STATE[role], f"{prefix}: role {role} incompatible with state {state}", errors)
            if parsed:
                type_key = (parsed["phase"], parsed["artifact"])
                allowed_roles = ARTIFACT_ALLOWED_ROLES.get(type_key)
                if allowed_roles:
                    require(role in allowed_roles, f"{prefix}: {parsed['phase']}/{parsed['artifact']} cannot use record_role={role}", errors)
                required_role = ARTIFACT_ROLE_STATE_RULES.get((parsed["phase"], parsed["artifact"], state))
                if required_role:
                    require(role == required_role, f"{prefix}: {parsed['phase']}/{parsed['artifact']} with lifecycle_state={state} must use record_role={required_role}", errors)
                expected_owner = ARTIFACT_OWNER_PROTOCOL.get(type_key)
                if expected_owner:
                    exp_skill, exp_protocol = expected_owner
                    require(item.get("owner_skill") == exp_skill, f"{prefix}: {parsed['phase']}/{parsed['artifact']} must use owner_skill={exp_skill}", errors)
                    require(item.get("owner_protocol") == exp_protocol, f"{prefix}: {parsed['phase']}/{parsed['artifact']} must use owner_protocol={exp_protocol}", errors)
            require(item.get("owner_skill") in VALID_OWNER_SKILLS, f"{prefix}.owner_skill invalid or missing", errors)
            require(item.get("owner_protocol") in VALID_OWNER_PROTOCOLS, f"{prefix}.owner_protocol invalid or missing", errors)
            require(isinstance(item.get("version"), int) and item.get("version") >= 1, f"{prefix}.version must be integer >= 1", errors)
            if state == "superseded":
                require(bool(item.get("superseded_by")), f"{prefix}.superseded_by required when lifecycle_state=superseded", errors)
            if state == "retired":
                require(bool(item.get("invalidated_by")), f"{prefix}.invalidated_by required when lifecycle_state=retired", errors)
            if item.get("invalidated_by"):
                invalidation_seen = True
                inv = parse_ref(item.get("invalidated_by"))
                require(inv is not None and inv["phase"] == "phase-04" and inv["artifact"] == "reapproval", f"{prefix}.invalidated_by must be a phase-04/reapproval@vN ref", errors)

    if isinstance(ca, dict):
        for key, expected in EXPECTED_ASSET_TYPES.items():
            value = ca.get(key)
            if value is None:
                continue
            item = resolve_pointer(value, refs_by_ref, refs_by_path)
            require(item is not None, f"current_assets.{key} must point to an asset_registry ref or path: {value}", errors)
            if item:
                actual_phase, actual_artifact = item_type(item)
                require((actual_phase, actual_artifact) == expected, f"current_assets.{key} must point to {expected[0]}/{expected[1]}, got {item.get('asset_ref')}", errors)
        if phase04_seen or invalidation_seen:
            require(bool(ca.get("reapproval_log")), "phase-04 or invalidated assets require current_assets.reapproval_log", errors)
            if ca.get("reapproval_log"):
                item = resolve_pointer(ca.get("reapproval_log"), refs_by_ref, refs_by_path)
                require(item is not None and item.get("record_role") == "reapproval-record", "current_assets.reapproval_log must point to a reapproval-record", errors)
    if isinstance(cp, dict):
        for key, expected in EXPECTED_POINTER_TYPES.items():
            value = cp.get(key)
            if value is None:
                continue
            item = resolve_pointer(value, refs_by_ref, refs_by_path)
            require(item is not None, f"current_pointers.{key} must point to an asset_registry ref or path: {value}", errors)
            if item:
                phase, artifact, state, role = expected
                actual_phase, actual_artifact = item_type(item)
                require((actual_phase, actual_artifact) == (phase, artifact), f"current_pointers.{key} must point to {phase}/{artifact}, got {item.get('asset_ref')}", errors)
                require(item.get("lifecycle_state") == state, f"current_pointers.{key} must point to lifecycle_state={state}", errors)
                require(item.get("record_role") == role, f"current_pointers.{key} must point to record_role={role}", errors)

    if args.check_paths:
        base = path.parent
        for collection in [ca or {}, cp or {}]:
            if isinstance(collection, dict):
                for key, rel in collection.items():
                    if rel and isinstance(rel, str) and not URL_RE.match(rel) and rel not in refs_by_ref:
                        if not (base / rel).exists() and not (args.allow_draft_paths and mode == "preflight-scaffold"):
                            errors.append(f"path does not exist for {key}: {rel}")
        for label, rel in registry_path_values:
            if rel and isinstance(rel, str) and not URL_RE.match(rel) and not (base / rel).exists() and not (args.allow_draft_paths and mode == "preflight-scaffold"):
                errors.append(f"path does not exist for {label}: {rel}")
    if mode == "preflight-scaffold":
        if isinstance(registry, list):
            for item in registry:
                if isinstance(item, dict) and item.get("record_role") in {"approval-record", "handoff-record"}:
                    errors.append(f"preflight scaffold must not contain formal approval/handoff record: {item.get('asset_ref')}")
        for key, value in (m.get("current_pointers") or {}).items():
            if isinstance(value, str) and value.startswith("_current/"):
                errors.append(f"preflight scaffold must not define formal _current pointers: {key}")

    if errors:
        print("MANIFEST_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print("manifest ok")
    sys.exit(0)

if __name__ == "__main__":
    main()
