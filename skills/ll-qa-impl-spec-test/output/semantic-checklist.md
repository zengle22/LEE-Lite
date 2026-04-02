# Output Semantic Checklist

- Verdict is one of `pass`, `pass_with_revisions`, or `block`.
- Verdict remains an implementation-readiness result, not an external gate decision.
- Output package contains intake, issue inventory, counterexample, and verdict surfaces.
- Repair routing points to a valid upstream artifact target.
- Candidate, package, and handoff refs are all present and traceable.
- Deep mode output contains semantic review, system views, logic risk inventory, UX risk inventory, UX improvement inventory, journey simulation, state invariant checks, cross-artifact trace, open questions, dimension reviews, and review coverage surfaces.
- Dimension reviews carry both score and coverage confidence for all 8 ADR-036 dimensions.
- Counterexample output covers the required family set or explicitly records coverage gaps for high-risk dimensions.
- Deep mode counterexamples include canonical-field-missing, invalid-input, patch-save-success-completion-not-updated, state-write-failed, network-failure, risk-gate-fail, device-auth-finalize-fail, and compatibility-conflict-blocked as covered, coverage-gap, or not-applicable.
- `review_coverage.status` must be one of `sufficient`, `partial`, or `insufficient`.
- `review_coverage.status != sufficient` must not coexist with `verdict=pass`.
- Phase 2 outputs, when emitted, must resolve `logic_risk_inventory_ref`, `ux_risk_inventory_ref`, `ux_improvement_inventory_ref`, `journey_simulation_ref`, `state_invariant_check_ref`, `cross_artifact_trace_ref`, `open_questions_ref`, and `false_negative_challenge_ref`.
- UX risk and UX improvement surfaces must be separated so friction and opportunity are not conflated.
