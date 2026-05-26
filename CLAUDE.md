# Claude Bootloader

This file is a thin adapter bootloader for Claude in this repository.

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

## Skill Runtime Environment

All skills in this repository (`skills/*`) are designed to run **exclusively
within an agent environment** (Claude Code, Codex, Cursor, etc.). They are not
standalone CLI tools and must not embed LLM API calls within their Python code.

**Architecture consequence**: When a skill needs semantic understanding
(e.g., `ll-v2-frz-ingest` parsing non-standard Markdown), the skill delegates
to the host agent via skill steps and natural language instructions — rather
than calling an LLM API internally. Python code handles rule-based logic only;
semantic extraction is performed by the agent.

## Patch Rules

Patch context, grading, reflow, and registration are governed by the
constitution and `ssot/registry/rule_registry.yaml`.

Before editing target files, inject patch context for exactly those target
files. After editing, do not register patches automatically; patch registration
requires user confirmation.
