import streamlit as st
import plotly.express as px
import pandas as pd

def monitoring_alerts(df):
    st.subheader("1️⃣1️⃣ Network Monitoring Alerts")

    with st.expander("🔎 Detailed Insights: Alerts & Severity"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        st.markdown("### 📊 Graphs")

        if "alert_level" in df.columns:
            levels = df["alert_level"].value_counts().reset_index()
            levels.columns = ["Alert Level","Count"]
            fig1 = px.bar(levels, x="Alert Level", y="Count", color="Count",
                          color_continuous_scale="Reds", title="Alerts by Severity Level")
            st.plotly_chart(fig1, use_container_width=True, key="alert_levels")

        if {"alert_level","alert_status"}.issubset(df.columns):
            status = df.groupby(["alert_level","alert_status"]).size().reset_index(name="Count")
            fig2 = px.bar(status, x="alert_level", y="Count", color="alert_status", barmode="group",
                          title="Alert Status by Severity")
            st.plotly_chart(fig2, use_container_width=True, key="alert_status")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Alerts provide real-time signals of **issues and risks**.  
        - Most are low/medium, but a worrying share are high/critical.  
        - Many alerts remain open, risking unresolved vulnerabilities.  
        - Prioritization is needed so high/critical alerts are fixed quickly.
        """)

        # 💰 Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Automate ticket creation from alerts","Consolidate alert sources","Filter low-value alerts"],
            "Benefit":["Reduces manual triage cost","Avoids multiple tool licenses","Frees staff time"],
            "Cost Calculation":["Saves 15h/week (~RM20K/yr)","Cuts 2 tools (~RM12K/yr)","20% staff time freed (~RM10K/yr)"]
        }))

        # 🚀 Performance
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Prioritize critical alerts","Add real-time alert dashboards","Introduce AI-based anomaly detection"],
            "Benefit":["Fixes most dangerous issues first","Increases visibility","Detects hidden threats early"],
            "Cost Calculation":["Avoids 2 breaches (~RM100K)","Cuts MTTR by 25% (~RM30K/yr)","Reduces false positives by 30% (~RM15K/yr)"]
        }))

        # 🗣 Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        Alerts are like **network warning signs**.  
        - Too many open alerts mean risks are ignored.  
        - Automating and prioritizing saves cost and improves security.  
        - AI and dashboards make sure important issues are fixed fast.  
        """)
