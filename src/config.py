import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
ARTICLES_DIR = RESOURCES_DIR / "articles"

# Zendesk Configuration
BASE_URL = "https://optisignshelp.zendesk.com/api/v2/help_center/en-us/articles"
PER_PAGE = 100
RATE_LIMIT_PAUSE = 1  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 3600  # seconds

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_NAME = "Zendesk Help Articles"

# Scheduler Configuration
CRON_SCHEDULE = os.getenv("CRON_SCHEDULE", "0 0 * * *")
