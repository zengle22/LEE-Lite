from __future__ import annotations

import unittest

from cli.lib.test_exec_case_expander import expand_requirement_cases
from cli.lib.test_exec_fixture_planner import plan_fixtures


class TestTestExecFixturePlanner(unittest.TestCase):
    def test_fixture_planner_uses_state_model_and_case_family(self) -> None:
        test_set = {
            "test_set_id": "TESTSET-FIXTURE-PLAN",
            "feat_ref": "FEAT-FIXTURE-PLAN",
            "title": "Gate fixture planning",
            "risk_focus": ["gate decision", "read-only guard"],
            "state_model": [
                {
                    "entity": "candidate_package",
                    "states": ["draft", "pending_gate", "approved", "rejected"],
                    "valid_transitions": [["draft", "pending_gate"], ["pending_gate", "approved"]],
                    "guarded_actions": [{"command": "gate.decide", "allowed_in": ["pending_gate"], "rejected_in": ["approved"]}],
                }
            ],
            "test_units": [
                {
                    "unit_ref": "TESTSET-FIXTURE-PLAN-U01",
                    "title": "gate approves candidate",
                    "priority": "P1",
                    "input_preconditions": ["candidate package exists"],
                    "trigger_action": "gate.decide",
                    "pass_conditions": ["candidate approved"],
                    "fail_conditions": ["candidate rejected"],
                    "required_evidence": ["stdout"],
                    "acceptance_ref": "AC-01",
                    "case_family": "state_transition",
                },
                {
                    "unit_ref": "TESTSET-FIXTURE-PLAN-U02",
                    "title": "monitor remains read only",
                    "priority": "P1",
                    "input_preconditions": ["candidate package exists"],
                    "trigger_action": "show-status",
                    "pass_conditions": ["read only"],
                    "fail_conditions": ["writes are blocked"],
                    "required_evidence": ["stdout"],
                    "acceptance_ref": "AC-02",
                    "case_family": "read_only_guard",
                },
            ],
            "acceptance_traceability": [
                {
                    "acceptance_ref": "AC-01",
                    "acceptance_scenario": "gate approves candidate",
                    "given": "candidate package exists",
                    "when": "decide",
                    "then": "candidate approved",
                    "unit_refs": ["TESTSET-FIXTURE-PLAN-U01"],
                    "coverage_status": "covered",
                }
            ],
        }
        case_pack = expand_requirement_cases(test_set)

        plan = plan_fixtures(test_set, case_pack, {"execution_modality": "cli", "coverage_mode": "qualification"})

        self.assertEqual(plan["artifact_type"], "fixture_plan")
        self.assertEqual(plan["state_model"][0]["entity"], "candidate_package")
        self.assertEqual(plan["fixtures"][0]["required_state"], "approved")
        self.assertEqual(plan["fixtures"][1]["required_state"], "draft")
        self.assertEqual(plan["fixtures"][1]["case_family"], "read_only_guard")
        self.assertIn("read only", " ".join(plan["fixtures"][1]["boundary_checks"]))
