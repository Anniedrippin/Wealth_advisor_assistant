import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.repositories.database import get_connection


class ApprovalRepository:
    """Repository layer for persisting advisory request states and HITL approvals."""

    def __init__(self):
        from app.repositories.database import init_db
        init_db()

    def save_request(
        self,
        request_id: str,
        client_id: str,
        status: str,
        input_data: Dict[str, Any],
        analysis_data: Optional[Dict[str, Any]] = None,
        insights_data: Optional[Dict[str, Any]] = None,
        requires_human_review: bool = False,
        reviewer_comments: Optional[str] = None
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO advisory_requests (
                    request_id, client_id, status, input_data, analysis_data, insights_data,
                    requires_human_review, reviewer_comments, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    status=excluded.status,
                    analysis_data=excluded.analysis_data,
                    insights_data=excluded.insights_data,
                    requires_human_review=excluded.requires_human_review,
                    reviewer_comments=excluded.reviewer_comments,
                    updated_at=excluded.updated_at
                """,
                (
                    request_id,
                    client_id,
                    status,
                    json.dumps(input_data),
                    json.dumps(analysis_data) if analysis_data else None,
                    json.dumps(insights_data) if insights_data else None,
                    1 if requires_human_review else 0,
                    reviewer_comments,
                    now,
                    now
                )
            )
            conn.commit()

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM advisory_requests WHERE request_id = ?", (request_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "request_id": row["request_id"],
                "client_id": row["client_id"],
                "status": row["status"],
                "input_data": json.loads(row["input_data"]) if row["input_data"] else {},
                "analysis_data": json.loads(row["analysis_data"]) if row["analysis_data"] else None,
                "insights_data": json.loads(row["insights_data"]) if row["insights_data"] else None,
                "requires_human_review": bool(row["requires_human_review"]),
                "reviewer_comments": row["reviewer_comments"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    def update_approval_status(self, request_id: str, status: str, reviewer_comments: Optional[str] = None) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE advisory_requests 
                SET status = ?, reviewer_comments = ?, updated_at = ?
                WHERE request_id = ?
                """,
                (status, reviewer_comments, now, request_id)
            )
            conn.commit()
            return cursor.rowcount > 0
