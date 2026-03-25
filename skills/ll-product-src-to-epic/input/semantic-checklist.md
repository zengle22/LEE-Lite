# Input Semantic Checklist

Review the `src_candidate_package` for readiness to enter `product.src-to-epic`.

- Is the package clearly produced by `ll-product-raw-to-src` and marked `freeze_ready` rather than `blocked` or `human_handoff_proposed`?
- Does the SRC candidate express a problem space large enough to justify an EPIC rather than a single FEAT?
- Does the SRC imply a shared governance/runtime change whose real effect depends on existing skill migration or cross-skill E2E validation?
- Are scope boundaries, non-goals, and key constraints explicit enough to prevent scope invention during EPIC design?
- Do the source refs, semantic findings, and acceptance report agree on the same authoritative story?
- Would accepting this package create a parallel truth, skip an unresolved review concern, or bypass an expected human decision?
