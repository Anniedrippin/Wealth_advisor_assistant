import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any


def render_client_dashboard(analysis_response: Dict[str, Any], client_input: Dict[str, Any]):
    st.subheader("📊 Client Financial Overview & Analysis")

    analysis = analysis_response.get("analysis", {})
    insights = analysis_response.get("insights", {})

    income = analysis.get("income", 0.0)
    expenses = analysis.get("expenses", 0.0)
    net_cash_flow = analysis.get("net_cash_flow", 0.0)
    expense_ratio = analysis.get("expense_ratio", 0.0)
    risk_level = insights.get("overall_risk", "UNKNOWN")

    # 1. KPI Cards Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Monthly Income", value=f"${income:,.2f}")
    with col2:
        st.metric(label="Monthly Expenses", value=f"${expenses:,.2f}")
    with col3:
        st.metric(
            label="Net Cash Flow",
            value=f"${net_cash_flow:,.2f}",
            delta=f"{'+' if net_cash_flow >= 0 else ''}${net_cash_flow:,.2f}"
        )
    with col4:
        st.metric(label="Expense Ratio", value=f"{expense_ratio*100:.1f}%")
    with col5:
        risk_color = "red" if risk_level == "HIGH" else ("orange" if risk_level == "MEDIUM" else "green")
        st.metric(label="Risk Tier", value=risk_level)

    st.markdown("---")

    # 2. Charts Row: Plotly Pie & Bar Charts
    chart_col1, chart_col2 = st.columns(2)

    category_breakdown = analysis.get("category_breakdown", {})
    if category_breakdown:
        df_cat = pd.DataFrame([
            {"Category": cat.capitalize(), "Amount ($)": amt}
            for cat, amt in category_breakdown.items()
        ])

        with chart_col1:
            st.markdown("##### 🍕 Expenses by Category")
            fig_pie = px.pie(
                df_cat,
                names="Category",
                values="Amount ($)",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)

    transactions = client_input.get("transactions", [])
    if transactions:
        df_tx = pd.DataFrame(transactions)
        df_tx["abs_amount"] = df_tx["amount"].abs()

        with chart_col2:
            st.markdown("##### 📈 Recent Transaction Breakdown")
            fig_bar = px.bar(
                df_tx,
                x="id",
                y="abs_amount",
                color="category",
                text="abs_amount",
                labels={"id": "Transaction ID", "abs_amount": "Amount ($)"},
                title=None
            )
            fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_bar, use_container_width=True)

    # 3. Transaction Data Table
    st.markdown("##### 📋 Ingested Transactions")
    if transactions:
        st.dataframe(pd.DataFrame(transactions), use_container_width=True)
    else:
        st.info("No explicit transaction items provided for this client.")
