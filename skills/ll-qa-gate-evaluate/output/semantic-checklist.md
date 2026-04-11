# Output Semantic Checklist: ll-qa-gate-evaluate

- [ ] release_gate_input.yaml exists at ssot/tests/.artifacts/tests/settlement/
- [ ] Has gate_evaluation root key
- [ ] evaluated_at timestamp present
- [ ] feature_id present
- [ ] final_decision is one of: pass, fail, conditional_pass
- [ ] api_chain section with all metrics
- [ ] e2e_chain section with all metrics
- [ ] anti_laziness_checks section with all 7 checks
- [ ] evidence_hash present (SHA-256)
- [ ] decision_reason present and explains the decision
