#!/usr/bin/env python3
"""Validate HILP agent-facing design, blueprint, and handoff asset content.

This validator complements validate_manifest.py. The manifest validator proves that
asset registry state and pointers are coherent; this validator proves that the
current agent-facing assets contain enough concrete content for HILE intake.
"""
import argparse
import fnmatch
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
REF_RE = re.compile(r"^(phase-\d{2})/([A-Za-z0-9_-]+)@v(\d+)$")
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>|\bTODO\b|@vN", re.IGNORECASE)
PATCHLIKE_RE = re.compile(r"diff --git|^@@|\breplace line\b|\binsert below\b", re.IGNORECASE | re.MULTILINE)

KIND_KEY = {
    "design-choice": "design_choice",
    "implementation-blueprint": "implementation_blueprint",
    "execution-handoff": "execution_handoff",
}
EXPECTED_PHASE = {
    "design-choice": "phase-02",
    "implementation-blueprint": "phase-03",
    "execution-handoff": "phase-05",
}
EXPECTED_REF_ARTIFACT = {
    "design-choice": "design-choice",
    "implementation-blueprint": "implementation-blueprint",
    "execution-handoff": "execution-handoff",
}


def load_yaml_blocks(path):
    text = path.read_text(encoding="utf-8")
    blocks = FENCE_RE.findall(text)
    if not blocks and text.strip():
        blocks = [text]
    loaded = []
    for block in blocks:
        try:
            data = yaml.safe_load(block)
        except Exception as exc:
            raise ValueError(f"{path}: invalid yaml block: {exc}") from exc
        if isinstance(data, dict):
            loaded.append(data)
    return loaded


def load_yaml_with_key(path, key):
    for data in load_yaml_blocks(path):
        if key in data:
            return data
    raise ValueError(f"{path}: no yaml block with key {key}")


def load_manifest(path):
    data = load_yaml_with_key(path, "manifest")
    manifest = data.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError(f"{path}: manifest must be a mapping")
    return manifest


def load_asset(path, kind):
    key = KIND_KEY[kind]
    data = load_yaml_with_key(path, key)
    if not isinstance(data.get(key), dict):
        raise ValueError(f"{path}: {key} must be a mapping")
    return data


def is_nonempty(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def require(cond, msg, errors):
    if not cond:
        errors.append(msg)


def parse_ref(ref):
    if not isinstance(ref, str):
        return None
    m = REF_RE.match(ref)
    if not m:
        return None
    phase, artifact, version = m.groups()
    return {"phase": phase, "artifact": artifact, "version": int(version)}


def walk_strings(value, prefix="$"):
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from walk_strings(v, f"{prefix}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk_strings(v, f"{prefix}[{i}]")


def check_no_placeholders(data, label, errors):
    for path, value in walk_strings(data):
        if PLACEHOLDER_RE.search(value):
            errors.append(f"{label}: unresolved placeholder in {path}: {value}")


def path_allowed_by_patterns(path, patterns):
    if not isinstance(path, str) or not path:
        return False
    for pat in patterns or []:
        if not isinstance(pat, str):
            continue
        if path == pat or fnmatch.fnmatchcase(path, pat):
            return True
        if pat.endswith("/**"):
            base = pat[:-3].rstrip("/")
            if path.startswith(base + "/"):
                return True
        if pat.endswith("/*"):
            base = pat[:-2].rstrip("/")
            if path.startswith(base + "/"):
                return True
    return False


def require_subset(child, parent, label, errors):
    if not isinstance(child, list):
        errors.append(f"{label}: expected list")
        return
    for item in child:
        if not path_allowed_by_patterns(item, parent):
            errors.append(f"{label}: {item} is outside allowed_files")


def require_required_fields(data, fields, label, errors):
    for field in fields:
        require(field in data, f"{label}: missing required field {field}", errors)


def validate_common(data, kind, errors):
    label = kind
    require_required_fields(data, ["asset_ref", "phase_id", "lifecycle_state", "record_role", KIND_KEY[kind]], label, errors)
    ref = data.get("asset_ref")
    parsed = parse_ref(ref)
    require(parsed is not None, f"{label}: asset_ref must match phase-nn/artifact@vN", errors)
    if parsed:
        require(parsed["phase"] == EXPECTED_PHASE[kind], f"{label}: asset_ref phase must be {EXPECTED_PHASE[kind]}", errors)
        require(parsed["artifact"] == EXPECTED_REF_ARTIFACT[kind], f"{label}: asset_ref artifact must be {EXPECTED_REF_ARTIFACT[kind]}", errors)
        require(data.get("phase_id") == parsed["phase"], f"{label}: phase_id must match asset_ref", errors)
    check_no_placeholders(data, label, errors)
    return parsed


def validate_approval_command(data, prefix, errors, label):
    body = data.get(KIND_KEY[label], {})
    approval = body.get("approval") if isinstance(body, dict) else None
    cmd = approval.get("required_command") if isinstance(approval, dict) else None
    expected = f"{prefix}{data.get('asset_ref')}"
    require(isinstance(cmd, str) and cmd == expected, f"{label}: approval.required_command must be concrete command {expected}", errors)


def validate_design(data, errors):
    validate_common(data, "design-choice", errors)
    dc = data.get("design_choice") or {}
    require(data.get("phase_id") == "phase-02", "design-choice: phase_id must be phase-02", errors)
    alternatives = dc.get("alternatives")
    require(isinstance(alternatives, list) and len(alternatives) > 0, "design-choice: design_choice.alternatives must be nonempty", errors)
    alt_ids = set()
    if isinstance(alternatives, list):
        for i, alt in enumerate(alternatives):
            if not isinstance(alt, dict):
                errors.append(f"design-choice: alternative[{i}] must be mapping")
                continue
            for field in ["id", "summary", "pros", "cons", "risks"]:
                require(is_nonempty(alt.get(field)), f"design-choice: alternative[{i}].{field} must be nonempty", errors)
            if alt.get("id"):
                alt_ids.add(alt.get("id"))
    recommended = dc.get("recommended_option")
    require(is_nonempty(recommended), "design-choice: recommended_option required", errors)
    require(recommended in alt_ids, "design-choice: recommended_option must match an alternative id", errors)
    require(is_nonempty(dc.get("rationale")), "design-choice: rationale must be nonempty", errors)
    if data.get("lifecycle_state") == "approved":
        require(data.get("record_role") == "approval-record", "design-choice: approved asset must use record_role=approval-record", errors)
        validate_approval_command(data, "批准设计：批准 ", errors, "design-choice")


def verification_contract_ok(vc):
    if not isinstance(vc, dict) or not vc:
        return False
    return any(is_nonempty(vc.get(k)) for k in ["must_haves", "test_commands", "manual_checks"])


def validate_blueprint(data, errors, expected_design_ref=None):
    validate_common(data, "implementation-blueprint", errors)
    bp = data.get("implementation_blueprint") or {}
    require(data.get("phase_id") == "phase-03", "implementation-blueprint: phase_id must be phase-03", errors)
    if expected_design_ref:
        require(bp.get("source_design_ref") == expected_design_ref, f"implementation-blueprint: source_design_ref must be {expected_design_ref}", errors)
    else:
        require(is_nonempty(bp.get("source_design_ref")), "implementation-blueprint: source_design_ref required", errors)
    allowed = bp.get("allowed_files")
    require(isinstance(allowed, list) and len(allowed) > 0, "implementation-blueprint: allowed_files must be nonempty", errors)
    require("forbidden_files" in bp and isinstance(bp.get("forbidden_files"), list), "implementation-blueprint: forbidden_files must exist as a list", errors)
    units = bp.get("execution_units")
    require(isinstance(units, list) and len(units) > 0, "implementation-blueprint: execution_units must be nonempty", errors)
    if isinstance(units, list):
        for i, unit in enumerate(units):
            label = f"implementation-blueprint: execution_units[{i}]"
            if not isinstance(unit, dict):
                errors.append(f"{label} must be mapping")
                continue
            for field in ["unit_id", "objective", "allowed_files", "implementation_intent", "verification", "stop_conditions"]:
                require(field in unit and is_nonempty(unit.get(field)), f"{label}.{field} must be nonempty", errors)
            for field in ["prohibited_files", "dependencies"]:
                require(field in unit and isinstance(unit.get(field), list), f"{label}.{field} must exist as a list", errors)
            if isinstance(unit.get("allowed_files"), list):
                require_subset(unit.get("allowed_files"), allowed or [], f"{label}.allowed_files", errors)
            intent = unit.get("implementation_intent")
            for _, s in walk_strings(intent):
                if PATCHLIKE_RE.search(s):
                    errors.append(f"{label}.implementation_intent must not contain patch-like instructions without exact commit/context evidence")
    require(verification_contract_ok(bp.get("verification_contract")), "implementation-blueprint: verification_contract must have must_haves, test_commands, or manual_checks", errors)
    if data.get("lifecycle_state") == "approved":
        require(data.get("record_role") == "approval-record", "implementation-blueprint: approved asset must use record_role=approval-record", errors)
        validate_approval_command(data, "批准蓝图：批准 ", errors, "implementation-blueprint")


def extract_unit_ids(units):
    result = set()
    if isinstance(units, list):
        for item in units:
            if isinstance(item, dict) and item.get("unit_id"):
                result.add(item.get("unit_id"))
            elif isinstance(item, str):
                result.add(item)
    return result


def extract_scope_unit_ids(scope):
    result = set()
    if isinstance(scope, list):
        for item in scope:
            if isinstance(item, str):
                result.add(item)
            elif isinstance(item, dict) and item.get("unit_id"):
                result.add(item.get("unit_id"))
    return result


def validate_handoff(data, errors, expected_design_ref=None, expected_blueprint_ref=None, blueprint_data=None):
    validate_common(data, "execution-handoff", errors)
    hf = data.get("execution_handoff") or {}
    require(data.get("phase_id") == "phase-05", "execution-handoff: phase_id must be phase-05", errors)
    require(data.get("lifecycle_state") == "closed-record", "execution-handoff: lifecycle_state must be closed-record", errors)
    require(data.get("record_role") == "handoff-record", "execution-handoff: record_role must be handoff-record", errors)
    require(hf.get("owner_skill") == "human-in-loop-execution", "execution-handoff: owner_skill must be human-in-loop-execution", errors)
    require(hf.get("owner_protocol") == "HILE", "execution-handoff: owner_protocol must be HILE", errors)
    if expected_design_ref:
        require(hf.get("source_design_ref") == expected_design_ref, f"execution-handoff: source_design_ref must be {expected_design_ref}", errors)
    else:
        require(is_nonempty(hf.get("source_design_ref")), "execution-handoff: source_design_ref required", errors)
    if expected_blueprint_ref:
        require(hf.get("source_blueprint_ref") == expected_blueprint_ref, f"execution-handoff: source_blueprint_ref must be {expected_blueprint_ref}", errors)
    else:
        require(is_nonempty(hf.get("source_blueprint_ref")), "execution-handoff: source_blueprint_ref required", errors)
    allowed = hf.get("allowed_files")
    require(isinstance(allowed, list) and len(allowed) > 0, "execution-handoff: allowed_files must be nonempty", errors)
    require(is_nonempty(hf.get("execution_scope")), "execution-handoff: execution_scope must be nonempty", errors)
    require(is_nonempty(hf.get("prohibited_scope")), "execution-handoff: prohibited_scope must be nonempty", errors)
    require("prohibited_files" in hf and isinstance(hf.get("prohibited_files"), list), "execution-handoff: prohibited_files must exist as a list", errors)
    units = hf.get("execution_units")
    require(isinstance(units, list) and len(units) > 0, "execution-handoff: execution_units must be nonempty", errors)
    handoff_unit_ids = extract_unit_ids(units)
    scope_unit_ids = extract_scope_unit_ids(hf.get("execution_scope"))
    if scope_unit_ids and handoff_unit_ids:
        for unit_id in scope_unit_ids:
            require(unit_id in handoff_unit_ids, f"execution-handoff: execution_scope unit {unit_id} is not in execution_units", errors)
    if isinstance(units, list):
        for i, unit in enumerate(units):
            label = f"execution-handoff: execution_units[{i}]"
            if not isinstance(unit, dict):
                errors.append(f"{label} must be mapping")
                continue
            for field in ["unit_id", "objective", "allowed_files"]:
                require(field in unit and is_nonempty(unit.get(field)), f"{label}.{field} must be nonempty", errors)
            require("prohibited_files" in unit and isinstance(unit.get("prohibited_files"), list), f"{label}.prohibited_files must exist as a list", errors)
            has_verification = is_nonempty(unit.get("verification")) or unit.get("inherits_verification_contract") is True
            has_stop = is_nonempty(unit.get("stop_conditions")) or unit.get("inherits_stop_conditions") is True
            require(has_verification, f"{label} must define verification or inherits_verification_contract: true", errors)
            require(has_stop, f"{label} must define stop_conditions or inherits_stop_conditions: true", errors)
            if isinstance(unit.get("allowed_files"), list):
                require_subset(unit.get("allowed_files"), allowed or [], f"{label}.allowed_files", errors)
    require(verification_contract_ok(hf.get("verification_contract")), "execution-handoff: verification_contract must be nonempty", errors)
    require(is_nonempty(hf.get("stop_conditions")), "execution-handoff: stop_conditions must be nonempty", errors)
    hpr = hf.get("hile_planning_requirement")
    require(isinstance(hpr, dict) and hpr.get("required") is True, "execution-handoff: hile_planning_requirement.required must be true", errors)
    rule = hpr.get("rule") if isinstance(hpr, dict) else None
    require(isinstance(rule, str) and "repo-aware Plan or Runbook before modifying files" in rule, "execution-handoff: hile_planning_requirement.rule must require a repo-aware Plan or Runbook before modifying files", errors)
    if blueprint_data:
        bp = blueprint_data.get("implementation_blueprint") or {}
        bp_units = extract_unit_ids(bp.get("execution_units"))
        for unit_id in handoff_unit_ids:
            require(unit_id in bp_units, f"execution-handoff: unit {unit_id} is not in source blueprint", errors)
        bp_allowed = bp.get("allowed_files") or []
        if isinstance(allowed, list):
            require_subset(allowed, bp_allowed, "execution-handoff.allowed_files compared to blueprint", errors)


def resolve_manifest_asset(manifest, manifest_base, planning_root, current_key):
    registry = manifest.get("asset_registry") or []
    current_assets = manifest.get("current_assets") or {}
    value = current_assets.get(current_key)
    if not value:
        return None, None
    refs = {item.get("asset_ref"): item for item in registry if isinstance(item, dict)}
    paths = {}
    for item in registry:
        if not isinstance(item, dict):
            continue
        for key in ["path", "agent_view"]:
            if item.get(key):
                paths[item.get(key)] = item
    item = refs.get(value) or paths.get(value)
    candidate_values = []
    if item:
        for key in ["agent_view", "path"]:
            if item.get(key):
                candidate_values.append(item.get(key))
    elif isinstance(value, str):
        candidate_values.append(value)
    for rel in candidate_values:
        path = Path(rel)
        if path.is_absolute() and path.exists():
            return path, item
        for base in [manifest_base, planning_root]:
            candidate = base / rel
            if candidate.exists():
                return candidate, item
    return None, item


def load_manifest_assets(planning_root, manifest_path):
    manifest = load_manifest(manifest_path)
    manifest_base = manifest_path.parent
    loaded = {}
    items = {}
    for current_key, kind in [
        ("design_choice", "design-choice"),
        ("implementation_blueprint", "implementation-blueprint"),
        ("execution_handoff", "execution-handoff"),
    ]:
        path, item = resolve_manifest_asset(manifest, manifest_base, planning_root, current_key)
        if not path:
            raise ValueError(f"manifest current_assets.{current_key} does not resolve to a readable agent asset")
        loaded[kind] = load_asset(path, kind)
        items[kind] = item
    return loaded, items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("planning_root", nargs="?", default=".")
    ap.add_argument("--manifest")
    ap.add_argument("--asset")
    ap.add_argument("--kind", choices=sorted(KIND_KEY))
    ap.add_argument("--check-paths", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    errors = []
    planning_root = Path(args.planning_root).resolve()
    try:
        if args.asset:
            if not args.kind:
                raise ValueError("--asset requires --kind")
            data = load_asset(Path(args.asset), args.kind)
            if args.kind == "design-choice":
                validate_design(data, errors)
            elif args.kind == "implementation-blueprint":
                validate_blueprint(data, errors)
            elif args.kind == "execution-handoff":
                validate_handoff(data, errors)
        else:
            if not args.manifest:
                raise ValueError("manifest mode requires --manifest")
            manifest_path = Path(args.manifest)
            if not manifest_path.is_absolute():
                if manifest_path.exists():
                    manifest_path = manifest_path.resolve()
                else:
                    manifest_path = (planning_root / manifest_path).resolve()
            assets, _items = load_manifest_assets(planning_root, manifest_path)
            design = assets["design-choice"]
            blueprint = assets["implementation-blueprint"]
            handoff = assets["execution-handoff"]
            validate_design(design, errors)
            validate_blueprint(blueprint, errors, expected_design_ref=design.get("asset_ref"))
            validate_handoff(
                handoff,
                errors,
                expected_design_ref=design.get("asset_ref"),
                expected_blueprint_ref=blueprint.get("asset_ref"),
                blueprint_data=blueprint,
            )
    except Exception as exc:
        errors.append(str(exc))

    if errors:
        print("HILP_ASSET_ERRORS")
        for error in errors:
            print(error)
        return 1
    print("hilp assets ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
