import streamlit as st

def dashboard_network(df):
    st.header("📊 Network Performance Dashboard")

    col1, col2, col3 = st.columns(3)

    if "uptime_percent" in df.columns:
        uptime = df["uptime_percent"].mean().round(2)
    else:
        uptime = 0
    col1.metric("Avg Uptime", f"{uptime}%")

    if "latency_ms" in df.columns:
        latency = df["latency_ms"].mean().round(2)
    else:
        latency = 0
    col2.metric("Avg Latency (ms)", latency)

    if "bandwidth_usage_mbps" in df.columns:
        bw = df["bandwidth_usage_mbps"].mean().round(2)
    else:
        bw = 0
    col3.metric("Avg Bandwidth Usage (Mbps)", bw)

    st.markdown("This dashboard shows **real-time KPIs** of uptime, latency, and traffic load across the network.")
