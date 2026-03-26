from __future__ import annotations

INTERFACE_CONTRACTS_BY_AXIS = {
    "projection_generation": [
        "`ProjectionRenderRequest`: input=`ssot_ref`, `template_version`, `review_stage`; output=`projection_ref`, `derived_markers`, `trace_refs`; errors=`ssot_not_ready`, `template_missing`; idempotent=`yes by ssot_ref + template_version`; precondition=`Machine SSOT freeze-ready for gate review`。",
        "`ProjectionRenderResult`: input=`projection_ref`; output=`review_blocks`, `derived_only`, `non_authoritative`, `non_inheritable`; errors=`marker_missing`; idempotent=`yes`; precondition=`projection rendered`。",
    ],
    "authoritative_snapshot": [
        "`SnapshotExtractionRequest`: input=`ssot_ref`, `projection_ref?`; output=`snapshot_ref`, `field_refs`; errors=`authoritative_field_missing`; idempotent=`yes by ssot_ref`; precondition=`SSOT authoritative fields resolvable`。",
        "`AuthoritativeSnapshot`: input=`snapshot_ref`; output=`completed_state`, `authoritative_output`, `frozen_downstream_boundary`, `open_technical_decisions`; errors=`incomplete_snapshot`; idempotent=`yes`; precondition=`snapshot extracted`。",
    ],
    "review_focus_risk": [
        "`ReviewFocusRequest`: input=`ssot_ref`, `projection_ref`; output=`focus_ref`, `focus_items`, `risk_items`, `ambiguity_items`; errors=`insufficient_context`; idempotent=`yes by ssot_ref + projection_ref`; precondition=`Projection already rendered`。",
        "`RiskSignal`: input=`focus_ref`; output=`signal_type`, `source_trace_refs`, `review_prompt`; errors=`signal_untraceable`; idempotent=`yes`; precondition=`focus extraction complete`。",
    ],
    "feedback_writeback": [
        "`ProjectionComment`: input=`projection_ref`, `comment_ref`, `comment_text`, `comment_author`; output=`mapped_field_refs`, `revision_request_ref`; errors=`mapping_failed`; idempotent=`yes by comment_ref`; precondition=`projection rendered for review`。",
        "`ProjectionRegenerationRequest`: input=`revision_request_ref`, `updated_ssot_ref`; output=`regenerated_projection_ref`; errors=`ssot_update_missing`; idempotent=`yes by revision_request_ref + updated_ssot_ref`; precondition=`Machine SSOT already updated`。",
    ],
    "runner_ready_job": [
        "`ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。",
        "`ReadyQueueRecord`: input=`ready_job_ref`; output=`queue_slot_ref`, `ready_visible`, `trace_ref`; errors=`queue_write_failed`; idempotent=`yes by ready_job_ref`; precondition=`ready execution job already materialized`。",
    ],
    "runner_operator_entry": [
        "`ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。",
        "`RunnerEntryReceipt`: input=`runner_run_ref`; output=`entry_mode`, `runner_context_ref`, `started_at`; errors=`receipt_missing`; idempotent=`yes`; precondition=`runner entry already accepted`。",
    ],
    "runner_control_surface": [
        "`RunnerControlAction`: input=`runner_context_ref`, `command`, `job_ref?`; output=`control_action_ref`, `runner_state_ref`; errors=`invalid_transition`, `ownership_conflict`; idempotent=`yes by runner_context_ref + command + job_ref`; precondition=`runner context active`。",
        "`RunnerStateRecord`: input=`control_action_ref`; output=`state`, `job_ref`, `ownership_ref`; errors=`state_missing`; idempotent=`yes`; precondition=`control action recorded`。",
    ],
    "runner_intake": [
        "`JobClaimRequest`: input=`runner_context_ref`, `ready_job_ref`; output=`claimed_job_ref`, `ownership_ref`, `running_state_ref`; errors=`job_not_ready`, `already_claimed`; idempotent=`yes by runner_context_ref + ready_job_ref`; precondition=`ready job visible in queue`。",
        "`RunningOwnershipRecord`: input=`claimed_job_ref`; output=`runner_context_ref`, `claimed_at`, `ownership_ref`; errors=`ownership_missing`; idempotent=`yes`; precondition=`job claimed by runner`。",
    ],
    "runner_dispatch": [
        "`NextSkillInvocation`: input=`claimed_job_ref`, `target_skill_ref`, `authoritative_input_ref`; output=`invocation_ref`, `execution_attempt_ref`, `dispatch_lineage_ref`; errors=`target_skill_missing`, `dispatch_failed`; idempotent=`yes by claimed_job_ref + target_skill_ref`; precondition=`claimed job already owned by runner`。",
        "`ExecutionAttemptRecord`: input=`invocation_ref`; output=`attempt_state`, `started_at`, `dispatch_lineage_ref`; errors=`attempt_missing`; idempotent=`yes`; precondition=`invocation emitted`。",
    ],
    "runner_feedback": [
        "`ExecutionOutcomeRecord`: input=`execution_attempt_ref`, `outcome`, `failure_evidence_ref?`; output=`execution_outcome_ref`, `retry_reentry_ref?`; errors=`invalid_outcome_transition`; idempotent=`yes by execution_attempt_ref + outcome`; precondition=`execution attempt already opened`。",
        "`RetryReentryDirective`: input=`execution_outcome_ref`; output=`reentry_target`, `retry_reason`, `lineage_ref`; errors=`retry_not_allowed`; idempotent=`yes`; precondition=`outcome is retry_reentry`。",
    ],
    "runner_observability": [
        "`RunnerObservabilitySnapshot`: input=`runner_scope_ref`, `status_filter?`; output=`observability_snapshot_ref`, `ready_backlog`, `running_items`, `failed_items`, `waiting_human_items`; errors=`status_projection_failed`; idempotent=`yes by runner_scope_ref + status_filter`; precondition=`runner scope exists`。",
        "`RunnerStatusQuery`: input=`observability_snapshot_ref`; output=`status_items`, `lineage_refs`, `next_operator_action?`; errors=`snapshot_missing`; idempotent=`yes`; precondition=`snapshot already projected`。",
    ],
    "collaboration": [
        "`HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`; errors=`invalid_state`, `missing_payload`, `duplicate_submission`; idempotent=`yes by producer_ref + proposal_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`。",
        "`DecisionReturnEnvelope` (consumed): input=`handoff_ref`, `decision_ref`, `decision`, `routing_hint`, `trace_ref`; output=`boundary_handoff_record | reentry_directive`; errors=`decision_conflict`, `handoff_missing`; idempotent=`yes by handoff_ref + decision_ref`; precondition=`decision object 已由 external gate authoritative emit`。",
    ],
    "formalization": [
        "`GateBriefRecord`: input=`handoff_ref`, `proposal_ref`, `evidence_refs`; output=`brief_record_ref`, `pending_human_decision_ref`, `priority`, `merge_group`, `human_projection`; errors=`invalid_state`, `brief_build_failed`; idempotent=`yes by handoff_ref + brief_round`; precondition=`handoff 已进入 gate pending`。",
        "`GateDecision`: input=`brief_record_ref`, `pending_human_decision_ref`, `human_action`, `decision_target`, `decision_basis_refs`; output=`decision_ref`, `decision`, `decision_reason`, `decision_target`, `decision_basis_refs`, `dispatch_target`; errors=`invalid_state`, `unknown_target`, `missing_basis_refs`, `policy_reject`; idempotent=`yes by pending_human_decision_ref + decision_round`; precondition=`pending human decision is active and uniquely claimed`。",
    ],
    "layering": [
        "`AdmissionRequest`: input=`consumer_ref`, `requested_ref`, `lineage_ref?`; output=`allow`, `resolved_formal_ref`, `layer`, `reason_code`; errors=`formal_ref_missing`, `lineage_missing`, `layer_violation`; idempotent=`yes by consumer_ref + requested_ref`; precondition=`requested object 已可解析到 registry / lineage`。",
        "`LineageResolveRequest`: input=`candidate_ref | formal_ref`; output=`authoritative_ref`, `layer`, `upstream_refs`, `downstream_refs`; errors=`unknown_ref`, `ambiguous_lineage`; idempotent=`yes`; precondition=`ref 存在于 registry/lineage store`。",
    ],
    "io_governance": [
        "`GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。",
        "`PolicyVerdict`: input=`logical_path`, `path_class`, `mode`, `caller_ref`; output=`allow`, `reason_code`, `resolved_path`, `mode_decision`; errors=`invalid_path_class`, `mode_forbidden`; idempotent=`yes`; precondition=`request normalized`。",
    ],
    "adoption_e2e": [
        "`OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。",
        "`PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。",
    ],
}

DEFAULT_API_COMMAND_SPECS = [
    {
        "command": "ll gate submit-handoff",
        "surface": "`ll gate submit-handoff --request <gate_submit_handoff.request.json> --response-out <gate_submit_handoff.response.json>` via `cli/commands/gate/command.py`",
        "request_schema": ["`producer_ref: string`", "`proposal_ref: string`", "`payload_ref: string`", "`trace_context_ref: string`"],
        "response_schema": ["success envelope=`{ ok: true, command_ref, trace_ref, result }`", "result fields=`handoff_ref`, `gate_pending_ref`, `canonical_payload_path`", "error envelope=`{ ok: false, command_ref, trace_ref, error }`"],
        "field_semantics": ["`handoff_ref` is the authoritative submission record for the producer proposal.", "`gate_pending_ref` is the queue-visible pending record consumed by the gate loop."],
        "errors": ["`invalid_state`", "`missing_payload`", "`duplicate_submission`"],
        "enum_domain": [],
        "invariants": ["one proposal/payload digest pair resolves to at most one authoritative handoff", "submission must not leak approve/reject semantics"],
        "canonical_refs": ["`handoff_ref`", "`gate_pending_ref`", "`trace_ref`", "`canonical_payload_path`"],
        "preconditions": ["payload is already persisted in a runtime-readable location"],
        "idempotency": "idempotent by `producer_ref + proposal_ref + payload_digest`",
    },
    {
        "command": "ll gate show-pending",
        "surface": "`ll gate show-pending --request <gate_show_pending.request.json> --response-out <gate_show_pending.response.json>` via `cli/commands/gate/command.py`",
        "request_schema": ["`gate_queue_ref: string?`", "`producer_ref: string?`"],
        "response_schema": ["success envelope=`{ ok: true, command_ref, trace_ref, result }`", "result fields=`pending_count`, `pending_items`, `assigned_gate_queue`"],
        "field_semantics": ["`pending_items` is a projection of authoritative queue-visible handoff records."],
        "errors": ["`query_invalid`"],
        "enum_domain": [],
        "invariants": ["empty queues must still return stable machine-readable envelopes"],
        "canonical_refs": ["`gate_pending_ref`", "`assigned_gate_queue`"],
        "preconditions": ["query filters are normalized before visibility is projected"],
        "idempotency": "idempotent by normalized query filter",
    },
]
