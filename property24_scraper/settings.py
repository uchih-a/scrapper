# ============================================================
#  Property24 Kenya Scraper — Settings
#  Proxy: Novada Web Unblocker (free trial)
# ============================================================

BOT_NAME = "property24_scraper"
SPIDER_MODULES = ["property24_scraper.spiders"]
NEWSPIDER_MODULE = "property24_scraper.spiders"

# ── Novada Web Unblocker credentials ────────────────────────
# Paste your trial credentials from dashboard.novada.com
NOVADA_USERNAME = "novada856pLg_SHr0D2-zone-unblock-region-us"
NOVADA_PASSWORD = "02ILzmWlGPqx"

# Novada Web Unblocker proxy endpoint
NOVADA_PROXY = "http://unblock.novada.pro:7799"

# ── Crawler identity ─────────────────────────────────────────
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

ROBOTSTXT_OBEY = False

# ── Concurrency & politeness ─────────────────────────────────
# Keep low to be polite and stay within trial bandwidth limits
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 1.5          # seconds between requests
RANDOMIZE_DOWNLOAD_DELAY = True  # actual delay = 0.5x–1.5x DOWNLOAD_DELAY

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.5
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# ── Retry ────────────────────────────────────────────────────
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504]

# ── Middleware ───────────────────────────────────────────────
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    "property24_scraper.middlewares.NovadaProxyMiddleware": 100,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

# ── Pipelines ────────────────────────────────────────────────
ITEM_PIPELINES = {
    "property24_scraper.pipelines.DeduplicationPipeline": 50,
    "property24_scraper.pipelines.CleanDataPipeline": 100,
    "property24_scraper.pipelines.CsvExportPipeline": 200,
}

# ── Output file ──────────────────────────────────────────────
CSV_OUTPUT_FILE = "property24_vacant_plots.csv"

# ── Crawl state — enables resume on restart ──────────────────
# Scrapy persists the request queue and seen-URL fingerprints
# in this folder so a re-run picks up exactly where it stopped.
# Delete / rename this folder to start a completely fresh crawl.
JOBDIR = "crawl_state"

# ── HTTP cache (speeds up re-runs during dev) ────────────────
HTTPCACHE_ENABLED = False   # set True during dev/testing
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_IGNORE_HTTP_CODES = [403, 429, 500]

# ── Logging ──────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE = "scraper.log"

# ── Request headers ──────────────────────────────────────────
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Novada-Render-Type": "html",
    "X-Novada-SSL-Verify": "false",
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# ── Disable strict SSL Verification (Mimics cURL's -k flag) ──
# Required because Novada Web Unblocker uses its own SSL certificates
# to intercept and render the JavaScript challenges.
# REMOVE or change this line
DOWNLOADER_CLIENTCONTEXTFACTORY = "scrapy.core.downloader.contextfactory.ScrapyClientContextFactory"
DOWNLOADER_CLIENT_TLS_METHOD = "TLSv1.2"
DOWNLOADER_CLIENT_TLS_CIPHERS = "DEFAULT"
DOWNLOADER_CLIENT_TLS_VERBOSE_LOGGING = True