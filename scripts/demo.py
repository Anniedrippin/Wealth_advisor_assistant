import asyncio
import json
import os
import sys

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.client import ClientFinancialInput
from app.services.advisory_service import AdvisoryService
from app.services.approval_service import ApprovalService
from app.agents.data_fetcher import DataFetcherAgent
from app.tools.crm import HTTPCRMTool


async def run_demo():
    print("================================================================================")
    print("  MINI MULTI-AGENT WEALTH ADVISOR ASSISTANT - DEMONSTRATION SUITE")
    print("================================================================================")

    advisory_service = AdvisoryService()
    approval_service = ApprovalService()

    # Load sample client datasets
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_clients.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        clients_data = json.load(f)

    # --------------------------------------------------------------------------
    # SCENARIO 1: Client C1001 - Normal Flow
    # --------------------------------------------------------------------------
    print("\n--- SCENARIO 1: Client C1001 (Normal Monthly Activity) ---")
    c1_input = ClientFinancialInput(**clients_data[0])
    res1 = await advisory_service.analyze_client(c1_input)

    print(f"Request ID:           {res1.request_id}")
    print(f"Client ID:            {res1.client_id}")
    print(f"Monthly Income:       ${res1.analysis.income:,.2f}")
    print(f"Monthly Expenses:     ${res1.analysis.expenses:,.2f}")
    print(f"Net Cash Flow:        ${res1.analysis.net_cash_flow:,.2f}")
    print(f"Expense Ratio:        {res1.analysis.expense_ratio*100:.1f}%")
    print(f"Anomalies Count:      {len(res1.analysis.anomalies)}")
    print(f"Overall Risk Tier:    {res1.insights.overall_risk}")
    print(f"Human Review Needed:  {res1.requires_human_review}")
    print(f"Executive Summary:    {res1.insights.executive_summary}")
    print("Recommendations:")
    for r in res1.insights.recommendations:
        print(f"  - [{r.priority}] {r.area}: {r.recommendation}")

    # --------------------------------------------------------------------------
    # SCENARIO 2: Client C1002 - Anomaly Flow & HITL Review
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("--- SCENARIO 2: Client C1002 (Anomalous $45,000 Transaction & HITL Gate) ---")
    c2_input = ClientFinancialInput(**clients_data[1])
    res2 = await advisory_service.analyze_client(c2_input)

    print(f"Request ID:           {res2.request_id}")
    print(f"Client ID:            {res2.client_id}")
    print(f"Status:               {res2.status}")
    print(f"Monthly Income:       ${res2.analysis.income:,.2f}")
    print(f"Monthly Expenses:     ${res2.analysis.expenses:,.2f}")
    print(f"Anomalies Flagged:")
    for a in res2.analysis.anomalies:
        print(f"  * [{a.severity}] Type: {a.type} | ID: {a.transaction_id} | Score: {a.score}")
        print(f"    Reason: {a.reason}")
    print(f"Overall Risk Tier:    {res2.insights.overall_risk}")
    print(f"Human Review Needed:  {res2.requires_human_review}")

    if res2.requires_human_review:
        print("\n>>> HITL Gate Triggered! Approving request via API...")
        app_res = approval_service.approve_request(res2.request_id, reviewer_comments="Approved after client phone verification.")
        print(f"Approval Result: Decision={app_res.decision}, Status={app_res.status}")

    # --------------------------------------------------------------------------
    # SCENARIO 3: Client C1003 - High Risk Signal Flow
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("--- SCENARIO 3: Client C1003 (High Expense Ratio & Category Concentration) ---")
    c3_input = ClientFinancialInput(**clients_data[2])
    res3 = await advisory_service.analyze_client(c3_input)

    print(f"Request ID:           {res3.request_id}")
    print(f"Client ID:            {res3.client_id}")
    print(f"Monthly Income:       ${res3.analysis.income:,.2f}")
    print(f"Monthly Expenses:     ${res3.analysis.expenses:,.2f}")
    print(f"Expense Ratio:        {res3.analysis.expense_ratio*100:.1f}%")
    print(f"Overall Risk Tier:    {res3.insights.overall_risk}")
    print(f"Anomalies Flagged:    {len(res3.analysis.anomalies)}")
    print("Key Findings:")
    for k in res3.insights.key_findings:
        print(f"  - {k}")

    # --------------------------------------------------------------------------
    # SCENARIO 4: CRM API Failure & Degraded Mode
    # --------------------------------------------------------------------------
    print("\n--------------------------------------------------------------------------------")
    print("--- SCENARIO 4: CRM API Failure (Graceful Degraded Mode) ---")
    
    # Simulate CRM call pointing to non-existent endpoint
    broken_crm_tool = HTTPCRMTool(base_url="http://localhost:9999_invalid")
    data_fetcher = DataFetcherAgent(crm_tool=broken_crm_tool)
    
    print("Calling Data Fetcher Agent with invalid CRM base URL...")
    fetch_result = await data_fetcher.execute(clients_data[0], "req_demo_degraded")

    print(f"CRM Context Available: {fetch_result['crm_context_available']}")
    print(f"CRM Context Data:      {fetch_result['crm_context']}")
    print(f"Normalized Income:     ${fetch_result['normalized_client_data']['income']:,.2f}")
    print("Result: System continued processing without crashing, flagging CRM context as unavailable!")
    print("================================================================================\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
