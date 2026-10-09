from typing import List, Dict
from pydantic import BaseModel, Field
from app.models.transaction import Anomaly


class FinancialAnalysis(BaseModel):
    income: float = Field(..., description="Stated or calculated income")
    expenses: float = Field(..., description="Stated or calculated expenses")
    net_cash_flow: float = Field(..., description="Income minus expenses")
    expense_ratio: float = Field(..., description="Expenses divided by income")
    savings_rate: float = Field(..., description="1 - expense_ratio")
    category_breakdown: Dict[str, float] = Field(default_factory=dict)
    category_percentages: Dict[str, float] = Field(default_factory=dict)
    anomalies: List[Anomaly] = Field(default_factory=list)
    total_transaction_expenses: float = Field(0.0)
    avg_transaction_amount: float = Field(0.0)
