from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from cli.ll import main


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def python_command(script: str) -> str:
    return f"\"{sys.executable}\" -c \"{script}\""


def python_file_command(path: Path) -> str:
    return f"\"{sys.executable}\" \"{path}\""


class TestExecSkillRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)
        self.repo_root = Path(__file__).resolve().parents[2]

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request_path(self, name: str) -> Path:
        return self.workspace / "contracts" / "input" / name

    def response_path(self, name: str) -> Path:
        return self.workspace / "artifacts" / "active" / name

    def build_request(self, command: str, payload: dict) -> dict:
        return {
            "api_version": "v1",
            "command": command,
            "request_id": f"req-{command.replace('.', '-')}",
            "workspace_root": self.workspace.as_posix(),
            "actor_ref": "test-suite",
            "trace": {"run_ref": "RUN-TEST-EXEC"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def feat_testset_path(self, feat_id: str) -> str:
        return str(
            self.repo_root
            / "artifacts"
            / "feat-to-testset"
            / f"adr007-qa-test-execution-20260325-rerun1--feat-src-adr007-qa-test-execution-20260325-rerun1-{feat_id}"
            / "test-set.yaml"
        )

    def write_env_spec(self, name: str, content: str) -> str:
        path = self.workspace / "ssot" / "test-env" / name
        write_yaml(path, content)
        return path.as_posix()

    def write_testset(self, name: str, content: str) -> str:
        path = self.workspace / "ssot" / "testset" / name
        write_yaml(path, content)
        return path.as_posix()

    def write_fake_playwright_scripts(self, case_ids: list[str] | None = None) -> tuple[Path, Path]:
        case_ids = case_ids or [
            "TS-SRC-ADR007-QA-TEST-EXECUTION-20260325-RERUN1-001-U01",
            "TS-SRC-ADR007-QA-TEST-EXECUTION-20260325-RERUN1-001-U02",
            "TS-SRC-ADR007-QA-TEST-EXECUTION-20260325-RERUN1-001-U03",
        ]
        tools_root = self.workspace / "tools"
        npm_script = tools_root / "fake_npm.py"
        playwright_script = tools_root / "fake_playwright.py"
        write_yaml(
            npm_script,
            "from pathlib import Path\n"
            "root = Path.cwd() / 'node_modules' / '@playwright' / 'test'\n"
            "root.mkdir(parents=True, exist_ok=True)\n"
            "print('fake npm install complete')\n",
        )
        write_yaml(
            playwright_script,
            "import json\n"
            "from pathlib import Path\n"
            "root = Path.cwd()\n"
            "artifacts = root / 'artifacts'\n"
            "report_dir = artifacts / 'test-results' / 'case-1'\n"
            "report_dir.mkdir(parents=True, exist_ok=True)\n"
            "shot = report_dir / 'final.png'\n"
            "shot.write_bytes(b'png')\n"
            f"case_ids = {json.dumps(case_ids, ensure_ascii=False)}\n"
            "specs = []\n"
            "for index, case_id in enumerate(case_ids):\n"
            "  attachments = [{'path': str(shot)}] if index == 0 else []\n"
            "  specs.append({\n"
            "    'title': f'[{case_id}] case {index + 1}',\n"
            "    'tests': [{'results': [{'status': 'passed', 'attachments': attachments, 'errors': []}]}],\n"
            "  })\n"
            "results = {'suites': [{'specs': specs, 'suites': []}]}\n"
            "(artifacts / 'html-report').mkdir(parents=True, exist_ok=True)\n"
            "(artifacts / 'results.json').write_text(json.dumps(results), encoding='utf-8')\n"
            "print('fake playwright complete')\n",
        )
        return npm_script, playwright_script

    def resolve_ref(self, ref_value: str) -> Path:
        path = Path(ref_value)
        return path if path.is_absolute() else self.workspace / path

    def assert_execution_outputs(self, payload: dict, expected_cases: int, expected_status: str) -> None:
        self.assertEqual(payload["run_status"], expected_status)
        for key in (
            "resolved_ssot_context_ref",
            "ui_intent_ref",
            "ui_binding_map_ref",
            "test_case_pack_ref",
            "test_case_pack_meta_ref",
            "script_pack_ref",
            "script_pack_meta_ref",
            "raw_runner_output_ref",
            "compliance_result_ref",
            "case_results_ref",
            "results_summary_ref",
            "evidence_bundle_ref",
            "test_report_ref",
            "output_validation_ref",
            "tse_ref",
        ):
            self.assertTrue(self.resolve_ref(payload[key]).exists(), key)
        case_results = read_json(self.resolve_ref(payload["case_results_ref"]))
        self.assertEqual(len(case_results["results"]), expected_cases)
        self.assertEqual(len([item for item in case_results["results"] if item["status"]]), expected_cases)
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["run_status"], expected_status)
        compliance = read_json(self.resolve_ref(payload["compliance_result_ref"]))
        self.assertEqual(compliance["status"], "pass")
        ui_intent = read_json(self.resolve_ref(payload["ui_intent_ref"]))
        self.assertEqual(len(ui_intent["cases"]), expected_cases)
        ui_binding_map = read_json(self.resolve_ref(payload["ui_binding_map_ref"]))
        self.assertEqual(len(ui_binding_map["cases"]), expected_cases)
        output_validation = read_json(self.resolve_ref(payload["output_validation_ref"]))
        self.assertEqual(output_validation["status"], "pass")
        tse = read_json(self.resolve_ref(payload["tse_ref"]))
        self.assertEqual(tse["run_status"], expected_status)
        self.assertEqual(tse["acceptance_status"], "not_reviewed")
        self.assertEqual(tse["output_validation_ref"], payload["output_validation_ref"])
        report_path = self.resolve_ref(payload["test_report_ref"])
        self.assertTrue(report_path.exists())
        candidate = read_json(self.resolve_ref(payload["candidate_managed_artifact_ref"]))
        self.assertEqual(candidate["run_status"], expected_status)
        self.assertEqual(candidate["tse_ref"], payload["tse_ref"])
        self.assertEqual(candidate["compliance_result_ref"], payload["compliance_result_ref"])

    def test_web_skill_emits_candidate_and_handoff_with_real_testset(self) -> None:
        npm_script, playwright_script = self.write_fake_playwright_scripts()
        env_ref = self.write_env_spec(
            "web-env.yaml",
            "execution_modality: web_e2e\n"
            "base_url: https://example.test\n"
            "browser: chromium\n"
            "headless: true\n"
            "workdir: .\n"
            "npm_command: >-\n"
            f"  {python_file_command(npm_script)}\n"
            "playwright_command: >-\n"
            f"  {python_file_command(playwright_script)}\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {
                "test_set_ref": self.feat_testset_path("001"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-web-001",
            },
        )
        req = self.request_path("skill-web.json")
        write_json(req, request)
        response = self.response_path("skill-web.response.json")
        self.assertEqual(
            self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)
        self.assertEqual(payload["data"]["skill_ref"], "skill.qa.test_exec_web_e2e")
        self.assertTrue(payload["data"]["candidate_managed_artifact_ref"].startswith("artifacts/active/qa/candidates/"))
        self.assertEqual(payload["data"]["pending_state"], "gate_pending")
        self.assert_execution_outputs(payload["data"], expected_cases=3, expected_status="completed")
        ui_intent = read_json(self.resolve_ref(payload["data"]["ui_intent_ref"]))
        self.assertTrue(all(item["derivation_mode"] in {"governance_inferred", "fallback_smoke"} for item in ui_intent["cases"]))
        ui_binding_map = read_json(self.resolve_ref(payload["data"]["ui_binding_map_ref"]))
        self.assertTrue(all(item["resolution_status"] in {"partial", "fallback_smoke", "resolved"} for item in ui_binding_map["cases"]))
        script_pack = read_json(self.resolve_ref(payload["data"]["script_pack_ref"]))
        self.assertEqual(script_pack["framework"], "playwright")
        spec_file = self.resolve_ref(script_pack["project_refs"]["spec_file_ref"])
        self.assertIn("@playwright/test", spec_file.read_text(encoding="utf-8"))
        self.assertIn("expect(page.locator('body')).toBeVisible()", spec_file.read_text(encoding="utf-8"))

    def test_web_skill_renders_explicit_ui_steps_into_playwright_spec(self) -> None:
        case_id = "TS-WEB-UI-001-U01"
        npm_script, playwright_script = self.write_fake_playwright_scripts([case_id])
        test_set_ref = self.write_testset(
            "web-ui-testset.yaml",
            "ssot_type: TESTSET\n"
            "test_set_id: TS-WEB-UI-001\n"
            "title: Web UI translator test set\n"
            "feat_ref: FEAT-WEB-UI-001\n"
            "epic_ref: EPIC-WEB-UI-001\n"
            "src_ref: SRC-WEB-UI-001\n"
            "test_units:\n"
            f"- unit_ref: {case_id}\n"
            "  title: Login flow with explicit ui steps\n"
            "  priority: P0\n"
            "  page_path: /login\n"
            "  expected_url: /dashboard\n"
            "  expected_text: Welcome back\n"
            "  selectors:\n"
            "    email_input:\n"
            "      testid: login-email\n"
            "    password_input: input[name='password']\n"
            "    primary_action:\n"
            "      role: button\n"
            "      name: Sign in\n"
            "  ui_steps:\n"
            "  - action: goto\n"
            "    path: /login\n"
            "  - action: fill\n"
            "    target: email_input\n"
            "    value: user@example.com\n"
            "  - action: fill\n"
            "    target: password_input\n"
            "    value: secret\n"
            "  - action: click\n"
            "    target: primary_action\n"
            "  - action: assert_text\n"
            "    text: Welcome back\n",
        )
        env_ref = self.write_env_spec(
            "web-ui-env.yaml",
            "execution_modality: web_e2e\n"
            "base_url: https://example.test\n"
            "browser: chromium\n"
            "headless: true\n"
            "workdir: .\n"
            "npm_command: >-\n"
            f"  {python_file_command(npm_script)}\n"
            "playwright_command: >-\n"
            f"  {python_file_command(playwright_script)}\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {
                "test_set_ref": test_set_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-web-ui-001",
            },
        )
        req = self.request_path("skill-web-ui.json")
        write_json(req, request)
        response = self.response_path("skill-web-ui.response.json")
        self.assertEqual(
            self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=1, expected_status="completed")
        binding_map = read_json(self.resolve_ref(payload["ui_binding_map_ref"]))
        self.assertEqual(binding_map["cases"][0]["resolution_status"], "resolved")
        self.assertEqual(binding_map["cases"][0]["unresolved_targets"], [])
        script_pack = read_json(self.resolve_ref(payload["script_pack_ref"]))
        spec_text = self.resolve_ref(script_pack["project_refs"]["spec_file_ref"]).read_text(encoding="utf-8")
        self.assertIn("case 'fill':", spec_text)
        self.assertIn('"testid": "login-email"', spec_text)
        self.assertIn("\"selector\": \"input[name='password']\"", spec_text)
        self.assertIn('"semantic_target": "primary_action"', spec_text)
        self.assertIn('"expectedUrl": "/dashboard"', spec_text)
        self.assertIn('"expectedText": "Welcome back"', spec_text)
        self.assertIn("expect(page.url()).toContain(String(item.expectedUrl))", spec_text)

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
        self.assertEqual(
            self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)),
            0,
        )
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
        self.assertEqual(
            self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=5, expected_status="completed_with_failures")
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["failed"], 1)
        bug_index = read_json(self.resolve_ref(payload["bug_bundle_ref"]))
        self.assertEqual(len(bug_index["bugs"]), 1)
        self.assertTrue(bug_index["bugs"][0]["case_id"].endswith("U03"))

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
        self.assertEqual(
            self.run_cli("skill", "test-exec-cli", "--request", str(req), "--response-out", str(response)),
            0,
        )
        payload = read_json(response)["data"]
        self.assert_execution_outputs(payload, expected_cases=5, expected_status="completed_with_warnings")
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["blocked"], 5)
        self.assertEqual(summary["failed"], 0)

    def test_cli_skill_pilot_integration_flow(self) -> None:
        command = python_command(
            "import os; "
            "assert os.environ['LEE_EXECUTION_MODALITY'] == 'cli'; "
            "print(os.environ['LEE_TEST_CASE_ID'])"
        )
        env_ref = self.write_env_spec(
            "cli-pilot-env.yaml",
            "execution_modality: cli\n"
            "command_entry: >-\n"
            f"  {command}\n"
            "workdir: .\n",
        )

        onboard_request = self.build_request(
            "rollout.onboard-skill",
            {
                "skill_ref": "skill.qa.test_exec_cli",
                "wave_id": "wave-pilot-01",
                "scope": "pilot",
                "compat_mode": True,
                "foundation_ready": True,
            },
        )
        onboard_req = self.request_path("pilot-onboard.json")
        write_json(onboard_req, onboard_request)
        onboard_response = self.response_path("pilot-onboard.response.json")
        self.assertEqual(
            self.run_cli("rollout", "onboard-skill", "--request", str(onboard_req), "--response-out", str(onboard_response)),
            0,
        )

        skill_request = self.build_request(
            "skill.test-exec-cli",
            {
                "test_set_ref": self.feat_testset_path("005"),
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-pilot-005",
            },
        )
        skill_req = self.request_path("pilot-skill.json")
        write_json(skill_req, skill_request)
        skill_response = self.response_path("pilot-skill.response.json")
        self.assertEqual(
            self.run_cli("skill", "test-exec-cli", "--request", str(skill_req), "--response-out", str(skill_response)),
            0,
        )
        skill_payload = read_json(skill_response)["data"]
        self.assert_execution_outputs(skill_payload, expected_cases=5, expected_status="completed")

        decide_request = self.build_request(
            "gate.decide",
            {
                "handoff_ref": skill_payload["handoff_ref"],
                "proposal_ref": "proposal-pilot-005",
                "decision": "approve",
            },
        )
        decide_req = self.request_path("pilot-decide.json")
        write_json(decide_req, decide_request)
        decide_response = self.response_path("pilot-decide.response.json")
        self.assertEqual(
            self.run_cli("gate", "decide", "--request", str(decide_req), "--response-out", str(decide_response)),
            0,
        )
        decision_payload = read_json(decide_response)["data"]

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": decision_payload["gate_decision_ref"],
                "candidate_ref": skill_payload["candidate_artifact_ref"],
                "target_formal_kind": "pilot-report",
            },
        )
        materialize_req = self.request_path("pilot-materialize.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("pilot-materialize.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )
        materialize_payload = read_json(materialize_response)["data"]

        admission_request = self.build_request(
            "registry.validate-admission",
            {"consumer_ref": "skill.qa.test_exec_cli.consumer", "requested_ref": materialize_payload["formal_ref"]},
        )
        admission_req = self.request_path("pilot-admission.json")
        write_json(admission_req, admission_request)
        admission_response = self.response_path("pilot-admission.response.json")
        self.assertEqual(
            self.run_cli("registry", "validate-admission", "--request", str(admission_req), "--response-out", str(admission_response)),
            0,
        )

        audit_request = self.build_request(
            "audit.emit-finding-bundle",
            {
                "workspace_diff_ref": "artifacts/active/diff.json",
                "gateway_receipt_refs": [skill_payload["candidate_receipt_ref"]],
                "registry_refs": [skill_payload["candidate_registry_record_ref"]],
                "policy_verdict_refs": [skill_payload["candidate_receipt_ref"]],
                "attempted_unmanaged_reads": [],
                "bypass_write_paths": [],
            },
        )
        audit_req = self.request_path("pilot-audit.json")
        write_json(audit_req, audit_request)
        audit_response = self.response_path("pilot-audit.response.json")
        self.assertEqual(
            self.run_cli("audit", "emit-finding-bundle", "--request", str(audit_req), "--response-out", str(audit_response)),
            0,
        )
        audit_payload = read_json(audit_response)["data"]

        pilot_request = self.build_request(
            "audit.submit-pilot-evidence",
            {
                "pilot_chain_ref": self.feat_testset_path("005"),
                "producer_ref": skill_payload["skill_ref"],
                "consumer_ref": "skill.qa.test_exec_cli.consumer",
                "audit_ref": audit_payload["finding_bundle_ref"],
                "gate_ref": decision_payload["gate_decision_ref"],
            },
        )
        pilot_req = self.request_path("pilot-submit-evidence.json")
        write_json(pilot_req, pilot_request)
        pilot_response = self.response_path("pilot-submit-evidence.response.json")
        self.assertEqual(
            self.run_cli("audit", "submit-pilot-evidence", "--request", str(pilot_req), "--response-out", str(pilot_response)),
            0,
        )
        pilot_payload = read_json(pilot_response)["data"]

        cutover_request = self.build_request(
            "rollout.cutover-wave",
            {"wave_id": "wave-pilot-01", "pilot_evidence_ref": pilot_payload["pilot_evidence_ref"]},
        )
        cutover_req = self.request_path("pilot-cutover.json")
        write_json(cutover_req, cutover_request)
        cutover_response = self.response_path("pilot-cutover.response.json")
        self.assertEqual(
            self.run_cli("rollout", "cutover-wave", "--request", str(cutover_req), "--response-out", str(cutover_response)),
            0,
        )
        cutover_payload = read_json(cutover_response)["data"]
        self.assertEqual(cutover_payload["readiness_label"], "cutover_guarded")


if __name__ == "__main__":
    unittest.main()
