import math
from typing import List, Optional
from app.config import settings
from app.models.transaction import Transaction, Anomaly
from app.tools.base import AnomalyDetectionTool


class DeterministicAnomalyDetector(AnomalyDetectionTool):
    """Pure Python deterministic anomaly detection implementation."""

    def __init__(
        self,
        zscore_threshold: float = settings.ANOMALY_ZSCORE_THRESHOLD,
        spending_spike_threshold: float = settings.SPENDING_SPIKE_THRESHOLD,
        category_concentration_threshold: float = settings.CATEGORY_CONCENTRATION_THRESHOLD
    ):
        self.zscore_threshold = zscore_threshold
        self.spending_spike_threshold = spending_spike_threshold
        self.category_concentration_threshold = category_concentration_threshold

    def detect_anomalies(
        self,
        transactions: List[Transaction],
        monthly_expenses: float,
        historical_monthly_avg: Optional[float] = None
    ) -> List[Anomaly]:
        anomalies: List[Anomaly] = []

        if not transactions:
            return anomalies

        amounts = [abs(t.amount) for t in transactions]
        total_tx_amount = sum(amounts)
        n = len(amounts)

        # 1. Z-Score Anomaly Detection
        if n > 1:
            mean = sum(amounts) / n
            variance = sum((x - mean) ** 2 for x in amounts) / (n - 1)
            std = math.sqrt(variance)

            if std > 0:
                for tx in transactions:
                    amt = abs(tx.amount)
                    z_score = (amt - mean) / std
                    if abs(z_score) >= self.zscore_threshold:
                        severity = "HIGH" if abs(z_score) >= 3.0 else "MEDIUM"
                        anomalies.append(
                            Anomaly(
                                transaction_id=tx.id,
                                type="TRANSACTION_ANOMALY",
                                severity=severity,
                                score=round(z_score, 2),
                                reason=f"Transaction '{tx.id}' of ${amt:,.2f} ({tx.category}) has an anomalous z-score of {z_score:.2f} (mean=${mean:,.2f}, std=${std:,.2f})."
                            )
                        )

        # 2. Spending Spike Detection
        if historical_monthly_avg is not None and historical_monthly_avg > 0:
            spike_ratio = monthly_expenses / historical_monthly_avg
            if spike_ratio >= self.spending_spike_threshold:
                severity = "HIGH" if spike_ratio >= 2.0 else "MEDIUM"
                anomalies.append(
                    Anomaly(
                        transaction_id="MONTHLY_SUMMARY",
                        type="SPENDING_SPIKE",
                        severity=severity,
                        score=round(spike_ratio, 2),
                        reason=f"Current monthly expenses (${monthly_expenses:,.2f}) exceed historical average (${historical_monthly_avg:,.2f}) by {spike_ratio:.1f}x."
                    )
                )

        # 3. Category Concentration Detection
        if total_tx_amount > 0:
            category_totals = {}
            for tx in transactions:
                category_totals[tx.category] = category_totals.get(tx.category, 0.0) + abs(tx.amount)

            for cat, amt in category_totals.items():
                ratio = amt / total_tx_amount
                if ratio >= self.category_concentration_threshold:
                    severity = "HIGH" if ratio >= 0.60 else "MEDIUM"
                    anomalies.append(
                        Anomaly(
                            transaction_id=f"CAT_{cat.upper()}",
                            type="CATEGORY_CONCENTRATION",
                            severity=severity,
                            score=round(ratio, 2),
                            reason=f"Unusual spending concentration: Category '{cat}' accounts for {ratio*100:.1f}% of total recent transaction spending (${amt:,.2f})."
                        )
                    )

        return anomalies
