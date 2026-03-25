# Output Semantic Checklist

Review the `epic_freeze_package` against the upstream `src_candidate_package`.

- Does the EPIC stay at the multi-FEAT product capability layer rather than collapsing into FEAT, TASK, UI, or implementation detail?
- Is the EPIC faithful to the upstream SRC package, including its scope boundaries, non-goals, and key constraints?
- Are success metrics, decomposition rules, and acceptance artifacts explicit enough for downstream `product.epic-to-feat` work?
- Does the output preserve `src_root_id`, `source_refs`, and ADR-025 acceptance traceability without inventing new requirements?
- When rollout/adoption is required, does the output keep a single EPIC while making rollout/E2E decomposition explicit enough that downstream `epic-to-feat` cannot silently drop it?
- Would a downstream reader treat this package as the single governed EPIC truth for the next decomposition step?
