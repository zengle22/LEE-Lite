# Rule Map

Purpose: route agents from the L0 constitution to the smallest rule set needed for a task.

Default: load `ssot/governance/AI-CONSTITUTION.md` first. Load this map only when a task needs rule detail beyond the constitution.

## Constitutional Rules

| Rule domain | Primary source | Registry |
| --- | --- | --- |
| Authority and carrier boundaries | `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD` | `ssot/registry/rule_registry.yaml` |
| FRZ semantic authority | `ssot/adr/ADR-050-SSOT语义治理总纲.md` | `ssot/registry/rule_registry.yaml` |
| Repository layout | `docs/repository-layout.md` | `ssot/registry/rule_registry.yaml` |
| Patch context and reflow | `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` | `ssot/registry/rule_registry.yaml` |
| Skill authoring and installation | `skills/ll-meta-skill-creator/SKILL.md`, `skills/ll-skill-install/SKILL.md` | `ssot/registry/skill_registry.yaml` |

## Load By Need

For a new workflow or runtime abstraction, load ADR-038 first.

For product semantics, FRZ, SSOT extraction, patch grading, or downstream semantic drift, load ADR-050 and then ADR-049 if the task touches patch handling.

For file placement, cleanup, or adapter location, load `docs/repository-layout.md`.

For a concrete skill execution, load `ssot/governance/maps/SKILL-MAP.md` and then only the selected `SKILL.md`.

## Enforcement

Use `tools/validate_ai_governance.py` to verify maps, registries, ADR references, adapter bootloaders, and skill read-order closure.
