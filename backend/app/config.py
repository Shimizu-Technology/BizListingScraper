"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/bizlistings")

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Scraper
SCRAPE_DELAY_SECONDS = float(os.getenv("SCRAPE_DELAY_SECONDS", "2"))
MAX_PAGES_PER_SCRAPE = int(os.getenv("MAX_PAGES_PER_SCRAPE", "100"))
STALE_THRESHOLD_DAYS = int(os.getenv("STALE_THRESHOLD_DAYS", "3"))
# Target states for scraping (comma-separated)
TARGET_STATES = os.getenv("TARGET_STATES", "MI,CT").split(",")
TARGET_STATE = TARGET_STATES[0]  # Primary state for backward compatibility

# Proxy (optional)
PROXY_URL = os.getenv("PROXY_URL")
