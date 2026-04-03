import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-feat-to-ui" / "scripts" / "feat_to_ui.py"


def test_feat_to_ui_cli_is_deprecated_and_disabled() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        input_dir = repo_root / "artifacts" / "epic-to-feat" / "demo"
        input_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "run",
                "--input",
                str(input_dir),
                "--feat-ref",
                "FEAT-UI-001",
                "--repo-root",
                str(repo_root),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["deprecated"] is True
        assert "deprecated and disabled" in payload["errors"][0]
