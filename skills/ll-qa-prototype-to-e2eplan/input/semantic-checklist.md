# Input Semantic Checklist: ll-qa-prototype-to-e2eplan

- [ ] Prototype or FEAT package path is valid
- [ ] Source is frozen
- [ ] Prototype has flow map (if prototype-driven), or FEAT has Scope (if API-derived)
- [ ] Output directory exists or can be created

---

# Output Semantic Checklist: ll-qa-prototype-to-e2eplan

- [ ] e2e-journey-plan.md exists at ssot/tests/e2e/{prototype_id}/
- [ ] Plan metadata is complete
- [ ] anchor_type is "prototype"
- [ ] derivation_mode set (prototype-driven or api-derived)
- [ ] At least 1 main journey (P0)
- [ ] At least 1 exception journey
- [ ] Each journey has entry_point and at least 2 user_steps
