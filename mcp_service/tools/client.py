import os
import requests
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

class MattermostClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        raw_url = base_url or os.getenv("MATTERMOST_URL", "http://127.0.0.1:8065/mattermost")
        self.base_url = raw_url.rstrip("/")
        if not self.base_url.endswith("/api/v4"):
            self.api_url = f"{self.base_url}/api/v4"
        else:
            self.api_url = self.base_url
            
        self.token = token or os.getenv("MATTERMOST_USER_TOKEN") or os.getenv("MATTERMOST_BOT_TOKEN", "")
        self.host_header = os.getenv("MATTERMOST_HOST_HEADER", "dinamica1.fciencias.unam.mx")

    def _get_headers(self, override_token: Optional[str] = None) -> Dict[str, str]:
        tok = override_token or self.token
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": self.host_header,
            "X-Forwarded-Proto": "https"
        }
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        return headers

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, override_token: Optional[str] = None) -> Any:
        url = f"{self.api_url}{endpoint}"
        resp = requests.get(url, headers=self._get_headers(override_token), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, data: Dict[str, Any], override_token: Optional[str] = None) -> Any:
        url = f"{self.api_url}{endpoint}"
        resp = requests.post(url, headers=self._get_headers(override_token), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def put(self, endpoint: str, data: Dict[str, Any], override_token: Optional[str] = None) -> Any:
        url = f"{self.api_url}{endpoint}"
        resp = requests.put(url, headers=self._get_headers(override_token), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def delete(self, endpoint: str, override_token: Optional[str] = None) -> bool:
        url = f"{self.api_url}{endpoint}"
        resp = requests.delete(url, headers=self._get_headers(override_token), timeout=30)
        resp.raise_for_status()
        return True
