from typing import Dict, Any, Optional
from app.logging_config import logger
from app.models.client import NormalizedClientData
from app.models.transaction import Transaction
from app.tools.base import FinancialAnalysisTool, AnomalyDetectionTool
from app.tools.financial_analysis import DefaultFinancialAnalysisTool
from app.tools.anomaly_detection import DeterministicAnomalyDetector


class AnalyzerAgent:
    """Agent responsible for deterministic numerical analysis and anomaly detection."""

    def __init__(
        self,
        analysis_tool: Optional[FinancialAnalysisTool] = None,
        anomaly_tool: Optional[AnomalyDetectionTool] = None
    ):
        self.analysis_tool = analysis_tool or DefaultFinancialAnalysisTool()
        self.anomaly_tool = anomaly_tool or DeterministicAnomalyDetector()

    def execute(self, normalized_data_dict: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        logger.info("Analyzer Agent started execution", extra={"request_id": request_id, "agent": "analyzer", "event": "start"})

        normalized = NormalizedClientData(**normalized_data_dict)
        
        # 1. Deterministic Financial Calculations
        analysis = self.analysis_tool.analyze_financials(
            income=normalized.income,
            monthly_expenses=normalized.monthly_expenses,
            transactions=normalized.transactions
        )

        # 2. Deterministic Anomaly Detection
        anomalies = self.anomaly_tool.detect_anomalies(
            transactions=normalized.transactions,
            monthly_expenses=normalized.monthly_expenses
        )

        analysis.anomalies = anomalies

        logger.info(
            f"Analyzer completed. Anomalies detected: {len(anomalies)}",
            extra={"request_id": request_id, "agent": "analyzer", "event": "complete", "anomaly_count": len(anomalies)}
        )

        return {
            "analysis": analysis.model_dump(),
            "anomalies": [a.model_dump() for a in anomalies]
        }
