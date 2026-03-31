import json
import tempfile
import unittest
from pathlib import Path

from cli.lib.workflow_revision import (
    build_revision_summary,
    load_revision_request,
    materialize_revision_request,
    normalize_revision_context,
)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class WorkflowRevisionTests(unittest.TestCase):
    def test_normalize_revision_context_builds_shared_schema(self) -> None:
        request = {
            "workflow_key": "product.src-to-epic",
            "run_id": "epic-revise",
            "source_run_id": "src-revise",
            "decision_type": "revise",
            "decision_target": "epic_freeze_package",
            "decision_reason": "请把 revise 上下文显式落到约束层，并保留最小补丁。",
            "revision_round": 2,
            "basis_refs": ["a.json", "b.json"],
            "trace": {"run_ref": "epic-revise"},
        }

        context = normalize_revision_context(
            request,
            revision_request_ref="artifacts/src-to-epic/epic-revise/revision-request.json",
        )

        self.assertEqual(context["revision_request_ref"], "artifacts/src-to-epic/epic-revise/revision-request.json")
        self.assertEqual(context["workflow_key"], "product.src-to-epic")
        self.assertEqual(context["source_run_id"], "src-revise")
        self.assertEqual(context["basis_refs"], ["a.json", "b.json"])
        self.assertEqual(context["trace"], {"run_ref": "epic-revise"})
        self.assertIn("Gate revise:", context["summary"])

    def test_materialize_revision_request_increments_existing_round(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "artifacts" / "epic-to-feat" / "feat-revise"
            _dump_json(artifacts_dir / "revision-request.json", {"revision_round": 1, "decision_reason": "old"})
            source_path = Path(temp_dir) / "incoming-revision.json"
            _dump_json(
                source_path,
                {
                    "workflow_key": "product.epic-to-feat",
                    "decision_reason": "new",
                    "revision_round": 1,
                },
            )

            revision_ref, payload, revision_round = materialize_revision_request(
                artifacts_dir,
                revision_request_path=source_path,
                load_json=_load_json,
                dump_json=_dump_json,
                increment_round=True,
                default_round=1,
            )

            self.assertEqual(revision_ref, str((artifacts_dir / "revision-request.json").resolve()))
            self.assertEqual(revision_round, 2)
            self.assertEqual(payload["revision_round"], 2)
            self.assertEqual(_load_json(artifacts_dir / "revision-request.json")["revision_round"], 2)

    def test_load_revision_request_prefers_explicit_then_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifacts_dir = root / "artifacts" / "feat-to-tech" / "tech-revision"
            _dump_json(artifacts_dir / "revision-request.json", {"decision_reason": "artifacts"})
            explicit_path = root / "revision-request.json"
            _dump_json(explicit_path, {"decision_reason": "explicit"})

            explicit_payload, explicit_loaded_path = load_revision_request(
                explicit_path,
                artifacts_dir=artifacts_dir,
                load_json=_load_json,
            )
            fallback_payload, fallback_loaded_path = load_revision_request(
                None,
                artifacts_dir=artifacts_dir,
                load_json=_load_json,
            )

            self.assertEqual(explicit_payload["decision_reason"], "explicit")
            self.assertEqual(explicit_loaded_path, explicit_path.resolve())
            self.assertEqual(fallback_payload["decision_reason"], "artifacts")
            self.assertEqual(fallback_loaded_path, (artifacts_dir / "revision-request.json").resolve())

    def test_build_revision_summary_is_stable_for_sparse_requests(self) -> None:
        summary = build_revision_summary({"decision_reason": "补充最小风险约束。"})
        self.assertEqual(summary, "Gate revise: 补充最小风险约束。")


if __name__ == "__main__":
    unittest.main()
