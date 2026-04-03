# Review Checklist

- `ssot_alignment`: confirm the FEAT bundle stays aligned with the upstream EPIC package, preserves `epic_freeze_ref`, `src_root_id`, `source_refs`, and inherited semantic-lock meaning.
- `object_completeness`: confirm the output is a real FEAT bundle with multiple independently acceptable FEAT slices, explicit acceptance boundaries, and usable downstream handoff targets.
- `contract_completeness`: confirm `feat_refs`, downstream workflow handoff metadata, evidence refs, and the document-test carrier are present and mutually coherent.
- `state_transition_closure`: review revision handling, freeze decisions, and downstream routing; if only part of that path was reviewed, emit `partial`, not `checked`.
- `failure_path`: review revise/rebuild and semantic-drift failure handling; if those paths were not inspected, emit `not_checked` and let the gate block.
- `testability`: confirm runtime validation, document-test, and downstream derivation checks can still prove the bundle is freeze-ready; if that proof is incomplete, emit `partial`.
- Required phase-1 rule: only the six dimensions above may appear in coverage, and each must use `checked|partial|not_checked`.
- Required phase-1 rule: any required dimension marked `not_checked`, or any positive `blocker_count`, must block freeze-ready handoff.
