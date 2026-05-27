# Agent Bootloader

This file is a thin adapter bootloader for generic agent entry points in this
repository.

## Default Load

Load only:

- `ssot/governance/AI-CONSTITUTION.md`

Do not load the full repository, mirrored adapter rules, skill copies, ADRs, or
runtime reports by default.

## Progressive Load

When the task needs more detail, follow the constitution's progressive
disclosure order:

1. Select the smallest relevant map under `ssot/governance/maps/`.
2. From that map, load only the required ADR, registry, `SKILL.md`, contract,
   checklist, schema, script, evidence, or report.

The maps route context. They do not override the constitution.

## Rule Authority

Claude, Codex, Cursor, local CLI commands, and future adapters use the same
governance source:

- Constitution: `ssot/governance/AI-CONSTITUTION.md`
- Rule routing and registries: `ssot/governance/maps/` and
  `ssot/registry/rule_registry.yaml`

This file must not copy, fork, extend, or replace constitutional rules. If this
bootloader conflicts with the constitution, the constitution wins and the
conflict must be recorded as a governance issue.

## Patch Rules

Patch context, grading, reflow, and registration are governed by the
constitution and `ssot/registry/rule_registry.yaml`.

Before editing target files, inject patch context for exactly those target
files. After editing, do not register patches automatically; patch registration
requires user confirmation.
