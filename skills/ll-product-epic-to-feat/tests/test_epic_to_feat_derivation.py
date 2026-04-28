from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from epic_to_feat_derivation import derive_feat_axes


@dataclass
class _MockPackage:
    epic_json: dict[str, Any]
    epic_frontmatter: dict[str, Any] = None

    def __post_init__(self):
        if self.epic_frontmatter is None:
            self.epic_frontmatter = {}


def test_derive_feat_axes_prioritizes_capability_axes() -> None:
    """
    Test that derive_feat_axes uses capability_axes as the first option for feat_axis
    when both capability_axes and product_surface are present.
    """
    package = _MockPackage(
        epic_json={
            "product_behavior_slices": [
                {
                    "id": "slice-1",
                    "name": "Some UI feature",
                    "product_surface": "Product Dashboard UI",
                    "capability_axes": ["User Authentication Capability"],
                    "scope": ["auth flow"],
                }
            ]
        }
    )

    axes = derive_feat_axes(package)

    assert len(axes) == 1
    assert axes[0]["feat_axis"] == "User Authentication Capability"
    # product_surface should still be present for downstream use
    assert axes[0]["product_surface"] == "Product Dashboard UI"
    assert axes[0]["capability_axes"] == ["User Authentication Capability"]


def test_derive_feat_axes_falls_back_correctly() -> None:
    """
    Test that derive_feat_axes falls back correctly when capability_axes is not present:
    capability_axes → name → product_surface → default.
    """
    # Case 1: No capability_axes, has name and product_surface
    package1 = _MockPackage(
        epic_json={
            "product_behavior_slices": [
                {
                    "name": "Feature Name",
                    "product_surface": "Product Surface",
                }
            ]
        }
    )
    axes1 = derive_feat_axes(package1)
    assert axes1[0]["feat_axis"] == "Feature Name"

    # Case 2: No capability_axes and no name, has product_surface
    package2 = _MockPackage(
        epic_json={
            "product_behavior_slices": [
                {
                    "product_surface": "Product Surface",
                }
            ]
        }
    )
    axes2 = derive_feat_axes(package2)
    assert axes2[0]["feat_axis"] == "Product Surface"

    # Case 3: No capability_axes, name, or product_surface - uses default
    package3 = _MockPackage(
        epic_json={
            "product_behavior_slices": [{}]
        }
    )
    axes3 = derive_feat_axes(package3)
    assert axes3[0]["feat_axis"] == "Feature Slice 1"


def test_derive_feat_axes_appends_skill_adoption_e2e() -> None:
    """
    Test that the skill-adoption-e2e axis is still appended correctly when required.
    """
    package = _MockPackage(
        epic_json={
            "rollout_requirement": {"required": True},
            "rollout_plan": {"required_feat_tracks": ["adoption_e2e"]},
            "product_behavior_slices": [
                {"name": "Feature 1", "capability_axes": ["Capability 1"]}
            ],
        }
    )

    axes = derive_feat_axes(package)

    assert len(axes) == 2
    assert axes[0]["feat_axis"] == "Capability 1"
    assert axes[1]["id"] == "skill-adoption-e2e"


def test_derive_feat_axes_uses_top_level_capability_axes() -> None:
    """
    Test that derive_feat_axes still handles top-level capability_axes correctly
    when product_behavior_slices is not present.
    """
    package = _MockPackage(
        epic_json={
            "capability_axes": [
                {
                    "id": "axis-1",
                    "name": "Top-Level Capability",
                    "scope": "Some scope",
                    "feat_axis": "Top-Level Axis",
                }
            ]
        }
    )

    axes = derive_feat_axes(package)

    assert len(axes) == 1
    assert axes[0]["feat_axis"] == "Top-Level Axis"
    assert axes[0]["name"] == "Top-Level Capability"


def test_derive_feat_axes_multiple_capability_axes_items() -> None:
    """
    Test that when capability_axes has multiple items, we just take the first one.
    """
    package = _MockPackage(
        epic_json={
            "product_behavior_slices": [
                {
                    "capability_axes": ["Primary Capability", "Secondary Capability"],
                    "name": "Feature",
                }
            ]
        }
    )

    axes = derive_feat_axes(package)

    assert len(axes) == 1
    assert axes[0]["feat_axis"] == "Primary Capability"
    # Both should still be stored in capability_axes field
    assert axes[0]["capability_axes"] == ["Primary Capability", "Secondary Capability"]


def test_derive_feat_axes_capability_axes_string_fallback() -> None:
    """
    Test that when capability_axes is a string instead of a list, ensure_list handles it.
    """
    package = _MockPackage(
        epic_json={
            "product_behavior_slices": [
                {
                    "capability_axes": "Single String Capability",
                    "name": "Feature",
                }
            ]
        }
    )

    axes = derive_feat_axes(package)

    assert len(axes) == 1
    assert axes[0]["feat_axis"] == "Single String Capability"
    assert axes[0]["capability_axes"] == ["Single String Capability"]
