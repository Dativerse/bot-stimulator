import json
import re
import ssl
import time
import urllib.request
import urllib.error
from src import config
from .parser import html_to_markdown

# Workaround for macOS Python SSL certificate issue
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def slugify(text: str, max_length: int = 80) -> str:
    """Create a filesystem-safe slug from a title string."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-")
    return text[:max_length].rstrip("-")

def make_filename(article: dict) -> str:
    """Build a Markdown filename:  <id>-<slug>.md"""
    article_id = article["id"]
    title = article.get("title") or article.get("name") or str(article_id)
    slug = slugify(title)
    return f"{article_id}-{slug}.md"

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

def article_to_markdown(article: dict) -> str:
    """Convert a Zendesk article JSON object into a full Markdown document."""
    title = article.get("title") or article.get("name") or "Untitled"
    body_html = article.get("body") or ""
    body_md = html_to_markdown(body_html) if body_html else "*No content.*"

    # Front-matter metadata
    lines = [
        "---",
        f"title: \"{title}\"",
        f"id: {article['id']}",
        f"url: {article.get('html_url', '')}",
        f"section_id: {article.get('section_id', '')}",
        f"created_at: {article.get('created_at', '')}",
        f"updated_at: {article.get('updated_at', '')}",
        f"edited_at: {article.get('edited_at', '')}",
        f"author_id: {article.get('author_id', '')}",
        f"draft: {article.get('draft', False)}",
        f"promoted: {article.get('promoted', False)}",
    ]
    labels = article.get("label_names")
    if labels:
        lines.append(f"labels: {json.dumps(labels)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(body_md)

    return "\n".join(lines)

def fetch_all_articles():
    """Fetch all articles from Zendesk and save them locally."""
    config.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    url: str | None = f"{config.BASE_URL}?per_page={config.PER_PAGE}"
    page = 0
    total_processed = 0
    total_added = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0
    saved_files = []

    print(f"Fetching articles from Zendesk Help Center…")
    print(f"Saving to: {config.ARTICLES_DIR}\n")

    while url:
        page += 1
        print(f"── Page {page} ──")
        data = fetch_json(url)

        articles = data.get("articles", [])
        if not articles:
            print("  No articles on this page.")
            break

        for article in articles:
            total_processed += 1
            try:
                filename = make_filename(article)
                filepath = config.ARTICLES_DIR / filename
                
                status = "added"
                if filepath.exists():
                    existing_content = filepath.read_text(encoding="utf-8")
                    match = re.search(r"^updated_at:\s*(.*)$", existing_content, re.MULTILINE)
                    if match:
                        existing_updated_at = match.group(1).strip()
                        new_updated_at = str(article.get('updated_at', '')).strip()
                        if existing_updated_at == new_updated_at:
                            status = "skipped"
                        else:
                            status = "updated"
                    else:
                        status = "updated"

                if status in ("added", "updated"):
                    md_content = article_to_markdown(article)
                    filepath.write_text(md_content, encoding="utf-8")
                    saved_files.append(filepath)

                if status == "added":
                    total_added += 1
                    print(f"  [Added] {filename}")
                elif status == "updated":
                    total_updated += 1
                    print(f"  [Updated] {filename}")
                elif status == "skipped":
                    total_skipped += 1
                    print(f"  [Skipped] {filename}")

            except Exception as e:
                total_errors += 1
                print(f"  [Error] {article.get('id', 'Unknown')} - {str(e)}")

        url = data.get("next_page")
        if url:
            time.sleep(config.RATE_LIMIT_PAUSE)

    print(f"\nDone! Processed {total_processed} articles.")
    print(f"   Added: {total_added}")
    print(f"   Updated: {total_updated}")
    print(f"   Skipped: {total_skipped}")
    if total_errors > 0:
        print(f"   Errors: {total_errors}")
    print(f"   Saved to {config.ARTICLES_DIR}")
    return saved_files
