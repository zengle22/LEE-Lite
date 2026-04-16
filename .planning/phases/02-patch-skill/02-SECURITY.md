---
phase: "02"
slug: patch-skill
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-16
updated: 2026-04-16T17:30:00Z
---

# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| User prompt → Executor Agent | Unstructured text input, must be classified and validated | Change description (no secrets) |
| AI-generated Patch YAML → Schema Validator | AI may produce invalid enum values or missing fields | PatchExperience YAML |
| Document path → File System | Path traversal risk if user-provided paths not sanitized | File path string |
| CLI payload → Python runtime | Untrusted input values (feat_id, input_value) must be validated | JSON payload fields |
| Registry read-modify-write → JSON file | Concurrent writes could corrupt registry (race condition) | patch_registry.json |
| Executor LLM output → File System | Executor generates YAML — must be validated before disk write | Patch YAML content |
| Supervisor judgment → Registration decision | Supervisor decides auto-pass vs escalate | Validation results |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-02-01 | Tampering | Executor Agent (AI-generated YAML) | mitigate | Supervisor agent calls `cli/lib/patch_schema.py` `validate_file()` before accepting generated Patch YAML; reject if schema validation fails | closed |
| T-02-02 | Spoofing | Input document path | mitigate | Runtime validates document path exists within workspace root using `Path.resolve().relative_to(workspace_root)` before processing | closed |
| T-02-03 | Information Disclosure | Patch registry reads | accept | Registry contains no secrets — only patch IDs, statuses, timestamps; low-value target | closed |
| T-02-04 | Repudiation | Patch registration without trace | mitigate | CLI protocol requires `request_id` in every request; runtime logs `request_id` with generated patch ID for audit trail | closed |
| T-02-05 | Tampering | Executor-generated YAML content | mitigate | Supervisor Layer 1 calls Python `validate_file()` — mechanical check, not LLM judgment; invalid YAML cannot pass | closed |
| T-02-06 | Elevation of Privilege | Supervisor auto-pass decision | mitigate | Auto-pass requires ALL conditions (schema valid + no conflict + confidence high + non-semantic); any failure triggers escalation | closed |
| T-02-07 | Repudiation | Patch registered without audit trail | mitigate | CLI protocol `request_id` logged; Supervisor validation result recorded in response JSON with evidence_refs | closed |
| T-02-08 | Injection | CLI payload values (feat_id, input_value) | mitigate | Runtime uses `ensure()` from cli.lib.errors to validate required fields before any processing; input_value stripped and checked non-empty; feat_id regex validated | closed |
| T-02-09 | Spoofing | Document path input | mitigate | `Path.resolve().relative_to(workspace_root.resolve())` check — raises INVALID_REQUEST if path escapes workspace | closed |
| T-02-10 | Tampering | Registry read-modify-write | accept | MVP is single-threaded via Claude Code sessions; race condition unlikely. For production, add file locking (portalocker) or atomic rename pattern | closed |
| T-02-11 | Tampering | Generated Patch YAML before validation | mitigate | Runtime calls `validate_file()` BEFORE updating registry — invalid patches never get registered | closed |
| T-02-12 | Testing Gap | Test coverage insufficient | accept | 25 tests cover core functions; additional edge cases can be added in future phases | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-02-01 | T-02-03 | Registry contains no secrets — only patch IDs, statuses, timestamps. Low-value target for attackers. | Phase 02 security audit | 2026-04-16 |
| AR-02-02 | T-02-10 | MVP is single-threaded via Claude Code sessions. Concurrent writes unlikely. Production should add file locking (portalocker) or atomic rename pattern. | Phase 02 security audit | 2026-04-16 |
| AR-02-03 | T-02-12 | 25 tests cover all 5 public functions (slugify, get_next_patch_id, detect_conflicts, register_patch_in_registry, run_skill). Adequate for Phase 02 scope. | Phase 02 security audit | 2026-04-16 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-16 | 12 | 12 | 0 | gsd-security-auditor (sonnet) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-16
