import sys
import json
import time
from typing import Dict, Union
from pathlib import Path
from openai import OpenAI
from src import config
from .base import Uploader
from .factory import register_uploader

@register_uploader("openai", "openapi")
class OpenAIUploader(Uploader):
    def __init__(self):
        """Initialize the OpenAI client and uploader configuration."""
        if not config.OPENAI_API_KEY:
            print("Failed to initialize OpenAI client:")
            print("Make sure your OPENAI_API_KEY is correctly set in your .env file.")
            sys.exit(1)

        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.vector_store_name = config.VECTOR_STORE_NAME

    def upload(self, stage_file: Union[Path, str]):
        """Upload saved markdown articles to the OpenAI Vector Store.
        
        Reads the files to upload from the provided `stage_file`.
        """
        stage_path = Path(stage_file)
        if not stage_path.exists():
            print(f"Error: Stage file '{stage_file}' not found.")
            return
        
        with open(stage_path, "r") as f:
            stage_data = json.load(f)
            
        files_to_upload = []
        files_to_delete = {}
        successfully_deleted_filenames = []
        
        # Build filename to file_id map from OpenAI
        try:
            # Note: client.files.list() gets all files across the organization.
            # For large organizations, pagination might be needed.
            all_files_resp = self.client.files.list(limit=1000)
            filename_to_id = {f.filename: f.id for f in all_files_resp.data}
        except Exception as e:
            print(f"Warning: Could not retrieve file IDs from OpenAI: {e}")
            filename_to_id = {}

        for filename, status in stage_data.items():
            filepath = config.ARTICLES_DIR / filename
            
            if status in ("New", "Modified"):
                if not filepath.exists():
                    continue
                    
                files_to_upload.append(filepath)
                
                # If Modified, we need to delete the old version first
                if status == "Modified" and filename in filename_to_id:
                    files_to_delete[filename] = filename_to_id[filename]
                    
            elif status == "Deleted":
                if filename in filename_to_id:
                    files_to_delete[filename] = filename_to_id[filename]
                else:
                    # Already not in OpenAI, consider it successfully deleted
                    successfully_deleted_filenames.append(filename)
        
        print(f"Reading from stage file: {len(files_to_upload)} files to upload, {len(files_to_delete)} files to delete from OpenAI.")
        
        if not files_to_upload and not files_to_delete:
            if successfully_deleted_filenames:
                # Clean up the stage file for items that needed no action
                for filename in successfully_deleted_filenames:
                    if stage_data.get(filename) == "Deleted":
                        del stage_data[filename]
                with open(stage_path, "w") as f:
                    json.dump(stage_data, f, indent=4)
            print("No actionable changes found for OpenAI in stage file.")
            return

        if files_to_upload:
            print(f"Found {len(files_to_upload)} file(s) that need to be uploaded.")
        if files_to_delete:
            print(f"Found {len(files_to_delete)} file(s) that need to be deleted.")

        # 1. Get or create the Vector Store
        print(f"Checking for existing Vector Store named '{self.vector_store_name}'...")
        vector_stores = self.client.vector_stores.list()
        existing_store = next((store for store in vector_stores if store.name == self.vector_store_name), None)

        if existing_store:
            vector_store = existing_store
            print(f"Found existing Vector Store with ID: {vector_store.id}")
        else:
            print("Creating new Vector Store...")
            vector_store = self.client.vector_stores.create(
                name=self.vector_store_name
            )
            print(f"Created Vector Store with ID: {vector_store.id}")

        # 2. Delete any existing files that are being updated
        if files_to_delete:
            print(f"Attempting to delete {len(files_to_delete)} outdated/deleted file(s) from OpenAI...")
            for filename, file_id in files_to_delete.items():
                try:
                    self.client.files.delete(file_id)
                    successfully_deleted_filenames.append(filename)
                except Exception as e:
                    print(f"  Warning: failed to delete file_id {file_id}: {e}")

        # 3. Upload files in a batch
        if files_to_upload:
            print("Uploading files... This might take a minute depending on the number of files.")
            
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                file_streams = [open(path, "rb") for path in files_to_upload]
                
                try:
                    file_batch = self.client.vector_stores.file_batches.upload_and_poll(
                        vector_store_id=vector_store.id,
                        files=file_streams
                    )
                    
                    print("\nUpload Complete!")
                    print(f"Batch Status: {file_batch.status}")
                    print(f"File Counts: {file_batch.file_counts}")
                    break
                    
                except Exception as e:
                    print(f"Upload attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print("Max retries reached. Upload failed.")
                        raise
                finally:
                    for f in file_streams:
                        f.close()

        # Clean up successfully deleted files from the stage_file
        for filename in successfully_deleted_filenames:
            if stage_data.get(filename) == "Deleted":
                del stage_data[filename]
        
        with open(stage_path, "w") as f:
            json.dump(stage_data, f, indent=4)
