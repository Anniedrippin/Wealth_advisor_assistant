from typing import Protocol, List, Dict, Any, Optional
from app.models.client import CRMClientProfile
from app.models.transaction import Transaction, Anomaly
from app.models.analysis import FinancialAnalysis


class CRMTool(Protocol):
    async def get_client(self, client_id: str) -> Optional[CRMClientProfile]:
        """Fetch CRM profile for a given client_id."""
        ...


class FinancialAnalysisTool(Protocol):
    def analyze_financials(
        self,
        income: float,
        monthly_expenses: float,
        transactions: List[Transaction]
    ) -> FinancialAnalysis:
        """Calculate deterministic financial metrics and aggregations."""
        ...


class AnomalyDetectionTool(Protocol):
    def detect_anomalies(
        self,
        transactions: List[Transaction],
        monthly_expenses: float,
        historical_monthly_avg: Optional[float] = None
    ) -> List[Anomaly]:
        """Detect anomalies via Z-score, Spending Spike, and Category Concentration."""
        ...


class MemoryTool(Protocol):
    async def store_memory(self, client_id: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store advisory summary into long-term vector memory."""
        ...

    async def retrieve_memories(self, client_id: str, query: str = "financial goals history risk", limit: int = 3) -> List[str]:
        """Retrieve client-specific historical memories from vector store."""
        ...
