# Output Semantic Checklist: ll-patch-capture

- [ ] Patch YAML file exists at ssot/experience-patches/{FEAT-ID}/UXPATCH-NNNN__{slug}.yaml
- [ ] Patch YAML passes schema validation (python -m cli.lib.patch_schema --type patch <file>)
- [ ] Patch ID follows UXPATCH-NNNN format with sequential numbering
- [ ] Patch status is "active" for new registrations
- [ ] change_class is one of: visual, interaction, semantic
- [ ] source.human_confirmed_class is non-null (matches ai_suggested_class in auto-pass mode)
- [ ] scope.feat_ref matches the input feat_id
- [ ] patch_registry.json has been updated with the new entry
- [ ] patch_registry.json last_updated timestamp is current
- [ ] For Document-to-SRC path: resolution.src_created is set if SRC was generated
- [ ] For Document-to-SRC path with experience-layer changes: semantic Patch exists as associated record
