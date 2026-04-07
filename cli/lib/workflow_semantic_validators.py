"""Small validation helpers for ADR-043 semantic coverage."""

from __future__ import annotations

from typing import Any


DEFAULT_PLACEHOLDERS = {
    "",
    "none",
    "tbd",
    "n/a",
    "unknown",
    "primary product actor",
    "secondary product actor",
}


def compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(compact_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(compact_text(item) for item in value.values())
    return str(value).strip()


def is_placeholder(value: Any, placeholders: set[str] | None = None) -> bool:
    text = compact_text(value).strip().lower()
    if not text:
        return True
    checks = placeholders or DEFAULT_PLACEHOLDERS
    return text in checks


def explicit_or_partial(*, explicit: bool, partial: bool = False, placeholder: bool = False, conflict: bool = False) -> str:
    if conflict:
        return "conflict"
    if placeholder:
        return "placeholder"
    if explicit:
        return "explicit"
    if partial:
        return "partial"
    return "missing"
