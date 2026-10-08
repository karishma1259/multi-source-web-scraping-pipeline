"""Shared networking + dynamic pagination. Source scrapers only add selectors."""
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import config

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    retries = Retry(total=3, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BaseScraper:
    name = ""
    start_url = ""

    def __init__(self, session=None, delay=config.REQUEST_DELAY,
                 timeout=config.REQUEST_TIMEOUT, max_pages=None):
        self.session = session or create_session()
        self.delay = delay
        self.timeout = timeout
        self.max_pages = max_pages
        self.pages_scraped = 0
        self.pages_failed = 0

    def fetch(self, url):
        """Return parsed soup, or None if the request failed (never raises)."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"          # keeps the pound sign correct
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as exc:
            logger.error("[%s] Failed to fetch %s: %s", self.name, url, exc)
            return None

    def parse_page(self, soup, page_url):
        raise NotImplementedError

    def scrape(self):
        url, page, records, visited = self.start_url, 1, [], set()
        while url and url not in visited:
            if self.max_pages and page > self.max_pages:
                logger.info("[%s] max_pages=%d reached", self.name, self.max_pages)
                break
            visited.add(url)
            logger.info("[%s] Page %d: %s", self.name, page, url)
            soup = self.fetch(url)
            if soup is None:
                self.pages_failed += 1
                break                            # stop this source, others continue
            self.pages_scraped += 1
            try:
                records.extend(self.parse_page(soup, url))
            except Exception:
                logger.exception("[%s] Parsing failed on %s", self.name, url)
            next_link = soup.select_one("li.next > a")
            url = urljoin(url, next_link["href"]) if next_link and next_link.get("href") else None
            page += 1
            time.sleep(self.delay)
        logger.info("[%s] Done: %d raw records, %d pages", self.name, len(records), self.pages_scraped)
        return records
