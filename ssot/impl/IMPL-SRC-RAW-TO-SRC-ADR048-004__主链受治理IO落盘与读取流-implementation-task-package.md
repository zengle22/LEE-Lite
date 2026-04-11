---
id: IMPL-SRC-RAW-TO-SRC-ADR048-004
ssot_type: IMPL
title: "主链受治理IO落盘与读取流 Implementation Task Package"
status: execution_ready
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-004
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-001
arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-001
api_ref: API-SRC-RAW-TO-SRC-ADR048-001
main_sequence:
  - step: 1
    task: TASK-001
    title: Define file-path governance rules and path resolution contracts
    depends_on: none
    done_when: All path patterns and resolution rules are explicit and tested
  - step: 2
    task: TASK-002
    title: Implement path validation and normalization guards
    depends_on: TASK-001
    done_when: All file operations pass through validated path resolution
  - step: 3
    task: TASK-003
    title: Implement read/write carriers with permission and mode enforcement
    depends_on: TASK-001, TASK-002
    done_when: File IO respects frozen permission and mode constraints
  - step: 4
    task: TASK-004
    title: Wire evidence collection and audit trail for IO operations
    depends_on: TASK-002, TASK-003
    done_when: All IO operations produce audit trail entries
  - step: 5
    task: TASK-005
    title: Collect acceptance evidence and close delivery handoff
    depends_on: TASK-004
    done_when: Every acceptance check backed by explicit evidence artifacts
implementation_units:
  - path: cli/lib/fs.py
    type: backend
    action: extend
    purpose: File system operations with path validation and governance
  - path: cli/lib/mainline_runtime.py
    type: backend
    action: extend
    purpose: Mainline IO carriers with path governance and audit trail
  - path: cli/lib/protocol.py
    type: backend
    action: extend
    purpose: IO operation protocol definitions and audit record structure
  - path: cli/commands/gate/command.py
    type: backend
    action: extend
    purpose: Gate IO governance CLI entry points
  - path: cli/lib/audit.py
    type: backend
    action: new
    purpose: Audit trail recording for all governed file operations
non_goals:
  - Does not redefine gate decision semantics
  - Does not handle formal publication (separate FEAT-003)
  - Does not define FEAT/TECH derivation rules
  - Does not manage UI surface or user testing
implementation_readiness: true
---

# 主链受治理IO落盘与读取流 Implementation Task Package

## Main Sequence Snapshot

- Step 1: TASK-001 Define file-path governance rules | depends_on: none | done_when: All path patterns and resolution rules are explicit and tested
- Step 2: TASK-002 Implement path validation guards | depends_on: TASK-001 | done_when: All file operations pass through validated path resolution
- Step 3: TASK-003 Implement IO carriers with permission enforcement | depends_on: TASK-001, TASK-002 | done_when: File IO respects frozen permission and mode constraints
- Step 4: TASK-004 Wire evidence collection and audit trail | depends_on: TASK-002, TASK-003 | done_when: All IO operations produce audit trail entries
- Step 5: TASK-005 Collect acceptance evidence | depends_on: TASK-004 | done_when: Every acceptance check backed by explicit evidence artifacts

## Implementation Unit Mapping Snapshot

- `cli/lib/fs.py` [backend | extend | owned]: File system operations with path validation and governance
- `cli/lib/mainline_runtime.py` [backend | extend | owned]: Mainline IO carriers with path governance and audit trail
- `cli/lib/protocol.py` [backend | extend | owned]: IO operation protocol definitions and audit record structure
- `cli/commands/gate/command.py` [backend | extend | owned]: Gate IO governance CLI entry points
- `cli/lib/audit.py` [backend | new | owned]: Audit trail recording for all governed file operations

## State Model Snapshot

- State transitions: `io_pending` -> `path_validation_done` -> `io_execution_completed` -> `audit_recorded_done`
- Recovery paths: `path_validation_failed` -> reject with clear error, no IO attempted
- Recovery paths: `io_execution_failed` -> log failure, rollback partial writes -> manual resolution
- Recovery paths: `audit_record_failed` -> fail-closed, block IO completion until audit succeeds
- Completion signals: path_validation_done, io_execution_completed, audit_recorded_done
- Failure signals: path_validation_failed, io_execution_failed, audit_record_failed
- Fail-closed: if audit fails, do not complete IO; require manual resolution

## Integration Points Snapshot

- All file IO flows through cli/lib/fs.py for path validation
- Mainline runtime delegates to fs.py for all read/write operations
- Audit trail is recorded for every governed IO operation
- Backward compat: legacy IO paths are logged as warnings and must migrate

## Completion Signals

- **path_validation_done**: all file paths validated against governance rules, no unauthorized access
- **io_execution_completed**: read/write operation completed successfully with correct permissions and audit trail
- **audit_recorded_done**: audit trail entry written for every governed IO operation

## Terminal State

- **audit_recorded**: all IO operations complete, audit trail verified, downstream consumers can safely read
- **Success outputs**: audit trail entries written, IO operations complete without violations
- **User-visible outcome**: governed file operations succeed with full audit trail; failures blocked with clear error messages

## Selected Upstream

- feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-004
- tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-001
- arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-001
- api_ref: API-SRC-RAW-TO-SRC-ADR048-001
