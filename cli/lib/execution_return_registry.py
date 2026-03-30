"""Registry and helpers for execution.return routing."""

from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import load_json, write_json


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


@dataclass(frozen=True)
class ExecutionReturnRoute:
    workflow_key: str
    artifacts_subdir: str
    scripts_subdir: str
    runtime_module: str
    candidate_ref_patterns: tuple[re.Pattern[str], ...]
    build_runtime_kwargs: Callable[["ExecutionReturnContext"], dict[str, Any]]
    authoritative_ref_patterns: tuple[re.Pattern[str], ...] = ()

    def matches(self, ref_value: str, *, authoritative: bool = False) -> re.Match[str] | None:
        candidate = str(ref_value or "").strip()
        if not candidate:
            return None
        patterns = self.authoritative_ref_patterns if authoritative else self.candidate_ref_patterns
        for pattern in patterns:
            match = pattern.fullmatch(candidate)
            if match:
                return match
        return None

    def invoke(self, context: "ExecutionReturnContext") -> dict[str, Any]:
        runtime_kwargs = self.build_runtime_kwargs(context)
        scripts_dir = context.workspace_root / "skills" / self.scripts_subdir / "scripts"
        with _prepend_sys_path(scripts_dir):
            runtime_module = __import__(self.runtime_module, fromlist=["run_workflow"])
            run_workflow = getattr(runtime_module, "run_workflow")
            result = run_workflow(**runtime_kwargs)
        return {"ok": bool(result.get("ok", True)), "target_skill": "execution.return", "result": result}


@dataclass(frozen=True)
class ExecutionReturnRouteResolution:
    route: ExecutionReturnRoute
    matched_field: str
    matched_ref: str
    candidate_match: re.Match[str]

    @property
    def source_run_id(self) -> str:
        groupdict = self.candidate_match.groupdict()
        run_id = str(groupdict.get("run_id") or "").strip()
        if run_id:
            return run_id
        if self.candidate_match.lastindex:
            return str(self.candidate_match.group(1) or "").strip()
        return ""


@dataclass(frozen=True)
class ExecutionReturnContext:
    workspace_root: Path
    trace: dict[str, Any]
    request_id: str
    job_ref: str | None
    job: dict[str, Any]
    payload: dict[str, Any]
    decision_ref: str
    decision: dict[str, Any]
    resolution: ExecutionReturnRouteResolution
    source_artifacts_dir: Path
    execution_evidence_path: Path
    input_path: Path
    revision_request_path: Path
    revision_request: dict[str, Any]
    revision_round: int

    @property
    def route(self) -> ExecutionReturnRoute:
        return self.resolution.route

    @property
    def workflow_key(self) -> str:
        return self.route.workflow_key

    @property
    def candidate_ref(self) -> str:
        return self.resolution.matched_ref

    @property
    def source_run_id(self) -> str:
        return self.resolution.source_run_id


_EXECUTION_RETURN_ROUTES: list[ExecutionReturnRoute] = []


def register_execution_return_route(route: ExecutionReturnRoute) -> ExecutionReturnRoute:
    _EXECUTION_RETURN_ROUTES.append(route)
    return route


def execution_return_routes() -> tuple[ExecutionReturnRoute, ...]:
    return tuple(_EXECUTION_RETURN_ROUTES)


def _load_execution_return_decision(workspace_root: Path, job: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    decision_ref = str(job.get("gate_decision_ref") or "").strip()
    ensure(decision_ref, "PRECONDITION_FAILED", "execution.return job missing gate_decision_ref")
    decision_path = Path(decision_ref)
    if not decision_path.is_absolute():
        decision_path = workspace_root / decision_ref
    ensure(decision_path.exists(), "PRECONDITION_FAILED", f"execution.return gate decision missing: {decision_path}")
    return decision_ref, load_json(decision_path)


def _execution_return_candidate_refs(job: dict[str, Any], decision: dict[str, Any]) -> list[tuple[str, str]]:
    refs = [
        ("candidate_ref", str(decision.get("candidate_ref") or "").strip()),
        ("decision_target", str(decision.get("decision_target") or "").strip()),
        ("authoritative_input_ref", str(job.get("authoritative_input_ref") or "").strip()),
        ("payload_ref", str(job.get("payload_ref") or "").strip()),
        ("job_decision_target", str(job.get("decision_target") or "").strip()),
    ]
    seen: set[str] = set()
    ordered: list[tuple[str, str]] = []
    for field, ref in refs:
        if not ref or ref in seen:
            continue
        seen.add(ref)
        ordered.append((field, ref))
    return ordered


def resolve_execution_return_route(job: dict[str, Any], decision: dict[str, Any]) -> ExecutionReturnRouteResolution:
    candidate_refs = _execution_return_candidate_refs(job, decision)
    for route in _EXECUTION_RETURN_ROUTES:
        for field, ref in candidate_refs:
            authoritative = field in {"authoritative_input_ref", "payload_ref"}
            match = route.matches(ref, authoritative=authoritative)
            if match:
                return ExecutionReturnRouteResolution(route=route, matched_field=field, matched_ref=ref, candidate_match=match)
    ref_debug = ", ".join(f"{field}={ref}" for field, ref in candidate_refs) or "<empty>"
    raise CommandError("REGISTRY_MISS", f"no execution.return route registered for {ref_debug}")


def _execution_return_source_input_path(workspace_root: Path, source_artifacts_dir: Path, execution_evidence_path: Path) -> Path:
    ensure(execution_evidence_path.exists(), "PRECONDITION_FAILED", f"execution.return source evidence missing: {execution_evidence_path}")
    execution = load_json(execution_evidence_path)
    input_path_value = str(execution.get("input_path") or "").strip()
    ensure(input_path_value, "PRECONDITION_FAILED", f"execution.return source input missing: {execution_evidence_path}")
    input_path = Path(input_path_value)
    if not input_path.is_absolute():
        input_path = workspace_root / input_path
    return input_path


def _load_output_json(source_artifacts_dir: Path, filename: str) -> dict[str, Any]:
    path = source_artifacts_dir / filename
    ensure(path.exists(), "PRECONDITION_FAILED", f"execution.return source artifact missing: {path}")
    payload = load_json(path)
    ensure(isinstance(payload, dict), "PRECONDITION_FAILED", f"execution.return source artifact must be an object: {path}")
    return payload


def _load_package_manifest(source_artifacts_dir: Path) -> dict[str, Any]:
    return _load_output_json(source_artifacts_dir, "package-manifest.json")


def _manifest_or_bundle_value(source_artifacts_dir: Path, *, key: str, bundle_filename: str) -> str:
    manifest = _load_package_manifest(source_artifacts_dir)
    value = str(manifest.get(key) or "").strip()
    if value:
        return value
    bundle = _load_output_json(source_artifacts_dir, bundle_filename)
    value = str(bundle.get(key) or "").strip()
    ensure(value, "PRECONDITION_FAILED", f"execution.return source artifact missing {key}: {source_artifacts_dir / bundle_filename}")
    return value


def _execution_return_source_run_id(job: dict[str, Any], resolution: ExecutionReturnRouteResolution) -> str:
    source_run_id = str(job.get("source_run_id") or "").strip()
    if source_run_id:
        return source_run_id
    source_run_id = resolution.source_run_id
    ensure(source_run_id, "PRECONDITION_FAILED", "execution.return job missing source_run_id")
    return source_run_id


def _build_revision_request(
    *,
    trace: dict[str, Any],
    request_id: str,
    job_ref: str | None,
    job: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
    resolution: ExecutionReturnRouteResolution,
    source_run_id: str,
    source_artifacts_dir: Path,
    execution_evidence_path: Path,
    input_path: Path,
) -> tuple[dict[str, Any], Path, int]:
    revision_request_path = source_artifacts_dir / "revision-request.json"
    revision_round = 1
    if revision_request_path.exists():
        previous_revision = load_json(revision_request_path)
        revision_round = int(previous_revision.get("revision_round") or 0) + 1
    candidate_ref = resolution.matched_ref
    revision_request = {
        "workflow_key": resolution.route.workflow_key,
        "run_id": source_run_id,
        "source_run_id": source_run_id,
        "decision_type": str(decision.get("decision_type") or job.get("decision_type") or "revise"),
        "decision_reason": str(decision.get("decision_reason") or job.get("reason") or "gate requested execution-side revision before resubmission"),
        "decision_target": str(decision.get("decision_target") or candidate_ref),
        "basis_refs": [
            ref
            for ref in [
                decision_ref,
                *[str(item).strip() for item in (decision.get("decision_basis_refs") or [])],
                str(job.get("authoritative_input_ref") or "").strip(),
            ]
            if ref
        ],
        "revision_round": revision_round,
        "source_gate_decision_ref": decision_ref,
        "source_return_job_ref": str(job_ref or job.get("job_ref") or ""),
        "authoritative_input_ref": str(job.get("authoritative_input_ref") or candidate_ref),
        "candidate_ref": candidate_ref,
        "matched_field": resolution.matched_field,
        "original_input_path": str(input_path),
        "triggered_by_request_id": request_id,
        "execution_evidence_ref": str(execution_evidence_path),
        "trace": trace,
    }
    return revision_request, revision_request_path, revision_round


def _materialize_revision_request(
    *,
    workspace_root: Path,
    trace: dict[str, Any],
    payload: dict[str, Any],
    request_id: str,
    job_ref: str | None,
    job: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
    resolution: ExecutionReturnRouteResolution,
) -> ExecutionReturnContext:
    source_run_id = _execution_return_source_run_id(job, resolution)
    source_artifacts_dir = workspace_root / "artifacts" / resolution.route.artifacts_subdir / source_run_id
    execution_evidence_path = source_artifacts_dir / "execution-evidence.json"
    input_path = _execution_return_source_input_path(workspace_root, source_artifacts_dir, execution_evidence_path)
    revision_request, revision_request_path, revision_round = _build_revision_request(
        trace=trace,
        request_id=request_id,
        job_ref=job_ref,
        job=job,
        decision_ref=decision_ref,
        decision=decision,
        resolution=resolution,
        source_run_id=source_run_id,
        source_artifacts_dir=source_artifacts_dir,
        execution_evidence_path=execution_evidence_path,
        input_path=input_path,
    )
    write_json(revision_request_path, revision_request)
    return ExecutionReturnContext(
        workspace_root=workspace_root,
        trace=trace,
        request_id=request_id,
        job_ref=job_ref,
        job=job,
        payload=payload,
        decision_ref=decision_ref,
        decision=decision,
        resolution=resolution,
        source_artifacts_dir=source_artifacts_dir,
        execution_evidence_path=execution_evidence_path,
        input_path=input_path,
        revision_request_path=revision_request_path,
        revision_request=revision_request,
        revision_round=revision_round,
    )


def _raw_to_src_build_runtime_kwargs(context: ExecutionReturnContext) -> dict[str, Any]:
    return {
        "input_path": str(context.input_path),
        "repo_root": context.workspace_root,
        "run_id": context.source_run_id,
        "allow_update": True,
        "revision_request_path": context.revision_request_path,
    }


def _src_to_epic_build_runtime_kwargs(context: ExecutionReturnContext) -> dict[str, Any]:
    return {
        "input_path": str(context.input_path),
        "repo_root": context.workspace_root,
        "run_id": context.source_run_id,
        "allow_update": True,
        "revision_request_path": context.revision_request_path,
    }


def _epic_to_feat_build_runtime_kwargs(context: ExecutionReturnContext) -> dict[str, Any]:
    return {
        "input_path": str(context.input_path),
        "repo_root": context.workspace_root,
        "run_id": context.source_run_id,
        "allow_update": True,
        "revision_request_path": context.revision_request_path,
    }


def _feat_to_tech_build_runtime_kwargs(context: ExecutionReturnContext) -> dict[str, Any]:
    feat_ref = _manifest_or_bundle_value(context.source_artifacts_dir, key="feat_ref", bundle_filename="tech-design-bundle.json")
    return {
        "input_path": str(context.input_path),
        "feat_ref": feat_ref,
        "repo_root": context.workspace_root,
        "run_id": context.source_run_id,
        "allow_update": True,
        "revision_request_path": context.revision_request_path,
    }


def _feat_to_testset_build_runtime_kwargs(context: ExecutionReturnContext) -> dict[str, Any]:
    feat_ref = _manifest_or_bundle_value(context.source_artifacts_dir, key="feat_ref", bundle_filename="test-set-bundle.json")
    return {
        "input_path": str(context.input_path),
        "feat_ref": feat_ref,
        "repo_root": context.workspace_root,
        "run_id": context.source_run_id,
        "allow_update": True,
        "revision_request_path": context.revision_request_path,
    }


def _tech_to_impl_build_runtime_kwargs(context: ExecutionReturnContext) -> dict[str, Any]:
    feat_ref = _manifest_or_bundle_value(context.source_artifacts_dir, key="feat_ref", bundle_filename="impl-bundle.json")
    tech_ref = _manifest_or_bundle_value(context.source_artifacts_dir, key="tech_ref", bundle_filename="impl-bundle.json")
    return {
        "input_path": str(context.input_path),
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "repo_root": context.workspace_root,
        "run_id": context.source_run_id,
        "allow_update": True,
        "revision_request_path": context.revision_request_path,
    }


register_execution_return_route(
    ExecutionReturnRoute(
        workflow_key="product.raw-to-src",
        artifacts_subdir="raw-to-src",
        scripts_subdir="ll-product-raw-to-src",
        runtime_module="raw_to_src_runtime",
        candidate_ref_patterns=(re.compile(r"^raw-to-src\.(?P<run_id>.+)\.src-candidate$"),),
        authoritative_ref_patterns=(re.compile(r"^raw-to-src\.(?P<run_id>.+)\.src-candidate$"),),
        build_runtime_kwargs=_raw_to_src_build_runtime_kwargs,
    )
)

register_execution_return_route(
    ExecutionReturnRoute(
        workflow_key="product.src-to-epic",
        artifacts_subdir="src-to-epic",
        scripts_subdir="ll-product-src-to-epic",
        runtime_module="src_to_epic_runtime",
        candidate_ref_patterns=(re.compile(r"^src-to-epic\.(?P<run_id>.+)\.epic-freeze$"),),
        authoritative_ref_patterns=(re.compile(r"^formal\.src\.(?P<run_id>.+)$"),),
        build_runtime_kwargs=_src_to_epic_build_runtime_kwargs,
    )
)

register_execution_return_route(
    ExecutionReturnRoute(
        workflow_key="product.epic-to-feat",
        artifacts_subdir="epic-to-feat",
        scripts_subdir="ll-product-epic-to-feat",
        runtime_module="epic_to_feat_runtime",
        candidate_ref_patterns=(re.compile(r"^epic-to-feat\.(?P<run_id>.+)\.feat-freeze-bundle$"),),
        authoritative_ref_patterns=(re.compile(r"^formal\.epic\.(?P<run_id>.+)$"),),
        build_runtime_kwargs=_epic_to_feat_build_runtime_kwargs,
    )
)

register_execution_return_route(
    ExecutionReturnRoute(
        workflow_key="dev.feat-to-tech",
        artifacts_subdir="feat-to-tech",
        scripts_subdir="ll-dev-feat-to-tech",
        runtime_module="feat_to_tech_runtime",
        candidate_ref_patterns=(re.compile(r"^feat-to-tech\.(?P<run_id>.+)\.tech-design-bundle$"),),
        authoritative_ref_patterns=(re.compile(r"^formal\.feat\.(?P<run_id>.+)$"),),
        build_runtime_kwargs=_feat_to_tech_build_runtime_kwargs,
    )
)

register_execution_return_route(
    ExecutionReturnRoute(
        workflow_key="qa.feat-to-testset",
        artifacts_subdir="feat-to-testset",
        scripts_subdir="ll-qa-feat-to-testset",
        runtime_module="feat_to_testset_runtime",
        candidate_ref_patterns=(re.compile(r"^feat-to-testset\.(?P<run_id>.+)\.test-set-bundle$"),),
        authoritative_ref_patterns=(re.compile(r"^formal\.feat\.(?P<run_id>.+)$"),),
        build_runtime_kwargs=_feat_to_testset_build_runtime_kwargs,
    )
)

register_execution_return_route(
    ExecutionReturnRoute(
        workflow_key="dev.tech-to-impl",
        artifacts_subdir="tech-to-impl",
        scripts_subdir="ll-dev-tech-to-impl",
        runtime_module="tech_to_impl_runtime",
        candidate_ref_patterns=(re.compile(r"^tech-to-impl\.(?P<run_id>.+)\.impl-bundle$"),),
        authoritative_ref_patterns=(re.compile(r"^formal\.tech\.(?P<run_id>.+)$"),),
        build_runtime_kwargs=_tech_to_impl_build_runtime_kwargs,
    )
)


def invoke_execution_return_job(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    job_ref: str | None,
    job: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    decision_ref, decision = _load_execution_return_decision(workspace_root, job)
    resolution = resolve_execution_return_route(job, decision)
    context = _materialize_revision_request(
        workspace_root=workspace_root,
        trace=trace,
        payload=payload,
        request_id=request_id,
        job_ref=job_ref,
        job=job,
        decision_ref=decision_ref,
        decision=decision,
        resolution=resolution,
    )
    result = resolution.route.invoke(context)
    return {
        **result,
        "workflow_key": resolution.route.workflow_key,
        "revision_request_ref": str(context.revision_request_path),
        "source_run_id": context.source_run_id,
        "matched_field": resolution.matched_field,
        "matched_ref": resolution.matched_ref,
    }
