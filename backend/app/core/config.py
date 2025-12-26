import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# App Settings
APP_NAME = "Polished"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# LLM Settings
LLM_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
