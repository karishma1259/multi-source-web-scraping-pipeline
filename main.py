"""Entry point:  python main.py   (see --help for options)."""
import argparse
import csv
import json
import logging
import time
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

import config
from processing.cleaning import CLEANERS
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.base_scraper import create_session
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

logger = logging.getLogger("main")


LOG_DIR = config.LOG_DIR


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    logging.basicConfig(
        level=logging.INFO, format=fmt,
        force=True,
        handlers=[logging.FileHandler(LOG_DIR / "scraper.log", mode="w", encoding="utf-8"),
                  logging.StreamHandler()],
    )


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Multi-source scraping pipeline")
    p.add_argument("--max-pages", type=int, default=None, help="limit pages per source (testing)")
    p.add_argument("--output-dir", default=str(config.OUTPUT_DIR), help="where to write the CSV and JSON")
    p.add_argument("--no-details", "--skip-details", dest="skip_details", action="store_true",
                   help="do not visit each book detail page (category/description stay empty; much faster)")
    p.add_argument("--delay", type=float, default=config.REQUEST_DELAY, help="seconds between requests")
    return p.parse_args(argv)


def process_source(name, raw_records, stats):
    """Clean + validate one source. Returns list of valid cleaned records."""
    s = stats[name]
    s["raw_collected"] = len(raw_records)
    cleaner = CLEANERS[name]
    reasons, valid = Counter(), []
    for raw in raw_records:
        try:
            rec = cleaner(raw)
        except Exception:
            logger.exception("[%s] Cleaning failed for %r", name, raw)
            reasons["cleaning_error"] += 1
            s["rejected"] += 1
            continue
        s["after_cleaning"] += 1
        problems = validate_record(rec)
        if problems:
            logger.warning("[%s] Rejected %s: %s", name, rec.get("source_url"), problems)
            for pr in problems:
                reasons[pr] += 1
            s["rejected"] += 1
        else:
            valid.append(rec)
    s["rejected_by_reason"] = dict(reasons)
    return valid


def write_csv(records, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=config.CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def run(args):
    setup_logging()
    out_dir = Path(args.output_dir)
    start = time.time()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    session = create_session()
    common = dict(session=session, delay=args.delay, max_pages=args.max_pages)
    scrapers = [BooksScraper(fetch_details=not args.skip_details, **common), QuotesScraper(**common)]

    stats = {s.name: {"raw_collected": 0, "after_cleaning": 0, "rejected": 0,
                      "rejected_by_reason": {}, "duplicates_removed": 0, "final": 0,
                      "pages_scraped": 0, "pages_failed": 0} for s in scrapers}
    all_valid = []
    for scraper in scrapers:
        try:
            raw = scraper.scrape()
        except Exception:
            logger.exception("[%s] Source failed completely; continuing", scraper.name)
            raw = []
        stats[scraper.name]["pages_scraped"] = scraper.pages_scraped
        stats[scraper.name]["pages_failed"] = scraper.pages_failed
        all_valid.extend(process_source(scraper.name, raw, stats))

    unique, dupes = find_duplicates(all_valid)
    for d in dupes:
        stats[d["source"]]["duplicates_removed"] += 1
        logger.warning("Duplicate removed: [%s] %s", d["source"], d["name_or_title"][:60])
    for rec in unique:
        stats[rec["source"]]["final"] += 1

    write_csv(unique, out_dir / "final_dataset.csv")

    reconciled = all(
        s["raw_collected"] - s["rejected"] - s["duplicates_removed"] == s["final"] for s in stats.values())
    report = {
        "run": {"started_at": started_at,
                "ended_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "duration_seconds": round(time.time() - start, 1),
                "options": vars(args)},
        "per_source": stats,
        "totals": {
            "raw_collected": sum(s["raw_collected"] for s in stats.values()),
            "after_cleaning": sum(s["after_cleaning"] for s in stats.values()),
            "rejected": sum(s["rejected"] for s in stats.values()),
            "rejected_validation": sum(s["rejected"] for s in stats.values()),
            "duplicates_detected": len(dupes),
            "final_record_count": len(unique),
        },
        "reconciliation_ok": reconciled,
    }
    path = out_dir / "summary_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    logger.info("Finished: %d rows written, reconciled=%s, %.1fs",
                len(unique), reconciled, report["run"]["duration_seconds"])
    return report


def main():
    run(parse_args())


if __name__ == "__main__":
    main()
