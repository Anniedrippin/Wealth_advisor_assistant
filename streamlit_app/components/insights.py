import streamlit as st
from typing import Dict, Any, List


def render_advisory_insights(analysis_response: Dict[str, Any]):
    st.subheader("💡 AI Advisory Insights & Recommendations")

    insights = analysis_response.get("insights", {})
    overall_risk = insights.get("overall_risk", "UNKNOWN")
    exec_summary = insights.get("executive_summary", "")
    key_findings: List[str] = insights.get("key_findings", [])
    recommendations: List[Dict[str, Any]] = insights.get("recommendations", [])
    follow_ups: List[str] = insights.get("follow_up_questions", [])
    confidence = insights.get("confidence", 1.0)
    disclaimer = analysis_response.get(
        "disclaimer",
        "This advisory insight is generated for demonstration and decision-support purposes only and does not constitute formal financial advice."
    )

    # Risk Callout
    risk_color = "red" if overall_risk == "HIGH" else ("orange" if overall_risk == "MEDIUM" else "green")
    st.markdown(f"#### Overall Assessed Risk: :{risk_color}[**{overall_risk}**]  *(Confidence: {confidence*100:.0f}%)*")

    if exec_summary:
        st.markdown(f"> **Executive Overview:** {exec_summary}")

    st.markdown("---")

    # Key Findings
    st.markdown("##### 📌 Key Analytical Findings")
    if key_findings:
        for finding in key_findings:
            st.markdown(f"• {finding}")
    else:
        st.info("No key findings generated.")

    st.markdown("---")

    # Recommendations
    st.markdown("##### 🎯 Recommended Advisory Actions")
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            prio = rec.get("priority", "MEDIUM")
            prio_icon = "🔴" if prio == "HIGH" else ("🟡" if prio == "MEDIUM" else "🟢")
            
            with st.container():
                st.markdown(f"**{i}. {prio_icon} [{prio}] {rec.get('area')}**")
                st.markdown(f"👉 **Action:** {rec.get('recommendation')}")
                st.caption(f"**Rationale:** {rec.get('reason')}")
                st.markdown("")
    else:
        st.info("No explicit recommendations needed.")

    # Follow-up Questions
    if follow_ups:
        st.markdown("---")
        st.markdown("##### ❓ Suggested Follow-Up Questions for Client")
        for q in follow_ups:
            st.markdown(f"• *\"{q}\"*")

    st.markdown("---")
    st.caption(f"⚖️ **Disclaimer:** {disclaimer}")
