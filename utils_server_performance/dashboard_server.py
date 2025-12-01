import streamlit as st

def dashboard_server(df):
    st.header("📊 Server Performance Dashboard")

    col1, col2, col3 = st.columns(3)

    if "uptime_percent" in df.columns:
        uptime = df["uptime_percent"].mean().round(2)
    else:
        uptime = 0
    col1.metric("Average Uptime", f"{uptime}%")

    if "cpu_usage" in df.columns:
        cpu = df["cpu_usage"].mean().round(2)
    else:
        cpu = 0
    col2.metric("Average CPU Usage", f"{cpu}%")

    if "memory_usage" in df.columns:
        mem = df["memory_usage"].mean().round(2)
    else:
        mem = 0
    col3.metric("Average Memory Usage", f"{mem}%")

    st.markdown("""
    This dashboard highlights the **core server KPIs**: uptime reliability, CPU utilization, and memory consumption.  
    These provide an instant overview of infrastructure stability and efficiency.
    """)
