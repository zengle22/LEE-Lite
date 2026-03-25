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

[Summarize the definition-layer design: scope, frozen rules, and non-functional requirements.]

## TECH-IMPL Design

### ASCII Architecture View

[Describe the concrete modules, responsibilities, and runtime placement.]

```text
[Module A] --> [Module B]
```

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

[If not required, say why explicitly.]

## Optional API

[If required, document concrete CLI command surfaces, request/response fields, errors, idempotency, and compatibility rules. If not required, say why explicitly.]

## Cross-Artifact Consistency

- status:
- checks:
- issues:

## Downstream Handoff

- target_workflow:
- tech_ref:
- arch_ref:
- api_ref:

## Traceability

[Map design sections back to authoritative FEAT refs.]
