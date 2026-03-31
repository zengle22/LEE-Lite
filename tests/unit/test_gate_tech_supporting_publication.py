from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cli.ll import main


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GateTechSupportingPublicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)

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
            "trace": {"run_ref": "RUN-001"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def test_gate_materialize_tech_candidate_promotes_arch_api_and_dispatches_refs(self) -> None:
        run_id = "feat-tech-supporting-run"
        package_dir = self.workspace / "artifacts" / "feat-to-tech" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "tech-design-bundle.md").write_text("# TECH Bundle\n", encoding="utf-8")
        write_json(
            package_dir / "tech-design-bundle.json",
            {
                "artifact_type": "tech_design_package",
                "workflow_key": "dev.feat-to-tech",
                "workflow_run_id": run_id,
                "title": "Minimal Onboarding Technical Design Package",
                "status": "accepted",
                "feat_ref": "FEAT-SRC-001-301",
                "tech_ref": "TECH-SRC-001-301",
                "arch_ref": "ARCH-SRC-001-301",
                "api_ref": "API-SRC-001-301",
                "arch_required": True,
                "api_required": True,
                "source_refs": ["FEAT-SRC-001-301", "EPIC-SRC-001-001", "SRC-001"],
            },
        )
        (package_dir / "arch-design.md").write_text(
            "---\nartifact_type: ARCH\narch_ref: ARCH-SRC-001-301\n---\n\n# ARCH-SRC-001-301\n\nBoundary placement.\n",
            encoding="utf-8",
        )
        (package_dir / "api-contract.md").write_text(
            "---\nartifact_type: API\napi_ref: API-SRC-001-301\n---\n\n# API-SRC-001-301\n\nContract surface.\n",
            encoding="utf-8",
        )
        write_json(package_dir / "handoff-to-tech-impl.json", {"target_workflow": "workflow.dev.tech_to_impl"})
        write_json(
            self.workspace / "artifacts" / "registry" / f"feat-to-tech-{run_id}-tech-design-bundle.json",
            {
                "artifact_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
                "managed_artifact_ref": f"artifacts/feat-to-tech/{run_id}/tech-design-bundle.md",
                "status": "committed",
                "trace": {"run_ref": run_id, "workflow_key": "dev.feat-to-tech"},
                "metadata": {"layer": "candidate"},
                "lineage": [],
            },
        )
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision-tech-supporting.json"
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": f"feat-to-tech.{run_id}.tech-design-bundle"})

        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-tech-supporting.json",
                "candidate_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
            },
        )
        materialize_req = self.request_path("gate-materialize-tech-supporting.json")
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path("gate-materialize-tech-supporting.response.json")
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )
        materialize_payload = read_json(materialize_response)
        self.assertEqual(materialize_payload["data"]["formal_ref"], f"formal.tech.{run_id}")
        self.assertEqual(
            materialize_payload["data"]["materialized_formal_refs"],
            ["formal.arch.arch-src-001-301", "formal.api.api-src-001-301"],
        )

        formal_tech_path = self.workspace / "ssot" / "tech" / "SRC-001" / "TECH-SRC-001-301__minimal-onboarding-technical-design-package.md"
        formal_arch_path = self.workspace / "ssot" / "architecture" / "ARCH-SRC-001-301__minimal-onboarding-technical-design-package-architecture-overview.md"
        formal_api_path = self.workspace / "ssot" / "api" / "SRC-001" / "API-SRC-001-301__minimal-onboarding-technical-design-package-api-contract.md"
        self.assertTrue(formal_tech_path.exists())
        self.assertTrue(formal_arch_path.exists())
        self.assertTrue(formal_api_path.exists())

        tech_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-tech-{run_id}.json")
        self.assertEqual(
            tech_record["metadata"]["materialized_formal_refs"],
            ["formal.arch.arch-src-001-301", "formal.api.api-src-001-301"],
        )

        dispatch_request = self.build_request(
            "gate.dispatch",
            {"gate_decision_ref": "artifacts/active/gates/decisions/gate-decision-tech-supporting.json"},
        )
        dispatch_req = self.request_path("gate-dispatch-tech-supporting.json")
        write_json(dispatch_req, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-tech-supporting.response.json")
        self.assertEqual(
            self.run_cli("gate", "dispatch", "--request", str(dispatch_req), "--response-out", str(dispatch_response)),
            0,
        )
        dispatch_payload = read_json(dispatch_response)
        job = read_json(self.workspace / dispatch_payload["data"]["materialized_job_refs"][0])
        self.assertEqual(job["arch_ref"], "ARCH-SRC-001-301")
        self.assertEqual(job["api_ref"], "API-SRC-001-301")
        self.assertEqual(
            job["supporting_formal_refs"],
            ["formal.arch.arch-src-001-301", "formal.api.api-src-001-301"],
        )
        self.assertEqual(len(job["input_refs"]), 4)
