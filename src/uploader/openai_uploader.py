import os
import sys
from openai import OpenAI
from src import config

def upload_articles(file_paths=None):
    """Upload saved markdown articles to the OpenAI Vector Store."""
    if not config.OPENAI_API_KEY:
        print("Failed to initialize OpenAI client:")
        print("Make sure your OPENAI_API_KEY is correctly set in your .env file.")
        sys.exit(1)

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    if file_paths is None:
        if not config.ARTICLES_DIR.exists():
            print(f"Error: Directory '{config.ARTICLES_DIR}' not found. Please run 'fetch' command first.")
            sys.exit(1)

        # 1. Collect all markdown file paths
        file_paths = []
        for filepath in config.ARTICLES_DIR.iterdir():
            if filepath.suffix == ".md":
                file_paths.append(filepath)
            
    if not file_paths:
        print("No markdown files found to upload.")
        return

    print(f"Found {len(file_paths)} markdown files. Preparing to upload to Vector Store...")

    # 2. Get or create the Vector Store
    vector_store_name = config.VECTOR_STORE_NAME
    print(f"Checking for existing Vector Store named '{vector_store_name}'...")
    
    vector_stores = client.vector_stores.list()
    existing_store = next((store for store in vector_stores if store.name == vector_store_name), None)

    if existing_store:
        vector_store = existing_store
        print(f"Found existing Vector Store with ID: {vector_store.id}")
    else:
        print("Creating new Vector Store...")
        vector_store = client.vector_stores.create(
            name=vector_store_name
        )
        print(f"Created Vector Store with ID: {vector_store.id}")

    # 3. Upload files in a batch
    print("Uploading files... This might take a minute depending on the number of files.")
    
    # We must pass file objects to the SDK
    file_streams = [open(path, "rb") for path in file_paths]
    
    try:
        # upload_and_poll automatically uploads all files and waits for them to be processed
        file_batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams
        )
        
        print("\nUpload Complete!")
        print(f"Batch Status: {file_batch.status}")
        print(f"File Counts: {file_batch.file_counts}")
        
    finally:
        # Always make sure we close the file streams
        for f in file_streams:
            f.close()
