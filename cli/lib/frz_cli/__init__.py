"""LL v2 SSOT models, exceptions, and shared utilities.

Truth source: ADR-056 §6–7 (SSOT v2 schema, FRZ Package format).
"""

from __future__ import annotations

from frz_cli.exceptions import (
    AlignmentFailError,
    CompletenessBlockedError,
    CompileConflictError,
    ConvergenceTimeoutError,
    DriftDetectedError,
    FreezeGuardBlockedError,
    FrozenObjectError,
    ImplVerifyFailError,
    InventedSemanticsError,
    LLCompilerError,
    V1SkillFailureError,
    V1SkillTimeoutError,
)
from frz_cli.models import (
    API,
    ARCH,
    EPIC,
    FEAT,
    FRZPackageV2,
    IMPL,
    SRC,
    TECH,
    UI,
    AlignmentVerdict,
    CompletenessVerdict,
    DriftVerdict,
    FreezeStatus,
    VerificationReport,
)

__all__ = [
    "LLCompilerError",
    "FrozenObjectError",
    "FreezeGuardBlockedError",
    "CompletenessBlockedError",
    "CompileConflictError",
    "InventedSemanticsError",
    "AlignmentFailError",
    "DriftDetectedError",
    "V1SkillTimeoutError",
    "V1SkillFailureError",
    "ImplVerifyFailError",
    "ConvergenceTimeoutError",
    "FreezeStatus",
    "SRC",
    "EPIC",
    "FEAT",
    "TECH",
    "ARCH",
    "API",
    "UI",
    "IMPL",
    "FRZPackageV2",
    "CompletenessVerdict",
    "AlignmentVerdict",
    "DriftVerdict",
    "VerificationReport",
]
