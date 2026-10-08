from processing.cleaning import (clean_price, clean_rating, clean_tags, clean_text,
                                 normalize_url, strip_quotes, clean_book, clean_quote)


def test_clean_text():
    assert clean_text("  Hello \n\xa0 World ") == "Hello World"
    assert clean_text("   ") is None and clean_text(None) is None


def test_price_rating():
    assert clean_price("£51.77") == 51.77
    assert clean_price("Â£1,051.77") == 1051.77
    assert clean_price(None) is None and clean_price("free") is None
    assert clean_rating("star-rating Three") == 3 and clean_rating("star-rating") is None


def test_quotes_tags_url():
    assert strip_quotes("\u201cThe world.\u201d") == "The world."
    assert clean_tags(["Love", " books", "love"]) == "books;love"
    assert clean_tags([]) is None
    assert normalize_url("catalogue/x.html", "https://books.toscrape.com/") == "https://books.toscrape.com/catalogue/x.html"
    assert normalize_url("ftp://x") is None


def test_clean_records_use_null_not_fake_values():
    b = clean_book({"title": " A  Book ", "source_url": "https://books.toscrape.com/a", "price_raw": "£5.00",
                    "rating_raw": "star-rating Two", "scraped_at": "t"})
    assert b["author"] is None and b["tags"] is None and b["price"] == 5.0 and b["rating"] == 2
    q = clean_quote({"text": "\u201cHi\u201d", "author": " Ann ", "tags": ["x"], "source_url": "https://quotes.toscrape.com/"})
    assert q["price"] is None and q["rating"] is None and q["author"] == "Ann"
