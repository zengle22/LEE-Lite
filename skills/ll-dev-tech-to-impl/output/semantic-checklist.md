# Output Semantic Checklist

Review the `feature_impl_candidate_package` against the selected TECH package.

- Is `impl-task.md` clearly task-first rather than a rewritten technical design?
- Does the package expose a concrete repo-aware touch set, including which modules are new, extended, or forbidden to modify?
- Does the package break implementation into ordered executable tasks with dependencies, parallelism, outputs, and task-level done criteria?
- Are the frozen state machine, API contracts, UI entry/exit, invariants, and boundaries embedded directly into IMPL instead of left as upstream-only references?
- Does every acceptance check map to named implementation tasks and evidence expectations?
- Is `upstream-design-refs.json` explicit enough that downstream execution does not need to guess `TECH / ARCH / API` authority?
- Are frontend, backend, and migration workstreams emitted only when the applicability assessment justifies them?
- If migration exists, is it based on explicit implementation surface rather than keyword-only inference?
- Does the package stay at the implementation-candidate layer instead of drifting into release planning, QA strategy, or code-complete claims?
- Does the handoff to `template.dev.feature_delivery_l2` preserve `feat_ref`, `impl_ref`, `tech_ref`, and optional `arch_ref / api_ref`?

