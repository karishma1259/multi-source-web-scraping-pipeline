"""Pure cleaning functions. No internet, no files."""
import re
from urllib.parse import urljoin

import config

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
QUOTE_CHARS = "\u201c\u201d\u2018\u2019\"'"


def clean_text(value):
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(value):
    text = clean_text(value)
    if text is None:
        return None
    return clean_text(text.strip(QUOTE_CHARS))


def clean_price(raw):
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))
    return float(match.group()) if match else None


def clean_rating(raw):
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(tags):
    if not tags:
        return None
    cleaned = {clean_text(t).lower() for t in tags if clean_text(t)}
    return ";".join(sorted(cleaned)) or None


def normalize_url(url, base=None):
    url = clean_text(url)
    if not url:
        return None
    if base:
        url = urljoin(base, url)
    return url if url.lower().startswith(("http://", "https://")) else None


def clean_book(raw):
    return {
        "source": config.BOOKS_SOURCE,
        "source_url": normalize_url(raw.get("source_url"), config.BOOKS_URL),
        "name_or_title": clean_text(raw.get("title")),
        "category": clean_text(raw.get("category")),
        "price": clean_price(raw.get("price_raw")),
        "rating": clean_rating(raw.get("rating_raw")),
        "author": None,
        "tags": None,
        "description": clean_text(raw.get("description")),
        "scraped_at": raw.get("scraped_at"),
    }


def clean_quote(raw):
    return {
        "source": config.QUOTES_SOURCE,
        "source_url": normalize_url(raw.get("source_url"), config.QUOTES_URL),
        "name_or_title": strip_quotes(raw.get("text")),
        "category": None,
        "price": None,
        "rating": None,
        "author": clean_text(raw.get("author")),
        "tags": clean_tags(raw.get("tags")),
        "description": None,
        "scraped_at": raw.get("scraped_at"),
    }


CLEANERS = {config.BOOKS_SOURCE: clean_book, config.QUOTES_SOURCE: clean_quote}
