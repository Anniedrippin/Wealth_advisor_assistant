import pytest
from app.models.transaction import Transaction
from app.tools.financial_analysis import DefaultFinancialAnalysisTool


def test_normal_financial_analysis():
    tool = DefaultFinancialAnalysisTool()
    txs = [
        Transaction(id="T1", date="2026-09-01", amount=-1000, category="groceries"),
        Transaction(id="T2", date="2026-09-02", amount=-3000, category="rent"),
    ]
    res = tool.analyze_financials(income=10000, monthly_expenses=4000, transactions=txs)
    
    assert res.income == 10000
    assert res.expenses == 4000
    assert res.net_cash_flow == 6000
    assert res.expense_ratio == 0.40
    assert res.savings_rate == 0.60
    assert res.category_breakdown["groceries"] == 1000
    assert res.category_breakdown["rent"] == 3000
    assert res.category_percentages["rent"] == 0.75


def test_zero_income_financial_analysis():
    tool = DefaultFinancialAnalysisTool()
    res = tool.analyze_financials(income=0, monthly_expenses=2000, transactions=[])
    assert res.expense_ratio == 1.0
    assert res.savings_rate == 0.0
    assert res.net_cash_flow == -2000


def test_zero_expenses_financial_analysis():
    tool = DefaultFinancialAnalysisTool()
    res = tool.analyze_financials(income=5000, monthly_expenses=0, transactions=[])
    assert res.expense_ratio == 0.0
    assert res.savings_rate == 1.0
    assert res.net_cash_flow == 5000
