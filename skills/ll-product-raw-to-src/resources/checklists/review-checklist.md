# Review Checklist

Phase-1 ADR-039 coverage dimensions:

- `ssot_alignment`
  - Does the skill reject already-governed SSOT input?
  - Are duplicate-title and multi-topic guards enforced before recommending downstream flow?
- `object_completeness`
  - Are ADR bridge outputs explicitly marked as `governance_bridge_src`?
  - Are the required package objects and evidence artifacts emitted?
- `contract_completeness`
  - Does the package include the expected handoff and job proposals when the action is not `blocked`?
  - Does the skill stop at proposals and leave final gate materialization outside the skill?
- `state_transition_closure`
  - Does the runner preserve the staged order from validation through freeze-readiness assessment?
- `failure_path`
  - If a dimension or guard is not actually reviewed, emit `not_checked` instead of `checked`.
  - If review completeness fails, the package must not proceed to freeze-ready handoff.
- `testability`
  - Are acceptance report, defect list, retry-budget report, execution evidence, and supervision evidence all emitted?

Phase-1 output rules:

- Every review must emit all six coverage keys.
- Use only `checked`, `partial`, or `not_checked`.
- If a required dimension is `not_checked`, the package is not freeze-ready.
- `blocker_count` must stay consistent with structured findings severity.
