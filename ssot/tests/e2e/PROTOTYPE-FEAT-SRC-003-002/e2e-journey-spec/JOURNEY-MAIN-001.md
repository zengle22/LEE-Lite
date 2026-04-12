# E2E Journey Spec — JOURNEY-MAIN-001: 启动 Runner

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main-start.happy |
| coverage_id | e2e.journey.main-start.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-002.AcceptanceChecks.named-skill-entry |

## Test Contract

### Entry Point

`ll loop run-execution --start`

### Preconditions

- `skills/l3/ll-execution-loop-job-runner/` bundle exists
- `artifacts/jobs/ready` directory exists and is accessible
- No existing active runner session

### User Steps

1. Operator executes `ll loop run-execution --start`
2. System verifies skill bundle exists at canonical path
3. System binds to ready queue (artifacts/jobs/ready)
4. System starts runner and preserves run context
5. Operator sees "Runner started" confirmation
6. Operator verifies skill authority is set to canonical bundle path

### Expected CLI States

- Step 2: CLI outputs "Verifying skill bundle: skills/l3/ll-execution-loop-job-runner/"
- Step 3: CLI outputs "Bound to ready queue: artifacts/jobs/ready"
- Step 4: CLI outputs "Preserving run context and lineage"
- Step 5: CLI outputs "Runner started. Session: {session-id}"
- Step 6: `ll loop monitor` shows runner active with correct bundle path

### Expected Network Events

- Skill bundle read: Verify canonical bundle path exists
- Ready queue scan: Initial scan of artifacts/jobs/ready
- Session creation: Write session state file
- Run context persistence: Write run context and lineage

### Expected Persistence

- Session file created with session-id
- Run context file with lineage refs
- No stale session files from prior runs

### Anti-False-Pass Checks

- runner_process_running (verify actual process, not just stdout)
- session_file_exists
- skill_bundle_verified (canonical path confirmed)
- no_console_error
- ready_queue_bound (not default or fallback)

### Evidence Required

- cli_output_log
- runner_process_status
- session_file_snapshot
- skill_bundle_verification
- run_context_snapshot
