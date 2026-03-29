---
artifact_type: project_init_request
schema_version: 1.0.0
project_name: Demo LEE Workspace
project_slug: demo-lee-workspace
description: Governed skill-first workspace for a new LL project.
target_root: E:/work/demo-lee-workspace
template_profile: lee-skill-first
default_branch: main
managed_files_policy: create_missing
initialize_runtime_shells: true
authoritative_layout_ref: skill://ll-project-init/resources/project-structure-reference.md
source_refs:
  - docs/repository-layout.md
---

# Demo LEE Workspace Initialization Request

Create the standard LEE Lite repository scaffold without overwriting any unmanaged files that may already exist in the target root.
