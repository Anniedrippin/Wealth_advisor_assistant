import pytest
from app.agents.data_fetcher import DataFetcherAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.insight_agent import InsightAgent
from app.agents.validator import GuardrailValidator


@pytest.mark.asyncio
async def test_data_fetcher_agent():
    agent = DataFetcherAgent()
    input_data = {
        "client_id": "C1001",
        "income": 180000,
        "monthly_expenses": 85000,
        "risk_profile": "moderate",
        "transactions": []
    }
    res = await agent.execute(input_data, "req_test_1")
    assert res["client_id"] == "C1001"
    assert res["normalized_client_data"]["income"] == 180000


def test_analyzer_agent():
    agent = AnalyzerAgent()
    normalized_dict = {
        "client_id": "C1001",
        "income": 180000,
        "monthly_expenses": 85000,
        "risk_profile": "moderate",
        "transactions": [
            {"id": "T1", "date": "2026-09-01", "amount": -45000, "category": "travel", "description": "Flight"}
        ],
        "crm_context_available": True
    }
    res = agent.execute(normalized_dict, "req_test_2")
    assert "analysis" in res
    assert "anomalies" in res


@pytest.mark.asyncio
async def test_insight_agent_deterministic_fallback():
    agent = InsightAgent()
    res = await agent.execute(
        client_id="C1001",
        normalized_data={"income": 180000, "monthly_expenses": 85000, "risk_profile": "moderate"},
        analysis_dict={"income": 180000, "expenses": 85000, "expense_ratio": 0.47, "savings_rate": 0.53, "net_cash_flow": 95000},
        anomalies_list=[],
        crm_context=None,
        request_id="req_test_3"
    )
    assert "insights" in res
    assert res["insights"]["overall_risk"] in ["LOW", "MEDIUM", "HIGH"]


def test_guardrail_validator_pass():
    validator = GuardrailValidator()
    valid_insights = {
        "overall_risk": "MEDIUM",
        "executive_summary": "Client shows stable cash flow.",
        "key_findings": ["Income exceeds expenses."],
        "recommendations": [
            {
                "priority": "HIGH",
                "area": "Cash Flow",
                "recommendation": "Maintain emergency buffer.",
                "reason": "Expense ratio is moderate."
            }
        ],
        "follow_up_questions": [],
        "requires_human_review": False,
        "confidence": 0.90
    }
    passed, err = validator.validate(valid_insights, "C1001", "req_test_4")
    assert passed is True
    assert err is None


def test_guardrail_validator_forbidden_guarantee_fail():
    validator = GuardrailValidator()
    invalid_insights = {
        "overall_risk": "LOW",
        "executive_summary": "Guaranteed return of 20% on this safe stock!",
        "key_findings": ["Risk free profit."],
        "recommendations": [
            {
                "priority": "HIGH",
                "area": "Trading",
                "recommendation": "Buy this stock now for guaranteed returns.",
                "reason": "No risk."
            }
        ],
        "follow_up_questions": [],
        "requires_human_review": False,
        "confidence": 1.0
    }
    passed, err = validator.validate(invalid_insights, "C1001", "req_test_5")
    assert passed is False
    assert "forbidden" in err.lower() or "compliance" in err.lower()
