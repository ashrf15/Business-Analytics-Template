import streamlit as st

def dashboard_sla(df):
    st.header("📊 SLA Compliance Dashboard")

    col1, col2, col3 = st.columns(3)

    if "met" in df.columns:
        overall = (df["met"].dropna().mean() * 100).round(1)
    else:
        overall = 0
    col1.metric("Overall Compliance", f"{overall}%")

    breaches = df[df["met"] == False].shape[0] if "met" in df.columns else 0
    col2.metric("Total Breaches", breaches)

    if "customer_satisfaction" in df.columns:
        csat = df["customer_satisfaction"].dropna().mean().round(2)
    else:
        csat = 0
    col3.metric("Avg Customer Satisfaction", csat)

    st.markdown("This dashboard shows **at-a-glance KPIs** of SLA compliance, breaches, and customer satisfaction.")
