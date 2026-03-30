from __future__ import annotations

import json
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from cli.lib.errors import CommandError
from cli.lib.execution_return_registry import ExecutionReturnRoute, resolve_execution_return_route
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

    def create_execution_return_job(
        self,
        name: str = "job-return.json",
        *,
        run_id: str = "user-onboarding-v2-20260330",
        candidate_ref: str | None = None,
        authoritative_input_ref: str | None = None,
        decision_target: str | None = None,
    ) -> str:
        source_artifacts_dir = self.workspace / "artifacts" / "raw-to-src" / run_id
        source_artifacts_dir.mkdir(parents=True, exist_ok=True)
        raw_input_path = self.workspace / "artifacts" / "raw-to-src" / f"{run_id}-raw-requirement.md"
        raw_input_path.write_text("# raw requirement\n\nrevision fixture\n", encoding="utf-8")
        write_json(
            source_artifacts_dir / "execution-evidence.json",
            {
                "run_id": run_id,
                "input_path": str(raw_input_path),
            },
        )
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json",
            {
                "decision_type": "revise",
                "decision_reason": "补充 recent_injury_status，并把 running_level 收敛为单一训练基础轴。",
                "candidate_ref": candidate_ref or f"raw-to-src.{run_id}.src-candidate",
                "decision_target": decision_target or candidate_ref or f"raw-to-src.{run_id}.src-candidate",
                "decision_basis_refs": [
                    f"artifacts/raw-to-src/{run_id}/supervision-evidence.json",
                ],
            },
        )
        job_ref = f"artifacts/jobs/waiting-human/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "execution_return",
                "status": "waiting-human",
                "queue_path": job_ref,
                "target_skill": "execution.return",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "payload_ref": candidate_ref or f"raw-to-src.{run_id}.src-candidate",
                "input_refs": [
                    "artifacts/active/gates/decisions/gate-decision.json",
                    candidate_ref or f"raw-to-src.{run_id}.src-candidate",
                ],
                "authoritative_input_ref": authoritative_input_ref or candidate_ref or f"raw-to-src.{run_id}.src-candidate",
                "decision_type": "revise",
                "reason": "gate requested execution-side revision before resubmission",
                "source_run_id": run_id,
                "created_at": "2026-03-30T00:00:00Z",
            },
        )
        return job_ref

    def create_src_to_epic_execution_return_job(
        self,
        name: str = "job-src-to-epic-return.json",
        *,
        run_id: str = "epic-user-onboarding-v2-20260330",
        source_src_run_id: str = "user-onboarding-v2-20260330",
    ) -> str:
        source_artifacts_dir = self.workspace / "artifacts" / "src-to-epic" / run_id
        source_artifacts_dir.mkdir(parents=True, exist_ok=True)
        source_input_dir = self.workspace / "artifacts" / "raw-to-src" / source_src_run_id
        source_input_dir.mkdir(parents=True, exist_ok=True)
        write_json(
            source_artifacts_dir / "execution-evidence.json",
            {
                "run_id": run_id,
                "input_path": str(source_input_dir),
            },
        )
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json",
            {
                "decision_type": "revise",
                "decision_reason": "请把 revise 上下文显式保留到 epic constraints，并通过 revision_request 落盘。",
                "candidate_ref": f"src-to-epic.{run_id}.epic-freeze",
                "decision_target": f"src-to-epic.{run_id}.epic-freeze",
                "decision_basis_refs": [
                    f"artifacts/src-to-epic/{run_id}/supervision-evidence.json",
                ],
            },
        )
        job_ref = f"artifacts/jobs/waiting-human/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "execution_return",
                "status": "waiting-human",
                "queue_path": job_ref,
                "target_skill": "execution.return",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "payload_ref": f"src-to-epic.{run_id}.epic-freeze",
                "input_refs": [
                    "artifacts/active/gates/decisions/gate-decision.json",
                    f"src-to-epic.{run_id}.epic-freeze",
                ],
                "authoritative_input_ref": f"src-to-epic.{run_id}.epic-freeze",
                "source_run_id": run_id,
                "decision_type": "revise",
                "reason": "gate requested execution-side revision before resubmission",
                "created_at": "2026-03-30T00:00:00Z",
            },
        )
        return job_ref

    def create_feat_to_tech_execution_return_job(
        self,
        name: str = "job-feat-to-tech-return.json",
        *,
        run_id: str = "tech-user-onboarding-v2-20260330",
        feat_source_run_id: str = "feat-user-onboarding-v2-20260330",
        feat_ref: str = "FEAT-SRC-001-201",
    ) -> str:
        source_artifacts_dir = self.workspace / "artifacts" / "feat-to-tech" / run_id
        source_artifacts_dir.mkdir(parents=True, exist_ok=True)
        source_input_dir = self.workspace / "artifacts" / "epic-to-feat" / feat_source_run_id
        source_input_dir.mkdir(parents=True, exist_ok=True)
        write_json(source_artifacts_dir / "package-manifest.json", {"run_id": run_id, "feat_ref": feat_ref})
        write_json(source_artifacts_dir / "tech-design-bundle.json", {"feat_ref": feat_ref, "tech_ref": "TECH-SRC-001-201"})
        write_json(source_artifacts_dir / "execution-evidence.json", {"run_id": run_id, "input_path": str(source_input_dir)})
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json",
            {
                "decision_type": "revise",
                "decision_reason": "请保留 revision context 并约束 tech design 的补丁式更新。",
                "candidate_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
                "decision_target": f"feat-to-tech.{run_id}.tech-design-bundle",
            },
        )
        job_ref = f"artifacts/jobs/waiting-human/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "execution_return",
                "status": "waiting-human",
                "queue_path": job_ref,
                "target_skill": "execution.return",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "payload_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
                "input_refs": ["artifacts/active/gates/decisions/gate-decision.json", f"feat-to-tech.{run_id}.tech-design-bundle"],
                "authoritative_input_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
                "source_run_id": run_id,
                "decision_type": "revise",
                "reason": "gate requested execution-side revision before resubmission",
                "created_at": "2026-03-30T00:00:00Z",
            },
        )
        return job_ref

    def create_feat_to_testset_execution_return_job(
        self,
        name: str = "job-feat-to-testset-return.json",
        *,
        run_id: str = "testset-user-onboarding-v2-20260330",
        feat_source_run_id: str = "feat-user-onboarding-v2-20260330",
        feat_ref: str = "FEAT-SRC-001-202",
    ) -> str:
        source_artifacts_dir = self.workspace / "artifacts" / "feat-to-testset" / run_id
        source_artifacts_dir.mkdir(parents=True, exist_ok=True)
        source_input_dir = self.workspace / "artifacts" / "epic-to-feat" / feat_source_run_id
        source_input_dir.mkdir(parents=True, exist_ok=True)
        write_json(source_artifacts_dir / "package-manifest.json", {"run_id": run_id, "feat_ref": feat_ref})
        write_json(source_artifacts_dir / "test-set-bundle.json", {"feat_ref": feat_ref, "test_set_ref": "TESTSET-SRC-001-202"})
        write_json(source_artifacts_dir / "execution-evidence.json", {"run_id": run_id, "input_path": str(source_input_dir)})
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json",
            {
                "decision_type": "revise",
                "decision_reason": "请保留 revision context 并对 test set 做最小补丁修订。",
                "candidate_ref": f"feat-to-testset.{run_id}.test-set-bundle",
                "decision_target": f"feat-to-testset.{run_id}.test-set-bundle",
            },
        )
        job_ref = f"artifacts/jobs/waiting-human/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "execution_return",
                "status": "waiting-human",
                "queue_path": job_ref,
                "target_skill": "execution.return",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "payload_ref": f"feat-to-testset.{run_id}.test-set-bundle",
                "input_refs": ["artifacts/active/gates/decisions/gate-decision.json", f"feat-to-testset.{run_id}.test-set-bundle"],
                "authoritative_input_ref": f"feat-to-testset.{run_id}.test-set-bundle",
                "source_run_id": run_id,
                "decision_type": "revise",
                "reason": "gate requested execution-side revision before resubmission",
                "created_at": "2026-03-30T00:00:00Z",
            },
        )
        return job_ref

    def create_tech_to_impl_execution_return_job(
        self,
        name: str = "job-tech-to-impl-return.json",
        *,
        run_id: str = "impl-user-onboarding-v2-20260330",
        tech_source_run_id: str = "tech-user-onboarding-v2-20260330",
        feat_ref: str = "FEAT-SRC-001-401",
        tech_ref: str = "TECH-SRC-001-401",
    ) -> str:
        source_artifacts_dir = self.workspace / "artifacts" / "tech-to-impl" / run_id
        source_artifacts_dir.mkdir(parents=True, exist_ok=True)
        source_input_dir = self.workspace / "artifacts" / "feat-to-tech" / tech_source_run_id
        source_input_dir.mkdir(parents=True, exist_ok=True)
        write_json(source_artifacts_dir / "package-manifest.json", {"run_id": run_id, "feat_ref": feat_ref, "tech_ref": tech_ref})
        write_json(source_artifacts_dir / "impl-bundle.json", {"feat_ref": feat_ref, "tech_ref": tech_ref, "impl_ref": "IMPL-SRC-001-401"})
        write_json(source_artifacts_dir / "execution-evidence.json", {"run_id": run_id, "input_path": str(source_input_dir)})
        write_json(
            self.workspace / "artifacts" / "active" / "gates" / "decisions" / "gate-decision.json",
            {
                "decision_type": "revise",
                "decision_reason": "请保留 revision context 并对 impl bundle 做最小补丁修订。",
                "candidate_ref": f"tech-to-impl.{run_id}.impl-bundle",
                "decision_target": f"tech-to-impl.{run_id}.impl-bundle",
            },
        )
        job_ref = f"artifacts/jobs/waiting-human/{name}"
        write_json(
            self.workspace / job_ref,
            {
                "job_id": Path(name).stem,
                "job_type": "execution_return",
                "status": "waiting-human",
                "queue_path": job_ref,
                "target_skill": "execution.return",
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "payload_ref": f"tech-to-impl.{run_id}.impl-bundle",
                "input_refs": ["artifacts/active/gates/decisions/gate-decision.json", f"tech-to-impl.{run_id}.impl-bundle"],
                "authoritative_input_ref": f"tech-to-impl.{run_id}.impl-bundle",
                "source_run_id": run_id,
                "decision_type": "revise",
                "reason": "gate requested execution-side revision before resubmission",
                "created_at": "2026-03-30T00:00:00Z",
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

    def test_gate_dispatch_execution_return_derives_registered_workflow_source_run_id(self) -> None:
        decision_ref = "artifacts/active/gates/decisions/gate-decision.json"
        write_json(
            self.workspace / decision_ref,
            {
                "decision_type": "revise",
                "candidate_ref": "src-to-epic.epic-user-onboarding-v2-20260330.epic-freeze",
                "decision_target": "src-to-epic.epic-user-onboarding-v2-20260330.epic-freeze",
            },
        )
        dispatch_request = self.build_request("gate.dispatch", {"gate_decision_ref": decision_ref})
        dispatch_path = self.request_path("gate-dispatch-src-to-epic-return.json")
        write_json(dispatch_path, dispatch_request)
        dispatch_response = self.response_path("gate-dispatch-src-to-epic-return.response.json")
        self.assertEqual(self.run_cli("gate", "dispatch", "--request", str(dispatch_path), "--response-out", str(dispatch_response)), 0)

        payload = read_json(dispatch_response)
        job = read_json(self.workspace / payload["data"]["materialized_job_ref"])
        self.assertEqual(job["status"], "waiting-human")
        self.assertEqual(job["authoritative_input_ref"], "src-to-epic.epic-user-onboarding-v2-20260330.epic-freeze")
        self.assertEqual(job["source_run_id"], "epic-user-onboarding-v2-20260330")
        self.assertEqual(job["workflow_key"], "product.src-to-epic")

    def test_invoke_target_supports_execution_return(self) -> None:
        source_run_id = "user-onboarding-v2-20260330"
        repo_root = Path(__file__).resolve().parents[2]
        raw_src_scripts = repo_root / "skills" / "ll-product-raw-to-src" / "scripts"
        if str(raw_src_scripts) not in sys.path:
            sys.path.insert(0, str(raw_src_scripts))
            self.addCleanup(lambda: sys.path.remove(str(raw_src_scripts)) if str(raw_src_scripts) in sys.path else None)
        job_ref = self.create_execution_return_job(run_id=source_run_id)
        job = read_json(self.workspace / job_ref)
        with patch("raw_to_src_runtime.run_workflow", return_value={"ok": True, "artifacts_dir": str(self.workspace / "artifacts" / "raw-to-src" / source_run_id)}) as run_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={"run_ref": "RUN-RUNNER-001"},
                request_id="req-return",
                job=job,
                job_ref=job_ref,
            )
        run_mock.assert_called_once()
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["run_id"], source_run_id)
        self.assertTrue(kwargs["allow_update"])
        self.assertEqual(Path(kwargs["input_path"]), self.workspace / "artifacts" / "raw-to-src" / f"{source_run_id}-raw-requirement.md")
        self.assertEqual(Path(kwargs["revision_request_path"]), self.workspace / "artifacts" / "raw-to-src" / source_run_id / "revision-request.json")
        self.assertEqual(result["target_skill"], "execution.return")
        revision_request = read_json(self.workspace / "artifacts" / "raw-to-src" / source_run_id / "revision-request.json")
        self.assertEqual(revision_request["revision_round"], 1)
        self.assertEqual(revision_request["source_return_job_ref"], job_ref)
        self.assertEqual(revision_request["source_run_id"], source_run_id)
        self.assertEqual(revision_request["decision_reason"], "补充 recent_injury_status，并把 running_level 收敛为单一训练基础轴。")
        self.assertIn(f"artifacts/raw-to-src/{source_run_id}/supervision-evidence.json", revision_request["basis_refs"])

    def test_invoke_target_supports_execution_return_for_src_to_epic(self) -> None:
        source_run_id = "epic-user-onboarding-v2-20260330"
        repo_root = Path(__file__).resolve().parents[2]
        src_to_epic_scripts = repo_root / "skills" / "ll-product-src-to-epic" / "scripts"
        if str(src_to_epic_scripts) not in sys.path:
            sys.path.insert(0, str(src_to_epic_scripts))
            self.addCleanup(lambda: sys.path.remove(str(src_to_epic_scripts)) if str(src_to_epic_scripts) in sys.path else None)
        job_ref = self.create_src_to_epic_execution_return_job(run_id=source_run_id)
        job = read_json(self.workspace / job_ref)
        with patch("src_to_epic_runtime.run_workflow", return_value={"ok": True, "artifacts_dir": str(self.workspace / "artifacts" / "src-to-epic" / source_run_id)}) as run_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={"run_ref": "RUN-RUNNER-002"},
                request_id="req-return-src-to-epic",
                job=job,
                job_ref=job_ref,
            )
        run_mock.assert_called_once()
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["run_id"], source_run_id)
        self.assertTrue(kwargs["allow_update"])
        self.assertEqual(Path(kwargs["input_path"]), self.workspace / "artifacts" / "raw-to-src" / "user-onboarding-v2-20260330")
        self.assertEqual(Path(kwargs["revision_request_path"]), self.workspace / "artifacts" / "src-to-epic" / source_run_id / "revision-request.json")
        self.assertEqual(result["workflow_key"], "product.src-to-epic")
        revision_request = read_json(self.workspace / "artifacts" / "src-to-epic" / source_run_id / "revision-request.json")
        self.assertEqual(revision_request["source_run_id"], source_run_id)
        self.assertEqual(revision_request["candidate_ref"], f"src-to-epic.{source_run_id}.epic-freeze")
        self.assertEqual(revision_request["decision_reason"], "请把 revise 上下文显式保留到 epic constraints，并通过 revision_request 落盘。")

    def test_invoke_target_supports_execution_return_for_feat_to_tech(self) -> None:
        source_run_id = "tech-user-onboarding-v2-20260330"
        repo_root = Path(__file__).resolve().parents[2]
        scripts_dir = repo_root / "skills" / "ll-dev-feat-to-tech" / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
            self.addCleanup(lambda: sys.path.remove(str(scripts_dir)) if str(scripts_dir) in sys.path else None)
        job_ref = self.create_feat_to_tech_execution_return_job(run_id=source_run_id)
        job = read_json(self.workspace / job_ref)
        with patch("feat_to_tech_runtime.run_workflow", return_value={"ok": True, "artifacts_dir": str(self.workspace / "artifacts" / "feat-to-tech" / source_run_id)}) as run_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={"run_ref": "RUN-RUNNER-003"},
                request_id="req-return-feat-to-tech",
                job=job,
                job_ref=job_ref,
            )
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["run_id"], source_run_id)
        self.assertEqual(kwargs["feat_ref"], "FEAT-SRC-001-201")
        self.assertEqual(Path(kwargs["input_path"]), self.workspace / "artifacts" / "epic-to-feat" / "feat-user-onboarding-v2-20260330")
        self.assertEqual(Path(kwargs["revision_request_path"]), self.workspace / "artifacts" / "feat-to-tech" / source_run_id / "revision-request.json")
        self.assertEqual(result["workflow_key"], "dev.feat-to-tech")

    def test_invoke_target_supports_execution_return_for_feat_to_testset(self) -> None:
        source_run_id = "testset-user-onboarding-v2-20260330"
        repo_root = Path(__file__).resolve().parents[2]
        scripts_dir = repo_root / "skills" / "ll-qa-feat-to-testset" / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
            self.addCleanup(lambda: sys.path.remove(str(scripts_dir)) if str(scripts_dir) in sys.path else None)
        job_ref = self.create_feat_to_testset_execution_return_job(run_id=source_run_id)
        job = read_json(self.workspace / job_ref)
        with patch("feat_to_testset_runtime.run_workflow", return_value={"ok": True, "artifacts_dir": str(self.workspace / "artifacts" / "feat-to-testset" / source_run_id)}) as run_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={"run_ref": "RUN-RUNNER-004"},
                request_id="req-return-feat-to-testset",
                job=job,
                job_ref=job_ref,
            )
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["run_id"], source_run_id)
        self.assertEqual(kwargs["feat_ref"], "FEAT-SRC-001-202")
        self.assertEqual(Path(kwargs["input_path"]), self.workspace / "artifacts" / "epic-to-feat" / "feat-user-onboarding-v2-20260330")
        self.assertEqual(Path(kwargs["revision_request_path"]), self.workspace / "artifacts" / "feat-to-testset" / source_run_id / "revision-request.json")
        self.assertEqual(result["workflow_key"], "qa.feat-to-testset")

    def test_invoke_target_supports_execution_return_for_tech_to_impl(self) -> None:
        source_run_id = "impl-user-onboarding-v2-20260330"
        repo_root = Path(__file__).resolve().parents[2]
        scripts_dir = repo_root / "skills" / "ll-dev-tech-to-impl" / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
            self.addCleanup(lambda: sys.path.remove(str(scripts_dir)) if str(scripts_dir) in sys.path else None)
        job_ref = self.create_tech_to_impl_execution_return_job(run_id=source_run_id)
        job = read_json(self.workspace / job_ref)
        with patch("tech_to_impl_runtime.run_workflow", return_value={"ok": True, "artifacts_dir": str(self.workspace / "artifacts" / "tech-to-impl" / source_run_id)}) as run_mock:
            result = invoke_target(
                workspace_root=self.workspace,
                trace={"run_ref": "RUN-RUNNER-005"},
                request_id="req-return-tech-to-impl",
                job=job,
                job_ref=job_ref,
            )
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["run_id"], source_run_id)
        self.assertEqual(kwargs["feat_ref"], "FEAT-SRC-001-401")
        self.assertEqual(kwargs["tech_ref"], "TECH-SRC-001-401")
        self.assertEqual(Path(kwargs["input_path"]), self.workspace / "artifacts" / "feat-to-tech" / "tech-user-onboarding-v2-20260330")
        self.assertEqual(Path(kwargs["revision_request_path"]), self.workspace / "artifacts" / "tech-to-impl" / source_run_id / "revision-request.json")
        self.assertEqual(result["workflow_key"], "dev.tech-to-impl")

    def test_execution_return_route_registry_resolves_by_candidate_ref(self) -> None:
        job = {
            "candidate_ref": "raw-to-src.demo-run.src-candidate",
            "authoritative_input_ref": "raw-to-src.demo-run.src-candidate",
        }
        decision = {
            "candidate_ref": "raw-to-src.demo-run.src-candidate",
            "decision_target": "raw-to-src.demo-run.src-candidate",
        }
        resolution = resolve_execution_return_route(job, decision)
        self.assertEqual(resolution.route.workflow_key, "product.raw-to-src")
        self.assertEqual(resolution.matched_field, "candidate_ref")
        self.assertEqual(resolution.source_run_id, "demo-run")

    def test_execution_return_route_registry_prefers_authoritative_input_ref_when_candidate_missing(self) -> None:
        fake_route = ExecutionReturnRoute(
            workflow_key="workflow.product.fake",
            artifacts_subdir="fake-workflow",
            scripts_subdir="fake-workflow",
            runtime_module="fake_runtime",
            candidate_ref_patterns=(re.compile(r"^fake-workflow\.(?P<run_id>.+)\.candidate$"),),
            build_runtime_kwargs=lambda context: {},
            authoritative_ref_patterns=(re.compile(r"^fake-workflow\.(?P<run_id>.+)\.candidate$"),),
        )
        job = {"authoritative_input_ref": "fake-workflow.demo.candidate"}
        decision = {"candidate_ref": "", "decision_target": "", "decision_reason": "revise"}
        with patch("cli.lib.execution_return_registry._EXECUTION_RETURN_ROUTES", [fake_route]):
            resolution = resolve_execution_return_route(job, decision)
        self.assertEqual(resolution.route.workflow_key, "workflow.product.fake")
        self.assertEqual(resolution.matched_field, "authoritative_input_ref")
        self.assertEqual(resolution.source_run_id, "demo")

    def test_execution_return_route_registry_resolves_feat_to_tech_candidate(self) -> None:
        job = {
            "candidate_ref": "feat-to-tech.demo-run.tech-design-bundle",
            "authoritative_input_ref": "feat-to-tech.demo-run.tech-design-bundle",
        }
        decision = {
            "candidate_ref": "feat-to-tech.demo-run.tech-design-bundle",
            "decision_target": "feat-to-tech.demo-run.tech-design-bundle",
        }
        resolution = resolve_execution_return_route(job, decision)
        self.assertEqual(resolution.route.workflow_key, "dev.feat-to-tech")
        self.assertEqual(resolution.source_run_id, "demo-run")

    def test_execution_return_route_registry_resolves_tech_to_impl_candidate(self) -> None:
        job = {
            "candidate_ref": "tech-to-impl.demo-run.impl-bundle",
            "authoritative_input_ref": "tech-to-impl.demo-run.impl-bundle",
        }
        decision = {
            "candidate_ref": "tech-to-impl.demo-run.impl-bundle",
            "decision_target": "tech-to-impl.demo-run.impl-bundle",
        }
        resolution = resolve_execution_return_route(job, decision)
        self.assertEqual(resolution.route.workflow_key, "dev.tech-to-impl")
        self.assertEqual(resolution.source_run_id, "demo-run")

    def test_loop_run_execution_releases_and_consumes_execution_return_job(self) -> None:
        job_ref = self.create_execution_return_job(name="job-return-loop.json")
        request = self.build_request("loop.run-execution", {"consume_all": True})
        request_path = self.request_path("loop-run-return.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-run-return.response.json")
        repo_root = Path(__file__).resolve().parents[2]
        raw_src_scripts = repo_root / "skills" / "ll-product-raw-to-src" / "scripts"
        if str(raw_src_scripts) not in sys.path:
            sys.path.insert(0, str(raw_src_scripts))
            self.addCleanup(lambda: sys.path.remove(str(raw_src_scripts)) if str(raw_src_scripts) in sys.path else None)
        with patch("raw_to_src_runtime.run_workflow", return_value={"ok": True, "artifacts_dir": str(self.workspace / "artifacts" / "raw-to-src" / "user-onboarding-v2-20260330")}) as run_mock:
            self.assertEqual(self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]
        self.assertEqual(payload["processed_count"], 1)
        self.assertEqual(len(payload["released_execution_return_jobs"]), 1)
        processed = payload["processed_jobs"][0]
        final_job = read_json(self.workspace / processed["final_job_ref"])
        self.assertEqual(final_job["status"], "done")
        self.assertFalse((self.workspace / "artifacts" / "jobs" / "waiting-human" / "job-return-loop.json").exists())
        self.assertTrue((self.workspace / "artifacts" / "jobs" / "done" / "job-return-loop.json").exists())
        run_mock.assert_called_once()

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
