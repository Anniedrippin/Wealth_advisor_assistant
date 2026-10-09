from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.transaction import Transaction


class ClientFinancialInput(BaseModel):
    client_id: str = Field(..., description="Unique client identifier")
    income: float = Field(..., description="Monthly or annual gross income")
    monthly_expenses: float = Field(..., description="Stated total monthly expenses")
    risk_profile: Optional[str] = Field("moderate", description="Self-reported risk profile")
    transactions: List[Transaction] = Field(default_factory=list, description="List of recent transactions")

    @field_validator("income")
    @classmethod
    def validate_income(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Income cannot be negative")
        return v

    @field_validator("monthly_expenses")
    @classmethod
    def validate_expenses(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Monthly expenses cannot be negative")
        return v


class CRMClientProfile(BaseModel):
    client_id: str
    name: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    existing_products: List[str] = Field(default_factory=list)
    risk_profile: Optional[str] = "moderate"
    financial_goals: List[str] = Field(default_factory=list)


class NormalizedClientData(BaseModel):
    client_id: str
    income: float
    monthly_expenses: float
    risk_profile: str
    transactions: List[Transaction] = Field(default_factory=list)
    crm_profile: Optional[CRMClientProfile] = None
    crm_context_available: bool = False
