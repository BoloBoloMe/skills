#!/usr/bin/env python3
"""Run HITL MVP self tests with generated flat-layout fixtures."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT))
from hitl_common import dump_yaml, load_manifest, load_yaml_document, refresh_human_view, registry_item_by_ref, sha256_file, write_manifest  # noqa: E402

MANIFEST_NAME = "manifest.yaml"


def run(cmd: list[str], cwd: Path | None = None, ok: bool = True, stdin: str | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run([sys.executable, *cmd], cwd=cwd, input=stdin, text=True, capture_output=True)
    if ok and result.returncode != 0:
        raise AssertionError(f"command failed: {cmd}\nSTDOUT:{result.stdout}\nSTDERR:{result.stderr}")
    if not ok and result.returncode == 0:
        raise AssertionError(f"command unexpectedly passed: {cmd}\n{result.stdout}")
    return result


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_NAME


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_asset(root: Path, ref: str, artifact: str, state: str, role: str, data: dict, replace: bool = False) -> None:
    """Fixture helper: exercise the canonical write_agent_asset.py API."""
    cmd = [str(SCRIPT / "write_agent_asset.py"), "--manifest", str(manifest_path(root)), "--asset-ref", ref, "--artifact", artifact, "--state", state, "--role", role, "--stdin"]
    if replace:
        cmd.append("--replace-draft")
    run(cmd, stdin=dump_yaml(data) + "\n")


def close_gate(manifest: dict, name: str, target: str) -> None:
    """Mark a gate closed in fixtures after prerequisite evidence exists."""
    items = [
        {
            "question": "fixture branch resolved?",
            "resolution_type": "evidence-closed",
            "resolution": "self-test fixture closes this branch",
            "evidence": ["self-test fixture evidence"],
        }
    ]
    if name == "pre_execution_plan":
        items = [
            {
                "resolution_id": "PEP-EU-001-S01-R001",
                "unit_id": "EU-001",
                "step_id": "EU-001-S01",
                "dependency_path": ["EU-001"],
                "question": "EU-001-S01 source-level change intent?",
                "resolution_type": "evidence-closed",
                "resolution": "self-test fixture closes source-level intent for src/a.py",
                "evidence": ["self-test fixture evidence"],
            }
        ]
    manifest["interrogation_gates"][name] = {
        "status": "closed",
        "target_asset": target,
        "blocking_unknowns": [],
        "evidence": ["self-test fixture evidence"],
        "resolution_items": items,
        "closure_command": f"关闭盘问: {name} {target}",
        "closed_at": "2026-05-20T00:00:00Z",
    }


def planning_assets() -> tuple[dict, dict, dict]:
    facts = {
        "asset_ref": "planning/facts@v1", "artifact": "facts", "schema_version": "0.0.1",
        "goals": ["deliver MVP"], "scope": ["skill files"], "non_scope": ["legacy migration"],
        "verified_facts": [{"fact": "single manifest", "source": "requirements"}], "assumptions": [], "unknowns": [],
        "acceptance": ["self tests pass"], "verification_strategy": ["run self tests"],
    }
    design = {
        "asset_ref": "planning/design@v1", "artifact": "design", "schema_version": "0.0.1",
        "candidates": [{"option": "single skill", "complexity": "medium", "code_volume": "medium", "impact_scope": "skill repo", "risk": "controlled", "testing_effort": "self tests"}],
        "recommended_option": "single skill", "rationale": "matches HITL 0.0.1", "rejected_options": ["dual protocol"], "risks": ["MVP coverage"],
    }
    blueprint = {
        "asset_ref": "planning/blueprint@v1", "artifact": "blueprint", "schema_version": "0.0.1", "source_design_ref": "planning/design@v1",
        "implementation_units": [{"unit_id": "EU-001", "objective": "write files", "implementation_intent": ["create HITL MVP"], "dependencies": [], "implementation_step_outline": [{"step_id": "EU-001-S01", "title": "edit source file", "expected_files": ["src/a.py"], "intent_seed": "change src/a.py"}], "allowed_files": ["src/**"], "prohibited_files": []}],
        "execution_contract": {"allowed_files": ["src/**", "README.md"], "prohibited_files": ["secrets/**"], "prohibited_scope": ["production secrets"], "verification_contract": {"must_haves": ["tests pass"], "test_commands": ["pytest"], "manual_checks": []}, "stop_conditions": ["scope drift"], "planning_requirement": {"repo_aware_plan_or_runbook_required": True}},
    }
    return facts, design, blueprint


def create_package(base: Path, tier: str = "standard") -> tuple[Path, dict]:
    run([str(SCRIPT / "init_hitl_package.py"), "测试变更", "--root", str(base), "--tier", tier])
    root = base / "测试变更"
    assert manifest_path(root).exists()
    assert not (root / "human-view.html").exists()
    facts, design, blueprint = planning_assets()
    write_asset(root, "planning/facts@v1", "facts", "completed", "content-asset", facts)
    assert (root / "human-view.html").exists()
    assert load_manifest(manifest_path(root))["current_pointers"]["active_human_view"] == "human-view@current"
    manifest = load_manifest(manifest_path(root))
    close_gate(manifest, "pre_design", "planning/design@v1")
    close_gate(manifest, "pre_blueprint", "planning/blueprint@v1")
    write_manifest(manifest_path(root), manifest)
    planning_role = "approval-target" if tier == "strict" else "content-asset"
    planning_state = "approved" if tier == "strict" else "completed"
    write_asset(root, "planning/design@v1", "design", planning_state, planning_role, design)
    write_asset(root, "planning/blueprint@v1", "blueprint", planning_state, planning_role, blueprint)
    manifest = load_manifest(manifest_path(root))
    refs = []
    for ref in ["planning/facts@v1", "planning/design@v1", "planning/blueprint@v1"]:
        item = registry_item_by_ref(manifest, ref)
        refs.append({"asset_ref": ref, "path": item["path"], "sha256": item["sha256"]})
    package_state = "completed" if tier == "strict" else "ready-for-approval"
    package_role = "content-asset" if tier == "strict" else "approval-target"
    package = {
        "asset_ref": "planning/implementation-package@v1", "artifact": "implementation-package", "schema_version": "0.0.1",
        "references": refs,
        "summary": "MVP package", "approval_scope": "approve package", "risk_summary": "low", "verification_summary": "self tests", "authorized_assets": ["planning/facts@v1", "planning/design@v1", "planning/blueprint@v1"],
    }
    write_asset(root, "planning/implementation-package@v1", "implementation-package", package_state, package_role, package)
    manifest = load_manifest(manifest_path(root))
    manifest["workflow"]["current_stage"] = "implementation-package"
    manifest["workflow"]["status"] = package_state
    manifest["current_pointers"]["active_agent_asset"] = "planning/implementation-package@v1"
    write_manifest(manifest_path(root), manifest)
    refresh_human_view(manifest_path(root))
    return root, package


def approve(root: Path) -> None:
    manifest = load_manifest(manifest_path(root))
    item = registry_item_by_ref(manifest, "planning/implementation-package@v1")
    item["lifecycle_state"] = "approved"
    manifest["current_pointers"]["latest_approval_target"] = "planning/implementation-package@v1"
    manifest["decision_log"].append({"decision_type": "approval", "command_used": "批准方案: planning/implementation-package@v1", "target_asset": "planning/implementation-package@v1", "authorized_assets": ["planning/facts@v1", "planning/design@v1", "planning/blueprint@v1"], "decided_by": "human", "decided_at": "2026-05-20T00:00:00Z"})
    write_manifest(manifest_path(root), manifest)


def write_resolution_file(path: Path, gate: str = "pre_design") -> None:
    """Self-test helper: materialize structured gate closure evidence."""
    if gate == "pre_execution_plan":
        data = {"evidence": ["self-test execution gate evidence"], "resolution_items": [{"resolution_id": "PEP-EU-001-S01-R001", "unit_id": "EU-001", "step_id": "EU-001-S01", "dependency_path": ["EU-001"], "question": "EU-001-S01 source-level change intent?", "resolution_type": "evidence-closed", "resolution": "self-test closes source-level intent for src/a.py", "evidence": ["self-test execution evidence"]}]}
    else:
        data = {"evidence": ["self-test gate evidence"], "resolution_items": [{"question": "fixture branch resolved?", "resolution_type": "evidence-closed", "resolution": "self-test fixture closes this branch", "evidence": ["self-test fixture evidence"]}]}
    write_text_file(path, dump_yaml(data) + "\n")


def transition_close_gate(root: Path, gate: str, target: str, resolution: Path) -> None:
    """Exercise transition_manifest.py close-gate in fixtures."""
    run([str(SCRIPT / "transition_manifest.py"), "close-gate", "--manifest", str(manifest_path(root)), "--gate", gate, "--target", target, "--command", f"关闭盘问: {gate} {target}", "--resolution-file", str(resolution)])


def transition_record(root: Path, decision_type: str, asset_ref: str, command: str, ok: bool = True) -> None:
    """Exercise transition_manifest.py record-decision in fixtures."""
    run([str(SCRIPT / "transition_manifest.py"), "record-decision", "--manifest", str(manifest_path(root)), "--decision-type", decision_type, "--asset-ref", asset_ref, "--command", command], ok=ok)


def archive_asset_check(root: Path, ok: bool = True) -> None:
    """Self-test helper: archive the current asset-check before recording a new one."""
    ref = (load_manifest(manifest_path(root)).get("current_pointers") or {}).get("latest_asset_check")
    if ref:
        run([str(SCRIPT / "archive_asset.py"), "--manifest", str(manifest_path(root)), "--asset-ref", str(ref), "--state", "superseded"], ok=ok)


def record_preapproval_check(root: Path, target_ref: str = "planning/implementation-package@v1", record_ref: str = "checks/asset-check@v1", ok: bool = True) -> None:
    """Record the pre-approval asset-check required by approval transitions."""
    run([str(SCRIPT / "validate_asset_check.py"), "--pre-approval", "--manifest", str(manifest_path(root)), "--target-ref", target_ref, "--record-ref", record_ref], ok=ok)


def record_final_check(root: Path, target_ref: str = "planning/implementation-package@v1", record_ref: str = "checks/asset-check@v2", ok: bool = True) -> None:
    """Record the final asset-check required before Plan/Runbook scaffold."""
    run([str(SCRIPT / "validate_asset_check.py"), "--manifest", str(manifest_path(root)), "--target-ref", target_ref, "--workspace", str(root), "--record-ref", record_ref], ok=ok)


def test_golden(tmp: Path) -> None:
    root, _ = create_package(tmp)
    run([str(SCRIPT / "validate_manifest.py"), str(manifest_path(root)), "--check-paths"])
    run([str(SCRIPT / "validate_planning_assets.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/facts@v1", "--asset-ref", "planning/design@v1", "--asset-ref", "planning/blueprint@v1", "--asset-ref", "planning/implementation-package@v1"])
    run([str(SCRIPT / "transform_human_view.py"), "--manifest", str(manifest_path(root))])
    run([str(SCRIPT / "transform_human_view.py"), "--manifest", str(manifest_path(root)), "--check"])
    run([str(SCRIPT / "validate_asset_check.py"), "--pre-approval", "--manifest", str(manifest_path(root)), "--target-ref", "planning/implementation-package@v1"])
    approve(root)
    run([str(SCRIPT / "transform_human_view.py"), "--manifest", str(manifest_path(root))])
    run([str(SCRIPT / "validate_asset_check.py"), "--manifest", str(manifest_path(root)), "--target-ref", "planning/implementation-package@v1", "--workspace", str(root)])


def test_interrogation_gates(tmp: Path) -> None:
    run([str(SCRIPT / "init_hitl_package.py"), "门禁变更", "--root", str(tmp), "--tier", "standard"])
    root = tmp / "门禁变更"
    _, design, _ = planning_assets()
    write_asset(root, "planning/design@v1", "design", "draft", "content-asset", design)
    run([str(SCRIPT / "transition_manifest.py"), "mark-asset", "--manifest", str(manifest_path(root)), "--asset-ref", "planning/design@v1", "--state", "ready-for-approval"], ok=False)
    run([str(SCRIPT / "validate_interrogation_gate.py"), "--manifest", str(manifest_path(root)), "--gate", "pre_design", "--target", "planning/design@v1"], ok=False)
    run([str(SCRIPT / "validate_planning_assets.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/design@v1"], ok=False)
    data = load_manifest(manifest_path(root))
    close_gate(data, "pre_design", "planning/design@v1")
    write_manifest(manifest_path(root), data)
    run([str(SCRIPT / "validate_interrogation_gate.py"), "--manifest", str(manifest_path(root)), "--gate", "pre_design", "--target", "planning/design@v1"])
    run([str(SCRIPT / "transition_manifest.py"), "mark-asset", "--manifest", str(manifest_path(root)), "--asset-ref", "planning/design@v1", "--state", "ready-for-approval"])
    run([str(SCRIPT / "validate_planning_assets.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/design@v1"])


def test_failures(tmp: Path) -> None:
    root, _ = create_package(tmp / "fail")
    run([str(SCRIPT / "transform_human_view.py"), "--manifest", str(manifest_path(root))])
    design_path = root / registry_item_by_ref(load_manifest(manifest_path(root)), "planning/design@v1")["path"]
    design_path.write_text(design_path.read_text(encoding="utf-8") + "drift: yes\n", encoding="utf-8")
    run([str(SCRIPT / "validate_asset_check.py"), "--pre-approval", "--manifest", str(manifest_path(root)), "--target-ref", "planning/implementation-package@v1", "--skip-human-view-check"], ok=False)
    run([str(SCRIPT / "transform_human_view.py"), "--manifest", str(manifest_path(root)), "--check"], ok=False)


def test_allowed_files(tmp: Path) -> None:
    root, _ = create_package(tmp / "scope")
    write_text_file(root / "planned-ok.txt", "src/a.py\n")
    write_text_file(root / "planned-bad.txt", "other/a.py\n")
    run([str(SCRIPT / "check_allowed_files.py"), "--manifest", str(manifest_path(root)), "--blueprint-ref", "planning/blueprint@v1", "--planned-file", str(root / "planned-ok.txt")])
    run([str(SCRIPT / "check_allowed_files.py"), "--manifest", str(manifest_path(root)), "--blueprint-ref", "planning/blueprint@v1", "--planned-file", str(root / "planned-bad.txt")], ok=False)


def test_plan(tmp: Path) -> None:
    root, _ = create_package(tmp / "plan")
    plan = {"asset_ref": "execution/plan@v1", "artifact": "plan", "schema_version": "0.0.1", "source_implementation_package_ref": "planning/implementation-package@v1", "source_design_ref": "planning/design@v1", "source_blueprint_ref": "planning/blueprint@v1", "repo_context": {"workspace": str(root), "branch": "main", "commit": "abc"}, "summary_evaluation": {"complexity": "low", "code_volume": "small", "impact_scope": "src", "risk_level": "low", "testing_effort": "small"}, "unit_plans": [{"unit_id": "EU-001", "planned_files": ["src/a.py"], "repo_observations": ["exists"], "implementation_steps": [{"step_id": "EU-001-S01", "title": "edit source file", "action": "modify src/a.py", "planned_files": ["src/a.py"]}], "source_level_change_intent": [{"step_id": "EU-001-S01", "implementation_step": "edit source file", "intent": "change src/a.py for fixture behavior", "target_changes": [{"file": "src/a.py", "symbols": ["fixture_symbol"], "change_type": "modify", "intent": "update fixture source content", "accepted_behavior": ["fixture passes"], "rejected_behavior": ["scope drift"]}], "interrogation_refs": ["PEP-EU-001-S01-R001"]}], "verification_plan": {"commands": ["pytest"], "expected_results": ["pass"]}, "risk_checks": ["scope"], "stop_conditions": ["drift"]}], "pre_modify_gate": {"result": "pass"}, "confirmation_command": "执行计划: execution/plan@v1"}
    write_asset(root, "execution/plan@v1", "plan", "draft", "confirmation-target", plan)
    run([str(SCRIPT / "validate_plan_or_runbook.py"), "--manifest", str(manifest_path(root)), "--plan-ref", "execution/plan@v1", "--implementation-package-ref", "planning/implementation-package@v1"], ok=False)
    manifest = load_manifest(manifest_path(root))
    close_gate(manifest, "pre_execution_plan", "execution/plan@v1")
    write_manifest(manifest_path(root), manifest)
    run([str(SCRIPT / "validate_plan_or_runbook.py"), "--manifest", str(manifest_path(root)), "--plan-ref", "execution/plan@v1", "--implementation-package-ref", "planning/implementation-package@v1"])


def test_strict_asset_check(tmp: Path) -> None:
    root, _ = create_package(tmp / "strict", tier="strict")
    run([str(SCRIPT / "transform_human_view.py"), "--manifest", str(manifest_path(root))])
    run([str(SCRIPT / "validate_asset_check.py"), "--manifest", str(manifest_path(root)), "--target-ref", "planning/implementation-package@v1", "--workspace", str(root)])


def test_asset_check_negative_targets(tmp: Path) -> None:
    root, _ = create_package(tmp / "negative-target")
    manifest = load_manifest(manifest_path(root))
    registry_item_by_ref(manifest, "planning/design@v1")["lifecycle_state"] = "approved"
    write_manifest(manifest_path(root), manifest)
    run([str(SCRIPT / "validate_asset_check.py"), "--manifest", str(manifest_path(root)), "--target-ref", "planning/design@v1", "--workspace", str(root), "--skip-human-view-check"], ok=False)


def test_preapproval_rejects_invalid_content(tmp: Path) -> None:
    run([str(SCRIPT / "init_hitl_package.py"), "坏审批", "--root", str(tmp), "--tier", "strict"])
    root = tmp / "坏审批"
    bad_design = {"asset_ref": "planning/design@v1", "artifact": "design", "schema_version": "0.0.1", "candidates": []}
    write_asset(root, "planning/design@v1", "design", "draft", "approval-target", bad_design)
    manifest = load_manifest(manifest_path(root))
    close_gate(manifest, "pre_design", "planning/design@v1")
    registry_item_by_ref(manifest, "planning/design@v1")["lifecycle_state"] = "ready-for-approval"
    write_manifest(manifest_path(root), manifest)
    run([str(SCRIPT / "validate_asset_check.py"), "--pre-approval", "--manifest", str(manifest_path(root)), "--target-ref", "planning/design@v1", "--skip-human-view-check"], ok=False)


def test_write_and_archive_guards(tmp: Path) -> None:
    run([str(SCRIPT / "init_hitl_package.py"), "写入保护", "--root", str(tmp), "--tier", "standard"])
    root = tmp / "写入保护"
    facts, _, _ = planning_assets()
    write_text_file(root / "agent/facts.v1.yaml", dump_yaml(facts) + "\n")
    cmd = [str(SCRIPT / "write_agent_asset.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/facts@v1", "--artifact", "facts", "--state", "draft", "--role", "content-asset", "--stdin", "--replace-draft"]
    run(cmd, stdin=dump_yaml(facts) + "\n", ok=False)
    cmd[cmd.index("draft")] = "superseded"
    cmd.remove("--replace-draft")
    run(cmd, stdin=dump_yaml(facts) + "\n", ok=False)


def test_forbidden_asset_fields_and_check_records(tmp: Path) -> None:
    """Guard old failure: asset bodies cannot carry manifest-owned decisions."""
    run([str(SCRIPT / "init_hitl_package.py"), "禁字段", "--root", str(tmp), "--tier", "standard"])
    root = tmp / "禁字段"
    facts, _, _ = planning_assets()
    bad = dict(facts)
    bad["approval"] = {"decided_by": "agent"}
    cmd = [str(SCRIPT / "write_agent_asset.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/facts@v1", "--artifact", "facts", "--state", "completed", "--role", "content-asset", "--stdin"]
    run(cmd, stdin=dump_yaml(bad) + "\n", ok=False)

    run([str(SCRIPT / "init_hitl_package.py"), "失败检查", "--root", str(tmp), "--tier", "strict"])
    check_root = tmp / "失败检查"
    bad_design = {"asset_ref": "planning/design@v1", "artifact": "design", "schema_version": "0.0.1", "candidates": []}
    write_asset(check_root, "planning/design@v1", "design", "draft", "approval-target", bad_design)
    manifest = load_manifest(manifest_path(check_root))
    close_gate(manifest, "pre_design", "planning/design@v1")
    registry_item_by_ref(manifest, "planning/design@v1")["lifecycle_state"] = "ready-for-approval"
    write_manifest(manifest_path(check_root), manifest)
    refresh_human_view(manifest_path(check_root))
    record_preapproval_check(check_root, "planning/design@v1", "checks/asset-check@v1", ok=False)
    manifest = load_manifest(manifest_path(check_root))
    assert manifest["current_pointers"]["latest_asset_check"] == "checks/asset-check@v1"
    assert registry_item_by_ref(manifest, "checks/asset-check@v1")["lifecycle_state"] == "blocked"


def test_superficial_gate_closure_rejected(tmp: Path) -> None:
    run([str(SCRIPT / "init_hitl_package.py"), "浅门禁", "--root", str(tmp), "--tier", "standard"])
    root = tmp / "浅门禁"
    manifest = load_manifest(manifest_path(root))
    manifest["interrogation_gates"]["pre_design"] = {
        "status": "closed",
        "target_asset": "planning/design@v1",
        "blocking_unknowns": [],
        "evidence": ["repo explored"],
        "closed_at": "2026-05-20T00:00:00Z",
    }
    write_manifest(manifest_path(root), manifest)
    run([str(SCRIPT / "validate_interrogation_gate.py"), "--manifest", str(manifest_path(root)), "--gate", "pre_design", "--target", "planning/design@v1"], ok=False)


def test_manifest_negative_semantics(tmp: Path) -> None:
    root, _ = create_package(tmp / "manifest-negative")
    manifest = load_manifest(manifest_path(root))
    manifest["current_pointers"]["active_human_view"] = "planning/design@v1"
    registry_item_by_ref(manifest, "planning/facts@v1")["record_role"] = "check-record"
    registry_item_by_ref(manifest, "planning/facts@v1")["lifecycle_state"] = "approved"
    write_manifest(manifest_path(root), manifest)
    run([str(SCRIPT / "validate_manifest.py"), str(manifest_path(root)), "--check-paths"], ok=False)
    fenced = root / "manifest.yaml"
    fenced.write_text("```yaml\nprotocol: HITL\nschema_version: 0.0.1\nprotocol_version: 0.0.1\n```\n", encoding="utf-8")
    run([str(SCRIPT / "validate_manifest.py"), str(fenced)], ok=False)


def test_archive_and_verify(tmp: Path) -> None:
    root, _ = create_package(tmp / "archive")
    run([str(SCRIPT / "archive_asset.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/design@v1", "--state", "superseded"])
    item = registry_item_by_ref(load_manifest(manifest_path(root)), "planning/design@v1")
    assert item["path"] == "agent/archive/design.v1.yaml"
    run([str(SCRIPT / "archive_asset.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/design@v1", "--state", "retired"], ok=False)
    run([str(SCRIPT / "write_verification_record.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "execution/verification@v1", "--command", "pytest", "--result", "pass"])


def test_transition_manifest_script(tmp: Path) -> None:
    run([str(SCRIPT / "init_hitl_package.py"), "状态转换", "--root", str(tmp), "--tier", "standard"])
    root = tmp / "状态转换"
    _, design, _ = planning_assets()
    write_asset(root, "planning/design@v1", "design", "draft", "content-asset", design)
    resolution = root / "resolution.yaml"
    write_resolution_file(resolution)
    transition_close_gate(root, "pre_design", "planning/design@v1", resolution)
    run([str(SCRIPT / "transition_manifest.py"), "close-gate", "--manifest", str(manifest_path(root)), "--gate", "pre_design", "--target", "planning/design@v1", "--command", "关闭盘问: pre_design planning/design@v1", "--resolution-file", str(resolution)], ok=False)
    root2, _ = create_package(tmp / "decision")
    transition_record(root2, "approval", "planning/implementation-package@v1", "批准方案: planning/implementation-package@v1", ok=False)
    record_preapproval_check(root2)
    transition_record(root2, "approval", "planning/implementation-package@v1", "批准方案: planning/implementation-package@v1")
    transition_record(root2, "approval", "planning/implementation-package@v1", "批准方案: planning/implementation-package@v1", ok=False)
    facts, _, _ = planning_assets()
    run([str(SCRIPT / "init_hitl_package.py"), "状态标记", "--root", str(tmp), "--tier", "standard"])
    mark_root = tmp / "状态标记"
    write_asset(mark_root, "planning/facts@v1", "facts", "draft", "content-asset", facts)
    run([str(SCRIPT / "transition_manifest.py"), "mark-asset", "--manifest", str(manifest_path(mark_root)), "--asset-ref", "planning/facts@v1", "--state", "ready-for-approval"])
    run([str(SCRIPT / "transition_manifest.py"), "mark-asset", "--manifest", str(manifest_path(mark_root)), "--asset-ref", "planning/facts@v1", "--state", "approved"], ok=False)


def test_compose_implementation_package_script(tmp: Path) -> None:
    run([str(SCRIPT / "init_hitl_package.py"), "组合包", "--root", str(tmp), "--tier", "standard"])
    root = tmp / "组合包"
    facts, design, blueprint = planning_assets()
    write_asset(root, "planning/facts@v1", "facts", "completed", "content-asset", facts)
    manifest = load_manifest(manifest_path(root))
    close_gate(manifest, "pre_design", "planning/design@v1")
    close_gate(manifest, "pre_blueprint", "planning/blueprint@v1")
    write_manifest(manifest_path(root), manifest)
    write_asset(root, "planning/design@v1", "design", "completed", "content-asset", design)
    write_asset(root, "planning/blueprint@v1", "blueprint", "completed", "content-asset", blueprint)
    content = {"summary": ["compose package"], "approval_scope": ["approve referenced planning assets"], "risk_summary": ["low"], "verification_summary": ["self tests"]}
    write_text_file(root / "package-content.yaml", dump_yaml(content) + "\n")
    run([str(SCRIPT / "compose_implementation_package.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "planning/implementation-package@v1", "--facts", "planning/facts@v1", "--design", "planning/design@v1", "--blueprint", "planning/blueprint@v1", "--content-file", str(root / "package-content.yaml")])
    package = load_yaml_document(root / "agent/implementation-package.v1.yaml")
    assert package["authorized_assets"] == ["planning/facts@v1", "planning/design@v1", "planning/blueprint@v1"]
    assert registry_item_by_ref(load_manifest(manifest_path(root)), "planning/implementation-package@v1")["lifecycle_state"] == "ready-for-approval"

    run([str(SCRIPT / "init_hitl_package.py"), "草稿失败", "--root", str(tmp), "--tier", "standard"])
    bad = tmp / "草稿失败"
    write_asset(bad, "planning/facts@v1", "facts", "draft", "content-asset", facts)
    manifest = load_manifest(manifest_path(bad))
    close_gate(manifest, "pre_design", "planning/design@v1")
    close_gate(manifest, "pre_blueprint", "planning/blueprint@v1")
    write_manifest(manifest_path(bad), manifest)
    write_asset(bad, "planning/design@v1", "design", "completed", "content-asset", design)
    write_asset(bad, "planning/blueprint@v1", "blueprint", "completed", "content-asset", blueprint)
    write_text_file(bad / "package-content.yaml", dump_yaml(content) + "\n")
    run([str(SCRIPT / "compose_implementation_package.py"), "--manifest", str(manifest_path(bad)), "--asset-ref", "planning/implementation-package@v1", "--facts", "planning/facts@v1", "--design", "planning/design@v1", "--blueprint", "planning/blueprint@v1", "--content-file", str(bad / "package-content.yaml")], ok=False)

    run([str(SCRIPT / "init_hitl_package.py"), "严格组合", "--root", str(tmp), "--tier", "strict"])
    strict = tmp / "严格组合"
    write_asset(strict, "planning/facts@v1", "facts", "completed", "content-asset", facts)
    manifest = load_manifest(manifest_path(strict))
    close_gate(manifest, "pre_design", "planning/design@v1")
    close_gate(manifest, "pre_blueprint", "planning/blueprint@v1")
    write_manifest(manifest_path(strict), manifest)
    write_asset(strict, "planning/design@v1", "design", "approved", "approval-target", design)
    write_asset(strict, "planning/blueprint@v1", "blueprint", "approved", "approval-target", blueprint)
    write_text_file(strict / "package-content.yaml", dump_yaml(content) + "\n")
    run([str(SCRIPT / "compose_implementation_package.py"), "--manifest", str(manifest_path(strict)), "--asset-ref", "planning/implementation-package@v1", "--facts", "planning/facts@v1", "--design", "planning/design@v1", "--blueprint", "planning/blueprint@v1", "--content-file", str(strict / "package-content.yaml")])
    assert registry_item_by_ref(load_manifest(manifest_path(strict)), "planning/implementation-package@v1")["lifecycle_state"] == "completed"


def scaffold_content() -> dict:
    """Return the human-authored fields required by scaffold_execution_plan.py."""
    return {"summary_evaluation": {"complexity": "low", "code_volume": "small", "impact_scope": "src", "risk_level": "low", "testing_effort": "small"}, "unit_plans": [{"unit_id": "EU-001", "repo_observations": ["src/a.py is the planned target"], "implementation_steps": [{"step_id": "EU-001-S01", "action": "modify src/a.py according to approved intent"}], "source_level_change_intent": [{"step_id": "EU-001-S01", "implementation_step": "edit source file", "intent": "change src/a.py for fixture behavior", "target_changes": [{"file": "src/a.py", "symbols": ["fixture_symbol"], "change_type": "modify", "intent": "update fixture source content", "accepted_behavior": ["fixture passes"], "rejected_behavior": ["scope drift"]}]}], "verification_plan": {"commands": ["pytest"], "expected_results": ["pass"]}, "risk_checks": ["stay inside scope"], "stop_conditions": ["scope drift"]}]}


def prepare_scaffold_plan(tmp: Path, confirm: bool = False) -> Path:
    """Create a package, scaffold a Plan, and optionally confirm it."""
    root, _ = create_package(tmp)
    record_preapproval_check(root)
    transition_record(root, "approval", "planning/implementation-package@v1", "批准方案: planning/implementation-package@v1")
    archive_asset_check(root)
    record_final_check(root)
    write_resolution_file(root / "execution-resolution.yaml", "pre_execution_plan")
    transition_close_gate(root, "pre_execution_plan", "execution/plan@v1", root / "execution-resolution.yaml")
    write_text_file(root / "planned-files.txt", "src/a.py\n")
    write_text_file(root / "plan-content.yaml", dump_yaml(scaffold_content()) + "\n")
    run([str(SCRIPT / "scaffold_execution_plan.py"), "--manifest", str(manifest_path(root)), "--asset-ref", "execution/plan@v1", "--implementation-package-ref", "planning/implementation-package@v1", "--planned-file", str(root / "planned-files.txt"), "--repo-root", str(root), "--content-file", str(root / "plan-content.yaml")])
    if confirm:
        transition_record(root, "execution-confirmation", "execution/plan@v1", "执行计划: execution/plan@v1")
    return root


def test_check_allowed_files_enhanced(tmp: Path) -> None:
    root = prepare_scaffold_plan(tmp / "planned-source")
    run([str(SCRIPT / "check_allowed_files.py"), "--manifest", str(manifest_path(root)), "--blueprint-ref", "planning/blueprint@v1", "--planned-from-plan", "execution/plan@v1"])
    git_root = tmp / "git-scope"
    git_root.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=git_root, check=True, capture_output=True)
    write_text_file(git_root / "README.md", "base\n")
    subprocess.run(["git", "-c", "user.name=Self Test", "-c", "user.email=self@test", "add", "README.md"], cwd=git_root, check=True)
    subprocess.run(["git", "-c", "user.name=Self Test", "-c", "user.email=self@test", "commit", "-m", "base"], cwd=git_root, check=True, capture_output=True)
    pkg_root, _ = create_package(git_root / "docs/changes")
    write_text_file(git_root / "src/existing.py", "old\n")
    snapshot = tmp / "snapshot.txt"
    run([str(SCRIPT / "check_allowed_files.py"), "--manifest", str(manifest_path(pkg_root)), "--write-snapshot", str(snapshot), "--repo-root", str(git_root), "--include-untracked"])
    write_text_file(git_root / "src/new.py", "new\n")
    run([str(SCRIPT / "check_allowed_files.py"), "--manifest", str(manifest_path(pkg_root)), "--blueprint-ref", "planning/blueprint@v1", "--changed-from-git", "--repo-root", str(git_root), "--include-untracked", "--exclude-existing-before", str(snapshot)])


def test_scaffold_execution_plan_script(tmp: Path) -> None:
    root = prepare_scaffold_plan(tmp / "scaffold")
    run([str(SCRIPT / "validate_plan_or_runbook.py"), "--manifest", str(manifest_path(root)), "--plan-ref", "execution/plan@v1", "--implementation-package-ref", "planning/implementation-package@v1"])
    strict, _ = create_package(tmp / "strict-scaffold", tier="strict")
    record_final_check(strict)
    write_resolution_file(strict / "execution-resolution.yaml", "pre_execution_plan")
    transition_close_gate(strict, "pre_execution_plan", "execution/runbook@v1", strict / "execution-resolution.yaml")
    write_text_file(strict / "planned-files.txt", "src/a.py\n")
    write_text_file(strict / "plan-content.yaml", dump_yaml(scaffold_content()) + "\n")
    run([str(SCRIPT / "scaffold_execution_plan.py"), "--manifest", str(manifest_path(strict)), "--asset-ref", "execution/plan@v1", "--implementation-package-ref", "planning/implementation-package@v1", "--planned-file", str(strict / "planned-files.txt"), "--repo-root", str(strict), "--content-file", str(strict / "plan-content.yaml")], ok=False)
    unapproved, _ = create_package(tmp / "unapproved")
    write_resolution_file(unapproved / "execution-resolution.yaml", "pre_execution_plan")
    transition_close_gate(unapproved, "pre_execution_plan", "execution/plan@v1", unapproved / "execution-resolution.yaml")
    write_text_file(unapproved / "planned-files.txt", "src/a.py\n")
    write_text_file(unapproved / "plan-content.yaml", dump_yaml(scaffold_content()) + "\n")
    run([str(SCRIPT / "scaffold_execution_plan.py"), "--manifest", str(manifest_path(unapproved)), "--asset-ref", "execution/plan@v1", "--implementation-package-ref", "planning/implementation-package@v1", "--planned-file", str(unapproved / "planned-files.txt"), "--repo-root", str(unapproved), "--content-file", str(unapproved / "plan-content.yaml")], ok=False)


def test_record_execution_evidence_script(tmp: Path) -> None:
    root = prepare_scaffold_plan(tmp / "evidence", confirm=False)
    commands = {"commands": [{"command": "pytest", "result": "pass", "output_summary": "tests passed"}], "skipped_items": [], "residual_risks": []}
    write_text_file(root / "commands.yaml", dump_yaml(commands) + "\n")
    run([str(SCRIPT / "record_execution_evidence.py"), "verification", "--manifest", str(manifest_path(root)), "--asset-ref", "execution/verification@v1", "--source", "execution/plan@v1", "--commands-file", str(root / "commands.yaml"), "--overall-result", "pass"], ok=False)
    transition_record(root, "execution-confirmation", "execution/plan@v1", "执行计划: execution/plan@v1")
    run([str(SCRIPT / "record_execution_evidence.py"), "verification", "--manifest", str(manifest_path(root)), "--asset-ref", "execution/verification@v1", "--source", "execution/plan@v1", "--commands-file", str(root / "commands.yaml"), "--overall-result", "pass"])
    write_text_file(root / "bad-changed.txt", "other/a.py\n")
    run([str(SCRIPT / "record_execution_evidence.py"), "close", "--manifest", str(manifest_path(root)), "--asset-ref", "execution/close@v1", "--source", "execution/plan@v1", "--verification-ref", "execution/verification@v1", "--changed-file", str(root / "bad-changed.txt"), "--conclusion", "completed"], ok=False)
    write_text_file(root / "changed.txt", "src/a.py\n")
    run([str(SCRIPT / "record_execution_evidence.py"), "close", "--manifest", str(manifest_path(root)), "--asset-ref", "execution/close@v1", "--source", "execution/plan@v1", "--verification-ref", "execution/verification@v1", "--changed-file", str(root / "changed.txt"), "--conclusion", "completed"])

    fail_root = prepare_scaffold_plan(tmp / "evidence-fail", confirm=True)
    fail_commands = {"commands": [{"command": "pytest", "result": "fail", "output_summary": "tests failed"}], "skipped_items": [], "residual_risks": ["failure remains"]}
    write_text_file(fail_root / "commands.yaml", dump_yaml(fail_commands) + "\n")
    run([str(SCRIPT / "record_execution_evidence.py"), "verification", "--manifest", str(manifest_path(fail_root)), "--asset-ref", "execution/verification@v1", "--source", "execution/plan@v1", "--commands-file", str(fail_root / "commands.yaml"), "--overall-result", "fail"])
    write_text_file(fail_root / "changed.txt", "src/a.py\n")
    run([str(SCRIPT / "record_execution_evidence.py"), "close", "--manifest", str(manifest_path(fail_root)), "--asset-ref", "execution/close@v1", "--source", "execution/plan@v1", "--verification-ref", "execution/verification@v1", "--changed-file", str(fail_root / "changed.txt"), "--conclusion", "completed"], ok=False)


def main() -> int:
    tests = [test_golden, test_interrogation_gates, test_failures, test_allowed_files, test_plan, test_strict_asset_check, test_asset_check_negative_targets, test_preapproval_rejects_invalid_content, test_write_and_archive_guards, test_forbidden_asset_fields_and_check_records, test_superficial_gate_closure_rejected, test_manifest_negative_semantics, test_archive_and_verify, test_transition_manifest_script, test_compose_implementation_package_script, test_check_allowed_files_enhanced, test_scaffold_execution_plan_script, test_record_execution_evidence_script]
    with tempfile.TemporaryDirectory(prefix="hitl-self-tests-") as d:
        tmp = Path(d)
        for test in tests:
            test(tmp / test.__name__)
            print(f"PASS {test.__name__}")
    print("HITL self tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
