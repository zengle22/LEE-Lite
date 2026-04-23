# Phase 15: 集成与追溯 - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate enum_guard into SSOT write paths, add Frozen Contract traceability to all outputs.

Requirements: FC-01 ~ FC-03, INT-01 ~ INT-03

Success Criteria:
1. SSOT write path (cli/lib/protocol.py) automatically invokes enum_guard validation
2. Existing FRZ/MSC validation flow remains unaffected
3. All output files explicitly reference FC-001 ~ FC-007

</domain>

<decisions>
## Implementation Decisions

### Integration Point
- **D-01:** Wrap `write_json()` in `cli/lib/fs.py` with enum_guard validation
  - Single interception point for all SSOT file writes
  - Path filtering to identify SSOT directories vs other paths

### Validation Behavior
- **D-02:** Block entirely on enum_guard violation — fail fast, reject the write
  - Raise error immediately when validation fails
  - Provides clear error message with field name, value, and allowed values

### FC Traceability Format
- **D-03:** Add `fc_refs: [...]` field in file header for machine-readable FC traceability
  - Each SSOT file lists applicable FCs (FC-001 ~ FC-007)
  - Enables automated audit tooling

### Backward Compatibility
- **D-04:** Path-based filtering — enum_guard only validates writes to SSOT directories
  - SSOT paths: `ssot/*.yaml`, `ssot/**/*.yaml`, `ssot/**/*.json`
  - FRZ paths (`frz/*.yaml`, etc.) bypass enum_guard validation entirely
  - Existing FRZ/MSC validation flow remains unaffected

### Scope: What This Phase Does NOT Cover
- Implementation of new validation logic (enum_guard already exists in Phase 13)
- Changes to schema validators (testset_schema.py, etc.) — they remain unchanged
- FRZ/MSC specific validation — these paths explicitly bypass enum_guard

</decisions>

<canonical_refs>
## Canonical References

### Frozen Contracts (FC-001 ~ FC-007)
- `ssot/epic/EPIC-009__adr-052-test-governance-dual-axis.md` — FC definitions
- `ssot/src/SRC-009__adr-052-ssot-semantic-governance-upgrade.md` — Frozen Contract specifications

### Phase Dependencies
- `cli/lib/enum_guard.py` — 6 governance enums, validate_enums() function (Phase 13)
- `cli/lib/governance_validator.py` — 11 governance objects (Phase 14)
- `cli/lib/fs.py` — write_json() function (integration target)
- `.planning/phases/12-schema-layer/12-CONTEXT.md` — schema patterns
- `.planning/phases/13-enum-guard/13-CONTEXT.md` — enum_guard design
- `.planning/phases/14-governance-validator/14-CONTEXT.md` — governance_validator design

### Existing Patterns
- `cli/lib/task_pack_schema.py` — dataclass(frozen=True) + validate() pattern
- `cli/lib/qa_schemas.py` — _require() / _enum_check() helpers
- `cli/lib/frz_schema.py` — Frozen dataclass + MSC validation pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Integration Target
- `cli/lib/fs.py` line 30-32: `write_json()` is the central write function
- All SSOT file writes go through write_json()
- This is the ideal integration point per D-01

### Enum Guard API
- `enum_guard.validate_enums(data: dict, label: str) -> list[EnumGuardViolation]`
- Returns empty list if valid, list of violations if invalid
- EnumGuardViolation: field, value, allowed, label fields

### Path Filtering Strategy
SSOT directories to validate:
- `ssot/**/*.yaml`
- `ssot/**/*.json`

FRZ directories to bypass:
- `frz/**/*.yaml`
- Any path containing "frz/"

</code_context>

<specifics>
## Specific Ideas

- The write_json wrapper should call enum_guard.validate_enums() on the payload
- Path checking: use `path.match()` or regex for SSOT path patterns
- FC references should be added to the file being written, not checked
- Error message should include which FC was violated if applicable

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-integration-traceability*
*Context gathered: 2026-04-23*
