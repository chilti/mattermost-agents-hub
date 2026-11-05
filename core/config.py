import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MATTERMOST_URL = os.getenv("MATTERMOST_URL", "http://127.0.0.1:8065/mattermost").rstrip("/")
MATTERMOST_WS_URL = os.getenv("MATTERMOST_WS_URL", "ws://127.0.0.1:8065/mattermost/api/v4/websocket")
MATTERMOST_HOST_HEADER = os.getenv("MATTERMOST_HOST_HEADER", "dinamica1.fciencias.unam.mx")
MATTERMOST_BOT_TOKEN = os.getenv("MATTERMOST_BOT_TOKEN", "")
MATTERMOST_BOT_USERNAME = os.getenv("MATTERMOST_BOT_USERNAME", "thinktank-bot")

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "openai/gpt-oss-20b")
