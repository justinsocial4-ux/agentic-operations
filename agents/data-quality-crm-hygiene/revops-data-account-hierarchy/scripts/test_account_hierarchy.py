from __future__ import annotations

import unittest

from account_hierarchy import (
    build_forest,
    check_cycle,
    company_name_signal,
    confidence_score,
    confidence_tier,
    jaro_winkler,
    normalize_name,
)


class AccountHierarchyTests(unittest.TestCase):
    def test_name_normalization_removes_legal_suffix_but_keeps_region(self) -> None:
        self.assertEqual(normalize_name("  Acme EMEA, GmbH  "), "acme emea")

    def test_name_signal_preserves_prefix_rule(self) -> None:
        result = company_name_signal("Acme Corp", "Acme EMEA")
        self.assertEqual(result["signal"], 0.95)
        self.assertEqual(result["method"], "parent_name_contained_in_child")
        self.assertGreater(jaro_winkler("Acme Corp", "Acme Corporation"), 0.99)

    def test_literal_non_renormalized_acme_score(self) -> None:
        result = confidence_score(email=0, duns=0, name=0.95, domain=0.88)
        self.assertEqual(result["raw_score"], 32.2)
        self.assertEqual(result["score"], 32.2)
        self.assertEqual(result["tier"], "discard")
        self.assertEqual(result["weight_total"], 1.05)
        self.assertFalse(result["renormalized"])

    def test_score_caps_at_100_without_renormalizing(self) -> None:
        result = confidence_score(email=1, duns=1, name=1, domain=1)
        self.assertEqual(result["raw_score"], 105.0)
        self.assertEqual(result["score"], 100.0)

    def test_manual_override_has_highest_precedence(self) -> None:
        result = confidence_score(email=0, duns=0, name=0, domain=0, manual_override=True)
        self.assertEqual(result["score"], 100.0)
        self.assertTrue(result["manual_override"])

    def test_tiers_match_pilot(self) -> None:
        self.assertEqual(confidence_tier(95), "auto_link_pending_approval")
        self.assertEqual(confidence_tier(85), "review_recommended")
        self.assertEqual(confidence_tier(70), "manual_review_required")
        self.assertEqual(confidence_tier(69.99), "discard")

    def test_cycle_detection_passes_valid_chain_and_rejects_loop(self) -> None:
        valid = check_cycle({"Acme Corp": None}, "Acme EMEA", "Acme Corp")
        self.assertFalse(valid["circular"])
        self.assertEqual(valid["depth"], 1)
        loop = check_cycle({"Acme Corp": "Acme EMEA"}, "Acme EMEA", "Acme Corp")
        self.assertTrue(loop["circular"])
        self.assertEqual(loop["reason"], "loop_detected")

    def test_cycle_detection_rejects_self_reference_and_depth(self) -> None:
        self.assertEqual(check_cycle({}, "A", "A")["reason"], "self_reference")
        links = {f"n{index}": f"n{index + 1}" for index in range(11)}
        links["n11"] = None
        result = check_cycle(links, "root_child", "n0", max_depth=10)
        self.assertEqual(result["reason"], "depth_exceeded")

    def test_tree_construction_is_stable(self) -> None:
        forest = build_forest({"Acme EMEA": "Acme Corp", "Acme Labs": "Acme Corp", "Acme Corp": None})
        self.assertEqual(forest[0]["account"], "Acme Corp")
        self.assertEqual(
            [child["account"] for child in forest[0]["children"]],
            ["Acme EMEA", "Acme Labs"],
        )


if __name__ == "__main__":
    unittest.main()
