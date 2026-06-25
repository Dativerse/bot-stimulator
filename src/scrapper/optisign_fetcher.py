import json
import time
import urllib.request
import urllib.error
import ssl
import certifi
from typing import Iterator, Dict, Any
from src import config
from .base import Fetcher
from .factory import register_fetcher


def _attempt_fetch_json(url: str, context: ssl.SSLContext, attempt: int) -> tuple[bool, dict | None]:
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "ArticleFetcher/1.0",
        })
        with urllib.request.urlopen(req, timeout=30, context=context) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            retry_after = int(exc.headers.get("Retry-After", config.RETRY_DELAY))
            print(f"  ⏳ Rate-limited. Waiting {retry_after}s…")
            time.sleep(retry_after)
            return False, None
        if attempt < config.MAX_RETRIES:
            print(f"  ⚠ HTTP {exc.code} — retrying ({attempt}/{config.MAX_RETRIES})…")
            time.sleep(config.RETRY_DELAY)
            return False, None
        raise
    except (urllib.error.URLError, TimeoutError) as exc:
        if attempt < config.MAX_RETRIES:
            print(f"  ⚠ Network error — retrying ({attempt}/{config.MAX_RETRIES})…")
            time.sleep(config.RETRY_DELAY)
            return False, None
        raise

def fetch_json(url: str) -> dict:
    """GET a URL and return parsed JSON, with retries."""
    context = ssl.create_default_context(cafile=certifi.where())
    for attempt in range(1, config.MAX_RETRIES + 1):
        success, data = _attempt_fetch_json(url, context, attempt)
        if success:
            return data

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

