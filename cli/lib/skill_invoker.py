"""Dispatch claimed jobs to governed workflow entrypoints."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from cli.lib.errors import CommandError, ensure
from cli.lib.execution_return_registry import invoke_execution_return_job
from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir


@contextmanager
def _prepend_sys_path(path: Path) -> Iterator[None]:
    text = str(path.resolve())
    inserted = False
    if text not in sys.path:
        sys.path.insert(0, text)
        inserted = True
    try:
        yield
    finally:
        if inserted:
            sys.path.remove(text)


def _invoke_feat_to_tech(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    ensure(job.get("feat_ref"), "PRECONDITION_FAILED", "feat_to_tech job missing feat_ref")
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-dev-feat-to-tech")
    with _prepend_sys_path(scripts_dir):
        from feat_to_tech_runtime import run_workflow

        result = run_workflow(
            input_path=input_ref,
            feat_ref=str(job["feat_ref"]),
            repo_root=workspace_root,
            run_id=str(payload.get("downstream_run_id") or ""),
            allow_update=True,
        )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_feat_to_ui(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    raise CommandError(
        "PRECONDITION_FAILED",
        "workflow.dev.feat_to_ui is deprecated and disabled; use workflow.dev.feat_to_proto first, then workflow.dev.proto_to_ui after human-reviewed prototype freeze",
    )


def _invoke_feat_to_proto(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    ensure(job.get("feat_ref"), "PRECONDITION_FAILED", "feat_to_proto job missing feat_ref")
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-dev-feat-to-proto")
    with _prepend_sys_path(scripts_dir):
        from feat_to_proto import build_package, repo_root_from, validate_input_package

        errors, context = validate_input_package(input_ref, str(job["feat_ref"]), workspace_root)
        if errors:
            result = {"ok": False, "errors": errors, "input_path": input_ref}
        else:
            result = build_package(
                context,
                repo_root_from(str(workspace_root)),
                str(payload.get("downstream_run_id") or ""),
                True,
            )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_proto_to_ui(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-dev-proto-to-ui")
    with _prepend_sys_path(scripts_dir):
        from proto_to_ui import build_package, repo_root_from, validate_input_package

        errors, context = validate_input_package(input_ref)
        if errors:
            result = {"ok": False, "errors": errors, "input_path": input_ref}
        else:
            result = build_package(
                context,
                repo_root_from(str(workspace_root)),
                str(payload.get("downstream_run_id") or ""),
                True,
            )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_src_to_epic(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-product-src-to-epic")
    with _prepend_sys_path(scripts_dir):
        from src_to_epic_runtime import run_workflow

        result = run_workflow(
            input_path=input_ref,
            repo_root=workspace_root,
            run_id=str(payload.get("downstream_run_id") or ""),
            allow_update=True,
        )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_epic_to_feat(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-product-epic-to-feat")
    with _prepend_sys_path(scripts_dir):
        from epic_to_feat_runtime import run_workflow

        result = run_workflow(
            input_path=input_ref,
            repo_root=workspace_root,
            run_id=str(payload.get("downstream_run_id") or ""),
            allow_update=True,
        )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_feat_to_testset(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    ensure(job.get("feat_ref"), "PRECONDITION_FAILED", "feat_to_testset job missing feat_ref")
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-qa-feat-to-testset")
    with _prepend_sys_path(scripts_dir):
        from feat_to_testset_runtime import run_workflow

        result = run_workflow(
            input_path=input_ref,
            feat_ref=str(job["feat_ref"]),
            repo_root=workspace_root,
            run_id=str(payload.get("downstream_run_id") or ""),
            allow_update=True,
        )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_tech_to_impl(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    ensure(job.get("feat_ref"), "PRECONDITION_FAILED", "tech_to_impl job missing feat_ref")
    ensure(job.get("tech_ref"), "PRECONDITION_FAILED", "tech_to_impl job missing tech_ref")
    input_ref = _authoritative_input_ref(job)
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "ll-dev-tech-to-impl")
    with _prepend_sys_path(scripts_dir):
        from tech_to_impl_runtime import run_workflow

        result = run_workflow(
            input_path=input_ref,
            feat_ref=str(job["feat_ref"]),
            tech_ref=str(job["tech_ref"]),
            repo_root=workspace_root,
            run_id=str(payload.get("downstream_run_id") or ""),
            allow_update=True,
        )
    return {"ok": bool(result.get("ok", True)), "target_skill": job["target_skill"], "result": result}


def _invoke_test_exec(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    target_skill: str,
    job: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    from cli.lib.test_exec_runtime import execute_test_exec_skill

    environment_ref = str(payload.get("test_environment_ref") or job.get("test_environment_ref") or "").strip()
    ensure(environment_ref, "PRECONDITION_FAILED", f"{target_skill} requires test_environment_ref")
    action = "test-exec-cli" if target_skill.endswith("test_exec_cli") else "test-exec-web-e2e"
    test_set_ref = _authoritative_input_ref(job)
    ensure(test_set_ref, "PRECONDITION_FAILED", f"{target_skill} job missing test set input")
    result = execute_test_exec_skill(
        workspace_root=workspace_root,
        trace=trace,
        action=action,
        request_id=request_id,
        payload={
            "test_set_ref": test_set_ref,
            "test_environment_ref": environment_ref,
            "proposal_ref": str(payload.get("proposal_ref") or request_id),
        },
    )
    return {"ok": True, "target_skill": target_skill, "result": result}


def _authoritative_input_ref(job: dict[str, Any]) -> str:
    input_ref = str(job.get("authoritative_input_ref") or job.get("formal_ref") or job.get("published_ref") or "").strip()
    ensure(input_ref, "PRECONDITION_FAILED", f"{job.get('target_skill') or 'job'} missing authoritative input")
    return input_ref


def invoke_target(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    job: dict[str, Any],
    payload: dict[str, Any] | None = None,
    job_ref: str | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    target_skill = str(job.get("target_skill") or "").strip()
    ensure(target_skill, "PRECONDITION_FAILED", "job missing target_skill")
    try:
        if target_skill == "execution.return":
            return invoke_execution_return_job(workspace_root, trace, request_id, job_ref, job, payload)
        if target_skill == "workflow.product.src_to_epic":
            return _invoke_src_to_epic(workspace_root, job, payload)
        if target_skill == "workflow.product.epic_to_feat":
            return _invoke_epic_to_feat(workspace_root, job, payload)
        if target_skill == "workflow.dev.feat_to_ui":
            return _invoke_feat_to_ui(workspace_root, job, payload)
        if target_skill == "workflow.dev.feat_to_proto":
            return _invoke_feat_to_proto(workspace_root, job, payload)
        if target_skill == "workflow.dev.proto_to_ui":
            return _invoke_proto_to_ui(workspace_root, job, payload)
        if target_skill == "workflow.dev.feat_to_tech":
            return _invoke_feat_to_tech(workspace_root, job, payload)
        if target_skill == "workflow.qa.feat_to_testset":
            return _invoke_feat_to_testset(workspace_root, job, payload)
        if target_skill == "workflow.dev.tech_to_impl":
            return _invoke_tech_to_impl(workspace_root, job, payload)
        if target_skill in {"skill.qa.test_exec_cli", "skill.qa.test_exec_web_e2e"}:
            return _invoke_test_exec(workspace_root, trace, request_id, target_skill, job, payload)
    except CommandError:
        raise
    except (FileNotFoundError, ValueError) as exc:
        raise CommandError("PRECONDITION_FAILED", f"failed to invoke {target_skill}: {exc}") from exc
    except Exception as exc:
        raise CommandError("INTERNAL_ERROR", f"failed to invoke {target_skill}: {exc}") from exc
    raise CommandError("PRECONDITION_FAILED", f"unsupported target_skill: {target_skill}")
