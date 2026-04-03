# Review Checklist

- `ssot_alignment`: confirm the EPIC stays aligned with the upstream SRC package, preserves `src_root_id` and `source_refs`, and does not drift away from inherited semantic locks or ADR-025 acceptance meaning.
- `object_completeness`: confirm the package still describes an EPIC boundary, includes the required capability slices, actors, upstream/downstream links, and does not collapse into a single FEAT or implementation object.
- `contract_completeness`: confirm `epic_freeze_ref`, downstream handoff to `product.epic-to-feat`, evidence refs, and the document-test carrier are present and mutually coherent.
- `state_transition_closure`: review whether revision handling, freeze decisions, and gate routing remain explicit; if only part of that was reviewed, emit `partial`, not `checked`.
- `failure_path`: review rebuild, revise, and semantic-drift failure handling; if the review did not inspect those paths, emit `not_checked` and expect the gate to block.
- `testability`: confirm the package can still be validated by runtime, document-test, and downstream freeze checks; if that proof is incomplete, emit `partial`.
- Required phase-1 rule: the six dimensions above must be emitted with the exact vocabulary `checked|partial|not_checked`; custom dimension names are forbidden.
- Required phase-1 rule: any required dimension marked `not_checked`, or any positive `blocker_count`, must block freeze-ready handoff.
