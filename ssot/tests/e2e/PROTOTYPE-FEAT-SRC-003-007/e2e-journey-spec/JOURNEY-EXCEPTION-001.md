# E2E Journey Spec — JOURNEY-EXCEPTION-001: 非权威数据源

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.non-authoritative |
| coverage_id | e2e.journey.exception.non-authoritative |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-007.Constraints.authoritative-state |

## Test Contract

### Entry Point

`ll loop monitor --source directory-scan` (or equivalent non-authoritative source config)

### Preconditions

- Runner is active
- Authoritative runner state exists
- Alternative non-authoritative source (directory scan) is available

### User Steps

1. Operator configures monitor to use directory scan instead of authoritative state
2. System detects non-authoritative data source
3. System returns NON_AUTHORITATIVE_SOURCE warning
4. Monitor data is displayed but marked as unreliable
5. Operator sees recommendation to use authoritative runner state

### Expected CLI States

- Step 3: CLI outputs "Warning: NON_AUTHORITATIVE_SOURCE - Monitor is reading from directory scan instead of authoritative runner state. Results may be unreliable."
- Step 4: All displayed data has [UNRELIABLE] marker
- Step 5: Warning includes "Use authoritative state: ll loop monitor --source authoritative"

### Expected Network Events

- Directory scan: Read directory listing instead of authoritative state files
- Warning log: Record non-authoritative source usage
- No authoritative state reads

### Expected Persistence

- Monitor output log records source type as "non-authoritative"
- Warning log entry persists
- No runner state files modified

### Anti-False-Pass Checks

- warning_displayed (NON_AUTHORITATIVE_SOURCE message shown)
- data_marked_unreliable (UI markers present)
- authoritative_source_not_used
- recommendation_included (guidance to use authoritative source)
- no_state_files_modified

### Evidence Required

- cli_output_log (including warning)
- monitor_source_config_snapshot
- data_reliability_markers
- warning_log_entry
