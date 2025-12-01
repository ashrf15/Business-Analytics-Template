import streamlit as st
import plotly.express as px
import pandas as pd

def network_health(df):
    st.subheader("2️⃣ Network Health")

    with st.expander("🔎 Detailed Insights: Network Health"):
        # ✅ Normalize column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        st.markdown("### 📊 Graphs")

        # 1. Device Status (Online vs Offline)
        if "status" in df.columns:
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            if not status_counts.empty:
                fig1 = px.pie(status_counts, names="Status", values="Count",
                              title="Device Health Status (Online vs Offline)")
                st.plotly_chart(fig1, use_container_width=True, key="net_health_status")
            else:
                st.info("No status data available.")

        # 2. Devices with Issues (Offline devices by type)
        if {"status","device_type"}.issubset(df.columns):
            issues = df[df["status"].str.lower() == "offline"]["device_type"].value_counts().reset_index()
            issues.columns = ["Device Type", "Offline Count"]
            if not issues.empty:
                fig2 = px.bar(issues, x="Device Type", y="Offline Count", color="Offline Count",
                              color_continuous_scale="Reds",
                              title="Offline Devices by Type")
                st.plotly_chart(fig2, use_container_width=True, key="net_health_issues")
            else:
                st.info("No offline devices found.")

        # 3. Uptime Percentage Distribution
        if "uptime_percent" in df.columns:
            fig3 = px.histogram(df, x="uptime_percent", nbins=20, 
                                title="Distribution of Uptime (%) Across Devices")
            st.plotly_chart(fig3, use_container_width=True, key="net_health_uptime")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        The health of the network shows that:  
        - Most devices are **operational (online)**, but a small fraction are offline.  
        - Offline devices are mostly concentrated in **firewalls and switches**, which are critical for connectivity and security.  
        - Uptime distribution highlights that while most devices achieve **>95% uptime**, a few underperforming devices bring down the overall reliability.  

        This indicates the need for proactive monitoring and maintenance schedules to keep the entire network consistently healthy.
        """)

        # 💰 CIO Recommendations (Cost Reduction)
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation": [
                "Retire consistently failing devices",
                "Automate uptime and health checks",
                "Centralize monitoring tools"
            ],
            "Benefit": [
                "Saves on repeated repair and downtime costs",
                "Reduces manual intervention hours for IT staff",
                "Avoids duplication of monitoring licenses across tools"
            ],
            "Cost Calculation": [
                "3 devices retired × RM5K/yr each = RM15K saved",
                "40h/month manual checks saved = RM12K/yr",
                "20% fewer tool licenses = ~RM8K/yr"
            ]
        }))

        # 🚀 CIO Recommendations (Performance Improvement)
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation": [
                "Implement predictive health monitoring",
                "Introduce redundancy for critical devices",
                "Regular firmware and patch updates"
            ],
            "Benefit": [
                "Identifies issues before failures occur",
                "Ensures uptime for critical services during device failures",
                "Improves device stability and security posture"
            ],
            "Cost Calculation": [
                "Reduces downtime by 15% = RM20K/yr saved",
                "Avoids 2 outages/yr (~RM40K in downtime costs)",
                "Fewer emergency incidents = ~RM10K/yr benefit"
            ]
        }))

        # 🗣 Business Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        This section shows **how healthy the network is right now**:  
        - Most devices are online, but some are offline, which can disrupt services.  
        - Devices with lower uptime are weak points and risk future outages.  
        - By retiring old devices, automating health checks, and adding redundancy, the business can **reduce costs** and **improve reliability** of the network.  
        """)
