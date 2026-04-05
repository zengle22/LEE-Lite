import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TESTS_UNIT = ROOT / "tests" / "unit"
if str(TESTS_UNIT) not in sys.path:
    sys.path.insert(0, str(TESTS_UNIT))

from test_cli_skill_impl_spec_test import TestImplSpecSkillRuntime  # noqa: E402


class ImplSpecFreezeGuardTests(TestImplSpecSkillRuntime):
    def test_freeze_guard_rejects_pass_with_revisions(self) -> None:
        response = self.build_phase2_surface_response(verdict="pass_with_revisions", review_coverage_status="partial")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "freeze-guard", str(response)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("freeze guard requires verdict=pass", result.stderr)

    def test_freeze_guard_rejects_pass_when_implementation_readiness_is_partial(self) -> None:
        response = self.build_phase2_surface_response(verdict="pass", review_coverage_status="sufficient")
        payload = json.loads(response.read_text(encoding="utf-8"))
        payload["data"]["implementation_readiness"] = "partial"
        response.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        guard_script = self.repo_root / "skills" / "ll-qa-impl-spec-test" / "scripts" / "impl_spec_test_skill_guard.py"
        result = subprocess.run([sys.executable, str(guard_script), "freeze-guard", str(response)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("freeze guard requires implementation_readiness=ready", result.stderr)


if __name__ == "__main__":
    unittest.main()
