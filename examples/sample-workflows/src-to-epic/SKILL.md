---
name: src-to-epic
description: Governed LEE Lite workflow skill for transforming a frozen SRC artifact into a EPIC artifact with contracts, structural validation, semantic supervision, evidence capture, and freeze gates. Use when Codex should run or maintain the product.src-to-epic workflow instead of drafting outputs without governance.
---

# Src To Epic

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
