# Example Output

```json
{
  "api_version": "v1",
  "command": "skill.test-exec-cli",
  "request_id": "req-test-exec-cli-001",
  "result_status": "success",
  "status_code": "OK",
  "exit_code": 0,
  "message": "governed skill candidate emitted",
  "data": {
    "skill_ref": "skill.qa.test_exec_cli",
    "runner_skill_ref": "skill.runner.test_cli",
    "candidate_artifact_ref": "candidate.skill-qa-test-exec-cli-req-test-exec-cli-001",
    "candidate_managed_artifact_ref": "artifacts/active/qa/candidates/candidate.skill-qa-test-exec-cli-req-test-exec-cli-001.json",
    "handoff_ref": "artifacts/active/mainline/handoffs/handoff-001.json",
    "run_status": "completed",
    "test_case_pack_ref": "artifacts/active/qa/executions/run-001/test-case-pack.yaml",
    "script_pack_ref": "artifacts/active/qa/executions/run-001/script-pack.json",
    "evidence_bundle_ref": "artifacts/active/qa/executions/run-001/evidence/index.json",
    "tse_ref": "artifacts/active/qa/executions/run-001/tse.json"
  }
}
```
