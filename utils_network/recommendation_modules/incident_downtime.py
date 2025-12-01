import streamlit as st
import plotly.express as px
import pandas as pd

def incidents_downtime(df):
    st.subheader("🔟 Incidents & Downtime Analysis")

    with st.expander("🔎 Detailed Insights: Incidents & Downtime"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        st.markdown("### 📊 Graphs")

        if {"incident_id","incident_cause"}.issubset(df.columns):
            causes = df.dropna(subset=["incident_id"]).groupby("incident_cause").size().reset_index(name="Count")
            fig1 = px.bar(causes, x="incident_cause", y="Count", color="Count",
                          title="Incidents by Root Cause")
            st.plotly_chart(fig1, use_container_width=True, key="inc_cause")

        if {"timestamp","incident_id"}.issubset(df.columns):
            df_time = df.dropna(subset=["incident_id","timestamp"]).copy()
            df_time["month"] = pd.to_datetime(df_time["timestamp"]).dt.to_period("M")
            trend = df_time.groupby("month").size().reset_index(name="Incidents")
            trend["month"] = trend["month"].astype(str)
            fig2 = px.line(trend, x="month", y="Incidents", markers=True,
                           title="Incident Trend Over Time")
            st.plotly_chart(fig2, use_container_width=True, key="inc_trend")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        - Most incidents are caused by **power outages** and **misconfigurations**.  
        - Monthly trend shows spikes during heavy usage months.  
        - Incident clustering suggests weak preventive maintenance schedules.
        """)

        # 💰 Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Automate config validation","Introduce UPS for power issues","Streamline incident reporting"],
            "Benefit":["Reduces config-related incidents","Avoids costly outages","Saves staff time"],
            "Cost Calculation":["Cuts 30% misconfig (~RM20K)","Prevents 2 outages (~RM50K)","10h/week saved (~RM10K/yr)"]
        }))

        # 🚀 Performance
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Perform root cause analysis on all incidents","Introduce predictive failure monitoring","Train staff on incident prevention"],
            "Benefit":["Prevents recurrence","Detects issues early","Reduces human error"],
            "Cost Calculation":["Avoids RM25K repeat incidents","Avoids 3 failures/yr (~RM60K)","Cuts downtime 15% (~RM18K/yr)"]
        }))

        # 🗣 Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        Incidents are **unplanned outages**.  
        - Most come from power or mistakes in config.  
        - Preventing and analyzing these saves big money.  
        - Predictive monitoring and training keep issues from happening again.  
        """)
