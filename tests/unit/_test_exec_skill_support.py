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


class SkillRuntimeHarness(unittest.TestCase):
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

    def run_json_command(
        self,
        group: str,
        command: str,
        request_name: str,
        response_name: str,
        payload: dict,
    ) -> dict:
        request = self.build_request(f"{group}.{command}", payload)
        request_path = self.request_path(request_name)
        response_path = self.response_path(response_name)
        write_json(request_path, request)
        self.assertEqual(
            self.run_cli(group, command, "--request", str(request_path), "--response-out", str(response_path)),
            0,
        )
        return read_json(response_path)["data"]

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

    def assert_execution_outputs(self, payload: dict, expected_cases: int, expected_status: str) -> tuple[dict, dict, dict, dict]:
        self.assertEqual(payload["run_status"], expected_status)
        for key in (
            "resolved_ssot_context_ref",
            "ui_intent_ref",
            "ui_source_context_ref",
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
        summary = read_json(self.resolve_ref(payload["results_summary_ref"]))
        self.assertEqual(summary["run_status"], expected_status)
        compliance = read_json(self.resolve_ref(payload["compliance_result_ref"]))
        self.assertEqual(compliance["status"], "pass")
        ui_intent = read_json(self.resolve_ref(payload["ui_intent_ref"]))
        ui_source_context = read_json(self.resolve_ref(payload["ui_source_context_ref"]))
        ui_binding_map = read_json(self.resolve_ref(payload["ui_binding_map_ref"]))
        self.assertEqual(len(ui_intent["cases"]), expected_cases)
        self.assertEqual(len(ui_binding_map["cases"]), expected_cases)
        output_validation = read_json(self.resolve_ref(payload["output_validation_ref"]))
        self.assertEqual(output_validation["status"], "pass")
        tse = read_json(self.resolve_ref(payload["tse_ref"]))
        self.assertEqual(tse["run_status"], expected_status)
        candidate = read_json(self.resolve_ref(payload["candidate_managed_artifact_ref"]))
        self.assertEqual(candidate["run_status"], expected_status)
        return ui_intent, ui_source_context, ui_binding_map, candidate
