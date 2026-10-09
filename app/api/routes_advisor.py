from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from app.models.client import ClientFinancialInput
from app.models.advisory import StructuredAdvisoryResponse, ApprovalRequest, ApprovalResponse
from app.services.advisory_service import AdvisoryService
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/advisor", tags=["Advisor"])

advisory_service = AdvisoryService()
approval_service = ApprovalService()


@router.post("/analyze", response_model=StructuredAdvisoryResponse)
async def analyze_financials(
    input_data: ClientFinancialInput,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
):
    """Ingest client financial data and execute multi-agent advisory analysis pipeline."""
    try:
        response = await advisory_service.analyze_client(input_data, request_id=x_request_id)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advisory pipeline execution failed: {str(e)}")


@router.get("/{request_id}", response_model=StructuredAdvisoryResponse)
def get_advisory_status(request_id: str):
    """Retrieve advisory response status and results by request_id."""
    result = advisory_service.get_advisory_status(request_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Request ID '{request_id}' not found.")
    return result


@router.post("/{request_id}/approve", response_model=ApprovalResponse)
def approve_advisory(request_id: str, body: Optional[ApprovalRequest] = None):
    """Human-in-the-Loop approval endpoint."""
    comments = body.reviewer_comments if body else None
    result = approval_service.approve_request(request_id, reviewer_comments=comments)
    if not result:
        raise HTTPException(status_code=404, detail=f"Request ID '{request_id}' not found or cannot be approved.")
    return result


@router.post("/{request_id}/reject", response_model=ApprovalResponse)
def reject_advisory(request_id: str, body: Optional[ApprovalRequest] = None):
    """Human-in-the-Loop rejection/override endpoint."""
    comments = body.reviewer_comments if body else None
    result = approval_service.reject_request(request_id, reviewer_comments=comments)
    if not result:
        raise HTTPException(status_code=404, detail=f"Request ID '{request_id}' not found or cannot be rejected.")
    return result
