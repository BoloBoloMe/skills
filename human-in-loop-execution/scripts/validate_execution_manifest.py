#!/usr/bin/env python3
"""Validate a canonical HILE execution manifest.

Hardening added after v2.24.1 audit:
- load enums and required fields from references/shared/canonical-protocol-schema.yaml
- require dual-view and owner fields on asset_registry entries
- preserve package_stage / asset-state coherence checks
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
COMPAT_PATH = ROOT / "references/shared/compatibility-contract.yaml"
FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
ASSET_REF_RE = re.compile(r"^hile/([A-Za-z0-9_-]+)@v(\d+)$")
HILP_HANDOFF_REF_RE = re.compile(r"^phase-05/execution-handoff@v\d+$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

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



def load_canonical():
    if CANON_PATH.exists():
        return yaml.safe_load(CANON_PATH.read_text(encoding="utf-8")) or {}
    return {}

def load_compat():
    if COMPAT_PATH.exists():
        return yaml.safe_load(COMPAT_PATH.read_text(encoding="utf-8")) or {}
    return {}

def major_minor(version):
    parts = str(version or "").split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else str(version or "")

CANON = load_canonical()
COMPAT = load_compat()
VALID_STAGES = set(CANON.get("package_stage_values", [])) or {"initialized", "intake-pending", "intake-passed", "planned", "confirmed", "in-progress", "blocked", "failed", "completed"}
VALID_INTAKE = set(CANON.get("intake_status_values", [])) or {"draft", "partial", "pass", "blocked"}
VALID_TIERS = set(CANON.get("execution_tier_values", [])) or {"tiny", "standard", "strict"}
VALID_STATES = set(CANON.get("lifecycle_state_values", [])) or {"draft", "ready-for-confirmation", "confirmed", "in-progress", "blocked", "completed", "failed", "superseded", "closed-record"}
VALID_ROLES = set(CANON.get("record_role_values", [])) or {"intake-record", "runbook", "plan", "inline-execution-record", "ledger", "unit-summary", "verification-evidence", "failure-forensics", "completion-record"}
ROLE_STATE = {k: set(v or []) for k, v in (CANON.get("role_state_matrix") or {}).items()}
VALID_OWNER_SKILLS = set(CANON.get("owner_skill_values", [])) or {"human-in-loop-execution"}
VALID_OWNER_PROTOCOLS = set(CANON.get("owner_protocol_values", [])) or {"HILE"}
REQUIRED_CURRENT_ASSETS = CANON.get("current_assets_required_fields") or ["intake_summary", "current_runbook", "current_plan", "tiny_inline_record", "ledger", "unit_summaries", "verification_evidence", "failure_forensics", "completion_review"]
REQUIRED_POINTERS = CANON.get("current_pointers_required_fields") or ["human_status", "agent_directory", "active_runbook_or_plan", "latest_runbook_or_plan", "latest_verification", "latest_completion_review"]
REGISTRY_REQUIRED = CANON.get("asset_registry_required_fields") or ["asset_ref", "path", "human_view", "agent_view", "lifecycle_state", "record_role", "version", "owner_skill", "owner_protocol", "created_at", "last_state_change_at"]

CURRENT_ASSET_SLOT_ROLES = {
    "intake_summary": {"intake-record"},
    "current_runbook": {"runbook"},
    "current_plan": {"plan"},
    "tiny_inline_record": {"inline-execution-record"},
    "ledger": {"ledger"},
    "unit_summaries": {"unit-summary"},
    "verification_evidence": {"verification-evidence"},
    "failure_forensics": {"failure-forensics"},
    "completion_review": {"completion-record"},
}
CURRENT_ASSET_STAGE_STATES = {
    "current_runbook": {
        "planned": {"draft", "ready-for-confirmation"},
        "confirmed": {"confirmed"},
        "in-progress": {"in-progress", "blocked"},
        "blocked": {"blocked"},
        "failed": {"failed", "blocked"},
        "completed": {"completed", "closed-record"},
    },
    "current_plan": {
        "planned": {"draft", "ready-for-confirmation"},
        "confirmed": {"confirmed"},
        "in-progress": {"in-progress", "blocked"},
        "blocked": {"blocked"},
        "failed": {"failed", "blocked"},
        "completed": {"completed", "closed-record"},
    },
}


def load_manifest(path: Path):
    text = path.read_text(encoding="utf-8")
    for block in FENCE_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and isinstance(data.get("manifest"), dict):
            return data["manifest"]
    raise ValueError("manifest must contain top-level manifest mapping in a yaml fenced block")


def require(cond, msg, errors):
    if not cond:
        errors.append(msg)


def maps(registry):
    by_ref, by_path = {}, {}
    for item in registry:
        if not isinstance(item, dict):
            continue
        if item.get("asset_ref"):
            by_ref[item["asset_ref"]] = item
        if item.get("path"):
            by_path[item["path"]] = item
    return by_ref, by_path


def find_planning_handoff(planning_manifest, handoff_ref):
    for item in planning_manifest.get("asset_registry") or []:
        if isinstance(item, dict) and item.get("asset_ref") == handoff_ref:
            return item
    return None


def parse_hilp_ref(ref):
    if not isinstance(ref, str):
        return None
    m = HILP_ASSET_REF_RE.match(ref)
    if not m:
        return None
    phase, artifact, version = m.groups()
    return {"phase": phase, "artifact": artifact, "version": int(version)}


def validate_hilp_manifest_contract(planning_manifest, errors):
    """Validate enough of the HILP manifest contract for provenance checks.

    This intentionally rejects HILP-looking partial manifests so HILE cannot
    claim a valid source handoff from incomplete planning provenance.
    """
    require(planning_manifest.get("protocol") == "HILP", "planning manifest protocol must be HILP", errors)
    compatible_versions = {str(v) for v in (COMPAT.get("compatible_schema_versions") or [])}
    expected_hilp = str(COMPAT.get("hilp_version", "2.24.0"))
    if not compatible_versions:
        compatible_versions = {expected_hilp}
    schema_version = str(planning_manifest.get("schema_version"))
    protocol_version = str(planning_manifest.get("protocol_version"))
    require(schema_version in compatible_versions, f"planning manifest schema_version must be one of compatible HILP versions {sorted(compatible_versions)}", errors)
    require(protocol_version in compatible_versions, f"planning manifest protocol_version must be one of compatible HILP versions {sorted(compatible_versions)}", errors)
    require(major_minor(schema_version) == major_minor(CANON.get("schema_version", "2.24.1")), "planning manifest schema_version must share HILP/HILE major.minor line", errors)
    require(planning_manifest.get("mode") in {"standard", "strict"}, "planning manifest mode must be standard or strict for execution provenance", errors)
    require(bool(planning_manifest.get("change_slug")), "planning manifest change_slug required", errors)
    ca = planning_manifest.get("current_assets")
    cp = planning_manifest.get("current_pointers")
    reg = planning_manifest.get("asset_registry")
    require(isinstance(ca, dict), "planning manifest current_assets must be mapping", errors)
    require(isinstance(cp, dict), "planning manifest current_pointers must be mapping", errors)
    require(isinstance(reg, list), "planning manifest asset_registry must be list", errors)
    ca = ca if isinstance(ca, dict) else {}
    cp = cp if isinstance(cp, dict) else {}
    reg = reg if isinstance(reg, list) else []
    for key in HILP_REQUIRED_CURRENT_ASSETS:
        require(key in ca, f"planning manifest current_assets.{key} required", errors)
    for key in HILP_REQUIRED_POINTERS:
        require(key in cp, f"planning manifest current_pointers.{key} required", errors)
    by_ref = {}
    by_path = {}
    seen = set()
    for idx, item in enumerate(reg):
        prefix = f"planning manifest asset_registry[{idx}]"
        require(isinstance(item, dict), f"{prefix} must be mapping", errors)
        if not isinstance(item, dict):
            continue
        for key in HILP_REGISTRY_REQUIRED:
            require(key in item, f"{prefix}.{key} required", errors)
        ref = item.get("asset_ref")
        parsed = parse_hilp_ref(ref)
        require(parsed is not None, f"{prefix}.asset_ref must match phase-nn/artifact@vN: {ref}", errors)
        if not parsed:
            continue
        require(ref not in seen, f"planning manifest duplicate asset_ref: {ref}", errors)
        seen.add(ref)
        by_ref[ref] = item
        if item.get("path"):
            by_path[item["path"]] = item
        require(item.get("phase_id") == parsed["phase"], f"{prefix}.phase_id must match asset_ref phase", errors)
        require(item.get("version") == parsed["version"], f"{prefix}.version must match asset_ref @vN", errors)
        expected_owner = HILP_OWNER_MATRIX.get((parsed["phase"], parsed["artifact"]))
        if expected_owner:
            skill, proto = expected_owner
            require(item.get("owner_skill") == skill, f"{prefix} {ref} must use owner_skill={skill}", errors)
            require(item.get("owner_protocol") == proto, f"{prefix} {ref} must use owner_protocol={proto}", errors)
        if (parsed["phase"], parsed["artifact"]) == ("phase-02", "design-choice") and item.get("lifecycle_state") == "approved":
            require(item.get("record_role") == "approval-record", f"{prefix} approved design-choice must use record_role=approval-record", errors)
        if (parsed["phase"], parsed["artifact"]) == ("phase-03", "implementation-blueprint") and item.get("lifecycle_state") == "approved":
            require(item.get("record_role") == "approval-record", f"{prefix} approved implementation-blueprint must use record_role=approval-record", errors)
        if (parsed["phase"], parsed["artifact"]) == ("phase-05", "execution-handoff"):
            require(item.get("lifecycle_state") == "closed-record", f"{prefix} execution-handoff must use lifecycle_state=closed-record", errors)
            require(item.get("record_role") == "handoff-record", f"{prefix} execution-handoff must use record_role=handoff-record", errors)
    for key, (phase, artifact, state, role) in HILP_EXPECTED_POINTERS.items():
        value = cp.get(key)
        if value is None:
            continue
        item = by_ref.get(value) or by_path.get(value)
        require(item is not None, f"planning manifest current_pointers.{key} must point to registry ref or path", errors)
        if item:
            parsed = parse_hilp_ref(item.get("asset_ref"))
            require(parsed and (parsed["phase"], parsed["artifact"]) == (phase, artifact), f"planning manifest current_pointers.{key} must point to {phase}/{artifact}", errors)
            require(item.get("lifecycle_state") == state, f"planning manifest current_pointers.{key} must point to lifecycle_state={state}", errors)
            require(item.get("record_role") == role, f"planning manifest current_pointers.{key} must point to record_role={role}", errors)


def resolve(value, by_ref, by_path):
    if value is None:
        return None
    return by_ref.get(value) or by_path.get(value)


def exists_path(base: Path, value: str) -> bool:
    p = Path(value)
    return p.exists() or (base / value).exists()


def by_role(reg, role):
    return [i for i in reg if isinstance(i, dict) and i.get("record_role") == role]


def value_items(value, by_ref, by_path):
    if value is None:
        return []
    if isinstance(value, list):
        return [resolve(v, by_ref, by_path) for v in value]
    return [resolve(value, by_ref, by_path)]


def validate_current_asset_slot(slot, value, stage, by_ref, by_path, errors):
    if value is None:
        return
    expected_roles = CURRENT_ASSET_SLOT_ROLES.get(slot)
    if not expected_roles:
        return
    items = value_items(value, by_ref, by_path)
    if not items:
        errors.append(f"current_assets.{slot} must point to registry ref or path: {value}")
        return
    for item in items:
        if item is None:
            errors.append(f"current_assets.{slot} must point to registry ref or path: {value}")
            continue
        role = item.get("record_role")
        state = item.get("lifecycle_state")
        if role not in expected_roles:
            errors.append(f"current_assets.{slot} must point to record_role={sorted(expected_roles)}, got {role}")
        allowed_states = CURRENT_ASSET_STAGE_STATES.get(slot, {}).get(stage)
        if allowed_states and state not in allowed_states:
            errors.append(f"current_assets.{slot} incompatible with package_stage={stage}; got lifecycle_state={state}")


def any_role(reg, roles, states=None):
    for item in reg:
        if not isinstance(item, dict):
            continue
        if item.get("record_role") in roles and (states is None or item.get("lifecycle_state") in states):
            return item
    return None


def is_completed_plan_or_runbook(item):
    return bool(item) and item.get("record_role") in {"plan", "runbook"} and item.get("lifecycle_state") in {"completed", "closed-record"}


def is_completed_inline_record(item):
    return bool(item) and item.get("record_role") == "inline-execution-record" and item.get("lifecycle_state") in {"completed", "closed-record"}


def unsafe_path(value):
    if not isinstance(value, str) or not value or URL_RE.match(value) or ASSET_REF_RE.match(value):
        return False
    if "\\" in value:
        return True
    # source_hilp_manifest may intentionally reference ../planning/manifest.md; asset paths may not.
    p = PurePosixPath(value)
    return p.is_absolute() or value.strip() != value


def validate_asset_path(label, value, errors):
    if unsafe_path(value) or (isinstance(value, str) and ".." in PurePosixPath(value).parts):
        errors.append(f"unsafe asset path for {label}: {value}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--check-paths", action="store_true")
    ap.add_argument("--allow-draft-paths", action="store_true")
    ap.add_argument("--planning-manifest", help="optional HILP planning manifest used to verify source_handoff_ref provenance")
    ap.add_argument("--allow-absolute-source-manifest", action="store_true", help="Allow source_hilp_manifest to be absolute. Default rejects it for portable persisted manifests.")
    args = ap.parse_args()
    path = Path(args.manifest)
    errors = []
    try:
        m = load_manifest(path)
    except Exception as exc:
        print(f"INVALID execution manifest parse: {exc}")
        sys.exit(1)

    require(str(m.get("schema_version")) == str(CANON.get("schema_version", "2.24")), "schema_version must match canonical schema", errors)
    require(str(m.get("protocol_version")) == str(CANON.get("protocol_version", "2.24")), "protocol_version must match canonical schema", errors)
    require(m.get("protocol") == "HILE", "protocol must be HILE", errors)
    tier = m.get("execution_tier")
    stage = m.get("package_stage") or "initialized"
    intake = m.get("intake_status")
    require(tier in VALID_TIERS, f"execution_tier must be {'|'.join(sorted(VALID_TIERS))}", errors)
    require(stage in VALID_STAGES, "package_stage invalid", errors)
    require(intake in VALID_INTAKE, "intake_status invalid", errors)
    require(bool(m.get("source_hilp_manifest")), "source_hilp_manifest required", errors)
    src_manifest = m.get("source_hilp_manifest")
    if isinstance(src_manifest, str) and Path(src_manifest).is_absolute() and not args.allow_absolute_source_manifest:
        errors.append("source_hilp_manifest must be relative unless --allow-absolute-source-manifest is set")
    source_handoff_ref = m.get("source_handoff_ref")
    require(bool(source_handoff_ref), "source_handoff_ref required", errors)
    if source_handoff_ref:
        require(isinstance(source_handoff_ref, str) and HILP_HANDOFF_REF_RE.match(source_handoff_ref), "source_handoff_ref must match phase-05/execution-handoff@vN", errors)
    if args.planning_manifest:
        try:
            planning_manifest = load_manifest(Path(args.planning_manifest))
            validate_hilp_manifest_contract(planning_manifest, errors)
            item = find_planning_handoff(planning_manifest, source_handoff_ref)
            require(item is not None, "source_handoff_ref not found in planning manifest asset_registry", errors)
            if item:
                require(item.get("lifecycle_state") == "closed-record", "source_handoff_ref must point to closed-record in planning manifest", errors)
                require(item.get("record_role") == "handoff-record", "source_handoff_ref must point to handoff-record in planning manifest", errors)
                require(item.get("owner_skill") == "human-in-loop-execution", "source_handoff_ref must be owned by human-in-loop-execution", errors)
                require(item.get("owner_protocol") == "HILE", "source_handoff_ref must use owner_protocol=HILE", errors)
        except Exception as exc:
            errors.append(f"planning manifest validation failed: {exc}")
    ca = m.get("current_assets")
    cp = m.get("current_pointers")
    reg = m.get("asset_registry")
    require(isinstance(ca, dict), "current_assets must be mapping", errors)
    require(isinstance(cp, dict), "current_pointers must be mapping", errors)
    require(isinstance(reg, list), "asset_registry must be list", errors)
    if isinstance(ca, dict):
        for key in REQUIRED_CURRENT_ASSETS:
            require(key in ca, f"current_assets.{key} required", errors)
        for key, value in ca.items():
            validate_asset_path(f"current_assets.{key}", value, errors)
    if isinstance(cp, dict):
        for key in REQUIRED_POINTERS:
            require(key in cp, f"current_pointers.{key} required", errors)
        require(bool(cp.get("human_status")), "current_pointers.human_status required", errors)
        require(bool(cp.get("agent_directory")), "current_pointers.agent_directory required", errors)
        for key, value in cp.items():
            validate_asset_path(f"current_pointers.{key}", value, errors)

    seen = set()
    paths = []
    registry_path_values = []
    if isinstance(reg, list):
        for i, item in enumerate(reg):
            prefix = f"asset_registry[{i}]"
            require(isinstance(item, dict), f"{prefix} must be mapping", errors)
            if not isinstance(item, dict):
                continue
            for key in REGISTRY_REQUIRED:
                require(key in item, f"{prefix}.{key} required", errors)
            for key in ["path", "human_view", "agent_view"]:
                require(bool(item.get(key)), f"{prefix}.{key} required for dual-view contract", errors)
                validate_asset_path(f"{prefix}.{key}", item.get(key), errors)
            ref = item.get("asset_ref")
            if ref:
                require(ref not in seen, f"duplicate asset_ref: {ref}", errors)
                seen.add(ref)
                mref = ASSET_REF_RE.match(ref)
                require(bool(mref), f"{prefix}.asset_ref must match hile/artifact@vN: {ref}", errors)
                if mref:
                    ver = int(mref.group(2))
                    require(item.get("version") == ver, f"{prefix}.version must match asset_ref @vN", errors)
            if item.get("path"):
                paths.append(item["path"])
                registry_path_values.append((f"{prefix}.path", item["path"]))
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
            require(item.get("owner_skill") in VALID_OWNER_SKILLS, f"{prefix}.owner_skill invalid or missing", errors)
            require(item.get("owner_protocol") in VALID_OWNER_PROTOCOLS, f"{prefix}.owner_protocol invalid or missing", errors)
            require(isinstance(item.get("version"), int) and item.get("version") >= 1, f"{prefix}.version must be integer >= 1", errors)
            if state == "superseded":
                require(bool(item.get("superseded_by")), f"{prefix}.superseded_by required when lifecycle_state=superseded", errors)

    reg_list = reg if isinstance(reg, list) else []
    by_ref, by_path = maps(reg_list)
    if isinstance(ca, dict):
        if intake == "pass":
            require(bool(ca.get("intake_summary")), "intake_status=pass requires current_assets.intake_summary", errors)
        if tier == "standard" and stage in {"planned", "confirmed", "in-progress", "blocked", "failed", "completed"}:
            require(bool(ca.get("current_plan")), "standard planned-or-later package requires current_assets.current_plan", errors)
        if tier == "strict" and stage in {"planned", "confirmed", "in-progress", "blocked", "failed", "completed"}:
            require(bool(ca.get("current_runbook")), "strict planned-or-later package requires current_assets.current_runbook", errors)
        if tier in {"standard", "strict"} and stage in {"confirmed", "in-progress"}:
            active_ref = ca.get("current_plan") if tier == "standard" else ca.get("current_runbook")
            active_item = resolve(active_ref, by_ref, by_path)
            require(active_item is not None, f"{tier} {stage} package requires a resolvable confirmed plan/runbook", errors)
            if active_item is not None:
                required_state = "confirmed" if stage == "confirmed" else "in-progress"
                require(active_item.get("lifecycle_state") == required_state, f"{tier} package_stage={stage} requires current plan/runbook lifecycle_state={required_state}", errors)
        if tier == "strict" and stage in {"in-progress", "blocked", "failed", "completed"}:
            require(bool(ca.get("ledger")), "strict in-progress-or-later package requires current_assets.ledger", errors)
            require(bool(ca.get("unit_summaries")), "strict in-progress-or-later package requires current_assets.unit_summaries", errors)
        if stage == "initialized":
            for role in ["plan", "runbook", "inline-execution-record", "verification-evidence", "completion-record", "failure-forensics"]:
                completedish = [i for i in by_role(reg_list, role) if i.get("lifecycle_state") in {"completed", "closed-record", "failed"}]
                require(not completedish, f"initialized package must not contain completed/closed/failed {role} assets", errors)
        if stage == "completed":
            latest_item = None
            if isinstance(cp, dict) and cp.get("latest_runbook_or_plan"):
                latest_item = resolve(cp.get("latest_runbook_or_plan"), by_ref, by_path)
                require(is_completed_plan_or_runbook(latest_item), "completed package latest_runbook_or_plan must point to completed/closed plan or runbook", errors)
            current_plan_items = [resolve(ca.get(key), by_ref, by_path) for key in ["current_plan", "current_runbook"]]
            if latest_item:
                current_plan_items.append(latest_item)
            completed_plan_or_runbook = any(is_completed_plan_or_runbook(item) for item in current_plan_items)
            inline_item = resolve(ca.get("tiny_inline_record"), by_ref, by_path)
            completed_inline = tier == "tiny" and is_completed_inline_record(inline_item)
            if tier in {"standard", "strict"}:
                require(completed_plan_or_runbook, f"completed {tier} package requires completed/closed plan or runbook", errors)
            else:
                require(completed_plan_or_runbook or completed_inline, "completed tiny package requires completed/closed plan/runbook or tiny_inline_record", errors)
            require(bool(ca.get("verification_evidence")) or any_role(reg_list, {"verification-evidence"}, {"completed", "closed-record"}) is not None, "completed package requires verification evidence", errors)
            require(bool(ca.get("completion_review")) or any_role(reg_list, {"completion-record"}, {"completed", "closed-record"}) is not None, "completed package requires completion review", errors)
        for key, value in ca.items():
            if value is None:
                continue
            validate_current_asset_slot(key, value, stage, by_ref, by_path, errors)
    if isinstance(cp, dict):
        active = cp.get("active_runbook_or_plan")
        if active:
            item = resolve(active, by_ref, by_path)
            require(item is not None, "current_pointers.active_runbook_or_plan must point to registry ref or path", errors)
            if item:
                require(item.get("record_role") in {"runbook", "plan"}, "active_runbook_or_plan must point to runbook or plan", errors)
                require(item.get("lifecycle_state") in {"ready-for-confirmation", "confirmed", "in-progress", "blocked"}, "active_runbook_or_plan must not point to completed/failed/superseded asset", errors)
        if stage in {"completed", "failed"}:
            require(not active, f"{stage} package must not have active_runbook_or_plan", errors)
        latest_plan = cp.get("latest_runbook_or_plan")
        if latest_plan:
            item = resolve(latest_plan, by_ref, by_path)
            require(item is not None, "current_pointers.latest_runbook_or_plan must point to registry ref or path", errors)
            if item:
                require(item.get("record_role") in {"runbook", "plan"}, "latest_runbook_or_plan must point to runbook or plan", errors)
        latest = cp.get("latest_verification")
        if latest:
            item = resolve(latest, by_ref, by_path)
            require(item is not None, "current_pointers.latest_verification must point to registry ref or path", errors)
            if item:
                require(item.get("record_role") == "verification-evidence", "latest_verification must point to verification-evidence", errors)
        latest_completion = cp.get("latest_completion_review")
        if latest_completion:
            item = resolve(latest_completion, by_ref, by_path)
            require(item is not None, "current_pointers.latest_completion_review must point to registry ref or path", errors)
            if item:
                require(item.get("record_role") == "completion-record", "latest_completion_review must point to completion-record", errors)
    if args.check_paths:
        base = path.parent
        src = m.get("source_hilp_manifest")
        if src and isinstance(src, str) and not URL_RE.match(src):
            if not exists_path(base, src) and not args.allow_draft_paths:
                errors.append(f"source_hilp_manifest path does not exist: {src}")
        for collection in [ca or {}, cp or {}]:
            if isinstance(collection, dict):
                for key, rel in collection.items():
                    if rel and isinstance(rel, str) and rel not in by_ref and not URL_RE.match(rel):
                        if not exists_path(base, rel) and not args.allow_draft_paths:
                            errors.append(f"path does not exist for {key}: {rel}")
        for label, rel in registry_path_values:
            if rel and isinstance(rel, str) and not URL_RE.match(rel) and not exists_path(base, rel) and not args.allow_draft_paths:
                errors.append(f"path does not exist for {label}: {rel}")
    if errors:
        print("EXECUTION_MANIFEST_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print("execution manifest ok")
    sys.exit(0)

if __name__ == "__main__":
    main()
