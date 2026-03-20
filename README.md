# LEE Lite Skill-First

This repository is organized around five durable layers:

- `spec/`: standards, contracts, schemas, and governance rules
- `skills/`: reusable skill definitions and tooling skills
- `cli/`: validators, helpers, and future CLI implementation
- `artifacts/`: reviewable outputs, reports, evidence, and lineage
- `docs/`: long-lived human-facing documentation

Runtime state is intentionally kept outside the project tree. Temporary
sessions, cache files, scratch outputs, locks, and debug logs must live in
system temp directories, user cache directories, or ignored local workspaces.
