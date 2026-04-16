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
        ctx.action in {"impl-spec-test", "test-exec-web-e2e", "test-exec-cli", "gate-human-orchestrator", "failure-capture", "spec-reconcile", "tech-to-impl", "feat-to-apiplan", "prototype-to-e2eplan", "api-manifest-init", "e2e-manifest-init", "api-spec-gen", "e2e-spec-gen", "settlement", "gate-evaluate", "render-testset-view", "api-spec-to-tests", "e2e-spec-to-tests", "api-test-exec", "e2e-test-exec", "patch-capture", "patch-settle"},
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

    if ctx.action == "patch-capture":
        from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir

        ensure("feat_id" in ctx.payload, "INVALID_REQUEST", "missing feat_id")
        ensure("input_type" in ctx.payload, "INVALID_REQUEST", "missing input_type")
        ensure("input_value" in ctx.payload, "INVALID_REQUEST", "missing input_value")

        scripts_dir = resolve_skill_scripts_dir(ctx.workspace_root, "ll-patch-capture")
        import importlib.util

        mod_path = scripts_dir / "patch_capture_runtime.py"
        spec = importlib.util.spec_from_file_location("patch_capture_runtime", mod_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["patch_capture_runtime"] = mod
        spec.loader.exec_module(mod)
        result = mod.run_skill(
            workspace_root=ctx.workspace_root,
            payload=ctx.payload,
            request_id=ctx.request["request_id"],
        )

        evidence_refs = _collect_refs(result)
        return "OK", "patch capture registered", {
            "canonical_path": result.get("patch_path", ""),
            **result,
        }, [], evidence_refs

    if ctx.action == "patch-settle":
        from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir
        import sys

        ensure("feat_id" in ctx.payload, "INVALID_REQUEST", "missing feat_id")

        scripts_dir = resolve_skill_scripts_dir(ctx.workspace_root, "ll-experience-patch-settle")
        import importlib.util

        mod_path = scripts_dir / "settle_runtime.py"
        spec = importlib.util.spec_from_file_location("settle_runtime", mod_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["settle_runtime"] = mod
        spec.loader.exec_module(mod)
        result = mod.run_skill(
            workspace_root=ctx.workspace_root,
            payload=ctx.payload,
        )

        evidence_refs = _collect_refs(result)
        return "OK", "patch settle completed", {
            "canonical_path": result.get("report_path", ""),
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
        # Phase 5: generation + execution skills (D-CLI-01)
        "api-spec-to-tests": ("ll-qa-api-spec-to-tests", "qa_skill_runtime"),
        "e2e-spec-to-tests": ("ll-qa-e2e-spec-to-tests", "qa_skill_runtime"),
        "api-test-exec": ("ll-qa-api-test-exec", "api_test_exec"),
        "e2e-test-exec": ("ll-qa-e2e-test-exec", "e2e_test_exec"),
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

    # Code-driven execution skills (bypass LLM runtime)
    EXEC_SKILL_RUNTIME = {
        "api-test-exec": ("cli.lib.api_test_exec", "run_api_test_exec"),
        "e2e-test-exec": ("cli.lib.e2e_test_exec", "run_e2e_test_exec"),
    }
    if ctx.action in EXEC_SKILL_RUNTIME:
        module_path, func_name = EXEC_SKILL_RUNTIME[ctx.action]
        from importlib import import_module
        mod = import_module(module_path)
        func = getattr(mod, func_name)
        result = func(
            spec_path=ctx.payload.get("spec_path", ""),
            test_dir=ctx.payload.get("test_dir", ""),
            manifest_path=ctx.payload.get("manifest_path", ""),
            evidence_dir=ctx.payload.get("evidence_dir", ""),
            run_id=ctx.request["request_id"],
            base_url=ctx.payload.get("base_url", ctx.payload.get("target_url", "")),
        )
        evidence_refs = _collect_refs(result)
        return "OK", f"governed {ctx.action} completed", {
            "canonical_path": result.get("evidence_dir", ""),
            **result,
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
