# Input Semantic Checklist: ll-experience-patch-settle

- [ ] feat_id is provided and non-empty
- [ ] feat_id format matches ^[a-zA-Z0-9][\w.\-]*$ (no path traversal)
- [ ] workspace points to an existing directory
- [ ] ssot/experience-patches/{feat_id}/ directory exists
- [ ] patch_registry.json exists and is valid JSON in feat directory
- [ ] At least one UXPATCH-*.yaml file with status pending_backwrite exists
- [ ] All pending_backwrite patches pass schema validation via cli/lib/patch_schema.py validate_file
- [ ] change_class_filter (if provided) is one of: visual, interaction, semantic
