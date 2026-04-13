"""
Property24 Kenya — Vacant Land / Plots Spider
==============================================
Crawls ALL pages of:
  https://www.property24.co.ke/vacant-land-plots-for-sale

For each listing card on the index pages it follows the detail
URL and extracts the 8 required fields plus bonus metadata.

Run command
-----------
    scrapy crawl vacant_plots

With a page limit (for testing):
    scrapy crawl vacant_plots -s MAX_PAGES=5

Demo mode (only the 4 listings we already fetched):
    scrapy crawl vacant_plots -s DEMO_MODE=True

Selectors verified against live rendered HTML — April 2026
----------------------------------------------------------
Structure confirmed from property24.co.ke detail page:

  Price       → div.p24_price  (inside div.p24_mBM)
  Title       → div.sc_listingAddress > h1
  Address     → div.p24_mBM > p  (subtitle line under h1)
  Size icons  → span.p24_size > span  (index 0=floor, index 1=erf)
  Description → div.sc_listingDetailsText
  Overview    → div.p24_propertyOverviewRow
                  div.p24_propertyOverviewKey  → label
                  div.p24_info                 → value

  Overview keys present on live page:
    "Listing Number", "Type of Property", "Street Address",
    "List Date", "Erf Size", "Floor Area", "Pets Allowed"
"""

import re
import scrapy
from datetime import datetime, timezone
from property24_scraper.items import VacantPlotItem


# ── Known listing URLs for demo / smoke-test mode ─────────────
DEMO_URLS = [
    "https://www.property24.co.ke/vacant-land-plot-for-sale-in-kajiado-117084774",
    "https://www.property24.co.ke/vacant-land-plot-for-sale-in-konza-117070090",
    "https://www.property24.co.ke/vacant-land-plot-for-sale-in-kitisuru-117068461",
    "https://www.property24.co.ke/vacant-land-plot-for-sale-in-karen-117092424",
]

BASE_URL = "https://www.property24.co.ke/vacant-land-plots-for-sale"


class VacantPlotsSpider(scrapy.Spider):
    name = "vacant_plots"
    allowed_domains = ["property24.co.ke"]

    custom_settings = {
        # override per-spider if needed
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_crawled = 0

    # ── Entry points ─────────────────────────────────────────

    async def start(self):
        demo_mode = getattr(self, "DEMO_MODE", None) or self.settings.get(
            "DEMO_MODE", False
        )
        
        start_page = int(self.settings.get("START_PAGE", 1))

        if str(demo_mode).lower() in ("true", "1", "yes"):
            self.logger.info("=== DEMO MODE — scraping 4 known listings only ===")
            for url in DEMO_URLS:
                yield scrapy.Request(url, callback=self.parse_listing)
        else:
            self.logger.info(f"=== FULL CRAWL MODE — starting from page {start_page} ===")
            
            start_url = f"{BASE_URL}?Page={start_page}" if start_page > 1 else BASE_URL
            
            yield scrapy.Request(
                start_url,
                callback=self.parse_index,
                meta={"page": start_page},
            )

    # ── Index page parser ────────────────────────────────────

    def parse_index(self, response):
        page = response.meta.get("page", 1)
        max_pages = int(self.settings.get("MAX_PAGES", 99999))
        self.pages_crawled += 1

        self.logger.info(f"[Index] Page {page} — status {response.status}")

        # ── extract listing detail URLs ───────────────────────
        listing_links = response.css(
            "a[href*='/vacant-land-plot-for-sale-in-']::attr(href)"
        ).getall()

        # deduplicate (same href sometimes appears twice per card)
        seen = set()
        for href in listing_links:
            url = response.urljoin(href)
            url = url.split("?")[0].split("#")[0]
            if url not in seen:
                seen.add(url)
                yield scrapy.Request(url, callback=self.parse_listing)

        self.logger.info(
            f"[Index] Page {page} → {len(seen)} unique listings queued"
        )

        # ── follow pagination ─────────────────────────────────
        if page < max_pages:
            next_page = self._get_next_page(response, page)
            if next_page:
                yield scrapy.Request(
                    next_page,
                    callback=self.parse_index,
                    meta={"page": page + 1},
                )
            else:
                self.logger.info("[Index] No more pages found — crawl complete.")

    def _get_next_page(self, response, current_page: int):
        """
        Property24 pagination: /vacant-land-plots-for-sale?Page=2
        """
        # check if a link for page+1 exists anywhere on page
        all_page_links = response.css("a[href*='Page=']::attr(href)").getall()
        target = f"Page={current_page + 1}"
        for link in all_page_links:
            if target in link:
                return response.urljoin(link)

        # construct URL directly from page counter
        total_text = response.css(
            "span:contains('of')::text, div:contains('of')::text"
        ).re_first(r"of\s+([\d,]+)")
        if total_text:
            total = int(total_text.replace(",", ""))
            if (current_page * 20) < total:
                return f"{BASE_URL}?Page={current_page + 1}"

        # last resort: always try page+1
        if self.pages_crawled > 0:
            return f"{BASE_URL}?Page={current_page + 1}"
        return None

    # ── Detail page parser ───────────────────────────────────

    def parse_listing(self, response):
        if response.status in (403, 404, 410):
            self.logger.warning(
                f"[Listing] Skipping {response.url} — status {response.status}"
            )
            return

        item = VacantPlotItem()

        # ── listing_url ──────────────────────────────────────
        item["listing_url"] = response.url

        # ── listing_no ───────────────────────────────────────
        # Primary: "Listing Number" row in Property Overview table
        # Fallback: last numeric segment in the URL
        listing_no = self._overview_field(response, "Listing Number")
        if not listing_no:
            match = re.search(r"(\d{8,})$", response.url)
            listing_no = match.group(1) if match else ""
        item["listing_no"] = listing_no

        # ── title ────────────────────────────────────────────
        # Confirmed: div.sc_listingAddress > h1
        title = response.css(".sc_listingAddress h1::text").get("").strip()
        if not title:
            title = response.css("h1::text").get("").strip()
        if not title:
            title = response.css("title::text").get("").strip()
        item["title"] = title

        # ── price ────────────────────────────────────────────
        # Confirmed: div.p24_price  (has whitespace — strip required)
        price = response.css(".p24_price::text").get("").strip()
        if not price:
            # fallback: find first element containing "KSh"
            price = response.xpath(
                "//*[contains(text(),'KSh')][1]/text()"
            ).get("").strip()
        item["price"] = price

        # ── location ─────────────────────────────────────────
        # Confirmed: div.p24_mBM > p  e.g. "Milima Rd Nairobi, Karen, Nairobi"
        # This is the subtitle line directly below the h1.
        location = response.css(".p24_mBM p::text").get("").strip()
        if not location:
            # breadcrumb fallback — last 2 crumbs are suburb + county
            crumbs = response.css(".breadcrumb li a::text").getall()
            crumbs = [c.strip() for c in crumbs if c.strip() and c.strip() != "Home"]
            location = ", ".join(crumbs[-2:]) if len(crumbs) >= 2 else ", ".join(crumbs)
        item["location"] = location

        # ── street_address ───────────────────────────────────
        # Confirmed: "Street Address" key in Property Overview table
        # e.g. "Milima Rd Nairobi, Karen"
        item["street_address"] = self._overview_field(response, "Street Address")

        # ── erf_size ─────────────────────────────────────────
        # Confirmed: "Erf Size" key in Property Overview table
        # e.g. "2 acres"
        # Also available as span.p24_size icons: [0]=floor area, [1]=erf size
        erf = (
            self._overview_field(response, "Erf Size")
            or self._overview_field(response, "Size of farm")
            or self._overview_field(response, "Plot Size")
        )
        if not erf:
            # icon spans fallback — index 1 is the erf/land size icon
            size_spans = response.css(".p24_size span::text").getall()
            size_spans = [s.strip() for s in size_spans if s.strip()]
            if len(size_spans) >= 2:
                erf = size_spans[1]
            elif size_spans:
                erf = size_spans[0]
        item["erf_size"] = (erf or "").strip()

        # ── description ──────────────────────────────────────
        # Confirmed: div.sc_listingDetailsText
        desc_parts = response.css(".sc_listingDetailsText *::text").getall()
        if not desc_parts:
            desc_parts = response.css(".sc_listingDetailsText::text").getall()
        description = " ".join(p.strip() for p in desc_parts if p.strip())
        item["description"] = description[:2000]

        # ── bonus fields ─────────────────────────────────────
        # Both confirmed in Property Overview table
        item["property_type"] = self._overview_field(response, "Type of Property")
        item["list_date"]     = self._overview_field(response, "List Date")
        item["scraped_at"]    = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        yield item

    # ── Helpers ──────────────────────────────────────────────

    def _overview_field(self, response, label: str) -> str:
        """
        Extracts a value from the Property Overview table.

        Confirmed HTML structure (April 2026):

            <div class="row p24_propertyOverviewRow">
                <div class="col-xs-6 p24_propertyOverviewKey">Listing Number</div>
                <div class="col-xs-6 noPadding">
                    <div class="p24_info">117092424</div>
                </div>
            </div>

        Strategy 1 uses XPath to find the row containing the matching
        key label, then grabs the p24_info value in the same row.
        Strategy 2 is a pure CSS loop as a backup.
        Strategies 3 & 4 handle older page versions.
        """

        # Strategy 1 — confirmed live structure (XPath, primary)
        value = response.xpath(
            f"//div[contains(@class,'p24_propertyOverviewRow')]"
            f"[.//div[contains(@class,'p24_propertyOverviewKey')]"
            f"  [normalize-space(.)='{label}']]"
            f"//div[contains(@class,'p24_info')]/text()"
        ).get()
        if value:
            return value.strip()

        # Strategy 2 — CSS loop (backup, same structure)
        for row in response.css(".p24_propertyOverviewRow"):
            key_text = row.css(".p24_propertyOverviewKey::text").get("").strip()
            if key_text.lower() == label.lower():
                val = row.css(".p24_info::text").get("").strip()
                if val:
                    return val

        # Strategy 3 — dt/dd pairs (legacy page versions)
        value = response.xpath(
            f"//dt[normalize-space(.)='{label}']/following-sibling::dd[1]/text()"
        ).get()
        if value:
            return value.strip()

        # Strategy 4 — table rows (legacy page versions)
        value = response.xpath(
            f"//td[normalize-space(.)='{label}']/following-sibling::td[1]/text()"
        ).get()
        if value:
            return value.strip()

        return ""