"""Fingerprint-based duplicate detection (duplicates are removed, and counted/logged)."""
import hashlib
import re


def make_fingerprint(rec):
    name = rec.get("name_or_title") or ""
    if rec["source"] == "Books to Scrape":
        key = f'{rec["source"]} {name}'
    else:
        key = f'{rec["source"]} {rec.get("author") or ""} {name[:50]}'
    key = re.sub(r"[^\w\s]", "", key.lower())
    key = " ".join(key.split())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records):
    seen, unique, dupes = set(), [], []
    for rec in records:
        fp = make_fingerprint(rec)
        (dupes if fp in seen else unique).append(rec)
        seen.add(fp)
    return unique, dupes
