"""Governed skill producer commands."""

from __future__ import annotations

import uuid
from argparse import Namespace
from datetime import datetime, timedelta, timezone

from cli.lib.errors import ensure
from cli.lib.failure_capture_skill import run_failure_capture
from cli.lib.gate_human_orchestrator_skill import run_gate_human_orchestrator
from cli.lib.gate_remediation import promote_detected_to_open
from cli.lib.impl_spec_test_runtime import execute_impl_spec_test_skill
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.push_notifier import (
    create_draft_phase_preview,
    schedule_reminder,
    show_terminal_notification,
)
from cli.lib.skill_contract_enforcement import enforce_ll_contract_payload
from cli.lib.spec_reconcile_skill import run_spec_reconcile
from cli.lib.test_exec_runtime import execute_test_exec_skill
from cli.lib.bug_registry import load_or_create_registry


def _skill_handler(ctx: CommandContext):
    ensure(
        ctx.action in {"impl-spec-test", "test-exec-web-e2e", "test-exec-cli", "gate-human-orchestrator", "failure-capture", "spec-reconcile", "tech-to-impl", "feat-to-apiplan", "prototype-to-e2eplan", "api-manifest-init", "e2e-manifest-init", "api-spec-gen", "e2e-spec-gen", "settlement", "gate-evaluate", "render-testset-view", "qa-test-run", "bug-transition", "bug-remediate", "bug-check-shadow"},
        "INVALID_REQUEST",
        "unsupported skill action",
    )
    if ctx.action == "spec-reconcile":
        enforce_ll_contract_payload(
            ctx.workspace_root,
            skill_dir_ref="skills/l3/ll-governance-spec-reconcile",
            payload=ctx.payload,
        )
        result = run_spec_reconcile(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            request_id=ctx.request["request_id"],
            payload=ctx.payload,
        )
        evidence_refs = _collect_refs(result)
        return "OK", "spec reconcile report emitted", {
            "canonical_path": result["canonical_path"],
            **result,
        }, [], evidence_refs
    if ctx.action == "failure-capture":
        result = run_failure_capture(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            request_id=ctx.request["request_id"],
            payload=ctx.payload,
        )
        evidence_refs = _collect_refs(result)
        return "OK", "governed failure capture package emitted", {
            "canonical_path": result["canonical_path"],
            **result,
        }, [], evidence_refs
    if ctx.action == "gate-human-orchestrator":
        result = run_gate_human_orchestrator(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            payload=ctx.payload,
        )
        evidence_refs = _collect_refs(result)
        message = "governed gate human orchestrator completed"
        if result.get("human_brief_markdown"):
            message = "governed gate human orchestrator prepared a pending human brief"
        return "OK", message, {
            "canonical_path": result["canonical_path"],
            **result,
        }, [], evidence_refs
    if ctx.action == "tech-to-impl":
        from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir
        from pathlib import Path

        for field in ("impl_ref", "feat_ref", "tech_ref", "arch_ref", "api_ref", "impl_package_ref"):
            ensure(field in ctx.payload, "INVALID_REQUEST", f"missing skill field: {field}")
        impl_package_ref = str(ctx.payload["impl_package_ref"]).strip()
        scripts_dir = resolve_skill_scripts_dir(ctx.workspace_root, "ll-dev-tech-to-impl")
        import sys

        inserted = False
        scripts_str = str(scripts_dir.resolve())
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)
            inserted = True
        try:
            from tech_to_impl_runtime import run_workflow

            result = run_workflow(
                input_path=impl_package_ref,
                feat_ref=str(ctx.payload["feat_ref"]),
                tech_ref=str(ctx.payload["tech_ref"]),
                repo_root=ctx.workspace_root,
                run_id=str(ctx.request["request_id"]),
                allow_update=True,
            )
        finally:
            if inserted and scripts_str in sys.path:
                sys.path.remove(scripts_str)
        evidence_refs = _collect_refs(result)
        return "OK", "tech-to-impl candidate emitted", {
            "canonical_path": result["artifacts_dir"],
            **result,
        }, [], evidence_refs

    _QA_SKILL_MAP = {
        "feat-to-apiplan": ("ll-qa-feat-to-apiplan", "feat_to_apiplan"),
        "prototype-to-e2eplan": ("ll-qa-prototype-to-e2eplan", "prototype_to_e2eplan"),
        "api-manifest-init": ("ll-qa-api-manifest-init", "api_manifest_init"),
        "e2e-manifest-init": ("ll-qa-e2e-manifest-init", "e2e_manifest_init"),
        "api-spec-gen": ("ll-qa-api-spec-gen", "api_spec_gen"),
        "e2e-spec-gen": ("ll-qa-e2e-spec-gen", "e2e_spec_gen"),
        "settlement": ("ll-qa-settlement", "qa_settlement"),
        "gate-evaluate": ("ll-qa-gate-evaluate", "qa_gate_evaluate"),
        "render-testset-view": ("render-testset-view", "qa_render_testset"),
    }
    if ctx.action in _QA_SKILL_MAP:
        from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir
        import sys

        skill_dir_name, runtime_module = _QA_SKILL_MAP[ctx.action]
        scripts_dir = resolve_skill_scripts_dir(ctx.workspace_root, skill_dir_name)
        inserted = False
        scripts_str = str(scripts_dir.resolve())
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)
            inserted = True
        try:
            # pylint: disable=import-outside-toplevel
            from qa_skill_runtime import run_skill

            result = run_skill(
                action=ctx.action,
                workspace_root=ctx.workspace_root,
                payload=ctx.payload,
                request_id=ctx.request["request_id"],
            )
        finally:
            if inserted and scripts_str in sys.path:
                sys.path.remove(scripts_str)

        # Gate FAIL post-processing: promote bugs, notify, schedule reminder
        if ctx.action == "gate-evaluate":
            final_decision = result.get("final_decision")
            if final_decision == "fail":
                feat_ref = ctx.payload.get("feat_ref", ctx.payload.get("feature_id", "unknown"))
                run_id = str(ctx.request["request_id"])

                # Try to get gap_list from settlement reports if available
                gap_list = []
                if "api_chain" in result and "gap_list" in result["api_chain"]:
                    gap_list.extend(result["api_chain"]["gap_list"])
                if "e2e_chain" in result and "gap_list" in result["e2e_chain"]:
                    gap_list.extend(result["e2e_chain"]["gap_list"])

                # Promote detected bugs to open
                try:
                    promote_result = promote_detected_to_open(
                        ctx.workspace_root, feat_ref, gap_list, run_id
                    )
                except Exception:
                    # Continue even if promotion fails
                    promote_result = {"promoted_count": 0}

                # Load registry to get the bugs
                try:
                    registry = load_or_create_registry(ctx.workspace_root, feat_ref)
                    open_bugs = [b for b in registry["bugs"] if b["status"] == "open"]
                except Exception:
                    open_bugs = []

                # Show terminal notification
                bug_count = len(open_bugs) or promote_result.get("promoted_count", 0)
                show_terminal_notification(feat_ref, bug_count, run_id)

                # Create draft phase preview
                if open_bugs:
                    try:
                        create_draft_phase_preview(ctx.workspace_root, feat_ref, open_bugs, run_id)
                    except Exception:
                        pass

                # Schedule T+4h reminder
                if open_bugs:
                    try:
                        trigger_at = datetime.now(timezone.utc) + timedelta(hours=4)
                        schedule_reminder(ctx.workspace_root, feat_ref, open_bugs, trigger_at)
                    except Exception:
                        pass

        evidence_refs = _collect_refs(result)
        return "OK", f"governed {ctx.action} completed", {
            "canonical_path": result.get("canonical_path", ""),
            **result,
        }, [], evidence_refs
    if ctx.action == "bug-transition":
        from cli.lib.bug_registry import (
            load_or_create_registry,
            registry_path,
            transition_bug_status_with_audit,
            _save_registry,
        )

        feat_ref = ctx.payload.get("feat_ref")
        bug_id = ctx.payload.get("bug_id")
        to_state = ctx.payload.get("to_state")
        reason = ctx.payload.get("reason")
        duplicate_of = ctx.payload.get("duplicate_of")
        actor = ctx.payload.get("actor", "user")
        run_id = ctx.payload.get("run_id", str(ctx.request["request_id"]))

        ensure(feat_ref, "INVALID_REQUEST", "feat_ref is required")
        ensure(bug_id, "INVALID_REQUEST", "bug_id is required")
        ensure(to_state, "INVALID_REQUEST", "to_state is required")

        registry = load_or_create_registry(ctx.workspace_root, feat_ref)

        # Find the bug
        bug = None
        for b in registry["bugs"]:
            if b.get("bug_id") == bug_id:
                bug = b
                break

        ensure(bug is not None, "INVALID_REQUEST", f"Bug {bug_id} not found")

        # Transition
        extra = {}
        if duplicate_of:
            extra["duplicate_of"] = duplicate_of

        new_bug = transition_bug_status_with_audit(
            ctx.workspace_root,
            feat_ref,
            bug,
            to_state,
            reason=reason,
            actor=actor,
            run_id=run_id,
            **extra,
        )

        # Update registry
        new_bugs = []
        for b in registry["bugs"]:
            if b.get("bug_id") == bug_id:
                new_bugs.append(new_bug)
            else:
                new_bugs.append(b)
        registry["bugs"] = new_bugs
        registry["version"] = str(uuid.uuid4())
        _save_registry(registry_path(ctx.workspace_root, feat_ref), registry)

        return "OK", f"Bug {bug_id} transitioned to {to_state}", {
            "bug_id": bug_id,
            "old_state": bug["status"],
            "new_state": to_state,
            "feat_ref": feat_ref,
        }, [], []
    if ctx.action == "bug-remediate":
        from cli.lib.bug_registry import load_or_create_registry

        feat_ref = ctx.payload.get("feat_ref")
        bug_id = ctx.payload.get("bug_id")
        batch = ctx.payload.get("batch", False)

        ensure(feat_ref, "INVALID_REQUEST", "feat_ref is required")

        registry = load_or_create_registry(ctx.workspace_root, feat_ref)
        open_bugs = [b for b in registry["bugs"] if b["status"] in {"open"}]

        if bug_id:
            open_bugs = [b for b in open_bugs if b.get("bug_id") == bug_id]
            ensure(open_bugs, "INVALID_REQUEST", f"Bug {bug_id} not found or not open")

        if not open_bugs:
            return "OK", "No open bugs to remediate", {
                "feat_ref": feat_ref,
                "bug_count": 0,
            }, [], []

        # Try to use bug_phase_generator if available
        phase_created = False
        phase_path = None
        try:
            from cli.lib.bug_phase_generator import create_bug_phase
            result = create_bug_phase(
                ctx.workspace_root,
                feat_ref,
                open_bugs,
                batch=batch,
            )
            phase_created = result.get("phase_created", False)
            phase_path = result.get("phase_path")
        except ImportError:
            pass

        return "OK", f"Prepared remediation for {len(open_bugs)} bugs", {
            "feat_ref": feat_ref,
            "bug_count": len(open_bugs),
            "bugs": [{"bug_id": b["bug_id"], "title": b["title"]} for b in open_bugs],
            "phase_created": phase_created,
            "phase_path": str(phase_path) if phase_path else None,
        }, [], []
    if ctx.action == "bug-check-shadow":
        from cli.lib.shadow_detect import check_shadow_fixes

        feat_ref = ctx.payload.get("feat_ref")
        since_commit = ctx.payload.get("since_commit")

        ensure(feat_ref, "INVALID_REQUEST", "feat_ref is required")

        result = check_shadow_fixes(
            ctx.workspace_root,
            feat_ref,
            since_commit=since_commit,
        )

        status = "OK" if result["shadow_fix_count"] == 0 else "WARN"
        return status, result["summary"], {
            "feat_ref": feat_ref,
            **result,
        }, result["warnings"], []
    if ctx.action == "qa-test-run":
        from cli.lib.test_orchestrator import run_spec_test
        from cli.lib.bug_registry import sync_bugs_to_registry

        # Extract parameters from payload
        feat_ref = ctx.payload.get("feat_ref")
        proto_ref = ctx.payload.get("proto_ref")
        app_url = ctx.payload.get("app_url", "http://localhost:3000")
        api_url = ctx.payload.get("api_url")
        chain = ctx.payload.get("chain", "api")
        coverage_mode = ctx.payload.get("coverage_mode", "smoke")
        resume = ctx.payload.get("resume", False)
        resume_from = ctx.payload.get("resume_from")
        verify_bugs = ctx.payload.get("verify_bugs", False)
        verify_mode = ctx.payload.get("verify_mode", "targeted")

        if chain == "both":
            # Execute API chain first, then E2E chain
            api_result = run_spec_test(
                workspace_root=ctx.workspace_root,
                feat_ref=feat_ref,
                proto_ref=proto_ref,
                base_url=api_url or app_url,
                app_url=app_url,
                api_url=api_url,
                modality="api",
                coverage_mode=coverage_mode,
                resume=resume,
                resume_from=resume_from,
                on_complete=sync_bugs_to_registry,
                verify_bugs=verify_bugs,
                verify_mode=verify_mode,
            )
            e2e_result = run_spec_test(
                workspace_root=ctx.workspace_root,
                feat_ref=feat_ref,
                proto_ref=proto_ref,
                base_url=api_url or app_url,
                app_url=app_url,
                api_url=api_url,
                modality="web_e2e",
                coverage_mode=coverage_mode,
                resume=resume,
                resume_from=resume_from,
                on_complete=sync_bugs_to_registry,
                verify_bugs=verify_bugs,
                verify_mode=verify_mode,
            )
            # Merge results
            merged_case_results = api_result.case_results + e2e_result.case_results
            merged_manifest_items = api_result.manifest_items + e2e_result.manifest_items
            merged_run_id = api_result.run_id
            merged_candidate_path = api_result.candidate_path or e2e_result.candidate_path

            evidence_refs = _collect_refs({
                "candidate_artifact_ref": api_result.execution_refs.get("candidate_artifact_ref", ""),
            })
            evidence_refs.extend(_collect_refs({
                "candidate_artifact_ref": e2e_result.execution_refs.get("candidate_artifact_ref", ""),
            }))

            return "OK", "governed qa-test-run completed (api + e2e)", {
                "canonical_path": merged_candidate_path or f"artifacts/active/qa/candidates/{merged_run_id}.json",
                "run_id": merged_run_id,
                "executed_count": len(merged_case_results),
                "manifest_items_count": len(merged_manifest_items),
            }, [], evidence_refs

        # Determine modality from chain
        modality = "api" if chain == "api" else "web_e2e"

        result = run_spec_test(
            workspace_root=ctx.workspace_root,
            feat_ref=feat_ref,
            proto_ref=proto_ref,
            base_url=api_url or app_url,
            app_url=app_url,
            api_url=api_url,
            modality=modality,
            coverage_mode=coverage_mode,
            resume=resume,
            resume_from=resume_from,
            on_complete=sync_bugs_to_registry,
            verify_bugs=verify_bugs,
            verify_mode=verify_mode,
        )

        evidence_refs = _collect_refs({
            "candidate_artifact_ref": result.execution_refs.get("candidate_artifact_ref", ""),
        })

        return "OK", f"governed qa-test-run completed", {
            "canonical_path": result.candidate_path or f"artifacts/active/qa/candidates/{result.run_id}.json",
            "run_id": result.run_id,
            "executed_count": len(result.case_results),
            "manifest_items_count": len(result.manifest_items),
        }, [], evidence_refs

    payload = ctx.payload
    if ctx.action == "impl-spec-test":
        for field in ("impl_ref", "impl_package_ref", "feat_ref", "tech_ref"):
            ensure(field in payload, "INVALID_REQUEST", f"missing skill field: {field}")
        result = execute_impl_spec_test_skill(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            request_id=ctx.request["request_id"],
            payload=payload,
        )
        excluded = {"skill_ref", "runner_skill_ref", "trace_ref"}
        evidence_refs = [value for key, value in result.items() if key.endswith("_ref") and key not in excluded]
        return "OK", "governed impl spec test candidate emitted", {
            "canonical_path": result["handoff_ref"],
            **result,
        }, [], evidence_refs
    for field in ("test_set_ref", "test_environment_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing skill field: {field}")
    result = execute_test_exec_skill(
        workspace_root=ctx.workspace_root,
        trace=ctx.trace,
        action=ctx.action,
        request_id=ctx.request["request_id"],
        payload=payload,
    )
    excluded = {"skill_ref", "runner_skill_ref", "trace_ref"}
    evidence_refs = [value for key, value in result.items() if key.endswith("_ref") and key not in excluded]
    return "OK", "governed skill candidate emitted", {
        "canonical_path": result["handoff_ref"],
        **result,
    }, [], evidence_refs


def _collect_refs(payload: dict[str, object]) -> list[str]:
    excluded = {"skill_ref", "runner_skill_ref"}
    refs: list[str] = []
    for key, value in payload.items():
        if key.endswith("_ref") and key not in excluded and isinstance(value, str) and value.strip():
            refs.append(value)
        elif key == "items" and isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                for nested_key, nested_value in item.items():
                    if nested_key.endswith("_ref") and nested_key not in excluded and isinstance(nested_value, str) and nested_value.strip():
                        refs.append(nested_value)
    return list(dict.fromkeys(refs))


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _skill_handler)
