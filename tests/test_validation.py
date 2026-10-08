from processing.validation import validate_record

GOOD = {"source": "Books to Scrape", "name_or_title": "x", "source_url": "https://a.com",
        "price": 1.0, "rating": 3}


def test_valid():
    assert validate_record(GOOD) == []


def test_each_rule():
    assert "unknown_source" in validate_record({**GOOD, "source": "Nope"})
    assert "missing_name" in validate_record({**GOOD, "name_or_title": None})
    assert "invalid_url" in validate_record({**GOOD, "source_url": "abc"})
    assert "invalid_price" in validate_record({**GOOD, "price": -1})
    assert "invalid_rating" in validate_record({**GOOD, "rating": 9})
    assert "missing_price" in validate_record({**GOOD, "price": None})
