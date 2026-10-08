"""Central settings. Override the main ones via CLI flags in main.py."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

BOOKS_SOURCE = "Books to Scrape"
QUOTES_SOURCE = "Quotes to Scrape"
BOOKS_URL = "https://books.toscrape.com/"
QUOTES_URL = "https://quotes.toscrape.com/"

REQUEST_TIMEOUT = 10          # seconds
REQUEST_DELAY = 0.5           # polite pause between requests
USER_AGENT = "ScrapingAssignment/1.0 (learning project)"

CSV_COLUMNS = [
    "source", "source_url", "name_or_title", "category", "price",
    "rating", "author", "tags", "description", "scraped_at",
]
