from typing import Dict, Any, Optional
from app.config import settings
from app.logging_config import logger
from app.models.client import ClientFinancialInput, CRMClientProfile, NormalizedClientData
from app.tools.base import CRMTool
from app.tools.crm import HTTPCRMTool, MockCRMTool


class DataFetcherAgent:
    """Agent responsible for validating input, fetching CRM context, and normalizing client data."""

    def __init__(self, crm_tool: Optional[CRMTool] = None):
        self.crm_tool = crm_tool or HTTPCRMTool()
        self.mock_crm_tool = MockCRMTool()

    async def execute(self, client_input_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        logger.info(f"Data Fetcher Agent started execution", extra={"request_id": request_id, "agent": "data_fetcher", "event": "start"})
        
        # 1. Validate Input Data
        try:
            client_input = ClientFinancialInput(**client_input_data)
        except Exception as e:
            logger.error(f"Input validation error: {e}", extra={"request_id": request_id, "agent": "data_fetcher", "error": str(e)})
            raise ValueError(f"Invalid client input data: {str(e)}")

        # 2. Retrieve CRM Context (with graceful failure handling)
        crm_profile: Optional[CRMClientProfile] = None
        crm_available = False

        try:
            crm_profile = await self.crm_tool.get_client(client_input.client_id)
            if crm_profile:
                crm_available = True
            else:
                # Try fallback mock CRM tool if HTTP fails
                crm_profile = await self.mock_crm_tool.get_client(client_input.client_id)
                if crm_profile:
                    crm_available = True
                    logger.info("Retrieved CRM data via local mock tool fallback", extra={"request_id": request_id, "agent": "data_fetcher"})
        except Exception as e:
            logger.warning(
                f"CRM API call failed: {e}. Continuing in degraded mode with financial data only.",
                extra={"request_id": request_id, "agent": "data_fetcher", "event": "crm_failure", "error": str(e)}
            )
            crm_profile = None
            crm_available = False

        # 3. Normalize into Common Internal Schema
        risk_profile = client_input.risk_profile or (crm_profile.risk_profile if crm_profile else "moderate")

        normalized = NormalizedClientData(
            client_id=client_input.client_id,
            income=client_input.income,
            monthly_expenses=client_input.monthly_expenses,
            risk_profile=risk_profile,
            transactions=client_input.transactions,
            crm_profile=crm_profile,
            crm_context_available=crm_available
        )

        logger.info(
            f"Data Fetcher completed successfully. CRM Context Available: {crm_available}",
            extra={"request_id": request_id, "agent": "data_fetcher", "event": "complete", "crm_context_available": crm_available}
        )

        return {
            "normalized_client_data": normalized.model_dump(),
            "crm_context": crm_profile.model_dump() if crm_profile else None,
            "crm_context_available": crm_available,
            "client_id": client_input.client_id
        }
