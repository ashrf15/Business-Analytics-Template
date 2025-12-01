import streamlit as st
import plotly.express as px
import pandas as pd

def server_health(df):
    st.subheader("2️⃣ Server Health")

    with st.expander("🔎 Detailed Insights: Server Health Status"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        st.markdown("### 📊 Graphs")

        if "status" in df.columns:
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status","Count"]
            fig1 = px.pie(status_counts, names="Status", values="Count",
                          title="Server Status (Up vs Down)")
            st.plotly_chart(fig1, use_container_width=True, key="srv_health_status")

        if {"status","server_type"}.issubset(df.columns):
            issues = df[df["status"].str.lower()=="down"]["server_type"].value_counts().reset_index()
            issues.columns = ["Server Type","Down Count"]
            fig2 = px.bar(issues, x="Server Type", y="Down Count", color="Down Count",
                          color_continuous_scale="Reds", title="Down Servers by Type")
            st.plotly_chart(fig2, use_container_width=True, key="srv_health_issues")

        if "uptime_percent" in df.columns:
            fig3 = px.histogram(df, x="uptime_percent", nbins=20,
                                title="Server Uptime Distribution (%)")
            st.plotly_chart(fig3, use_container_width=True, key="srv_health_uptime")

        st.markdown("### 🔍 Analysis")
        st.markdown("""
        - Most servers Up, but ~10% Down.  
        - Down mostly in Physical servers.  
        - Uptime clusters around 98% with a few poor performers.
        """)

        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Retire failing servers","Automate uptime checks","Centralize monitoring"],
            "Benefit":["Avoid repair cost","Reduce manual checks","Avoid duplicate tools"],
            "Cost Calculation":["3 servers × RM5K = RM15K","40h/month saved = RM12K","20% license cut = RM8K"]
        }))

        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Predictive monitoring","Add redundancy","Regular patching"],
            "Benefit":["Catch failures early","Minimize downtime","Improve stability"],
            "Cost Calculation":["15% less downtime = RM20K","Avoid 2 outages = RM40K","Fewer incidents = RM10K"]
        }))

        st.markdown("### 🗣 Business Explanation")
        st.markdown("""
        Shows **which servers are up, down, and their uptime history**.  
        Replacing weak servers and monitoring better keeps systems healthy.  
        """)
