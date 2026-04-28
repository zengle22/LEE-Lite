---
phase: 20
plan: 01
status: complete
completed: 2026-04-27
---

# Phase 20-01: Semantic Drift Scanner — Implementation Summary

## What Was Delivered

### 1. Core Module: `cli/lib/semantic_drift_scanner.py`
- **ViolationType Enum**: Two detection types:
  - `OVERLAY_ELEVATION`: Overlay terms (governance/gate/handoff/formal/registry/validation/audit/bypass/settlement) as primary objects
  - `API_DUPLICATE`: Same API endpoint declared in multiple files
- **Violation Dataclass**: Frozen immutable DTO with type, severity, file_path, anchor_id, detail, evidence
- **ScanResult Dataclass**: Frozen immutable result container with counts and violation list
- **Detection Functions**:
  - `scan_overlay_elevation()`: Scans epic/ and feat/ directories for overlay terms in primary topics
  - `scan_api_duplicates()`: Scans api/ directory for duplicate endpoints in .md/.yaml/.yml files
  - `scan_ssot()`: Orchestrator combining both detectors
- **CLI Entry Point**: `main()` with `--ssot-dir` and `--output` (human/json) options

### 2. Test Suite: `cli/lib/test_semantic_drift_scanner.py`
- 14 unit tests covering:
  - Overlay detection: positive (governance/gate/handoff), negative, multiple files
  - API duplicate detection: positive, negative, multiple endpoints, YAML files
  - scan_ssot combined results (with and without violations)
  - CLI output formats (human and JSON), --help
- 97% test coverage on the test module itself
- 84% test coverage on the core module

### 3. Verification Results
- ✅ All 14 tests pass
- ✅ CLI works with real SSOT directory
- ✅ Found 4 existing violations in current SSOT:
  1. `EPIC-SRC-003-001__gate-execution-runner.md` - contains 'gate' in primary topic
  2. `FEAT-009-A__independent-verification-and-audit.md` - contains 'bypass' in primary topic
  3. `FEAT-SRC-005-002__主链-gate-审核与裁决流.md` - contains 'gate' in primary topic
  4. `FEAT-SRC-005-003__formal-发布与下游准入流.md` - contains 'formal' in primary topic
- ✅ JSON output format valid and machine-readable
- ✅ Human output format clear and actionable

## Implementation Decisions Followed
- ✅ **Pure rule-based, no LLM**: Stable and predictable
- ✅ **Frozen dataclasses**: Immutable DTOs for safety
- ✅ **CommandError/ensure pattern**: Consistent error handling
- ✅ **CLI pattern matches enum_guard/governance_validator**: Consistent user experience
- ✅ **Path safety and file size limits (1MB cap)**: Prevents DoS
- ✅ **Non-blocking CI approach**: Scanner reports, doesn't fail builds (exit code = blocker_count, configurable)

## Next Steps for Phase 20
The detection capability is complete. Next phases (21+) will address the detected violations according to the roadmap.

## Files Created/Modified
- Created: `cli/lib/semantic_drift_scanner.py` (158 SLOC)
- Created: `cli/lib/test_semantic_drift_scanner.py` (171 SLOC)
- Created: `.planning/phases/20-p0-defect-fix/20-01-SUMMARY.md` (this file)
