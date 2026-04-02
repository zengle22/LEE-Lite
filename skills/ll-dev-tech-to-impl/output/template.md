---
artifact_type: feature_impl_candidate_package
workflow_key: dev.tech-to-impl
status: in_progress
package_role: candidate
schema_version: 1.0.0
source_refs:
  - dev.feat-to-tech::RUN-ID
feat_ref: FEAT-TODO
impl_ref: IMPL-FEAT-TODO
tech_ref: TECH-FEAT-TODO
---

# {{TITLE}}

## Selected Upstream

[Summarize the selected FEAT and inherited TECH authority.]

## Package Semantics

[State that IMPL is the canonical execution package / execution-time single entrypoint, not a domain truth source, and summarize freshness/provisional/discrepancy policy.]

## Applicability Assessment

[State whether frontend, backend, and migration workstreams apply, and why.]

## Implementation Task

[Embed the execution-critical summary directly here: concrete touch set, repo-aware placement, embedded contracts, ordered tasks, and acceptance mapping. `impl-task.md` may expand this package, but `impl-bundle.md` must still be self-contained enough for downstream execution intake and review.]

## Integration Plan

[Summarize integration sequencing assumptions.]

## Evidence Plan

[Summarize evidence coverage expectations for downstream execution.]

## Smoke Gate Subject

[Summarize the blocked/ready criteria for smoke review.]

## Delivery Handoff

[Describe the canonical handoff into `template.dev.feature_delivery_l2`.]

## Consumption Boundary

[State explicitly that release summaries are not the coder/tester execution contract. `impl-bundle.md` and `impl-task.md` together form the strong self-contained implementation package, and neither may omit execution-critical facts by pushing them into upstream refs only.]

## Traceability

[Map output sections back to authoritative TECH and FEAT refs.]

