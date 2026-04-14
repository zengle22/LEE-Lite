# Codebase Structure

**Analysis Date:** 2026-04-14

## Directory Layout

```
LEE-Lite-skill-first/
├── cli/                          # CLI runtime package
│   ├── __main__.py               # Entry point: `python -m cli`
│   ├── ll.py                     # Argparse root: defines all 10 command groups
│   ├── commands/                 # Subcommand handlers
│   │   ├── artifact/command.py   # artifact read/write/commit/promote/append-run-log
│   │   ├── audit/command.py      # audit scan/emit/submit
│   │   ├── evidence/command.py   # evidence bundle
│   │   ├── gate/command.py       # gate create/verify/evaluate/materialize/dispatch/release-hold/close-run
│   │   ├── job/command.py        # job claim/release-hold/run/renew-lease/complete/fail
│   │   ├── loop/command.py       # loop run-execution/resume-execution/show-status/show-backlog/recover-jobs
│   │   ├── registry/command.py   # registry resolve/verify/validate/publish/bind
│   │   ├── rollout/command.py    # rollout onboard/cutover/fallback/assess/validate/summarize
│   │   ├── skill/command.py      # skill impl-spec-test/test-exec/spec-reconcile/tech-to-impl
│   │   └── validate/command.py   # validate request/response
│   └── lib/                      # Runtime libraries
│       ├── protocol.py           # CommandContext, run_with_protocol, response builder
│       ├── errors.py             # CommandError, STATUS_SEMANTICS, EXIT_CODE_MAP
│       ├── fs.py                 # File I/O: load_json, write_json, canonical paths
│       ├── mainline_runtime.py   # Handoff submission, file locking, pending index
│       ├── skill_invoker.py      # Skill dispatcher: maps target_skill to Python function
│       ├── ready_job_dispatch.py # Downstream job builders per formal kind
│       ├── execution_runner.py   # run_job: claim->invoke->record outcome
│       ├── job_queue.py          # Queue ops: list, claim, renew, release_hold
│       ├── job_state.py          # State machine: transitions, leases, timeouts
│       ├── registry_store.py     # File-backed registry: bind, resolve, verify
│       ├── managed_gateway.py    # governed_read/governed_write with policy
│       ├── formalization.py      # Formal publication facade
│       ├── formalization_*.py    # Materialization, rendering, snapshot, owner merge
│       ├── policy.py             # Path policy enforcement
│       ├── lineage.py            # Lineage tracking
│       ├── reentry.py            # Reentry directives for revise/retry
│       ├── pilot_chain.py        # Pilot evidence validation
│       ├── rollout_state.py      # Rollout state management
│       ├── runner_entry.py       # Runner bootstrap and entry receipts
│       ├── runner_monitor.py     # Status/recovery snapshots
│       ├── test_exec_*.py        # QA test execution: artifacts, execution, reporting, runtime
│       ├── review_projection/    # Human review projection rendering
│       │   ├── renderer.py       # render_projection, build_gate_human_projection
│       │   ├── template.py       # Projection templates
│       │   ├── snapshot.py       # Authoritative SSOT snapshots
│       │   ├── focus.py          # Review focus analysis
│       │   ├── markers.py        # Projection traceability markers
│       │   ├── prompt_blocks.py  # Prompt block composition
│       │   ├── traceability.py   # Field-to-SSOT traceability
│       │   ├── regeneration.py   # Regeneration support
│       │   ├── revision_request.py
│       │   ├── risk_analyzer.py
│       │   ├── writeback.py
│       │   └── field_selector.py
│       ├── parsers/              # Input parsers (empty shell)
│       ├── reporters/            # Output reporters (empty shell)
│       ├── rules/                # Policy rules (empty shell)
│       ├── schemas/              # JSON schemas (empty shell)
│       └── utils/                # General utilities (empty shell)
├── skills/                       # Workflow skill definitions
│   ├── l3/                       # L3 governance skills (if present)
│   ├── ll-product-raw-to-src/    # RAW -> SRC normalization
│   ├── ll-product-src-to-epic/   # SRC -> EPIC derivation
│   ├── ll-product-epic-to-feat/  # EPIC -> FEAT decomposition
│   ├── ll-dev-feat-to-tech/      # FEAT -> TECH design
│   ├── ll-dev-feat-to-proto/     # FEAT -> PROTOTYPE
│   ├── ll-dev-feat-to-surface-map/ # FEAT -> SURFACE_MAP
│   ├── ll-dev-feat-to-ui/        # FEAT -> UI (deprecated)
│   ├── ll-dev-proto-to-ui/       # PROTOTYPE -> UI
│   ├── ll-dev-tech-to-impl/      # TECH -> IMPL
│   ├── ll-qa-feat-to-testset/    # FEAT -> TESTSET
│   ├── ll-qa-feat-to-apiplan/    # FEAT -> API plan
│   ├── ll-qa-e2e-spec-gen/       # E2E spec generation
│   ├── ll-qa-api-spec-gen/       # API spec generation
│   ├── ll-qa-impl-spec-test/     # IMPL spec testing
│   ├── ll-qa-test-exec-cli/      # CLI test execution
│   ├── ll-qa-test-exec-web-e2e/  # Web E2E test execution
│   ├── ll-qa-gate-evaluate/      # QA gate evaluation
│   ├── ll-qa-settlement/         # QA settlement
│   ├── ll-gate-human-orchestrator/ # Human gate orchestration
│   ├── ll-meta-skill-creator/    # Skill creation tooling
│   ├── ll-skill-install/         # Skill installation
│   ├── ll-project-init/          # Project initialization
│   └── test-exec-common/         # Shared test execution utilities
│       └── <skill>/
│           ├── SKILL.md          # Human-readable skill guide
│           ├── ll.contract.yaml  # Machine-readable skill contract
│           ├── ll.lifecycle.yaml # Lifecycle state definitions
│           ├── agents/           # Agent prompt files
│           ├── scripts/          # Python entry scripts (*_runtime.py)
│           ├── input/            # Input contracts and schemas
│           ├── output/           # Output contracts and schemas
│           ├── resources/        # Templates, checklists, examples
│           └── evidence/         # Evidence schemas and templates
├── ssot/                         # Single Source of Truth definitions
│   ├── adr/                      # Architecture Decision Records (ADR-001 through ADR-048+)
│   ├── src/                      # SRC formal objects
│   ├── epic/                     # EPIC formal objects
│   ├── feat/                     # FEAT formal objects
│   ├── tech/                     # TECH formal objects
│   ├── impl/                     # IMPL formal objects
│   ├── testset/                  # TESTSET formal objects
│   ├── ui/                       # UI formal objects
│   ├── prototype/                # PROTOTYPE formal objects
│   ├── api/                      # API formal objects
│   ├── mapping/                  # SURFACE_MAP objects
│   ├── tasks/                    # Historical TASK objects (deprecated)
│   ├── devplan/                  # Historical DEVPLAN objects (deprecated)
│   ├── testplan/                 # Historical TESTPLAN objects (deprecated)
│   ├── gate/                     # Gate configuration
│   ├── architecture/             # Architecture definitions
│   ├── release/                  # Release objects
│   └── README.md                 # Canonical object model and naming rules
├── artifacts/                    # Runtime state (git-tracked structure)
│   ├── jobs/                     # Job queue by status
│   │   ├── ready/                # Jobs awaiting execution
│   │   ├── running/              # Jobs claimed/running
│   │   ├── done/                 # Completed jobs
│   │   ├── failed/               # Failed jobs
│   │   └── waiting-human/        # Jobs held for human review
│   ├── registry/                 # File-backed artifact registry (*.json)
│   ├── active/                   # Active runtime state
│   │   ├── gates/                # Gate state (briefs, decisions, dispatch, projections)
│   │   ├── qa/                   # QA candidates and results
│   │   ├── receipts/             # Write receipts
│   │   ├── handoffs/             # Active handoff records
│   │   ├── closures/             # Run closure records
│   │   └── rollout/              # Pilot evidence and rollout state
│   ├── evidence/                 # Execution and supervision evidence
│   │   ├── execution/            # Execution attempt records
│   │   └── supervision/          # Supervision evidence
│   ├── formal/                   # Published formal SSOT copies
│   ├── lineage/                  # Lineage snapshots and index
│   ├── reports/                  # Generated reports (freeze, repair, review, validation)
│   ├── raw-input/                # Raw input storage
│   ├── tmp-skill-tests/          # Temporary skill test artifacts
│   └── agent.md                  # Agent navigation guide
├── tools/                        # CI and automation
│   └── ci/                       # CI pipeline scripts
│       ├── run_checks.py         # Main CI orchestrator
│       ├── checks_code.py        # Code quality checks
│       ├── checks_repo.py        # Repository governance checks
│       ├── checks_runtime.py     # Runtime validation
│       ├── tests.py              # Test verification
│       ├── write_changed_files.py # File change detection
│       └── manifests/            # CI manifest definitions
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── qa/                       # QA-specific tests
│   ├── fixtures/                 # Test fixtures
│   ├── golden/                   # Golden file tests
│   ├── defect/                   # Defect-related tests
│   └── test_ui_derivation_contracts.py
├── docs/                         # Human-facing documentation
│   ├── adr/                      # Local ADRs (gitkeep)
│   ├── architecture/             # Architecture docs (gitkeep)
│   ├── governance/               # Governance docs (gitkeep)
│   ├── playbooks/                # Operational playbooks (gitkeep)
│   └── repository-layout.md      # Repository layout guide
├── examples/                     # Example workflows and samples
│   ├── sample-src/               # Sample source input
│   └── sample-workflows/         # Workflow examples (src-to-epic full example)
├── .agents/                      # Agent skills and configurations
│   └── skills/                   # BMAD and custom agent skills
├── .claude/                      # Claude Code configuration
├── .local/                       # Local smoke test workspaces (git-ignored)
│   └── smoke/                    # Smoke test directories (adr001-*, adr007-*)
├── .omc/                         # Oh-My-Claude state
├── .planning/                    # Planning artifacts
│   └── codebase/                 # Codebase analysis documents
├── .project/                     # Project-specific configuration
├── .workflow/                    # Workflow run data
├── .github/                      # GitHub CI configuration
├── legacy/                       # Deprecated code (archived)
├── tmp/                          # Temporary scratch space
├── evidence/                     # Top-level evidence storage
├── scripts/                      # Top-level utility scripts
├── agent.md                      # Root agent navigation map
├── README.md                     # Project overview
├── Makefile                      # Build targets (minimal)
├── .editorconfig                 # Editor configuration
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore rules
├── .projectignore                # Project ignore rules
└── package.json                  # Node.js package (minimal)
```

## Directory Purposes

**`cli/` -- CLI Runtime:**
- Purpose: Command-line interface and governed workflow runtime
- Contains: Argparse entry, command handlers, library modules for protocol, state, dispatch, and skill invocation
- Key files: `cli/ll.py` (argparse root), `cli/lib/protocol.py` (request/response DTO), `cli/lib/skill_invoker.py` (skill dispatcher)

**`cli/commands/` -- Subcommand Handlers:**
- Purpose: One subdirectory per CLI command group, each with `command.py` and `__init__.py`
- Contains: Handler functions that receive `CommandContext` and return `(status_code, message, data, diagnostics, evidence_refs)`
- Naming: `cli/commands/{group}/command.py` with `handle(args: Namespace) -> int`

**`cli/lib/` -- Runtime Libraries:**
- Purpose: Shared logic for protocol handling, state management, gate decisions, skill dispatch
- Contains: ~60 Python modules organized by concern (protocol, errors, fs, gate, job, skill, test_exec, review_projection, formalization)
- Pattern: Flat module structure with subpackages only for review_projection

**`skills/` -- Workflow Skills:**
- Purpose: Reusable workflow transformations, each a self-contained skill directory
- Contains: Skill contracts (YAML), agent prompts, entry scripts, input/output validation
- Naming convention: `ll-{domain}-{source}-{target}/` (e.g. `ll-dev-feat-to-tech`)
- Each skill has: `SKILL.md`, `ll.contract.yaml`, `ll.lifecycle.yaml`, `scripts/`, `agents/`, `input/`, `output/`, `resources/`, `evidence/`

**`ssot/` -- Single Source of Truth:**
- Purpose: Canonical definitions of domain objects (SRC, EPIC, FEAT, TECH, IMPL, TESTSET, etc.)
- Contains: Markdown and YAML files following ADR-008 naming conventions
- Naming: `{TYPE}-{SRC-N}-{NNN}__{description}.md` (e.g. `FEAT-SRC-001-004__user-auth.md`)

**`artifacts/` -- Runtime State:**
- Purpose: File-backed state for jobs, gates, registry, evidence
- Contains: JSON files organized by lifecycle stage and status
- Pattern: Directory encodes state (e.g. `jobs/ready/` vs `jobs/running/`)

**`tools/ci/` -- CI Pipeline:**
- Purpose: Repository governance and quality checks
- Contains: Python scripts for code checks, repo checks, runtime validation

**`tests/` -- Test Suite:**
- Purpose: Unit, integration, and QA tests
- Contains: `pytest` test files organized by type

## Key File Locations

**Entry Points:**
- `cli/__main__.py`: `python -m cli` entry
- `cli/ll.py`: Argparse root, builds 10 command groups with sub-actions

**Configuration:**
- `skills/*/ll.contract.yaml`: Machine-readable skill definition
- `skills/*/ll.lifecycle.yaml`: Lifecycle state semantics
- `ssot/README.md`: Canonical object model, naming rules, deprecated objects

**Core Logic:**
- `cli/lib/protocol.py`: Request/response protocol, CommandContext DTO
- `cli/lib/mainline_runtime.py`: Handoff submission with file locking
- `cli/lib/skill_invoker.py`: Skill dispatcher mapping target_skill to function
- `cli/lib/ready_job_dispatch.py`: Downstream dispatch builders per formal kind
- `cli/lib/execution_runner.py`: Job execution flow (claim -> invoke -> record)
- `cli/lib/job_queue.py`: Queue operations (list, claim, renew, release)
- `cli/lib/formalization_materialize.py`: Formal artifact materialization

**Testing:**
- `tests/unit/`: Unit tests for protocol, runner, skills
- `tests/integration/`: Integration tests
- `tools/ci/tests.py`: CI test verification

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g. `skill_invoker.py`, `ready_job_dispatch.py`)
- Command handlers: `command.py` inside each command subdirectory
- Runtime modules: `{skill_name}_runtime.py` (e.g. `feat_to_tech_runtime.py`)
- Contract files: `ll.contract.yaml`, `ll.lifecycle.yaml`
- Documentation: `SKILL.md`, `agent.md`, `README.md`
- SSOT objects: `{TYPE}-{SRC}-{N}-{NNN}__description.md`
- Schema files: `schema.json` inside `input/` or `output/` directories
- Evidence schemas: `{type}-evidence.schema.json`

**Directories:**
- CLI commands: `cli/commands/{group}/` (lowercase)
- Skills: `skills/ll-{domain}-{source}-{target}/` (lowercase, hyphenated)
- SSOT types: `ssot/{type}/` (lowercase)
- Artifact states: `artifacts/jobs/{status}/` (lowercase, status as directory)
- Subpackages: `cli/lib/review_projection/` (only nested package in cli/lib)

## Import Organization

**CLI internal imports:**
```python
from cli.lib.errors import CommandError, ensure
from cli.lib.fs import load_json, write_json, canonical_to_path, to_canonical_path
from cli.lib.protocol import CommandContext, run_with_protocol
```

**Skill script imports:**
- Skills import from `cli.lib.*` via sys.path insertion at runtime (`skill_invoker.py`, `skill_runtime_paths.py`)
- Pattern: `_prepend_sys_path(scripts_dir)` context manager temporarily adds skill scripts to sys.path

**Protocol pattern:**
```python
def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _handler)
```

## Where to Add New Code

**New Skill:**
1. Create directory: `skills/ll-{domain}-{source}-{target}/`
2. Add skeleton: `SKILL.md`, `ll.contract.yaml`, `ll.lifecycle.yaml`
3. Add directories: `scripts/`, `agents/`, `input/`, `output/`, `resources/`, `evidence/`
4. Register in `skill_invoker.py`: Add `_invoke_{source}_{target}()` function and route in `invoke_target()`
5. Register in `cli/commands/skill/command.py`: Add action to handler dispatch
6. Register in `cli/ll.py`: Add action to `skill` subparser if new action needed

**New CLI Command Group:**
1. Create directory: `cli/commands/{group}/` with `__init__.py` and `command.py`
2. Implement `handle(args: Namespace) -> int` using `run_with_protocol()`
3. Register in `cli/ll.py`: Add `groups.add_parser("{group}")`, define sub-actions, set `handler=handle_{group}`
4. Add import at top of `cli/ll.py`

**New Gate Decision Logic:**
- Modify `_evaluate_action()` or `_dispatch_action()` in `cli/commands/gate/command.py`
- Add new decision types to `GATE_DECISIONS` set
- Add new dispatch targets to `_dispatch_target()` mapping

**New Job Queue Status:**
- Add to `JOB_STATUS_DIRS` in `cli/lib/job_state.py`
- Add to `ALLOWED_TRANSITIONS` for valid state changes
- Create corresponding directory under `artifacts/jobs/`

**New Formal Object Type:**
- Define in `ssot/README.md` canonical object model
- Add materialization logic in `cli/lib/formalization_materialize.py`
- Add dispatch builder in `cli/lib/ready_job_dispatch.py`
- Add rendering in `cli/lib/formalization_render.py`
- Add snapshot/compliance functions in `cli/lib/formalization_snapshot.py`

**New Review Projection Template:**
- Add to `cli/lib/review_projection/template.py`
- Define blocks in `cli/lib/review_projection/prompt_blocks.py`

## Special Directories

**`.local/` (git-ignored):**
- Purpose: Local smoke test workspaces and temporary execution
- Contains: `smoke/adr*/` directories with test-specific harnesses and fixtures
- Generated: Yes, by smoke test runs
- Committed: No

**`.agents/`:**
- Purpose: BMAD and custom agent skill configurations
- Contains: Agent definitions, references, scripts
- Generated: No, manually maintained

**`.planning/`:**
- Purpose: Planning and analysis artifacts
- Contains: Codebase analysis documents, plans
- Generated: By GSD map-codebase and planner agents

**`.workflow/`:**
- Purpose: Workflow run data and generated artifacts
- Contains: Run directories with intermediate outputs
- Generated: Yes, by workflow execution

**`artifacts/jobs/` (state-encoded):**
- Purpose: Job queue with status encoded by directory membership
- Subdirectories: `ready/`, `running/`, `done/`, `failed/`, `waiting-human/`, `deadletter/`
- Moving a job file between directories transitions its state
- Generated: Yes, by gate dispatch and job runner

**`artifacts/registry/`:**
- Purpose: File-backed artifact registry
- Contains: Slugified JSON records mapping artifact_ref to managed_artifact_path
- Generated: Yes, by `bind_record()` in `registry_store.py`

**`legacy/`:**
- Purpose: Archived/deprecated code
- Contains: Old implementations no longer in the active pipeline
- Committed: Yes, for historical reference

---

*Structure analysis: 2026-04-14*
