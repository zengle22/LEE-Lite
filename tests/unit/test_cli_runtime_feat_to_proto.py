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


class CliRuntimeFeatToProtoTest(unittest.TestCase):
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

    def materialize(self, request_name: str, response_name: str, candidate_ref: str, decision_name: str) -> dict:
        decision_path = self.workspace / "artifacts" / "active" / "gates" / "decisions" / decision_name
        write_json(decision_path, {"decision_type": "approve", "candidate_ref": candidate_ref})
        materialize_request = self.build_request(
            "gate.materialize",
            {
                "gate_decision_ref": f"artifacts/active/gates/decisions/{decision_name}",
                "candidate_ref": candidate_ref,
            },
        )
        materialize_req = self.request_path(request_name)
        write_json(materialize_req, materialize_request)
        materialize_response = self.response_path(response_name)
        self.assertEqual(
            self.run_cli("gate", "materialize", "--request", str(materialize_req), "--response-out", str(materialize_response)),
            0,
        )
        return read_json(materialize_response)

    def test_gate_materialize_feat_to_proto_candidate_promotes_owner_stable_prototype_path(self) -> None:
        run_dir = "src001-proto-20260407--feat-src-001-001"
        prototype_dir = self.workspace / "artifacts" / "feat-to-proto" / run_dir / "prototype"
        prototype_dir.mkdir(parents=True, exist_ok=True)
        (prototype_dir / "index.html").write_text("<html><body>Prototype shell</body></html>\n", encoding="utf-8")
        write_json(
            prototype_dir.parent / "prototype-bundle.json",
            {
                "artifact_type": "prototype_package",
                "workflow_key": "dev.feat-to-proto",
                "workflow_run_id": "src001-proto-20260407",
                "feat_ref": "FEAT-SRC-001-001",
                "feat_title": "Homepage Advice Panel",
                "prototype_owner_ref": "PROTO-RUNNER-OPERATOR-MAIN",
                "prototype_ref": "PROTO-FEAT-SRC-001-001",
                "source_refs": ["FEAT-SRC-001-001", "EPIC-SRC-001-001", "SRC-001"],
            },
        )
        candidate_ref = f"feat-to-proto.{run_dir}.prototype"
        write_json(
            self.workspace / "artifacts" / "registry" / f"feat-to-proto-{run_dir}-prototype.json",
            {
                "artifact_ref": candidate_ref,
                "managed_artifact_ref": f"artifacts/feat-to-proto/{run_dir}/prototype/index.html",
                "status": "candidate",
                "trace": {"run_ref": run_dir, "workflow_key": "dev.feat-to-proto"},
                "metadata": {
                    "layer": "candidate",
                    "target_kind": "prototype",
                    "source_package_ref": f"artifacts/feat-to-proto/{run_dir}",
                },
                "lineage": ["FEAT-SRC-001-001"],
            },
        )
        payload = self.materialize(
            "gate-materialize-feat-proto.json",
            "gate-materialize-feat-proto.response.json",
            candidate_ref,
            "gate-decision-prototype.json",
        )
        self.assertEqual(payload["data"]["formal_ref"], f"formal.prototype.{run_dir}")
        self.assertEqual(payload["data"]["assigned_id"], "PROTO-RUNNER-OPERATOR-MAIN")

        formal_path = self.workspace / "ssot" / "prototype" / "SRC-001" / "PROTO-RUNNER-OPERATOR-MAIN" / "index.html"
        self.assertTrue(formal_path.exists())
        self.assertIn("Prototype shell", formal_path.read_text(encoding="utf-8"))

        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-prototype-{run_dir}.json")
        self.assertEqual(
            registry_record["managed_artifact_ref"],
            "ssot/prototype/SRC-001/PROTO-RUNNER-OPERATOR-MAIN/index.html",
        )
        self.assertEqual(registry_record["metadata"]["prototype_owner_ref"], "PROTO-RUNNER-OPERATOR-MAIN")

    def test_gate_materialize_feat_to_proto_candidate_migrates_existing_feat_named_formal_record_to_owner_path(self) -> None:
        run_dir = "src001-proto-20260407--feat-src-001-002"
        prototype_dir = self.workspace / "artifacts" / "feat-to-proto" / run_dir / "prototype"
        prototype_dir.mkdir(parents=True, exist_ok=True)
        (prototype_dir / "index.html").write_text("<html><body>Updated prototype shell</body></html>\n", encoding="utf-8")
        write_json(
            prototype_dir.parent / "prototype-bundle.json",
            {
                "artifact_type": "prototype_package",
                "workflow_key": "dev.feat-to-proto",
                "workflow_run_id": "src001-proto-20260407",
                "feat_ref": "FEAT-SRC-001-002",
                "feat_title": "Runner Control Surface",
                "prototype_owner_ref": "PROTO-RUNNER-OPERATOR-MAIN",
                "prototype_ref": "PROTO-FEAT-SRC-001-002",
                "source_refs": ["FEAT-SRC-001-002", "EPIC-SRC-001-001", "SRC-001"],
            },
        )
        candidate_ref = f"feat-to-proto.{run_dir}.prototype"
        write_json(
            self.workspace / "artifacts" / "registry" / f"feat-to-proto-{run_dir}-prototype.json",
            {
                "artifact_ref": candidate_ref,
                "managed_artifact_ref": f"artifacts/feat-to-proto/{run_dir}/prototype/index.html",
                "status": "candidate",
                "trace": {"run_ref": run_dir, "workflow_key": "dev.feat-to-proto"},
                "metadata": {
                    "layer": "candidate",
                    "target_kind": "prototype",
                    "source_package_ref": f"artifacts/feat-to-proto/{run_dir}",
                },
                "lineage": ["FEAT-SRC-001-002"],
            },
        )
        legacy_formal_dir = self.workspace / "ssot" / "prototype" / "SRC-001" / "PROTOTYPE-FEAT-SRC-001-002"
        legacy_formal_dir.mkdir(parents=True, exist_ok=True)
        (legacy_formal_dir / "index.html").write_text("<html><body>Legacy prototype shell</body></html>\n", encoding="utf-8")
        write_json(
            self.workspace / "artifacts" / "registry" / f"formal-prototype-{run_dir}.json",
            {
                "artifact_ref": f"formal.prototype.{run_dir}",
                "managed_artifact_ref": "ssot/prototype/SRC-001/PROTOTYPE-FEAT-SRC-001-002/index.html",
                "status": "materialized",
                "trace": {"run_ref": "legacy-run", "workflow_key": "manual.formalization.backfill"},
                "metadata": {"target_kind": "prototype"},
                "lineage": [],
            },
        )
        payload = self.materialize(
            "gate-materialize-feat-proto-migrate.json",
            "gate-materialize-feat-proto-migrate.response.json",
            candidate_ref,
            "gate-decision-prototype-migrate.json",
        )
        self.assertEqual(payload["data"]["assigned_id"], "PROTO-RUNNER-OPERATOR-MAIN")

        owner_path = self.workspace / "ssot" / "prototype" / "SRC-001" / "PROTO-RUNNER-OPERATOR-MAIN" / "index.html"
        self.assertTrue(owner_path.exists())
        self.assertIn("Updated prototype shell", owner_path.read_text(encoding="utf-8"))

        registry_record = read_json(self.workspace / "artifacts" / "registry" / f"formal-prototype-{run_dir}.json")
        self.assertEqual(
            registry_record["managed_artifact_ref"],
            "ssot/prototype/SRC-001/PROTO-RUNNER-OPERATOR-MAIN/index.html",
        )

    def test_gate_materialize_feat_to_proto_candidate_merges_multiple_feat_pages_by_owner(self) -> None:
        owner_ref = "PROTO-RUNNER-OPERATOR-MAIN"
        run_specs = [
            ("src001-proto-20260407-r1--feat-src-001-003", "FEAT-SRC-001-003", "Entry Flow", "entry-page"),
            ("src001-proto-20260407-r1--feat-src-001-004", "FEAT-SRC-001-004", "Monitor Flow", "monitor-page"),
            ("src001-proto-20260407-r1--feat-src-999-999", "FEAT-SRC-999-999", "Dirty Flow", "dirty-page"),
        ]
        for run_dir, feat_ref, feat_title, page_id in run_specs:
            package_dir = self.workspace / "artifacts" / "feat-to-proto" / run_dir
            prototype_dir = package_dir / "prototype"
            prototype_dir.mkdir(parents=True, exist_ok=True)
            (prototype_dir / "index.html").write_text("<html><body>Prototype shell</body></html>\n", encoding="utf-8")
            write_json(
                package_dir / "prototype-bundle.json",
                {
                    "artifact_type": "prototype_package",
                    "workflow_key": "dev.feat-to-proto",
                    "workflow_run_id": run_dir,
                    "feat_ref": feat_ref,
                    "feat_title": feat_title,
                    "prototype_owner_ref": owner_ref,
                    "prototype_ref": f"PROTO-{feat_ref}",
                    "surface_map_ref": f"SURFACE-MAP-{feat_ref}",
                    "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"] if feat_ref != "FEAT-SRC-999-999" else [feat_ref, "EPIC-SRC-999-001"],
                    "pages": [{"page_id": page_id, "title": feat_title, "page_goal": f"{feat_title} goal."}],
                },
            )
            write_json(
                prototype_dir / "mock-data.json",
                {
                    "feat_ref": feat_ref,
                    "feat_title": feat_title,
                    "source_refs": [feat_ref, "EPIC-SRC-001-001", "SRC-001"] if feat_ref != "FEAT-SRC-999-999" else [feat_ref, "EPIC-SRC-999-001"],
                    "prototype_owner_ref": owner_ref,
                    "surface_map_ref": f"SURFACE-MAP-{feat_ref}",
                    "pages": [{"page_id": page_id, "title": feat_title, "page_goal": f"{feat_title} goal."}],
                },
            )
            write_json(
                prototype_dir / "journey-model.json",
                {
                    "feat_ref": feat_ref,
                    "journey_surface_inventory": [
                        {"surface_id": page_id, "surface_title": feat_title, "composes_feat_refs": [feat_ref]}
                    ],
                    "feat_dependency_order": ["FEAT-SRC-001-003", "FEAT-SRC-001-004"],
                    "checked_at": "2026-04-07T00:00:00Z",
                },
            )
            candidate_ref = f"candidate.prototype.{run_dir}"
            write_json(
                self.workspace / "artifacts" / "registry" / f"candidate-prototype-{run_dir}.json",
                {
                    "artifact_ref": candidate_ref,
                    "managed_artifact_ref": f"artifacts/feat-to-proto/{run_dir}/prototype/index.html",
                    "status": "committed",
                    "trace": {"run_ref": run_dir, "workflow_key": "dev.feat-to-proto"},
                    "metadata": {
                        "layer": "candidate",
                        "target_kind": "prototype",
                        "source_package_ref": f"artifacts/feat-to-proto/{run_dir}",
                    },
                    "lineage": [feat_ref],
                },
            )

        self.materialize(
            "gate-materialize-feat-proto-merged-seed.json",
            "gate-materialize-feat-proto-merged-seed.response.json",
            "candidate.prototype.src001-proto-20260407-r1--feat-src-001-003",
            "gate-decision-prototype-merged-seed.json",
        )
        payload = self.materialize(
            "gate-materialize-feat-proto-merged.json",
            "gate-materialize-feat-proto-merged.response.json",
            "candidate.prototype.src001-proto-20260407-r1--feat-src-001-004",
            "gate-decision-prototype-merged.json",
        )
        self.assertEqual(payload["data"]["assigned_id"], owner_ref)

        owner_dir = self.workspace / "ssot" / "prototype" / "SRC-001" / owner_ref
        self.assertTrue((owner_dir / "index.html").exists())
        merged_mock_data = read_json(owner_dir / "mock-data.json")
        self.assertEqual(merged_mock_data["feat_ref"], owner_ref)
        self.assertEqual(merged_mock_data["related_feat_refs"], ["FEAT-SRC-001-003", "FEAT-SRC-001-004"])
        self.assertEqual([page["page_id"] for page in merged_mock_data["pages"]], ["entry-page", "monitor-page"])
        self.assertNotIn("FEAT-SRC-999-999", merged_mock_data["related_feat_refs"])
        owner_manifest = read_json(owner_dir / "owner-publication-manifest.json")
        self.assertEqual(owner_manifest["prototype_owner_ref"], owner_ref)
        self.assertEqual(owner_manifest["related_feat_refs"], ["FEAT-SRC-001-003", "FEAT-SRC-001-004"])


if __name__ == "__main__":
    unittest.main()
