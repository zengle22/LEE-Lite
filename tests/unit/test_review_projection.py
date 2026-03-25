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
        self.assertTrue(all("##" not in trace_ref for trace_ref in projection["trace_refs"]))

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

    def test_render_projection_aligns_epic_freeze_payload(self) -> None:
        ssot_ref = self._bind_ssot(
            "epic.freeze-review-projection",
            {
                "freeze_ready": True,
                "status": "accepted",
                "artifact_type": "epic_freeze_package",
                "title": "主链正式交接与治理闭环统一能力",
                "epic_freeze_ref": "EPIC-ADR001-003-006-UNIFIED-MAINLINE-202-4-RERUN5",
                "epic_intent": "把主链治理问题空间冻结为稳定的产品行为切片。",
                "business_goal": "下游 FEAT 按产品行为切片而不是能力轴拆分。",
                "actors_and_roles": [
                    {
                        "role": "workflow / orchestration 设计者",
                        "responsibility": "定义主链边界和交接关系。",
                    },
                    {
                        "role": "governed skill 作者",
                        "responsibility": "提交 candidate 并消费 decision。",
                    },
                ],
                "product_behavior_slices": [
                    {
                        "name": "主链候选提交与交接流",
                        "product_surface": "候选提交流：governed skill 提交 candidate package 并形成 authoritative handoff submission",
                        "completed_state": "上游 workflow 已看到正式提交完成。",
                        "business_deliverable": "给 gate 使用的 authoritative handoff submission。",
                    },
                    {
                        "name": "主链 gate 审核与裁决流",
                        "product_surface": "审批裁决流：gate 审核 handoff 并输出 authoritative decision result",
                        "completed_state": "gate 已给出单一 authoritative decision result。",
                        "business_deliverable": "给 execution 或 formal 发布链消费的 authoritative decision result。",
                    },
                ],
                "upstream_and_downstream": [
                    "Downstream：产出一个可继续拆分为多个 FEAT 的单一主 EPIC，并交接给 `product.epic-to-feat`。",
                    "下游消费形态：主链候选提交、gate 裁决、formal 物化、准入等产品级 FEAT 切片。",
                ],
                "constraints_and_dependencies": [
                    "ADR-005 是主链文件 IO / 路径治理前置基础。",
                    "foundation 与 adoption_e2e 必须同时落成。",
                ],
            },
        )

        projection = render_projection(self.workspace, {"ssot_ref": ssot_ref, "template_version": "v1"})

        self.assertEqual(projection["status"], "review_visible")
        summary_block = next(block for block in projection["review_blocks"] if block["id"] == "product_summary")
        roles_block = next(block for block in projection["review_blocks"] if block["id"] == "roles")
        flow_block = next(block for block in projection["review_blocks"] if block["id"] == "main_flow")
        deliverables_block = next(block for block in projection["review_blocks"] if block["id"] == "deliverables")
        snapshot_block = next(block for block in projection["review_blocks"] if block["id"] == "authoritative_snapshot")
        self.assertIn("把主链治理问题空间冻结为稳定的产品行为切片。", summary_block["content"][0])
        self.assertIn("workflow / orchestration 设计者", roles_block["content"][0])
        self.assertIn("候选提交流", flow_block["content"][0])
        self.assertIn("authoritative handoff submission", deliverables_block["content"][0])
        self.assertEqual(snapshot_block["status"], "complete")
        self.assertIn("EPIC-ADR001-003-006-UNIFIED-MAINLINE-202-4-RERUN5", " ".join(snapshot_block["content"]))
        self.assertTrue(
            all(
                not trace_ref.startswith(f"{ssot_ref}#{ssot_ref}#")
                for trace_ref in projection["trace_refs"]
            )
        )

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
