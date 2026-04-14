# Architecture

**Analysis Date:** 2026-04-14

## Pattern Overview

**Overall:** File-Driven Event Loop with Gated State Machine

This is a Python CLI-first governed workflow runtime. The system orchestrates a multi-stage product development pipeline (RAW -> SRC -> EPIC -> FEAT -> TECH/PROTOTYPE/TESTSET -> IMPL) using file-based artifacts, explicit gate decisions, and a job runner loop. There is no persistent database -- all state lives in JSON/YAML files under the workspace tree.

**Key Characteristics:**
- **File-first state machine**: Jobs, gates, decisions, and artifacts are all JSON files on disk. Transitions are performed by moving/rewriting files.
- **Gated progression**: Every stage transition passes through a gate (create package -> evaluate -> materialize -> dispatch) that can approve, reject, revise, retry, or hold for human review.
- **Skill-based execution**: Each workflow step is a "skill" -- a self-contained Python module with defined input/output contracts, validation, and evidence requirements.
- **Runner loop dispatch**: A CLI command (`loop run-execution`) polls ready jobs from `artifacts/jobs/ready/`, claims them, runs the target skill, and records the outcome.
- **Immutable lineage**: Artifacts carry trace metadata, registry records track provenance, and handoff files preserve the chain of custody between stages.

## Layers

**CLI Runtime (`cli/`):**
- Purpose: Command-line interface, protocol handling, runtime orchestration
- Location: `cli/ll.py`, `cli/commands/`, `cli/lib/`
- Contains: Argparse-based CLI, command handlers, protocol DTOs, filesystem utilities, gate logic, job queue management, skill invocation
- Depends on: Python stdlib + PyYAML
- Used by: External runners, CI pipeline, human operators

**Skills (`skills/`):**
- Purpose: Reusable workflow skills that transform artifacts from one stage to the next
- Location: `skills/ll-{domain}-{source}-{target}/` (e.g. `skills/ll-dev-feat-to-tech/`)
- Contains: Entry scripts, agent prompts, input/output contracts, validation scripts, lifecycle definitions
- Depends on: CLI lib modules (invoked via `sys.path` insertion)
- Used by: `skill_invoker.py` dispatch, CLI `skill` command group

**SSOT (`ssot/`):**
- Purpose: Single Source of Truth -- canonical definitions of domain objects
- Location: `ssot/{src,epic,feat,tech,impl,testset,ui,prototype,api,mapping,adr}/`
- Contains: Markdown and YAML definitions of formal objects (SRC, EPIC, FEAT, TECH, IMPL, etc.)
- Depends on: Nothing (authoritative source)
- Used by: Formalization layer, review projections, gate decisions

**Artifacts (`artifacts/`):**
- Purpose: Runtime state -- jobs, gates, registry, evidence, and active handoffs
- Location: `artifacts/{jobs,registry,active,evidence,formal,reports,lineage}/`
- Contains: JSON/YAML runtime files organized by lifecycle stage
- Depends on: CLI writes, skills produce
- Used by: All layers

**Tools (`tools/`):**
- Purpose: CI checks and repository governance
- Location: `tools/ci/`
- Contains: Repo checks, code checks, runtime checks, test verification
- Depends on: CLI lib modules
- Used by: GitHub Actions, pre-commit

## Data Flow

### Main Pipeline (Product Lifecycle)

```
RAW input -> src_to_epic -> EPIC -> epic_to_feat -> FEAT
                                                    |
                       +----------------------------+----------------------------+
                       |                            |                            |
                  feat_to_tech                 feat_to_proto                feat_to_testset
                       |                            |                            |
                     TECH                    proto_to_ui                    TESTSET
                       |                            |                            |
                  tech_to_impl                    UI PROTOTYPE            test_exec_cli/web_e2e
                       |                                                       |
                     IMPL                                                 test results
```

1. **RAW ingestion**: Raw input is processed by `ll-product-src-to-epic` to produce SRC formal objects
2. **SRC -> EPIC**: `workflow.product.src_to_epic` skill generates epic from source
3. **EPIC -> FEAT**: `workflow.product.epic_to_feat` skill decomposes epic into features
4. **FEAT parallel dispatch**: Each FEAT triggers three downstream skills in parallel:
   - `workflow.dev.feat_to_tech` (TECH design)
   - `workflow.dev.feat_to_proto` (PROTOTYPE)
   - `workflow.qa.feat_to_testset` (TESTSET)
5. **TECH -> IMPL**: `workflow.dev.tech_to_impl` generates implementation spec
6. **PROTOTYPE -> UI**: `workflow.dev.proto_to_ui` generates UI spec
7. **TESTSET -> Execution**: `skill.qa.test_exec_cli` or `skill.qa.test_exec_web_e2e` runs tests

### Gate Decision Flow

```
Skill produces candidate
  -> submit_handoff (mainline_runtime.py) writes to artifacts/active/gates/pending/
  -> gate evaluate: audit findings + target matrix -> decision (approve/revise/retry/reject/handoff)
  -> if approve: materialize_formal -> write to ssot/{type}/ directory
  -> dispatch: build downstream handoff + job files
  -> job sits in artifacts/jobs/ready/ (or artifacts/jobs/waiting-human/ if hold)
```

### Execution Loop Flow

```
loop run-execution:
  -> list_ready_jobs (job_queue.py) -> artifacts/jobs/ready/*.json
  -> claim_job -> transition status "ready" -> "claimed"
  -> run_job (execution_runner.py) -> invoke_target (skill_invoker.py)
  -> skill produces output -> write attempt record
  -> if ok: complete_job -> "done"
  -> if fail: fail_job -> "failed"
```

### State Machine (Job Lifecycle)

```
ready -> claimed -> running -> done (terminal)
                          -> failed -> ready (retry)
                          -> waiting-human -> ready (released)
                          -> deadletter (terminal)
```

Defined in `cli/lib/job_state.py`: `ALLOWED_TRANSITIONS`. Lease-based timeout prevents abandoned running jobs.

**State Management:**
- All state is file-backed. No in-memory persistence across CLI invocations.
- Job status is encoded by directory membership: `artifacts/jobs/ready/`, `running/`, `done/`, `failed/`, `waiting-human/`, `deadletter/`
- File locking via `fcntl` (POSIX) or `msvcrt` (Windows) for concurrent access safety (`mainline_runtime.py`)
- Registry records in `artifacts/registry/` provide lookup by artifact_ref

## Key Abstractions

**CommandContext (`cli/lib/protocol.py`):**
- Purpose: DTO carrying request/response paths, workspace root, parsed JSON request
- Examples: `cli/lib/protocol.py` lines 14-23
- Pattern: Frozen dataclass with validated properties (`payload`, `trace`)

**CommandError (`cli/lib/errors.py`):**
- Purpose: Structured exception with status code, message, diagnostics, data, evidence_refs
- Examples: `cli/lib/errors.py` lines 33-50
- Pattern: Exception subclass with semantic status mapping (`STATUS_SEMANTICS`, `EXIT_CODE_MAP`)

**Skill Contract (`skills/*/ll.contract.yaml`):**
- Purpose: Declarative skill definition with workflow_key, roles, runtime mode, input/output validation, lifecycle states
- Examples: `skills/ll-dev-feat-to-tech/ll.contract.yaml`
- Pattern: YAML with structured sections: `authority`, `roles`, `runtime`, `input`, `output`, `validation`, `evidence`, `lifecycle`, `gate`

**Handoff (`cli/lib/mainline_runtime.py`):**
- Purpose: File-based handoff from skill producer to gate consumer
- Examples: `submit_handoff()` writes to `artifacts/active/gates/handoffs/{key}.json`
- Pattern: Idempotent submission with SHA-256 digest dedup, file locking

**Formal Record (`cli/lib/registry_store.py`):**
- Purpose: Registry binding of artifact_ref to managed_artifact_path with status and lineage
- Examples: `bind_record()`, `resolve_registry_record()`
- Pattern: Slugified filename in `artifacts/registry/`, lookup by artifact_ref or managed_artifact_ref

**Downstream Dispatch (`cli/lib/ready_job_dispatch.py`):**
- Purpose: After gate approval, build handoff files and job queue entries for downstream skills
- Examples: `build_feat_downstream_dispatch()`, `build_src_downstream_dispatch()`
- Pattern: Per-formal-kind builder function, emits both handoff and job files, evaluates spec reconcile holds

**Review Projection (`cli/lib/review_projection/`):**
- Purpose: Generate human-readable review summaries from Machine SSOT data
- Examples: `build_gate_human_projection()` in `renderer.py`
- Pattern: Template-based block composition with traceability markers and field focus analysis

## Entry Points

**CLI Entrypoint (`cli/ll.py`):**
- Location: `cli/ll.py` + `cli/__main__.py`
- Triggers: `python -m cli` or `python cli/ll.py`
- Responsibilities: Argparse parsing, subcommand routing to handlers, protocol enforcement

**Command Groups (10 subcommands):**
- `artifact`: read/write/commit/promote/append-run-log (managed gateway operations)
- `registry`: resolve-formal-ref/verify-eligibility/validate-admission/publish-formal/bind-record
- `audit`: scan-workspace/emit-finding-bundle/submit-pilot-evidence
- `gate`: submit-handoff/show-pending/decide/create/verify/evaluate/materialize/dispatch/release-hold/close-run
- `loop`: run-execution/resume-execution/show-status/show-backlog/recover-jobs
- `job`: claim/release-hold/run/renew-lease/complete/fail
- `rollout`: onboard-skill/cutover-wave/fallback-wave/assess-skill/validate-pilot/summarize-readiness
- `skill`: impl-spec-test/test-exec-web-e2e/test-exec-cli/gate-human-orchestrator/failure-capture/spec-reconcile/tech-to-impl
- `validate`: request/response
- `evidence`: bundle

**Skill Scripts (`skills/*/scripts/`):**
- Location: `skills/ll-{domain}-{source}-{target}/scripts/{workflow}_runtime.py`
- Triggers: Invoked via `skill_invoker.py` sys.path insertion
- Responsibilities: Execute the actual workflow transformation

## Error Handling

**Strategy:** Structured error codes with semantic exit codes, propagated through protocol responses

**Patterns:**
- `ensure(condition, status_code, message)` raises `CommandError` -- used pervasively for preconditions
- Command handlers return `(status_code, message, data, diagnostics, evidence_refs)` tuples
- `run_with_protocol()` catches `CommandError`, builds response, persists to JSON
- Status codes map to semantics: `OK` -> success, `INVALID_REQUEST` -> fatal, `PRECONDITION_FAILED` -> retryable, etc.
- No exception bubbling -- all errors are caught at the protocol layer and serialized

## Cross-Cutting Concerns

**Logging:** No dedicated logging framework. Evidence files (JSON) serve as the audit trail. All operations write receipt, attempt, and outcome records to `artifacts/`.

**Validation:** Multi-layer validation at skill boundaries:
- Structural: JSON schema validation via `validate_input`/`validate_output` scripts
- Semantic: Checklist-based validation via `semantic-checklist.md` files
- Gate-level: Precondition checks before materialization (`_ensure_raw_to_src_gate_ready`, `_ensure_proto_to_ui_gate_ready`)
- Spec reconcile: ADR-044 automated spec consistency checks that can hold downstream dispatch

**Authentication:** Actor identity via `actor_ref` field in requests. No cryptographic auth -- file-based trust model.

**Canonical Paths:** All file references use forward-slash canonical paths relative to workspace root (`to_canonical_path`, `canonical_to_path` in `cli/lib/fs.py`).

**Evidence Chain:** Every operation produces evidence files with `trace` metadata containing `run_ref`, linking the entire execution history.

---

*Architecture analysis: 2026-04-14*
