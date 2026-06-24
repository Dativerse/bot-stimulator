import sys
import time
from typing import Dict, Union, List
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

    def _execute_sync(self, files_to_upload: List[Path], files_to_delete: List[str]) -> List[str]:
        """Execute the sync logic specific to OpenAI Vector Store."""
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

        openai_files_to_delete = {}
        for filename in files_to_delete:
            if filename in filename_to_id:
                openai_files_to_delete[filename] = filename_to_id[filename]
            else:
                successfully_deleted_filenames.append(filename)

        print(f"Reading from stage file: {len(files_to_upload)} files to upload, {len(openai_files_to_delete)} files to delete from OpenAI.")

        if not files_to_upload and not openai_files_to_delete:
            print("No actionable changes found for OpenAI in stage file.")
            return successfully_deleted_filenames

        if files_to_upload:
            print(f"Found {len(files_to_upload)} file(s) that need to be uploaded.")
        if openai_files_to_delete:
            print(f"Found {len(openai_files_to_delete)} file(s) that need to be deleted.")

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
        if openai_files_to_delete:
            print(f"Attempting to delete {len(openai_files_to_delete)} outdated/deleted file(s) from OpenAI...")
            for filename, file_id in openai_files_to_delete.items():
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
                        
        return successfully_deleted_filenames
