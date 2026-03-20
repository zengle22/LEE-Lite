#!/usr/bin/env python3
"""
Initialize a governed LEE Lite workflow skill.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MAX_SKILL_NAME_LENGTH = 64
REQUIRED_LIFECYCLE_STATES = [
    "drafted",
    "structurally_validated",
    "semantically_reviewed",
    "revised",
    "accepted",
    "frozen",
    "rejected",
]


def normalize_skill_name(raw_name: str) -> str:
    normalized = raw_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def format_title(skill_name: str) -> str:
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def format_display_name(skill_name: str) -> str:
    return " ".join(word.upper() if word in {"ll", "lee"} else word.capitalize() for word in skill_name.split("-"))


def generate_short_description(display_name: str) -> str:
    text = f"Governed skill for {display_name}"
    if len(text) < 25:
        text = f"Governed workflow skill for {display_name}"
    if len(text) > 64:
        text = f"{display_name} workflow helper"
    return text[:64].rstrip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_executable(path: Path) -> None:
    try:
        path.chmod(0o755)
    except OSError:
        pass


def skill_description(input_artifact: str, output_artifact: str, workflow_key: str) -> str:
    return (
        f"Governed LEE Lite workflow skill for transforming a frozen {input_artifact.upper()} "
        f"artifact into a {output_artifact.upper()} artifact with contracts, structural validation, "
        f"semantic supervision, evidence capture, and freeze gates. Use when Codex should run or "
        f"maintain the {workflow_key} workflow instead of drafting outputs without governance."
    )


def render_skill_md(skill_name: str, title: str, description: str) -> str:
    return f"""---
name: {skill_name}
description: {description}
---

# {title}

This skill wraps a LEE Lite workflow in a standard skill shell plus a governance pack. Do not bypass contracts, evidence, or freeze rules.

## Run Protocol

1. Read `ll.contract.yaml`, then load the input and output contracts.
2. Validate the input structurally before drafting or modifying output.
3. Produce or revise the output using `output/template.md` and the output contract.
4. Record execution evidence before handing the result to the supervisor.
5. Let the supervisor review the output semantically using the semantic checklists and supervision evidence.
6. Freeze only after all gate conditions in `ll.contract.yaml` pass.

## Role Split

- Executor responsibilities live in `agents/executor.md`.
- Supervisor responsibilities live in `agents/supervisor.md`.
- The executor must not issue the final semantic pass on its own output.

## Files To Read

- `ll.contract.yaml` for the governance contract.
- `ll.lifecycle.yaml` for allowed states.
- `input/` and `output/` for contracts, schemas, templates, and semantic checklists.
- `evidence/` for expected evidence shapes.
- `resources/` for examples, glossary, and reusable checklists.

## Default Scripts

- `scripts/validate_input.sh`
- `scripts/validate_output.sh`
- `scripts/collect_evidence.sh`
- `scripts/freeze_guard.sh`

Replace the placeholder commands in those scripts with project-specific `lee` invocations when integrating the workflow into a real repository.
"""


def render_openai_yaml(skill_name: str) -> str:
    display_name = format_display_name(skill_name)
    short_description = generate_short_description(display_name)
    default_prompt = f"Use ${skill_name} to run the governed {skill_name} workflow."
    return "\n".join(
        [
            "interface:",
            f"  display_name: {yaml_quote(display_name)}",
            f"  short_description: {yaml_quote(short_description)}",
            f"  default_prompt: {yaml_quote(default_prompt)}",
            "",
        ]
    )


def render_ll_contract(skill_name: str, input_artifact: str, output_artifact: str, workflow_key: str, lee_command: str, max_revision_rounds: int) -> str:
    return f"""skill_id: {skill_name}
skill_type: workflow
version: 0.1.0
workflow_key: {workflow_key}

roles:
  executor:
    required: true
    evidence_required: true
    prompt_file: agents/executor.md
  supervisor:
    required: true
    evidence_required: true
    prompt_file: agents/supervisor.md

input:
  artifact_type: {input_artifact}
  contract_file: input/contract.yaml
  schema_file: input/schema.json
  structural_validation_required: true
  semantic_validation_required: true

output:
  artifact_type: {output_artifact}
  contract_file: output/contract.yaml
  schema_file: output/schema.json
  template_file: output/template.md
  structural_validation_required: true
  semantic_validation_required: true

validation:
  structural:
    - "{lee_command} validate schema $INPUT"
    - "{lee_command} validate trace $INPUT"
    - "{lee_command} validate freeze $INPUT"
    - "{lee_command} validate schema $OUTPUT"
    - "{lee_command} validate trace $OUTPUT"
    - "{lee_command} validate naming $OUTPUT"
  semantic:
    input_checklist: input/semantic-checklist.md
    output_checklist: output/semantic-checklist.md

evidence:
  execution_schema: evidence/execution-evidence.schema.json
  supervision_schema: evidence/supervision-evidence.schema.json
  report_template: evidence/report.template.md

lifecycle:
  definition_file: ll.lifecycle.yaml
  max_revision_rounds: {max_revision_rounds}

gate:
  freeze_requires:
    - input_structural_pass
    - input_semantic_pass
    - output_structural_pass
    - output_semantic_pass
    - execution_evidence_present
    - supervision_evidence_present
  reject_when:
    - authoritative_input_missing
    - scope_drift_unresolved
    - required_evidence_missing
"""


def render_lifecycle(max_revision_rounds: int) -> str:
    states_yaml = "\n".join(f"  - {state}" for state in REQUIRED_LIFECYCLE_STATES)
    return f"""version: 0.1.0
states:
{states_yaml}

transitions:
  drafted:
    - structurally_validated
    - rejected
  structurally_validated:
    - semantically_reviewed
    - revised
    - rejected
  semantically_reviewed:
    - accepted
    - revised
    - rejected
  revised:
    - structurally_validated
    - rejected
  accepted:
    - frozen
    - revised
  frozen: []
  rejected: []

limits:
  max_revision_rounds: {max_revision_rounds}
"""


def render_input_contract(input_artifact: str) -> str:
    return f"""artifact_type: {input_artifact}
schema_version: 0.1.0
accepted_states:
  - frozen
required_fields:
  - id
  - title
  - summary
  - scope
  - constraints
required_refs:
  - source_freeze_ref
structural_checks:
  - schema
  - trace
  - freeze
forbidden_states:
  - draft
  - ambiguous
forbidden_changes:
  - unresolved_source_conflicts
notes:
  - Replace required fields and refs with workflow-specific requirements.
"""


def render_output_contract(input_artifact: str, output_artifact: str) -> str:
    return f"""artifact_type: {output_artifact}
schema_version: 0.1.0
required_source_refs:
  - "{input_artifact.upper()}-*"
required_sections:
  - Overview
  - Scope
  - Non-Goals
  - Constraints
  - Traceability
structural_checks:
  - schema
  - trace
  - naming
semantic_gate:
  required: true
forbidden_content:
  - implementation-level task breakdown
  - unstated new requirements
notes:
  - Replace section names and source ref patterns with workflow-specific values.
"""


def render_input_checklist(input_artifact: str) -> str:
    return f"""# Input Semantic Checklist

Review the {input_artifact.upper()} input for semantic readiness.

- Is the input frozen and authoritative enough for downstream decomposition?
- Are critical constraints explicit rather than implied?
- Does the input avoid unresolved ambiguity that would force unsafe inference?
- Do referenced upstream sources agree with each other?
- Would accepting this input create a parallel truth or bypass a more authoritative source?
"""


def render_output_checklist(input_artifact: str, output_artifact: str) -> str:
    return f"""# Output Semantic Checklist

Review the {output_artifact.upper()} output against the upstream {input_artifact.upper()} source.

- Is the output faithful to the authoritative input?
- Does it avoid introducing new scope not present in the source?
- Does it stay at the correct artifact layer?
- Does it preserve critical constraints and non-goals?
- Would a downstream reader treat this output as the single governed truth for this layer?
"""


def render_output_template(output_artifact: str, input_artifact: str) -> str:
    source_label = input_artifact.upper()
    return f"""---
artifact_type: {output_artifact}
status: drafted
schema_version: 0.1.0
source_refs:
  - {source_label}-TODO
---

# {{TITLE}}

## Overview

[Summarize the artifact purpose.]

## Scope

[Define what is in scope.]

## Non-Goals

[Define what is explicitly out of scope.]

## Constraints

[List inherited and workflow-specific constraints.]

## Traceability

[Map output sections back to authoritative {source_label} refs.]
"""


def render_json_schema(title: str, artifact_type: str, source_ref_required: bool) -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "required": ["artifact_type", "status", "schema_version"],
        "properties": {
            "artifact_type": {"type": "string", "const": artifact_type},
            "status": {"type": "string"},
            "schema_version": {"type": "string"},
        },
        "additionalProperties": True,
    }
    if source_ref_required:
        schema["required"].append("source_refs")
        schema["properties"]["source_refs"] = {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        }
    return json.dumps(schema, indent=2) + "\n"


def render_execution_schema(skill_name: str) -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{skill_name} execution evidence",
        "type": "object",
        "required": [
            "skill_id",
            "run_id",
            "role",
            "inputs",
            "outputs",
            "commands_run",
            "structural_results",
            "key_decisions",
            "uncertainties",
        ],
        "properties": {
            "skill_id": {"type": "string"},
            "run_id": {"type": "string"},
            "role": {"type": "string", "const": "executor"},
            "inputs": {"type": "array", "items": {"type": "string"}},
            "outputs": {"type": "array", "items": {"type": "string"}},
            "commands_run": {"type": "array", "items": {"type": "string"}},
            "structural_results": {"type": "object"},
            "key_decisions": {"type": "array", "items": {"type": "string"}},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    }
    return json.dumps(schema, indent=2) + "\n"


def render_supervision_schema(skill_name: str) -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{skill_name} supervision evidence",
        "type": "object",
        "required": [
            "skill_id",
            "run_id",
            "role",
            "reviewed_inputs",
            "reviewed_outputs",
            "semantic_findings",
            "decision",
            "reason",
        ],
        "properties": {
            "skill_id": {"type": "string"},
            "run_id": {"type": "string"},
            "role": {"type": "string", "const": "supervisor"},
            "reviewed_inputs": {"type": "array", "items": {"type": "string"}},
            "reviewed_outputs": {"type": "array", "items": {"type": "string"}},
            "semantic_findings": {"type": "array", "items": {"type": "object"}},
            "decision": {"type": "string", "enum": ["pass", "revise", "reject"]},
            "reason": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return json.dumps(schema, indent=2) + "\n"


def render_report_template(skill_name: str) -> str:
    return f"""# {skill_name} Review Report

## Run Summary

- run_id:
- workflow:
- input_ref:
- output_ref:

## Structural Validation

- input:
- output:

## Execution Evidence

- commands:
- decisions:
- uncertainties:

## Supervision Evidence

- findings:
- decision:
- reason:

## Freeze Decision

- status:
- gate_results:
"""


def render_executor_prompt(skill_name: str) -> str:
    return f"""# Executor

You are the executor for `{skill_name}`.

## Responsibilities

1. Read the input and output contracts before editing any artifact.
2. Run structural checks first.
3. Draft or revise the output without bypassing the source contract.
4. Record execution evidence for all significant commands, decisions, and uncertainties.
5. Hand the result to the supervisor after structural validation passes.

## Forbidden Actions

- issuing the final semantic pass
- freezing output
- hiding uncertainty
- adding scope not justified by the source
"""


def render_supervisor_prompt(skill_name: str) -> str:
    return f"""# Supervisor

You are the supervisor for `{skill_name}`.

## Responsibilities

1. Review the generated output, the input source, and the execution evidence.
2. Run semantic review using the semantic checklists.
3. Decide `pass`, `revise`, or `reject`.
4. Record supervision evidence with concrete findings and a reasoned decision.
5. Allow freeze only when the full gate is satisfied.

## Forbidden Actions

- silent approval without evidence
- rewriting the artifact without recording a review decision
- bypassing unresolved scope drift
- overriding contract failures
"""


def render_glossary() -> str:
    return """# Glossary

- contract: explicit input or output requirements for an artifact.
- structural validation: deterministic checks such as schema, naming, refs, or file presence.
- semantic validation: review of fidelity, scope, and artifact responsibility.
- execution evidence: executor record of commands, decisions, and uncertainties.
- supervision evidence: supervisor record of findings and disposition.
- freeze gate: final condition set that must pass before an artifact is treated as governed truth.
"""


def render_input_example(input_artifact: str) -> str:
    return f"""---
artifact_type: {input_artifact}
status: frozen
schema_version: 0.1.0
source_freeze_ref: {input_artifact.upper()}-001
---

# Example {input_artifact.upper()}

## Summary

Example upstream artifact.

## Scope

Example scope.

## Constraints

Example constraints.
"""


def render_output_example(output_artifact: str, input_artifact: str) -> str:
    return f"""---
artifact_type: {output_artifact}
status: accepted
schema_version: 0.1.0
source_refs:
  - {input_artifact.upper()}-001
---

# Example {output_artifact.upper()}

## Overview

Example governed output.

## Scope

Example output scope.

## Non-Goals

Example non-goals.

## Constraints

Example inherited constraints.

## Traceability

Map the output back to the source refs.
"""


def render_authoring_checklist() -> str:
    return """# Authoring Checklist

- Define the workflow boundary in plain language.
- Confirm input and output artifact types.
- Confirm authoritative source and freeze expectations.
- Fill input and output contracts with explicit required fields and refs.
- Replace placeholder `lee` commands with real project commands.
- Update semantic checklists with workflow-specific risks.
- Keep executor and supervisor instructions separate.
"""


def render_review_checklist() -> str:
    return """# Review Checklist

- Does the skill keep a standard `SKILL.md` shell?
- Does `ll.contract.yaml` define roles, validations, evidence, lifecycle, and freeze gates?
- Are structural and semantic validations separate?
- Are execution and supervision evidence schemas present?
- Are role prompts split between executor and supervisor?
- Do placeholder scripts exist for input validation, output validation, evidence, and freeze guard?
"""


def render_validate_script(kind: str) -> str:
    contract_path = f"{kind}/contract.yaml"
    schema_path = f"{kind}/schema.json"
    return f"""#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_{kind}.sh <artifact-path>"
  exit 1
fi

ARTIFACT_PATH="$1"

if [ ! -f "$ARTIFACT_PATH" ]; then
  echo "Artifact not found: $ARTIFACT_PATH"
  exit 1
fi

echo "Validate $ARTIFACT_PATH against {contract_path} and {schema_path}"
echo "Replace this placeholder with project-specific lee validation commands."
"""


def render_collect_evidence_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

echo "Collect execution and supervision evidence for this workflow run."
echo "Replace this placeholder with project-specific evidence collection logic."
"""


def render_freeze_guard_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

echo "Check freeze gate conditions from ll.contract.yaml before freezing."
echo "Replace this placeholder with project-specific freeze guard logic."
"""


def initialize_skill(skill_name: str, output_dir: Path, input_artifact: str, output_artifact: str, workflow_key: str, lee_command: str, max_revision_rounds: int) -> Path:
    skill_dir = output_dir / skill_name
    if skill_dir.exists():
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")

    title = format_title(skill_name)
    description = skill_description(input_artifact, output_artifact, workflow_key)
    skill_dir.mkdir(parents=True, exist_ok=False)

    write_text(skill_dir / "SKILL.md", render_skill_md(skill_name, title, description))
    write_text(skill_dir / "agents" / "openai.yaml", render_openai_yaml(skill_name))
    write_text(
        skill_dir / "ll.contract.yaml",
        render_ll_contract(
            skill_name,
            input_artifact,
            output_artifact,
            workflow_key,
            lee_command,
            max_revision_rounds,
        ),
    )
    write_text(skill_dir / "ll.lifecycle.yaml", render_lifecycle(max_revision_rounds))
    write_text(skill_dir / "input" / "contract.yaml", render_input_contract(input_artifact))
    write_text(
        skill_dir / "input" / "schema.json",
        render_json_schema(f"{skill_name} input", input_artifact, False),
    )
    write_text(
        skill_dir / "input" / "semantic-checklist.md",
        render_input_checklist(input_artifact),
    )
    write_text(skill_dir / "output" / "contract.yaml", render_output_contract(input_artifact, output_artifact))
    write_text(
        skill_dir / "output" / "schema.json",
        render_json_schema(f"{skill_name} output", output_artifact, True),
    )
    write_text(
        skill_dir / "output" / "semantic-checklist.md",
        render_output_checklist(input_artifact, output_artifact),
    )
    write_text(skill_dir / "output" / "template.md", render_output_template(output_artifact, input_artifact))
    write_text(
        skill_dir / "evidence" / "execution-evidence.schema.json",
        render_execution_schema(skill_name),
    )
    write_text(
        skill_dir / "evidence" / "supervision-evidence.schema.json",
        render_supervision_schema(skill_name),
    )
    write_text(skill_dir / "evidence" / "report.template.md", render_report_template(skill_name))
    write_text(skill_dir / "agents" / "executor.md", render_executor_prompt(skill_name))
    write_text(skill_dir / "agents" / "supervisor.md", render_supervisor_prompt(skill_name))
    write_text(skill_dir / "resources" / "glossary.md", render_glossary())
    write_text(skill_dir / "resources" / "examples" / "input.example.md", render_input_example(input_artifact))
    write_text(skill_dir / "resources" / "examples" / "output.example.md", render_output_example(output_artifact, input_artifact))
    write_text(skill_dir / "resources" / "checklists" / "authoring-checklist.md", render_authoring_checklist())
    write_text(skill_dir / "resources" / "checklists" / "review-checklist.md", render_review_checklist())

    validate_input = skill_dir / "scripts" / "validate_input.sh"
    validate_output = skill_dir / "scripts" / "validate_output.sh"
    collect_evidence = skill_dir / "scripts" / "collect_evidence.sh"
    freeze_guard = skill_dir / "scripts" / "freeze_guard.sh"
    write_text(validate_input, render_validate_script("input"))
    write_text(validate_output, render_validate_script("output"))
    write_text(collect_evidence, render_collect_evidence_script())
    write_text(freeze_guard, render_freeze_guard_script())
    make_executable(validate_input)
    make_executable(validate_output)
    make_executable(collect_evidence)
    make_executable(freeze_guard)

    return skill_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a governed LEE Lite workflow skill.")
    parser.add_argument("skill_name", help="Skill name in hyphen-case or a name that can be normalized")
    parser.add_argument("--path", required=True, help="Directory where the skill folder will be created")
    parser.add_argument("--input-artifact", required=True, help="Input artifact type, for example src")
    parser.add_argument("--output-artifact", required=True, help="Output artifact type, for example epic")
    parser.add_argument("--workflow-key", help="Optional workflow key override")
    parser.add_argument("--lee-command", default="lee", help="LEE command prefix to place in templates")
    parser.add_argument("--max-revision-rounds", type=int, default=2, help="Maximum revision rounds in lifecycle")
    args = parser.parse_args()

    skill_name = normalize_skill_name(args.skill_name)
    if not skill_name:
        print("[ERROR] Skill name must include at least one letter or digit.")
        return 1
    if len(skill_name) > MAX_SKILL_NAME_LENGTH:
        print(f"[ERROR] Skill name is too long ({len(skill_name)} characters).")
        return 1
    if args.max_revision_rounds < 0:
        print("[ERROR] max revision rounds must be non-negative.")
        return 1

    workflow_key = args.workflow_key or skill_name.replace("-", ".")
    output_dir = Path(args.path).resolve()

    try:
        skill_dir = initialize_skill(
            skill_name=skill_name,
            output_dir=output_dir,
            input_artifact=args.input_artifact.strip().lower(),
            output_artifact=args.output_artifact.strip().lower(),
            workflow_key=workflow_key,
            lee_command=args.lee_command.strip(),
            max_revision_rounds=args.max_revision_rounds,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Created governed workflow skill at {skill_dir}")
    print("[OK] Next: replace placeholder sections and project-specific lee commands.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
