"""End-to-end test with fake scrapers (no internet)."""
import csv
import json

import main
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
from tests.test_scrapers import B1, B2, Q1, Q2, fake_fetch


def test_full_pipeline(tmp_path, monkeypatch):
    def books_fetch(self, url):
        return fake_fetch({"https://books.toscrape.com/": B1,
                           "https://books.toscrape.com/catalogue/page-2.html": B2})(url)

    def quotes_fetch(self, url):
        return fake_fetch({"https://quotes.toscrape.com/": Q1,
                           "https://quotes.toscrape.com/page/2/": Q2})(url)

    monkeypatch.setattr(BooksScraper, "fetch", books_fetch)
    monkeypatch.setattr(QuotesScraper, "fetch", quotes_fetch)
    monkeypatch.setattr(main, "LOG_DIR", tmp_path / "logs")

    report = main.run(main.parse_args(["--output-dir", str(tmp_path), "--delay", "0", "--no-details"]))

    rows = list(csv.DictReader(open(tmp_path / "final_dataset.csv", encoding="utf-8")))
    saved = json.load(open(tmp_path / "summary_report.json", encoding="utf-8"))
    assert saved["totals"]["final_record_count"] == len(rows)
    assert report["reconciliation_ok"] is True
    assert {r["source"] for r in rows} == {"Books to Scrape", "Quotes to Scrape"}
    # the broken book record and the author-less quote must be rejected, not crash the run
    assert report["totals"]["rejected_validation"] == 2
