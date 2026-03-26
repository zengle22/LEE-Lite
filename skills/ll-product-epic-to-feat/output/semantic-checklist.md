# Output Semantic Checklist

Review the `feat_freeze_package` against the upstream `epic_freeze_package`.

- Does each FEAT stay at the independently acceptable product capability layer rather than collapsing into TASK, UI, or implementation detail?
- Does each FEAT define the product shape itself: actors, user story, trigger, pre/postconditions, business flow, deliverables, and business timeline?
- Is the FEAT inventory faithful to the parent EPIC scope, decomposition rules, non-goals, and inherited constraints?
- If the parent EPIC carries `semantic_lock`, does the FEAT bundle preserve that exact runtime anchor instead of decomposing into a nearby but different chain such as formal publication or admission?
- When the parent EPIC carries `rollout_requirement.required = true` or `required_feat_tracks` includes `adoption_e2e`, does the FEAT bundle include an explicit skill-onboarding / migration / cross-skill-E2E slice rather than treating rollout as release-only glue?
- Are the structured acceptance checks FEAT-specific rather than bundle-generic, and are they explicit enough for downstream TECH and TESTSET derivation?
- Would a downstream reader be able to draw the main business flow and list the FEAT deliverables without reopening TECH?
- Does the bundle provide a horizontal boundary matrix that makes overlap and adjacent non-responsibility explicit across FEATs, while shared non-goals stay at bundle level?
- Are traceability and independent-acceptance requirements expressed as bundle-level conventions rather than padding every FEAT acceptance list?
- Does the output preserve `epic_freeze_ref`, `src_root_id`, `source_refs`, and review traceability without inventing new requirements?
- Would a downstream reader treat this package as the single governed FEAT truth for downstream TECH and TESTSET derivation?
