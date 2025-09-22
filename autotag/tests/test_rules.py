from __future__ import annotations

from autotag.app.services.rules_engine import get_rules_engine


def test_top_up_rule_hits() -> None:
    engine = get_rules_engine()
    result = engine.apply_rules("please top up my wallet", "en")
    assert result["category"] == "top_up"
    assert any("cat_topup" in hit for hit in result["hits"])


def test_withdraw_rule_hits() -> None:
    engine = get_rules_engine()
    result = engine.apply_rules("can I withdraw cash from wallet?", "en")
    assert result["category"] == "withdraw"
    assert any("cat_withdraw" in hit for hit in result["hits"])
