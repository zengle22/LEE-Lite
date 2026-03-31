"""Shared revision-request helpers for governed workflow runtimes."""

from __future__ import annotations

from pathlib import Path
from textwrap import shorten
from typing import Any, Callable, Mapping

JsonLoad = Callable[[Path], dict[str, Any]]
JsonDump = Callable[[Path, dict[str, Any]], None]
EnsureList = Callable[[Any], list[Any]]
SummarizeText = Callable[[str, int], str]


def _normalize_ref(repo_root: Path | None, path: str | Path | None) -> str:
    if not path:
        return ""
    resolved = Path(path).resolve()
    if repo_root is None:
        return str(resolved)
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _ensure_list(values: Any, ensure_list: EnsureList | None) -> list[Any]:
    if ensure_list is not None:
        return ensure_list(values)
    if values is None:
        return []
    if isinstance(values, list):
        return values
    return [values]


def _shorten(text: str, limit: int, summarize_text: SummarizeText | None) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    if summarize_text is not None:
        return summarize_text(normalized, limit)
    return shorten(normalized, width=limit, placeholder="...")


def is_revision_context(payload: Any) -> bool:
    return isinstance(payload, dict) and "summary" in payload and "revision_request_ref" in payload


def build_revision_summary(
    revision_request: Mapping[str, Any] | None,
    *,
    summarize_text: SummarizeText | None = None,
    reason_limit: int = 180,
    output_limit: int = 220,
    prefix: str = "Gate revise",
) -> str:
    if not revision_request:
        return ""
    decision_target = _shorten(_normalize_text(revision_request.get("decision_target")), 80, summarize_text)
    decision_reason = _shorten(
        _normalize_text(revision_request.get("decision_reason") or revision_request.get("reason")),
        reason_limit,
        summarize_text,
    )
    revision_round = _normalize_text(revision_request.get("revision_round"))
    pieces = [piece for piece in [f"round {revision_round}" if revision_round else "", decision_target, decision_reason] if piece]
    summary = " | ".join(pieces) if pieces else "gate revise request"
    return _shorten(f"{prefix}: {summary}", output_limit, summarize_text)


def normalize_revision_context(
    revision_request: Mapping[str, Any] | None,
    *,
    revision_request_ref: str = "",
    revision_request_path: str | Path | None = None,
    repo_root: Path | None = None,
    ensure_list: EnsureList | None = None,
    summarize_text: SummarizeText | None = None,
    reason_limit: int = 180,
    output_limit: int = 220,
    prefix: str = "Gate revise",
) -> dict[str, Any]:
    if not revision_request:
        return {}
    if is_revision_context(revision_request) and not revision_request_ref and not revision_request_path:
        context = dict(revision_request)
        if not isinstance(context.get("trace"), dict):
            context["trace"] = {}
        if "basis_refs" in context:
            context["basis_refs"] = [
                _normalize_text(item)
                for item in _ensure_list(context.get("basis_refs"), ensure_list)
                if _normalize_text(item)
            ]
        if not _normalize_text(context.get("summary")):
            context["summary"] = build_revision_summary(
                context,
                summarize_text=summarize_text,
                reason_limit=reason_limit,
                output_limit=output_limit,
                prefix=prefix,
            )
        return context

    context_ref = revision_request_ref or _normalize_ref(repo_root, revision_request_path)
    return {
        "revision_request_ref": context_ref or _normalize_text(revision_request.get("revision_request_ref")),
        "workflow_key": _normalize_text(revision_request.get("workflow_key")),
        "run_id": _normalize_text(revision_request.get("run_id")),
        "source_run_id": _normalize_text(revision_request.get("source_run_id")),
        "decision_type": _normalize_text(revision_request.get("decision_type")),
        "decision_target": _normalize_text(revision_request.get("decision_target")),
        "decision_reason": _normalize_text(revision_request.get("decision_reason") or revision_request.get("reason")),
        "revision_round": revision_request.get("revision_round"),
        "basis_refs": [
            _normalize_text(item)
            for item in _ensure_list(revision_request.get("basis_refs"), ensure_list)
            if _normalize_text(item)
        ],
        "source_gate_decision_ref": _normalize_text(revision_request.get("source_gate_decision_ref")),
        "source_return_job_ref": _normalize_text(revision_request.get("source_return_job_ref")),
        "authoritative_input_ref": _normalize_text(revision_request.get("authoritative_input_ref")),
        "candidate_ref": _normalize_text(revision_request.get("candidate_ref")),
        "original_input_path": _normalize_text(revision_request.get("original_input_path")),
        "triggered_by_request_id": _normalize_text(revision_request.get("triggered_by_request_id")),
        "trace": revision_request.get("trace") if isinstance(revision_request.get("trace"), dict) else {},
        "summary": build_revision_summary(
            revision_request,
            summarize_text=summarize_text,
            reason_limit=reason_limit,
            output_limit=output_limit,
            prefix=prefix,
        ),
    }


def load_revision_request(
    revision_request_path: str | Path | None,
    *,
    artifacts_dir: Path | None,
    load_json: JsonLoad,
) -> tuple[dict[str, Any] | None, Path | None]:
    candidate_paths: list[Path] = []
    if revision_request_path:
        candidate_paths.append(Path(revision_request_path).resolve())
    if artifacts_dir is not None:
        candidate_paths.append((artifacts_dir / "revision-request.json").resolve())
    for candidate in candidate_paths:
        if candidate.exists():
            payload = load_json(candidate)
            if isinstance(payload, dict):
                return payload, candidate
    return None, None


def materialize_revision_request(
    artifacts_dir: Path,
    *,
    revision_request: dict[str, Any] | None = None,
    revision_request_path: str | Path | None = None,
    load_json: JsonLoad,
    dump_json: JsonDump,
    delete_if_missing: bool = False,
    increment_round: bool = False,
    default_round: int = 1,
) -> tuple[str, dict[str, Any], int]:
    target_path = (artifacts_dir / "revision-request.json").resolve()
    payload = dict(revision_request or {})
    if not payload and revision_request_path:
        source_path = Path(revision_request_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Revision request not found: {source_path}")
        loaded = load_json(source_path)
        if isinstance(loaded, dict):
            payload = dict(loaded)
    if not payload and target_path.exists() and not delete_if_missing:
        loaded = load_json(target_path)
        if isinstance(loaded, dict):
            payload = dict(loaded)
    if not payload:
        if delete_if_missing and target_path.exists():
            target_path.unlink()
        return "", {}, 0

    revision_round = int(payload.get("revision_round") or 0)
    if increment_round:
        previous_round = 0
        existing_payload: dict[str, Any] = {}
        if target_path.exists():
            existing_payload = load_json(target_path)
            previous_round = int(existing_payload.get("revision_round") or 0)
        current_without_round = {key: value for key, value in payload.items() if key != "revision_round"}
        existing_without_round = {key: value for key, value in existing_payload.items() if key != "revision_round"}
        if existing_without_round and current_without_round == existing_without_round:
            revision_round = previous_round or int(payload.get("revision_round") or default_round)
        else:
            revision_round = previous_round + 1 if previous_round else int(payload.get("revision_round") or default_round)
        payload["revision_round"] = revision_round

    dump_json(target_path, payload)
    return str(target_path), payload, revision_round
