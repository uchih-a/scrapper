"""
Pipelines
=========
1. DeduplicationPipeline — skips listings already in the CSV (resume safety net)
2. CleanDataPipeline     — strips whitespace, normalises price & size strings
3. CsvExportPipeline     — writes all items to a single CSV (appends safely)
"""

import csv
import os
import re
import logging
from datetime import datetime, timezone
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)

# ── Column order in the CSV ───────────────────────────────────
CSV_FIELDS = [
    "listing_no",
    "title",
    "price",
    "location",
    "street_address",
    "erf_size",
    "property_type",
    "list_date",
    "description",
    "listing_url",
    "scraped_at",
]


# ─────────────────────────────────────────────────────────────
class DeduplicationPipeline:
    """
    Drops items whose listing_no already exists in the output CSV.

    This is the safety net for resume runs: if a page is re-crawled
    after a restart, the items are silently discarded instead of
    being written a second time.
    """

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.seen_ids: set[str] = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_file=crawler.settings.get(
                "CSV_OUTPUT_FILE", "property24_vacant_plots.csv"
            )
        )

    def open_spider(self, spider):
        """Load already-scraped listing numbers from the existing CSV."""
        if os.path.isfile(self.output_file):
            with open(self.output_file, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ln = row.get("listing_no", "").strip()
                    if ln:
                        self.seen_ids.add(ln)
            spider.logger.info(
                f"[Dedup] Loaded {len(self.seen_ids)} existing listing_no values "
                f"from {self.output_file} — duplicates will be skipped."
            )
        else:
            spider.logger.info("[Dedup] No existing CSV — starting fresh.")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        ln = str(adapter.get("listing_no", "")).strip()
        if ln and ln in self.seen_ids:
            raise DropItem(f"[Dedup] Skipping duplicate listing_no={ln}")
        if ln:
            self.seen_ids.add(ln)
        return item


# ─────────────────────────────────────────────────────────────
class CleanDataPipeline:
    """Normalise raw scraped strings before they hit the CSV."""

    def process_item(self, item, spider=None):
        adapter = ItemAdapter(item)

        # strip extra whitespace from every string field
        for field in adapter.field_names():
            val = adapter.get(field)
            if isinstance(val, str):
                adapter[field] = " ".join(val.split())

        # normalise price  →  "KSh 15,000,000"
        price = adapter.get("price", "")
        if price:
            price = re.sub(r"\s+", " ", price).strip()
            # ensure KSh prefix
            if price and not price.lower().startswith("ksh"):
                price = "KSh " + price
            adapter["price"] = price

        # normalise erf_size  →  strip redundant label text
        erf = adapter.get("erf_size", "")
        if erf:
            erf = re.sub(r"(?i)erf\s*size[:\s]*", "", erf).strip()
            adapter["erf_size"] = erf

        # stamp scrape time if not already set
        if not adapter.get("scraped_at"):
            adapter["scraped_at"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

        return item


# ─────────────────────────────────────────────────────────────
class CsvExportPipeline:
    """
    Writes items to a single CSV file.
    - Creates the file with a header row on first run.
    - Appends on subsequent runs (so you can resume interrupted crawls).
    """

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.file = None
        self.writer = None
        self.items_written = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_file=crawler.settings.get(
                "CSV_OUTPUT_FILE", "property24_vacant_plots.csv"
            )
        )

    def open_spider(self, spider):
        file_exists = os.path.isfile(self.output_file)
        self.file = open(self.output_file, "a", newline="", encoding="utf-8-sig")
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore",
        )
        if not file_exists:
            self.writer.writeheader()
            logger.info(f"[CsvPipeline] Created {self.output_file}")
        else:
            logger.info(f"[CsvPipeline] Appending to existing {self.output_file}")

    def close_spider(self, spider):
        if self.file:
            self.file.close()
        logger.info(f"[CsvPipeline] Done — {self.items_written} items written.")

    def process_item(self, item, spider=None):
        self.writer.writerow(ItemAdapter(item).asdict())
        self.items_written += 1
        if self.items_written % 100 == 0:
            logger.info(f"[CsvPipeline] {self.items_written} items saved so far...")
            self.file.flush()
        return item
