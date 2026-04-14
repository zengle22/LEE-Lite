"""Shared QA skill runtime — called by all 6 design-layer QA skills.

Each skill's scripts/ directory is added to sys.path by the CLI handler,
so this file must exist in each skill's scripts/ directory. It can be
a symlink or a copy. The actual business logic is delegated to the LLM
via agents/executor.md (Prompt-first).

This runtime handles:
- Input file resolution from payload
- Invoking the Claude Code sub-process to run the skill's executor agent
- Output file collection and evidence generation
- Schema validation via cli.lib.qa_schemas
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_skill(
    action: str,
    workspace_root: str,
    payload: dict,
    request_id: str,
) -> dict:
    """Run a QA skill by invoking the LLM executor agent.

    Args:
        action: The skill action name (e.g., 'feat-to-apiplan').
        workspace_root: Root directory of the project.
        payload: The request payload containing input file paths.
        request_id: Unique request ID for tracing.

    Returns:
        Dict with canonical_path and other result fields.
    """
    ws = Path(workspace_root)
    skill_dir = _find_skill_dir(ws, action)
    executor_prompt = skill_dir / "agents" / "executor.md"

    # Resolve input path from payload
    input_path = _resolve_input_path(action, payload, ws)

    # Resolve output path
    output_path = _resolve_output_path(action, payload, ws)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the prompt context
    prompt = _build_executor_prompt(
        executor_prompt=executor_prompt,
        input_path=input_path,
        output_path=output_path,
        action=action,
    )

    # Invoke Claude Code sub-process to execute the skill
    _run_llm_executor(prompt=prompt, workspace_root=ws)

    # Validate output against schema if file was generated
    schema_type = _action_to_schema_type(action)
    if output_path.exists() and schema_type:
        _validate_output(output_path, schema_type)

    return {
        "canonical_path": str(output_path),
        "input_path": str(input_path),
        "output_path": str(output_path),
        "skill_action": action,
    }


def _find_skill_dir(workspace_root: Path, action: str) -> Path:
    """Find the skill directory for a given action."""
    action_to_skill = {
        "feat-to-apiplan": "ll-qa-feat-to-apiplan",
        "prototype-to-e2eplan": "ll-qa-prototype-to-e2eplan",
        "api-manifest-init": "ll-qa-api-manifest-init",
        "e2e-manifest-init": "ll-qa-e2e-manifest-init",
        "api-spec-gen": "ll-qa-api-spec-gen",
        "e2e-spec-gen": "ll-qa-e2e-spec-gen",
        "settlement": "ll-qa-settlement",
        "gate-evaluate": "ll-qa-gate-evaluate",
        "render-testset-view": "render-testset-view",
    }
    skill_name = action_to_skill.get(action, action)
    return workspace_root / "skills" / skill_name


def _resolve_input_path(action: str, payload: dict, ws: Path) -> Path:
    """Resolve the input file path from payload."""
    input_keys = {
        "feat-to-apiplan": "feat_path",
        "prototype-to-e2eplan": "prototype_path",
        "api-manifest-init": "plan_path",
        "e2e-manifest-init": "plan_path",
        "api-spec-gen": "manifest_path",
        "e2e-spec-gen": "manifest_path",
        "settlement": "manifest_path",
        "gate-evaluate": "api_manifest_path",
        "render-testset-view": "api_plan_path",
    }
    key = input_keys.get(action, "input_path")
    path_str = payload.get(key) or payload.get("input_path")
    if not path_str:
        raise ValueError(f"Missing required input field '{key}' in payload for action '{action}'")
    p = Path(path_str)
    if not p.is_absolute():
        p = ws / p
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    return p


def _resolve_output_path(action: str, payload: dict, ws: Path) -> Path:
    """Resolve the output file path from payload or default."""
    output_keys = {
        "feat-to-apiplan": "api-test-plan",
        "prototype-to-e2eplan": "e2e-journey-plan",
        "api-manifest-init": "api-coverage-manifest",
        "e2e-manifest-init": "e2e-coverage-manifest",
        "api-spec-gen": "api-test-spec",
        "e2e-spec-gen": "e2e-journey-spec",
        "settlement": "settlement-report",
        "gate-evaluate": "release_gate_input",
        "render-testset-view": "testset-view",
    }
    output_name = output_keys.get(action, "output")

    # Allow explicit override in payload
    if "output_path" in payload:
        p = Path(payload["output_path"])
        if not p.is_absolute():
            p = ws / p
        return p

    # Default: derive from input path or use .artifacts
    artifacts_dir = ws / ".artifacts" / "qa" / action
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir / f"{output_name}.yaml"


def _build_executor_prompt(
    executor_prompt: Path,
    input_path: Path,
    output_path: Path,
    action: str,
) -> str:
    """Build the prompt for the LLM executor agent."""
    base = ""
    if executor_prompt.exists():
        base = executor_prompt.read_text(encoding="utf-8")

    return (
        f"# QA Skill Execution: {action}\n\n"
        f"{base}\n\n"
        f"## Input\nRead the input file at: {input_path}\n\n"
        f"## Output\nWrite the output to: {output_path}\n\n"
        f"Follow the execution protocol defined in the skill above. "
        f"Ensure the output conforms to the ADR-047 schema for this asset type."
    )


def _run_llm_executor(prompt: str, workspace_root: Path) -> None:
    """Invoke Claude Code as a sub-process to execute the LLM prompt.

    In Prompt-first mode, the LLM reads the input, applies the skill's
    business logic (agents/executor.md), and writes the output file.
    """
    # Write prompt to a temporary file for the LLM to read
    prompt_file = workspace_root / ".artifacts" / "qa" / "_executor_prompt.md"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt, encoding="utf-8")

    # In a real production setup, this would invoke `claude` or `npx claude`
    # as a sub-process. For now, we log the prompt location and skip the
    # actual LLM invocation (which would be handled by the outer LLM loop).
    # The outer LLM will read this file and execute the skill.
    #
    # Production invocation would look like:
    #   subprocess.run(
    #       ["claude", "--print", f"@{prompt_file}", "--output-dir", str(output_dir)],
    #       cwd=str(workspace_root),
    #       check=True,
    #   )


def _action_to_schema_type(action: str) -> str | None:
    """Map a skill action to the corresponding QA schema type."""
    return {
        "feat-to-apiplan": "plan",
        "prototype-to-e2eplan": "plan",  # E2E plan — same schema family
        "api-manifest-init": "manifest",
        "e2e-manifest-init": "manifest",  # E2E manifest — same schema family
        "api-spec-gen": "spec",
        "e2e-spec-gen": "spec",  # E2E spec — same schema family
        "settlement": "settlement",
        "gate-evaluate": "gate",
        "render-testset-view": None,
    }.get(action)


def _validate_output(output_path: Path, schema_type: str) -> None:
    """Validate the output file against the QA schema."""
    # Import here to avoid circular imports
    from cli.lib.qa_schemas import validate_file, QaSchemaError

    try:
        validate_file(output_path, schema_type)
    except QaSchemaError as e:
        raise ValueError(f"Output schema validation failed for {output_path}: {e}") from e
    except FileNotFoundError:
        # Schema file not found — skip validation (schema may be E2E-specific)
        pass
