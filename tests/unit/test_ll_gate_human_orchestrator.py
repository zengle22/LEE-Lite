import json
import tempfile
from pathlib import Path

from gate_human_orchestrator_test_support import GateHumanOrchestratorTestSupport, ROOT


class GateHumanOrchestratorWorkflowTests(GateHumanOrchestratorTestSupport):

    def test_run_approve_auto_materializes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "gate-approve", cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            bundle_markdown = (artifacts_dir / "gate-decision-bundle.md").read_text(encoding="utf-8")
            runtime_refs = json.loads((artifacts_dir / "runtime-artifact-refs.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "gate-freeze-gate.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle["decision"], "approve")
            self.assertEqual(bundle["dispatch_target"], "formal_publication_trigger")
            self.assertEqual(bundle["machine_ssot_ref"], "candidate.impl")
            self.assertEqual(bundle["projection_status"], "review_visible")
            self.assertTrue(bundle["human_projection_ref"].endswith(".json"))
            self.assertEqual(bundle["decision_display"], "批准")
            self.assertEqual(bundle["dispatch_target_display"], "进入 formal publication")
            self.assertEqual(bundle["projection_status_display"], "可供评审")
            self.assertEqual(bundle["materialized_job_ref"], "")
            self.assertTrue(bundle["materialized_handoff_ref"].endswith("materialized-handoff.json"))
            self.assertTrue(runtime_refs["dispatch_receipt_ref"].endswith("-dispatch-receipt.json"))
            self.assertTrue(freeze_gate["freeze_ready"])
            self.assertIn("# Gate 裁决包 gate-approve", bundle_markdown)
            self.assertIn("## 人工评审简报", bundle_markdown)
            self.assertIn("### 产品摘要", bundle_markdown)
            self.assertIn("## Projection 标记", bundle_markdown)
            self.assertIn("- 状态: 完整", bundle_markdown)
            self.assertIn("- decision: 批准", bundle_markdown)
            self.assertIn("- dispatch_target: 进入 formal publication", bundle_markdown)

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir), cwd=ROOT)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", str(artifacts_dir), cwd=ROOT)
            self.assertEqual(readiness.returncode, 0, readiness.stderr)

    def test_run_revise_dispatches_execution_return(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)
            self.write_json(
                repo_root / "artifacts" / "active" / "audit" / "finding-bundle.json",
                {"findings": [{"severity": "blocker", "title": "missing basis"}]},
            )

            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "gate-revise", cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            artifacts_dir = Path(payload["artifacts_dir"])
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            freeze_gate = json.loads((artifacts_dir / "gate-freeze-gate.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle["decision"], "revise")
            self.assertEqual(bundle["dispatch_target"], "execution_return")
            self.assertEqual(bundle["projection_status"], "review_visible")
            self.assertEqual(bundle["decision_display"], "修订后重审")
            self.assertEqual(bundle["dispatch_target_display"], "回流 execution")
            self.assertEqual(bundle["projection_status_display"], "可供评审")
            self.assertEqual(bundle["materialized_handoff_ref"], "")
            self.assertTrue(bundle["materialized_job_ref"].endswith("-return.json"))
            self.assertTrue(freeze_gate["freeze_ready"])

            validate = self.run_cmd("validate-output", "--artifacts-dir", str(artifacts_dir), cwd=ROOT)
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_prepare_round_show_pending_and_capture_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            prepare_payload = json.loads(prepare.stdout)
            artifacts_dir = Path(prepare_payload["artifacts_dir"])
            self.assertTrue((artifacts_dir / "human-decision-request.json").exists())
            self.assertTrue((artifacts_dir / "human-decision-request.md").exists())
            self.assertTrue((artifacts_dir / "round-state.json").exists())
            self.assertEqual(prepare_payload["review_summary"]["status"], "pending_human_reply")
            self.assertEqual(prepare_payload["review_summary"]["decision_target"], "candidate.impl")
            self.assertIn("approve", prepare_payload["review_summary"]["allowed_actions"])
            self.assertIn("## 需要你做的决定", prepare_payload["human_brief"]["markdown"])
            self.assertIn("approve", prepare_payload["human_brief"]["summary"]["allowed_actions"])
            self.assertIn("## Machine SSOT 人类友好全文", prepare_payload["human_brief"]["markdown"])
            self.assertIn("## Machine SSOT 文件骨架", prepare_payload["human_brief"]["markdown"])
            self.assertIn("## 关键待审阅点", prepare_payload["human_brief"]["markdown"])

            pending = self.run_cmd("show-pending", "--repo-root", str(repo_root), cwd=ROOT)
            self.assertEqual(pending.returncode, 0, pending.stderr)
            pending_payload = json.loads(pending.stdout)
            self.assertEqual(pending_payload["pending_count"], 1)
            self.assertEqual(pending_payload["items"][0]["run_id"], "gate-round")
            self.assertEqual(pending_payload["items"][0]["review_summary"]["status"], "pending_human_reply")
            self.assertEqual(pending_payload["items"][0]["review_summary"]["decision_target"], "candidate.impl")
            self.assertIn("## 可直接回复的格式", pending_payload["items"][0]["human_brief"]["markdown"])
            self.assertTrue(pending_payload["items"][0]["review_summary"]["ssot_fulltext_markdown"])
            self.assertTrue(pending_payload["items"][0]["review_summary"]["ssot_outline"])
            self.assertTrue(pending_payload["items"][0]["review_summary"]["review_checkpoints"])

            capture = self.run_cmd(
                "capture-decision",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--reply",
                "revise: Please tighten the evidence and target wording.",
                "--approver",
                "human/reviewer-001",
                cwd=ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)
            capture_payload = json.loads(capture.stdout)
            submission = json.loads((artifacts_dir / "human-decision-submission.json").read_text(encoding="utf-8"))
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            state = json.loads((artifacts_dir / "round-state.json").read_text(encoding="utf-8"))

            self.assertEqual(submission["decision"], "revise")
            self.assertEqual(bundle["decision"], "revise")
            self.assertTrue(any(item.endswith("human-decision-request.json") for item in bundle["source_refs"]))
            self.assertTrue(any(item.endswith("human-decision-submission.json") for item in bundle["source_refs"]))
            self.assertEqual(state["status"], "decision_recorded")
            self.assertEqual(capture_payload["decision"], "revise")

    def test_claim_next_pulls_from_runtime_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_gate_ready_package(repo_root)
            self.make_runtime_pending_item(repo_root, key="queue-item-001")

            claim = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "queue-round",
                cwd=ROOT,
            )
            self.assertEqual(claim.returncode, 0, claim.stderr)
            claim_payload = json.loads(claim.stdout)
            artifacts_dir = Path(claim_payload["artifacts_dir"])
            pending = json.loads((repo_root / "artifacts" / "active" / "gates" / "pending" / "queue-item-001.json").read_text(encoding="utf-8"))
            state = json.loads((artifacts_dir / "round-state.json").read_text(encoding="utf-8"))

            self.assertEqual(pending["claim_status"], "active")
            self.assertEqual(pending["claimed_run_id"], "queue-round")
            self.assertEqual(state["handoff_ref"], "artifacts/active/gates/handoffs/queue-item-001.json")
            self.assertTrue((artifacts_dir / "queue-claim.json").exists())
            self.assertTrue((artifacts_dir / "human-decision-request.json").exists())
            self.assertEqual(claim_payload["review_summary"]["status"], "pending_human_reply")
            self.assertEqual(claim_payload["review_summary"]["decision_target"], "candidate.impl")
            self.assertIn("revise: <原因>", claim_payload["review_summary"]["reply_examples"])
            self.assertIn("## 可直接回复的格式", claim_payload["human_brief"]["markdown"])

    def test_claim_next_reuses_existing_active_claim_for_same_actor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_gate_ready_package(repo_root)
            self.make_runtime_pending_item(repo_root, key="queue-item-002")

            first = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "queue-round-reuse",
                cwd=ROOT,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "queue-round-new",
                cwd=ROOT,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            second_payload = json.loads(second.stdout)

            self.assertTrue(second_payload["reused_active_claim"])
            self.assertEqual(second_payload["run_id"], "queue-round-reuse")
            self.assertEqual(second_payload["status"], "pending_human_reply")
            self.assertIn("## 待审批对象", second_payload["human_brief"]["markdown"])

    def test_claim_next_reuse_refreshes_missing_ssot_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_gate_ready_package(repo_root)
            self.make_runtime_pending_item(repo_root, key="queue-item-refresh")

            first = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "queue-round-refresh",
                cwd=ROOT,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            artifacts_dir = repo_root / "artifacts" / "gate-human-orchestrator" / "queue-round-refresh"
            request_path = artifacts_dir / "human-decision-request.json"
            request_payload = json.loads(request_path.read_text(encoding="utf-8"))
            request_payload["ssot_excerpt"] = []
            request_path.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            second = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "queue-round-refresh-r2",
                cwd=ROOT,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            second_payload = json.loads(second.stdout)
            refreshed_request = json.loads(request_path.read_text(encoding="utf-8"))

            self.assertTrue(second_payload["reused_active_claim"])
            self.assertTrue(refreshed_request["ssot_excerpt"])
            self.assertTrue(any(item.startswith("产品摘要:") for item in refreshed_request["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("完成态:") for item in refreshed_request["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("权威输出:") for item in refreshed_request["ssot_excerpt"]))

    def test_claim_next_legacy_queue_maps_payload_to_registry_candidate_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_legacy_runtime_pending_item(repo_root, key="legacy-queue-item")

            claim = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "legacy-round",
                cwd=ROOT,
            )
            self.assertEqual(claim.returncode, 0, claim.stderr)
            synthetic = json.loads(
                (repo_root / "artifacts" / "gate-human-orchestrator" / "legacy-round" / "synthetic-gate-ready-package.json").read_text(encoding="utf-8")
            )

            self.assertEqual(synthetic["payload"]["candidate_ref"], "formal.src.run-legacy")

    def test_prepare_round_feat_freeze_package_renders_human_friendly_bundle_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_feat_freeze_gate_ready_package(repo_root, run_id="feat-freeze-round")

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-feat-freeze-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            prepare_payload = json.loads(prepare.stdout)
            summary = prepare_payload["review_summary"]
            markdown = prepare_payload["human_brief"]["markdown"]

            self.assertTrue(any(item.startswith("Bundle 意图:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("拆分结果:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any("features[3]" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("Runner 用户入口流" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("用户入口" in item for item in summary["review_checkpoints"]))
            self.assertIn("### 本轮实际拆出的 FEAT", markdown)
            self.assertIn("Runner 用户入口流", markdown)
            self.assertIn("Runner 控制面流", markdown)
            self.assertIn("Runner 运行监控流", markdown)
            self.assertIn("workflow.dev.feat_to_tech", markdown)
            self.assertIn("### 这轮 FEAT 面向的关键角色", markdown)

    def test_prepare_round_tech_design_package_renders_human_friendly_implementation_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_tech_design_gate_ready_package(repo_root, run_id="tech-design-round")

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-tech-design-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            prepare_payload = json.loads(prepare.stdout)
            summary = prepare_payload["review_summary"]
            markdown = prepare_payload["human_brief"]["markdown"]

            self.assertTrue(any(item.startswith("实现目标:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("状态机:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("实现模块:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any("tech_design_package" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("state_model" in item or "可见字段" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("state_model" in item.lower() or "合同" in item for item in summary["review_checkpoints"]))
            self.assertIn("### 这份 TECH 主要在实现什么", markdown)
            self.assertIn("### 实现边界与职责分工", markdown)
            self.assertIn("### 计划落到哪些模块", markdown)
            self.assertIn("### 核心状态机", markdown)
            self.assertIn("### 关键接口合同", markdown)
            self.assertIn("workflow.dev.tech_to_impl", markdown)

    def test_prepare_round_test_set_package_renders_human_friendly_validation_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_test_set_gate_ready_package(repo_root, run_id="test-set-round")

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-test-set-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            prepare_payload = json.loads(prepare.stdout)
            summary = prepare_payload["review_summary"]
            markdown = prepare_payload["human_brief"]["markdown"]

            self.assertTrue(any(item.startswith("测试目标:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("关键测试单元:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("通过标准:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("下游执行目标:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any("test_set_candidate_package" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("fail-closed" in item or "环境" in item for item in summary["review_checkpoints"]))
            self.assertIn("### 这份 TESTSET 要覆盖什么", markdown)
            self.assertIn("### 明确不覆盖什么", markdown)
            self.assertIn("### 关键测试单元", markdown)
            self.assertIn("### 通过标准", markdown)
            self.assertIn("### 执行前置环境假设", markdown)
            self.assertIn("skill.qa.test_exec_cli", markdown)

    def test_prepare_round_impl_package_renders_human_friendly_delivery_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_impl_gate_ready_package(repo_root, run_id="impl-round")

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-impl-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            prepare_payload = json.loads(prepare.stdout)
            summary = prepare_payload["review_summary"]
            markdown = prepare_payload["human_brief"]["markdown"]

            self.assertTrue(any(item.startswith("实现目标:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("执行面:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("实施步骤:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any(item.startswith("交付模板:") for item in summary["ssot_excerpt"]))
            self.assertTrue(any("feature_impl_candidate_package" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("implementation_steps" in item or "交付输入" in item for item in summary["ssot_outline"]))
            self.assertTrue(any("IMPL" in item or "evidence" in item for item in summary["review_checkpoints"]))
            self.assertIn("### 这份 IMPL 具体覆盖什么", markdown)
            self.assertIn("### 必须继承的实现约束", markdown)
            self.assertIn("### 计划落到哪些模块", markdown)
            self.assertIn("### 核心状态机", markdown)
            self.assertIn("### 冻结接口合同", markdown)
            self.assertIn("### 实施任务拆分", markdown)
            self.assertIn("### 交付与验收", markdown)
            self.assertIn("template.dev.feature_delivery_l2", markdown)

    def test_capture_decision_refreshes_legacy_synthetic_round_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_legacy_runtime_pending_item(repo_root, key="legacy-capture-item")

            claim = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "legacy-capture-round",
                cwd=ROOT,
            )
            self.assertEqual(claim.returncode, 0, claim.stderr)
            artifacts_dir = repo_root / "artifacts" / "gate-human-orchestrator" / "legacy-capture-round"

            capture = self.run_cmd(
                "capture-decision",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--reply",
                "approve",
                "--approver",
                "human/reviewer-001",
                cwd=ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)
            submission = json.loads((artifacts_dir / "human-decision-submission.json").read_text(encoding="utf-8"))
            self.assertEqual(submission["decision_target"], "formal.src.run-legacy")

    def test_capture_decision_approve_materializes_formal_src_for_raw_to_src_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_raw_to_src_gate_ready_package(repo_root, run_id="raw-src-approve")

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-raw-src-approve",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            artifacts_dir = repo_root / "artifacts" / "gate-human-orchestrator" / "gate-raw-src-approve"

            capture = self.run_cmd(
                "capture-decision",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--reply",
                "approve",
                "--approver",
                "human/reviewer-001",
                cwd=ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))

            self.assertEqual(bundle["formal_ref"], "formal.src.raw-src-approve")
            self.assertEqual(bundle["assigned_id"], "SRC-001")
            self.assertTrue(bundle["materialized_ssot_ref"].endswith("materialized-src.json"))
            formal_path = repo_root / "ssot" / "src" / "SRC-001__src-candidate.md"
            self.assertTrue(formal_path.exists())
            self.assertIn("Approved content.", formal_path.read_text(encoding="utf-8"))

    def test_close_run_releases_claim_and_allows_next_queue_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_gate_ready_package(repo_root)
            self.make_runtime_pending_item(repo_root, key="queue-item-a")
            self.make_runtime_pending_item(repo_root, key="queue-item-b")

            first_claim = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "round-a",
                cwd=ROOT,
            )
            self.assertEqual(first_claim.returncode, 0, first_claim.stderr)
            first_artifacts_dir = repo_root / "artifacts" / "gate-human-orchestrator" / "round-a"

            capture = self.run_cmd(
                "capture-decision",
                "--artifacts-dir",
                str(first_artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--reply",
                "approve",
                "--approver",
                "human/reviewer-001",
                cwd=ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)

            close = self.run_cmd(
                "close-run",
                "--artifacts-dir",
                str(first_artifacts_dir),
                "--repo-root",
                str(repo_root),
                cwd=ROOT,
            )
            self.assertEqual(close.returncode, 0, close.stderr)
            close_payload = json.loads(close.stdout)
            closed_state = json.loads((first_artifacts_dir / "round-state.json").read_text(encoding="utf-8"))
            first_pending = json.loads((repo_root / "artifacts" / "active" / "gates" / "pending" / "queue-item-a.json").read_text(encoding="utf-8"))

            self.assertEqual(close_payload["status"], "closed")
            self.assertEqual(closed_state["status"], "closed")
            self.assertEqual(first_pending["claim_status"], "released")
            self.assertEqual(first_pending["pending_state"], "closed")

            second_claim = self.run_cmd(
                "claim-next",
                "--repo-root",
                str(repo_root),
                "--run-id",
                "round-b",
                cwd=ROOT,
            )
            self.assertEqual(second_claim.returncode, 0, second_claim.stderr)
            second_payload = json.loads(second_claim.stdout)
            self.assertEqual(second_payload["run_id"], "round-b")
            self.assertFalse(second_payload.get("reused_active_claim", False))
            self.assertTrue(second_payload["gate_pending_ref"].endswith("queue-item-b.json"))

    def test_close_run_rejects_pending_human_reply_round(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "close-guard-round",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            artifacts_dir = repo_root / "artifacts" / "gate-human-orchestrator" / "close-guard-round"

            close = self.run_cmd(
                "close-run",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                cwd=ROOT,
            )
            self.assertNotEqual(close.returncode, 0)
            self.assertIn("round is not closeable: pending_human_reply", close.stderr)

    def test_capture_comment_and_regenerate_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_gate_ready_package(repo_root)

            run_result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "gate-comment", cwd=ROOT)
            self.assertEqual(run_result.returncode, 0, run_result.stderr)
            artifacts_dir = Path(json.loads(run_result.stdout)["artifacts_dir"])

            comment_result = self.run_cmd(
                "capture-comment",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--comment-ref",
                "comment-001",
                "--comment-text",
                "Please tighten the product summary wording.",
                "--comment-author",
                "reviewer-A",
                "--target-block",
                "product_summary",
                cwd=ROOT,
            )
            self.assertEqual(comment_result.returncode, 0, comment_result.stderr)
            comment_payload = json.loads(comment_result.stdout)
            self.assertTrue(comment_payload["revision_request_ref"].endswith("comment-001.json"))

            updated_ssot = repo_root / "artifacts" / "active" / "run-001" / "candidate-updated.json"
            current = json.loads((repo_root / "artifacts" / "active" / "run-001" / "candidate.json").read_text(encoding="utf-8"))
            current["product_summary"] = "Updated summary after gate reviewer feedback."
            self.write_json(updated_ssot, current)

            regenerate_result = self.run_cmd(
                "regenerate-projection",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--updated-ssot-ref",
                "artifacts/active/run-001/candidate-updated.json",
                cwd=ROOT,
            )
            self.assertEqual(regenerate_result.returncode, 0, regenerate_result.stderr)
            bundle = json.loads((artifacts_dir / "gate-decision-bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["machine_ssot_ref"], "artifacts/active/run-001/candidate-updated.json")
            summary_block = next(block for block in bundle["human_projection"]["review_blocks"] if block["id"] == "product_summary")
            self.assertIn("Updated summary after gate reviewer feedback.", summary_block["content"][0])


if __name__ == "__main__":
    unittest.main()
