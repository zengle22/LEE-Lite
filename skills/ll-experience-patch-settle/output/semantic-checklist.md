# Output Semantic Checklist: ll-experience-patch-settle

- [ ] resolved_patches.yaml exists at ssot/experience-patches/{feat_id}/
- [ ] resolved_patches.yaml contains settlement_report top-level key
- [ ] settlement_report.generated_at contains valid ISO timestamp
- [ ] settlement_report.total_settled > 0 and matches results array count
- [ ] settlement_report.by_class counts match actual settlement distribution
- [ ] All processed patches have status updated from pending_backwrite to terminal state
- [ ] patch_registry.json last_updated reflects settlement time
- [ ] For interaction patches: ui-spec-delta.yaml, flow-spec-delta.yaml, test-impact-draft.yaml exist
- [ ] Delta files contain original_text / original_flow fields (D-06 compliance)
- [ ] For semantic patches: SRC-XXXX__{slug}.yaml exists with requires_gate_approval: true
- [ ] For visual patches: no delta files generated, status set to retain_in_code
- [ ] No frozen SSOT files were modified (D-05)
- [ ] Escalation conditions (D-10) checked: conflicts, ambiguity, test_impact uncertainty
