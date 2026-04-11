# Output Semantic Checklist: ll-qa-e2e-spec-gen

- [ ] Spec files exist at ssot/tests/e2e/{prototype_id}/e2e-journey-spec/
- [ ] Number of spec files = number of non-cut coverage items
- [ ] Each spec has entry_point section
- [ ] Each spec has user_steps list
- [ ] Each spec has expected_ui_states
- [ ] Each spec has expected_network_events (if API calls exist)
- [ ] Each spec has expected_persistence
- [ ] Each spec has evidence_required (with playwright_trace + screenshot)
- [ ] Each spec has anti_false_pass_checks (P0: at least 3)
- [ ] Filenames are unique
