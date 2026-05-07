#!/usr/bin/env python3
"""Validate HILE handoff intake with HILP planning manifest proof."""
import argparse
import re
import sys
from pathlib import Path, PurePosixPath

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

ACCEPTED_OWNER_SKILL_VALUES = {"human-in-loop-execution"}
ROOT = Path(__file__).resolve().parents[1]
COMPAT_PATH = ROOT / "references/shared/compatibility-contract.yaml"

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
HILP_ASSET_REF_RE = re.compile(r"^(phase-\d{2})/([A-Za-z0-9_-]+)@v(\d+)$")
HILP_REQUIRED_CURRENT_ASSETS = ["requirements_facts", "design_choice", "implementation_blueprint", "execution_handoff", "reapproval_log", "archive_index", "audit_trail"]
HILP_REQUIRED_POINTERS = ["human_review", "agent_directory", "latest_approved_design", "latest_approved_blueprint", "latest_handoff"]
HILP_REGISTRY_REQUIRED = ["asset_ref", "path", "human_view", "agent_view", "phase_id", "lifecycle_state", "record_role", "version", "owner_skill", "owner_protocol", "created_at", "last_state_change_at"]
HILP_OWNER_MATRIX = {
    ("phase-01", "requirements-facts"): ("human-in-loop-planning", "HILP"),
    ("phase-02", "design-choice"): ("human-in-loop-planning", "HILP"),
    ("phase-03", "implementation-blueprint"): ("human-in-loop-planning", "HILP"),
    ("phase-04", "reapproval"): ("human-in-loop-planning", "HILP"),
    ("phase-05", "execution-handoff"): ("human-in-loop-execution", "HILE"),
    ("phase-06", "archive-index"): ("human-in-loop-planning", "HILP"),
}
HILP_EXPECTED_POINTERS = {
    "latest_approved_design": ("phase-02", "design-choice", "approved", "approval-record"),
    "latest_approved_blueprint": ("phase-03", "implementation-blueprint", "approved", "approval-record"),
    "latest_handoff": ("phase-05", "execution-handoff", "closed-record", "handoff-record"),
}
HILP_EXPECTED_CURRENT_ASSETS = {
    "design_choice": ("phase-02", "design-choice"),
    "implementation_blueprint": ("phase-03", "implementation-blueprint"),
    "execution_handoff": ("phase-05", "execution-handoff"),
}


def yaml_blocks(path: Path):
    text = path.read_text(encoding="utf-8")
    blocks = []
    for block in FENCE_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict):
            blocks.append(data)
    if not blocks:
        raise ValueError(f"{path} must contain a yaml mapping block")
    return blocks


def load_compatibility():
    try:
        data = yaml.safe_load(COMPAT_PATH.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        data = {}
    versions = {str(v) for v in data.get("compatible_schema_versions", [])}
    if not versions:
        versions = {str(data.get("schema_version", "2.24"))}
    return {
        "schema_versions": versions,
        "hilp_version": str(data.get("hilp_version", "2.24")),
        "hile_version": str(data.get("hile_version", "2.24")),
    }


def version_fields_ok(obj, label, compat, errors, protocol_version=None):
    schema_version = obj.get("schema_version")
    proto_version = obj.get("protocol_version")
    if str(schema_version) not in compat["schema_versions"]:
        errors.append(f"{label}.schema_version must be one of {sorted(compat['schema_versions'])}")
    expected = protocol_version or compat["hilp_version"]
    if str(proto_version) != str(expected):
        errors.append(f"{label}.protocol_version must be {expected}")


def load_handoff(path: Path):
    for data in yaml_blocks(path):
        if "execution_handoff" in data and isinstance(data["execution_handoff"], dict):
            h = dict(data["execution_handoff"])
            for k in ["schema_version", "protocol_version", "asset_ref", "phase_id", "lifecycle_state", "record_role", "owner_skill", "owner_protocol"]:
                if k in data and k not in h:
                    h[k] = data[k]
            if isinstance(data.get("state"), dict):
                for k, v in data["state"].items():
                    h.setdefault(k, v)
            if "hile_entry_check" in data:
                h["hile_entry_check"] = data["hile_entry_check"]
            return h
        if any(k in data for k in ["owner_skill", "source_design_ref", "source_blueprint_ref"]):
            return data
    raise ValueError("no execution_handoff mapping found")


def load_manifest(path: Path):
    for data in yaml_blocks(path):
        if isinstance(data.get("manifest"), dict):
            return data["manifest"]
    raise ValueError("planning manifest must contain top-level manifest mapping")


def nonempty(value):
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return True


def parse_hilp_ref(ref):
    if not isinstance(ref, str):
        return None
    m = HILP_ASSET_REF_RE.match(ref)
    if not m:
        return None
    phase, artifact, version = m.groups()
    return {"phase": phase, "artifact": artifact, "version": int(version)}


def registry_by_ref(manifest):
    reg = manifest.get("asset_registry") or []
    out = {}
    if isinstance(reg, list):
        for item in reg:
            if isinstance(item, dict) and item.get("asset_ref"):
                out[item["asset_ref"]] = item
    return out


def registry_by_path(manifest):
    reg = manifest.get("asset_registry") or []
    out = {}
    if isinstance(reg, list):
        for item in reg:
            if isinstance(item, dict) and item.get("path"):
                out[item["path"]] = item
    return out


def resolve_manifest_value(value, by_ref, by_path):
    if value is None:
        return None
    return by_ref.get(value) or by_path.get(value)


def validate_hilp_manifest_contract(manifest, compat, errors):
    """Minimal embedded HILP manifest validator for HILE provenance checks.

    HILE cannot safely claim full intake pass unless the upstream planning
    manifest is not merely HILP-looking, but contains the canonical fields and
    role/owner/pointer semantics required for an approved design, approved
    blueprint, and closed execution handoff.
    """
    if manifest.get("protocol") != "HILP":
        errors.append("planning manifest protocol must be HILP")
    version_fields_ok(manifest, "planning manifest", compat, errors, protocol_version=compat["hilp_version"])
    if manifest.get("mode") not in {"standard", "strict"}:
        errors.append("planning manifest mode must be standard or strict for HILE intake")
    if not nonempty(manifest.get("change_slug")):
        errors.append("planning manifest change_slug required")
    ca = manifest.get("current_assets")
    cp = manifest.get("current_pointers")
    reg = manifest.get("asset_registry")
    if not isinstance(ca, dict):
        errors.append("planning manifest current_assets must be a mapping")
        ca = {}
    if not isinstance(cp, dict):
        errors.append("planning manifest current_pointers must be a mapping")
        cp = {}
    if not isinstance(reg, list):
        errors.append("planning manifest asset_registry must be a list")
        reg = []
    for key in HILP_REQUIRED_CURRENT_ASSETS:
        if key not in ca:
            errors.append(f"planning manifest current_assets.{key} required")
    for key in HILP_REQUIRED_POINTERS:
        if key not in cp:
            errors.append(f"planning manifest current_pointers.{key} required")
    by_ref = {}
    by_path = {}
    seen = set()
    for idx, item in enumerate(reg):
        prefix = f"planning manifest asset_registry[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        for key in HILP_REGISTRY_REQUIRED:
            if key not in item:
                errors.append(f"{prefix}.{key} required")
        ref = item.get("asset_ref")
        parsed = parse_hilp_ref(ref)
        if not parsed:
            errors.append(f"{prefix}.asset_ref must match phase-nn/artifact@vN: {ref}")
            continue
        if ref in seen:
            errors.append(f"planning manifest duplicate asset_ref: {ref}")
        seen.add(ref)
        by_ref[ref] = item
        if item.get("path"):
            by_path[item["path"]] = item
        if item.get("phase_id") != parsed["phase"]:
            errors.append(f"{prefix}.phase_id must match asset_ref phase")
        if item.get("version") != parsed["version"]:
            errors.append(f"{prefix}.version must match asset_ref @vN")
        expected_owner = HILP_OWNER_MATRIX.get((parsed["phase"], parsed["artifact"]))
        if expected_owner:
            exp_skill, exp_protocol = expected_owner
            if item.get("owner_skill") != exp_skill:
                errors.append(f"{prefix} {ref} must use owner_skill={exp_skill}")
            if item.get("owner_protocol") != exp_protocol:
                errors.append(f"{prefix} {ref} must use owner_protocol={exp_protocol}")
        if parsed["phase"] == "phase-02" and parsed["artifact"] == "design-choice" and item.get("lifecycle_state") == "approved" and item.get("record_role") != "approval-record":
            errors.append(f"{prefix} approved design-choice must use record_role=approval-record")
        if parsed["phase"] == "phase-03" and parsed["artifact"] == "implementation-blueprint" and item.get("lifecycle_state") == "approved" and item.get("record_role") != "approval-record":
            errors.append(f"{prefix} approved implementation-blueprint must use record_role=approval-record")
        if parsed["phase"] == "phase-05" and parsed["artifact"] == "execution-handoff":
            if item.get("lifecycle_state") != "closed-record":
                errors.append(f"{prefix} execution-handoff must use lifecycle_state=closed-record")
            if item.get("record_role") != "handoff-record":
                errors.append(f"{prefix} execution-handoff must use record_role=handoff-record")
    for key, (phase, artifact) in HILP_EXPECTED_CURRENT_ASSETS.items():
        value = ca.get(key)
        if value is None:
            continue
        item = resolve_manifest_value(value, by_ref, by_path)
        if not item:
            errors.append(f"planning manifest current_assets.{key} must point to registry ref or path")
            continue
        parsed = parse_hilp_ref(item.get("asset_ref"))
        if not parsed or (parsed["phase"], parsed["artifact"]) != (phase, artifact):
            errors.append(f"planning manifest current_assets.{key} must point to {phase}/{artifact}")
    for key, (phase, artifact, state, role) in HILP_EXPECTED_POINTERS.items():
        value = cp.get(key)
        if value is None:
            continue
        item = resolve_manifest_value(value, by_ref, by_path)
        if not item:
            errors.append(f"planning manifest current_pointers.{key} must point to registry ref or path")
            continue
        parsed = parse_hilp_ref(item.get("asset_ref"))
        if not parsed or (parsed["phase"], parsed["artifact"]) != (phase, artifact):
            errors.append(f"planning manifest current_pointers.{key} must point to {phase}/{artifact}")
        if item.get("lifecycle_state") != state:
            errors.append(f"planning manifest current_pointers.{key} must point to lifecycle_state={state}")
        if item.get("record_role") != role:
            errors.append(f"planning manifest current_pointers.{key} must point to record_role={role}")


def has_glob(value):
    return isinstance(value, str) and any(ch in value for ch in "*?[")


def validate_scope_pattern(value, label, errors):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        errors.append(f"{label} invalid empty or padded path: {value}")
        return
    if "\\" in value:
        errors.append(f"{label} must use POSIX relative path, not backslash path: {value}")
        return
    p = PurePosixPath(value)
    if p.is_absolute():
        errors.append(f"{label} absolute paths are not allowed: {value}")
    if ".." in p.parts:
        errors.append(f"{label} parent traversal is not allowed: {value}")
    if value in {".", ""}:
        errors.append(f"{label} must name a file or file glob, not workspace root")
    for part in p.parts:
        if "**" in part and part != "**":
            errors.append(f"{label} invalid recursive glob segment; use ** as a complete path segment: {value}")


def validate_file_scope_contract(h, errors):
    for field in ["allowed_files", "prohibited_files"]:
        value = h.get(field)
        if field == "prohibited_files" and value is None:
            continue
        if not isinstance(value, list):
            errors.append(f"{field} must be a list")
            continue
        for idx, pattern in enumerate(value):
            validate_scope_pattern(pattern, f"{field}[{idx}]", errors)
    units = h.get("execution_units") or []
    if isinstance(units, list):
        for ui, unit in enumerate(units):
            if not isinstance(unit, dict):
                continue
            for field in ["allowed_files", "prohibited_files"]:
                value = unit.get(field)
                if field == "prohibited_files" and value is None:
                    continue
                if not isinstance(value, list):
                    errors.append(f"execution_units[{ui}].{field} must be a list")
                    continue
                for pi, pattern in enumerate(value):
                    validate_scope_pattern(pattern, f"execution_units[{ui}].{field}[{pi}]", errors)


def unit_allowed_within_top(unit_pattern, top_patterns):
    if not isinstance(unit_pattern, str) or not unit_pattern:
        return False
    if unit_pattern in top_patterns or "**" in top_patterns or "*" in top_patterns:
        return True
    if not has_glob(unit_pattern):
        for top in top_patterns:
            if not isinstance(top, str):
                continue
            if top.endswith("/**") and unit_pattern.startswith(top[:-3].rstrip("/") + "/"):
                return True
            if top.endswith("/*") and unit_pattern.startswith(top[:-2].rstrip("/") + "/"):
                suffix = unit_pattern[len(top[:-2].rstrip("/"))+1:]
                if "/" not in suffix:
                    return True
    for top in top_patterns:
        if isinstance(top, str) and top.endswith("/**") and unit_pattern.startswith(top[:-3].rstrip("/") + "/"):
            return True
    return False


def validate_execution_units(h, errors):
    units = h.get("execution_units")
    top_allowed = h.get("allowed_files") if isinstance(h.get("allowed_files"), list) else []
    if not isinstance(units, list) or not units:
        errors.append("execution_units required and non-empty")
        return
    seen = set()
    for idx, unit in enumerate(units):
        prefix = f"execution_units[{idx}]"
        if not isinstance(unit, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        unit_id = unit.get("unit_id")
        if not isinstance(unit_id, str) or not unit_id.strip():
            errors.append(f"{prefix}.unit_id required")
        elif unit_id in seen:
            errors.append(f"{prefix}.unit_id duplicate: {unit_id}")
        else:
            seen.add(unit_id)
        if not nonempty(unit.get("objective")):
            errors.append(f"{prefix}.objective required and non-empty")
        allowed = unit.get("allowed_files")
        if not isinstance(allowed, list) or not allowed:
            errors.append(f"{prefix}.allowed_files required and non-empty")
        else:
            for pattern in allowed:
                if not isinstance(pattern, str) or not pattern.strip():
                    errors.append(f"{prefix}.allowed_files contains invalid entry")
                elif not unit_allowed_within_top(pattern, top_allowed):
                    errors.append(f"{prefix}.allowed_files entry outside top-level allowed_files: {pattern}")
        if "prohibited_files" not in unit:
            errors.append(f"{prefix}.prohibited_files key required; use [] when empty")
        elif unit.get("prohibited_files") is not None and not isinstance(unit.get("prohibited_files"), list):
            errors.append(f"{prefix}.prohibited_files must be a list")
        if not nonempty(unit.get("verification")) and not nonempty(unit.get("verification_contract")) and not unit.get("inherits_verification_contract"):
            errors.append(f"{prefix}.verification or inherits_verification_contract required")
        if not nonempty(unit.get("stop_conditions")) and not unit.get("inherits_stop_conditions"):
            errors.append(f"{prefix}.stop_conditions or inherits_stop_conditions required")


def validate_hile_planning_requirement(h, errors):
    hpr = h.get("hile_planning_requirement")
    if not isinstance(hpr, dict):
        errors.append("hile_planning_requirement mapping required")
        return
    if hpr.get("required") is not True:
        errors.append("hile_planning_requirement.required must be true")
    rule = hpr.get("rule")
    required_phrase = "repo-aware Plan or Runbook before modifying files"
    if not isinstance(rule, str) or required_phrase not in rule:
        errors.append("hile_planning_requirement.rule must require a repo-aware Plan or Runbook before modifying files")


def check_approved(ref, label, reg, errors):
    item = reg.get(ref)
    if not item:
        errors.append(f"{label} {ref} not found in planning manifest asset_registry")
        return
    if item.get("lifecycle_state") != "approved":
        errors.append(f"{label} {ref} must have lifecycle_state=approved in planning manifest")
    if item.get("record_role") != "approval-record":
        errors.append(f"{label} {ref} must have record_role=approval-record in planning manifest")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handoff")
    ap.add_argument("--workspace", help="Current execution repo/worktree root. Required unless handoff declares execution_workspace.")
    ap.add_argument("--planning-manifest", help="HILP planning manifest proving source design and blueprint approval.")
    ap.add_argument("--allow-partial", action="store_true", help="Allow partial intake when planning manifest is unavailable. Never use this to claim full intake pass.")
    args = ap.parse_args()

    errors = []
    warnings = []
    try:
        h = load_handoff(Path(args.handoff))
    except Exception as exc:
        print(f"INVALID handoff parse: {exc}")
        sys.exit(1)

    if h.get("owner_skill") not in ACCEPTED_OWNER_SKILL_VALUES:
        errors.append("owner_skill must be human-in-loop-execution")
    if h.get("owner_protocol") != "HILE":
        errors.append("owner_protocol must be HILE")

    compat = load_compatibility()
    version_fields_ok(h, "handoff", compat, errors, protocol_version=compat["hilp_version"])

    for field in ["source_design_ref", "source_blueprint_ref", "execution_scope", "allowed_files", "prohibited_scope", "stop_conditions", "verification_contract"]:
        if not nonempty(h.get(field)):
            errors.append(f"{field} required and non-empty")
    if "prohibited_files" not in h:
        errors.append("prohibited_files key required; use [] when there is no explicit denylist beyond allowed_files")
    elif h.get("prohibited_files") is not None and not isinstance(h.get("prohibited_files"), list):
        errors.append("prohibited_files must be a list; use [] when empty")
    validate_file_scope_contract(h, errors)
    validate_execution_units(h, errors)
    validate_hile_planning_requirement(h, errors)

    state = h.get("lifecycle_state") or h.get("state")
    role = h.get("record_role") or h.get("role")
    if state != "closed-record":
        errors.append("handoff lifecycle_state must be closed-record")
    if role != "handoff-record":
        errors.append("handoff record_role must be handoff-record")
    if "hile_entry_check" in h:
        errors.append("planning handoff must not contain HILE-owned hile_entry_check result")

    workspace = args.workspace or h.get("execution_workspace") or h.get("worktree") or h.get("project_root")
    if not workspace:
        errors.append("execution workspace/root must be provided by --workspace or handoff field")
    elif not Path(str(workspace)).exists():
        errors.append(f"workspace path does not exist: {workspace}")

    if args.planning_manifest:
        try:
            manifest = load_manifest(Path(args.planning_manifest))
            validate_hilp_manifest_contract(manifest, compat, errors)
            reg = registry_by_ref(manifest)
            check_approved(h.get("source_design_ref"), "source_design_ref", reg, errors)
            check_approved(h.get("source_blueprint_ref"), "source_blueprint_ref", reg, errors)
            handoff_ref = h.get("asset_ref")
            if not handoff_ref:
                errors.append("handoff asset_ref required when planning manifest is provided")
                handoff_item = None
            else:
                handoff_item = reg.get(handoff_ref)
                if not handoff_item:
                    errors.append(f"handoff asset_ref {handoff_ref} not found in planning manifest asset_registry")
            if handoff_item:
                item_state = handoff_item.get("lifecycle_state") or handoff_item.get("state")
                item_role = handoff_item.get("record_role") or handoff_item.get("role")
                if item_state != "closed-record":
                    errors.append("handoff asset_ref in planning manifest must have lifecycle_state=closed-record")
                if item_role != "handoff-record":
                    errors.append("handoff asset_ref in planning manifest must have record_role=handoff-record")
                item_path = handoff_item.get("path")
                current_assets = manifest.get("current_assets") or {}
                current_pointers = manifest.get("current_pointers") or {}
                if isinstance(current_assets, dict):
                    ca_value = current_assets.get("execution_handoff")
                    if ca_value not in {handoff_ref, item_path}:
                        errors.append("planning manifest current_assets.execution_handoff must point to the handoff asset_ref or path")
                else:
                    errors.append("planning manifest current_assets must be a mapping")
                if isinstance(current_pointers, dict):
                    cp_value = current_pointers.get("latest_handoff")
                    if cp_value not in {handoff_ref, item_path}:
                        errors.append("planning manifest current_pointers.latest_handoff must point to the handoff asset_ref or path")
                else:
                    errors.append("planning manifest current_pointers must be a mapping")
        except Exception as exc:
            errors.append(f"planning manifest validation failed: {exc}")
    else:
        msg = "planning manifest not provided; approved design and blueprint cannot be mechanically verified"
        if args.allow_partial:
            warnings.append(msg)
        else:
            errors.append(msg)

    if errors:
        print("HANDOFF_INTAKE_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    if warnings:
        print("HANDOFF_INTAKE_WARNINGS")
        print("\n".join(warnings))
        if args.allow_partial and not args.planning_manifest:
            print("HANDOFF_INTAKE_PARTIAL")
            print("partial intake only; execution is not authorized until planning manifest provenance is mechanically verified")
            return
    print("handoff intake ok")

if __name__ == "__main__":
    main()
