# Phase 15: 集成与追溯 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 15-integration-traceability
**Areas discussed:** Integration Point, Validation Failure, FC Traceability, Backward Compat

---

## Integration Point

| Option | Description | Selected |
|--------|-------------|----------|
| fs.py write_json wrapper (Recommended) | Wrap write_json() in fs.py with validation. Single point catches all writes. Path filtering for SSOT directories. | ✓ |
| Schema validators (testset_schema.py, etc.) | Add enum_guard calls inside each schema validate() function. Precise but requires updating each file. | |
| Command-level (each command.py) | Call enum_guard in each command before write. Most explicit but highest maintenance burden. | |

**User's choice:** fs.py write_json wrapper (Recommended)
**Notes:** User chose the single-point integration approach — wrap write_json() in fs.py with enum_guard validation. This avoids updating multiple files and provides centralized validation control.

## Validation Failure

| Option | Description | Selected |
|--------|-------------|----------|
| Block entirely — fail fast (Recommended) | Raise error immediately, reject the write. Consistent with governance-first approach. | ✓ |
| Add diagnostics, allow write | Return violations in diagnostics but complete the write. Risk of invalid SSOT files. | |
| Strict mode: block, Permissive mode: warn | Add --strict flag. Block in strict (default), warn in permissive. | |

**User's choice:** Block entirely — fail fast (Recommended)
**Notes:** User chose the governance-first approach — block SSOT writes entirely when enum_guard validation fails. No bypass mechanism needed.

## FC Traceability

| Option | Description | Selected |
|--------|-------------|----------|
| YAML/JSON frontmatter (Recommended) | Add fc_refs: [FC-001, FC-002, ...] field in file header. Machine-readable, easy to audit. | ✓ |
| Comment headers (# FC-001, # FC-002, ...) | Add comment at top of each file listing applicable FCs. Human-readable. | |
| Both frontmatter + comments | Both machine-readable fc_refs field AND human-readable comments. Most complete but verbose. | |

**User's choice:** YAML/JSON frontmatter (Recommended)
**Notes:** User chose machine-readable FC traceability via `fc_refs` field in file header. Enables automated auditing.

## Backward Compat

| Option | Description | Selected |
|--------|-------------|----------|
| Path-based filtering (Recommended) | In write_json wrapper, check if path matches SSOT patterns (ssot/*.yaml, etc.). FRZ paths bypass enum_guard. | ✓ |
| Content-based detection | Inspect payload content to determine if enum_guard applies. Flexible but complex. | |
| Bypass flag | Add --no-validate flag to write_json for cases that need bypass. Explicit but requires discipline. | |

**User's choice:** Path-based filtering (Recommended)
**Notes:** User chose path-based filtering to ensure FRZ/MSC paths bypass enum_guard validation entirely.

---

## Claude's Discretion

- None — all decisions were user-selected

## Deferred Ideas

- None — discussion stayed within phase scope
