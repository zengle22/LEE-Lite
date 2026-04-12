# E2E Journey Spec — JOURNEY-MAIN-001: Auto-Continue Job 生成

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-001.Scope.ready-job-generation |

## Test Contract

### Entry Point

`POST /api/v1/jobs/generate` (triggered by gate approve event)

### Preconditions

- Gate decision exists with status = "approved" and progression_mode = "auto-continue"
- `artifacts/jobs/ready` directory exists and is writable
- Candidate package refs are valid and accessible

### User Steps

1. Operator confirms gate approve decision
2. System detects progression_mode = auto-continue
3. System generates ready job with authoritative refs
4. System writes job file to `artifacts/jobs/ready/job-ready-{id}.json`
5. Operator verifies job file exists and content is complete
6. Operator verifies job contains next_skill_target and all authoritative refs

### Expected CLI States

- Step 2: CLI outputs "Detecting progression mode: auto-continue"
- Step 3: CLI outputs "Generating ready job: job-ready-{id}"
- Step 4: CLI outputs "Job written to artifacts/jobs/ready/job-ready-{id}.json"
- Step 5-6: Operator runs `cat artifacts/jobs/ready/job-ready-{id}.json` and sees complete JSON

### Expected Network Events

- Gate decision read: GET gate decision record
- Job write: File write to artifacts/jobs/ready/
- Gate decision update: Mark job_generation_status = "emitted"

### Expected Persistence

- Job file persists at artifacts/jobs/ready/job-ready-{id}.json
- Gate decision record updated with job generation reference
- No file in artifacts/jobs/hold directory

### Anti-False-Pass Checks

- file_exists_in_ready_queue (not just stdout confirmation)
- job_content_complete (all fields present and valid)
- no_file_in_hold_queue (verify no queue leak)
- gate_decision_updated (job_generation_status changed)
- no_console_error

### Evidence Required

- cli_output_log
- job_file_snapshot
- gate_decision_diff
- directory_listing_before_and_after
