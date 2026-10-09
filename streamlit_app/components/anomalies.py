import streamlit as st
import pandas as pd
from typing import Dict, Any, List


def render_anomalies_dashboard(analysis_response: Dict[str, Any]):
    st.subheader("🚨 Detected Financial Anomalies")

    analysis = analysis_response.get("analysis", {})
    anomalies: List[Dict[str, Any]] = analysis.get("anomalies", [])

    if not anomalies:
        st.success("✅ No financial anomalies detected for this client session.")
        return

    st.warning(f"⚠️ Flagged **{len(anomalies)}** anomaly signal(s) requiring attention.")

    for i, anom in enumerate(anomalies, 1):
        sev = anom.get("severity", "MEDIUM")
        badge_style = "🔴 HIGH / CRITICAL" if sev == "HIGH" else ("🟡 MEDIUM" if sev == "MEDIUM" else "🟢 LOW")
        
        with st.container():
            st.markdown(f"### {i}. {badge_style} — {anom.get('type')}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Target ID:** `{anom.get('transaction_id')}`")
            with col2:
                st.markdown(f"**Anomaly Score:** `{anom.get('score')}`")
            with col3:
                st.markdown(f"**Severity Level:** `{sev}`")
            
            st.info(f"**Explanation:** {anom.get('reason')}")
            st.markdown("---")

    # Table view
    st.markdown("##### 📊 Anomaly Summary Matrix")
    df_anom = pd.DataFrame(anomalies)
    st.dataframe(df_anom, use_container_width=True)
