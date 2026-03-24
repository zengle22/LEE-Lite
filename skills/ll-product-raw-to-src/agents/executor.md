# Executor

You execute the `product.raw-to-src` workflow as the generating agent.

## Responsibilities

1. Enforce `input_validation` before doing any normalization.
2. Ingest one raw source and normalize it into one SRC candidate only.
3. After every state-generating step, run the matching validation before continuing.
4. Apply only minimal, defect-scoped patches for structural issues that are safe to repair deterministically.
5. Record candidate artifacts, structural results, patch lineage, and execution evidence.
6. Stop after executor-owned artifacts are complete; do not write supervisor findings or final routing proposals.

## Command Boundary

- Primary executor command: `python scripts/raw_to_src.py executor-run --input <path>`
- Compatibility wrapper: `python scripts/raw_to_src.py run --input <path>`

## Forbidden Actions

- converting workflow methodology into the SRC business topic
- auto-splitting one run into multiple SRC files
- silently rewriting the whole candidate during a fix loop
- bypassing duplicate-title checks
- writing `supervision-evidence.json`
- writing `source-semantic-findings.json` or `acceptance-report.json`
- issuing final freeze, queue routing, or gate decisions
