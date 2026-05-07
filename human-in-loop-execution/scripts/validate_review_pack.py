#!/usr/bin/env python3
"""Validate a HILP/HILE review-pack enough to protect human approval entrypoints."""
import argparse
import re
import sys
from pathlib import Path, PurePosixPath

try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
URL_RE = re.compile(r"^https?://")
ASSET_REF_RE = re.compile(r"^(phase-\d{2}/[A-Za-z0-9_-]+@v\d+|hile/[A-Za-z0-9_-]+@v\d+)$")
ALLOWED = {
    "hilp": {"design_approval", "blueprint_approval", "handoff_review", "reapproval_decision"},
    "hile": {"runbook_confirmation", "plan_confirmation", "completion_review", "failure_forensics_review"},
}
CLOSED = {"approved", "confirmed", "rejected", "needs_revision", "needs_hilp_reapproval"}

COMMAND_RULES = {
    ("hilp", "design_approval"): re.compile(r"^批准设计：批准 phase-02/design-choice@v[0-9]+$"),
    ("hilp", "blueprint_approval"): re.compile(r"^批准蓝图：批准 phase-03/implementation-blueprint@v[0-9]+$"),
    ("hilp", "reapproval_decision"): re.compile(r"^批准重审：(批准|重做设计|重做蓝图|重做交接|阻断执行|维持原批准) phase-04/reapproval@v[0-9]+$"),
    ("hile", "runbook_confirmation"): re.compile(r"^确认执行：确认执行 Runbook .+"),
    ("hile", "plan_confirmation"): re.compile(r"^确认执行：确认执行 Plan .+"),
}
NO_COMMAND_DECISIONS = {
    ("hilp", "handoff_review"),
    ("hile", "completion_review"),
    ("hile", "failure_forensics_review"),
}
HILP_COMMAND_TARGET_RE = re.compile(r"(phase-\d{2}/[A-Za-z0-9_-]+@v\d+)$")
HILE_COMMAND_TARGET_RE = re.compile(r"确认执行：(?:确认执行 Runbook|确认执行 Plan) (.+)$")


def load_pack(path: Path):
    text = path.read_text(encoding="utf-8")
    for block in FENCE_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and isinstance(data.get("review_pack"), dict):
            return data["review_pack"]
    raise ValueError("review-pack must contain top-level review_pack mapping in a yaml fenced block")


def load_manifest(path: Path):
    text = path.read_text(encoding="utf-8")
    for block in FENCE_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and isinstance(data.get("manifest"), dict):
            return data["manifest"]
    raise ValueError("manifest must contain top-level manifest mapping")


def registry_refs(manifest):
    out = set()
    for item in manifest.get("asset_registry") or []:
        if isinstance(item, dict):
            if item.get("asset_ref"):
                out.add(item["asset_ref"])
            if item.get("path"):
                out.add(item["path"])
    return out


def unsafe_path(value):
    if value is None:
        return False
    if not isinstance(value, str):
        return True
    if value.startswith("http://") or value.startswith("https://") or ASSET_REF_RE.match(value):
        return False
    p = PurePosixPath(value)
    return p.is_absolute() or ".." in p.parts or "\\" in value or value.strip() != value



def resolve_link_base(review_pack_path: Path, manifest_path: Path | None) -> Path:
    if manifest_path is not None:
        return manifest_path.parent
    if review_pack_path.parent.name == "review-pack":
        return review_pack_path.parent.parent
    return review_pack_path.parent


def link_exists(base: Path, value) -> bool:
    if not isinstance(value, str) or not value or URL_RE.match(value) or ASSET_REF_RE.match(value):
        return True
    return (base / value).exists()


def check_review_pack_links(rp: dict, base: Path, errors: list[str]) -> None:
    target = rp.get("review_target")
    if isinstance(target, dict):
        for key in ["agent_view", "human_view"]:
            value = target.get(key)
            if value and not link_exists(base, value):
                errors.append(f"review_target.{key} does not exist: {value}")
    for idx, item in enumerate(rp.get("linked_agent_artifacts") or []):
        if not isinstance(item, dict):
            continue
        value = item.get("path")
        if value and not link_exists(base, value):
            errors.append(f"linked_agent_artifacts[{idx}].path does not exist: {value}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("review_pack")
    ap.add_argument("--manifest")
    ap.add_argument("--kind", required=True, choices=["hilp", "hile"])
    ap.add_argument("--check-links", action="store_true")
    ap.add_argument("--check-command", action="store_true")
    args = ap.parse_args()
    errors = []
    try:
        rp = load_pack(Path(args.review_pack))
    except Exception as exc:
        print(f"INVALID review-pack parse: {exc}")
        sys.exit(1)

    decision = rp.get("decision_required")
    if decision not in ALLOWED[args.kind]:
        errors.append(f"decision_required invalid for {args.kind}: {decision}")
    if rp.get("lifecycle_state") not in {"open", "closed"}:
        errors.append("lifecycle_state must be open|closed")
    target = rp.get("review_target")
    if not isinstance(target, dict):
        errors.append("review_target mapping required")
    else:
        ref = target.get("asset_ref") or target.get("artifact_ref")
        if not ref:
            errors.append("review_target.asset_ref or artifact_ref required")
        for key in ["agent_view", "human_view"]:
            if key not in target:
                errors.append(f"review_target.{key} required")
            elif unsafe_path(target.get(key)):
                errors.append(f"review_target.{key} unsafe: {target.get(key)}")
    if not rp.get("human_summary"):
        errors.append("human_summary required")
    if not isinstance(rp.get("linked_agent_artifacts"), list):
        errors.append("linked_agent_artifacts must be a list")
    if not isinstance(rp.get("decision_record"), dict):
        errors.append("decision_record mapping required")
    else:
        status = rp["decision_record"].get("status")
        if not status:
            errors.append("decision_record.status required")
        if rp.get("lifecycle_state") == "closed" and status not in CLOSED:
            errors.append("closed review-pack requires final decision_record.status")
    if args.check_command:
        cmd = rp.get("required_command")
        if cmd not in {None, "none"}:
            if not isinstance(cmd, str) or "<" in cmd or ">" in cmd:
                errors.append("required_command must be concrete; templates with <...> are not allowed in generated review-packs")
            if "@vN" in str(cmd):
                errors.append("required_command must use a concrete @v number")
        rule = COMMAND_RULES.get((args.kind, decision))
        if rule:
            if not isinstance(cmd, str) or not rule.match(cmd):
                errors.append(f"required_command does not match decision_required={decision}")
            elif isinstance(target, dict):
                target_ref = target.get("asset_ref") or target.get("artifact_ref")
                agent_view = target.get("agent_view")
                if args.kind == "hilp":
                    m = HILP_COMMAND_TARGET_RE.search(cmd)
                    if m and target_ref and m.group(1) != target_ref:
                        errors.append("required_command target asset does not match review_target")
                else:
                    m = HILE_COMMAND_TARGET_RE.match(cmd)
                    if m and agent_view and m.group(1) != agent_view:
                        errors.append("required_command path does not match review_target.agent_view")
        elif (args.kind, decision) in NO_COMMAND_DECISIONS:
            if cmd not in {None, "none"}:
                # Failure forensics may optionally point humans to an explicit HILP reapproval command.
                if not (args.kind == "hile" and decision == "failure_forensics_review" and re.match(r"^批准重审：(批准|重做设计|重做蓝图|重做交接|阻断执行|维持原批准) phase-04/reapproval@v[0-9]+$", str(cmd))):
                    errors.append(f"decision_required={decision} must not require an execution/approval command")
    manifest_path_for_links = Path(args.manifest) if args.manifest else None
    if args.manifest:
        try:
            refs = registry_refs(load_manifest(Path(args.manifest)))
            if isinstance(target, dict):
                ref = target.get("asset_ref") or target.get("artifact_ref")
                if ref and ref not in refs:
                    errors.append(f"review_target {ref} not found in manifest asset_registry")
        except Exception as exc:
            errors.append(f"manifest validation failed: {exc}")
    if args.check_links:
        base = resolve_link_base(Path(args.review_pack), manifest_path_for_links)
        check_review_pack_links(rp, base, errors)
    if errors:
        print("REVIEW_PACK_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print("review-pack ok")


if __name__ == "__main__":
    main()
