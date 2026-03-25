# Authoring Checklist

- Confirm the workflow stays between `ll-product-raw-to-src` and `product.epic-to-feat`.
- Require a freeze-ready `src_candidate_package`, not raw demand text.
- Encode the canonical template path and `lee run product.src-to-epic` command.
- Keep EPIC output at the multi-FEAT layer and forbid FEAT or TASK leakage.
- Require `epic_freeze_ref`, `src_root_id`, and a downstream handoff artifact.
- Preserve ADR-025 acceptance artifacts as explicit runtime outputs.
- Keep executor and supervisor responsibilities separate.
