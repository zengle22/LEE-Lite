---
artifact_type: tech_design_package
status: drafted
schema_version: 1.0.0
source_refs:
  - product.epic-to-feat::RUN-TODO
feat_ref: FEAT-TODO
tech_ref: TECH-FEAT-TODO
arch_required: false
api_required: false
---

# {TITLE}

## Selected FEAT

- feat_ref:
- title:
- epic_freeze_ref:
- src_root_id:

## Need Assessment

- arch_required:
- arch_rationale:
- api_required:
- api_rationale:

## TECH Design

[Summarize the formal technical design: scope, frozen rules, and concrete implementation-ready detail.]

### Implementation Carrier View

[Describe the concrete runtime carriers, module boundaries, and technical placement without repeating ARCH boundary rationale.]

```text
[Module A] --> [Module B]
```

### State Model

[Freeze the key states and allowed transitions.]

### Module Plan

[Name the concrete technical modules/components and their owned responsibilities.]

### Implementation Strategy

[Describe implementation sequencing at the design level, not IMPL task ticket sequencing.]

### Implementation Unit Mapping

[Map each implementation unit to package/module/file and say whether it is new or extended.]

### Interface Contracts

[For each core component, specify input, output, errors, key fields, idempotency, and preconditions.]

### Main Sequence

[Describe the primary success path and at least one revision/fallback path.]

```text
Producer -> Runtime : Example flow
```

### Exception and Compensation

[Describe compensation, partial-success rules, and recovery paths.]

### Integration Points

[Describe who calls these modules, where they attach to existing CLI/loop/skill paths, and compatibility mode behavior.]

### Minimal Code Skeleton

[Provide one happy-path pseudocode block and one failure-path pseudocode block.]

```python
def happy_path() -> None:
    ...
```

```python
def failure_path() -> None:
    ...
```

## Optional ARCH

[If emitted, record only `arch_ref`, a few summary topics, and the pointer to `arch-design.md`. Do not duplicate ARCH body content here. If not required, say why explicitly.]

## Optional API

[If emitted, record only `api_ref`, contract surfaces, command refs, response-envelope summary, and the pointer to `api-contract.md`. Keep full contract detail in the standalone API artifact. If not required, say why explicitly.]

## Cross-Artifact Consistency

- status:
- checks:
- issues:
- minor_open_items:

## Downstream Handoff

- target_workflow:
- tech_ref:
- arch_ref:
- api_ref:

## Traceability

[Map design sections back to authoritative FEAT refs.]
