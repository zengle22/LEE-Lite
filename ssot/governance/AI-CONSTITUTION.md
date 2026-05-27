# LEE Lite Project Constitution

Status: Canonical
Scope: all AI agents, CLI carriers, skills, workflows, gates, governance tooling, and project knowledge routing in this repository
Default context rule: load this file first and only this file by default

## 1. Basic Project Rules

The project tree stores reusable, reviewable, versionable, and traceable content only.

- Canonical governance belongs in `ssot/`.
- Canonical ADRs belong in `ssot/adr/`.
- Canonical skills belong in `skills/`.
- Shared validators, helpers, adapters, and command carriers belong in `cli/` and `tools/`.
- Durable audit outcomes belong in `artifacts/`.
- Human-facing explanatory or operational documentation belongs in `docs/`.
- Runtime residue, scratch state, temporary downloads, shell dumps, retry context, local cache, and unconfirmed drafts must stay outside the canonical tree or inside ignored local space.

Agent adapter files such as `CLAUDE.md`, `AGENTS.md`, and `agent.md` are bootloaders. They may point to this constitution and describe adapter loading mechanics, but they must not copy, fork, extend, or replace constitutional rules.

All skills in `skills/*` run inside an agent environment such as Claude Code, Codex, or Cursor. They are not standalone LLM applications, and their Python code must not embed LLM API calls. Semantic understanding is delegated to the host agent through governed skill instructions; scripts handle rule-based mechanics only.

If a skill invokes a script, command, validator, or tool and that invocation fails, the skill execution must fail. The host agent may report the failure, collect evidence, or route repair work, but it must not manually perform the failed tool step and then treat the skill as successful.

## 2. Knowledge Map

Project knowledge is routed by authority, not by convenience.

| Knowledge need | Primary source | Supplemental source |
| --- | --- | --- |
| Project rules and agent behavior | `ssot/governance/AI-CONSTITUTION.md` | `ssot/governance/maps/`, `ssot/registry/rule_registry.yaml` |
| Architecture decisions and governed design truth | `ssot/adr/` | `docs/architecture/`, `docs/guides/` |
| Repository layout | `docs/repository-layout.md` | `ssot/governance/maps/RULE-MAP.md` |
| SSOT object model and semantic routing | `ssot/adr/ADR-050-SSOT语义治理总纲.md`, `ssot/governance/maps/SSOT-MAP.md` | `ssot/README.md`, `docs/` |
| Runtime, carrier, and authority boundaries | `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD` | `ssot/governance/maps/RUNTIME-MAP.md` |
| Patch grading and reflow | `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` | `ssot/registry/rule_registry.yaml` |
| Skill authoring and execution | `skills/*/SKILL.md`, `ssot/governance/maps/SKILL-MAP.md` | `docs/guides/`, skill-local resources |
| Operational explanations, guides, and implementation notes | `ssot/adr/` when they decide authority | `docs/` when they explain or supplement |

When ADR and docs disagree, `ssot/adr/` wins for project knowledge and governance truth. `docs/` may explain, summarize, or operationalize ADRs, but must not silently override them.

## 3. Authority First

Always classify the architectural authority before selecting a carrier.

- Command is an explicit entry point.
- Skill is a governed capability template.
- Tool is an atomic execution capability with schema, permission, and evidence semantics.
- Agent is an execution subject with role, context boundary, and allowed tool pool.
- Workflow is a multi-step process authority.
- Task is a recoverable runtime work unit.
- Session is long-lived execution context and runtime residue.
- Artifact is a durable formal output.
- Evidence is an artifact used to support a claim, gate, or decision.
- Gate is the only authority that may promote state.

Carrier must not redefine authority. A script is not automatically a tool, a CLI command is not automatically a skill, and a session trace is not automatically a formal artifact.

## 4. Semantic Authority

FRZ is the semantic source of truth. SSOT objects express, project, and organize FRZ truth; they must not invent or rewrite business semantics.

FRZ content must come from human discussion, reviewed upstream documents, or accepted external-framework output. AI may structure and extract; AI must not fabricate frozen truth.

## 5. Extraction Over Generation

SRC, EPIC, FEAT, SURFACE_MAP, TECH, API, UI, PROTOTYPE, IMPL, and TESTSET are governed projections around a frozen semantic source. Downstream objects may add implementation detail only inside their explicit authority boundary.

If a proposed change alters user journeys, functional logic, state transitions, acceptance criteria, or expected test behavior, it is a semantic change and must return to FRZ revision before SSOT update.

## 6. Gate Ownership

Skills produce candidates, evidence, and handoff proposals. They do not self-promote canonical state.

Only a Gate may approve, reject, revise, or advance a governed state transition. Runners, skills, scripts, commands, and agents are carriers or participants, not promotion authority.

## 7. Evidence Before Claims

No implementation-readiness, release-readiness, freeze, settlement, or gate decision is valid without evidence references.

Execution evidence records what was done. Supervision evidence records review, semantic checks, and decision rationale. Executor and supervisor responsibilities must remain separated; an executor must not issue the final semantic pass on its own output.

## 8. Patch Reflow

Experience changes use ADR-049 grading.

- visual: Minor, retain or patch in code unless a downstream spec explicitly requires backwrite.
- interaction: Minor, settle through patch backwrite to UI, flow, or TESTSET authority as applicable.
- semantic: Major, revise FRZ, then re-extract or update SSOT through the governed chain.
- other: Minor by default, human may escalate.

Patch context relevant to target files must be injected before code edits. Patch registration after edits requires user confirmation.

## 9. Progressive Disclosure

Agents must not load the entire repository by default.

Load order:

1. Batch 0: this constitution only.
2. Batch 1: one map under `ssot/governance/maps/` selected by task type.
3. Batch 2: the smallest relevant set of ADRs or `SKILL.md` files.
4. Batch 3: contracts, checklists, agents, scripts, and schemas only when execution requires them.
5. Batch 4: evidence, runtime reports, and historical material only for verification, debugging, or audit.

Maps and registries guide disclosure. They do not override this constitution.

## 10. Repository Boundary

The project tree stores reusable, reviewable, versionable, and traceable content.

Canonical rules belong in `ssot/`. Canonical skills belong in `skills/`. Shared validators and carriers belong in `cli/` and `tools/`. Runtime residue, scratch state, temporary downloads, shell dumps, retry context, and unconfirmed drafts must not become canonical project content.

## 11. One Constitution

Claude, Codex, Cursor, local CLI commands, and any future agent adapter must reference this same constitution. Adapter files may act as bootloaders, but they must not copy, fork, or extend constitutional rules.

If an adapter, skill, registry, or document conflicts with this constitution, the constitution wins and the conflict must be recorded as a governance issue.

## 12. Broken References Block

Governance references must be closed. A required ADR, map, registry, contract, read-order file, schema, or authority reference that cannot be resolved blocks the affected workflow until repaired or explicitly marked planned with owner and reason.

Missing authority is not a warning when it affects promotion, freeze, patch routing, skill execution, or evidence validation; it is a blocker.
