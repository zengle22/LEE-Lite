"""LL v2 compiler and verification exception hierarchy.

Truth source: design.md §Error Handling & Recovery.
"""

from __future__ import annotations


class LLCompilerError(Exception):
    """Base exception for LL v2 compile and verify operations."""

    error_code: str = "E0000"
    step: str = "unknown"
    recoverable: bool = False

    def __init__(self, message: str, step: str = "unknown", recoverable: bool = False) -> None:
        super().__init__(message)
        self.step = step
        self.recoverable = recoverable


class FrozenObjectError(LLCompilerError):
    """Raised when an attempt is made to modify a frozen object."""

    error_code = "E0601"

    def __init__(self, message: str = "Object is frozen and cannot be modified") -> None:
        super().__init__(message, step="freeze", recoverable=False)


class FreezeGuardBlockedError(LLCompilerError):
    """Raised when Freeze Guard intercepts a silent modification."""

    error_code = "E0602"

    def __init__(self, message: str = "Freeze Guard blocked modification") -> None:
        super().__init__(message, step="freeze", recoverable=False)


class CompletenessBlockedError(LLCompilerError):
    """Raised when step_1 completeness check fails."""

    error_code = "E0101"

    def __init__(self, message: str, missing_items: list[dict] | None = None) -> None:
        super().__init__(message, step="completeness", recoverable=True)
        self.missing_items = missing_items or []


class CompileConflictError(LLCompilerError):
    """Raised when step_2 SSOT chain has internal conflicts."""

    error_code = "E0201"

    def __init__(self, message: str) -> None:
        super().__init__(message, step="compile", recoverable=True)


class InventedSemanticsError(LLCompilerError):
    """Raised when compiled output contains untraceable semantics."""

    error_code = "E0202"

    def __init__(self, message: str, invented_fields: list[str] | None = None) -> None:
        super().__init__(message, step="compile", recoverable=True)
        self.invented_fields = invented_fields or []


class AlignmentFailError(LLCompilerError):
    """Raised when step_3 alignment check fails."""

    error_code = "E0301"

    def __init__(self, message: str, issues: list[dict] | None = None) -> None:
        super().__init__(message, step="alignment", recoverable=True)
        self.issues = issues or []


class DriftDetectedError(LLCompilerError):
    """Raised when step_4 drift detection finds semantic drift."""

    error_code = "E0401"

    def __init__(self, message: str, drift_items: list[dict] | None = None) -> None:
        super().__init__(message, step="drift", recoverable=True)
        self.drift_items = drift_items or []


class V1SkillTimeoutError(LLCompilerError):
    """Raised when v1 test_generation times out."""

    error_code = "E0501"

    def __init__(self, message: str = "v1 Skill call timed out") -> None:
        super().__init__(message, step="test_generation", recoverable=True)


class V1SkillFailureError(LLCompilerError):
    """Raised when v1 test_generation execution fails."""

    error_code = "E0502"

    def __init__(self, message: str = "v1 Skill execution failed") -> None:
        super().__init__(message, step="test_generation", recoverable=True)


class ImplVerifyFailError(LLCompilerError):
    """Raised when impl-verify comprehensive verdict is fail."""

    error_code = "E1001"

    def __init__(self, message: str, report: dict | None = None) -> None:
        super().__init__(message, step="impl_verify", recoverable=True)
        self.report = report or {}


class ConvergenceTimeoutError(LLCompilerError):
    """Raised when dual-line convergence times out."""

    error_code = "E2001"

    def __init__(self, message: str = "Convergence timed out") -> None:
        super().__init__(message, step="convergence", recoverable=True)
