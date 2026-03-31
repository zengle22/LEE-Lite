from __future__ import annotations

import unittest

from cli.lib.test_exec_case_expander import expand_requirement_cases
from cli.lib.test_exec_script_mapper import map_scripts


class TestTestExecScriptMapper(unittest.TestCase):
    def test_script_mapper_preserves_command_entry_and_case_family(self) -> None:
        test_set = {
            "test_set_id": "TESTSET-SCRIPT-MAP",
            "feat_ref": "FEAT-SCRIPT-MAP",
            "title": "Runner script mapping",
            "test_units": [
                {
                    "unit_ref": "TESTSET-SCRIPT-MAP-U01",
                    "title": "happy path",
                    "priority": "P1",
                    "input_preconditions": ["ready job exists"],
                    "trigger_action": "run-execution",
                    "pass_conditions": ["exit zero"],
                    "fail_conditions": ["claim conflict"],
                    "required_evidence": ["stdout"],
                    "acceptance_ref": "AC-01",
                },
                {
                    "unit_ref": "TESTSET-SCRIPT-MAP-U02",
                    "title": "read only monitor",
                    "priority": "P1",
                    "input_preconditions": ["queue exists"],
                    "trigger_action": "show-status",
                    "pass_conditions": ["read only"],
                    "fail_conditions": ["writes are blocked"],
                    "required_evidence": ["stdout"],
                    "acceptance_ref": "AC-02",
                },
            ],
        }
        case_pack = expand_requirement_cases(test_set)
        script_pack = map_scripts(
            test_set,
            case_pack,
            {"execution_modality": "cli", "command_entry": "python tools/run_case.py", "workdir": "."},
        )

        self.assertEqual(script_pack["artifact_type"], "script_pack")
        self.assertEqual(script_pack["runner_skill_ref"], "skill.runner.test_cli")
        self.assertEqual(script_pack["runner_config"]["command_entry"], "python tools/run_case.py")
        self.assertEqual(script_pack["bindings"][0]["case_id"], "TESTSET-SCRIPT-MAP-U01")
        self.assertEqual(script_pack["bindings"][0]["expected_outcome"], "exit_code_zero")
        self.assertEqual(script_pack["bindings"][1]["case_family"], "read_only_guard")
        self.assertEqual(script_pack["bindings"][1]["expected_outcome"], "exit_code_zero_with_read_only_verdict")

