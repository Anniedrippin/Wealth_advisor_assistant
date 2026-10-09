import pytest
from app.agents.data_fetcher import DataFetcherAgent
from app.tools.base import CRMTool
from app.models.client import CRMClientProfile


class FailingCRMTool(CRMTool):
    async def get_client(self, client_id: str) -> CRMClientProfile | None:
        raise Exception("Simulated CRM 500 Internal Server Error")


@pytest.mark.asyncio
async def test_crm_failure_degraded_mode():
    agent = DataFetcherAgent(crm_tool=FailingCRMTool())
    input_data = {
        "client_id": "C9999",
        "income": 100000,
        "monthly_expenses": 50000,
        "risk_profile": "moderate",
        "transactions": []
    }
    
    # Should not raise exception, should handle CRM failure gracefully
    res = await agent.execute(input_data, "req_err_1")
    assert res["crm_context_available"] is False
    assert res["crm_context"] is None
    assert res["normalized_client_data"]["income"] == 100000


@pytest.mark.asyncio
async def test_invalid_negative_income_validation():
    agent = DataFetcherAgent()
    invalid_input = {
        "client_id": "C1001",
        "income": -5000, # Negative income
        "monthly_expenses": 1000,
        "transactions": []
    }
    
    with pytest.raises(ValueError):
        await agent.execute(invalid_input, "req_err_2")
