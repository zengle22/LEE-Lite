# LEE Lite AI Constitution

Status: Canonical  
Scope: all AI agents, CLI carriers, skills, workflows, gates, and governance tooling in this repository  
Default context rule: load this file first and only this file by default

## 1. Authority First

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

## 2. Semantic Authority

FRZ is the semantic source of truth. SSOT objects express, project, and organize FRZ truth; they must not invent or rewrite business semantics.

FRZ content must come from human discussion, reviewed upstream documents, or accepted external-framework output. AI may structure and extract; AI must not fabricate frozen truth.

## 3. Extraction Over Generation

SRC, EPIC, FEAT, SURFACE_MAP, TECH, API, UI, PROTOTYPE, IMPL, and TESTSET are governed projections around a frozen semantic source. Downstream objects may add implementation detail only inside their explicit authority boundary.

If a proposed change alters user journeys, functional logic, state transitions, acceptance criteria, or expected test behavior, it is a semantic change and must return to FRZ revision before SSOT update.

## 4. Gate Ownership

Skills produce candidates, evidence, and handoff proposals. They do not self-promote canonical state.

Only a Gate may approve, reject, revise, or advance a governed state transition. Runners, skills, scripts, commands, and agents are carriers or participants, not promotion authority.

## 5. Evidence Before Claims

No implementation-readiness, release-readiness, freeze, settlement, or gate decision is valid without evidence references.

Execution evidence records what was done. Supervision evidence records review, semantic checks, and decision rationale. Executor and supervisor responsibilities must remain separated; an executor must not issue the final semantic pass on its own output.

## 6. Patch Reflow

Experience changes use ADR-049 grading.

- visual: Minor, retain or patch in code unless a downstream spec explicitly requires backwrite.
- interaction: Minor, settle through patch backwrite to UI, flow, or TESTSET authority as applicable.
- semantic: Major, revise FRZ, then re-extract or update SSOT through the governed chain.
- other: Minor by default, human may escalate.

Patch context relevant to target files must be injected before code edits. Patch registration after edits requires user confirmation.

## 7. Progressive Disclosure

Agents must not load the entire repository by default.

Load order:

1. Batch 0: this constitution only.
2. Batch 1: one map under `ssot/governance/maps/` selected by task type.
3. Batch 2: the smallest relevant set of ADRs or `SKILL.md` files.
4. Batch 3: contracts, checklists, agents, scripts, and schemas only when execution requires them.
5. Batch 4: evidence, runtime reports, and historical material only for verification, debugging, or audit.

Maps and registries guide disclosure. They do not override this constitution.

## 8. Repository Boundary

The project tree stores reusable, reviewable, versionable, and traceable content.

Canonical rules belong in `ssot/`. Canonical skills belong in `skills/`. Shared validators and carriers belong in `cli/` and `tools/`. Runtime residue, scratch state, temporary downloads, shell dumps, retry context, and unconfirmed drafts must not become canonical project content.

## 9. One Constitution

Claude, Codex, Cursor, local CLI commands, and any future agent adapter must reference this same constitution. Adapter files may act as bootloaders, but they must not copy, fork, or extend constitutional rules.

If an adapter, skill, registry, or document conflicts with this constitution, the constitution wins and the conflict must be recorded as a governance issue.

## 10. Broken References Block

Governance references must be closed. A required ADR, map, registry, contract, read-order file, schema, or authority reference that cannot be resolved blocks the affected workflow until repaired or explicitly marked planned with owner and reason.

Missing authority is not a warning when it affects promotion, freeze, patch routing, skill execution, or evidence validation; it is a blocker.
