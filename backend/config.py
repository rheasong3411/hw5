"""Shared model and runtime configuration."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".env", override=False)
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MAX_DELEGATION_DEPTH = 3
MAX_REQUESTS = 60
MAX_TOTAL_TOKENS = 120000
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")

if not PORTKEY_API_KEY:
    raise RuntimeError("PORTKEY_API_KEY must be set in the environment or the parent .env file")
