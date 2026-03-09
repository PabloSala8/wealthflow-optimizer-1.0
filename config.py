import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5")) * 1024 * 1024
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/wealthflow_uploads")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BROKER_SPECS_PATH = os.path.join(BASE_DIR, "data", "broker_specs.json")
SAMPLE_PORTFOLIO_PATH = os.path.join(BASE_DIR, "data", "sample_portfolio.csv")

CANONICAL_FIELDS = [
    "ticker",
    "market_value",
    "cash_sweep",
    "num_options_contracts",
    "account_type",
    "quantity",
    "avg_cost",
    "asset_class",
    "sector",
    "notes",
]

ALLOWED_EXTENSIONS = {"csv"}
