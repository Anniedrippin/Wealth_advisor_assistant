import json
from pathlib import Path
from typing import Optional
import httpx
from app.config import settings
from app.logging_config import logger
from app.models.client import CRMClientProfile
from app.tools.base import CRMTool


class MockCRMTool(CRMTool):
    """In-memory or file-based mock CRM tool for deterministic/offline mode."""

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else Path(__file__).parents[2] / "mock_crm" / "data" / "clients.json"
        self._cache = {}

    def _load(self):
        if not self._cache and self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)

    async def get_client(self, client_id: str) -> Optional[CRMClientProfile]:
        self._load()
        if client_id in self._cache:
            return CRMClientProfile(**self._cache[client_id])
        return None


class HTTPCRMTool(CRMTool):
    """HTTP client CRM tool that interacts with the Mock CRM REST API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 3.0):
        self.base_url = base_url or settings.CRM_BASE_URL
        self.timeout = timeout

    async def get_client(self, client_id: str) -> Optional[CRMClientProfile]:
        url = f"{self.base_url.rstrip('/')}/mock-crm/clients/{client_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return CRMClientProfile(**data)
                elif response.status_code == 404:
                    logger.warning(f"CRM Client not found: {client_id}", extra={"event": "crm_404", "client_id": client_id})
                    return None
                else:
                    logger.error(f"CRM API error {response.status_code}: {response.text}", extra={"event": "crm_error", "client_id": client_id})
                    return None
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"CRM HTTP request failed: {str(e)}", extra={"event": "crm_timeout", "client_id": client_id, "error": str(e)})
            return None
