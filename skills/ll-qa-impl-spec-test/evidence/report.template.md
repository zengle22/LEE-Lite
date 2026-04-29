# Impl Spec Test Evidence

- request_id: {{ request_id }}
- mode: {{ execution_mode.mode }}
- verdict: {{ verdict }}
- review_coverage_status: {{ review_coverage.status }}
- review_coverage_status values are `sufficient`, `partial`, or `insufficient`.
- phase2 extended surfaces, when emitted, must be separately addressable by ref.
- gate_subject_ref: {{ gate_subject_ref }}
- logic_risk_inventory_ref: {{ logic_risk_inventory_ref }}
- ux_risk_inventory_ref: {{ ux_risk_inventory_ref }}
- ux_improvement_inventory_ref: {{ ux_improvement_inventory_ref }}
- journey_simulation_ref: {{ journey_simulation_ref }}
- state_invariant_check_ref: {{ state_invariant_check_ref }}
- cross_artifact_trace_ref: {{ cross_artifact_trace_ref }}
- open_questions_ref: {{ open_questions_ref }}
- false_negative_challenge_ref: {{ false_negative_challenge_ref }}
