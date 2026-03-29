# Repository Layout

## Scope

This repository no longer uses a separate `spec/` standards layer.
Repo-wide rules live in `ssot/` when they need canonical governance and in
`docs/` when they are explanatory or operational.

## Directory Principle

The project tree only stores content that is:

- reusable
- reviewable
- versionable
- traceable

Runtime state is excluded from the main project tree.

## Runtime Boundary

The following do not belong in the repository:

- session state
- agent scratch files
- temporary patches
- command cache
- shell stdout or stderr dumps
- retry context
- local token or cache files
- process locks and PID files
- temporary downloads
- unconfirmed repair drafts

Recommended homes for runtime state:

- system temp directories such as `/tmp/ll/`
- user cache directories such as `~/.cache/ll/`
- user state directories such as `~/.ll/`
- ignored local workspaces such as `/.local/`

Project-internal runtime outcomes are allowed only when they are durable audit
objects, such as validation reports, review reports, freeze reports, execution
evidence, supervision evidence, and lineage snapshots.

## Top-Level Responsibilities

### `/.claude/`

Claude-specific integration only.

Allowed:

- command shims
- Claude-facing skill adapters
- Claude settings

Not allowed:

- canonical artifact state
- shared governance rules
- CLI implementation
- runtime residue

### `/ssot/`

Canonical governable rules and formal objects.

Allowed:

- ADRs and formal lifecycle objects
- repository-wide governance rules
- canonical object definitions
- rules that downstream workflows inherit

Not allowed:

- workflow-local helper notes
- temporary drafts
- runtime residue

### `/skills/`

Reusable skill definitions and skill tooling.

Allowed:

- `SKILL.md`
- contracts and lifecycle files
- templates and checklists
- governance references
- skill-local scripts

Skill-local human checklists must stay inside the owning skill tree.
When a checklist is primarily for manual acceptance or operator verification of
one specific skill, the canonical home is:

- `skills/<skill-id>/resources/checklists/acceptance-checklist.md`

Cross-skill playbooks or repo-wide operational guides belong in `docs/`, not in
an individual skill folder.

Not allowed:

- runtime scratch state
- temporary execution residue
- formal project artifacts

### `/cli/`

Shared validators, helpers, adapters, and future command implementations.

### `/artifacts/`

Reviewable outputs and audit outcomes only.

Allowed:

- `src/`, `epic/`, `feat/`, `task/`
- validation, review, freeze, and repair reports
- execution and supervision evidence
- lineage indexes and snapshots

Not allowed:

- raw command logs
- cache files
- temporary downloads
- `final-final-v2` style drafts

### `/docs/`

Human-facing long-lived documentation such as architecture notes, playbooks,
policy writeups, and repository guides.

### `/knowledge/`

Durable patterns, retrospectives, and distilled learnings that are useful but
are not the canonical rule source.

### `/examples/`

Learning and demo material only. Example content must not be treated as the
authoritative source of production truth.

### `/tests/`

Unit, integration, fixture, and golden test material only.

### `/.local/`

Ignored local workspace for machine-specific experiments and developer-only
helpers. This directory may exist in the repository as a documented shell, but
its mutable contents must stay untracked.

## Forbidden Root Directories

Do not introduce ambiguous top-level folders such as:

- `tmp/`
- `temp/`
- `scratch/`
- `runtime/`
- `sessions/`
- `cache/`
- `logs/`
- `debug/`
- `drafts/`
- `misc/`
- `stuff/`
- `backup/`
- `old/`
- `final2/`
- `test2/`
- `new/`

## Current Mapping

This repository is initialized with the following canonical mapping:

- example workflow sample: `examples/sample-workflows/src-to-epic/`
- skill tooling: `skills/ll-meta-skill-creator/`
- Codex skill tooling: `skills/ll-meta-skill-creator-codex/`
- repository layout guide: `docs/repository-layout.md`

## Practical Rule

Use this sentence as the default review gate:

> Project tree = SSOT + Skill + CLI + Artifacts + Docs + Knowledge.
> Runtime lives outside the tree. Only outcomes enter the tree.
