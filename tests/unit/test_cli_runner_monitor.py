from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli.ll import main


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CliRunnerMonitorTest(unittest.TestCase):
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
            "trace": {"run_ref": "RUN-MONITOR-001"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def create_job(
        self,
        *,
        status: str,
        name: str,
        target_skill: str,
        created_at: str,
        retry_count: int = 0,
        retry_budget: int = 0,
        extras: dict | None = None,
    ) -> str:
        directory = {
            "ready": "artifacts/jobs/ready",
            "claimed": "artifacts/jobs/running",
            "running": "artifacts/jobs/running",
            "done": "artifacts/jobs/done",
            "failed": "artifacts/jobs/failed",
            "waiting-human": "artifacts/jobs/waiting-human",
            "deadletter": "artifacts/jobs/deadletter",
        }[status]
        job_ref = f"{directory}/{name}"
        payload = {
            "job_id": Path(name).stem,
            "job_type": "next_skill",
            "status": status,
            "queue_path": job_ref,
            "target_skill": target_skill,
            "created_at": created_at,
            "retry_count": retry_count,
            "retry_budget": retry_budget,
        }
        if extras:
            payload.update(extras)
        write_json(self.workspace / job_ref, payload)
        return job_ref

    def test_show_status_aggregates_operator_facing_summary(self) -> None:
        self.create_job(
            status="ready",
            name="job-ready.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            retry_budget=1,
        )
        self.create_job(
            status="running",
            name="job-running.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-21T00:00:00Z",
            extras={"started_at": "2026-03-21T01:00:00Z", "claim_owner": "runner-1"},
        )
        self.create_job(
            status="failed",
            name="job-failed.json",
            target_skill="workflow.qa.feat_to_testset",
            created_at="2026-03-22T00:00:00Z",
            retry_count=0,
            retry_budget=2,
            extras={"failure_reason": "dispatch failed"},
        )
        self.create_job(
            status="waiting-human",
            name="job-waiting-human.json",
            target_skill="workflow.qa.feat_to_testset",
            created_at="2026-03-23T00:00:00Z",
            extras={"failure_reason": "needs review"},
        )
        self.create_job(
            status="deadletter",
            name="job-deadletter.json",
            target_skill="skill.qa.test_exec_cli",
            created_at="2026-03-24T00:00:00Z",
            extras={"failure_reason": "budget exhausted"},
        )
        self.create_job(
            status="done",
            name="job-done.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-25T00:00:00Z",
        )

        request = self.build_request("loop.show-status", {})
        request_path = self.request_path("loop-show-status.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-show-status.response.json")

        self.assertEqual(self.run_cli("loop", "show-status", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]

        self.assertEqual(payload["counts"]["ready"], 1)
        self.assertEqual(payload["counts"]["running"], 1)
        self.assertEqual(payload["counts"]["failed"], 1)
        self.assertEqual(payload["counts"]["waiting-human"], 1)
        self.assertEqual(payload["counts"]["deadletter"], 1)
        self.assertEqual(payload["counts"]["done"], 1)
        self.assertEqual(payload["queue_summary"]["statuses"]["ready"]["count"], 1)
        self.assertEqual(payload["queue_summary"]["statuses"]["waiting-human"]["count"], 1)
        self.assertEqual(payload["queue_summary"]["oldest_visible_job_ref"], "artifacts/jobs/ready/job-ready.json")
        self.assertGreater(payload["queue_summary"]["oldest_visible_age_seconds"], 0)

        target_summary = {item["target_skill"]: item for item in payload["target_skill_summary"]}
        self.assertEqual(target_summary["workflow.dev.feat_to_tech"]["total_jobs"], 3)
        self.assertEqual(target_summary["workflow.dev.feat_to_tech"]["counts"]["ready"], 1)
        self.assertEqual(target_summary["workflow.qa.feat_to_testset"]["total_jobs"], 2)
        self.assertEqual(target_summary["workflow.qa.feat_to_testset"]["counts"]["failed"], 1)

        recovery = payload["recoverable_queue_summary"]
        self.assertEqual(recovery["ready_count"], 1)
        self.assertEqual(recovery["retryable_failed_count"], 1)
        self.assertEqual(recovery["waiting_human_count"], 1)
        self.assertEqual(recovery["deadletter_count"], 1)
        self.assertGreater(recovery["oldest_recoverable_age_seconds"], 0)
        self.assertEqual(
            [item["action"] for item in recovery["suggested_actions"]],
            [
                "drain-ready-queue",
                "review-retryable-failures",
                "review-waiting-human",
                "inspect-deadletters",
                "observe-running-jobs",
            ],
        )

    def test_show_backlog_keeps_global_summary_but_filters_jobs(self) -> None:
        self.create_job(
            status="ready",
            name="job-ready.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            retry_budget=1,
        )
        self.create_job(
            status="waiting-human",
            name="job-waiting-human.json",
            target_skill="workflow.qa.feat_to_testset",
            created_at="2026-03-23T00:00:00Z",
        )

        request = self.build_request("loop.show-backlog", {})
        request_path = self.request_path("loop-show-backlog.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-show-backlog.response.json")

        self.assertEqual(self.run_cli("loop", "show-backlog", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]

        self.assertEqual(payload["status_filter"], "ready")
        self.assertEqual(payload["focus_count"], 1)
        self.assertEqual(len(payload["jobs"]), 1)
        self.assertEqual(payload["jobs"][0]["status"], "ready")
        self.assertEqual(payload["counts"]["ready"], 1)
        self.assertEqual(payload["counts"]["waiting-human"], 1)
        self.assertEqual(payload["recoverable_queue_summary"]["focus"], "ready")

    def test_run_execution_returns_post_run_monitor_and_recovery_summary(self) -> None:
        self.create_job(
            status="ready",
            name="job-loop.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            retry_budget=1,
            extras={
                "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
                "handoff_ref": "artifacts/active/handoffs/handoff.json",
                "formal_ref": "formal.feat.demo",
            },
        )

        request = self.build_request("loop.run-execution", {"consume_all": True})
        request_path = self.request_path("loop-run-execution.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-run-execution.response.json")

        with patch(
            "cli.lib.execution_runner.invoke_target",
            return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
        ):
            self.assertEqual(self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)), 0)

        payload = read_json(response_path)
        data = payload["data"]
        snapshot = read_json(self.workspace / data["post_run_snapshot_ref"])

        self.assertEqual(data["processed_count"], 1)
        self.assertEqual(data["post_run_counts"]["done"], 1)
        self.assertEqual(data["post_run_counts"].get("ready", 0), 0)
        self.assertEqual(data["recoverable_queue_summary"]["recoverable_count"], 0)
        self.assertEqual(snapshot["queue_summary"]["statuses"]["running"]["count"], 0)
        self.assertEqual(snapshot["recoverable_queue_summary"]["ready_count"], 0)
        self.assertIn(data["post_run_snapshot_ref"], payload["evidence_refs"])

    def test_recovery_scan_reports_recoverable_jobs_without_mutating_queue(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-expired-running.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            extras={
                "claim_owner": "runner-1",
                "runner_run_id": "run-expired",
                "claimed_at": "2026-03-20T00:01:00Z",
                "started_at": "2026-03-20T00:02:00Z",
                "lease_timeout_seconds": 60,
                "lease_expires_at": "2026-03-20T00:03:00Z",
            },
        )

        request = self.build_request("loop.show-status", {"recovery_action": "scan"})
        request_path = self.request_path("loop-recovery-scan.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-recovery-scan.response.json")

        self.assertEqual(self.run_cli("loop", "show-status", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]

        self.assertEqual(payload["recovery_action"], "scan")
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_count"], 1)
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_job_refs"], [running_ref])
        self.assertEqual(payload["recovery_repair_summary"]["repaired_count"], 0)
        self.assertEqual(payload["queue_summary"]["statuses"]["running"]["count"], 1)
        self.assertEqual(payload["recoverable_queue_summary"]["running_count"], 1)
        self.assertTrue((self.workspace / running_ref).exists())

    def test_recovery_repair_rehomes_expired_jobs_and_updates_summary(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-expired-repair.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            extras={
                "claim_owner": "runner-1",
                "runner_run_id": "run-expired",
                "claimed_at": "2026-03-20T00:01:00Z",
                "started_at": "2026-03-20T00:02:00Z",
                "lease_timeout_seconds": 60,
                "lease_expires_at": "2026-03-20T00:03:00Z",
            },
        )

        request = self.build_request("loop.show-status", {"recovery_action": "repair"})
        request_path = self.request_path("loop-recovery-repair.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-recovery-repair.response.json")

        self.assertEqual(self.run_cli("loop", "show-status", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]

        self.assertEqual(payload["recovery_action"], "repair")
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_count"], 1)
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_job_refs"], [running_ref])
        self.assertEqual(payload["recovery_repair_summary"]["repaired_count"], 1)
        self.assertEqual(payload["recovery_repair_summary"]["recovered_jobs"][0]["job_ref"], "artifacts/jobs/ready/job-expired-repair.json")
        self.assertEqual(payload["queue_summary"]["statuses"]["ready"]["count"], 1)
        self.assertEqual(payload["queue_summary"]["statuses"]["running"]["count"], 0)
        self.assertEqual(payload["recoverable_queue_summary"]["ready_count"], 1)
        ready_ref = "artifacts/jobs/ready/job-expired-repair.json"
        self.assertTrue((self.workspace / ready_ref).exists())
        self.assertFalse((self.workspace / running_ref).exists())

    def test_recover_jobs_command_defaults_to_scan_and_keeps_queue_intact(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-explicit-recover-scan.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            extras={
                "claim_owner": "runner-1",
                "runner_run_id": "run-expired",
                "claimed_at": "2026-03-20T00:01:00Z",
                "started_at": "2026-03-20T00:02:00Z",
                "lease_timeout_seconds": 60,
                "lease_expires_at": "2026-03-20T00:03:00Z",
            },
        )

        request = self.build_request("loop.recover-jobs", {})
        request_path = self.request_path("loop-recover-jobs.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-recover-jobs.response.json")

        self.assertEqual(self.run_cli("loop", "recover-jobs", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]

        self.assertEqual(payload["recovery_action"], "scan")
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_count"], 1)
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_job_refs"], [running_ref])
        self.assertEqual(payload["recovery_repair_summary"]["repaired_count"], 0)
        self.assertEqual(payload["queue_summary"]["statuses"]["running"]["count"], 1)
        self.assertTrue((self.workspace / running_ref).exists())

    def test_recover_jobs_command_repair_rehomes_expired_jobs(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-explicit-recover-repair.json",
            target_skill="workflow.dev.feat_to_tech",
            created_at="2026-03-20T00:00:00Z",
            extras={
                "claim_owner": "runner-1",
                "runner_run_id": "run-expired",
                "claimed_at": "2026-03-20T00:01:00Z",
                "started_at": "2026-03-20T00:02:00Z",
                "lease_timeout_seconds": 60,
                "lease_expires_at": "2026-03-20T00:03:00Z",
            },
        )

        request = self.build_request("loop.recover-jobs", {"recovery_action": "repair"})
        request_path = self.request_path("loop-recover-jobs-repair.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-recover-jobs-repair.response.json")

        self.assertEqual(self.run_cli("loop", "recover-jobs", "--request", str(request_path), "--response-out", str(response_path)), 0)
        payload = read_json(response_path)["data"]

        self.assertEqual(payload["recovery_action"], "repair")
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_count"], 1)
        self.assertEqual(payload["recovery_scan_summary"]["expired_running_job_refs"], [running_ref])
        self.assertEqual(payload["recovery_repair_summary"]["repaired_count"], 1)
        self.assertEqual(payload["recovery_repair_summary"]["recovered_jobs"][0]["job_ref"], "artifacts/jobs/ready/job-explicit-recover-repair.json")
        self.assertEqual(payload["queue_summary"]["statuses"]["ready"]["count"], 1)
        self.assertEqual(payload["queue_summary"]["statuses"]["running"]["count"], 0)
        self.assertEqual(payload["recoverable_queue_summary"]["ready_count"], 1)
        self.assertEqual(payload["recoverable_queue_summary"]["running_count"], 0)
        self.assertEqual(payload["recoverable_queue_summary"]["focus"], "all")
        self.assertEqual(payload["recoverable_queue_summary"]["suggested_actions"][0]["action"], "drain-ready-queue")
        self.assertTrue((self.workspace / "artifacts/jobs/ready/job-explicit-recover-repair.json").exists())
        self.assertFalse((self.workspace / running_ref).exists())
        ready_job = read_json(self.workspace / "artifacts/jobs/ready/job-explicit-recover-repair.json")
        self.assertEqual(ready_job["last_recovered_from_status"], "running")
        self.assertEqual(ready_job["last_recovered_owner"], "runner-1")
        self.assertTrue(ready_job["lease_recovered_at"])
        self.assertEqual(ready_job["claim_owner"], "")
        self.assertEqual(ready_job["runner_run_id"], "")
        self.assertEqual(ready_job["lease_expires_at"], "")
        self.assertEqual(ready_job["heartbeat_at"], "")
        self.assertEqual(ready_job["lease_renewed_at"], "")
        self.assertEqual(ready_job["heartbeat_count"], 0)
        self.assertEqual(ready_job["state_history"][-1]["status"], "ready")
        self.assertIn("recovered expired", ready_job["state_history"][-1]["note"])

    def test_run_execution_rejects_non_integer_max_jobs(self) -> None:
        request = self.build_request("loop.run-execution", {"max_jobs": "oops"})
        request_path = self.request_path("loop-run-execution-invalid-max-jobs.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-run-execution-invalid-max-jobs.response.json")

        self.assertEqual(
            self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)),
            2,
        )

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "INVALID_REQUEST")
        self.assertEqual(payload["message"], "max_jobs must be an integer")

    def test_run_execution_rejects_float_max_jobs(self) -> None:
        request = self.build_request("loop.run-execution", {"max_jobs": 1.5})
        request_path = self.request_path("loop-run-execution-float-max-jobs.json")
        write_json(request_path, request)
        response_path = self.response_path("loop-run-execution-float-max-jobs.response.json")

        self.assertEqual(
            self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)),
            2,
        )

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "INVALID_REQUEST")
        self.assertEqual(payload["message"], "max_jobs must be an integer")
