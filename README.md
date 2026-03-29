# LEE Lite Skill-First

This repository is organized around durable layers with clearer ownership:

- `ssot/`: canonical, governable rules and formal objects
- `skills/`: reusable workflow skills and skill-local contracts or schemas
- `cli/`: validators, helpers, and future CLI implementation
- `artifacts/`: reviewable outputs, reports, evidence, and lineage
- `docs/`: long-lived human-facing documentation and repository guides
- `knowledge/`: durable patterns, retrospectives, and distilled learnings

Runtime state is intentionally kept outside the project tree. Temporary
sessions, cache files, scratch outputs, locks, and debug logs must live in
system temp directories, user cache directories, or ignored local workspaces.
