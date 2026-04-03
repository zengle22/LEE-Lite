# Input Semantic Checklist

Review the selected TECH package for task-first implementation readiness.

- Is the package already freeze-ready at the TECH layer, not merely structurally present?
- Does the selected `tech_ref` remain the authoritative technical design source for the selected `feat_ref`?
- Does `selected_upstream_refs` explicitly carry `integration_context_ref`, `canonical_owner_refs`, `state_machine_ref`, `nfr_constraints_ref`, `migration_constraints_ref`, and `algorithm_constraint_refs`?
- Are scope, constraints, dependencies, acceptance checks, and the frozen upstream refs explicit enough to derive implementation tasks without inventing new design truth?
- If `ARCH` or `API` are present, are they referenced as inherited authorities rather than restated or re-decided?
- Would accepting this TECH package force IMPL to guess boundaries, state transitions, ownership, migration behavior, or algorithm rules that should have been fixed upstream?
- Can `upstream-design-refs.json` and the downstream handoff mirror the same frozen refs without reinterpretation?

