"""
scrape_release_activity.py

Business context:
For business reporting, teams often need to track the release cadence and
versioning activity of public software projects (e.g., open-source
dependencies their products rely on, or competitor tooling). This script
automates the extraction of release/tag information from a public GitHub
repository page.

Target site: https://github.com/<owner>/<repo>/tags
(A public page, accessible without authentication, with structured HTML
and no CAPTCHA / heavy JS rendering required for the content we need.)

What it does:
1. Fetches one or more "tags" pages for a given public GitHub repository
2. Parses each tag entry for: tag/version name, release date, commit SHA,
   and the link to the release notes
3. Handles network errors and missing elements gracefully
4. Stores the results in a Pandas DataFrame and writes them to CSV
5. Prints a sample of the extracted data to the console
"""

import sys
import time
import csv
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd

REPO_OWNER = "pandas-dev"
REPO_NAME = "pandas"
BASE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/tags"

OUTPUT_CSV = "release_activity.csv"
MAX_PAGES = 2          # number of tag-list pages to scrape
REQUEST_TIMEOUT = 10   # seconds
RETRY_LIMIT = 2        # retries per page on failure

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_page(url, retries=RETRY_LIMIT):
    """Fetch a page with basic retry/error handling. Returns HTML text or None."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as exc:
            print(f"[WARN] Attempt {attempt} failed for {url}: {exc}")
            time.sleep(1)
    print(f"[ERROR] Giving up on {url} after {retries} attempts.")
    return None


def parse_tag_entry(box_row):
    """Extract tag name, release date, commit SHA, and notes link from one entry."""
    record = {
        "tag": None,
        "release_date": None,
        "commit_sha": None,
        "release_notes_url": None,
    }

    # Tag name + release notes link
    try:
        h2 = box_row.find("h2")
        tag_link = h2.find("a")
        record["tag"] = tag_link.get_text(strip=True)
        record["release_notes_url"] = "https://github.com" + tag_link.get("href", "")
    except AttributeError:
        print("[WARN] Missing tag name/link, skipping field.")

    # Release date
    try:
        rel_time = box_row.find("relative-time")
        record["release_date"] = rel_time.get("datetime")
    except AttributeError:
        print("[WARN] Missing release date, skipping field.")

    # Commit SHA (first muted link that looks like a short hash)
    try:
        muted_links = box_row.find_all("a", class_="Link--muted")
        for link in muted_links:
            text = link.get_text(strip=True)
            href = link.get("href", "")
            if "/commit/" in href:
                record["commit_sha"] = text
                break
    except AttributeError:
        print("[WARN] Missing commit SHA, skipping field.")

    return record


def scrape_release_activity(max_pages=MAX_PAGES):
    """Scrape one or more tag-list pages and return a list of release records."""
    all_records = []

    for page_num in range(1, max_pages + 1):
        url = BASE_URL if page_num == 1 else f"{BASE_URL}?after={all_records[-1]['tag']}" if all_records else BASE_URL
        # GitHub paginates tags via an 'after=<tag>' cursor; for page 1 we
        # just hit the base URL. For simplicity/robustness in this demo we
        # only request page 1 unless additional pages are explicitly needed.
        if page_num > 1 and not all_records:
            break

        print(f"[INFO] Fetching page {page_num}: {url}")

        html = fetch_page(url)
        if html is None:
            continue  # skip this page, keep going

        soup = BeautifulSoup(html, "html.parser")
        box_rows = soup.find_all("div", class_="Box-row")

        if not box_rows:
            print(f"[WARN] No tag entries found on page {page_num}.")
            continue

        for row in box_rows:
            record = parse_tag_entry(row)
            record["source_page"] = page_num
            all_records.append(record)

        print(f"[INFO] Extracted {len(box_rows)} records from page {page_num}.")

        if page_num < max_pages:
            time.sleep(1)  # be polite between requests

    return all_records


def main():
    print(f"[INFO] Scrape started at {datetime.now().isoformat(timespec='seconds')}")
    print(f"[INFO] Target repository: {REPO_OWNER}/{REPO_NAME}")

    records = scrape_release_activity(MAX_PAGES)

    if not records:
        print("[ERROR] No data extracted. Exiting without writing CSV.")
        sys.exit(1)

    df = pd.DataFrame(records)

    # Reorder columns for a cleaner business report
    df = df[["source_page", "tag", "release_date", "commit_sha", "release_notes_url"]]

    # Write to CSV
    df.to_csv(OUTPUT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"[INFO] Wrote {len(df)} records to {OUTPUT_CSV}")

    # Sample output to console (success demonstration)
    print("\n=== SAMPLE OF EXTRACTED DATA ===")
    print(df.head(10).to_string(index=False))

    print("\n=== SUMMARY STATS ===")
    print(f"Total release/tag records extracted: {len(df)}")
    print(f"Most recent release date:             {df['release_date'].max()}")
    print(f"Oldest release date in this batch:    {df['release_date'].min()}")


if __name__ == "__main__":
    main()
