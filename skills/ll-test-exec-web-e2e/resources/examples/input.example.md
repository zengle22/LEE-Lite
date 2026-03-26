# Example Input

```json
{
  "api_version": "v1",
  "command": "skill.test-exec-web-e2e",
  "request_id": "req-test-exec-web-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "codex",
  "trace": {
    "run_ref": "RUN-ADR007-WEB-001"
  },
  "payload": {
    "test_set_ref": "artifacts/feat-to-testset/adr007-qa-test-execution-20260325-rerun1--feat-src-adr007-qa-test-execution-20260325-rerun1-001/test-set.yaml",
    "test_environment_ref": "ssot/test-env/web-staging.yaml",
    "proposal_ref": "proposal-web-001",
    "frontend_code_ref": "E:/frontend/app",
    "ui_runtime_ref": "http://127.0.0.1:4173",
    "ui_source_spec": {
      "codebase_ref": "E:/frontend/app",
      "runtime_ref": "http://127.0.0.1:4173"
    }
  }
}
```
