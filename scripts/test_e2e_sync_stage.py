import json
import tempfile
import sys
from io import StringIO
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from src import config
from src.scrapper.base import Fetcher
from src.uploader.base import Uploader

class DummyFetcher(Fetcher):
    def __init__(self):
        super().__init__()
        self.provider = "dummy"
        self.articles_to_return = []

    def get_articles(self) -> Iterator[Dict[str, Any]]:
        for article in self.articles_to_return:
            yield article

class DummyUploader(Uploader):
    def execute_new(self, filename: str) -> Optional[str]:
        print(f"  [DummyUploader] execute_new for {filename}")
        return f"file_id_{filename}"
        
    def execute_update(self, filename: str, file_id: str) -> Optional[str]:
        print(f"  [DummyUploader] execute_update for {filename}, replacing {file_id}")
        return f"file_id_{filename}_v2"
        
    def execute_delete(self, filename: str, file_id: str) -> bool:
        print(f"  [DummyUploader] execute_delete for {filename}, file_id {file_id}")
        return True

def run_e2e_test():
    # Setup temporary directories so we don't mess up actual data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        temp_resources = temp_path / "resources"
        temp_articles = temp_resources / "articles"
        
        temp_resources.mkdir()
        temp_articles.mkdir()

        # Override config paths
        original_resources = config.RESOURCES_DIR
        original_articles = config.ARTICLES_DIR
        
        config.RESOURCES_DIR = temp_resources
        config.ARTICLES_DIR = temp_articles

        try:
            fetcher = DummyFetcher()
            uploader = DummyUploader()
            stage_file = temp_resources / "sync_stage.json"
            
            # --- RUN 1: NEW ---
            print("\n=== RUN 1: Fetching and uploading a new article ===")
            fetcher.articles_to_return = [
                {
                    "id": 100,
                    "title": "Test Article",
                    "body": "<p>Content</p>",
                    "updated_at": "2023-01-01T10:00:00Z"
                }
            ]
            run_and_capture(fetcher, uploader, stage_file)

            # --- RUN 2: UNCHANGED / SYNCED ---
            print("\n=== RUN 2: Fetching the same article (Should stay SYNCED) ===")
            run_and_capture(fetcher, uploader, stage_file)

            # --- RUN 3: MODIFIED ---
            print("\n=== RUN 3: Modifying the article's updated_at (Should re-upload) ===")
            fetcher.articles_to_return = [
                {
                    "id": 100,
                    "title": "Test Article",
                    "body": "<p>Updated Content</p>",
                    "updated_at": "2023-01-02T10:00:00Z"
                }
            ]
            run_and_capture(fetcher, uploader, stage_file)

            # --- RUN 4: DELETED ---
            print("\n=== RUN 4: Returning no articles (Should delete file remotely and locally) ===")
            fetcher.articles_to_return = []
            run_and_capture(fetcher, uploader, stage_file)

        finally:
            # Restore config
            config.RESOURCES_DIR = original_resources
            config.ARTICLES_DIR = original_articles

def run_and_capture(fetcher, uploader, stage_file_path):
    print("Executing fetch_or_update()...")
    # Capture stdout
    captured_output = StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    try:
        fetcher.fetch_or_update()
        print("\nExecuting uploader.upload()...")
        uploader.upload(stage_file_path)
    except Exception as e:
        sys.stdout = original_stdout
        print(f"Exception during run: {e}")
    finally:
        sys.stdout = original_stdout
    
    print("Logs:")
    print("-" * 40)
    print(captured_output.getvalue().strip())
    print("-" * 40)
    
    if stage_file_path.exists():
        with open(stage_file_path, "r") as f:
            stage_data = json.load(f)
            
        print("sync_stage.json state:")
        print(json.dumps(stage_data, indent=2))
    else:
        print("sync_stage.json does not exist yet.")


if __name__ == "__main__":
    run_e2e_test()
