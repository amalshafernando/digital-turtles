from app.services.priority import score_priority


def test_priority_rules():
    assert score_priority("Thanks, just a question about sizes", "ORDER") == "low"
    assert score_priority("where is my refund", "REFUND") == "medium"
    assert score_priority("URGENT I was charged twice!!!", "PAYMENT") == "high"
