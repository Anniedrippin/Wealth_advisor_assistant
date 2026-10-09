from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from app.models.analysis import FinancialAnalysis
from app.models.transaction import Anomaly


class Recommendation(BaseModel):
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Priority level")
    area: str = Field(..., description="Financial area e.g. Cash Flow, Emergency Fund, Risk Management")
    recommendation: str = Field(..., description="Actionable advisory insight")
    reason: str = Field(..., description="Justification based on data")


class AdvisoryInsight(BaseModel):
    overall_risk: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Calculated risk tier")
    executive_summary: str = Field(..., description="Brief executive overview")
    key_findings: List[str] = Field(default_factory=list, description="Key analytical findings")
    anomalies: List[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    recommendations: List[Recommendation] = Field(default_factory=list, description="List of advisory recommendations")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions for client")
    requires_human_review: bool = Field(False, description="Whether human approval gate is triggered")
    confidence: float = Field(1.0, description="Confidence level in the assessment (0.0 to 1.0)")


class StructuredAdvisoryResponse(BaseModel):
    request_id: str
    status: Literal["completed", "PENDING_HUMAN_REVIEW", "APPROVED", "REJECTED", "FAILED"]
    client_id: str
    analysis: FinancialAnalysis
    insights: AdvisoryInsight
    memory_used: bool = False
    crm_context_available: bool = False
    requires_human_review: bool = False
    human_review_details: Optional[Dict[str, Any]] = None
    disclaimer: str = "This advisory insight is generated for demonstration and decision-support purposes only and does not constitute formal financial, investment, or legal advice."


class ApprovalRequest(BaseModel):
    reviewer_comments: Optional[str] = Field(None, description="Optional notes from human reviewer")


class ApprovalResponse(BaseModel):
    request_id: str
    status: str
    decision: str
    reviewer_comments: Optional[str] = None
    updated_at: str
