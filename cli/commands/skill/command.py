"""Governed skill producer commands."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.failure_capture_skill import run_failure_capture
from cli.lib.gate_human_orchestrator_skill import run_gate_human_orchestrator
from cli.lib.impl_spec_test_runtime import execute_impl_spec_test_skill
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.skill_contract_enforcement import enforce_ll_contract_payload
from cli.lib.spec_reconcile_skill import run_spec_reconcile
from cli.lib.test_exec_runtime import execute_test_exec_skill


def _skill_handler(ctx: CommandContext):
    ensure(
        ctx.action in {"impl-spec-test", "test-exec-web-e2e", "test-exec-cli", "gate-human-orchestrator", "failure-capture", "spec-reconcile", "tech-to-impl", "feat-to-apiplan", "prototype-to-e2eplan", "api-manifest-init", "e2e-manifest-init", "api-spec-gen", "e2e-spec-gen", "settlement", "gate-evaluate", "render-testset-view", "qa-test-run"},
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

    # QA skill actions — Prompt-first via skill's agents/executor.md
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
        evidence_refs = _collect_refs(result)
        return "OK", f"governed {ctx.action} completed", {
            "canonical_path": result.get("canonical_path", ""),
            **result,
        }, [], evidence_refs

    if ctx.action == "qa-test-run":
        from cli.lib.test_orchestrator import run_spec_test

        # Extract parameters from payload
        feat_ref = ctx.payload.get("feat_ref")
        proto_ref = ctx.payload.get("proto_ref")
        app_url = ctx.payload.get("app_url", "http://localhost:3000")
        api_url = ctx.payload.get("api_url")
        chain = ctx.payload.get("chain", "api")
        coverage_mode = ctx.payload.get("coverage_mode", "smoke")
        resume = ctx.payload.get("resume", False)
        resume_from = ctx.payload.get("resume_from")

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
        )

        evidence_refs = _collect_refs({
            "candidate_artifact_ref": result.execution_refs.get("candidate_artifact_ref", ""),
        })

        return "OK", f"governed qa-test-run completed", {
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
