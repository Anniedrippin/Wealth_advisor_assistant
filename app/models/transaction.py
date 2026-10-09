from typing import Optional, Literal
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: str = Field(..., description="Unique transaction ID")
    date: str = Field(..., description="ISO date format string (YYYY-MM-DD)")
    amount: float = Field(..., description="Transaction amount (negative for expense, positive for income/credit)")
    category: str = Field(..., description="Expense/income category")
    description: Optional[str] = Field("", description="Transaction description")


class Anomaly(BaseModel):
    transaction_id: str = Field(..., description="Associated transaction ID or category key")
    type: Literal["TRANSACTION_ANOMALY", "SPENDING_SPIKE", "CATEGORY_CONCENTRATION"] = Field(
        ..., description="Type of detected anomaly"
    )
    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Severity level")
    score: float = Field(..., description="Calculated statistical score (z-score, ratio, etc.)")
    reason: str = Field(..., description="Human-readable reason for the anomaly flag")
