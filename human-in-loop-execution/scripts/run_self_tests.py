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
import shutil
import subprocess
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
run(["scripts/validate_documented_commands.py", str(ROOT)])
run(["scripts/validate_transcript_semantics.py", str(ROOT)])

with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "docs/changes"
    planning = root / "safe-demo/planning/manifest.md"
    planning.parent.mkdir(parents=True, exist_ok=True)
    planning.write_text("# Planning Manifest\n\n```yaml\nmanifest:\n  schema_version: \"2.24.0\"\n  protocol_version: \"2.24.0\"\n  change_slug: safe-demo\n  protocol: HILP\n  mode: standard\n  current_assets: {}\n  asset_registry: []\n  current_pointers: {}\n  last_updated_at: '2026-05-04T00:00:00Z'\n```\n", encoding="utf-8")
    run(["scripts/init_execution_package.py", "safe-demo", "--root", str(root), "--source-handoff", "phase-05/execution-handoff@v1", "--planning-manifest", str(planning), "--tier", "standard"])
    run(["scripts/init_execution_package.py", "../escaped", "--root", str(root), "--source-handoff", "phase-05/execution-handoff@v1", "--planning-manifest", str(planning), "--tier", "standard"], expect_ok=False)
with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    manifest_path = base / "manifest.md"
    manifest_path.write_text((ROOT / "tests/fixtures/valid/completed-execution-manifest.md").read_text(encoding="utf-8"), encoding="utf-8")
    for rel in ["agent/03-plan.yaml.md", "human/03-plan.md"]:
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n", encoding="utf-8")
    review_pack = base / "review-pack/plan-confirmation.md"
    review_pack.parent.mkdir(parents=True, exist_ok=True)
    review_pack.write_text("""# Plan Confirmation

```yaml
review_pack:
  review_pack_ref: review-pack/plan-confirmation.md
  review_target:
    artifact_ref: hile/plan@v1
    agent_view: agent/03-plan.yaml.md
    human_view: human/03-plan.md
  decision_required: plan_confirmation
  lifecycle_state: open
  source_handoff_ref: phase-05/execution-handoff@v1
  tier: standard
  human_summary: Confirm the execution plan.
  scope:
    allowed_changes: []
    forbidden_changes: []
  pre_modify_check_summary:
    within_scope: pass
    target_files_allowed: pass
    dependencies_ready: pass
    stop_conditions_known: pass
    verification_available: pass
  verification_expectations: []
  required_command: 确认执行：确认执行 Plan agent/03-plan.yaml.md
  blocking_questions: []
  linked_agent_artifacts:
    - path: agent/03-plan.yaml.md
      purpose: plan contract
  decision_record:
    status: pending
    decided_by: null
    decided_at: null
    command_used: null
```
""", encoding="utf-8")
    run(["scripts/validate_review_pack.py", str(review_pack), "--manifest", str(manifest_path), "--kind", "hile", "--check-links", "--check-command"])
    (base / "human/03-plan.md").unlink()
    run(["scripts/validate_review_pack.py", str(review_pack), "--manifest", str(manifest_path), "--kind", "hile", "--check-links", "--check-command"], expect_ok=False)
    (base / "human/03-plan.md").write_text("ok\n", encoding="utf-8")
    review_pack.write_text(review_pack.read_text(encoding="utf-8").replace("确认执行：确认执行 Plan agent/03-plan.yaml.md", "批准设计：批准 phase-02/design-choice@v1"), encoding="utf-8")
    run(["scripts/validate_review_pack.py", str(review_pack), "--manifest", str(manifest_path), "--kind", "hile", "--check-links", "--check-command"], expect_ok=False)
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
    missing_doc = Path(td) / "missing-workspace.md"
    missing_doc.write_text(
        "`scripts/check_allowed_files.py --handoff a.md --planned-file planned.txt`\n",
        encoding="utf-8",
    )
    run(["scripts/validate_documented_commands.py", td], expect_ok=False)
run(["scripts/validate_plan_or_runbook.py", "tests/fixtures/valid/repo-aware-plan.md", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--execution-manifest", "tests/fixtures/valid/completed-execution-manifest.md", "--workspace", "."])
run(["scripts/validate_plan_or_runbook.py", "tests/fixtures/valid/repo-aware-runbook.md", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--execution-manifest", "tests/fixtures/valid/strict-runbook-manifest.md", "--workspace", "."])
run(["scripts/validate_plan_or_runbook.py", "tests/fixtures/invalid/thin-plan-missing-repo-observations.md", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--execution-manifest", "tests/fixtures/valid/completed-execution-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_plan_or_runbook.py", "tests/fixtures/invalid/plan-planned-files-out-of-scope.md", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--execution-manifest", "tests/fixtures/valid/completed-execution-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_plan_or_runbook.py", "tests/fixtures/invalid/plan-placeholder-confirmation.md", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--execution-manifest", "tests/fixtures/valid/completed-execution-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/valid/completed-execution-manifest.md"])
run(["scripts/validate_execution_manifest.py", "tests/fixtures/invalid/standard-confirmed-with-unconfirmed-plan.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/invalid/initialized-with-completed-assets.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/invalid/completed-without-plan.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/invalid/completed-with-draft-latest-plan.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/invalid/current-plan-role-mismatch.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/invalid/source-handoff-ref-mismatch.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/valid/e2e/completed-execution-manifest.md", "--planning-manifest", "tests/fixtures/invalid/planning-manifest-wrong-handoff-owner.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/valid/e2e/completed-execution-manifest.md", "--planning-manifest", "tests/fixtures/invalid/malformed-hilp-planning-manifest.md"], expect_ok=False)
run(["scripts/validate_execution_manifest.py", "tests/fixtures/valid/tiny-inline-completed-manifest.md"])
run(["scripts/run_fake_repo_e2e.py"])
run(["scripts/validate_handoff_intake.py", "tests/fixtures/valid/e2e/execution-handoff.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."])
partial = subprocess.run([sys.executable, "scripts/validate_handoff_intake.py", "tests/fixtures/valid/e2e/execution-handoff.md", "--workspace", ".", "--allow-partial"], cwd=ROOT, text=True, capture_output=True)
if partial.returncode != 0 or "HANDOFF_INTAKE_PARTIAL" not in partial.stdout or "handoff intake ok" in partial.stdout:
    print(partial.stdout)
    print(partial.stderr)
    raise SystemExit("partial intake output must be clearly partial and must not say handoff intake ok")
run(["scripts/validate_handoff_intake.py", "tests/fixtures/invalid/no-execution-units.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_handoff_intake.py", "tests/fixtures/invalid/unit-without-allowed-files.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_handoff_intake.py", "tests/fixtures/invalid/unit-allowed-outside-top.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_handoff_intake.py", "tests/fixtures/invalid/old-schema-handoff.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_handoff_intake.py", "tests/fixtures/valid/e2e/execution-handoff.md", "--planning-manifest", "tests/fixtures/invalid/malformed-hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_handoff_intake.py", "tests/fixtures/invalid/unsafe-allowed-files-handoff.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/validate_handoff_intake.py", "tests/fixtures/invalid/missing-hile-planning-requirement.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md", "--workspace", "."], expect_ok=False)
run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--planned-file", "tests/fixtures/valid/e2e/planned-files.txt", "--workspace", "."])
run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/canonical-execution-handoff-wrapper.md", "--planned-file", "tests/fixtures/valid/planned-files.txt", "--workspace", ".", "--unit-id", "EU-001"])
run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/canonical-execution-handoff-wrapper.md", "--planned-file", "tests/fixtures/invalid/unit-planned-files-out-of-scope.txt", "--workspace", ".", "--unit-id", "EU-001"], expect_ok=False)
run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--changed-file", "tests/fixtures/valid/e2e/changed-files.txt", "--workspace", "."])
run(["scripts/validate_execution_manifest.py", "tests/fixtures/valid/e2e/completed-execution-manifest.md", "--planning-manifest", "tests/fixtures/valid/e2e/hilp-planning-manifest.md"])


with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "docs/changes"
    planning = root / "init-demo/planning/manifest.md"
    planning.parent.mkdir(parents=True, exist_ok=True)
    planning.write_text("# Planning Manifest\n\n```yaml\nmanifest:\n  schema_version: \"2.24.0\"\n  protocol_version: \"2.24.0\"\n  change_slug: init-demo\n  protocol: HILP\n  mode: standard\n  current_assets: {}\n  asset_registry: []\n  current_pointers: {}\n  last_updated_at: '2026-05-04T00:00:00Z'\n```\n", encoding="utf-8")
    run(["scripts/init_execution_package.py", "init-demo", "--root", str(root), "--source-handoff", "phase-05/execution-handoff@v1", "--planning-manifest", str(planning), "--tier", "standard"])
    manifest = root / "init-demo/execution/manifest.md"
    run(["scripts/validate_execution_manifest.py", str(manifest), "--check-paths"])

# Fake repo e2e smoke: real file modification -> git diff -> HILE scope gate.
if shutil.which("git"):
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "src").mkdir()
        (repo / "tests").mkdir()
        (repo / "src" / "e2e.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        (repo / "tests" / "e2e_test.py").write_text("from src.e2e import value\n\ndef test_value():\n    assert value() == 2\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "e2e@example.test"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "HILE E2E"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        planned = repo / "planned-files.txt"
        planned.write_text("src/e2e.py\ntests/e2e_test.py\n", encoding="utf-8")
        run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--planned-file", str(planned), "--workspace", str(repo)])
        (repo / "src" / "e2e.py").write_text("def value():\n    return 2\n", encoding="utf-8")
        diff = subprocess.check_output(["git", "diff", "--name-only"], cwd=repo, text=True)
        changed = repo / "changed-files.txt"
        changed.write_text(diff, encoding="utf-8")
        run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/e2e/execution-handoff.md", "--changed-file", str(changed), "--workspace", str(repo)])
run(["scripts/check_allowed_files.py", "--handoff", "tests/fixtures/valid/canonical-execution-handoff-wrapper.md", "--planned-file", "tests/fixtures/valid/planned-files.txt", "--workspace", "."])
run(["scripts/check_allowed_files.py", "--allowed-file", "tests/fixtures/valid/allow-all-files.txt", "--changed-file", "tests/fixtures/invalid/changed-files-parent-traversal.txt", "--workspace", "."], expect_ok=False)
run(["scripts/check_allowed_files.py", "--allowed-file", "tests/fixtures/valid/allow-all-files.txt", "--changed-file", "tests/fixtures/invalid/changed-files-absolute.txt", "--workspace", "."], expect_ok=False)

run(["scripts/check_allowed_files.py", "--allowed-file", "tests/fixtures/valid/one-level-src-allow.txt", "--changed-file", "tests/fixtures/valid/src-direct-file.txt", "--workspace", "."])
run(["scripts/check_allowed_files.py", "--allowed-file", "tests/fixtures/valid/one-level-src-allow.txt", "--changed-file", "tests/fixtures/valid/src-nested-file.txt", "--workspace", "."], expect_ok=False)
run(["scripts/check_allowed_files.py", "--allowed-file", "tests/fixtures/valid/recursive-src-allow.txt", "--changed-file", "tests/fixtures/valid/src-nested-file.txt", "--workspace", "."])

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    manifest_text = (ROOT / "tests/fixtures/valid/completed-execution-manifest.md").read_text(encoding="utf-8")
    manifest_path = base / "manifest.md"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    for rel in [
        "../planning/manifest.md",
        "agent/00-directory.md",
        "agent/01-intake.yaml.md",
        "agent/03-plan.yaml.md",
        "agent/07-verification-evidence.yaml.md",
        "agent/08-completion-review.yaml.md",
        "human/01-intake.md",
        "human/03-plan.md",
        "human/05-completion-review.md",
        "human/07-verification-evidence.md",
        "human/08-completion-review.md",
    ]:
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n", encoding="utf-8")
    run(["scripts/validate_execution_manifest.py", str(manifest_path), "--check-paths"])
    (base / "human/08-completion-review.md").unlink()
    run(["scripts/validate_execution_manifest.py", str(manifest_path), "--check-paths"], expect_ok=False)

with tempfile.TemporaryDirectory() as td:
    ok = Path(td) / "formal-review.md"
    ok.write_text("确认执行：确认执行 Plan agent/03-plan.yaml.md\n", encoding="utf-8")
    run(["scripts/validate_placeholders.py", td])
    bad = Path(td) / "formal-review.md"
    bad.write_text("Use <actual-changed-files.txt> and <execution-manifest.md>.\n", encoding="utf-8")
    run(["scripts/validate_placeholders.py", td], expect_ok=False)

with tempfile.TemporaryDirectory() as td:
    bad_root = Path(td) / "human-in-loop-execution"
    (bad_root / "references/shared").mkdir(parents=True, exist_ok=True)
    (bad_root / "references/agent").mkdir(parents=True, exist_ok=True)
    (bad_root / "references/shared/compatibility-contract.yaml").write_text(
        'schema_version: "2.24.0"\nhilp_version: "2.24.0"\nhile_version: "2.24.1"\nproducer_skill: human-in-loop-planning\nconsumer_skill: human-in-loop-execution\n',
        encoding="utf-8",
    )
    (bad_root / "references/agent/02-execution-tiers.md").write_text(
        '# tiers\n\n```yaml\nstandard:\n  confirmation_required: true\n  require_confirmation_when:\n    - always_before_file_modification\n```\n\npartial\n',
        encoding="utf-8",
    )
    (bad_root / "references/agent/03-routing.md").write_text(
        '# routing\n\n```yaml\nstandard_confirmation_resolution:\n  no' + '_confirmation_required:\n    route: tier_standard' + '_and_confirmation_not_required\n    allowed_action: execute_plan_with_tdd_and_verification\n```\n',
        encoding="utf-8",
    )
    run(["scripts/validate_protocol_consistency.py", str(bad_root)], expect_ok=False)

print("self-tests ok")
