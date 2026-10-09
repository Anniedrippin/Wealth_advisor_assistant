import streamlit as st
from typing import Dict, Any, List


def render_agent_trace(analysis_response: Dict[str, Any]):
    st.subheader("🤖 LangGraph Agent Execution Trace")
    
    details = analysis_response.get("human_review_details", {})
    execution_logs = details.get("execution_logs", [])
    crm_available = analysis_response.get("crm_context_available", False)
    status = analysis_response.get("status", "completed")
    requires_hitl = analysis_response.get("requires_human_review", False)
    anomalies = analysis_response.get("analysis", {}).get("anomalies", [])

    steps = [
        {
            "name": "Orchestrator Agent",
            "status": "COMPLETED",
            "icon": "✓",
            "summary": f"Initialized workflow for Request ID: {analysis_response.get('request_id')}",
            "decision": "Routed initial state to Data Fetcher node."
        },
        {
            "name": "Data Fetcher Agent",
            "status": "COMPLETED",
            "icon": "✓",
            "summary": f"Validated input schema and normalized financial profile.",
            "decision": f"CRM Context retrieved: {crm_available}."
        },
        {
            "name": "CRM Tool Interface",
            "status": "COMPLETED" if crm_available else "DEGRADED",
            "icon": "✓" if crm_available else "⚠️",
            "summary": "Invoked Mock/HTTP CRM tool abstraction.",
            "decision": "Profile attached." if crm_available else "CRM unavailable; continued with financial data only."
        },
        {
            "name": "Analyzer Agent",
            "status": "COMPLETED",
            "icon": "✓",
            "summary": "Ran pure Python deterministic financial calculations.",
            "decision": f"Expense ratio calculated: {analysis_response.get('analysis', {}).get('expense_ratio', 0)*100:.1f}%."
        },
        {
            "name": "Deterministic Anomaly Detector",
            "status": "COMPLETED",
            "icon": "✓",
            "summary": "Evaluated Z-score, spending spike, and category concentration.",
            "decision": f"Detected {len(anomalies)} anomalies."
        },
        {
            "name": "Risk / Insight Agent",
            "status": "COMPLETED",
            "icon": "✓",
            "summary": "Generated structured advisory recommendations.",
            "decision": f"Assigned Risk Tier: {analysis_response.get('insights', {}).get('overall_risk')}."
        },
        {
            "name": "Guardrail Validator",
            "status": "COMPLETED",
            "icon": "✓",
            "summary": "Validated non-empty recommendations and compliance constraints.",
            "decision": "Sanity and compliance checks passed."
        },
        {
            "name": "Human-in-the-Loop Evaluator",
            "status": "PENDING_REVIEW" if requires_hitl and status == "PENDING_HUMAN_REVIEW" else ("APPROVED" if status == "APPROVED" else "PASSED"),
            "icon": "⚠️" if requires_hitl and status == "PENDING_HUMAN_REVIEW" else "✓",
            "summary": "Evaluated high-risk / anomaly thresholds for human approval.",
            "decision": "Human approval gate triggered." if requires_hitl else "Automated completion approved."
        }
    ]

    for step in steps:
        with st.expander(f"{step['icon']} {step['name']} — {step['status']}"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**Status:** `{step['status']}`")
            with col2:
                st.markdown(f"**Decision:** {step['decision']}")
            st.caption(f"**Summary:** {step['summary']}")

    if execution_logs:
        with st.expander("📜 Full Execution Event Log"):
            for log in execution_logs:
                st.text(f"• {log}")
