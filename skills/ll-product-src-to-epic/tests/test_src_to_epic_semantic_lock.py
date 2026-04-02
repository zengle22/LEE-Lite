from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src_to_epic_runtime import build_semantic_drift_check


class _Package:
    def __init__(self) -> None:
        self.src_candidate = {
            "semantic_lock": {
                "domain_type": "implementation_readiness_rule",
                "one_sentence_truth": "Only test IMPL readiness before implementation start.",
                "primary_object": "qa.impl-spec-test",
                "lifecycle_stage": "pre_implementation_gate",
                "allowed_capabilities": [
                    "impl_readiness_testing",
                    "score_to_verdict_decision_support",
                ],
                "forbidden_capabilities": [
                    "new_business_truth_authoring",
                    "second_layer_tech_design",
                ],
                "inheritance_rule": "IMPL remains the main tested object.",
            }
        }


def test_build_semantic_drift_check_accepts_implementation_readiness_anchor() -> None:
    package = _Package()

    result = build_semantic_drift_check(
        package,
        epic_title="Implementation readiness testing capability",
        business_goal="Ensure implementation readiness before implementation start with stable verdict output.",
        scope=[
            "pre implementation gate review",
            "IMPL readiness assessment and verdict production",
            "cross artifact conflict detection",
        ],
        product_behavior_slices=[
            {
                "name": "impl spec testing flow",
                "goal": "Reviewers can judge readiness without re-reading the ADR.",
            }
        ],
    )

    assert result["semantic_lock_present"] is True
    assert result["semantic_lock_preserved"] is True
    assert "domain_type" in result["anchor_matches"]
