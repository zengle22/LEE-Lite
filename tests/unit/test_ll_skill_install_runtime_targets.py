from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ci.common import ROOT


INSTALL_SCRIPT = ROOT / "skills" / "ll-skill-install" / "scripts" / "install_adapter.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LlSkillInstallRuntimeTargetsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module(INSTALL_SCRIPT, "install_adapter_runtime_targets")

    def test_default_skills_dir_uses_claude_home_for_claude_runtime(self) -> None:
        with patch.dict("os.environ", {"CLAUDE_HOME": r"C:\Users\tester\.claude-custom"}, clear=False):
            target = self.module.default_skills_dir("claude")
        self.assertEqual(target, Path(r"C:\Users\tester\.claude-custom") / "skills")

    def test_default_skills_dir_uses_codex_home_for_codex_runtime(self) -> None:
        with patch.dict("os.environ", {"CODEX_HOME": r"C:\Users\tester\.codex-custom"}, clear=False):
            target = self.module.default_skills_dir("codex")
        self.assertEqual(target, Path(r"C:\Users\tester\.codex-custom") / "skills")

    def test_default_skills_dir_falls_back_to_hidden_runtime_dirs(self) -> None:
        fake_home = Path(r"C:\Users\tester")
        with patch.object(self.module.Path, "home", return_value=fake_home):
            self.assertEqual(self.module.default_skills_dir("claude"), fake_home / ".claude" / "skills")
            self.assertEqual(self.module.default_skills_dir("codex"), fake_home / ".codex" / "skills")

    def test_main_uses_runtime_default_destination_for_claude(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "demo-skill"
            source_dir.mkdir()
            (source_dir / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: Demo skill.\n---\n\n# Demo Skill\n",
                encoding="utf-8",
            )
            observed: dict[str, Path | bool | None] = {}

            def fake_install_adapter(source_skill_dir: Path, dest_root: Path, workspace_root: Path | None, replace: bool) -> Path:
                observed["source_skill_dir"] = source_skill_dir
                observed["dest_root"] = dest_root
                observed["workspace_root"] = workspace_root
                observed["replace"] = replace
                return dest_root / "demo-skill"

            with patch.dict("os.environ", {"CLAUDE_HOME": r"C:\Users\tester\.claude-runtime"}, clear=False):
                with patch.object(self.module, "install_adapter", side_effect=fake_install_adapter):
                    with patch("sys.argv", ["install_adapter.py", "--source", str(source_dir), "--runtime", "claude", "--replace"]):
                        exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(observed["source_skill_dir"], source_dir)
        self.assertEqual(observed["dest_root"], Path(r"C:\Users\tester\.claude-runtime") / "skills")
        self.assertIsNone(observed["workspace_root"])
        self.assertTrue(observed["replace"])


if __name__ == "__main__":
    unittest.main()
