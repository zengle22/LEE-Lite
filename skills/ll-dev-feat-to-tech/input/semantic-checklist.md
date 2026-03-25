# Input Semantic Checklist

Review the selected FEAT inside the `feat_freeze_package` for semantic readiness.

- Is the package already freeze-ready at the FEAT layer, not merely structurally present?
- Does the selected `feat_ref` remain a FEAT rather than a TASK, implementation slice, or architecture-only note?
- Are scope, constraints, dependencies, and acceptance checks explicit enough to derive design objects without inventing new product scope?
- Does the selected FEAT preserve authoritative EPIC and SRC lineage through `source_refs`, `epic_freeze_ref`, and `src_root_id`?
- Would accepting this FEAT force the design workflow to guess missing boundaries that should have been fixed upstream?
