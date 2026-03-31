from __future__ import annotations

import yaml

from cli.lib.test_exec_execution import _coverage_expansion_targets
from _test_exec_skill_support import SkillRuntimeHarness, python_command, python_file_command, read_json, write_json, write_yaml


class TestCliExecSkillRuntime(SkillRuntimeHarness):
    def test_cli_skill_emits_candidate_and_handoff_with_real_testset(self) -> None:
        command = python_command(
            "import os; "
            "assert os.environ['LEE_EXECUTION_MODALITY'] == 'cli'; "
            "print(os.environ['LEE_TEST_CASE_ID'])"
        )
        env_ref = self.write_env_spec(
            "cli-env.yaml",
            "execution_modality: cli\n"
            "command_entry: >-\n"
            f"  {command}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-001",
            },
        )
        req = self.request_path("skill-cli.json")
        write_json(req, request)
        response = self.response_path("skill-cli.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)
        self.assertEqual(payload["data"]["skill_ref"], "skill.qa.test_exec_cli")
        self.assertEqual(payload["data"]["runner_skill_ref"], "skill.runner.test_cli")
        self.assertEqual(payload["data"]["assigned_gate_queue"], "mainline.gate.pending")
        self.assert_execution_outputs(payload["data"], expected_cases=5, expected_status="completed")

    def test_cli_skill_records_failed_cases_and_bug_bundle(self) -> None:
        command = python_command(
            "import os, sys; "
            "case_id = os.environ['LEE_TEST_CASE_ID']; "
            "print(case_id); "
            "sys.exit(7 if case_id.endswith('U03') else 0)"
        )
        env_ref = self.write_env_spec(
            "cli-failing-env.yaml",
            "execution_modality: cli\n"
            "command_entry: >-\n"
            f"  {command}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-fail-001",
            },
        )
        req = self.request_path("skill-cli-fail.json")
        write_json(req, request)
        response = self.response_path("skill-cli-fail.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=5, expected_status="completed_with_failures")
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["failed"], 1)
        bug_index = read_json(self.resolve_ref(payload["bug_bundle_ref"]))
        self.assertEqual(len(bug_index["bugs"]), 1)

    def test_cli_skill_timeout_maps_to_blocked_warning_run(self) -> None:
        command = python_command("import time; time.sleep(2)")
        env_ref = self.write_env_spec(
            "cli-timeout-env.yaml",
            "execution_modality: cli\n"
            "timeout_seconds: 1\n"
            "command_entry: >-\n"
            f"  {command}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-timeout-001",
            },
        )
        req = self.request_path("skill-cli-timeout.json")
        write_json(req, request)
        response = self.response_path("skill-cli-timeout.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=5, expected_status="completed_with_warnings")
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["blocked"], 5)

    def test_cli_skill_can_run_smoke_mode_with_python_inline_command(self) -> None:
        command = python_command("import os; print(os.environ['LEE_TEST_CASE_ID'])")
        env_ref = self.write_env_spec(
            "cli-smoke-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: smoke\n"
            "command_entry: >-\n"
            f"  {command}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-smoke-001",
            },
        )
        req = self.request_path("skill-cli-smoke.json")
        write_json(req, request)
        response = self.response_path("skill-cli-smoke.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=5, expected_status="completed")
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertEqual(coverage_summary["status"], "disabled")

    def test_cli_skill_rejects_python_inline_command_when_coverage_is_enabled(self) -> None:
        command = python_command("import os; print(os.environ['LEE_TEST_CASE_ID'])")
        env_ref = self.write_env_spec(
            "cli-qualification-inline-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_scope_name:\n"
            "  - qualification inline rejection\n"
            "coverage_include:\n"
            f"  - {(self.workspace / 'tools' / 'qualification_inline_target.py').as_posix()}\n"
            "command_entry: >-\n"
            f"  {command}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-inline-reject-001",
            },
        )
        req = self.request_path("skill-cli-inline-reject.json")
        write_json(req, request)
        response = self.response_path("skill-cli-inline-reject.response.json")
        self.assertNotEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")
        self.assertIn("python -c", payload["message"])

    def test_cli_skill_pilot_integration_flow(self) -> None:
        command = python_command("import os; assert os.environ['LEE_EXECUTION_MODALITY'] == 'cli'; print(os.environ['LEE_TEST_CASE_ID'])")
        env_ref = self.write_env_spec(
            "cli-pilot-env.yaml",
            "execution_modality: cli\n" "command_entry: >-\n" f"  {command}\n" "workdir: .\n",
        )
        self.run_json_command(
            "rollout",
            "onboard-skill",
            "pilot-onboard.json",
            "pilot-onboard.response.json",
            {"skill_ref": "skill.qa.test_exec_cli", "wave_id": "wave-pilot-01", "scope": "pilot", "compat_mode": True, "foundation_ready": True},
        )
        skill_payload = self.run_json_command(
            "skill",
            "test-exec-cli",
            "pilot-skill.json",
            "pilot-skill.response.json",
            {"test_set_ref": self.feat_testset_path("005"), "test_environment_ref": env_ref, "proposal_ref": "proposal-pilot-005"},
        )
        self.assert_execution_outputs(skill_payload, expected_cases=5, expected_status="completed")
        decision_payload = self.run_json_command(
            "gate",
            "decide",
            "pilot-decide.json",
            "pilot-decide.response.json",
            {"handoff_ref": skill_payload["handoff_ref"], "proposal_ref": "proposal-pilot-005", "decision": "approve"},
        )
        materialize_payload = self.run_json_command(
            "gate",
            "materialize",
            "pilot-materialize.json",
            "pilot-materialize.response.json",
            {"gate_decision_ref": decision_payload["gate_decision_ref"], "candidate_ref": skill_payload["candidate_artifact_ref"], "target_formal_kind": "pilot-report"},
        )
        self.run_json_command(
            "registry",
            "validate-admission",
            "pilot-admission.json",
            "pilot-admission.response.json",
            {"consumer_ref": "skill.qa.test_exec_cli.consumer", "requested_ref": materialize_payload["formal_ref"]},
        )
        audit_payload = self.run_json_command(
            "audit",
            "emit-finding-bundle",
            "pilot-audit.json",
            "pilot-audit.response.json",
            {
                "workspace_diff_ref": "artifacts/active/diff.json",
                "gateway_receipt_refs": [skill_payload["candidate_receipt_ref"]],
                "registry_refs": [skill_payload["candidate_registry_record_ref"]],
                "policy_verdict_refs": [skill_payload["candidate_receipt_ref"]],
                "attempted_unmanaged_reads": [],
                "bypass_write_paths": [],
            },
        )
        pilot_payload = self.run_json_command(
            "audit",
            "submit-pilot-evidence",
            "pilot-submit-evidence.json",
            "pilot-submit-evidence.response.json",
            {
                "pilot_chain_ref": self.feat_testset_path("005"),
                "producer_ref": skill_payload["skill_ref"],
                "consumer_ref": "skill.qa.test_exec_cli.consumer",
                "audit_ref": audit_payload["finding_bundle_ref"],
                "gate_ref": decision_payload["gate_decision_ref"],
            },
        )
        cutover_payload = self.run_json_command(
            "rollout",
            "cutover-wave",
            "pilot-cutover.json",
            "pilot-cutover.response.json",
            {"wave_id": "wave-pilot-01", "pilot_evidence_ref": pilot_payload["pilot_evidence_ref"]},
        )
        self.assertEqual(cutover_payload["readiness_label"], "cutover_guarded")

    def test_cli_skill_keeps_branch_derived_targets_when_later_round_has_no_new_gap(self) -> None:
        script_path = self.workspace / "tools" / "branch_priority_target_stable.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if 'missing-branch' in case_id:\n"
            "    print('branch-seed-case')\n"
            "elif case_id.endswith('U02'):\n"
            "    print('branch-two')\n"
            "else:\n"
            "    print('branch-one')\n",
        )
        testset_ref = self.write_testset(
            "branch-priority-stable-testset.yaml",
            "id: TESTSET-BRANCH-PRIORITY-STABLE\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-BRANCH-PRIORITY-STABLE\n"
            "title: Branch Priority Stable Test Set\n"
            "feat_ref: FEAT-BRANCH-PRIORITY-STABLE\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - fallback-family\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 2\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-BRANCH-PRIORITY-STABLE-U01\n"
            "    title: branch case one\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n"
            "  - unit_ref: TESTSET-BRANCH-PRIORITY-STABLE-U02\n"
            "    title: branch case two\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-branch-priority-stable-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_branch_enabled: true\n"
            "coverage_scope_name:\n"
            "  - branch priority stable scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 2\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-branch-priority-stable-001",
            },
        )
        req = self.request_path("skill-cli-branch-priority-stable.json")
        write_json(req, request)
        response = self.response_path("skill-cli-branch-priority-stable.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=4, expected_status="completed")
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["expansion_round"], 2)
        self.assertIn(test_case_pack["expansion_stop_reason"], {"coverage_below_goal", "qualification_budget_exhausted", "expansion_targets_exhausted"})
        self.assertFalse(any(case["case_id"].endswith("fallback-family") for case in test_case_pack["cases"]))
        self.assertTrue(any("missing-branch" in case["case_id"] for case in test_case_pack["cases"]))
        self.assertTrue(any("missing-line" in case["case_id"] for case in test_case_pack["cases"]))

    def test_cli_skill_collects_real_coverage_when_enabled_for_python_script(self) -> None:
        script_path = self.workspace / "tools" / "coverage_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if case_id.endswith('U03'):\n"
            "    print('branch-three')\n"
            "else:\n"
            "    print('branch-default')\n",
        )
        env_ref = self.write_env_spec(
            "cli-coverage-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_scope_name:\n"
            "  - collaboration-cli-runtime\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-coverage-001",
            },
        )
        req = self.request_path("skill-cli-coverage.json")
        write_json(req, request)
        response = self.response_path("skill-cli-coverage.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertEqual(coverage_summary["status"], "collected")
        self.assertGreater(float(coverage_summary["line_rate_percent"]), 0.0)

    def test_cli_skill_auto_adopts_feature_owned_coverage_scope_from_testset(self) -> None:
        script_path = self.workspace / "tools" / "auto_coverage_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if case_id.endswith('U02'):\n"
            "    print('branch-u02')\n"
            "else:\n"
            "    print('branch-default')\n",
        )
        testset_ref = self.write_testset(
            "auto-coverage-testset.yaml",
            "id: TESTSET-AUTO-COVERAGE\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-AUTO-COVERAGE\n"
            "title: Auto Coverage Test Set\n"
            "feat_ref: FEAT-AUTO-COVERAGE\n"
            "recommended_coverage_scope_name:\n"
            "  - auto feature scope\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-AUTO-COVERAGE-U01\n"
            "    title: first branch\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n"
            "  - unit_ref: TESTSET-AUTO-COVERAGE-U02\n"
            "    title: second branch\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-auto-coverage-env.yaml",
            "execution_modality: cli\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-auto-coverage-001",
            },
        )
        req = self.request_path("skill-cli-auto-coverage.json")
        write_json(req, request)
        response = self.response_path("skill-cli-auto-coverage.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=2, expected_status="completed")
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertEqual(coverage_summary["status"], "collected")
        self.assertEqual(coverage_summary["scope"], ["auto feature scope"])
        self.assertEqual(coverage_summary["scope_origin"], "test_set.feature_owned_code_paths")
        self.assertEqual(coverage_summary["include"], [script_path.as_posix()])
        report_text = self.resolve_ref(payload["test_report_ref"]).read_text(encoding="utf-8")
        self.assertIn("coverage_scope_origin: test_set.feature_owned_code_paths", report_text)

    def test_cli_skill_ranks_coverage_details_expansion_targets_by_file_gap(self) -> None:
        coverage_ref = "artifacts/active/qa/executions/seed-ranking/coverage-details.json"
        details = {
            "meta": {"format": 3, "version": "7.13.5", "timestamp": "2026-03-31T00:00:00", "branch_coverage": True, "show_contexts": False},
            "files": {
                "pkg\\main.py": {
                    "missing_lines": [10],
                    "missing_branches": ["10->11"],
                    "summary": {"percent_covered": 90.0},
                },
                "pkg\\helper.py": {
                    "missing_lines": [3, 5, 7],
                    "missing_branches": ["3->4", "5->6"],
                    "summary": {"percent_covered": 40.0},
                },
            },
            "totals": {"covered_lines": 0, "num_statements": 0, "missing_lines": 0, "percent_covered": 0.0},
        }
        write_json(self.workspace / coverage_ref, details)
        targets = _coverage_expansion_targets(self.workspace, {"coverage_details_ref": coverage_ref})
        self.assertGreaterEqual(len(targets), 4)
        self.assertEqual(targets[:4], [
            "helper-missing-branch-3-to-4",
            "helper-missing-branch-5-to-6",
            "helper-missing-line-3",
            "helper-missing-line-5",
        ])

    def test_cli_skill_collects_branch_coverage_when_enabled_for_python_script(self) -> None:
        script_path = self.workspace / "tools" / "branch_coverage_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if case_id.endswith('U02'):\n"
            "    print('branch-u02')\n"
            "else:\n"
            "    print('branch-default')\n",
        )
        testset_ref = self.write_testset(
            "branch-coverage-testset.yaml",
            "id: TESTSET-BRANCH-COVERAGE\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-BRANCH-COVERAGE\n"
            "title: Branch Coverage Test Set\n"
            "feat_ref: FEAT-BRANCH-COVERAGE\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-BRANCH-COVERAGE-U01\n"
            "    title: first branch\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n"
            "  - unit_ref: TESTSET-BRANCH-COVERAGE-U02\n"
            "    title: second branch\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-branch-coverage-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_branch_enabled: true\n"
            "coverage_scope_name:\n"
            "  - branch scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-branch-coverage-001",
            },
        )
        req = self.request_path("skill-cli-branch-coverage.json")
        write_json(req, request)
        response = self.response_path("skill-cli-branch-coverage.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=2, expected_status="completed")
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertTrue(coverage_summary["branch_coverage"])
        self.assertIsNotNone(coverage_summary["branch_rate_percent"])
        self.assertGreaterEqual(float(coverage_summary["branch_rate_percent"]), 0.0)

    def test_cli_skill_rejects_testset_that_embeds_execution_artifacts(self) -> None:
        script_path = self.workspace / "tools" / "boundary_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "print(os.environ['LEE_TEST_CASE_ID'])\n",
        )
        testset_ref = self.write_testset(
            "boundary-testset.yaml",
            "id: TESTSET-BOUNDARY\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-BOUNDARY\n"
            "title: Boundary Test Set\n"
            "feat_ref: FEAT-BOUNDARY\n"
            "test_case_pack:\n"
            "  artifact_type: test_case_pack\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-BOUNDARY-U01\n"
            "    title: boundary unit\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-boundary-env.yaml",
            "execution_modality: cli\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-boundary-001",
            },
        )
        req = self.request_path("skill-cli-boundary.json")
        write_json(req, request)
        response = self.response_path("skill-cli-boundary.response.json")
        self.assertNotEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")
        self.assertIn("must not embed execution artifacts", payload["message"])

    def test_cli_skill_expands_case_pack_when_qualification_budget_and_hints_are_present(self) -> None:
        script_path = self.workspace / "tools" / "qualification_expand_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "print(os.environ['LEE_TEST_CASE_ID'])\n",
        )
        testset_ref = self.write_testset(
            "qualification-expand-testset.yaml",
            "id: TESTSET-QUALIFICATION-EXPAND\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-QUALIFICATION-EXPAND\n"
            "title: Qualification Expansion Test Set\n"
            "feat_ref: FEAT-QUALIFICATION-EXPAND\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - gate-decision-types\n"
            "  - dispatch-target-variants\n"
            "expansion_hints:\n"
            "  - qualification should expand branch families\n"
            "qualification_budget: 3\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-QUALIFICATION-EXPAND-U01\n"
            "    title: qualification base unit\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-qualification-expand-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_scope_name:\n"
            "  - qualification expansion scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "qualification_budget: 3\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-qualification-expand-001",
            },
        )
        req = self.request_path("skill-cli-qualification-expand.json")
        write_json(req, request)
        response = self.response_path("skill-cli-qualification-expand.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=3, expected_status="completed")
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["projection_mode"], "qualification_expansion")
        self.assertEqual(test_case_pack["qualification_plan"]["qualification_budget"], 3)
        self.assertEqual(len(test_case_pack["cases"]), 3)
        self.assertEqual(sum(1 for case in test_case_pack["cases"] if case["derivation_basis"] == "qualification_expansion"), 2)
        self.assertTrue(any("-EXP-R1-" in case["case_id"] for case in test_case_pack["cases"]))

    def test_cli_skill_marks_qualification_projection_mode_and_strategy_hints(self) -> None:
        script_path = self.workspace / "tools" / "mode_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "print(case_id)\n",
        )
        testset_ref = self.write_testset(
            "mode-testset.yaml",
            "id: TESTSET-MODE\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-MODE\n"
            "title: Mode Test Set\n"
            "feat_ref: FEAT-MODE\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - gate-decision-types\n"
            "expansion_hints:\n"
            "  - qualification should expand branch families\n"
            "qualification_expectation: expand until coverage target or budget is exhausted\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-MODE-U01\n"
            "    title: mode unit\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-mode-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_scope_name:\n"
            "  - mode scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-mode-001",
            },
        )
        req = self.request_path("skill-cli-mode.json")
        write_json(req, request)
        response = self.response_path("skill-cli-mode.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["projection_mode"], "qualification_expansion")
        self.assertEqual(test_case_pack["generation_mode"], "qualification_expansion")
        self.assertEqual(test_case_pack["expansion_round"], 1)
        self.assertEqual(test_case_pack["qualification_plan"]["coverage_mode"], "qualification")
        resolved = yaml.safe_load(self.resolve_ref(payload["resolved_ssot_context_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(resolved["coverage_goal"], {"line_rate_percent": 101})
        self.assertEqual(resolved["branch_families"], ["gate-decision-types"])
        self.assertEqual(resolved["expansion_hints"], ["qualification should expand branch families"])
        self.assertEqual(resolved["qualification_expectation"], "expand until coverage target or budget is exhausted")

    def test_cli_skill_qualification_feedback_loop_preserves_lineage(self) -> None:
        script_path = self.workspace / "tools" / "feedback_loop_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if 'EXP' in case_id:\n"
            "    print('expansion-branch')\n"
            "else:\n"
            "    print('minimal-branch')\n",
        )
        testset_ref = self.write_testset(
            "feedback-loop-testset.yaml",
            "id: TESTSET-FEEDBACK-LOOP\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-FEEDBACK-LOOP\n"
            "title: Feedback Loop Test Set\n"
            "feat_ref: FEAT-FEEDBACK-LOOP\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - branch-family-a\n"
            "expansion_hints:\n"
            "  - branch-hint-a\n"
            "qualification_expectation: expand minimal projection once coverage is below target\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-FEEDBACK-LOOP-U01\n"
            "    title: minimal branch\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-feedback-loop-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_scope_name:\n"
            "  - feedback loop scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-feedback-loop-001",
            },
        )
        req = self.request_path("skill-cli-feedback-loop.json")
        write_json(req, request)
        response = self.response_path("skill-cli-feedback-loop.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=2, expected_status="completed")
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["projection_mode"], "qualification_expansion")
        self.assertEqual(test_case_pack["expansion_round"], 1)
        self.assertEqual(test_case_pack["qualification_budget"], 1)
        self.assertEqual(test_case_pack["qualification_lineage"][0]["projection_mode"], "minimal_projection")
        self.assertEqual(test_case_pack["qualification_lineage"][0]["round"], 0)
        self.assertEqual(len(test_case_pack["cases"]), 2)
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["projection_mode"], "qualification_expansion")
        self.assertEqual(summary["expansion_round"], 1)
        self.assertEqual(summary["qualification_budget"], 1)
        self.assertEqual(summary["qualification_lineage"][0]["projection_mode"], "minimal_projection")
        self.assertEqual(summary["qualification_lineage"][0]["round"], 0)
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertEqual(coverage_summary["status"], "collected")
        self.assertGreater(float(coverage_summary["line_rate_percent"]), 80.0)

    def test_cli_skill_collects_branch_coverage_when_enabled(self) -> None:
        script_path = self.workspace / "tools" / "branch_coverage_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if case_id.endswith('U01'):\n"
            "    print('branch-one')\n"
            "else:\n"
            "    print('branch-two')\n",
        )
        testset_ref = self.write_testset(
            "branch-coverage-testset.yaml",
            "id: TESTSET-BRANCH-COVERAGE\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-BRANCH-COVERAGE\n"
            "title: Branch Coverage Test Set\n"
            "feat_ref: FEAT-BRANCH-COVERAGE\n"
            "coverage_goal:\n"
            "  line_rate_percent: 100\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-BRANCH-COVERAGE-U01\n"
            "    title: branch case one\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n"
            "  - unit_ref: TESTSET-BRANCH-COVERAGE-U02\n"
            "    title: branch case two\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-branch-coverage-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_branch_enabled: true\n"
            "coverage_scope_name:\n"
            "  - branch coverage scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-branch-coverage-001",
            },
        )
        req = self.request_path("skill-cli-branch-coverage.json")
        write_json(req, request)
        response = self.response_path("skill-cli-branch-coverage.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=2, expected_status="completed")
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertTrue(coverage_summary["branch_coverage"])
        self.assertGreaterEqual(int(coverage_summary["num_branches"]), 1)
        self.assertIsNotNone(coverage_summary["branch_rate_percent"])

    def test_cli_skill_uses_branch_derived_seed_for_expansion_when_branch_coverage_is_enabled(self) -> None:
        script_path = self.workspace / "tools" / "branch_seed_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if case_id.endswith('U01'):\n"
            "    print('branch-one')\n"
            "else:\n"
            "    print('branch-two')\n",
        )
        testset_ref = self.write_testset(
            "branch-seed-testset.yaml",
            "id: TESTSET-BRANCH-SEED\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-BRANCH-SEED\n"
            "title: Branch Seed Test Set\n"
            "feat_ref: FEAT-BRANCH-SEED\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - fallback-family\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 1\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-BRANCH-SEED-U01\n"
            "    title: branch seed unit\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-branch-seed-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_branch_enabled: true\n"
            "coverage_scope_name:\n"
            "  - branch seed scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 1\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-branch-seed-001",
            },
        )
        req = self.request_path("skill-cli-branch-seed.json")
        write_json(req, request)
        response = self.response_path("skill-cli-branch-seed.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=2, expected_status="completed")
        coverage_summary = read_json(self.resolve_ref(payload["coverage_summary_ref"]))
        self.assertTrue(coverage_summary["branch_coverage"])
        self.assertGreaterEqual(int(coverage_summary["num_branches"]), 1)
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertIn("missing-branch", test_case_pack["cases"][1]["case_id"])
        self.assertIn("missing-branch", str(test_case_pack["cases"][1]["qualification_family"]))
        self.assertNotIn("fallback-family", test_case_pack["cases"][1]["case_id"])

    def test_cli_skill_keeps_branch_derived_targets_when_later_round_has_no_new_gap(self) -> None:
        script_path = self.workspace / "tools" / "branch_priority_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if 'missing-branch' in case_id:\n"
            "    print('branch-seed-case')\n"
            "elif case_id.endswith('U02'):\n"
            "    print('branch-two')\n"
            "else:\n"
            "    print('branch-one')\n",
        )
        testset_ref = self.write_testset(
            "branch-priority-testset.yaml",
            "id: TESTSET-BRANCH-PRIORITY\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-BRANCH-PRIORITY\n"
            "title: Branch Priority Test Set\n"
            "feat_ref: FEAT-BRANCH-PRIORITY\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - fallback-family\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 2\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-BRANCH-PRIORITY-U01\n"
            "    title: branch case one\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n"
            "  - unit_ref: TESTSET-BRANCH-PRIORITY-U02\n"
            "    title: branch case two\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-branch-priority-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_branch_enabled: true\n"
            "coverage_scope_name:\n"
            "  - branch priority scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 2\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-branch-priority-001",
            },
        )
        req = self.request_path("skill-cli-branch-priority.json")
        write_json(req, request)
        response = self.response_path("skill-cli-branch-priority.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=4, expected_status="completed")
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["expansion_round"], 2)
        self.assertTrue(any("missing-branch" in case["case_id"] for case in test_case_pack["cases"]))
        self.assertFalse(any(case["case_id"].endswith("fallback-family") for case in test_case_pack["cases"]))

    def test_cli_skill_orders_coverage_expansion_targets_by_file_score_and_priority(self) -> None:
        details_path = self.workspace / "artifacts" / "coverage-details.json"
        summary_path = self.workspace / "artifacts" / "coverage-summary.json"
        beta_path = self.workspace / "src" / "beta.py"
        delta_path = self.workspace / "src" / "delta.py"
        alpha_path = self.workspace / "src" / "alpha.py"
        gamma_path = self.workspace / "src" / "gamma.py"
        write_json(
            details_path,
            {
                "files": {
                    "src/alpha.py": {
                        "missing_lines": [3, 5, 7],
                        "summary": {"percent_covered": 60.0},
                    },
                    "src/beta.py": {
                        "missing_lines": [1, 2],
                        "summary": {"percent_covered": 80.0},
                    },
                    "src/delta.py": {
                        "missing_lines": [4, 6],
                        "summary": {"percent_covered": 80.0},
                    },
                    "src/gamma.py": {
                        "missing_lines": [9],
                        "summary": {"percent_covered": 90.0},
                    },
                }
            },
        )
        write_json(
            summary_path,
            {
                "include": [
                    beta_path.as_posix(),
                    delta_path.as_posix(),
                    alpha_path.as_posix(),
                    gamma_path.as_posix(),
                ]
            },
        )
        refs = {
            "coverage_details_ref": str(details_path),
            "coverage_summary_ref": str(summary_path),
        }
        targets = _coverage_expansion_targets(self.workspace, refs)
        self.assertEqual(
            targets[:6],
            [
                "alpha-missing-line-3",
                "alpha-missing-line-5",
                "alpha-missing-line-7",
                "beta-missing-line-1",
                "beta-missing-line-2",
                "delta-missing-line-4",
            ],
        )

    def test_cli_skill_prefers_matching_test_unit_for_expansion_source(self) -> None:
        script_path = self.workspace / "tools" / "checkout_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if 'U02' in case_id:\n"
            "    print('checkout-branch')\n"
            "else:\n"
            "    print('report-branch')\n",
        )
        testset_ref = self.write_testset(
            "unit-selector-testset.yaml",
            "id: TESTSET-UNIT-SELECTOR\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-UNIT-SELECTOR\n"
            "title: Unit Selector Test Set\n"
            "feat_ref: FEAT-UNIT-SELECTOR\n"
            "coverage_goal:\n"
            "  line_rate_percent: 101\n"
            "branch_families:\n"
            "  - checkout-flow\n"
            "qualification_budget: 3\n"
            "max_expansion_rounds: 1\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-UNIT-SELECTOR-U01\n"
            "    title: report branch unit\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    page_path: /reports\n"
            "    expected_text: summary\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n"
            "  - unit_ref: TESTSET-UNIT-SELECTOR-U02\n"
            "    title: checkout branch unit\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    page_path: /checkout\n"
            "    expected_text: checkout\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-unit-selector-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_scope_name:\n"
            "  - unit selector scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "qualification_budget: 3\n"
            "max_expansion_rounds: 1\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-unit-selector-001",
            },
        )
        req = self.request_path("skill-cli-unit-selector.json")
        write_json(req, request)
        response = self.response_path("skill-cli-unit-selector.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=3, expected_status="completed")
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["projection_mode"], "qualification_expansion")
        self.assertEqual(test_case_pack["qualification_round"], 1)
        self.assertTrue(test_case_pack["cases"][2]["case_id"].startswith("TESTSET-UNIT-SELECTOR-U02-EXP-R1-checkout-flow"))
        self.assertEqual(test_case_pack["cases"][2]["qualification_family"], "checkout-flow")

    def test_cli_skill_qualification_feedback_loop_can_expand_multiple_rounds(self) -> None:
        script_path = self.workspace / "tools" / "feedback_loop_multi_round_target.py"
        write_yaml(
            script_path,
            "import os\n"
            "case_id = os.environ['LEE_TEST_CASE_ID']\n"
            "if 'EXP-R2' in case_id:\n"
            "    print('round-two-branch')\n"
            "elif 'EXP-R1' in case_id:\n"
            "    print('round-one-branch')\n"
            "else:\n"
            "    print('minimal-branch')\n",
        )
        testset_ref = self.write_testset(
            "feedback-loop-multi-round-testset.yaml",
            "id: TESTSET-FEEDBACK-LOOP-MULTI\n"
            "ssot_type: TESTSET\n"
            "test_set_id: TESTSET-FEEDBACK-LOOP-MULTI\n"
            "title: Feedback Loop Multi Round Test Set\n"
            "feat_ref: FEAT-FEEDBACK-LOOP-MULTI\n"
            "coverage_goal:\n"
            "  line_rate_percent: 100\n"
            "branch_families:\n"
            "  - branch-family-a\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 2\n"
            "feature_owned_code_paths:\n"
            f"  - {script_path.as_posix()}\n"
            "test_units:\n"
            "  - unit_ref: TESTSET-FEEDBACK-LOOP-MULTI-U01\n"
            "    title: minimal branch\n"
            "    priority: P0\n"
            "    input_preconditions: []\n"
            "    trigger_action: run\n"
            "    pass_conditions:\n"
            "      - exits successfully\n"
            "    fail_conditions: []\n"
            "    required_evidence:\n"
            "      - stdout\n",
        )
        env_ref = self.write_env_spec(
            "cli-feedback-loop-multi-round-env.yaml",
            "execution_modality: cli\n"
            "coverage_mode: qualification\n"
            "coverage_enabled: true\n"
            "coverage_scope_name:\n"
            "  - feedback loop multi round scope\n"
            "coverage_include:\n"
            f"  - {script_path.as_posix()}\n"
            "qualification_budget: 2\n"
            "max_expansion_rounds: 2\n"
            "command_entry: >-\n"
            f"  {python_file_command(script_path)}\n"
            "workdir: .\n",
        )
        request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": testset_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-cli-feedback-loop-multi-round-001",
            },
        )
        req = self.request_path("skill-cli-feedback-loop-multi-round.json")
        write_json(req, request)
        response = self.response_path("skill-cli-feedback-loop-multi-round.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=2, expected_status="completed")
        test_case_pack = yaml.safe_load(self.resolve_ref(payload["test_case_pack_ref"]).read_text(encoding="utf-8"))
        self.assertEqual(test_case_pack["projection_mode"], "qualification_expansion")
        self.assertEqual(test_case_pack["expansion_round"], 2)
        self.assertEqual(test_case_pack["qualification_max_expansion_rounds"], 2)
        self.assertEqual(len(test_case_pack["qualification_lineage"]), 3)
        self.assertEqual(test_case_pack["qualification_lineage"][2]["round"], 2)
        self.assertEqual(test_case_pack["qualification_lineage"][2]["projection_mode"], "qualification_expansion")
        self.assertIn("-EXP-R2-", test_case_pack["cases"][1]["case_id"])
        self.assertIn("feedback-loop-multi-round-target-missing-line-", test_case_pack["cases"][1]["case_id"])
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["expansion_round"], 2)
        self.assertEqual(summary["expansion_stop_reason"], "qualification_budget_exhausted")
        self.assertEqual(len(summary["qualification_lineage"]), 3)
