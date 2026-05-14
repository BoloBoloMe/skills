#!/usr/bin/env python3
"""Validate a repository-aware HILE Plan or Runbook before file modification."""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import check_allowed_files as scope_gate  # noqa: E402

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
HILP_HANDOFF_REF_RE = re.compile(r"^phase-05/execution-handoff@v\d+$")
HILP_BLUEPRINT_REF_RE = re.compile(r"^phase-03/implementation-blueprint@v\d+$")
HILE_ASSET_RE = re.compile(r"^hile/(plan|runbook)@v\d+$")
PLACEHOLDER_RE = re.compile(r"<[^>]+>|@vN\b")


def load_yaml_blocks(path):
    text = Path(path).read_text(encoding="utf-8")
    blocks = []
    for block in FENCE_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict):
            blocks.append(data)
    if not blocks:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            blocks.append(data)
    return blocks


def first_mapping(path, keys):
    for data in load_yaml_blocks(path):
        for key in keys:
            if isinstance(data.get(key), dict):
                return key, data[key]
        if any(k in data for k in ["source_handoff_ref", "source_execution_units", "unit_plans"]):
            return "plan", data
    raise ValueError(f"no {keys} mapping found in {path}")


def norm_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return []


def nonempty(value):
    return value is not None and value != [] and value != {} and value != ""


def load_manifest(path):
    for data in load_yaml_blocks(path):
        if isinstance(data.get("manifest"), dict):
            return data["manifest"]
    raise ValueError("execution manifest must contain top-level manifest mapping")


def require(cond, msg, errors):
    if not cond:
        errors.append(msg)


def manifest_tier(manifest):
    return manifest.get("execution_tier")


def source_units_from_handoff(handoff_path):
    unit_ids = set()
    for data in load_yaml_blocks(handoff_path):
        root = data.get("execution_handoff") or data.get("handoff") or data
        if not isinstance(root, dict):
            continue
        for eu in root.get("execution_units") or []:
            if isinstance(eu, dict) and eu.get("unit_id"):
                unit_ids.add(str(eu["unit_id"]))
    return unit_ids


def validate_scope(plan_doc, handoff_path, workspace, errors):
    all_planned = []
    unit_planned = []
    for unit in plan_doc.get("unit_plans") or []:
        if not isinstance(unit, dict):
            continue
        uid = str(unit.get("unit_id"))
        for f in norm_list(unit.get("planned_files")):
            all_planned.append(f)
            unit_planned.append((uid, f))
    tmp_all = Path(workspace) / ".hile-planned-files.tmp"
    try:
        tmp_all.write_text("\n".join(all_planned) + ("\n" if all_planned else ""), encoding="utf-8")
        raw_allowed, raw_prohibited, _, _, _ = scope_gate.scope_from_handoff(handoff_path, None)
        scope_errors = []
        ws = Path(workspace).resolve(strict=False)
        allowed = scope_gate.normalize_patterns(raw_allowed, ws, "allowed_files", scope_errors)
        prohibited = scope_gate.normalize_patterns(raw_prohibited, ws, "prohibited_files", scope_errors)
        planned = scope_gate.normalize_files(all_planned, ws, "planned", scope_errors)
        if scope_errors:
            errors.extend(scope_errors)
        if not allowed:
            errors.append("no explicit handoff allowed_files patterns found")
        errors.extend(scope_gate.check_files("planned", planned, allowed, prohibited))
        for uid in sorted({u for u, _ in unit_planned if u and u != "None"}):
            raw_allowed, raw_prohibited, raw_unit_allowed, raw_unit_prohibited, unit_found = scope_gate.scope_from_handoff(handoff_path, uid)
            if not unit_found:
                errors.append(f"execution unit not found in handoff: {uid}")
                continue
            unit_errors = []
            unit_allowed = scope_gate.normalize_patterns(raw_unit_allowed, ws, "execution_units.allowed_files", unit_errors)
            unit_prohibited = scope_gate.normalize_patterns(raw_unit_prohibited, ws, "execution_units.prohibited_files", unit_errors)
            unit_files = scope_gate.normalize_files([f for u, f in unit_planned if u == uid], ws, f"planned for unit {uid}", unit_errors)
            if unit_errors:
                errors.extend(unit_errors)
            if not unit_allowed:
                errors.append(f"no execution_units.allowed_files for unit {uid}")
            errors.extend(scope_gate.check_files(f"planned for unit {uid}", unit_files, unit_allowed, unit_prohibited))
    finally:
        try:
            tmp_all.unlink()
        except OSError:
            pass


def step_files(step):
    return norm_list(step.get("files")) if isinstance(step, dict) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_or_runbook")
    ap.add_argument("--handoff", required=True)
    ap.add_argument("--execution-manifest", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--allow-tiny-unconfirmed", action="store_true")
    args = ap.parse_args()
    errors = []
    try:
        doc_type, doc = first_mapping(args.plan_or_runbook, ["plan", "runbook"])
    except Exception as exc:
        print(f"PLAN_OR_RUNBOOK_ERRORS\n{exc}")
        sys.exit(1)
    try:
        manifest = load_manifest(args.execution_manifest)
    except Exception as exc:
        print(f"PLAN_OR_RUNBOOK_ERRORS\nexecution manifest parse failed: {exc}")
        sys.exit(1)

    tier = manifest_tier(manifest)
    require(tier in {"tiny", "standard", "strict"}, "execution manifest execution_tier must be tiny|standard|strict", errors)
    require(doc_type in {"plan", "runbook"}, "document must contain plan or runbook mapping", errors)
    if tier == "standard":
        require(doc_type == "plan", "standard execution requires a Plan, not a Runbook-only document", errors)
    if tier == "strict":
        require(doc_type == "runbook", "strict execution requires a Runbook", errors)

    asset_ref = doc.get("asset_ref")
    if asset_ref:
        require(bool(HILE_ASSET_RE.match(str(asset_ref))), "asset_ref must match hile/plan@vN or hile/runbook@vN", errors)
    source_handoff_ref = doc.get("source_handoff_ref")
    require(bool(source_handoff_ref), "source_handoff_ref required", errors)
    require(isinstance(source_handoff_ref, str) and HILP_HANDOFF_REF_RE.match(source_handoff_ref), "source_handoff_ref must match phase-05/execution-handoff@vN", errors)
    require(source_handoff_ref == manifest.get("source_handoff_ref"), "source_handoff_ref must match execution manifest", errors)
    source_blueprint_ref = doc.get("source_blueprint_ref")
    require(bool(source_blueprint_ref), "source_blueprint_ref required", errors)
    require(isinstance(source_blueprint_ref, str) and HILP_BLUEPRINT_REF_RE.match(source_blueprint_ref), "source_blueprint_ref must match phase-03/implementation-blueprint@vN", errors)

    source_units = norm_list(doc.get("source_execution_units"))
    require(bool(source_units), "source_execution_units required", errors)
    known_units = source_units_from_handoff(args.handoff)
    for uid in source_units:
        require(uid in known_units, f"source_execution_unit not found in handoff: {uid}", errors)

    repo_context = doc.get("repo_context")
    require(isinstance(repo_context, dict), "repo_context mapping required", errors)
    if isinstance(repo_context, dict):
        for key in ["workspace", "branch", "commit"]:
            require(nonempty(repo_context.get(key)), f"repo_context.{key} required", errors)

    unit_plans = doc.get("unit_plans")
    require(isinstance(unit_plans, list) and bool(unit_plans), "unit_plans non-empty list required", errors)
    seen_units = set()
    if isinstance(unit_plans, list):
        for idx, unit in enumerate(unit_plans):
            prefix = f"unit_plans[{idx}]"
            require(isinstance(unit, dict), f"{prefix} must be mapping", errors)
            if not isinstance(unit, dict):
                continue
            uid = str(unit.get("unit_id"))
            require(uid in source_units, f"{prefix}.unit_id must be listed in source_execution_units", errors)
            seen_units.add(uid)
            planned_files = norm_list(unit.get("planned_files"))
            require(bool(planned_files), f"{prefix}.planned_files required", errors)
            repo_observations = unit.get("repo_observations")
            require(isinstance(repo_observations, list) and bool(repo_observations), f"{prefix}.repo_observations non-empty list required", errors)
            if isinstance(repo_observations, list):
                for oi, obs in enumerate(repo_observations):
                    op = f"{prefix}.repo_observations[{oi}]"
                    require(isinstance(obs, dict), f"{op} must be mapping", errors)
                    if isinstance(obs, dict):
                        require(nonempty(obs.get("file")) or nonempty(obs.get("anchor")), f"{op} requires file or anchor", errors)
                        require(nonempty(obs.get("status")), f"{op}.status required", errors)
                        require(nonempty(obs.get("observation")), f"{op}.observation required", errors)
            steps = unit.get("implementation_steps")
            require(isinstance(steps, list) and bool(steps), f"{prefix}.implementation_steps non-empty list required", errors)
            if isinstance(steps, list):
                for si, step in enumerate(steps):
                    sp = f"{prefix}.implementation_steps[{si}]"
                    require(isinstance(step, dict), f"{sp} must be mapping", errors)
                    if isinstance(step, dict):
                        require(nonempty(step.get("step_id")), f"{sp}.step_id required", errors)
                        require(nonempty(step.get("action")), f"{sp}.action required", errors)
                        files = step_files(step)
                        require(bool(files), f"{sp}.files required", errors)
                        for f in files:
                            require(f in planned_files, f"{sp}.files entry not in planned_files: {f}", errors)
                        require(nonempty(step.get("anchors")) or nonempty(step.get("expected_result")), f"{sp} requires anchors or expected_result", errors)
            source_intent = unit.get("source_level_change_intent")
            require(isinstance(source_intent, list) and bool(source_intent), f"{prefix}.source_level_change_intent non-empty list required", errors)
            valid_step_ids = {str(step.get("step_id")) for step in steps if isinstance(step, dict) and step.get("step_id")} if isinstance(steps, list) else set()
            if isinstance(source_intent, list):
                for ci, item in enumerate(source_intent):
                    cp = f"{prefix}.source_level_change_intent[{ci}]"
                    require(isinstance(item, dict), f"{cp} must be mapping", errors)
                    if isinstance(item, dict):
                        file_value = str(item.get("file") or "")
                        require(nonempty(file_value), f"{cp}.file required", errors)
                        if file_value:
                            require(file_value in planned_files, f"{cp}.file entry not in planned_files: {file_value}", errors)
                        require(nonempty(item.get("symbol_or_anchor")) or nonempty(item.get("location")), f"{cp} requires symbol_or_anchor or location", errors)
                        require(nonempty(item.get("change_type")), f"{cp}.change_type required", errors)
                        require(nonempty(item.get("intent")), f"{cp}.intent required", errors)
                        require(isinstance(item.get("intended_operations"), list) and bool(item.get("intended_operations")), f"{cp}.intended_operations non-empty list required", errors)
                        require(isinstance(item.get("review_focus"), list) and bool(item.get("review_focus")), f"{cp}.review_focus non-empty list required", errors)
                        for field in ["intent", "intended_operations"]:
                            values = item.get(field) if isinstance(item.get(field), list) else [item.get(field)]
                            text = "\n".join(str(v) for v in values if v is not None)
                            require(not re.search(r"(?m)^(@@ |\+\+\+ |--- |[+-]\s*[^\s-])", text), f"{cp}.{field} must describe intent, not embed a unified diff or patch hunk", errors)
                        related = norm_list(item.get("related_implementation_steps"))
                        for sid in related:
                            require(sid in valid_step_ids, f"{cp}.related_implementation_steps entry not found in implementation_steps: {sid}", errors)
            verification_plan = unit.get("verification_plan")
            require(isinstance(verification_plan, dict), f"{prefix}.verification_plan mapping required", errors)
            if isinstance(verification_plan, dict):
                require(nonempty(verification_plan.get("commands")) or nonempty(verification_plan.get("manual_checks")), f"{prefix}.verification_plan requires commands or manual_checks", errors)
                require(nonempty(verification_plan.get("expected_results")), f"{prefix}.verification_plan.expected_results required", errors)
                require(nonempty(verification_plan.get("evidence_to_collect")), f"{prefix}.verification_plan.evidence_to_collect required", errors)
            for key in ["risk_checks", "stop_conditions"]:
                require(isinstance(unit.get(key), list) and bool(unit.get(key)), f"{prefix}.{key} non-empty list required", errors)
    missing_unit_plans = set(source_units) - seen_units
    for uid in sorted(missing_unit_plans):
        errors.append(f"missing unit_plan for source_execution_unit: {uid}")

    gate = doc.get("pre_modify_gate")
    require(isinstance(gate, dict), "pre_modify_gate mapping required", errors)
    if isinstance(gate, dict):
        check = gate.get("planned_files_check")
        require(isinstance(check, dict), "pre_modify_gate.planned_files_check mapping required", errors)
        if isinstance(check, dict):
            require(nonempty(check.get("command")), "pre_modify_gate.planned_files_check.command required", errors)
            require(check.get("result") == "pass", "pre_modify_gate.planned_files_check.result must be pass", errors)
        require(norm_list(gate.get("out_of_scope_files")) == [], "pre_modify_gate.out_of_scope_files must be empty", errors)

    confirmation = doc.get("confirmation")
    require(isinstance(confirmation, dict), "confirmation mapping required", errors)
    if isinstance(confirmation, dict):
        required = confirmation.get("required")
        if tier in {"standard", "strict"}:
            require(required is True, f"{tier} confirmation.required must be true", errors)
            require(confirmation.get("status") in {"pending", "confirmed"}, "confirmation.status must be pending or confirmed", errors)
            cmd = confirmation.get("required_command")
            expected = "Runbook" if tier == "strict" else "Plan"
            require(isinstance(cmd, str) and cmd.startswith(f"确认执行：确认执行 {expected} "), f"confirmation.required_command must be fixed {expected} confirmation command", errors)
            require(isinstance(cmd, str) and not PLACEHOLDER_RE.search(cmd or ""), "confirmation.required_command must not contain placeholders", errors)
        elif not args.allow_tiny_unconfirmed:
            require(required is True, "tiny without --allow-tiny-unconfirmed still requires confirmation.required=true", errors)

    validate_scope(doc, args.handoff, args.workspace, errors)

    if errors:
        print("PLAN_OR_RUNBOOK_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print("plan/runbook ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
