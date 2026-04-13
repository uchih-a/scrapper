# Property24 Kenya — Vacant Plots Scraper

Scrapy spider that crawls ALL vacant land / plot listings on
[property24.co.ke](https://www.property24.co.ke/vacant-land-plots-for-sale)
and exports them to a clean CSV file.

Bypasses Cloudflare protection via **Novada Web Unblocker** (7-day free trial).

---

## Output fields (CSV columns)

| Column | Example |
|--------|---------|
| `listing_no` | 117084774 |
| `title` | Vacant Land / Plot for Sale in Kajiado |
| `price` | KSh 15,000,000 |
| `location` | Kajiado, Kajiado County |
| `street_address` | Oltepesi Kajiado County, Kajiado |
| `erf_size` | 15 acres |
| `property_type` | Vacant Land / Plot |
| `list_date` | 01 April 2026 |
| `description` | 15 acres of prime roadside land... |
| `listing_url` | https://www.property24.co.ke/... |
| `scraped_at` | 2026-04-05 10:22:11 UTC |

---

## Quick start

### 1. Install dependencies

```bash
pip install scrapy itemadapter
```

### 2. Get your Novada free trial credentials

1. Go to [https://dashboard.novada.com](https://dashboard.novada.com)
2. Register a free account
3. Navigate to **Web Unblocker** → copy your **Username** and **Password**

> ⚠️ Make sure you activate the **Web Unblocker** product specifically —
> NOT the Scraper API. The Web Unblocker is what handles Cloudflare sites
> like Property24.

### 3. Add your credentials

Open `property24_scraper/settings.py` and fill in:

```python
NOVADA_USERNAME = "your_actual_username"
NOVADA_PASSWORD = "your_actual_password"
```

**Or** use environment variables (more secure):

```bash
export NOVADA_USERNAME="your_username"
export NOVADA_PASSWORD="your_password"
```

Then update `settings.py` to read from env:
```python
import os
NOVADA_USERNAME = os.environ.get("NOVADA_USERNAME", "")
NOVADA_PASSWORD = os.environ.get("NOVADA_PASSWORD", "")
```

### 4. Run the spider

```bash
cd property24_scraper

# Full crawl — all 22,000+ listings
scrapy crawl vacant_plots

# Demo mode — only 4 known listings (fast, zero bandwidth cost)
scrapy crawl vacant_plots -s DEMO_MODE=True

# Limited crawl — first 5 pages (~100 listings)
scrapy crawl vacant_plots -s MAX_PAGES=5
```

Output file: `property24_vacant_plots.csv`
Log file:    `scraper.log`

---

## Project structure

```
property24_scraper/
│
├── scrapy.cfg
├── requirements.txt
├── README.md
│
└── property24_scraper/
    ├── __init__.py
    ├── settings.py        ← credentials & tuning knobs live here
    ├── items.py           ← field definitions
    ├── middlewares.py     ← Novada proxy injection
    ├── pipelines.py       ← data cleaning + CSV export
    └── spiders/
        └── vacant_plots.py ← main spider
```

---

## Tuning for the free trial (bandwidth saving tips)

The Novada Web Unblocker charges per GB of traffic.
During your 7-day trial you have a limited quota.
These settings in `settings.py` help stay within limits:

| Setting | Value | Why |
|---------|-------|-----|
| `CONCURRENT_REQUESTS` | 8 | Enough speed without hammering |
| `DOWNLOAD_DELAY` | 1.5s | Polite crawling |
| `HTTPCACHE_ENABLED` | `True` | Cache pages so re-runs don't re-fetch |
| `MAX_PAGES` | 50 | Test with 50 pages before going full |

**Recommended test sequence:**

1. `DEMO_MODE=True` — confirm your credentials work (4 requests)
2. `MAX_PAGES=5` — validate all 11 CSV columns look correct
3. `MAX_PAGES=50` — check ~1,000 listings and estimate bandwidth
4. Full crawl — let it run overnight

---

## Resuming an interrupted crawl

The CSV pipeline **appends** to the existing file rather than
overwriting it. This means if the scraper stops mid-way (network
issue, trial quota hit, etc.) you can simply restart it and it
will continue from where the pagination left off.

To avoid duplicates across runs, deduplicate by `listing_no`
in Excel:  **Data → Remove Duplicates → Column: listing_no**

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NotConfigured: Novada credentials not set` | Fill in `NOVADA_USERNAME` and `NOVADA_PASSWORD` in settings.py |
| Getting 403 on every request | Make sure you activated **Web Unblocker** in Novada dashboard, not Scraper API |
| Empty `price` / `erf_size` fields | Property24 may have updated their CSS — run `scrapy shell <url>` and inspect the page |
| Very slow crawl | Increase `CONCURRENT_REQUESTS` to 16 and reduce `DOWNLOAD_DELAY` to 1.0 |
| CSV has duplicate rows | Deduplicate on `listing_no` in Excel |

---

## After the free trial — what next?

| Option | Cost | Notes |
|--------|------|-------|
| Novada Web Unblocker | $4.70/GB | ~22k listings ≈ 3–5 GB ≈ $15–24 total |
| Bright Data Web Unlocker | ~$3/GB | Slightly cheaper at scale |
| Scrapeless | Free tier available | Limited monthly requests on free plan |

A full crawl of all 22,000+ listings will consume roughly 3–6 GB
depending on page size. Plan accordingly.

---

## Legal note

This scraper accesses only **publicly available listing data**.
Always review Property24's Terms of Service before large-scale
commercial use of the data.
# scrapper
