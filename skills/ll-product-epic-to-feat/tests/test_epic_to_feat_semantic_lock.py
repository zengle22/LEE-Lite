from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from epic_to_feat_runtime import build_semantic_drift_check


class _Package:
    def __init__(self) -> None:
        self.epic_json = {
            "title": "IMPL 实施前文档压力测试与 Implementation Readiness 统一能力",
            "business_goal": "The EPIC freezes implementation readiness as a product capability before implementation start.",
        }
        self.epic_frontmatter = {
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
        feats=[
            {
                "title": "IMPL intake and authority binding",
                "goal": "Reviewers can judge readiness without re-reading the ADR.",
                "identity_and_scenario": {"product_interface": "implementation readiness intake"},
            },
            {
                "title": "Cross-artifact consistency review",
                "goal": "Detect conflicts before implementation starts.",
                "identity_and_scenario": {"product_interface": "cross-artifact review"},
            },
        ],
    )

    assert result["semantic_lock_present"] is True
    assert result["semantic_lock_preserved"] is True
    assert "implementation_readiness_signature" in result["anchor_matches"]

