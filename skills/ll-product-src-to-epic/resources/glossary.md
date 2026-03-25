# Glossary

- src_candidate_package: the freeze-ready handoff package emitted by `ll-product-raw-to-src`.
- epic_freeze_package: the governed EPIC package emitted by this skill for downstream FEAT decomposition.
- structural validation: deterministic checks such as schema, refs, required artifact presence, and handoff completeness.
- semantic validation: review of fidelity, scope, artifact layer, and downstream usability.
- ADR-025: the acceptance checkpoint policy that requires auto-check, review, defect handling, and approval before freeze.
- epic_freeze_ref: the authoritative EPIC freeze reference that downstream `product.epic-to-feat` must consume.
