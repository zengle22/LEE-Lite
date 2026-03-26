# Output Semantic Checklist

Review the `epic_freeze_package` against the upstream `src_candidate_package`.

- Does the EPIC stay at the multi-FEAT product capability layer rather than collapsing into FEAT, TASK, UI, or implementation detail?
- Does the EPIC define business value/problem, product positioning, actors/roles, and upstream/downstream context instead of only listing governance principles?
- Is the EPIC faithful to the upstream SRC package, including its scope boundaries, non-goals, and key constraints?
- If the SRC carries `semantic_lock`, does the EPIC preserve that exact runtime anchor instead of translating it into a nearby but different chain such as formal publication or admission?
- Are epic success criteria, decomposition rules, and acceptance artifacts explicit enough for downstream `product.epic-to-feat` work?
- Would a downstream FEAT author know what product capability block this EPIC owns without reopening the source ADR/SRC?
- Does the output preserve `src_root_id`, `source_refs`, and ADR-025 acceptance traceability without inventing new requirements?
- When rollout/adoption is required, does the output keep a single EPIC while making rollout/E2E decomposition explicit enough that downstream `epic-to-feat` cannot silently drop it?
- Would a downstream reader treat this package as the single governed EPIC truth for the next decomposition step?
