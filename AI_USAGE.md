# AI Usage

> NOTE TO SELF: edit this file so it reflects what YOU really did before submitting.

## Tools used
- Claude (Anthropic) – initial project scaffold, scrapers, cleaning/validation/dedup code, tests, README.

## What each tool was used for
- Designing the common data model and project structure.
- Generating the pagination loop, retry session and parsing code.
- Generating unit tests and an offline end-to-end test (fake HTML, no internet).

## Representative prompts
1. "Build the full scraping assignment (Books + Quotes to Scrape) with cleaning, validation, dedup, CSV + JSON report, logging."
2. "Make main.py testable (run(args), --output-dir) so an end-to-end test can run offline."

## AI-assisted parts
Almost all modules (`scrapers/`, `processing/`, `main.py`, `tests/`) were AI-generated, then reviewed by me.

## Changes after reviewing AI output
- (Fill in) e.g. checked selectors in browser DevTools, adjusted delay, verified CSV manually.

## Incorrect/incomplete AI suggestions found
- (Fill in honestly) e.g. first version of main.py had no `run()` function, so the end-to-end test could not call it; fixed.

## Testing and verification
- `python -m pytest` (offline tests: cleaning, validation, dedup, parsing, pagination, failure handling, end-to-end).
- Full run from a fresh venv; checked both sources in CSV, prices numeric, ratings 1-5,
  JSON final count == CSV rows, `reconciliation_ok: true`.
