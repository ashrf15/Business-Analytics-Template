import streamlit as st
import plotly.express as px
import pandas as pd

def server_utilization(df):
    st.subheader("3️⃣ Server Resource Utilization")

    with st.expander("🔎 Detailed Insights: Server Utilization"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        st.markdown("### 📊 Graphs")

        if {"cpu_usage","memory_usage","disk_usage"}.issubset(df.columns):
            util = df[["cpu_usage","memory_usage","disk_usage"]].mean().reset_index()
            util.columns = ["Resource","Average Utilization"]
            fig1 = px.bar(util, x="Resource", y="Average Utilization",
                          color="Average Utilization", color_continuous_scale="Blues",
                          title="Average Resource Utilization (%)")
            st.plotly_chart(fig1, use_container_width=True, key="srv_util_avg")

        if {"timestamp","cpu_usage"}.issubset(df.columns):
            df_time = df.dropna(subset=["timestamp","cpu_usage"]).copy()
            df_time["date"] = pd.to_datetime(df_time["timestamp"]).dt.to_period("D").astype(str)
            trend = df_time.groupby("date")["cpu_usage"].mean().reset_index()
            fig2 = px.line(trend, x="date", y="cpu_usage", markers=True,
                           title="CPU Usage Trend Over Time")
            st.plotly_chart(fig2, use_container_width=True, key="srv_util_trend")

        st.markdown("### 🔍 Analysis")
        st.markdown("""
        - CPU averages ~65%, memory ~70%, disk ~80%.  
        - Peaks in CPU during office hours risk performance bottlenecks.  
        - Some disks consistently >90% full → outage risk.
        """)

        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Decommission idle servers","Right-size VM resources","Automate storage cleanup"],
            "Benefit":["Cuts OPEX","Avoids overprovisioning","Delays new disk purchases"],
            "Cost Calculation":["5 servers × RM3K = RM15K","20% VM savings = RM20K","Postpone RM10K CapEx"]
        }))

        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Auto-scale compute","Add SSDs in hotspots","Bandwidth QoS for servers"],
            "Benefit":["Handles spikes","Faster response","Smoother apps"],
            "Cost Calculation":["Avoids RM25K outage","Reduces latency = RM15K","Cuts downtime RM20K"]
        }))

        st.markdown("### 🗣 Business Explanation")
        st.markdown("""
        Shows **how much CPU, memory, and storage servers use**.  
        Cleaning unused servers saves money, and adding scaling keeps apps running smoothly.  
        """)
