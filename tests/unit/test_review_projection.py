from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cli.lib.registry_store import bind_record
from cli.lib.review_projection.regeneration import ProjectionRegenerationError, request_projection_regeneration
from cli.lib.review_projection.renderer import render_projection
from cli.lib.review_projection.writeback import ProjectionWritebackError, writeback_projection_comment


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ReviewProjectionRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        self.trace = {"run_ref": "RUN-ADR015"}

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_render_projection_writes_expected_blocks(self) -> None:
        ssot_ref = self._bind_ssot(
            "candidate.review-projection",
            {
                "freeze_ready": True,
                "status": "freeze_ready",
                "product_summary": "Projection keeps Machine SSOT readable to human reviewers.",
                "roles": ["reviewer", "ssot owner"],
                "main_flow": ["render", "review", "decide"],
                "deliverables": ["review projection"],
                "completed_state": "Projection rendered for gate review.",
                "authoritative_output": "Machine SSOT",
                "frozen_downstream_boundary": "Projection is non-inheritable.",
                "open_technical_decisions": ["Confirm regeneration sequencing."],
            },
        )

        projection = render_projection(self.workspace, {"ssot_ref": ssot_ref, "template_version": "v1", "review_stage": "gate_review"})

        self.assertEqual(projection["status"], "review_visible")
        self.assertTrue((self.workspace / projection["projection_ref"]).exists())
        block_ids = [block["id"] for block in projection["review_blocks"]]
        self.assertEqual(block_ids[:4], ["product_summary", "roles", "main_flow", "deliverables"])
        self.assertIn("authoritative_snapshot", block_ids)
        self.assertIn("review_focus", block_ids)
        self.assertIn("risks_ambiguities", block_ids)
        self.assertTrue(projection["derived_markers"]["derived_only"])

    def test_render_projection_flags_missing_authoritative_fields(self) -> None:
        ssot_ref = self._bind_ssot(
            "candidate.incomplete-projection",
            {
                "freeze_ready": True,
                "product_summary": "Projection exists but constraints are incomplete.",
                "roles": ["reviewer"],
                "main_flow": ["review"],
                "deliverables": ["projection"],
            },
        )

        projection = render_projection(self.workspace, {"ssot_ref": ssot_ref, "template_version": "v1"})

        snapshot_block = next(block for block in projection["review_blocks"] if block["id"] == "authoritative_snapshot")
        self.assertEqual(snapshot_block["status"], "constraints_missing")
        self.assertEqual(projection["status"], "traceability_pending")

    def test_writeback_and_regeneration_follow_ssot_roundtrip(self) -> None:
        ssot_path = self.workspace / "artifacts" / "active" / "run-001" / "machine-ssot.json"
        write_json(
            ssot_path,
            {
                "freeze_ready": True,
                "status": "freeze_ready",
                "product_summary": "Initial summary.",
                "roles": ["reviewer"],
                "main_flow": ["review"],
                "deliverables": ["projection"],
                "completed_state": "ready",
                "authoritative_output": "Machine SSOT",
                "frozen_downstream_boundary": "No downstream inheritance.",
                "open_technical_decisions": ["Need clearer reviewer wording."],
            },
        )
        bind_record(
            self.workspace,
            "candidate.ssot-roundtrip",
            "artifacts/active/run-001/machine-ssot.json",
            "candidate",
            self.trace,
        )
        projection = render_projection(self.workspace, {"ssot_ref": "candidate.ssot-roundtrip", "template_version": "v1"})

        comment = writeback_projection_comment(
            self.workspace,
            projection["projection_ref"],
            "comment-001",
            "Please clarify the product summary for reviewers.",
            "reviewer-A",
            target_block="product_summary",
        )
        self.assertEqual(comment["status"], "ssot_revision_requested")
        self.assertTrue(comment["mapped_field_refs"])

        updated_path = self.workspace / "artifacts" / "active" / "run-001" / "machine-ssot-updated.json"
        updated_payload = read_json(ssot_path)
        updated_payload["product_summary"] = "Updated summary after reviewer feedback."
        write_json(updated_path, updated_payload)

        regenerated = request_projection_regeneration(
            self.workspace,
            comment["revision_request_ref"],
            "artifacts/active/run-001/machine-ssot-updated.json",
        )
        self.assertEqual(regenerated["status"], "projection_regenerated")
        regenerated_projection = read_json(self.workspace / regenerated["regenerated_projection_ref"])
        summary_block = next(block for block in regenerated_projection["review_blocks"] if block["id"] == "product_summary")
        self.assertIn("Updated summary after reviewer feedback.", summary_block["content"][0])

    def test_writeback_mapping_failure_and_missing_regeneration_input(self) -> None:
        ssot_ref = self._bind_ssot(
            "candidate.mapping-failure",
            {
                "freeze_ready": True,
                "product_summary": "Summary.",
                "roles": ["reviewer"],
                "main_flow": ["review"],
                "deliverables": ["projection"],
                "completed_state": "ready",
                "authoritative_output": "Machine SSOT",
                "frozen_downstream_boundary": "No downstream inheritance.",
                "open_technical_decisions": ["Decision remains open."],
            },
        )
        projection = render_projection(self.workspace, {"ssot_ref": ssot_ref, "template_version": "v1"})

        with self.assertRaises(ProjectionWritebackError):
            writeback_projection_comment(
                self.workspace,
                projection["projection_ref"],
                "comment-unknown",
                "This needs improvement.",
                "reviewer-B",
            )

        comment_path = self.workspace / "artifacts" / "active" / "gates" / "comments" / "comment-unknown.json"
        self.assertEqual(read_json(comment_path)["status"], "comment_mapping_pending")

        comment = writeback_projection_comment(
            self.workspace,
            projection["projection_ref"],
            "comment-known",
            "Please revisit the deliverables wording.",
            "reviewer-B",
            target_block="deliverables",
        )
        with self.assertRaises(ProjectionRegenerationError):
            request_projection_regeneration(self.workspace, comment["revision_request_ref"], "missing-updated-ssot.json")
        revision = read_json(self.workspace / comment["revision_request_ref"])
        self.assertEqual(revision["status"], "projection_regeneration_pending")
        self.assertFalse(revision["current_projection_allowed"])

    def _bind_ssot(self, artifact_ref: str, payload: dict) -> str:
        target = self.workspace / "artifacts" / "active" / "run-001" / f"{artifact_ref.replace('.', '-')}.json"
        write_json(target, payload)
        bind_record(
            self.workspace,
            artifact_ref,
            target.relative_to(self.workspace).as_posix(),
            "candidate",
            self.trace,
        )
        return artifact_ref


if __name__ == "__main__":
    unittest.main()
