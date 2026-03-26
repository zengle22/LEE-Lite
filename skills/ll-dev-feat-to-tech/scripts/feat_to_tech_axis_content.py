"""Axis-specific static content loaded from data assets."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    path = Path(__file__).with_name("feat_to_tech_axis_content.json")
    return json.loads(path.read_text(encoding="utf-8"))


def axis_content(axis: str, section: str) -> Any:
    return _content().get(axis, {}).get(section)
