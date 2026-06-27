# Bot Stimulator

Bot Stimulator CLI is a tool designed to fetch articles and upload them to OpenAI's Vector Store, keeping your AI assistants up to date.

## Project Structure

```text
.
├── Dockerfile
├── README.md
├── REQUIREMENTS.md
├── main.py
├── requirements.txt
├── resources/           # Stores sync status and scraped files
├── src/
│   ├── config.py        # Configuration and env variables
│   ├── scheduler/       # APScheduler setup for cron jobs
│   ├── scrapper/        # Logic to fetch and parse articles
│   ├── uploader/        # Logic to format and upload to Vector Stores
│   └── utils/           # Helper utilities (HTML to Markdown parsing)
└── tests/               # Unit tests
```

## Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:Dativerse/bot-stimulator.git
   cd bot-stimulator
   ```

2. **Environment Variables:**
   Copy the example environment file and fill in your keys.
   ```bash
   cp .env.example .env
   ```
   *Required variables in `.env`:*
   - `OPENAI_API_KEY`: Your OpenAI API Key.
   - `CRON_SCHEDULE`: Desired cron schedule (e.g., `"0 0 * * *"` for daily).

3. **Install Dependencies (Local setup):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## How to Run Locally

You can run the application directly using Python or via Docker.

### Using Python

The application provides a CLI with the following commands:

- **Fetch articles:**
  ```bash
  python main.py fetch
  ```

- **Upload local articles to OpenAI Vector Store:**
  ```bash
  python main.py upload
  ```

- **Sync (Fetch and immediately Upload):**
  ```bash
  python main.py sync
  ```

- **Run scheduled cron job:**
  ```bash
  python main.py cron
  ```

### Using Docker

1. **Build the image:**
   ```bash
   docker build -t bot-stimulator .
   ```

2. **Run the container (example running sync task):**
   docker run --rm --env-file .env bot-stimulator python main.py sync
   ```

## OpenAI Chunking Strategy

This project utilizes a **Static Chunking Strategy** with a maximum size of `1000` tokens and an overlap of `200` tokens when uploading articles to the Vector Store.

**Why Static (1000 Tokens)?**
- Based on our metadata analysis of over 400 articles, the content is highly structured using Markdown headers (`#`, `##`, `###`).
- **99% of all header-separated sections are under ~750 tokens**.
- By setting a strict `1000` token limit, we ensure that nearly all semantic sections remain perfectly intact within a single chunk without being severed.
- For the rare 1% of outlier sections that are abnormally large, this static limit acts as a crucial backstop to ensure chunks remain optimally sized for the `text-embedding` models, maintaining high retrieval precision.

## Daily Job Logs

The automated daily sync is managed through our CI/CD pipeline. View the job logs here:
- [GitHub Actions - Bot Stimulator Logs](https://github.com/Dativerse/bot-stimulator/actions)
- [Live Job Logs Server](http://137.184.27.194:8080/)

## Screenshot of Playground Answer

![Playground Answer](resources/envidence/Assistant%20&%20Programmatically%20Load%20Vector%20Store.png)
