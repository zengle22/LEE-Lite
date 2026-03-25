from __future__ import annotations

from _test_exec_skill_support import SkillRuntimeHarness, python_command, read_json, write_json


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
