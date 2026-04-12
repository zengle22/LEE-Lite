---
id: API-SRC-RAW-TO-SRC-ADR048-001
ssot_type: API
title: API Contract - Formal Publication and Downstream Admission Interfaces
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-003
---

# API Contract - Formal Publication and Downstream Admission Interfaces

## materialize_formal_ref

- **input**: `gate_decision_ref`, `formal_type`, `consumer_eligibility_rules`
- **output**: `formal_ref`, `materialization_report_ref`
- **errors**: `gate_decision_not_approved`, `formal_type_unknown`, `materialization_failed`
- **idempotent**: yes, by gate_decision_ref hash

## dispatch_downstream

- **input**: `formal_ref`
- **output**: `dispatch_report_ref`
- **errors**: `formal_not_materialized`, `downstream_unreachable`, `dispatch_blocked`
- **idempotent**: yes, by formal_ref hash

## check_admission_eligibility

- **input**: `formal_ref`, `consumer_ref`, `consumer_type`
- **output**: `eligibility_verdict`, `eligibility_report_ref`
- **errors**: `formal_not_found`, `consumer_not_registered`
- **idempotent**: yes
