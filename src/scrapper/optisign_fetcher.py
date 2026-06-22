import json
import ssl
import time
import urllib.request
import urllib.error
from typing import Iterator, Dict, Any
from src import config
from .base import Fetcher
from .factory import register_fetcher

# Workaround for macOS Python SSL certificate issue
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def fetch_json(url: str) -> dict:
    """GET a URL and return parsed JSON, with retries."""
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "ArticleFetcher/1.0",
            })
            with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = int(exc.headers.get("Retry-After", config.RETRY_DELAY))
                print(f"  ⏳ Rate-limited. Waiting {retry_after}s…")
                time.sleep(retry_after)
                continue
            if attempt < config.MAX_RETRIES:
                print(f"  ⚠ HTTP {exc.code} — retrying ({attempt}/{config.MAX_RETRIES})…")
                time.sleep(config.RETRY_DELAY)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < config.MAX_RETRIES:
                print(f"  ⚠ Network error — retrying ({attempt}/{config.MAX_RETRIES})…")
                time.sleep(config.RETRY_DELAY)
                continue
            raise

@register_fetcher("optic", "optisign")
class OptisignFetcher(Fetcher):
    """Fetcher implementation for Zendesk Optisign articles."""
    
    def __init__(self):
        super().__init__()
        self.provider = "optic"

    def get_articles(self) -> Iterator[Dict[str, Any]]:
        """Yield all articles from Zendesk API."""
        url: str | None = f"{config.BASE_URL}?per_page={config.PER_PAGE}"
        page = 0

        while url:
            page += 1
            print(f"── Page {page} ──")
            data = fetch_json(url)

            articles = data.get("articles", [])
            if not articles:
                print("  No articles on this page.")
                break

            for article in articles:
                yield article

            url = data.get("next_page")
            if url:
                time.sleep(config.RATE_LIMIT_PAUSE)

