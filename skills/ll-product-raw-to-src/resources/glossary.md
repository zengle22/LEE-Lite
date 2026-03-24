# Glossary

- raw input: any upstream product source such as ADR, raw requirement, business opportunity, or business opportunity freeze.
- SRC candidate: normalized source artifact produced by this skill before external gate materialization.
- thin bridge SRC: ADR-derived candidate that records change scope and downstream impact without pretending to be downstream product design.
- structural validation: deterministic checks for schema shape, status guards, refs, and required sections.
- semantic validation: review of topic fidelity, scope boundaries, and proper artifact layering.
- acceptance report: staged review output that records semantic findings and defect severities.
- minimal patch: a defect-scoped repair that updates only the referenced issue instead of rewriting the whole candidate.
- external gate: the consumer that reads result summary, proposals, and evidence to decide freeze, retry, blocked, or next-skill routing.
