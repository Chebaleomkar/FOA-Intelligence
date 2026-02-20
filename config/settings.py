"""
Configuration settings for the FOA Intelligence pipeline.
"""

from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "out"
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
ONTOLOGY_PATH = PROJECT_ROOT / "config" / "ontology.yaml"

# Ensure directories exist
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# API Endpoints (No authentication required!)
# ──────────────────────────────────────────────────────────────
GRANTS_GOV_BASE_URL = "https://api.grants.gov"
GRANTS_GOV_SEARCH_URL = f"{GRANTS_GOV_BASE_URL}/v1/api/search2"
GRANTS_GOV_FETCH_URL = f"{GRANTS_GOV_BASE_URL}/v1/api/fetchOpportunity"

NSF_API_BASE_URL = "https://api.nsf.gov/services/v1"
NSF_AWARDS_URL = f"{NSF_API_BASE_URL}/awards.json"

# ──────────────────────────────────────────────────────────────
# Ingestion Settings
# ──────────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 25
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds
RATE_LIMIT_DELAY = 1.0  # seconds between API calls

# ──────────────────────────────────────────────────────────────
# Embedding / Tagging Settings
# ──────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_SIMILARITY_THRESHOLD = 0.35
MAX_TAGS_PER_FOA = 10

# ──────────────────────────────────────────────────────────────
# Source Identifiers
# ──────────────────────────────────────────────────────────────
SOURCE_GRANTS_GOV = "grants_gov"
SOURCE_NSF = "nsf"
