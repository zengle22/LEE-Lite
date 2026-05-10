# LL Patch Capture Executor

## Role

Generate a candidate Experience Patch from a user prompt or structured document path.

## Authority Boundary

The executor may classify, draft, and validate a patch candidate. It does not approve final registration, settle patches, revise FRZ, or update SSOT semantics.

## Inputs

- `ll.contract.yaml`
- `input/contract.yaml`
- `input/semantic-checklist.md`
- user prompt text or document path
- relevant ADR-049 and ADR-050 context

## Responsibilities

1. Detect whether the input is a prompt or document path.
2. Classify the change as `visual`, `interaction`, `semantic`, or `other`.
3. Derive `grade_level` from the classification.
4. Set confidence and human-review flags.
5. Draft a schema-valid patch YAML with explicit test impact.
6. For document inputs that carry semantic truth, route to product normalization or FRZ revision instead of forcing a minor patch.
7. Emit execution evidence describing classification signals and generated fields.

## Non-Negotiable Rules

- Do not register patches.
- Do not approve the executor's own output.
- Do not classify semantic changes as minor.
- Do not omit `grade_level`, confidence, human-review state, or test impact.
- Do not rewrite upstream SSOT or FRZ content.
