# Output Semantic Checklist

Review the `feature_impl_candidate_package` against the selected TECH package.

- Is `impl-task.md` clearly task-first rather than a rewritten technical design?
- Is `upstream-design-refs.json` explicit enough that downstream execution does not need to guess `TECH / ARCH / API` authority?
- Are frontend, backend, and migration workstreams emitted only when the applicability assessment justifies them?
- Does the package stay at the implementation-candidate layer instead of drifting into release planning, QA strategy, or code-complete claims?
- Does the handoff to `template.dev.feature_delivery_l2` preserve `feat_ref`, `impl_ref`, `tech_ref`, and optional `arch_ref / api_ref`?

