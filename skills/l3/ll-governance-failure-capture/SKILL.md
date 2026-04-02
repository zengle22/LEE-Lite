---
name: ll-governance-failure-capture
description: Governed LEE Lite workflow skill for capturing a failure into a constrained failure package with contracts, structural validation, semantic supervision, evidence capture, and freeze gates. Use when Codex should freeze a problem into a governed package instead of repairing the output first.
---

# LL Governance Failure Capture

This skill captures a detected problem into a governed package. It is capture-only: do not use it to auto-repair artifacts.

## Run Protocol

1. Read `ll.contract.yaml`, `input/contract.yaml`, and `output/contract.yaml`.
2. Validate the request structurally before writing any package files.
3. Run `python scripts/workflow_runtime.py run --input <artifact> --repo-root <repo-root>`.
4. Produce one constrained package with `capture_manifest.json`, `diagnosis_stub.json`, `repair_context.json`, and either `failure_case.json` or `issue_log.json`.
5. Stop after capture. Hand repair to a human or a human-directed AI pass.

## Role Split

- Executor captures the package and keeps the scope tight.
- Supervisor checks that the package is sufficient for later repair and governance.
- Neither role should silently repair the failed artifact in this workflow.

## Files To Read

- `ll.contract.yaml`
- `input/`
- `output/`
- `resources/examples/`
- `resources/checklists/`
- `resources/contracts/`

## Non-Goals

- automatic repair
- broad refactors
- final diagnosis
- system-wide remediation planning
