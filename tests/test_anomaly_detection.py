import pytest
from app.models.transaction import Transaction
from app.tools.anomaly_detection import DeterministicAnomalyDetector


def test_no_transactions():
    detector = DeterministicAnomalyDetector()
    anomalies = detector.detect_anomalies([], monthly_expenses=5000)
    assert len(anomalies) == 0


def test_normal_transactions_no_anomalies():
    detector = DeterministicAnomalyDetector(zscore_threshold=2.5)
    txs = [
        Transaction(id="T1", date="2026-09-01", amount=-1000, category="groceries"),
        Transaction(id="T2", date="2026-09-02", amount=-1200, category="utilities"),
        Transaction(id="T3", date="2026-09-03", amount=-1100, category="dining"),
        Transaction(id="T4", date="2026-09-04", amount=-1050, category="transportation"),
    ]
    anomalies = detector.detect_anomalies(txs, monthly_expenses=4350)
    # No single transaction z-score >= 2.5
    z_anomalies = [a for a in anomalies if a.type == "TRANSACTION_ANOMALY"]
    assert len(z_anomalies) == 0


def test_large_transaction_zscore_anomaly():
    detector = DeterministicAnomalyDetector(zscore_threshold=2.5)
    txs = [
        Transaction(id="T1", date="2026-09-01", amount=-1000, category="groceries"),
        Transaction(id="T2", date="2026-09-02", amount=-1500, category="dining"),
        Transaction(id="T3", date="2026-09-03", amount=-2000, category="utilities"),
        Transaction(id="T4", date="2026-09-04", amount=-1800, category="transportation"),
        Transaction(id="T5", date="2026-09-05", amount=-1200, category="shopping"),
        Transaction(id="T6", date="2026-09-06", amount=-1400, category="groceries"),
        Transaction(id="T7", date="2026-09-07", amount=-1600, category="dining"),
        Transaction(id="T8", date="2026-09-08", amount=-1300, category="utilities"),
        Transaction(id="T9", date="2026-09-09", amount=-45000, category="travel"),
    ]
    anomalies = detector.detect_anomalies(txs, monthly_expenses=56800)
    z_anomalies = [a for a in anomalies if a.type == "TRANSACTION_ANOMALY"]
    assert len(z_anomalies) >= 1
    assert z_anomalies[0].transaction_id == "T9"
    assert z_anomalies[0].severity in ["MEDIUM", "HIGH"]


def test_spending_spike_anomaly():
    detector = DeterministicAnomalyDetector(spending_spike_threshold=1.5)
    txs = [Transaction(id="T1", date="2026-09-01", amount=-10000, category="travel")]
    anomalies = detector.detect_anomalies(txs, monthly_expenses=15000, historical_monthly_avg=8000)
    spike_anomalies = [a for a in anomalies if a.type == "SPENDING_SPIKE"]
    assert len(spike_anomalies) == 1
    assert spike_anomalies[0].score == 1.88


def test_category_concentration_anomaly():
    detector = DeterministicAnomalyDetector(category_concentration_threshold=0.40)
    txs = [
        Transaction(id="T1", date="2026-09-01", amount=-15000, category="shopping"),
        Transaction(id="T2", date="2026-09-02", amount=-22000, category="shopping"),
        Transaction(id="T3", date="2026-09-03", amount=-5000, category="dining"),
    ]
    anomalies = detector.detect_anomalies(txs, monthly_expenses=42000)
    conc_anomalies = [a for a in anomalies if a.type == "CATEGORY_CONCENTRATION"]
    assert len(conc_anomalies) == 1
    assert "shopping" in conc_anomalies[0].reason.lower()
