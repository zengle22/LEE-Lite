# SECURITY.md — LEE-Lite-skill-first

**Phase:** 02 — patch-skill
**Date:** 2026-04-16
**Auditor:** gsd-security-auditor
**ASVS Level:** 1

## Threat Verification Summary

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-02-01 | Tampering (AI-generated YAML) | mitigate | CLOSED | supervisor.md:17-19 (`python -m cli.lib.patch_schema`); patch_capture_runtime.py:185 (`validate_file`) |
| T-02-02 | Spoofing (Input document path) | mitigate | CLOSED | patch_capture_runtime.py:171 (`doc_path.resolve().relative_to(workspace_root.resolve())`) |
| T-02-03 | Information Disclosure (Registry reads) | accept | CLOSED | Accepted risk — registry contains only id, status, change_class, created_at, title, patch_file; no secrets |
| T-02-04 | Repudiation (Audit trail) | mitigate | CLOSED | patch_capture_runtime.py:216 (`patch["source"]["session"] = request_id`) |
| T-02-05 | Tampering (Executor YAML) | mitigate | CLOSED | Duplicate of T-02-01; supervisor.md:16-22 Layer 1 mechanical validation |
| T-02-06 | Elevation of Privilege (Auto-pass) | mitigate | CLOSED | supervisor.md:52-57 (auto-pass ALL-conditions); patch_capture_runtime.py:208,219-231 (escalation checks) |
| T-02-07 | Repudiation (Audit trail) | mitigate | CLOSED | command.py:122 (`evidence_refs = _collect_refs(result)`); patch_capture_runtime.py:216 (`session = request_id`) |
| T-02-08 | Injection (CLI payload) | mitigate | CLOSED | patch_capture_runtime.py:138-140 (`ensure()` for feat_id, input_type, input_value); command.py:104-106 (payload field validation) |
| T-02-09 | Spoofing (Document path) | mitigate | CLOSED | Duplicate of T-02-02; patch_capture_runtime.py:171 |
| T-02-10 | Tampering (Registry R-M-W) | accept | CLOSED | Accepted risk — single-threaded CLI MVP; fcntl read locking present (lines 31-43), no write locking (expected for MVP) |
| T-02-11 | Tampering (Patch YAML pre-validation) | mitigate | CLOSED | patch_capture_runtime.py:185 (`validate_file`) called before line 258 (`register_patch_in_registry`) |
| T-02-12 | Testing Gap | mitigate | CLOSED | test_patch_capture_runtime.py has 25 tests (3 slugify + 3 get_next_patch_id + 4 detect_conflicts + 2 register + 13 run_skill) |

**Result:** 12/12 threats CLOSED. 0 OPEN.

## Accepted Risks

| Threat ID | Description | Rationale |
|-----------|-------------|-----------|
| T-02-03 | Registry file reads expose no secrets | Registry contains only patch metadata (id, status, change_class, timestamps, title, file path). No authentication tokens, API keys, or credentials stored or transmitted. |
| T-02-10 | Registry read-modify-write race condition | Phase 02 MVP is a single-threaded CLI. Concurrent access not expected. fcntl shared locks used for reads on Unix. Write locking to be added when multi-user/multi-threaded access is introduced. |

## Unregistered Flags

None — no `## Threat Flags` section was provided from SUMMARY.md for this phase.

## Security Controls Implemented

### Input Validation
- `feat_id`: regex validation (`^[a-zA-Z0-9][\w.\-]*$`), max 128 chars, path traversal rejection
- `input_type`: enum validation (prompt | document)
- `input_value`: required, max 50000 chars
- Document paths: `Path.resolve().relative_to(workspace_root)` containment check

### Schema Validation
- All generated Patch YAML validated via `validate_file()` against `PatchExperience` dataclass before registration
- Enum validation for status, change_class, severity, actor, backwrite_status

### Audit Trail
- `request_id` propagated to `source.session` on every patch
- CLI handler returns `evidence_refs` in response JSON

### Auto-pass Safeguards
- Requires ALL conditions: schema valid + no conflicts + non-semantic + high confidence
- Escalation triggers: first patch for FEAT, semantic classification, disputed test_impact, conflicts, low confidence

## Files Verified

- `E:\ai\LEE-Lite-skill-first\skills\ll-patch-capture\agents\supervisor.md`
- `E:\ai\LEE-Lite-skill-first\skills\ll-patch-capture\agents\executor.md`
- `E:\ai\LEE-Lite-skill-first\skills\ll-patch-capture\scripts\patch_capture_runtime.py`
- `E:\ai\LEE-Lite-skill-first\skills\ll-patch-capture\scripts\test_patch_capture_runtime.py`
- `E:\ai\LEE-Lite-skill-first\cli\commands\skill\command.py`
- `E:\ai\LEE-Lite-skill-first\cli\lib\patch_schema.py`
