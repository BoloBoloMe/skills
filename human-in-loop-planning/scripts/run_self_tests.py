#!/usr/bin/env python3
"""Run bundled self-tests, including positive and negative fixtures.

The runner executes validator scripts in-process with runpy to avoid flaky
subprocess behavior in constrained execution environments. CI should still wrap
this whole script with an outer timeout.
"""
import os
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, expect_ok=True):
    print("$ " + " ".join(args), flush=True)
    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT)
        sys.argv = args[:]
        try:
            runpy.run_path(str(ROOT / args[0]), run_name="__main__")
            code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
    if expect_ok and code != 0:
        raise SystemExit(code)
    if not expect_ok and code == 0:
        print("expected failure but command succeeded")
        raise SystemExit(1)

run(["scripts/validate_yaml_blocks.py", str(ROOT), "--shape"])
run(["scripts/check_links_and_state.py", str(ROOT)])
run(["scripts/validate_protocol_consistency.py", str(ROOT)])
run(["scripts/validate_examples.py", str(ROOT)])
run(["scripts/validate_manifest.py", "tests/fixtures/valid/strict-manifest.md"])
run(["scripts/validate_manifest.py", "tests/fixtures/valid/reapproval-manifest.md"])
run(["scripts/validate_manifest.py", "tests/fixtures/valid/e2e/planning-manifest.md"])
run(["scripts/validate_manifest.py", "tests/fixtures/invalid/pointer-artifact-mismatch.md"], expect_ok=False)
run(["scripts/validate_manifest.py", "tests/fixtures/invalid/strict-missing-audit-trail.md"], expect_ok=False)
run(["scripts/validate_manifest.py", "tests/fixtures/invalid/reapproval-missing-log.md"], expect_ok=False)
run(["scripts/validate_manifest.py", "tests/fixtures/invalid/approved-working-asset.md"], expect_ok=False)
run(["scripts/validate_manifest.py", "tests/fixtures/invalid/design-owner-mismatch.md"], expect_ok=False)
run(["scripts/validate_manifest.py", "tests/fixtures/invalid/persisted-preflight-mode.md"], expect_ok=False)
run(["scripts/validate_documented_commands.py", str(ROOT)])
run(["scripts/validate_transcript_semantics.py", str(ROOT)])

with tempfile.TemporaryDirectory() as td:
    run(["scripts/init_change_package.py", "safe-demo", "--root", td, "--mode", "standard"])
    run(["scripts/init_change_package.py", "../escaped", "--root", td, "--mode", "standard"], expect_ok=False)
with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    manifest_path = base / "manifest.md"
    manifest_path.write_text((ROOT / "tests/fixtures/valid/strict-manifest.md").read_text(encoding="utf-8"), encoding="utf-8")
    for rel in ["agent/02-design-choice.yaml.md", "human/03-design-summary.md"]:
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n", encoding="utf-8")
    review_pack = base / "review-pack/design-review.md"
    review_pack.parent.mkdir(parents=True, exist_ok=True)
    review_pack.write_text("""# Design Review

```yaml
review_pack:
  review_pack_ref: review-pack/design-review.md
  review_target:
    asset_ref: phase-02/design-choice@v1
    agent_view: agent/02-design-choice.yaml.md
    human_view: human/03-design-summary.md
  decision_required: design_approval
  lifecycle_state: open
  generated_from_manifest_version: 1
  human_summary: Review the design decision.
  scope:
    in_scope: []
    out_of_scope: []
  risk_review:
    known_risks: []
    irreversible_or_high_risk_items: []
    mitigations: []
  verification_expectations: []
  blocking_questions: []
  required_command: 批准设计：批准 phase-02/design-choice@v1
  linked_agent_artifacts:
    - path: agent/02-design-choice.yaml.md
      purpose: design contract
  audit_evidence:
    audit_trail_path: audit/audit-trail.md
    latest_entry_ref: null
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
""", encoding="utf-8")
    run(["scripts/validate_review_pack.py", str(review_pack), "--manifest", str(manifest_path), "--kind", "hilp", "--check-links", "--check-command"])
    (base / "human/03-design-summary.md").unlink()
    run(["scripts/validate_review_pack.py", str(review_pack), "--manifest", str(manifest_path), "--kind", "hilp", "--check-links", "--check-command"], expect_ok=False)
    (base / "human/03-design-summary.md").write_text("ok\n", encoding="utf-8")
    review_pack.write_text(review_pack.read_text(encoding="utf-8").replace("批准设计：批准 phase-02/design-choice@v1", "确认执行：确认执行 Plan agent/03-plan.yaml.md"), encoding="utf-8")
    run(["scripts/validate_review_pack.py", str(review_pack), "--manifest", str(manifest_path), "--kind", "hilp", "--check-links", "--check-command"], expect_ok=False)
with tempfile.TemporaryDirectory() as td:
    duplicate_doc = Path(td) / "duplicate-command.md"
    duplicate_doc.write_text(
        "`scripts/check_allowed_files.py --handoff a.md --handoff b.md --workspace .`\n",
        encoding="utf-8",
    )
    run(["scripts/validate_documented_commands.py", td], expect_ok=False)
with tempfile.TemporaryDirectory() as td:
    duplicate_yaml = Path(td) / "duplicate-yaml-key.md"
    duplicate_yaml.write_text("""```yaml
item:
  objective: one
  objective: two
```
""", encoding="utf-8")
    run(["scripts/validate_yaml_blocks.py", td, "--shape"], expect_ok=False)
with tempfile.TemporaryDirectory() as td:
    missing_doc = Path(td) / "missing-check-paths.md"
    missing_doc.write_text(
        "`scripts/validate_manifest.py planning/manifest.md`\n",
        encoding="utf-8",
    )
    run(["scripts/validate_documented_commands.py", td], expect_ok=False)

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    manifest_text = (ROOT / "tests/fixtures/valid/strict-manifest.md").read_text(encoding="utf-8")
    manifest_path = base / "manifest.md"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    for rel in [
        "audit/audit-trail.md",
        "agent/00-directory.md",
        "agent/01-requirements-facts.yaml.md",
        "agent/02-design-choice.yaml.md",
        "agent/03-implementation-blueprint.yaml.md",
        "agent/05-execution-handoff.yaml.md",
        "human/03-requirements-summary.md",
        "human/03-design-summary.md",
        "human/04-blueprint-summary.md",
        "human/04-handoff-summary.md",
        "review-pack/handoff-review.md",
    ]:
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n", encoding="utf-8")
    run(["scripts/validate_manifest.py", str(manifest_path), "--check-paths"])
    (base / "human/04-handoff-summary.md").unlink()
    run(["scripts/validate_manifest.py", str(manifest_path), "--check-paths"], expect_ok=False)

with tempfile.TemporaryDirectory() as td:
    ok = Path(td) / "formal-review.md"
    ok.write_text("批准设计：批准 phase-02/design-choice@v3\n", encoding="utf-8")
    run(["scripts/validate_placeholders.py", td])
    bad = Path(td) / "formal-review.md"
    bad.write_text("Use <planned-files.txt> and approve @vN later.\n", encoding="utf-8")
    run(["scripts/validate_placeholders.py", td], expect_ok=False)

# Content-level validation for HILP planning assets.
run(["scripts/validate_hilp_assets.py", "tests/fixtures/valid/assets", "--manifest", "tests/fixtures/valid/assets/planning-manifest-with-complete-assets.md"])
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/valid/assets/complete-design-choice.md", "--kind", "design-choice"])
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/valid/assets/complete-implementation-blueprint.md", "--kind", "implementation-blueprint"])
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/valid/assets/complete-execution-handoff.md", "--kind", "execution-handoff"])
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/design-no-alternatives.md", "--kind", "design-choice"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/design-recommended-option-not-in-alternatives.md", "--kind", "design-choice"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/blueprint-empty-execution-units.md", "--kind", "implementation-blueprint"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/blueprint-unit-missing-verification.md", "--kind", "implementation-blueprint"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/blueprint-unit-allowed-outside-top.md", "--kind", "implementation-blueprint"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", "tests/fixtures/invalid/assets/handoff-source-blueprint-mismatch", "--manifest", "tests/fixtures/invalid/assets/handoff-source-blueprint-mismatch/planning-manifest-with-complete-assets.md"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", "tests/fixtures/invalid/assets/handoff-unit-not-in-blueprint", "--manifest", "tests/fixtures/invalid/assets/handoff-unit-not-in-blueprint/planning-manifest-with-complete-assets.md"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/handoff-missing-hile-planning-requirement.md", "--kind", "execution-handoff"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", ".", "--asset", "tests/fixtures/invalid/assets/handoff-empty-verification-contract.md", "--kind", "execution-handoff"], expect_ok=False)
run(["scripts/validate_hilp_assets.py", "tests/fixtures/invalid/assets/handoff-allowed-files-wider-than-blueprint", "--manifest", "tests/fixtures/invalid/assets/handoff-allowed-files-wider-than-blueprint/planning-manifest-with-complete-assets.md"], expect_ok=False)

print("self-tests ok")
