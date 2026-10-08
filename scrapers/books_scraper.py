"""Books to Scrape: selectors + optional detail-page enrichment."""
import logging
import time
from urllib.parse import urljoin

import config
from scrapers.base_scraper import BaseScraper, utc_now

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    name = config.BOOKS_SOURCE
    start_url = config.BOOKS_URL

    def __init__(self, fetch_details=True, **kwargs):
        super().__init__(**kwargs)
        self.fetch_details = fetch_details

    def parse_page(self, soup, page_url):
        records = []
        for article in soup.select("article.product_pod"):
            try:
                link = article.select_one("h3 > a")
                price = article.select_one("p.price_color")
                rating = article.select_one("p.star-rating")
                records.append({
                    "title": link.get("title") if link else None,
                    "source_url": urljoin(page_url, link["href"]) if link and link.get("href") else None,
                    "price_raw": price.get_text() if price else None,
                    "rating_raw": " ".join(rating.get("class", [])) if rating else None,
                    "category": None,
                    "description": None,
                    "scraped_at": utc_now(),
                })
            except Exception:
                logger.exception("[%s] Skipping bad record on %s", self.name, page_url)
        return records

    def _enrich(self, rec):
        soup = self.fetch(rec["source_url"])
        if soup is None:
            return
        crumbs = soup.select("ul.breadcrumb li a")
        if len(crumbs) >= 3:
            rec["category"] = crumbs[2].get_text()
        desc = soup.select_one("#product_description ~ p")
        rec["description"] = desc.get_text() if desc else None

    def scrape(self):
        records = super().scrape()
        if self.fetch_details:
            logger.info("[%s] Fetching %d detail pages", self.name, len(records))
            for i, rec in enumerate(records, 1):
                if rec.get("source_url"):
                    try:
                        self._enrich(rec)
                    except Exception:
                        logger.exception("[%s] Detail failed for %s", self.name, rec["source_url"])
                    time.sleep(self.delay)
                if i % 100 == 0:
                    logger.info("[%s] Details %d/%d", self.name, i, len(records))
        return records
