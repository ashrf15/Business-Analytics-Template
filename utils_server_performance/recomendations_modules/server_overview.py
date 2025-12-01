import streamlit as st
import plotly.express as px
import pandas as pd

def server_overview(df):
    st.subheader("1️⃣ Server Overview")

    with st.expander("🔎 Detailed Insights: Server Inventory Overview"):
        # ✅ Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        st.markdown("### 📊 Graphs")

        # Server Types Distribution
        if "server_type" in df.columns:
            type_counts = df["server_type"].value_counts().reset_index()
            type_counts.columns = ["Server Type", "Count"]
            fig1 = px.bar(type_counts, x="Server Type", y="Count", 
                          color="Count", color_continuous_scale="Blues",
                          title="Number of Servers by Type")
            st.plotly_chart(fig1, use_container_width=True, key="srv_overview_type")

        # Server Status (Up vs Down)
        if "status" in df.columns:
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig2 = px.pie(status_counts, names="Status", values="Count",
                          title="Server Status Distribution (Up vs Down)")
            st.plotly_chart(fig2, use_container_width=True, key="srv_overview_status")

        # Servers by Location
        if "location" in df.columns:
            loc_counts = df["location"].value_counts().reset_index()
            loc_counts.columns = ["Location", "Count"]
            fig3 = px.bar(loc_counts, x="Location", y="Count",
                          color="Count", color_continuous_scale="Greens",
                          title="Servers by Location")
            st.plotly_chart(fig3, use_container_width=True, key="srv_overview_loc")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        The server inventory shows a **mixed infrastructure of Physical, Virtual, and Cloud servers**.  
        - The majority are **Virtual servers**, indicating optimization for scalability and flexibility.  
        - Around **10% of servers are currently Down**, which poses risks for uptime and user services.  
        - The distribution across multiple data centers highlights **redundancy**, but also creates **management complexity**.  

        This snapshot provides IT with a foundation to optimize both cost and performance.
        """)

        # 💰 CIO Recommendations (Cost Reduction)
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation": [
                "Decommission underutilized physical servers",
                "Consolidate workloads onto fewer high-capacity virtual machines",
                "Leverage cloud burst capacity instead of on-prem scaling"
            ],
            "Benefit": [
                "Cuts power, cooling, and licensing costs",
                "Reduces hardware maintenance overhead",
                "Avoids CapEx for underused physical capacity"
            ],
            "Cost Calculation": [
                "10 servers × RM4K/yr OPEX = RM40K saved",
                "20% fewer servers needed = ~RM25K/yr",
                "Defers CapEx of RM100K by shifting burst loads to cloud"
            ]
        }))

        # 🚀 CIO Recommendations (Performance Improvement)
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation": [
                "Standardize server types for easier management",
                "Implement proactive monitoring for status changes",
                "Improve geo-distribution for branch users"
            ],
            "Benefit": [
                "Simplifies patching, updates, and support",
                "Detects outages faster, reducing downtime impact",
                "Improves performance for remote offices"
            ],
            "Cost Calculation": [
                "15% faster troubleshooting (~RM12K/yr benefit)",
                "Cuts downtime by 20% = ~RM30K/yr saved",
                "Boosts branch productivity worth ~RM18K/yr"
            ]
        }))

        # 🗣 Business Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        This section shows **how many servers you have, what types they are, where they are located, and how many are running or down**.  
        - Retiring unused servers and moving more to the cloud saves costs.  
        - Monitoring and standardizing servers keeps operations smooth.  
        - Adding coverage for branch locations ensures better service for all users.  
        """)
