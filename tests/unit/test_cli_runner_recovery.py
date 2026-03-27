from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cli.lib.errors import CommandError
from cli.lib.execution_runner import run_job
from cli.lib.job_outcome import complete_job, fail_job
from cli.lib.job_queue import claim_job, list_ready_jobs
from cli.ll import main


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iso_z(offset_seconds: int) -> str:
    value = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=offset_seconds)
    return value.isoformat().replace("+00:00", "Z")


class CliRunnerRecoveryTest(unittest.TestCase):
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

    def build_request(self, command: str, payload: dict, *, actor_ref: str = "test-suite") -> dict:
        return {
            "api_version": "v1",
            "command": command,
            "request_id": f"req-{command.replace('.', '-')}",
            "workspace_root": self.workspace.as_posix(),
            "actor_ref": actor_ref,
            "trace": {"run_ref": "RUN-RECOVERY-001"},
            "payload": payload,
        }

    def run_cli(self, *argv: str) -> int:
        return main(list(argv))

    def create_job(self, *, status: str, name: str, claim_owner: str = "", lease_expires_at: str = "", retry_count: int = 0) -> str:
        if status in {"claimed", "running"}:
            relative = f"artifacts/jobs/running/{name}"
        else:
            relative = f"artifacts/jobs/{status}/{name}"
        payload = {
            "job_id": Path(name).stem,
            "job_type": "next_skill",
            "status": status,
            "queue_path": relative,
            "target_skill": "workflow.dev.feat_to_tech",
            "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
            "handoff_ref": "artifacts/active/handoffs/handoff.json",
            "input_refs": ["artifacts/active/gates/decisions/gate-decision.json", "formal.feat.demo"],
            "authoritative_input_ref": "formal.feat.demo",
            "formal_ref": "formal.feat.demo",
            "published_ref": "ssot/feat/FEAT-DEMO.md",
            "source_run_id": "RUN-RECOVERY-001",
            "retry_count": retry_count,
            "retry_budget": 2,
            "created_at": iso_z(-600),
            "feat_ref": "FEAT-DEMO-001",
        }
        if status in {"claimed", "running"}:
            payload.update(
                {
                    "claim_owner": claim_owner or "runner-a",
                    "runner_run_id": "run-prev",
                    "claimed_at": iso_z(-600),
                    "lease_timeout_seconds": 60,
                    "lease_expires_at": lease_expires_at,
                }
            )
        if status == "running":
            payload["started_at"] = iso_z(-500)
        write_json(self.workspace / relative, payload)
        return relative

    def test_list_ready_jobs_recovers_expired_claimed_job(self) -> None:
        job_ref = self.create_job(status="claimed", name="job-expired-claimed.json", lease_expires_at=iso_z(-30))

        ready_jobs = list_ready_jobs(self.workspace)

        self.assertEqual(len(ready_jobs), 1)
        ready_ref = ready_jobs[0]["job_ref"]
        self.assertEqual(ready_ref, "artifacts/jobs/ready/job-expired-claimed.json")
        self.assertFalse((self.workspace / job_ref).exists())
        ready_job = read_json(self.workspace / ready_ref)
        self.assertEqual(ready_job["status"], "ready")
        self.assertEqual(ready_job["claim_owner"], "")
        self.assertEqual(ready_job["last_recovered_from_status"], "claimed")

    def test_job_claim_recovers_expired_running_job(self) -> None:
        running_ref = self.create_job(status="running", name="job-expired-running.json", lease_expires_at=iso_z(-30))
        request = self.build_request(
            "job.claim",
            {"job_ref": running_ref, "runner_id": "runner-b", "runner_run_id": "run-recovered"},
            actor_ref="runner-b",
        )
        request_path = self.request_path("job-claim-recover.json")
        response_path = self.response_path("job-claim-recover.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "claim", "--request", str(request_path), "--response-out", str(response_path)), 0)

        payload = read_json(response_path)
        claimed_job = read_json(self.workspace / payload["data"]["claimed_job_ref"])
        self.assertEqual(claimed_job["status"], "claimed")
        self.assertEqual(claimed_job["claim_owner"], "runner-b")
        self.assertEqual(claimed_job["last_recovered_from_status"], "running")
        self.assertEqual(claimed_job["last_recovered_owner"], "runner-a")

    def test_expired_lease_blocks_run_and_complete_until_recovered(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-expired-run.json", lease_expires_at=iso_z(-30))
        with self.assertRaises(CommandError):
            run_job(
                self.workspace,
                job_ref=claimed_ref,
                trace={},
                request_id="req-run-expired",
                actor_ref="runner-a",
                owner_ref="runner-a",
                payload={},
            )

        running_ref = self.create_job(status="running", name="job-expired-complete.json", lease_expires_at=iso_z(-30))
        with self.assertRaises(CommandError):
            complete_job(
                self.workspace,
                job_ref=running_ref,
                trace={},
                actor_ref="runner-a",
                owner_ref="runner-a",
            )

    def test_complete_rejects_claimed_job_before_run_transition(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-claimed-complete.json", lease_expires_at=iso_z(300))

        with self.assertRaises(CommandError) as ctx:
            complete_job(
                self.workspace,
                job_ref=claimed_ref,
                trace={},
                actor_ref="runner-a",
                owner_ref="runner-a",
            )

        self.assertEqual(ctx.exception.status_code, "PRECONDITION_FAILED")
        self.assertIn("job is not running", ctx.exception.message)

    def test_job_complete_command_rejects_claimed_job_and_preserves_job_file(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-claimed-complete-cli.json", lease_expires_at=iso_z(300))

        request = self.build_request(
            "job.complete",
            {
                "job_ref": claimed_ref,
                "runner_id": "runner-a",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-complete-claimed.json")
        response_path = self.response_path("job-complete-claimed.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "complete", "--request", str(request_path), "--response-out", str(response_path)), 4)

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")
        self.assertIn("job is not running", payload["message"])
        claimed_job = read_json(self.workspace / claimed_ref)
        self.assertEqual(claimed_job["status"], "claimed")
        self.assertFalse((self.workspace / "artifacts/evidence/execution/job-claimed-complete-cli-outcome.json").exists())

    def test_job_fail_command_rejects_retry_budget_exhausted_without_outcome_evidence(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-fail-retry-exhausted-cli.json",
            claim_owner="runner-a",
            lease_expires_at=iso_z(300),
            retry_count=2,
        )
        before_job = read_json(self.workspace / running_ref)

        request = self.build_request(
            "job.fail",
            {
                "job_ref": running_ref,
                "runner_id": "runner-a",
                "failure_mode": "retry-reentry",
                "reason": "temporary downstream failure",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-fail-retry-exhausted-cli.json")
        response_path = self.response_path("job-fail-retry-exhausted-cli.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "fail", "--request", str(request_path), "--response-out", str(response_path)), 4)

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")
        self.assertEqual(payload["message"], "retry budget exhausted")
        after_job = read_json(self.workspace / running_ref)
        self.assertEqual(after_job, before_job)
        self.assertFalse((self.workspace / "artifacts/evidence/execution/job-fail-retry-exhausted-cli-outcome.json").exists())

    def test_job_fail_command_requeues_retry_reentry_successfully_with_evidence(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-fail-requeue-cli.json",
            claim_owner="runner-a",
            lease_expires_at=iso_z(300),
            retry_count=1,
        )
        before_job = read_json(self.workspace / running_ref)

        request = self.build_request(
            "job.fail",
            {
                "job_ref": running_ref,
                "runner_id": "runner-a",
                "failure_mode": "retry-reentry",
                "reason": "temporary downstream failure",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-fail-requeue-cli.json")
        response_path = self.response_path("job-fail-requeue-cli.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "fail", "--request", str(request_path), "--response-out", str(response_path)), 0)

        payload = read_json(response_path)
        data = payload["data"]
        self.assertEqual(payload["status_code"], "OK")
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["requeued_job_ref"], "artifacts/jobs/ready/job-fail-requeue-cli.json")
        self.assertEqual(data["job_ref"], data["requeued_job_ref"])
        self.assertTrue(data["execution_outcome_ref"])

        ready_job = read_json(self.workspace / data["requeued_job_ref"])
        self.assertEqual(ready_job["status"], "ready")
        self.assertEqual(ready_job["queue_path"], data["requeued_job_ref"])
        self.assertEqual(ready_job["retry_count"], before_job["retry_count"] + 1)
        self.assertEqual(ready_job["claim_owner"], "")
        self.assertEqual(ready_job["runner_run_id"], "")
        self.assertTrue((self.workspace / data["execution_outcome_ref"]).exists())
        outcome = read_json(self.workspace / data["execution_outcome_ref"])
        self.assertEqual(outcome["outcome"], "retry-reentry")
        self.assertEqual(outcome["job_ref"], running_ref)

    def test_job_release_hold_promotes_waiting_human_job_to_ready(self) -> None:
        waiting_ref = self.create_job(status="waiting-human", name="job-release-hold.json")
        waiting_job = read_json(self.workspace / waiting_ref)
        waiting_job["progression_mode"] = "hold"
        waiting_job["hold_reason"] = "test_environment_pending"
        waiting_job["required_preconditions"] = ["test_environment_ref"]
        write_json(self.workspace / waiting_ref, waiting_job)

        request = self.build_request(
            "job.release-hold",
            {
                "job_ref": waiting_ref,
                "note": "environment is now ready",
            },
            actor_ref="runner.operator",
        )
        request_path = self.request_path("job-release-hold.json")
        response_path = self.response_path("job-release-hold.response.json")
        write_json(request_path, request)

        self.assertEqual(
            self.run_cli("job", "release-hold", "--request", str(request_path), "--response-out", str(response_path)),
            0,
        )

        payload = read_json(response_path)
        data = payload["data"]
        self.assertEqual(data["released_job_ref"], "artifacts/jobs/ready/job-release-hold.json")
        released_job = read_json(self.workspace / data["released_job_ref"])
        self.assertEqual(released_job["status"], "ready")
        self.assertEqual(released_job["queue_path"], data["released_job_ref"])
        self.assertEqual(released_job["progression_mode"], "auto-continue")
        self.assertEqual(released_job["hold_released_by"], "runner.operator")
        self.assertTrue(released_job["hold_released_at"])
        self.assertEqual(released_job["state_history"][-1]["status"], "ready")
        self.assertIn("environment is now ready", released_job["state_history"][-1]["note"])
        self.assertFalse((self.workspace / waiting_ref).exists())

    def test_job_release_hold_rejects_non_waiting_human_job(self) -> None:
        ready_ref = self.create_job(status="ready", name="job-release-hold-invalid.json")

        request = self.build_request(
            "job.release-hold",
            {
                "job_ref": ready_ref,
            },
            actor_ref="runner.operator",
        )
        request_path = self.request_path("job-release-hold-invalid.json")
        response_path = self.response_path("job-release-hold-invalid.response.json")
        write_json(request_path, request)

        self.assertEqual(
            self.run_cli("job", "release-hold", "--request", str(request_path), "--response-out", str(response_path)),
            4,
        )

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")
        self.assertEqual(payload["message"], f"job is not on hold: {ready_ref}")

    def test_job_run_heartbeat_only_renews_active_claim(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-heartbeat.json", lease_expires_at=iso_z(300))
        before = read_json(self.workspace / claimed_ref)

        request = self.build_request(
            "job.run",
            {
                "job_ref": claimed_ref,
                "lease_action": "heartbeat",
                "lease_timeout_seconds": 600,
                "runner_id": "runner-a",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-heartbeat.json")
        response_path = self.response_path("job-heartbeat.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "run", "--request", str(request_path), "--response-out", str(response_path)), 0)

        payload = read_json(response_path)
        renewed_job = read_json(self.workspace / payload["data"]["renewed_job_ref"])
        before_expiry = datetime.fromisoformat(before["lease_expires_at"].replace("Z", "+00:00"))
        after_expiry = datetime.fromisoformat(renewed_job["lease_expires_at"].replace("Z", "+00:00"))
        self.assertEqual(renewed_job["status"], "claimed")
        self.assertEqual(renewed_job["heartbeat_count"], 1)
        self.assertGreater(after_expiry, before_expiry)
        self.assertEqual(renewed_job["lease_timeout_seconds"], 600)
        self.assertTrue(renewed_job["heartbeat_at"])
        self.assertTrue(renewed_job["lease_renewed_at"])

    def test_heartbeat_rejects_expired_lease(self) -> None:
        running_ref = self.create_job(status="running", name="job-expired-heartbeat.json", lease_expires_at=iso_z(-30))
        request = self.build_request(
            "job.run",
            {
                "job_ref": running_ref,
                "lease_action": "heartbeat",
                "runner_id": "runner-a",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-heartbeat-expired.json")
        response_path = self.response_path("job-heartbeat-expired.response.json")
        write_json(request_path, request)

        self.assertEqual(
            self.run_cli("job", "run", "--request", str(request_path), "--response-out", str(response_path)),
            4,
        )
        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "PRECONDITION_FAILED")

    def test_job_renew_lease_explicit_command_renews_active_claim(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-renew-explicit.json", lease_expires_at=iso_z(300))
        before = read_json(self.workspace / claimed_ref)

        request = self.build_request(
            "job.renew-lease",
            {
                "job_ref": claimed_ref,
                "runner_id": "runner-a",
                "lease_timeout_seconds": 900,
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-renew-explicit.json")
        response_path = self.response_path("job-renew-explicit.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "renew-lease", "--request", str(request_path), "--response-out", str(response_path)), 0)

        payload = read_json(response_path)
        renewed_job = read_json(self.workspace / payload["data"]["renewed_job_ref"])
        before_expiry = datetime.fromisoformat(before["lease_expires_at"].replace("Z", "+00:00"))
        after_expiry = datetime.fromisoformat(renewed_job["lease_expires_at"].replace("Z", "+00:00"))
        self.assertEqual(renewed_job["status"], "claimed")
        self.assertGreater(after_expiry, before_expiry)
        self.assertEqual(renewed_job["lease_timeout_seconds"], 900)

    def test_job_claim_rejects_non_integer_lease_timeout(self) -> None:
        ready_ref = self.create_job(status="ready", name="job-invalid-timeout.json")

        request = self.build_request(
            "job.claim",
            {
                "job_ref": ready_ref,
                "runner_id": "runner-a",
                "lease_timeout_seconds": "oops",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-claim-invalid-timeout.json")
        response_path = self.response_path("job-claim-invalid-timeout.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "claim", "--request", str(request_path), "--response-out", str(response_path)), 2)

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "INVALID_REQUEST")
        self.assertEqual(payload["message"], "lease_timeout_seconds must be an integer")

    def test_job_renew_lease_rejects_boolean_lease_timeout(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-invalid-bool-timeout.json", lease_expires_at=iso_z(300))

        request = self.build_request(
            "job.renew-lease",
            {
                "job_ref": claimed_ref,
                "runner_id": "runner-a",
                "lease_timeout_seconds": True,
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-renew-invalid-bool-timeout.json")
        response_path = self.response_path("job-renew-invalid-bool-timeout.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "renew-lease", "--request", str(request_path), "--response-out", str(response_path)), 2)

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "INVALID_REQUEST")
        self.assertEqual(payload["message"], "lease_timeout_seconds must be an integer")

    def test_job_renew_lease_rejects_zero_timeout_in_job_record(self) -> None:
        claimed_ref = self.create_job(status="claimed", name="job-invalid-zero-timeout.json", lease_expires_at=iso_z(300))
        malformed = read_json(self.workspace / claimed_ref)
        malformed["lease_timeout_seconds"] = 0
        write_json(self.workspace / claimed_ref, malformed)

        request = self.build_request(
            "job.renew-lease",
            {
                "job_ref": claimed_ref,
                "runner_id": "runner-a",
            },
            actor_ref="runner-a",
        )
        request_path = self.request_path("job-renew-invalid-zero-timeout.json")
        response_path = self.response_path("job-renew-invalid-zero-timeout.response.json")
        write_json(request_path, request)

        self.assertEqual(self.run_cli("job", "renew-lease", "--request", str(request_path), "--response-out", str(response_path)), 2)

        payload = read_json(response_path)
        self.assertEqual(payload["status_code"], "INVALID_REQUEST")
        self.assertEqual(payload["message"], "lease_timeout_seconds must be >= 1")

    def test_job_fail_rejects_non_integer_retry_counts_in_job_record(self) -> None:
        cases = [
            ("retry_count", "oops", "retry_count must be an integer"),
            ("retry_budget", True, "retry_budget must be an integer"),
            ("retry_count", -1, "retry_count must be >= 0"),
            ("retry_budget", -1, "retry_budget must be >= 0"),
            ("retry_count", 1.5, "retry_count must be an integer"),
            ("retry_budget", 1.5, "retry_budget must be an integer"),
        ]
        for field_name, invalid_value, expected_message in cases:
            running_ref = self.create_job(
                status="running",
                name=f"job-invalid-{field_name}.json",
                claim_owner="runner-a",
                lease_expires_at=iso_z(300),
                retry_count=1,
            )
            malformed = read_json(self.workspace / running_ref)
            malformed[field_name] = invalid_value
            write_json(self.workspace / running_ref, malformed)
            before_job = read_json(self.workspace / running_ref)

            request = self.build_request(
                "job.fail",
                {
                    "job_ref": running_ref,
                    "runner_id": "runner-a",
                    "failure_mode": "retry-reentry",
                    "reason": "temporary downstream failure",
                },
                actor_ref="runner-a",
            )
            request_path = self.request_path(f"job-fail-invalid-{field_name}.json")
            response_path = self.response_path(f"job-fail-invalid-{field_name}.response.json")
            write_json(request_path, request)

            self.assertEqual(self.run_cli("job", "fail", "--request", str(request_path), "--response-out", str(response_path)), 2)

            payload = read_json(response_path)
            self.assertEqual(payload["status_code"], "INVALID_REQUEST")
            self.assertEqual(payload["message"], expected_message)
            after_job = read_json(self.workspace / running_ref)
            self.assertEqual(after_job, before_job)
            self.assertFalse((self.workspace / f"artifacts/evidence/execution/{Path(running_ref).stem}-outcome.json").exists())

    def test_retry_reentry_requeues_without_owner(self) -> None:
        running_ref = self.create_job(status="running", name="job-retry.json", claim_owner="runner-a", lease_expires_at=iso_z(300))

        outcome = fail_job(
            self.workspace,
            job_ref=running_ref,
            trace={},
            actor_ref="runner-a",
            owner_ref="runner-a",
            reason="temporary downstream failure",
            failure_mode="retry-reentry",
        )

        ready_job = read_json(self.workspace / outcome["requeued_job_ref"])
        self.assertEqual(ready_job["status"], "ready")
        self.assertEqual(ready_job["retry_count"], 1)
        self.assertEqual(ready_job["claim_owner"], "")
        self.assertEqual(ready_job["runner_run_id"], "")
        self.assertEqual(ready_job["lease_expires_at"], "")
        self.assertEqual(ready_job["started_at"], "")
        self.assertEqual(ready_job["heartbeat_at"], "")
        self.assertEqual(ready_job["lease_renewed_at"], "")
        self.assertEqual(ready_job["heartbeat_count"], 0)

    def test_retry_reentry_rejects_when_retry_budget_exhausted(self) -> None:
        running_ref = self.create_job(
            status="running",
            name="job-retry-exhausted.json",
            claim_owner="runner-a",
            lease_expires_at=iso_z(300),
            retry_count=2,
        )
        before_job = read_json(self.workspace / running_ref)

        with self.assertRaises(CommandError) as ctx:
            fail_job(
                self.workspace,
                job_ref=running_ref,
                trace={},
                actor_ref="runner-a",
                owner_ref="runner-a",
                reason="temporary downstream failure",
                failure_mode="retry-reentry",
            )

        self.assertEqual(ctx.exception.status_code, "PRECONDITION_FAILED")
        self.assertEqual(ctx.exception.message, "retry budget exhausted")
        after_job = read_json(self.workspace / running_ref)
        self.assertEqual(after_job, before_job)
        self.assertFalse((self.workspace / "artifacts/evidence/execution/job-retry-exhausted-outcome.json").exists())

    def test_waiting_human_and_deadletter_are_not_recoverable(self) -> None:
        waiting_ref = self.create_job(status="waiting-human", name="job-waiting.json")
        deadletter_ref = self.create_job(status="deadletter", name="job-deadletter.json")

        with self.assertRaises(CommandError):
            claim_job(self.workspace, waiting_ref, runner_id="runner-a", actor_ref="runner-a", runner_run_id="run-1")
        with self.assertRaises(CommandError):
            claim_job(self.workspace, deadletter_ref, runner_id="runner-a", actor_ref="runner-a", runner_run_id="run-1")

        ready_jobs = list_ready_jobs(self.workspace)
        self.assertEqual(ready_jobs, [])
