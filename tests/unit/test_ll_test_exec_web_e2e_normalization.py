from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "ll-test-exec-web-e2e" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import normalize_request  # noqa: E402
import run_normalized  # noqa: E402


class WebE2ENormalizationTests(unittest.TestCase):
    def test_normalize_request_maps_legacy_api_version_and_test_set_refs(self) -> None:
        request = {
            "api_version": "1.0.0",
            "command": "skill.test-exec-web-e2e",
            "request_id": "req-001",
            "workspace_root": "workspace",
            "actor_ref": "actor",
            "trace": {"run_ref": "RUN-1"},
            "payload": {
                "test_set_refs": ["artifacts/feat-to-testset/demo/test-set.yaml", "artifacts/feat-to-testset/demo/ignored.yaml"],
                "test_environment_ref": "ssot/test-env/web.yaml",
            },
        }

        normalized = normalize_request.normalize_request(request)

        self.assertEqual(normalized["api_version"], "v1")
        self.assertEqual(normalized["payload"]["test_set_ref"], "artifacts/feat-to-testset/demo/test-set.yaml")

    def test_run_normalized_invokes_cli_from_repo_root_with_normalized_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            request_path = temp_dir_path / "request.json"
            response_path = temp_dir_path / "response.json"
            request_path.write_text(
                json.dumps(
                    {
                        "api_version": "1.0.0",
                        "command": "skill.test-exec-web-e2e",
                        "request_id": "req-002",
                        "workspace_root": temp_dir_path.as_posix(),
                        "actor_ref": "actor",
                        "trace": {"run_ref": "RUN-2"},
                        "payload": {
                            "test_set_refs": ["artifacts/feat-to-testset/demo/test-set.yaml"],
                            "test_environment_ref": "ssot/test-env/web.yaml",
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            captured: dict[str, object] = {}

            def fake_run(args, check=False, cwd=None):  # type: ignore[no-untyped-def]
                args = list(args)
                captured.setdefault("calls", []).append({"args": args, "check": check, "cwd": cwd})
                if any(str(item).endswith("normalize_request.py") for item in args):
                    output_index = args.index("--output") + 1
                    output_path = Path(args[output_index])
                    output_path.write_text(
                        json.dumps(
                            {
                                "api_version": "v1",
                                "command": "skill.test-exec-web-e2e",
                                "request_id": "req-002",
                                "workspace_root": temp_dir_path.as_posix(),
                                "actor_ref": "actor",
                                "trace": {"run_ref": "RUN-2"},
                                "payload": {
                                    "test_set_ref": "artifacts/feat-to-testset/demo/test-set.yaml",
                                    "test_environment_ref": "ssot/test-env/web.yaml",
                                },
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(args=args, returncode=0)
                self.assertIn("-m", args)
                self.assertIn("cli", args)
                self.assertEqual(cwd, Path(run_normalized.__file__).resolve().parents[3])
                normalized_request_path = Path(args[args.index("--request") + 1])
                normalized_request = json.loads(normalized_request_path.read_text(encoding="utf-8"))
                self.assertEqual(normalized_request["api_version"], "v1")
                self.assertEqual(normalized_request["payload"]["test_set_ref"], "artifacts/feat-to-testset/demo/test-set.yaml")
                response_path = Path(args[args.index("--response-out") + 1])
                response_path.write_text(json.dumps({"status": "ok"}) + "\n", encoding="utf-8")
                return subprocess.CompletedProcess(args=args, returncode=0)

            with patch("run_normalized.subprocess.run", side_effect=fake_run):
                self.assertEqual(
                    run_normalized.main([
                        "--request",
                        str(request_path),
                        "--response-out",
                        str(response_path),
                    ]),
                    0,
                )


if __name__ == "__main__":
    unittest.main()
