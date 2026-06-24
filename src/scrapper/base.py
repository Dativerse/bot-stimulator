import json
import re
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any
from pathlib import Path
from src import config
from src.utils.parser import html_to_markdown

class Fetcher(ABC):
    """Abstract base class for all article fetchers."""
    
    def __init__(self):
        self.provider = "base"

    @abstractmethod
    def get_articles(self) -> Iterator[Dict[str, Any]]:
        """Yield articles fetched from the specific provider."""
        pass

    def _slugify(self, text: str, max_length: int = 80) -> str:
        """Create a filesystem-safe slug from a title string."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"-{2,}", "-", text)
        text = text.strip("-")
        return text[:max_length].rstrip("-")

    def _make_filename(self, article: dict) -> str:
        """Build a Markdown filename:  <id>-<slug>.md"""
        article_id = article["id"]
        title = article.get("title") or article.get("name") or str(article_id)
        slug = self._slugify(title)
        return f"{article_id}-{slug}.md"

    def _article_to_markdown(self, article: dict) -> str:
        """Convert an article JSON object into a full Markdown document."""
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

    def fetch_or_update(self) -> Path:
        """Fetch all articles from the configured provider and save them locally."""
        config.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

        total_processed = 0
        total_added = 0
        total_updated = 0
        total_skipped = 0
        total_deleted = 0
        total_errors = 0
        
        # Track existing files to find deleted ones
        existing_files = set(f.name for f in config.ARTICLES_DIR.glob("*.md"))
        stage_data = {}

        print(f"Fetching articles using provider: {self.provider}…")
        print(f"Saving to: {config.ARTICLES_DIR}\n")

        for article in self.get_articles():
            total_processed += 1
            try:
                filename = self._make_filename(article)
                filepath = config.ARTICLES_DIR / filename
                
                status = "New"
                if filepath.exists():
                    existing_content = filepath.read_text(encoding="utf-8")
                    match = re.search(r"^updated_at:\s*(.*)$", existing_content, re.MULTILINE)
                    if match:
                        existing_updated_at = match.group(1).strip()
                        new_updated_at = str(article.get('updated_at', '')).strip()
                        if existing_updated_at == new_updated_at:
                            status = "Unchanged"
                        else:
                            status = "Modified"
                    else:
                        status = "Modified"

                if status in ("New", "Modified"):
                    md_content = self._article_to_markdown(article)
                    filepath.write_text(md_content, encoding="utf-8")

                stage_data[filename] = status
                
                if filename in existing_files:
                    existing_files.remove(filename)

                if status == "New":
                    total_added += 1
                    print(f"  [New] {filename}")
                elif status == "Modified":
                    total_updated += 1
                    print(f"  [Modified] {filename}")
                elif status == "Unchanged":
                    total_skipped += 1
                    print(f"  [Unchanged] {filename}")

            except Exception as e:
                total_errors += 1
                print(f"  [Error] {article.get('id', 'Unknown')} - {str(e)}")

        # Handle deleted files
        for deleted_filename in existing_files:
            stage_data[deleted_filename] = "Deleted"
            total_deleted += 1
            deleted_filepath = config.ARTICLES_DIR / deleted_filename
            try:
                deleted_filepath.unlink()
                print(f"  [Deleted] {deleted_filename}")
            except Exception as e:
                print(f"  [Error Deleting] {deleted_filename} - {str(e)}")

        print(f"\nDone! Processed {total_processed} articles.")
        print(f"   New: {total_added}")
        print(f"   Modified: {total_updated}")
        print(f"   Unchanged: {total_skipped}")
        print(f"   Deleted: {total_deleted}")
        if total_errors > 0:
            print(f"   Errors: {total_errors}")
            
        # Write stage file for uploader
        stage_file = config.RESOURCES_DIR / "sync_stage.json"
        with open(stage_file, "w") as f:
            json.dump(stage_data, f, indent=4)

        print(f"   Saved to {config.ARTICLES_DIR}")
        print(f"   Stage file created at {stage_file}")
        return stage_file
