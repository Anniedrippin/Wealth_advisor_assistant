import streamlit as st
from typing import Dict, Any
from streamlit_app.api_client import AdvisoryAPIClient


def render_hitl_panel(analysis_response: Dict[str, Any], api_client: AdvisoryAPIClient):
    st.subheader("🛡️ Human-in-the-Loop (HITL) Review Checkpoint")

    request_id = analysis_response.get("request_id")
    client_id = analysis_response.get("client_id")
    status = analysis_response.get("status", "completed")
    requires_hitl = analysis_response.get("requires_human_review", False)
    insights = analysis_response.get("insights", {})
    anomalies = analysis_response.get("analysis", {}).get("anomalies", [])

    if status == "APPROVED":
        st.success(f"✅ Advisory Request `{request_id}` has been **APPROVED** by Human Advisor.")
        return
    elif status == "REJECTED":
        st.error(f"❌ Advisory Request `{request_id}` has been **REJECTED** by Human Advisor.")
        return

    if not requires_hitl and status != "PENDING_HUMAN_REVIEW":
        st.info("✅ Automated workflow passed without requiring human intervention.")
        return

    st.warning("⚠️ **ACTION REQUIRED**: This advisory assessment requires human advisor approval before release.")

    with st.expander("🔍 Review Summary & Supporting Evidence", expanded=True):
        st.markdown(f"**Client ID:** `{client_id}` | **Request ID:** `{request_id}`")
        st.markdown(f"**Assessed Risk Level:** `{insights.get('overall_risk')}`")
        st.markdown(f"**Flagged Anomalies Count:** `{len(anomalies)}`")
        
        if anomalies:
            st.markdown("**Flagged Anomalies:**")
            for a in anomalies:
                st.markdown(f"• **[{a.get('severity')}] {a.get('type')}**: {a.get('reason')}")

        st.markdown("**Key Recommendation:**")
        recs = insights.get("recommendations", [])
        if recs:
            st.markdown(f"👉 *{recs[0].get('recommendation')}*")

    # Reviewer decision controls
    comments = st.text_area("Optional Reviewer Comments / Overrides:", placeholder="e.g. Approved after phone verification with client.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ [ APPROVE ]", type="primary", use_container_width=True):
            try:
                result = api_client.approve_request(request_id, reviewer_comments=comments)
                st.success("Advisory insight APPROVED successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to approve request: {e}")

    with col2:
        if st.button("❌ [ REJECT ]", use_container_width=True):
            try:
                result = api_client.reject_request(request_id, reviewer_comments=comments)
                st.warning("Advisory insight REJECTED.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reject request: {e}")
