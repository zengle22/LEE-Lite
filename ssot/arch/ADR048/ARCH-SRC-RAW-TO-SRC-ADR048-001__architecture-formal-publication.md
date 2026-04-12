---
id: ARCH-SRC-RAW-TO-SRC-ADR048-001
ssot_type: ARCH
title: Architecture - Formal Publication and Downstream Admission
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-003
---

# Architecture - Formal Publication and Downstream Admission

## Architecture Summary

The formal publication layer sits between gate decision outcomes and downstream consumer dispatch. It materializes approved decisions into formal refs with managed state transitions and routes downstream consumers based on formal_ref type.

## Layering

- Formal materialization consumes gate decision artifacts and produces typed formal refs.
- Downstream dispatch reads formal refs and routes to eligible consumers (src, epic, feat, tech, testset).
- Registry provides formal ref lookup and consumer eligibility verification.
- Existing skills without formal dispatch observe published refs via registry fallback.

## Ownership

- Formal state management: owned by formal publication flow.
- Dispatch routing: owned by ready_job_dispatch flow.
- Consumer eligibility: owned by registry with formal_ref type constraints.
