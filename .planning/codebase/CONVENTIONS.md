# Coding Conventions

**Analysis Date:** 2026-04-14

## Naming Patterns

**Files:**
- snake_case for all Python files (e.g., `runner_monitor.py`, `test_cli_runner_monitor.py`)
- Test files prefixed with `test_` and located under `tests/unit/` (e.g., `tests/unit/test_cli_runner_monitor.py`)
- Internal support modules prefixed with underscore (e.g., `tests/unit/_test_exec_skill_support.py`)
- Skill scripts follow `<domain>_<action>_<phase>.py` pattern (e.g., `src_to_epic_behavior_review.py`, `feat_to_testset_gate_integration.py`)

**Functions:**
- snake_case for all functions and methods
- Private helpers prefixed with underscore: `_add_action_parser`, `_decision_type`, `_utc_now`, `_gate_key`
- Handler functions use descriptive verb+noun: `handle_artifact`, `run_with_protocol`, `execute_test_exec_skill`

**Variables:**
- snake_case throughout
- Reference fields consistently suffixed with `_ref` (e.g., `request_path`, `response_path`, `candidate_ref`, `gate_decision_ref`)

**Types:**
- PascalCase for classes: `CommandError`, `CommandContext`, `CliRunnerMonitorTest`
- Dataclasses used for structured data: `CommandError`, `CommandContext`, `Violation`, `ExecutionRunnerStartRequest`
- `frozen=True` used on immutable dataclasses: `ExecutionRunnerStartRequest`, `ExecutionRunnerRunRef`, `RunnerEntryReceipt`

**Modules/Packages:**
- snake_case directories: `cli/lib/`, `cli/commands/`, `tests/unit/`, `skills/ll-product-src-to-epic/`
- Skill package naming: `ll-<domain>-<action>` (e.g., `ll-product-src-to-epic`, `ll-qa-feat-to-testset`)

## Code Style

**Formatting:**
- `.editorconfig` present at root with 2-space indentation, LF line endings, UTF-8 charset, trailing newline, trailing whitespace trimming
- No automated formatter (black/ruff) detected in the codebase; style enforced through CI governance checks

**Linting:**
- No `.eslintrc`, `ruff.toml`, or equivalent linter config in the project root
- Code quality enforced via CI checks in `tools/ci/`:
  - `tools/ci/checks_code.py` -- file size governance (max 500 lines per file, max 80 lines per function)
  - `tools/ci/checks_repo.py` -- repository hygiene checks
  - `tools/ci/checks_runtime.py` -- CLI surface governance, skill governance, cross-domain compatibility
  - Violation system: `@dataclass Violation(check, code, path, message)` defined in `tools/ci/common.py`

## Import Organization

**Order (observed pattern in `cli/lib/` and `cli/commands/`):**
1. `from __future__ import annotations` (always first, in every file)
2. Standard library imports (grouped: `argparse`, `datetime`, `json`, `pathlib`, `typing`, `subprocess`, `unittest`, `tempfile`, `ast`, `dataclasses`, `fnmatch`)
3. Third-party imports (`import yaml`, `import pytest`)
4. Local imports relative to project root (e.g., `from cli.lib.errors import CommandError, ensure`)

**Import style:**
- Absolute imports used throughout: `from cli.lib.errors import CommandError` not `from ..errors import CommandError`
- Grouped imports from same module on single line: `from cli.lib.errors import CommandError, EXIT_CODE_MAP, STATUS_SEMANTICS, ensure`
- No path aliases (no `@` imports or `sys.path` manipulation in production code; limited `sys.path.insert` in test harness and skill dispatch)

## Error Handling

**Strategy: Structured exception with status codes and explicit propagation.**

All errors flow through a centralized taxonomy in `cli/lib/errors.py`:

```python
@dataclass
class CommandError(Exception):
    """Structured error raised by command handlers."""
    status_code: str       # e.g., "INVALID_REQUEST", "PRECONDITION_FAILED"
    message: str
    diagnostics: list[str] = field(default_factory=list)
    data: dict[str, object] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)

    @property
    def result_status(self) -> str:
        return STATUS_SEMANTICS[self.status_code]

    @property
    def exit_code(self) -> int:
        return EXIT_CODE_MAP[self.status_code]
```

**Status codes and exit codes (from `cli/lib/errors.py`):**
- `OK` -> exit 0
- `INVALID_REQUEST` -> exit 2
- `POLICY_DENIED` -> exit 3
- `ELIGIBILITY_DENIED` -> exit 3
- `PRECONDITION_FAILED` -> exit 4
- `PROVISIONAL_SLICE_DISABLED` -> exit 4
- `INVARIANT_VIOLATION` -> exit 5
- `INTERNAL_ERROR` -> exit 10
- `REGISTRY_MISS` -> exit 10

**Guard helper pattern:**
```python
def ensure(condition: bool, status_code: str, message: str, diagnostics: list[str] | None = None) -> None:
    if not condition:
        raise CommandError(status_code, message, diagnostics or [])
```

Used extensively for validation:
```python
ensure(field in request, "INVALID_REQUEST", f"missing request field: {field}")
ensure(request.get("api_version") == "v1", "INVALID_REQUEST", "unsupported api_version")
```

**Protocol-level error capture:**
`cli/lib/protocol.py` `run_with_protocol` catches `CommandError` and converts to structured JSON response:
```python
def run_with_protocol(args: Namespace, handler) -> int:
    ctx = load_context(args)
    try:
        status_code, message, data, diagnostics, evidence_refs = handler(ctx)
        response = build_response(ctx, status_code, message, data, diagnostics, evidence_refs)
    except CommandError as exc:
        response = build_response(ctx, exc.status_code, exc.message, exc.data, exc.diagnostics, exc.evidence_refs)
    return persist_response(ctx, response)
```

**Validation helpers:**
`parse_int` in `cli/lib/errors.py` handles type-safe integer parsing with chained exception:
```python
def parse_int(value: object, *, field_name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise CommandError("INVALID_REQUEST", f"{field_name} must be an integer")
    # ...
```

**Filesystem error wrapping:**
`cli/lib/fs.py` wraps `FileNotFoundError` and `json.JSONDecodeError` into `CommandError`:
```python
def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CommandError("INVALID_REQUEST", f"request file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CommandError("INVALID_REQUEST", f"invalid json file: {path}", [str(exc)]) from exc
```

## Logging

**Framework: None.** The codebase does not use `logging` module. No `import logging` or `logger =` detected in any source file.

**Output patterns:**
- CLI commands communicate via JSON file protocol (request/response files)
- CI tools use `print()` to stdout/stderr for debugging: `tools/ci/common.py` `run_pytest()` prints pytest output to CI logs
- No structured logging, no log levels, no log rotation
- Observability is file-based: artifacts written to `artifacts/` directory with canonical path references

## Comments

**When to Comment:**
- Module-level docstrings present on most files: `"""Error taxonomy for the CLI runtime."""`, `"""Protocol handling for structured file requests and responses."""`, `"""Filesystem helpers for the CLI runtime."""`
- Minimal inline comments; code is self-documenting through explicit naming
- No `TODO`, `FIXME`, `HACK`, or `XXX` markers detected in production code

**Docstrings:**
- Module docstrings: one-line descriptions at top of each file
- Function docstrings: not consistently present; most functions rely on descriptive names
- Class docstrings: present on dataclasses: `"""Structured error raised by command handlers."""`

## Function Design

**Size:**
- Governed by CI check: max 80 lines per function (`tools/ci/checks_code.py` `MAX_FUNCTION_LINES = 80`)
- Max 500 lines per file (`MAX_FILE_LINES = 500`)
- Most functions are focused and small; gate dispatch handler (`cli/commands/gate/command.py`) is the largest at ~790 lines due to many action handlers

**Parameters:**
- Explicit keyword arguments preferred for complex functions
- `CommandContext` dataclass bundles related state for handlers
- `payload` dict passed through skill handlers with field validation at entry points

**Return Values:**
- Command handlers return 4-tuple: `(status_code, message, data_dict, diagnostics, evidence_refs)`
- Exit codes returned as `int` from `main()` functions
- `run_with_protocol` returns `int` exit code

## Module Design

**Exports:**
- Each `cli/commands/<name>/` package has `__init__.py` (minimal) and `command.py` (handler logic)
- `cli/commands/<name>/command.py` exports `handle(args: Namespace) -> int`
- `cli/lib/` modules export individual functions and classes; no `__all__` declarations

**Barrel Files:**
- No barrel files detected; each module imports directly from source
- `__init__.py` files are minimal, mostly docstrings

**Command Pattern:**
- CLI entry point: `cli/ll.py` `main(argv)` -> builds argparse parser -> dispatches to handler
- Each command group (artifact, registry, audit, gate, loop, job, rollout, skill, validate, evidence) has its own handler
- All handlers go through `run_with_protocol` for structured request/response lifecycle

**Handler Dispatch:**
- Action dispatch via dictionary mapping:
```python
def _gate_handler(ctx: CommandContext):
    handlers = {
        "create": _package_action,
        "evaluate": _evaluate_action,
        "materialize": _materialize_action,
        "dispatch": _dispatch_action,
        "release-hold": _release_hold_action,
        "close-run": _close_action,
    }
    handlers.update(collaboration_handlers())
    return handlers[ctx.action](ctx)
```

## Type Annotations

**Coverage:**
- `from __future__ import annotations` present in every `.py` file in `cli/` and `tools/ci/`
- All function signatures use type annotations: `def handle(args: Namespace) -> int:`
- Return types annotated on all public functions
- `typing` module imports: `Callable`, `Any`, `annotations`, `Namespace`

## Data Protocol

**Request/Response format:**
- JSON file-based protocol between CLI commands
- Request envelope: `{"api_version": "v1", "command": "<group>.<action>", "request_id": "...", "workspace_root": "...", "actor_ref": "...", "trace": {...}, "payload": {...}}`
- Response envelope: `{"api_version": "v1", "command": "...", "request_id": "...", "result_status": "...", "status_code": "...", "exit_code": N, "message": "...", "data": {...}, "diagnostics": [...], "evidence_refs": [...]}`
- All paths stored as POSIX-style canonical paths (forward slashes)

---

*Convention analysis: 2026-04-14*
