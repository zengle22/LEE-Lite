"""Patch schema definitions for the Experience Patch Layer (ADR-049)."""

from __future__ import annotations

from enum import Enum


class PatchStatus(str, Enum):
    """Lifecycle states for an experience patch."""

    draft = "draft"
    proposed = "proposed"
    approved = "approved"
    applied = "applied"
    rejected = "rejected"
    superseded = "superseded"


class ChangeClass(str, Enum):
    """Classification of the change type."""

    ui_flow = "ui_flow"
    copy_text = "copy_text"
    validation = "validation"
    navigation = "navigation"
    layout = "layout"
    interaction = "interaction"
    performance = "performance"
    accessibility = "accessibility"
    error_handling = "error_handling"
    data_display = "data_display"
    other = "other"
