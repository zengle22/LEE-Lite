import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = ROOT / "skills" / "ll-meta-skill-creator"
SCRIPTS_DIR = SKILL_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

import evaluate_skill  # noqa: E402


INIT_SCRIPT = SCRIPTS_DIR / "init_lee_workflow_skill.py"
VALIDATE_STACK_SCRIPT = SCRIPTS_DIR / "validate_skill_stack.py"
EVALUATE_SCRIPT = SCRIPTS_DIR / "evaluate_skill.py"


class LlMetaSkillCreatorTests(unittest.TestCase):
    def run_cmd(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_build_runner_command_codex_uses_safe_defaults(self) -> None:
        with mock.patch.object(evaluate_skill.shutil, "which", side_effect=lambda name: "C:\\tools\\codex.cmd" if name == "codex.cmd" else None):
            cmd = evaluate_skill.build_runner_command(
                runner="codex",
                workspace=ROOT,
                prompt="Use $skill to solve x",
                output_file=ROOT / "out.txt",
                timeout_seconds=90,
            )

        self.assertEqual(cmd[0], "C:\\tools\\codex.cmd")
        self.assertIn("-a", cmd)
        self.assertIn("never", cmd)
        self.assertIn("--sandbox", cmd)
        self.assertIn("read-only", cmd)
        self.assertIn("--ephemeral", cmd)
        self.assertIn("--output-last-message", cmd)

    def test_build_runner_command_claude_uses_separator_and_safe_flags(self) -> None:
        with mock.patch.object(evaluate_skill.shutil, "which", side_effect=lambda name: "C:\\tools\\claude.exe" if name == "claude.exe" else None):
            cmd = evaluate_skill.build_runner_command(
                runner="claude",
                workspace=ROOT,
                prompt="Use $skill to solve x",
                output_file=ROOT / "unused.txt",
                timeout_seconds=60,
            )

        self.assertEqual(cmd[0], "C:\\tools\\claude.exe")
        self.assertIn("--permission-mode", cmd)
        self.assertIn("bypassPermissions", cmd)
        self.assertIn("--allowedTools", cmd)
        self.assertIn("--no-session-persistence", cmd)
        self.assertEqual(cmd[-2], "--")
        self.assertEqual(cmd[-1], "Use $skill to solve x")

    def test_run_forward_tests_captures_timeout(self) -> None:
        with mock.patch.object(
            evaluate_skill,
            "build_runner_command",
            return_value=["fake-runner", "arg"],
        ), mock.patch.object(
            evaluate_skill.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(cmd=["fake-runner", "arg"], timeout=5),
        ):
            results = evaluate_skill.run_forward_tests(
                runner="codex",
                workspace=ROOT,
                prompts=["prompt one"],
                max_prompts=1,
                timeout_seconds=5,
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "fail")
        self.assertEqual(results[0]["exit_code"], "timeout")

    def test_build_auto_forward_prompts_is_bounded(self) -> None:
        prompts = evaluate_skill.build_auto_forward_prompts(
            skill_path=ROOT / "fake-skill",
            skill_name="fake-skill",
            contract={
                "workflow_key": "product.src-to-epic",
                "input": {"artifact_type": "src"},
                "output": {"artifact_type": "epic"},
            },
        )

        self.assertGreaterEqual(len(prompts), 2)
        self.assertIn("Do not modify files.", prompts[0])
        self.assertIn("Keep the answer under 200 words.", prompts[0])
        self.assertIn("frozen SRC artifact", prompts[1])

    def test_generated_skill_passes_validation_stack(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            init = self.run_cmd(
                INIT_SCRIPT,
                "tmp-src-to-epic",
                "--path",
                str(temp_root),
                "--input-artifact",
                "src",
                "--output-artifact",
                "epic",
                "--workflow-key",
                "product.src-to-epic",
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            skill_path = temp_root / "tmp-src-to-epic"
            validate = self.run_cmd(VALIDATE_STACK_SCRIPT, str(skill_path))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("[OK] Validation stack passed.", validate.stdout)

    def test_evaluate_skill_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            init = self.run_cmd(
                INIT_SCRIPT,
                "tmp-eval-src-to-epic",
                "--path",
                str(temp_root),
                "--input-artifact",
                "src",
                "--output-artifact",
                "epic",
                "--workflow-key",
                "product.src-to-epic",
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            skill_path = temp_root / "tmp-eval-src-to-epic"
            report_path = temp_root / "evaluation-report.md"
            evaluate = self.run_cmd(EVALUATE_SCRIPT, str(skill_path), "--report-out", str(report_path))
            self.assertEqual(evaluate.returncode, 0, evaluate.stderr)
            self.assertTrue(report_path.exists())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Skill Evaluation Report", report)
            self.assertIn("Forward-Test Prompt Suggestions", report)
            self.assertIn("Automatic Forward-Test Results", report)


if __name__ == "__main__":
    unittest.main()
