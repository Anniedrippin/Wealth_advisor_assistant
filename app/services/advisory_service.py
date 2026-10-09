from typing import Dict, Any, Optional
from app.agents.orchestrator import OrchestratorAgent
from app.models.client import ClientFinancialInput
from app.models.analysis import FinancialAnalysis
from app.models.advisory import StructuredAdvisoryResponse, AdvisoryInsight
from app.repositories.approval_repository import ApprovalRepository


class AdvisoryService:
    """Service layer for wealth advisory operations."""

    def __init__(
        self,
        orchestrator: Optional[OrchestratorAgent] = None,
        repository: Optional[ApprovalRepository] = None
    ):
        self.repository = repository or ApprovalRepository()
        self.orchestrator = orchestrator or OrchestratorAgent(repository=self.repository)

    async def analyze_client(
        self,
        client_input: ClientFinancialInput,
        request_id: Optional[str] = None
    ) -> StructuredAdvisoryResponse:
        # Check idempotency / existing request if request_id specified
        if request_id:
            existing = self.repository.get_request(request_id)
            if existing and existing.get("status") in ["completed", "PENDING_HUMAN_REVIEW", "APPROVED"]:
                return self._build_response_from_dict(existing)

        # Run multi-agent orchestrator state machine
        input_dict = client_input.model_dump()
        final_state = await self.orchestrator.run_analysis_pipeline(input_dict, request_id=request_id)

        req_id = final_state["request_id"]
        status = final_state.get("status", "completed")
        analysis_dict = final_state.get("analysis", {})
        insights_dict = final_state.get("insights", {})

        response = StructuredAdvisoryResponse(
            request_id=req_id,
            status=status,
            client_id=final_state["client_id"],
            analysis=FinancialAnalysis(**analysis_dict),
            insights=AdvisoryInsight(**insights_dict),
            memory_used=len(final_state.get("historical_memories", [])) > 0,
            crm_context_available=final_state.get("crm_context_available", False),
            requires_human_review=final_state.get("requires_human_review", False),
            human_review_details={
                "status": status,
                "execution_logs": final_state.get("execution_logs", [])
            }
        )

        return response

    def get_advisory_status(self, request_id: str) -> Optional[StructuredAdvisoryResponse]:
        record = self.repository.get_request(request_id)
        if not record:
            return None
        return self._build_response_from_dict(record)

    def _build_response_from_dict(self, record: Dict[str, Any]) -> StructuredAdvisoryResponse:
        analysis_data = record.get("analysis_data") or {}
        insights_data = record.get("insights_data") or {}

        return StructuredAdvisoryResponse(
            request_id=record["request_id"],
            status=record["status"],
            client_id=record["client_id"],
            analysis=FinancialAnalysis(**analysis_data),
            insights=AdvisoryInsight(**insights_data),
            memory_used=False,
            crm_context_available=True,
            requires_human_review=record.get("requires_human_review", False),
            human_review_details={
                "status": record["status"],
                "reviewer_comments": record.get("reviewer_comments")
            }
        )
