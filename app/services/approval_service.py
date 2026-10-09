from datetime import datetime, timezone
from typing import Optional
from app.models.advisory import ApprovalResponse
from app.repositories.approval_repository import ApprovalRepository


class ApprovalService:
    """Service layer for Human-in-the-Loop approval gate workflow."""

    def __init__(self, repository: Optional[ApprovalRepository] = None):
        self.repository = repository or ApprovalRepository()

    def approve_request(self, request_id: str, reviewer_comments: Optional[str] = None) -> Optional[ApprovalResponse]:
        record = self.repository.get_request(request_id)
        if not record:
            return None

        success = self.repository.update_approval_status(
            request_id=request_id,
            status="APPROVED",
            reviewer_comments=reviewer_comments or "Approved by human advisor."
        )

        if not success:
            return None

        return ApprovalResponse(
            request_id=request_id,
            status="completed",
            decision="APPROVED",
            reviewer_comments=reviewer_comments or "Approved by human advisor.",
            updated_at=datetime.now(timezone.utc).isoformat()
        )

    def reject_request(self, request_id: str, reviewer_comments: Optional[str] = None) -> Optional[ApprovalResponse]:
        record = self.repository.get_request(request_id)
        if not record:
            return None

        success = self.repository.update_approval_status(
            request_id=request_id,
            status="REJECTED",
            reviewer_comments=reviewer_comments or "Rejected by human advisor."
        )

        if not success:
            return None

        return ApprovalResponse(
            request_id=request_id,
            status="completed",
            decision="REJECTED",
            reviewer_comments=reviewer_comments or "Rejected by human advisor.",
            updated_at=datetime.now(timezone.utc).isoformat()
        )
