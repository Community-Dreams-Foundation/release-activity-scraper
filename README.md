# Release Activity Scraper

## Overview
This Python script automates the extraction of release/tag data from a
public GitHub repository's "Tags" page, for use in business reporting
(e.g., tracking the release cadence of a software dependency or
competitor open-source project).

## Target Website
`https://github.com/pandas-dev/pandas/tags`

This page is publicly accessible without authentication, contains
structured HTML, and does not require complex JS rendering or CAPTCHA
solving to access the data we need.

## What It Extracts
For each release/tag entry:
- **tag** - the version/tag name (e.g., `v3.0.3`)
- **release_date** - ISO 8601 timestamp of the release/tag commit
- **commit_sha** - short commit hash associated with the tag
- **release_notes_url** - link to the release notes page

## How To Run

```bash
pip install requests beautifulsoup4 pandas
python scrape_release_activity.py
```

## Output
- `release_activity.csv` - structured CSV with all extracted records
- Console output showing a sample of the extracted data and summary stats

## Error Handling
- Network requests are retried up to 2 times with a short delay on failure
- Missing HTML elements (tag name, date, commit SHA) are logged as warnings
  and result in `None`/empty values rather than crashing the script
- If no data can be extracted at all, the script exits with a non-zero
  status code and writes no CSV

## Configuration
Change the target repository by editing these constants at the top of
`scrape_release_activity.py`:

```python
REPO_OWNER = "pandas-dev"
REPO_NAME = "pandas"
MAX_PAGES = 2
```
