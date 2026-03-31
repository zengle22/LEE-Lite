from __future__ import annotations

import unittest

from cli.lib.test_exec_traceability import build_traceability_matrix, infer_functional_areas, infer_logic_dimensions, infer_state_model, trace_unit


class TestTestExecTraceability(unittest.TestCase):
    def test_build_traceability_matrix_preserves_structured_contract(self) -> None:
        test_set = {
            "test_set_id": "TESTSET-RUNNER-TRACE",
            "title": "Runner Observability Traceability",
            "feature_owned_code_paths": [
                "cli/lib/runner_monitor.py",
                "cli/commands/loop/command.py",
            ],
            "functional_areas": [
                {
                    "key": "runner_observability_surface",
                    "kind": "control_surface",
                    "related_entities": ["execution_job"],
                    "related_commands": ["loop.show-status"],
                    "description": "runner observability surface",
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
                    "states": ["ready", "running", "failed"],
                    "valid_transitions": [["ready", "running"]],
                    "guarded_actions": [{"command": "loop.show-status", "allowed_in": ["ready"], "rejected_in": []}],
                }
            ],
            "risk_focus": ["single-owner claim", "read-only monitor surface"],
            "acceptance_traceability": [
                {
                    "acceptance_ref": "AC-01",
                    "acceptance_scenario": "monitor can see backlog",
                    "given": "ready jobs exist",
                    "when": "show status",
                    "then": "status buckets are visible",
                    "unit_refs": ["TESTSET-RUNNER-TRACE-U01"],
                    "coverage_status": "covered",
                }
            ],
            "test_units": [
                {
                    "unit_ref": "TESTSET-RUNNER-TRACE-U01",
                    "title": "monitor visible status buckets",
                    "priority": "P1",
                    "input_preconditions": ["queue contains ready jobs"],
                    "trigger_action": "show-status",
                    "observation_points": ["status buckets visible"],
                    "pass_conditions": ["ready backlog visible"],
                    "fail_conditions": ["read-only guard missing"],
                    "required_evidence": ["stdout"],
                    "functional_area_key": "runner_observability_surface",
                    "case_family": "read_only_guard",
                    "acceptance_ref": "AC-01",
                }
            ],
        }

        matrix = build_traceability_matrix(test_set)
        self.assertEqual(matrix["artifact_type"], "traceability_matrix")
        self.assertEqual(matrix["functional_areas"][0]["key"], "runner_observability_surface")
        self.assertEqual(matrix["logic_dimensions"]["control_surface"], ["authorized_action", "rejected_action", "read_only_guard"])
        self.assertEqual(matrix["state_model"][0]["entity"], "execution_job")
        self.assertEqual(matrix["acceptance_rows"][0]["acceptance_ref"], "AC-01")
        self.assertTrue(matrix["acceptance_rows"][0]["covered_by_case"])
        self.assertEqual(matrix["unit_rows"][0]["case_family"], "read_only_guard")
        self.assertIn("read_only_guard", matrix["unit_rows"][0]["logic_dimensions"][0])

    def test_infer_defaults_from_runtime_shaped_testset(self) -> None:
        test_set = {
            "title": "Execution Runner 用户入口流",
            "feature_owned_code_paths": [
                "cli/lib/runner_entry.py",
                "cli/lib/execution_runner.py",
                "cli/commands/loop/command.py",
            ],
        }

        areas = infer_functional_areas(test_set)
        dims = infer_logic_dimensions(test_set)
        state_model = infer_state_model(test_set)
        unit = trace_unit(
            {
                **test_set,
                "risk_focus": ["authoritative runner context"],
            },
            {
                "unit_ref": "TESTSET-RUNNER-TRACE-U02",
                "title": "start and resume preserve context",
                "priority": "P1",
                "input_preconditions": ["runner context exists"],
                "trigger_action": "run-execution",
                "pass_conditions": ["runner_run_ref persists"],
                "fail_conditions": ["manual relay required"],
                "required_evidence": ["stdout"],
            },
        )

        self.assertEqual(areas[0]["kind"], "control_surface")
        self.assertIn("retry_reentry", dims["stateful"])
        self.assertEqual(state_model[0]["entity"], "execution_job")
        self.assertEqual(unit["functional_area_key"], "execution_runner_surface")
        self.assertEqual(unit["case_family"], "state_transition")
        self.assertIn("authoritative runner context", unit["risk_refs"])

