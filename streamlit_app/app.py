import sys
import pathlib

# Ensure root directory is in sys.path for streamlit execution
ROOT_DIR = pathlib.Path(__file__).parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import streamlit as st
from streamlit_app.api_client import AdvisoryAPIClient
from streamlit_app.components.dashboard import render_client_dashboard
from streamlit_app.components.agent_trace import render_agent_trace
from streamlit_app.components.anomalies import render_anomalies_dashboard
from streamlit_app.components.insights import render_advisory_insights
from streamlit_app.components.hitl import render_hitl_panel
from streamlit_app.components.memory import render_memory_viewer

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Wealth Advisor Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Instantiate API client
api_client = AdvisoryAPIClient()

st.title("💼 Mini Multi-Agent Wealth Advisor Assistant")
st.caption("Production-Quality LangGraph Agent Architecture & Monitoring Interface")

# Sidebar - System Status & Demo Client Selector
st.sidebar.title("⚙️ Control Panel")

# 1. Backend Health Badge
health = api_client.check_health()
if health.get("status") == "healthy":
    st.sidebar.success(f"🟢 Backend Online (`{health.get('app_env')}`)")
else:
    st.sidebar.error("🔴 Backend Offline or Unreachable")

st.sidebar.markdown("---")

# 2. Demo Client Selection
st.sidebar.subheader("👤 Select Demo Client")
sample_data_path = pathlib.Path(__file__).parents[1] / "data" / "sample_clients.json"

clients_payloads = []
if sample_data_path.exists():
    with open(sample_data_path, "r", encoding="utf-8") as f:
        clients_payloads = json.load(f)

client_options = {
    "C1001 — Sarah Connor (Normal Monthly Activity)": 0,
    "C1002 — Marcus Vance (Anomalous $45,000 Transaction)": 1,
    "C1003 — Elena Rostova (High Expense Ratio & Risk Signal)": 2
}

selected_label = st.sidebar.selectbox("Choose Client Profile:", list(client_options.keys()))
selected_idx = client_options[selected_label]
selected_client_input = clients_payloads[selected_idx] if clients_payloads else {}

st.sidebar.markdown("---")
run_analysis_btn = st.sidebar.button("🚀 Run Multi-Agent Analysis", type="primary", use_container_width=True)

# Session state initialization
if "analysis_response" not in st.session_state or run_analysis_btn:
    with st.spinner("Executing LangGraph Multi-Agent StateMachine..."):
        try:
            st.session_state["analysis_response"] = api_client.analyze_client(selected_client_input)
            st.session_state["current_input"] = selected_client_input
        except Exception as e:
            st.error(f"Analysis pipeline error: {e}")

analysis_resp = st.session_state.get("analysis_response")
current_input = st.session_state.get("current_input", selected_client_input)

# Main Navigation Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Client Dashboard",
    "🤖 Agent Trace",
    "🚨 Anomalies",
    "💡 Advisory Insights",
    "🛡️ Human Approval (HITL)",
    "🧠 Memory Viewer"
])

if analysis_resp:
    with tab1:
        render_client_dashboard(analysis_resp, current_input)

    with tab2:
        render_agent_trace(analysis_resp)

    with tab3:
        render_anomalies_dashboard(analysis_resp)

    with tab4:
        render_advisory_insights(analysis_resp)

    with tab5:
        render_hitl_panel(analysis_resp, api_client)

    with tab6:
        render_memory_viewer(api_client)
else:
    st.info("Click 'Run Multi-Agent Analysis' in the sidebar to execute the pipeline.")
