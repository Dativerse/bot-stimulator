import json
import re
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any
from pathlib import Path
from src import config
from src.utils.parser import html_to_markdown
from src.enums import SyncStatus

class Fetcher(ABC):
    """Abstract base class for all article fetchers."""
    
    def __init__(self):
        self.provider = "base"

    @abstractmethod
    def get_articles(self) -> Iterator[Dict[str, Any]]:
        """Yield articles fetched from the specific provider."""

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

    def _get_article_status(self, filepath: Path, article: dict, filename: str, stage_data: dict) -> SyncStatus:
        """Determine if an article is New, Modified, or Unchanged."""
        if not filepath.exists():
            return SyncStatus.NEW
        
        existing_content = filepath.read_text(encoding="utf-8")
        match = re.search(r"^updated_at:\s*(.*)$", existing_content, re.MULTILINE)
        if not match:
            return SyncStatus.MODIFIED
            
        existing_updated_at = match.group(1).strip()
        new_updated_at = str(article.get('updated_at', '')).strip()
        
        if existing_updated_at != new_updated_at:
            return SyncStatus.MODIFIED
            
        return stage_data[filename]["status"]

    def _delete_file_safe(self, deleted_filepath: Path, deleted_filename: str):
        try:
            deleted_filepath.unlink()
            print(f"  [Deleted] {deleted_filename}")
        except Exception as e:
            print(f"  [Error Deleting] {deleted_filename} - {str(e)}")

    def _handle_deleted_files(self, existing_files: set, stage_data: dict, stats: dict):
        """Remove leftover files and update stage data."""
        for deleted_filename in existing_files:
            if deleted_filename not in stage_data:
                stage_data[deleted_filename] = {}
            stage_data[deleted_filename]["status"] = SyncStatus.DELETED
            
            stats["total_deleted"] += 1
            deleted_filepath = config.ARTICLES_DIR / deleted_filename
            self._delete_file_safe(deleted_filepath, deleted_filename)

    def _write_stage_file(self, stage_data: dict) -> Path:
        """Write the sync stage file and return its path."""
        stage_file = config.RESOURCES_DIR / "sync_stage.json"
        with open(stage_file, "w") as f:
            json.dump(stage_data, f, indent=4)
        return stage_file

    def _print_summary(self, stats: dict):
        """Print the final sync summary."""
        print(f"\nDone! Processed {stats['total_processed']} articles.")
        print(f"   New: {stats['total_added']}")
        print(f"   Modified: {stats['total_updated']}")
        print(f"   Uploaded: {stats['total_skipped']}")
        if stats.get('total_synced', 0) > 0:
            print(f"   Synced: {stats['total_synced']}")
        print(f"   Deleted: {stats['total_deleted']}")
        if stats['total_errors'] > 0:
            print(f"   Errors: {stats['total_errors']}")
        print(f"   Saved to {config.ARTICLES_DIR}")

    def _process_article_safe(self, article: dict, existing_files: set, stage_data: dict, stats: dict):
        try:
            filename = self._make_filename(article)
            filepath = config.ARTICLES_DIR / filename
            
            status = self._get_article_status(filepath, article, filename, stage_data)

            if status in (SyncStatus.NEW, SyncStatus.MODIFIED):
                md_content = self._article_to_markdown(article)
                filepath.write_text(md_content, encoding="utf-8")

            if filename not in stage_data:
                stage_data[filename] = {}
            stage_data[filename]["status"] = status
            
            existing_files.discard(filename)

            if status == SyncStatus.NEW:
                stats["total_added"] += 1
                print(f"  [New] {filename}")
            elif status == SyncStatus.MODIFIED:
                stats["total_updated"] += 1
                print(f"  [Modified] {filename}")
            elif status == SyncStatus.UPLOADED:
                stats["total_skipped"] += 1
                print(f"  [Uploaded] {filename}")
            elif status == SyncStatus.SYNCED:
                stats["total_synced"] += 1
                print(f"  [Synced] {filename}")

        except Exception as e:
            stats["total_errors"] += 1
            print(f"  [Error] {article.get('id', 'Unknown')} - {str(e)}")

    def fetch_or_update(self) -> Path:
        """Fetch all articles from the configured provider and save them locally."""
        config.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

        stats = {
            "total_processed": 0, "total_added": 0, "total_updated": 0,
            "total_skipped": 0, "total_deleted": 0, "total_errors": 0,
            "total_synced": 0
        }
        
        # Track existing files to find deleted ones
        existing_files = set(f.name for f in config.ARTICLES_DIR.glob("*.md"))
        
        stage_file = config.RESOURCES_DIR / "sync_stage.json"
        existing_stage_data = {}
        if stage_file.exists():
            try:
                with open(stage_file, "r") as f:
                    existing_stage_data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: sync_stage.json is corrupted. Starting fresh.")

        # stage_data is initialized from existing to preserve uploader's data (like file_id)
        stage_data = existing_stage_data.copy()

        print(f"Fetching articles using provider: {self.provider}…")
        print(f"Saving to: {config.ARTICLES_DIR}\n")

        for article in self.get_articles():
            stats["total_processed"] += 1
            self._process_article_safe(article, existing_files, stage_data, stats)

        self._handle_deleted_files(existing_files, stage_data, stats)
        self._print_summary(stats)
            
        stage_file = self._write_stage_file(stage_data)
        print(f"   Stage file created at {stage_file}")
        
        return stage_file
