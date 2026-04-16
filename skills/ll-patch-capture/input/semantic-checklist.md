# Input Semantic Checklist: ll-patch-capture

- [ ] feat_id is provided and non-empty
- [ ] input_type is either "prompt" or "document"
- [ ] input_value contains meaningful content (not whitespace-only)
- [ ] If input_type is "document", the file exists and is readable
- [ ] If input_type is "document", the file is within the workspace root (no path traversal)
- [ ] Dual-path routing decision is explicit: Prompt-to-Patch or Document-to-SRC
