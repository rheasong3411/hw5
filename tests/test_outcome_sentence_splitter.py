from backend.main import _split_outcome_sentences


def test_outcome_splitter_preserves_decimals_and_abbreviations():
    text = "Cost is $52.20 at 1.25 units, i.e. the price from Acme Co. Confirm it. Next step."

    assert _split_outcome_sentences(text) == [
        "Cost is $52.20 at 1.25 units, i.e. the price from Acme Co. Confirm it.",
        "Next step.",
    ]
