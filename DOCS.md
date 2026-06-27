# Bot Stimulator: Approach and Rationale

This document maps the project's core requirements to the implemented architecture, explaining *why* specific engineering decisions were made to ensure a robust, production-ready, and scalable solution.

## Requirement 1: Scrape & Normalize to Markdown
**Goal**: Ingest messy web content from Optisign, convert to clean Markdown, save as `<slug>.md`, and remove nav/ads.

### Approach & Rationale
- **HTML to Markdown Parsing Strategy**: Instead of naive text extraction, a custom HTML-to-Markdown parser was built (`src/utils/parser.py`). 
  - *Why?* High-quality vector embeddings rely on clean, structured text. By filtering out non-content elements (`ignore_tags`, scripts, ads) and preserving semantic structures (headings, code blocks), we maximize the relevance of LLM retrieval. Noise reduces accuracy; structure enhances it.

## Requirement 2: Programmatically Load Vector Store & Chunking
**Goal**: Upload Markdown files to OpenAI Vector Store via API. Explain chunking strategy.

### Approach & Rationale
- **Chunking Strategy - `auto` over `static`**: The `OpenAIUploader` relies on OpenAI's `auto` chunking strategy for the Vector Store.
  - *Why?* Because we explicitly pre-processed the messy HTML into well-structured Markdown, OpenAI's `auto` strategy can leverage semantic markers (`# Headers`, paragraphs) to chunk the document intelligently. A static token count would arbitrarily slice sentences in half, destroying context. The engineering effort was placed on *data preparation* (clean Markdown) rather than *re-inventing chunking algorithms*.

## Requirement 3: Deploy as Daily Job & Delta Sync
**Goal**: Wrap in `main.py`, Dockerize, schedule daily, upload only deltas (new/updated), log counts.

### Approach & Rationale
- **Robust Delta Detection via State Management**: A `sync_stage.json` file is utilized to track the state of each article (`New`, `Modified`, `Uploaded`, `Synced`, `Deleted`) based on timestamps and content hashes.
  - *Why?* Fetching all articles and blindly re-uploading them is inefficient and costly (OpenAI API limits and billing). The state file acts as a local cache/ledger, ensuring only necessary delta operations are performed on the remote Vector Store. Furthermore, this robust state tracking mechanism ensures the application is **fully compatible with being re-deployed while running**. If a redeployment interrupts an active sync, the new container will safely pick up right where the previous one left off without duplicating effort or losing data.
- **Reactive Error Handling (No Defensive Clutter)**: The codebase eschews deep `if-else` defensive checks (like `os.path.exists`) in favor of idiomatic Python `try-except` blocks.
  - *Why?* Proactive checks are subject to race conditions and clutter business logic. Reactive handling ensures that if a single file fails (e.g., permission issue, network timeout), the job logs the error and continues processing the rest of the batch, preventing a complete job failure.
- **Dual-Mode Scheduling (APScheduler)**: The job is orchestrated via `src/scheduler/base.py`.
  - *Why?* The scheduler is configured to run the sync *immediately* upon startup and then on a recurring `CRON_SCHEDULE`. This ensures that deploying the Docker container yields immediate results, while simultaneously satisfying the daily recurring requirement without manual intervention.

## Shared Architecture: The Extensible Provider Pattern

Both the **Fetcher** (Scrapper) and the **Uploader** share the exact same architectural DNA, combining the **Factory Pattern** and the **Strategy/Template Method Pattern**. 

### Architecture Diagram

```text
                        +--------------------------------+
                        |                                |
                        |            main.py             |
                        |                                |
                        +----------------+---------------+
                                         |
                                         v
                        +--------------------------------+
                        |                                |
                        |      src/utils/factory.py      |
                        |                                |
                        +--------+---------------+-------+
                                 |               |
               +-----------------+               +-----------------+
               |                                                   |
               v                                                   v
    +-------------------------+                         +-------------------------+
    |                         |                         |                         |
    |      BaseScrapper       |                         |      BaseUploader       |
    |  (src/scrapper/base.py) |                         | (src/uploader/base.py)  |
    |                         |                         |                         |
    +-----------+-------------+                         +-----------+-------------+
                |                                                   |
                v                                                   v
    +-------------------------+                         +-------------------------+
    |                         |                         |                         |
    |     OptisignFetcher     |                         |     OpenAIUploader      |
    | (src/scrapper/optisign_ |                         | (src/uploader/openai_   |
    |       fetcher.py)       |                         |       uploader.py)      |
    +-------------------------+                         +-------------------------+
```

### Approach & Rationale
- **The Factory Registry (`src/utils/factory.py`)**: Both modules are instantiated dynamically using a shared Registry. `main.py` is entirely decoupled from concrete implementations. It simply asks the factory for the provider specified in `.env`.
- **Base Class Abstractions**: Both implement a base class (`BaseScrapper` in `src/scrapper/base.py` and `BaseUploader` in `src/uploader/base.py`) that handles universal orchestration logic (like reading/writing to `sync_stage.json`, calculating deltas, and logging). The child classes (e.g., `OptisignFetcher`, `OpenAIUploader`) only implement the API-specific integration.
  - *Why?* This rigorously adheres to the **Open/Closed Principle** (open for extension, closed for modification) and ensures absolute **Separation of Concerns**. If the business transitions from Optisign to Intercom tomorrow, or from OpenAI to Pinecone next week, a new class is simply registered without touching a single line of the core orchestration logic in `main.py`.

## Summary of Senior Engineering Practices
1. **Separation of Concerns**: Heavy utilization of Factories, Base classes, and modular utilities.
2. **Data-Centric Focus**: Understanding that AI applications require a high signal-to-noise ratio; thus, investing heavily in the Markdown parser to optimize downstream LLM ingestion.
3. **Resilience**: Graceful degradation via `try-except`, avoiding catastrophic failures on partial data issues.
4. **Maintainability**: High unit test coverage (`tests/`) ensuring that core parsing and orchestration logic remain stable through future refactors.
