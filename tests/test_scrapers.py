"""Offline scraper tests using fake HTML + a fake session (no internet)."""
from bs4 import BeautifulSoup

from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BOOK_HTML = """<article class="product_pod"><p class="star-rating Three"></p>
<h3><a href="catalogue/a-light_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
<div class="product_price"><p class="price_color">\u00a351.77</p></div></article>
<article class="product_pod"><h3></h3></article>
<ul class="pager"><li class="next"><a href="catalogue/page-2.html">next</a></li></ul>"""

QUOTE_HTML = """<div class="quote"><span class="text">\u201cHello\u201d</span>
<span>by <small class="author">Ann</small></span>
<div class="tags"><a class="tag">b</a><a class="tag">a</a></div></div>"""


B1 = BOOK_HTML + ""
B2 = """<article class="product_pod"><p class="star-rating One"></p>
<h3><a href="b2/index.html" title="Second Book">Second ...</a></h3>
<div class="product_price"><p class="price_color">\u00a310.00</p></div></article>"""
Q1 = QUOTE_HTML + '<li class="next"><a href="/page/2/">n</a></li>'
Q2 = QUOTE_HTML.replace("Hello", "Bye").replace("Ann", "Bob") + \
    '<div class="quote"><span class="text">\u201cNo author\u201d</span></div>'


def fake_fetch(pages):
    def _fetch(url):
        return BeautifulSoup(pages[url], "lxml") if url in pages else None
    return _fetch


class FakeResp:
    def __init__(self, text, status=200):
        self.text, self.status_code, self.encoding = text, status, "utf-8"

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, timeout=10):
        return FakeResp(self.pages[url])


def test_book_parse_handles_missing_elements():
    recs = BooksScraper(fetch_details=False, session=object()).parse_page(
        BeautifulSoup(BOOK_HTML, "lxml"), "https://books.toscrape.com/")
    assert len(recs) == 2
    assert recs[0]["title"] == "A Light in the Attic"
    assert recs[0]["source_url"] == "https://books.toscrape.com/catalogue/a-light_1000/index.html"
    assert recs[0]["rating_raw"] == "star-rating Three"
    assert recs[1]["title"] is None and recs[1]["price_raw"] is None   # no crash


def test_quote_parse():
    recs = QuotesScraper(session=object()).parse_page(BeautifulSoup(QUOTE_HTML, "lxml"), "https://quotes.toscrape.com/")
    assert recs[0]["author"] == "Ann" and recs[0]["tags"] == ["b", "a"]


def test_pagination_follows_next_link_until_end():
    pages = {
        "https://quotes.toscrape.com/": QUOTE_HTML + '<li class="next"><a href="/page/2/">n</a></li>',
        "https://quotes.toscrape.com/page/2/": QUOTE_HTML,
    }
    s = QuotesScraper(session=FakeSession(pages), delay=0)
    assert len(s.scrape()) == 2 and s.pages_scraped == 2


def test_failed_page_does_not_crash():
    class Boom:
        def get(self, *a, **k):
            import requests
            raise requests.ConnectionError("down")
    s = QuotesScraper(session=Boom(), delay=0)
    assert s.scrape() == [] and s.pages_failed == 1
