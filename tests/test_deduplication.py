from processing.deduplication import find_duplicates


def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None}
    recs = [{**base, "name_or_title": "Example Book Title"},
            {**base, "name_or_title": "  Example Book Title "},
            {**base, "name_or_title": "EXAMPLE BOOK TITLE"}]
    unique, dupes = find_duplicates(recs)
    assert len(unique) == 1 and len(dupes) == 2


def test_same_text_different_source_is_not_duplicate():
    recs = [{"source": "Books to Scrape", "author": None, "name_or_title": "Hi"},
            {"source": "Quotes to Scrape", "author": "A", "name_or_title": "Hi"}]
    unique, dupes = find_duplicates(recs)
    assert len(unique) == 2 and not dupes
