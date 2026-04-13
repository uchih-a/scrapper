"""
Novada Web Unblocker — Scrapy Downloader Middleware
====================================================
Routes every request through the Novada proxy endpoint so that
Cloudflare JS challenges, CAPTCHAs and IP bans are handled
transparently before Scrapy ever sees the response.

Setup
-----
1. Sign up at https://dashboard.novada.com
2. Activate Web Unblocker trial in the dashboard
3. Copy the exact proxy endpoint + your username & password into settings.py

How it works
------------
The Web Unblocker works as an HTTP CONNECT proxy.
Scrapy's built-in proxy support handles SSL tunneling correctly.

IMPORTANT — correct proxy endpoint:
  Check your Novada dashboard for the exact hostname.
  Set NOVADA_PROXY in settings.py to the value shown there, e.g.:
    NOVADA_PROXY = "http://gate.novada.com:7777"
"""

import base64
import logging

from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class NovadaProxyMiddleware:
    """Injects Novada Web Unblocker credentials into every request."""

    def __init__(self, username: str, password: str, proxy_url: str):
        self.proxy_url = proxy_url
        raw = f"{username}:{password}".encode("utf-8")
        self.proxy_auth = "Basic " + base64.b64encode(raw).decode("utf-8")
        logger.info(f"[NovadaProxy] Routing all requests via {proxy_url}")

    @classmethod
    def from_crawler(cls, crawler):
        username = crawler.settings.get("NOVADA_USERNAME", "")
        password = crawler.settings.get("NOVADA_PASSWORD", "")
        proxy_url = crawler.settings.get("NOVADA_PROXY", "")

        if not username or username == "YOUR_NOVADA_USERNAME":
            raise NotConfigured(
                "Novada credentials not set. "
                "Edit NOVADA_USERNAME and NOVADA_PASSWORD in settings.py"
            )
        if not proxy_url or proxy_url == "http://unblock.novada.pro:7799":
            logger.warning(
                "[NovadaProxy] Using default proxy URL. "
                "If DNS fails, check your Novada dashboard for the correct endpoint "
                "and update NOVADA_PROXY in settings.py"
            )
        return cls(username, password, proxy_url)

    # Scrapy 2.13+ compatible — no spider argument
    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxy_url
        request.headers["Proxy-Authorization"] = self.proxy_auth
