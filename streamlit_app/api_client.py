from typing import Dict, Any, Optional
import httpx
from streamlit_app.config import API_BASE_URL


class AdvisoryAPIClient:
    """HTTP client wrapper communicating exclusively with the FastAPI backend."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
        return {"status": "unhealthy"}

    def analyze_client(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/advisor/analyze"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise Exception(f"API Error ({resp.status_code}): {resp.text}")

    def get_advisory_status(self, request_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/advisor/{request_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise Exception(f"API Error ({resp.status_code}): {resp.text}")

    def approve_request(self, request_id: str, reviewer_comments: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/advisor/{request_id}/approve"
        body = {"reviewer_comments": reviewer_comments} if reviewer_comments else {}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=body)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise Exception(f"API Error ({resp.status_code}): {resp.text}")

    def reject_request(self, request_id: str, reviewer_comments: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/advisor/{request_id}/reject"
        body = {"reviewer_comments": reviewer_comments} if reviewer_comments else {}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=body)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise Exception(f"API Error ({resp.status_code}): {resp.text}")

    def get_client_memory(self, client_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/memory/{client_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"client_id": client_id, "count": 0, "memories": []}
