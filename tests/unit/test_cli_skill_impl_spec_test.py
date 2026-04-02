from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class SkillRuntimeHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        self.repo_root = Path(__file__).resolve().parents[2]

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request_path(self, name: str) -> Path:
        return self.workspace / "contracts" / "input" / name

    def response_path(self, name: str) -> Path:
        return self.workspace / "artifacts" / "active" / name

    def resolve_ref(self, ref_value: str) -> Path:
        path = Path(ref_value)
        return path if path.is_absolute() else self.workspace / path


class TestImplSpecSkillRuntime(SkillRuntimeHarness):
    def write_markdown_doc(self, relative: str, frontmatter: dict, body: str) -> str:
        path = self.workspace / relative
        payload = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + body
        write_yaml(path, payload)
        return path.as_posix()

    def write_yaml_doc(self, relative: str, payload: dict) -> str:
        path = self.workspace / relative
        write_yaml(path, yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))
        return path.as_posix()

    def build_phase2_surface_response(self, *, verdict: str, review_coverage_status: str) -> Path:
        base = self.workspace / "artifacts" / "active" / "qa" / "impl-spec-tests" / "phase2-surface"
        base.mkdir(parents=True, exist_ok=True)
        ref_root = "qa/impl-spec-tests/phase2-surface"
        deep_review_refs = {
            "semantic_review_ref": f"{ref_root}/semantic-review.json",
            "system_views_ref": f"{ref_root}/system-views.json",
            "logic_risk_inventory_ref": f"{ref_root}/logic-risk-inventory.json",
            "ux_risk_inventory_ref": f"{ref_root}/ux-risk-inventory.json",
            "ux_improvement_inventory_ref": f"{ref_root}/ux-improvement-inventory.json",
            "journey_simulation_ref": f"{ref_root}/journey-simulation.json",
            "state_invariant_check_ref": f"{ref_root}/state-invariant-check.json",
            "cross_artifact_trace_ref": f"{ref_root}/cross-artifact-trace.json",
            "open_questions_ref": f"{ref_root}/open-questions.json",
            "false_negative_challenge_ref": f"{ref_root}/false-negative-challenge.json",
            "dimension_reviews_ref": f"{ref_root}/dimension-reviews.json",
            "review_coverage_ref": f"{ref_root}/review-coverage.json",
            "defects_ref": f"{ref_root}/impl-spec-test-defects.json",
        }
        (base / "impl-spec-test-report.md").write_text("# Phase 2 Deep Review\n", encoding="utf-8")
        artifacts = {
            "package-manifest.json": {"artifact_type": "impl_spec_test_report_package"},
            "impl-spec-test-report.json": {"artifact_type": "impl_spec_test_report"},
            "semantic-review.json": {"artifacts": ["IMPL", "FEAT", "TECH"]},
            "system-views.json": {"functional_chain": {}, "user_journey": {}},
            "logic-risk-inventory.json": {
                "items": [
                    {"id": "logic-state-001", "severity": "high", "title": "completion state and guard can diverge"},
                    {"id": "logic-state-002", "severity": "medium", "title": "state transition is not explicitly reversible"},
                ]
            },
            "ux-risk-inventory.json": {
                "items": [
                    {"id": "ux-friction-001", "severity": "medium", "title": "deferred device entry may not expose a clear skip affordance"},
                ]
            },
            "ux-improvement-inventory.json": {
                "items": [
                    {"id": "ux-improve-001", "priority": "opportunity", "title": "surface deferred device entry earlier"},
                ]
            },
            "journey-simulation.json": {
                "personas": ["first_time_user", "high_risk_user", "returning_user"],
                "scenarios": ["invalid_input", "network_failure", "device_finalize_failure"],
            },
            "state-invariant-check.json": {
                "invariants": ["profile_ready implies homepage_entry_allowed"],
                "violations": [],
            },
            "cross-artifact-trace.json": {
                "trace": [{"from": "FEAT", "to": "IMPL"}, {"from": "TECH", "to": "TESTSET"}],
            },
            "open-questions.json": ["Should deferred device entry be skip-first or continue-first?"],
            "false-negative-challenge.json": {
                "challenges": ["happy-path-only review would miss recovery coverage gaps"],
            },
            "dimension-reviews.json": {
                "functional_logic": {"score": 8, "coverage_confidence": 0.9},
                "data_modeling": {"score": 8, "coverage_confidence": 0.9},
                "user_journey": {"score": 8, "coverage_confidence": 0.9},
                "ui_usability": {"score": 8, "coverage_confidence": 0.9},
                "api_contract": {"score": 8, "coverage_confidence": 0.9},
                "implementation_executability": {"score": 8, "coverage_confidence": 0.9},
                "testability": {"score": 8, "coverage_confidence": 0.9},
                "migration_compatibility": {"score": 8, "coverage_confidence": 0.9},
            },
            "review-coverage.json": {
                "status": review_coverage_status,
                "counterexample_gap_dimensions": [] if review_coverage_status != "insufficient" else ["data_modeling"],
            },
            "impl-spec-test-defects.json": {
                "blocking_issues": [],
                "high_priority_issues": [],
                "normal_issues": [],
            },
            "impl-spec-test-gate-subject.json": {
                "artifact_type": "implementation_readiness_gate_subject",
                "verdict": verdict,
            },
            "implementation-readiness-intake.json": {
                "main_test_object_ref": "ssot/impl/IMPL-IMPL-SPEC-001__demo.md",
                "authority_bindings": [],
            },
            "cross-artifact-issue-inventory.json": {"summary": {"blocking": 0, "high_priority": 0, "normal": 0}},
            "implementation-readiness-verdict.json": {
                "verdict": verdict,
                "implementation_readiness": "partial" if verdict != "pass" else "ready",
            },
            "execution-evidence.json": {"request_id": "phase2", "execution_mode": {"mode": "deep_spec_testing"}},
            "supervision-evidence.json": {"authority_bindings": [], "issue_counts": {}, "review_coverage": {}, "dimension_reviews": {}},
            "repair-patch-suggestions.md": "# Repair Suggestions\n",
        }
        for filename, payload in artifacts.items():
            path = base / filename
            if filename.endswith(".md"):
                path.write_text(payload, encoding="utf-8")
            else:
                write_json(path, payload)
        response = {
            "api_version": "v1",
            "command": "skill.impl-spec-test",
            "request_id": "phase2-surface",
            "result_status": "ok",
            "status_code": "200",
            "exit_code": 0,
            "message": "ok",
            "data": {
                "skill_ref": "skill.qa.impl_spec_test",
                "runner_skill_ref": "skill.runner.impl_spec_test",
                "candidate_artifact_ref": "candidate.phase2-surface",
                "candidate_managed_artifact_ref": f"{ref_root}/candidate.json",
                "candidate_receipt_ref": f"{ref_root}/receipt.json",
                "candidate_registry_record_ref": f"{ref_root}/registry.json",
                "handoff_ref": f"{ref_root}/handoff.json",
                "gate_pending_ref": f"{ref_root}/gate-pending.json",
                "run_status": "completed_with_findings" if verdict != "pass" else "completed",
                "verdict": verdict,
                "implementation_readiness": "partial" if verdict != "pass" else "ready",
                "self_contained_readiness": "insufficient" if review_coverage_status == "insufficient" else "sufficient",
                "self_contained_evaluation_mode": "strong_self_contained",
                "recommended_next_action": "revise_impl" if verdict != "pass" else "proceed_to_gate",
                "recommended_actor": "impl_author" if verdict != "pass" else "human_gate",
                "repair_target_artifact": "IMPL",
                "execution_mode": "deep_spec_testing",
                "report_package_ref": f"{ref_root}/package-manifest.json",
                "report_json_ref": f"{ref_root}/impl-spec-test-report.json",
                "report_markdown_ref": f"{ref_root}/impl-spec-test-report.md",
                **deep_review_refs,
                "gate_subject_ref": f"{ref_root}/impl-spec-test-gate-subject.json",
                "intake_result_ref": f"{ref_root}/implementation-readiness-intake.json",
                "issue_inventory_ref": f"{ref_root}/cross-artifact-issue-inventory.json",
                "counterexample_result_ref": f"{ref_root}/impl-spec-test-counterexamples.json",
                "readiness_verdict_ref": f"{ref_root}/implementation-readiness-verdict.json",
                "repair_suggestions_ref": f"{ref_root}/repair-patch-suggestions.md",
                "execution_evidence_ref": f"{ref_root}/execution-evidence.json",
                "supervision_evidence_ref": f"{ref_root}/supervision-evidence.json",
            },
        }
        write_json(self.response_path("phase2-surface.response.json"), response)
        write_json(base / "impl-spec-test-counterexamples.json", {"mode": "deep_spec_testing", "scenarios": []})
        write_json(base / "candidate.json", {"candidate": True})
        write_json(base / "receipt.json", {"receipt": True})
        write_json(base / "registry.json", {"registry": True})
        write_json(base / "handoff.json", {"handoff": True})
        write_json(base / "gate-pending.json", {"gate_pending": True})
        return self.response_path("phase2-surface.response.json")

    def test_impl_spec_skill_surface_declares_phase2_deep_review_artifacts(self) -> None:
        skill_root = self.repo_root / "skills" / "ll-qa-impl-spec-test"
        output_contract_text = (skill_root / "output" / "contract.yaml").read_text(encoding="utf-8")
        output_contract = yaml.safe_load((skill_root / "output" / "contract.yaml").read_text(encoding="utf-8"))
        output_schema = json.loads((skill_root / "output" / "schema.json").read_text(encoding="utf-8"))
        ll_contract = yaml.safe_load((skill_root / "ll.contract.yaml").read_text(encoding="utf-8"))
        executor = (skill_root / "agents" / "executor.md").read_text(encoding="utf-8").lower()
        supervisor = (skill_root / "agents" / "supervisor.md").read_text(encoding="utf-8").lower()
        output_checklist = (skill_root / "output" / "semantic-checklist.md").read_text(encoding="utf-8").lower()
        expected_refs = {
            "logic_risk_inventory_ref",
            "ux_risk_inventory_ref",
            "ux_improvement_inventory_ref",
            "journey_simulation_ref",
            "state_invariant_check_ref",
            "cross_artifact_trace_ref",
            "open_questions_ref",
            "false_negative_challenge_ref",
        }
        for ref in expected_refs:
            self.assertIn(ref, output_contract_text)
        self.assertTrue(expected_refs.issubset(set(output_contract["phase2_extended_data_fields"])))
        self.assertTrue(expected_refs.issubset(set(output_schema["properties"]["data"]["properties"])))
        self.assertTrue(expected_refs.issubset(set(ll_contract["runtime"]["phase2_extended_output_artifacts"])))
        expected_freeze_checks = {ref.replace("_ref", "_present") for ref in expected_refs}
        self.assertTrue(expected_freeze_checks.issubset(set(ll_contract["gate"]["phase2_freeze_requires"])))
        self.assertIn("six-stage path", (skill_root / "input" / "semantic-checklist.md").read_text(encoding="utf-8").lower())
        self.assertIn("logic risk inventory", output_checklist)
        self.assertIn("review_coverage.status", output_checklist)
        self.assertIn("logic risk inventory", executor)
        self.assertIn("false-negative challenge", executor)
        self.assertIn("ux improvement inventory", executor)
        self.assertIn("logic risk inventory", supervisor)
        self.assertIn("false-negative challenge", supervisor)

    def test_impl_spec_skill_guard_accepts_review_profile_input(self) -> None:
        request_path = self.request_path("review-profile.request.json")
        write_json(
            request_path,
            {
                "api_version": "v1",
                "command": "skill.impl-spec-test",
                "request_id": "review-profile",
                "workspace_root": self.workspace.as_posix(),
                "actor_ref": "test-suite",
                "trace": {"run_ref": "review-profile"},
                "payload": {
                    "impl_ref": "IMPL-1",
                    "impl_package_ref": "IMPL-1",
                    "feat_ref": "FEAT-1",
                    "tech_ref": "TECH-1",
                    "review_profile": {
                        "focus_areas": ["ux", "logic"],
                        "personas": ["first_time_user"],
                        "counterexample_families": ["network_failure"],
                        "coverage_goal": "deep",
                    },
                    "journey_personas": ["first_time_user"],
                    "counterexample_families": ["network_failure"],
                    "review_focus": ["journey"],
                    "false_negative_challenge": True,
                },
            },
        )
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-input", str(request_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_impl_spec_skill_guard_accepts_phase2_surface_with_partial_coverage(self) -> None:
        guard_response = self.build_phase2_surface_response(verdict="pass_with_revisions", review_coverage_status="partial")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(guard_response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = guard_response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        logic_inventory = read_json(artifact_root / "logic-risk-inventory.json")
        journey_simulation = read_json(artifact_root / "journey-simulation.json")
        review_coverage = read_json(artifact_root / "review-coverage.json")
        self.assertEqual(review_coverage["status"], "partial")
        self.assertTrue(any(item["id"].startswith("logic-state-") for item in logic_inventory["items"]))
        self.assertIn("first_time_user", journey_simulation["personas"])

    def test_impl_spec_skill_guard_rejects_pass_when_review_coverage_is_partial(self) -> None:
        guard_response = self.build_phase2_surface_response(verdict="pass", review_coverage_status="partial")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(guard_response)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be pass unless review coverage is sufficient", result.stderr)

    def build_authority_fixture(
        self,
        *,
        conflicting_tech: bool = False,
        ui_blocking: bool = False,
        missing_recovery: bool = False,
    ) -> dict[str, str]:
        feat_id = "FEAT-IMPL-SPEC-001"
        tech_id = "TECH-IMPL-SPEC-001"
        impl_id = "IMPL-IMPL-SPEC-001"
        ui_id = "UI-IMPL-SPEC-001"
        testset_id = "TESTSET-IMPL-SPEC-001"
        self.write_markdown_doc(
            f"ssot/feat/{feat_id}__demo.md",
            {"id": feat_id, "ssot_type": "FEAT", "status": "frozen"},
            "\n".join(
                [
                    "# Demo FEAT",
                    "",
                    "## In Scope",
                    "- Demo onboarding feature keeps device connection deferred and non-blocking.",
                    "- User completes `profile_ready` and receives `homepage_entry_allowed`.",
                    "",
                ]
            )
            + "\n",
        )
        self.write_markdown_doc(
            f"ssot/tech/{tech_id}__demo.md",
            {"id": tech_id, "ssot_type": "TECH", "status": "accepted"},
            "\n".join(
                [
                    "# Demo TECH",
                    "",
                    "## State Model Snapshot",
                    "- `registered` -> `profile_ready` -> `homepage_entered`",
                    "- `user_profile` remains the sole authority for onboarding profile fields.",
                    "- `birthdate` remains the canonical age-related field for onboarding completion.",
                    "",
                    "## Main Sequence Snapshot",
                    "- validate onboarding input",
                    "- persist `profile_ready`",
                    "- allow `homepage_entry_allowed`",
                    "",
                    "## Integration Points Snapshot",
                    "- homepage guard reads the unified onboarding state.",
                    "- network failure keeps the user on the onboarding page and supports retry.",
                    "",
                ]
            )
            + "\n",
        )
        self.write_markdown_doc(
            f"ssot/architecture/ARCH-IMPL-SPEC-001__demo.md",
            {"id": "ARCH-IMPL-SPEC-001", "ssot_type": "ARCH", "status": "accepted"},
            "# Demo ARCH\n\n## State Model Snapshot\n- layering preserves the onboarding state boundary.\n",
        )
        self.write_markdown_doc(
            f"ssot/api/API-IMPL-SPEC-001__demo.md",
            {"id": "API-IMPL-SPEC-001", "ssot_type": "API", "status": "accepted"},
            "# Demo API\n\n## API Contract Snapshot\n- `SubmitProfile`: output=`profile_ready`, `homepage_entry_allowed`; errors=`invalid_input`, `network_failure`; precondition=`registered`\n",
        )
        self.write_markdown_doc(
            f"ssot/ui/{ui_id}__demo.md",
            {"id": ui_id, "ssot_type": "UI", "status": "approved"},
            (
                "# Demo UI\n\n## UI Constraint Snapshot\n- Device connection remains deferred and the user can skip to continue.\n"
                if not ui_blocking
                else "# Demo UI\n\n## UI Constraint Snapshot\n- User must connect device before continue to the homepage.\n"
            ),
        )
        self.write_yaml_doc(
            f"ssot/testset/{testset_id}__demo.yaml",
            {
                "id": testset_id,
                "ssot_type": "TESTSET",
                "status": "approved",
                "title": "Demo TESTSET",
                "coverage_scope": ["Validate `profile_ready`, `homepage_entry_allowed`, and deferred device entry."],
                "test_units": [
                    {
                        "unit_ref": "TS-U01",
                        "observation_points": ["`profile_ready`", "`homepage_entry_allowed`", "`birthdate` canonical write"],
                        "pass_conditions": ["`profile_ready` and `homepage_entry_allowed` are visible.", "`birthdate` remains canonical."],
                        "fail_conditions": ["`invalid_input` keeps the user on the onboarding page.", "`network_failure` keeps retry available on the onboarding page."],
                    }
                ],
                "acceptance_traceability": [{"acceptance_ref": "AC-01", "then": "Profile submit reaches `profile_ready` and `homepage_entry_allowed`."}],
            },
        )
        impl_frontmatter = {
            "id": impl_id,
            "ssot_type": "IMPL",
            "status": "execution_ready",
            "feat_ref": feat_id,
            "tech_ref": "TECH-IMPL-SPEC-OTHER" if conflicting_tech else tech_id,
        }
        self.write_markdown_doc(
            f"ssot/impl/{impl_id}__demo.md",
            impl_frontmatter,
            "\n".join(
                [
                    "# Demo IMPL",
                    "",
                    "## Main Sequence Snapshot",
                    "- collect minimal onboarding input",
                    "- validate and persist `profile_ready`",
                    "- release `homepage_entry_allowed` and keep device entry deferred",
                    "- preserve `birthdate` as the canonical age-related field and allow retry after `network_failure`",
                    "",
                    "## State Model Snapshot",
                    "- `registered` -> `profile_ready` -> `homepage_entered`",
                    *([] if missing_recovery else ["- invalid submission keeps the user on the onboarding page and supports retry."]),
                    *([] if missing_recovery else ["- network failure keeps the user on the onboarding page and supports retry."]),
                    *(["- `registered(fail)` -> `error_visible`"] if missing_recovery else []),
                    "",
                    "## Integration Points Snapshot",
                    "- homepage guard reads onboarding state after submit.",
                    "- device entry remains deferred and non-blocking.",
                    "",
                    "## Implementation Unit Mapping Snapshot",
                    "- onboarding/profile_form (new): collect required fields.",
                    "- onboarding/profile_submit (new): persist `profile_ready` and `homepage_entry_allowed`.",
                    "- routing/homepage_guard (extend): allow homepage after `profile_ready`.",
                    "",
                ]
            )
            + "\n",
        )
        return {
            "impl_ref": impl_id,
            "impl_package_ref": impl_id,
            "feat_ref": feat_id,
            "tech_ref": tech_id,
            "arch_ref": "ARCH-IMPL-SPEC-001",
            "api_ref": "API-IMPL-SPEC-001",
            "ui_refs": [ui_id],
            "testset_refs": [testset_id],
        }

    def assert_ref_set(self, payload: dict, keys: list[str]) -> None:
        for key in keys:
            self.assertTrue(self.resolve_ref(payload[key]).exists(), key)

    def test_impl_spec_skill_emits_candidate_and_handoff(self) -> None:
        response = self.build_phase2_surface_response(verdict="pass", review_coverage_status="sufficient")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        self.assertEqual(read_json(artifact_root / "review-coverage.json")["status"], "sufficient")
        self.assertIn("logic-state-001", {item["id"] for item in read_json(artifact_root / "logic-risk-inventory.json")["items"]})
        self.assertIn("first_time_user", read_json(artifact_root / "journey-simulation.json")["personas"])

    def test_impl_spec_skill_forces_deep_mode_and_blocks_on_authority_conflict(self) -> None:
        response = self.build_phase2_surface_response(verdict="block", review_coverage_status="insufficient")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        ux_risk = read_json(artifact_root / "ux-risk-inventory.json")
        self.assertTrue(any(item["id"].startswith("ux-friction-") for item in ux_risk["items"]))
        self.assertEqual(read_json(artifact_root / "review-coverage.json")["status"], "insufficient")

    def test_impl_spec_skill_blocks_when_failure_paths_have_no_recovery(self) -> None:
        response = self.build_phase2_surface_response(verdict="block", review_coverage_status="partial")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        state_invariants = read_json(artifact_root / "state-invariant-check.json")
        self.assertIn("profile_ready implies homepage_entry_allowed", state_invariants["invariants"])
        self.assertGreater(len(read_json(artifact_root / "false-negative-challenge.json")["challenges"]), 0)

    def test_impl_spec_skill_blocks_when_ui_conflicts_with_non_blocking_flow(self) -> None:
        response = self.build_phase2_surface_response(verdict="block", review_coverage_status="partial")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        ux_improvement = read_json(artifact_root / "ux-improvement-inventory.json")
        self.assertTrue(any(item["id"].startswith("ux-improve-") for item in ux_improvement["items"]))
        self.assertIn("skip-first", " ".join(read_json(artifact_root / "open-questions.json")))

    def test_impl_spec_skill_marks_migration_gap_as_pass_with_revisions(self) -> None:
        response = self.build_phase2_surface_response(verdict="pass_with_revisions", review_coverage_status="insufficient")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        self.assertEqual(read_json(artifact_root / "review-coverage.json")["status"], "insufficient")
        trace = read_json(artifact_root / "cross-artifact-trace.json")
        self.assertGreaterEqual(len(trace["trace"]), 2)

    def test_impl_spec_skill_supports_rollout_pilot_chain(self) -> None:
        response = self.build_phase2_surface_response(verdict="pass", review_coverage_status="sufficient")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "validate-output", str(response)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact_root = response.parent / "qa" / "impl-spec-tests" / "phase2-surface"
        self.assertEqual(read_json(artifact_root / "review-coverage.json")["status"], "sufficient")
        self.assertIn("deferred device entry", read_json(artifact_root / "ux-risk-inventory.json")["items"][0]["title"].lower())
