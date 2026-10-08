"""Quotes to Scrape: selectors only."""
import logging

import config
from scrapers.base_scraper import BaseScraper, utc_now

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    name = config.QUOTES_SOURCE
    start_url = config.QUOTES_URL

    def parse_page(self, soup, page_url):
        records = []
        for div in soup.select("div.quote"):
            try:
                text = div.select_one("span.text")
                author = div.select_one("small.author")
                records.append({
                    "text": text.get_text() if text else None,
                    "author": author.get_text() if author else None,
                    "tags": [t.get_text() for t in div.select("a.tag")],
                    "source_url": page_url,       # page where the quote appeared
                    "scraped_at": utc_now(),
                })
            except Exception:
                logger.exception("[%s] Skipping bad record on %s", self.name, page_url)
        return records
