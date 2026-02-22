import os
from dotenv import load_dotenv

load_dotenv()

PUBLIC_DATA_API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "./data/apt_tracker.db")
DEFAULT_YEARS = 5
PORT = int(os.getenv("PORT", 8000))
