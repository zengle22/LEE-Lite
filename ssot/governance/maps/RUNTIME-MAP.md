# Runtime Map

Purpose: map runtime concepts to their authority and carrier.

Primary authority: `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD`.

| Runtime concept | Authority meaning | Current carrier |
| --- | --- | --- |
| Command | Explicit trigger entry point | `cli/commands/`, `.claude/commands/` |
| Skill | Governed capability template | `skills/<skill-id>/SKILL.md` |
| Tool | Atomic execution capability with schema, permission, evidence semantics | CLI protocol contracts, tool-specific runtime |
| Agent | Execution subject with role and context boundary | `skills/<skill-id>/agents/*.md`, adapter runtime |
| Workflow | Multi-step process authority | `skills/<skill-id>/ll.contract.yaml`, workflow ADRs |
| Task | Recoverable runtime work unit | job object family and TaskPack runtime |
| Session | Long-lived context and runtime residue | `.workflow/`, local runtime directories |
| Artifact | Durable formal output | `artifacts/`, `ssot/` |
| Evidence | Artifact supporting a claim or decision | evidence refs, `artifacts/evidence/`, skill evidence outputs |
| Gate | State promotion boundary | gate runtime and gate artifacts |

## Common Misclassifications

- A CLI command is a carrier, not the capability authority.
- A script is a carrier, not automatically a Tool.
- `impl-task.md` is an artifact carrier, not runtime Task authority.
- `.workflow/` content is session residue, not formal SSOT.
- A skill may produce a candidate, but Gate owns promotion.

## Load Next

For skill execution, load `ssot/governance/maps/SKILL-MAP.md`.

For file placement, load `docs/repository-layout.md`.

For gate decisions, load the relevant gate skill and ADRs listed in `ADR-MAP.md`.
