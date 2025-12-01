import streamlit as st
import plotly.express as px
import pandas as pd

def server_availability(df):
    st.subheader("5️⃣ Server Availability")

    with st.expander("🔎 Detailed Insights: Availability & Downtime"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        st.markdown("### 📊 Graphs")

        if {"downtime_incident","downtime_type"}.issubset(df.columns):
            downtime = df[df["downtime_incident"]==1].groupby("downtime_type").size().reset_index(name="Count")
            fig1 = px.bar(downtime, x="downtime_type", y="Count", color="Count",
                          color_continuous_scale="Reds", title="Downtime by Type")
            st.plotly_chart(fig1, use_container_width=True, key="srv_avail_downtype")

        if {"timestamp","downtime_incident"}.issubset(df.columns):
            df_time = df.dropna(subset=["timestamp"]).copy()
            df_time["month"] = pd.to_datetime(df_time["timestamp"]).dt.to_period("M").astype(str)
            trend = df_time.groupby("month")["downtime_incident"].sum().reset_index()
            fig2 = px.line(trend, x="month", y="downtime_incident", markers=True,
                           title="Downtime Incidents Over Time")
            st.plotly_chart(fig2, use_container_width=True, key="srv_avail_trend")

        st.markdown("### 🔍 Analysis")
        st.markdown("""
        - Downtime is split between Planned and Unplanned.  
        - Unplanned outages cause biggest service impact.  
        - Trend shows clustering around patch cycles.
        """)

        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Automate maintenance windows","Improve scheduling","Reduce patch downtime"],
            "Benefit":["Avoids overtime","Less wasted user hours","Cuts OPEX"],
            "Cost Calculation":["Save RM8K/yr","Save RM12K/yr","Avoids RM20K downtime"]
        }))

        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Add HA clustering","Perform RCA on outages","Improve change mgmt"],
            "Benefit":["Resilient infra","Prevent repeats","Lower incident count"],
            "Cost Calculation":["Avoid 2 outages = RM50K","Cut downtime 15% = RM25K","Saves RM10K/yr"]
        }))

        st.markdown("### 🗣 Business Explanation")
        st.markdown("""
        Shows **planned vs unplanned downtime**.  
        Scheduling and clustering saves money, and prevents surprise outages.  
        """)
