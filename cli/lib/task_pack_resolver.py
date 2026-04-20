"""Task Pack dependency resolution module (PACK-02). Stub for Wave 0."""
from __future__ import annotations


class TaskPackResolverError(ValueError):
    pass


def resolve_order(pack_data: dict) -> list[str]:
    raise NotImplementedError
