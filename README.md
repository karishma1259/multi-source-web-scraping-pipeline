# Multi-Source Web Scraping & Data Consolidation

ETL pipeline that scrapes **Books to Scrape** and **Quotes to Scrape**, cleans, validates,
deduplicates and consolidates them into one CSV plus a JSON summary.

```
Scrape (both sites) -> Clean -> Validate -> Deduplicate -> Consolidate -> Save files
```

## Python version
3.10 – 3.12 (developed on 3.11).

## Setup
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python main.py                    # full run (~10-12 min because of 1,000 book detail pages)
python main.py --skip-details     # fast run (~1 min): category/description stay empty
python main.py --max-pages 2      # quick smoke test
python -m pytest                  # offline unit + end-to-end tests
```
CLI options: `--max-pages N`, `--skip-details` (alias `--no-details`), `--delay SECONDS`, `--output-dir PATH`.

### Docker (optional)
```bash
docker compose up --build         # writes to ./output and ./logs
```

## Dependencies
`requests`, `beautifulsoup4`, `lxml`, `pytest` (see `requirements.txt`).
Why Requests + BeautifulSoup: both sites are plain server-rendered HTML, so a browser tool
(Selenium/Playwright) would only add overhead.

## Step 1 – Source exploration
| Item | Books to Scrape | Quotes to Scrape |
|---|---|---|
| One record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a[title]` (visible text is truncated with `...`) | `span.text` (wrapped in curly quotes) |
| Price | `p.price_color` (`£51.77`) | – |
| Rating | class on `p.star-rating` (`Three`) | – |
| Author / Tags | – | `small.author` / `a.tag` |
| Category / Description | only on detail page (`ul.breadcrumb`, `#product_description + p`) | – |
| Next page | `li.next > a` (relative link) | `li.next > a` |

## How pagination works
`BaseScraper.scrape()` starts at the home page, parses records, then reads `li.next > a`,
converts the relative href with `urljoin` and repeats until no next link exists. Page numbers
are never hard-coded. A `visited` set prevents infinite loops. If a page fails after retries,
that source stops and the other source still runs.

## Data model
`source, source_url, name_or_title, category, price, rating, author, tags, description, scraped_at`

| Column | Books | Quotes |
|---|---|---|
| source_url | book detail page | page where the quote appeared |
| name_or_title | title | quote text (curly quotes removed) |
| category / description | from detail page | empty |
| price / rating | float / int 1-5 | empty |
| author / tags | empty | author / `tag1;tag2` (lowercase, sorted) |

Non-applicable fields are empty (`None`); nothing is invented (no fake price 0 for quotes).

## Cleaning approach (`processing/cleaning.py`)
Pure functions, no I/O: `clean_text` (whitespace, `\xa0`), `strip_quotes`, `clean_price`
(`£51.77` -> `51.77`), `clean_rating` (`Three` -> `3`), `clean_tags`, `normalize_url`
(relative -> absolute, http/https only). Empty strings become `None`. Response encoding is
forced to UTF-8 so `£` is not corrupted.

## Validation approach (`processing/validation.py`)
Returns a list of problem codes per record: `unknown_source`, `missing_name`, `invalid_url`,
`invalid_price`, `invalid_rating`, `missing_price` (books), `missing_author` (quotes).
Invalid records are logged as WARNING, counted per reason in the report, and excluded.

## Deduplication approach (`processing/deduplication.py`)
SHA-256 fingerprint of lowercase, punctuation-free, whitespace-collapsed text:
- Books: `source + title`
- Quotes: `source + author + first 50 characters of quote`

Duplicates are **removed** (not flagged) because the final dataset should be one row per real
item; every removed duplicate is logged and counted in the summary, so nothing is hidden.
The real sites contain no duplicates, so the logic is proven by unit tests with deliberately
duplicated data (`tests/test_deduplication.py`).

## Error-handling approach
- `requests.Session` with automatic retry + exponential backoff (429/500/502/503/504), 10 s timeout.
- `fetch()` never raises: failures are logged and return `None`.
- Each record is parsed in `try/except`; missing elements return `None`, not a crash.
- Each source runs in its own `try/except`; one failing source does not stop the other.
- Logs go to console and `logs/scraper.log`.

## Output
- `output/final_dataset.csv` – standardized records, fixed column order, UTF-8.
- `output/summary_report.json` – per-source raw/cleaned/rejected (by reason)/duplicates/final,
  pages scraped/failed, totals, duration, and `reconciliation_ok`
  (raw - rejected - duplicates == final).
- `logs/scraper.log` – timestamped run log.

## Assumptions
- Quote `source_url` = the listing page where the quote appeared (quotes have no own page).
- Quote `category` is left empty rather than a fake label.
- 0.5 s delay between requests (polite scraping).

## Known limitations
- Full run is sequential (~10-12 min); `--skip-details` trades category/description for speed.
- Two different quotes with identical author + first 50 characters would be treated as duplicates.
- A failed page stops that source (remaining pages are not attempted).

## If this ran regularly in production
Scheduler (cron/Airflow), checkpoint/resume, incremental scraping by URL, concurrent fetching
with rate limiting, database storage (PostgreSQL), alerting on failures/low counts.

## AI usage summary
See `AI_USAGE.md`.
