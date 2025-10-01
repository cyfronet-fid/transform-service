import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(os.getenv("OAI_OUTPUT_DIR", BASE_DIR / "output"))

# Solr configuration
SOLR_URL = os.getenv("SOLR_URL", "http://localhost:8983")
SOLR_COLLECTIONS = os.getenv("SOLR_EOSCPL_DATASET_COLS_NAME", "")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))

if not SOLR_URL or not SOLR_COLLECTIONS:
    raise ValueError(
        "Missing required SOLR_URL or SOLR_EOSCPL_DATASET_COLS_NAME env variables"
    )

SOLR_COLLECTION_LIST = SOLR_COLLECTIONS.split()

# Logging
LOG_FILE = os.getenv("OAI_LOG_FILE", str(BASE_DIR / "oai_pmh.log"))

# File handling
DELETE_FILES_AFTER_SEND = True

# Defaults
DEFAULT_METADATA_PREFIX = os.getenv("DEFAULT_METADATA_PREFIX", "oai_dc")
DEFAULT_REPOSITORY = "onedata"
DEFAULT_MAX_RECORDS = 100
