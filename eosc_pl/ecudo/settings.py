import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(os.getenv("ECUDO_OUTPUT_DIR", BASE_DIR / "output"))
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Solr configuration
SOLR_URL = os.getenv("SOLR_URL", "http://localhost:8983")
SOLR_COLLECTIONS = os.getenv("SOLR_EOSCPL_DATASET_COLS_NAME", "")
SOLR_COLLECTION_LIST = SOLR_COLLECTIONS.split()

# ECUDO / Metadata fetch configuration
BASE_URL = os.getenv("ECUDO_BASE_URL", "http://central.ecudo.pl")
TOTAL_RECORDS = int(os.getenv("ECUDO_TOTAL_RECORDS", 500))
PAGE_SIZE = int(os.getenv("ECUDO_PAGE_SIZE", 50))
CONCURRENCY = int(os.getenv("ECUDO_CONCURRENCY", 10))
TIMEOUT = int(os.getenv("ECUDO_TIMEOUT", 15))
MAX_RETRIES = int(os.getenv("ECUDO_MAX_RETRIES", 3))
TARGET_ORG_ID = os.getenv("ECUDO_TARGET_ORG", "iopan")

HEADERS = {
    "User-Agent": os.getenv(
        "ECUDO_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0 Safari/537.36",
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": os.getenv("ECUDO_ACCEPT_LANGUAGE", "en"),
}

# Logging
LOG_FILE = os.getenv("ECUDO_LOG_FILE", str(BASE_DIR / "ecudo.log"))

# File handling
DELETE_FILES_AFTER_SEND = True

# Batch size for fetching metadata / solr updates
BATCH_SIZE = PAGE_SIZE

# Validate required settings
if not SOLR_URL or not SOLR_COLLECTION_LIST:
    raise ValueError(
        "Missing required SOLR_URL or SOLR_EOSCPL_DATASET_COLS_NAME env variables"
    )
