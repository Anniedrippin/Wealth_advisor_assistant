import math
from typing import List
from app.models.transaction import Transaction
from app.models.analysis import FinancialAnalysis
from app.tools.base import FinancialAnalysisTool


class DefaultFinancialAnalysisTool(FinancialAnalysisTool):
    """Pure Python deterministic financial analysis engine."""

    def analyze_financials(
        self,
        income: float,
        monthly_expenses: float,
        transactions: List[Transaction]
    ) -> FinancialAnalysis:
        net_cash_flow = income - monthly_expenses
        expense_ratio = round(monthly_expenses / income, 4) if income > 0 else 1.0
        savings_rate = round(max(0.0, 1.0 - expense_ratio), 4)

        category_breakdown = {}
        total_tx_expense = 0.0

        for tx in transactions:
            # Expense amounts are stored as negative or positive values. Take magnitude for expenses.
            amt = abs(tx.amount)
            total_tx_expense += amt
            category_breakdown[tx.category] = category_breakdown.get(tx.category, 0.0) + amt

        category_percentages = {}
        if total_tx_expense > 0:
            for cat, amt in category_breakdown.items():
                category_percentages[cat] = round(amt / total_tx_expense, 4)

        avg_tx_amount = round(total_tx_expense / len(transactions), 2) if transactions else 0.0

        return FinancialAnalysis(
            income=income,
            expenses=monthly_expenses,
            net_cash_flow=net_cash_flow,
            expense_ratio=expense_ratio,
            savings_rate=savings_rate,
            category_breakdown=category_breakdown,
            category_percentages=category_percentages,
            anomalies=[],
            total_transaction_expenses=total_tx_expense,
            avg_transaction_amount=avg_tx_amount
        )
