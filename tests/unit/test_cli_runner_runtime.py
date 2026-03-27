from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from cli.lib.errors import CommandError
from cli.lib.execution_runner import run_job
from cli.lib.job_outcome import complete_job
from cli.lib.job_queue import claim_job
from cli.ll import main
from cli.lib.skill_invoker import invoke_target


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CliRunnerRuntimeTest(unittest.TestCase):
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
            "trace": {"run_ref": "RUN-RUNNER-001"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def create_ready_job(self, name: str = "job-001.json") -> str:
        job_ref = f"artifacts/jobs/ready/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "next_skill",
                "status": "ready",
                "queue_path": job_ref,
                "target_skill": "workflow.dev.feat_to_tech",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "handoff_ref": "artifacts/active/handoffs/handoff.json",
                "input_refs": ["artifacts/active/gates/decisions/gate-decision.json", "formal.feat.demo"],
                "authoritative_input_ref": "formal.feat.demo",
                "formal_ref": "formal.feat.demo",
                "published_ref": "ssot/feat/FEAT-DEMO.md",
                "source_run_id": "RUN-RUNNER-001",
                "retry_count": 0,
                "retry_budget": 1,
                "created_at": "2026-03-26T00:00:00Z",
                "feat_ref": "FEAT-DEMO-001",
            },
        )
        return job_ref

    def test_job_claim_run_and_complete(self) -> None:
        ready_job_ref = self.create_ready_job()
        claim_request = self.build_request("job.claim", {"ready_job_ref": ready_job_ref})
        claim_path = self.request_path("job-claim.json")
        write_json(claim_path, claim_request)
        claim_response = self.response_path("job-claim.response.json")
        self.assertEqual(self.run_cli("job", "claim", "--request", str(claim_path), "--response-out", str(claim_response)), 0)
        claimed = read_json(claim_response)
        claimed_job_ref = claimed["data"]["claimed_job_ref"]
        claimed_job = read_json(self.workspace / claimed_job_ref)
        self.assertEqual(claimed_job["status"], "claimed")

        run_request = self.build_request("job.run", {"job_ref": claimed_job_ref})
        run_path = self.request_path("job-run.json")
        write_json(run_path, run_request)
        run_response = self.response_path("job-run.response.json")
        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True, "artifacts_dir": "artifacts/downstream/demo"}},
        ):
            self.assertEqual(self.run_cli("job", "run", "--request", str(run_path), "--response-out", str(run_response)), 0)
        run_payload = read_json(run_response)
        running_job = read_json(self.workspace / run_payload["data"]["job_ref"])
        self.assertEqual(running_job["status"], "running")

        complete_request = self.build_request(
            "job.complete",
            {"job_ref": run_payload["data"]["job_ref"], "execution_attempt_ref": run_payload["data"]["execution_attempt_ref"]},
        )
        complete_path = self.request_path("job-complete.json")
        write_json(complete_path, complete_request)
        complete_response = self.response_path("job-complete.response.json")
        self.assertEqual(self.run_cli("job", "complete", "--request", str(complete_path), "--response-out", str(complete_response)), 0)
        complete_payload = read_json(complete_response)
        done_job = read_json(self.workspace / complete_payload["data"]["completed_job_ref"])
        self.assertEqual(done_job["status"], "done")

    def test_loop_run_execution_consumes_ready_job(self) -> None:
        self.create_ready_job("job-loop.json")
        request = self.build_request("loop.run-execution", {"consume_all": True})
        request_path = self.request_path("loop-run.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-run.response.json")
        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)
        self.assertEqual(payload["data"]["processed_count"], 1)
        processed = payload["data"]["processed_jobs"][0]
        final_job = read_json(self.workspace / processed["final_job_ref"])
        self.assertEqual(final_job["status"], "done")
        self.assertFalse((self.workspace / "artifacts" / "jobs" / "ready" / "job-loop.json").exists())

    def test_loop_run_execution_bootstraps_runner_context_when_entry_payload_present(self) -> None:
        self.create_ready_job("job-loop-entry.json")
        request = self.build_request(
            "loop.run-execution",
            {
                "consume_all": True,
                "entry_mode": "start",
                "runner_scope_ref": "runner.scope.default",
                "runner_run_id": "runner-loop-start-001",
            },
        )
        request_path = self.request_path("loop-run-entry.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-run-entry.response.json")
        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]
        self.assertEqual(payload["entry_mode"], "start")
        self.assertEqual(payload["runner_scope_ref"], "runner.scope.default")
        self.assertEqual(payload["runner_run_id"], "runner-loop-start-001")
        self.assertTrue((self.workspace / payload["runner_context_ref"]).exists())
        self.assertTrue((self.workspace / payload["entry_receipt_ref"]).exists())
        context = read_json(self.workspace / payload["runner_context_ref"])
        self.assertEqual(context["runner_run_id"], "runner-loop-start-001")

    def test_loop_resume_execution_restores_existing_context(self) -> None:
        start_request = self.build_request(
            "loop.run-execution",
            {
                "entry_mode": "start",
                "runner_scope_ref": "runner.scope.default",
                "runner_run_id": "runner-loop-start-ctx-001",
            },
        )
        start_request_path = self.request_path("loop-run-start.json")
        start_response_path = self.response_path("loop-run-start.response.json")
        write_json(start_request_path, start_request)
        self.assertEqual(self.run_cli("loop", "run-execution", "--request", str(start_request_path), "--response-out", str(start_response_path)), 0)

        self.create_ready_job("job-loop-resume.json")
        resume_request = self.build_request(
            "loop.resume-execution",
            {
                "runner_scope_ref": "runner.scope.default",
                "consume_all": True,
                "runner_run_id": "ignored-runner-id",
            },
        )
        resume_request_path = self.request_path("loop-resume.json")
        resume_response_path = self.response_path("loop-resume.response.json")
        write_json(resume_request_path, resume_request)
        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(self.run_cli("loop", "resume-execution", "--request", str(resume_request_path), "--response-out", str(resume_response_path)), 0)
        payload = read_json(resume_response_path)["data"]
        self.assertEqual(payload["entry_mode"], "resume")
        self.assertEqual(payload["runner_run_id"], "runner-loop-start-ctx-001")
        context = read_json(self.workspace / payload["runner_context_ref"])
        self.assertEqual(context["runner_run_id"], "runner-loop-start-ctx-001")
        done_job = read_json(self.workspace / payload["processed_jobs"][0]["final_job_ref"])
        self.assertEqual(done_job["runner_run_id"], "runner-loop-start-ctx-001")

    def test_loop_show_status_and_backlog(self) -> None:
        self.create_ready_job("job-backlog.json")
        write_json(
            self.workspace / "artifacts" / "jobs" / "done" / "job-done.json",
            {
                "job_id": "job-done",
                "status": "done",
                "target_skill": "workflow.dev.feat_to_tech",
            },
        )
        status_request = self.build_request("loop.show-status", {})
        status_path = self.request_path("loop-status.json")
        write_json(status_path, status_request)
        status_response = self.response_path("loop-status.response.json")
        self.assertEqual(self.run_cli("loop", "show-status", "--request", str(status_path), "--response-out", str(status_response)), 0)
        status_payload = read_json(status_response)
        self.assertEqual(status_payload["data"]["counts"]["ready"], 1)
        self.assertEqual(status_payload["data"]["counts"]["done"], 1)

        backlog_request = self.build_request("loop.show-backlog", {})
        backlog_path = self.request_path("loop-backlog.json")
        write_json(backlog_path, backlog_request)
        backlog_response = self.response_path("loop-backlog.response.json")
        self.assertEqual(self.run_cli("loop", "show-backlog", "--request", str(backlog_path), "--response-out", str(backlog_response)), 0)
        backlog_payload = read_json(backlog_response)
        self.assertEqual(backlog_payload["data"]["status_filter"], "ready")
        self.assertEqual(len(backlog_payload["data"]["jobs"]), 1)

    def test_gate_dispatch_formal_src_emits_src_to_epic_job(self) -> None:
        run_id = "raw-src-runner"
        decision_ref = "artifacts/active/gates/decisions/gate-decision.json"
        write_json(
            self.workspace / "artifacts" / "registry" / f"formal-src-{run_id}.json",
            {
                "artifact_ref": f"formal.src.{run_id}",
                "managed_artifact_ref": "ssot/src/SRC-001__runner-test.md",
                "status": "materialized",
                "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
                "metadata": {
                    "assigned_id": "SRC-001",
                    "source_package_ref": f"artifacts/raw-to-src/{run_id}",
                },
                "lineage": [decision_ref],
            },
        )
        write_json(
            self.workspace / decision_ref,
            {
                "decision_type": "approve",
                "candidate_ref": f"raw-to-src.{run_id}.src-candidate",
                "formal_ref": f"formal.src.{run_id}",
                "published_ref": "ssot/src/SRC-001__runner-test.md",
                "materialized_handoff_ref": "artifacts/active/handoffs/gate-ready.json",
            },
        )
        dispatch_request = self.build_request("gate.dispatch", {"gate_decision_ref": decision_ref})
        dispatch_path = self.request_path("gate-dispatch-src.json")
        write_json(dispatch_path, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-src.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_path), "--response-out", str(dispatch_response)), 0)

        payload = read_json(dispatch_response)
        self.assertEqual(len(payload["data"]["materialized_job_refs"]), 1)
        job = read_json(self.workspace / payload["data"]["materialized_job_ref"])
        self.assertEqual(job["status"], "ready")
        self.assertEqual(job["target_skill"], "workflow.product.src_to_epic")
        self.assertEqual(job["src_ref"], "SRC-001")
        self.assertEqual(job["authoritative_input_ref"], f"formal.src.{run_id}")

    def test_gate_dispatch_formal_epic_emits_epic_to_feat_job(self) -> None:
        run_id = "src-epic-runner"
        decision_ref = "artifacts/active/gates/decisions/gate-decision.json"
        write_json(
            self.workspace / "artifacts" / "registry" / f"formal-epic-{run_id}.json",
            {
                "artifact_ref": f"formal.epic.{run_id}",
                "managed_artifact_ref": "ssot/epic/EPIC-SRC-001-001__runner-test.md",
                "status": "materialized",
                "trace": {"run_ref": run_id, "workflow_key": "product.src-to-epic"},
                "metadata": {
                    "assigned_id": "EPIC-SRC-001-001",
                    "src_ref": "SRC-001",
                    "source_package_ref": f"artifacts/src-to-epic/{run_id}",
                },
                "lineage": [decision_ref],
            },
        )
        write_json(
            self.workspace / decision_ref,
            {
                "decision_type": "approve",
                "candidate_ref": f"src-to-epic.{run_id}.epic-freeze",
                "formal_ref": f"formal.epic.{run_id}",
                "published_ref": "ssot/epic/EPIC-SRC-001-001__runner-test.md",
                "materialized_handoff_ref": "artifacts/active/handoffs/gate-ready.json",
            },
        )
        dispatch_request = self.build_request("gate.dispatch", {"gate_decision_ref": decision_ref})
        dispatch_path = self.request_path("gate-dispatch-epic.json")
        write_json(dispatch_path, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-epic.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_path), "--response-out", str(dispatch_response)), 0)

        payload = read_json(dispatch_response)
        self.assertEqual(len(payload["data"]["materialized_job_refs"]), 1)
        job = read_json(self.workspace / payload["data"]["materialized_job_ref"])
        self.assertEqual(job["status"], "ready")
        self.assertEqual(job["target_skill"], "workflow.product.epic_to_feat")
        self.assertEqual(job["epic_ref"], "EPIC-SRC-001-001")
        self.assertEqual(job["src_ref"], "SRC-001")

    def test_gate_dispatch_execution_return_uses_waiting_human_queue(self) -> None:
        decision_ref = "artifacts/active/gates/decisions/gate-decision.json"
        write_json(
            self.workspace / decision_ref,
            {
                "decision_type": "revise",
                "candidate_ref": "candidate.impl",
                "decision_target": "artifacts/impl/run-001",
            },
        )
        dispatch_request = self.build_request("gate.dispatch", {"gate_decision_ref": decision_ref})
        dispatch_path = self.request_path("gate-dispatch-return.json")
        write_json(dispatch_path, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-return.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_path), "--response-out", str(dispatch_response)), 0)

        payload = read_json(dispatch_response)
        job_ref = payload["data"]["materialized_job_ref"]
        self.assertTrue(job_ref.startswith("artifacts/jobs/waiting-human/"))
        job = read_json(self.workspace / job_ref)
        self.assertEqual(job["status"], "waiting-human")
        self.assertEqual(job["authoritative_input_ref"], "artifacts/impl/run-001")
        self.assertFalse((self.workspace / "artifacts" / "jobs" / "ready" / "gate-decision-return.json").exists())

    def test_invoke_target_supports_product_runner_targets(self) -> None:
        with patch("cli.lib.skill_invoker._invoke_src_to_epic", return_value={"ok": True, "target_skill": "workflow.product.src_to_epic"}) as src_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={},
                request_id="req-src",
                job={"target_skill": "workflow.product.src_to_epic", "formal_ref": "formal.src.demo"},
            )
        src_mock.assert_called_once()
        self.assertEqual(result["target_skill"], "workflow.product.src_to_epic")

        with patch(
            "cli.lib.skill_invoker._invoke_epic_to_feat",
            return_value={"ok": True, "target_skill": "workflow.product.epic_to_feat"},
        ) as epic_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={},
                request_id="req-epic",
                job={"target_skill": "workflow.product.epic_to_feat", "formal_ref": "formal.epic.demo"},
            )
        epic_mock.assert_called_once()
        self.assertEqual(result["target_skill"], "workflow.product.epic_to_feat")

    def test_runner_enforces_claim_owner_and_running_only_completion(self) -> None:
        ready_job_ref = self.create_ready_job("job-owner.json")
        claimed = claim_job(
            self.workspace,
            ready_job_ref,
            runner_id="runner-a",
            actor_ref="runner-a",
            runner_run_id="run-owner",
        )
        with self.assertRaises(CommandError):
            run_job(
                self.workspace,
                job_ref=claimed["job_ref"],
                trace={},
                request_id="req-owner-mismatch",
                actor_ref="runner-b",
                owner_ref="runner-b",
                payload={},
            )

        attempt = run_job(
            self.workspace,
            job_ref=claimed["job_ref"],
            trace={},
            request_id="req-owner-match",
            actor_ref="runner-a",
            owner_ref="runner-a",
            payload={},
        )
        with self.assertRaises(CommandError):
            complete_job(
                self.workspace,
                job_ref=attempt["job_ref"],
                trace={},
                actor_ref="runner-b",
                owner_ref="runner-b",
                execution_attempt_ref=attempt["execution_attempt_ref"],
            )

    def test_invoke_src_to_epic_prefers_authoritative_input_ref(self) -> None:
        captured: dict[str, str] = {}
        fake_module = types.ModuleType("src_to_epic_runtime")

        def fake_run_workflow(*, input_path: str, repo_root: Path, run_id: str, allow_update: bool) -> dict:
            captured["input_path"] = input_path
            return {"ok": True, "run_id": run_id}

        fake_module.run_workflow = fake_run_workflow
        with patch.dict(sys.modules, {"src_to_epic_runtime": fake_module}):
            result = invoke_target(
                workspace_root=self.workspace,
                trace={},
                request_id="req-src-input",
                job={
                    "target_skill": "workflow.product.src_to_epic",
                    "formal_ref": "formal.src.demo",
                    "authoritative_input_ref": "ssot/src/SRC-001__demo.md",
                },
            )
        self.assertEqual(captured["input_path"], "ssot/src/SRC-001__demo.md")
        self.assertTrue(result["ok"])
