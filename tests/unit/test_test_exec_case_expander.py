from __future__ import annotations

import unittest

from cli.lib.test_exec_case_expander import expand_requirement_cases


class TestTestExecCaseExpander(unittest.TestCase):
    def test_requirement_driven_expansion_builds_traceable_case_pack(self) -> None:
        test_set = {
            "test_set_id": "TESTSET-RUNNER-EXPAND",
            "feat_ref": "FEAT-RUNNER-EXPAND",
            "title": "Runner feedback expansion",
            "coverage_goal": {"line_rate_percent": 80},
            "branch_families": ["runner-feedback", "runner-observability"],
            "expansion_hints": ["missing-line-11", "missing-branch-claim"],
            "qualification_budget": 3,
            "max_expansion_rounds": 2,
            "risk_focus": ["retry-reentry", "authoritative outcome"],
            "functional_areas": [
                {
                    "key": "execution_runner_surface",
                    "kind": "control_surface",
                    "related_entities": ["execution_job"],
                    "related_commands": ["job.run", "job.fail"],
                    "description": "runner surface",
                }
            ],
            "logic_dimensions": {
                "universal": ["happy_path", "boundary_conditions", "invalid_input"],
                "stateful": ["valid_transition", "invalid_transition", "retry_reentry"],
                "control_surface": ["authorized_action", "rejected_action", "read_only_guard"],
            },
            "state_model": [
                {
                    "entity": "execution_job",
                    "states": ["ready", "claimed", "running", "failed"],
                    "valid_transitions": [["ready", "claimed"], ["claimed", "running"]],
                    "guarded_actions": [{"command": "job.fail", "allowed_in": ["running"], "rejected_in": ["ready"]}],
                }
            ],
            "acceptance_traceability": [
                {
                    "acceptance_ref": "AC-01",
                    "acceptance_scenario": "job reaches running state",
                    "given": "ready job exists",
                    "when": "claim and run",
                    "then": "running ownership is visible",
                    "unit_refs": ["TESTSET-RUNNER-EXPAND-U01"],
                    "coverage_status": "covered",
                }
            ],
            "test_units": [
                {
                    "unit_ref": "TESTSET-RUNNER-EXPAND-U01",
                    "title": "job reaches running state",
                    "priority": "P1",
                    "input_preconditions": ["ready job exists"],
                    "trigger_action": "run-execution",
                    "observation_points": ["running ownership visible"],
                    "pass_conditions": ["running ownership persists"],
                    "fail_conditions": ["claim conflict"],
                    "required_evidence": ["stdout"],
                    "acceptance_ref": "AC-01",
                }
            ],
        }

        case_pack = expand_requirement_cases(
            test_set,
            {"execution_modality": "cli", "coverage_mode": "qualification", "qualification_budget": 3},
            projection_mode="qualification_expansion",
            qualification_round=1,
            expansion_targets=["missing-line-11", "missing-branch-claim"],
        )

        self.assertEqual(case_pack["artifact_type"], "test_case_pack")
        self.assertEqual(case_pack["projection_mode"], "qualification_expansion")
        self.assertEqual(case_pack["qualification_round"], 1)
        self.assertEqual(case_pack["functional_areas"][0]["key"], "execution_runner_surface")
        self.assertEqual(case_pack["logic_dimensions"]["universal"], ["happy_path", "boundary_conditions", "invalid_input"])
        self.assertEqual(case_pack["state_model"][0]["entity"], "execution_job")
        self.assertGreaterEqual(len(case_pack["cases"]), 2)
        self.assertEqual(case_pack["cases"][0]["case_family"], "state_transition")
        self.assertEqual(case_pack["cases"][0]["functional_area_key"], "execution_runner_surface")
        self.assertTrue(case_pack["cases"][1]["case_id"].startswith("TESTSET-RUNNER-EXPAND-U01-EXP-R1-"))
        self.assertEqual(case_pack["cases"][1]["qualification_family"], "missing-line-11")
        self.assertEqual(case_pack["cases"][1]["derivation_basis"], "qualification_expansion")
        self.assertIn("requirement_driven_expansion", case_pack["cases"][1]["derivation_tags"])
        self.assertTrue(case_pack["coverage_matrix"]["unit_rows"])
