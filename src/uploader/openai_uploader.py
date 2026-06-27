import sys
from typing import Optional
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

    def _get_or_create_vector_store(self):
        if hasattr(self, '_vector_store'):
            return self._vector_store
            
        print(f"Checking for existing Vector Store named '{self.vector_store_name}'...")
        vector_stores = self.client.vector_stores.list()
        existing_store = next((store for store in vector_stores if store.name == self.vector_store_name), None)

        if existing_store:
            self._vector_store = existing_store
            print(f"Found existing Vector Store with ID: {self._vector_store.id}")
        else:
            print("Creating new Vector Store...")
            self._vector_store = self.client.vector_stores.create(
                name=self.vector_store_name
            )
            print(f"Created Vector Store with ID: {self._vector_store.id}")
        return self._vector_store

    def execute_new(self, filename: str) -> Optional[str]:
        file_path = config.ARTICLES_DIR / filename
        if not file_path.exists():
            print(f"File {filename} not found.")
            return None
            
        vector_store = self._get_or_create_vector_store()
        
        try:
            print(f"Uploading {filename} to OpenAI...")
            with open(file_path, "rb") as f:
                response = self.client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            print(f"Attaching {filename} (ID: {response.id}) to Vector Store {vector_store.id}...")
            self.client.vector_stores.files.create_and_poll(
                vector_store_id=vector_store.id,
                file_id=response.id
            )
            print(f"Successfully uploaded and attached {filename}.")
            return response.id
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")
            if 'response' in locals() and hasattr(response, 'id'):
                print(f"Cleaning up orphaned file: {response.id}")
                try:
                    self.client.files.delete(response.id)
                except Exception as cleanup_err:
                    print(f"  Warning: failed to clean up file {response.id}: {cleanup_err}")
            return None

    def execute_update(self, filename: str, file_id: str) -> Optional[str]:
        print(f"Updating {filename} (deleting old file_id: {file_id})...")
        self.execute_delete(filename, file_id)
        return self.execute_new(filename)

    def execute_delete(self, filename: str, file_id: str) -> bool:
        print(f"Deleting {filename} (file_id: {file_id})...")
        try:
            self.client.files.delete(file_id)
            return True
        except Exception as e:
            print(f"  Warning: failed to delete file_id {file_id}: {e}")
            return False
