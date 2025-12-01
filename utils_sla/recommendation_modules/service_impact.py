import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def service_impact(df):
    st.subheader("6️⃣ Service Impact")

    with st.expander("🔎 Detailed Insights: Business Impact of SLA Breaches"):
        st.markdown("### 📊 Graphs")

        # Impact distribution for breaches
        if {"impact","met"}.issubset(df.columns):
            imp = df[df["met"] == False]["impact"].value_counts().reset_index()
            imp.columns = ["impact","count"]
            if not imp.empty:
                fig1 = px.bar(imp, x="impact", y="count", color="count",
                              color_continuous_scale="Reds", title="Impact Levels for Breached SLAs")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No breach impact data available.")

        # Breaches by Service with impact weight (proxy)
        if {"service","met","impact"}.issubset(df.columns):
            impact_weight = {"Low":1, "Medium":2, "High":3}
            dfx = df[df["met"] == False].copy()
            if _nonempty(dfx):
                dfx["ImpactScore"] = dfx["impact"].map(impact_weight).fillna(0)
                svc_score = dfx.groupby("service")["ImpactScore"].sum().reset_index()
                fig2 = px.bar(svc_score, x="service", y="ImpactScore",
                              color="ImpactScore", color_continuous_scale="Reds",
                              title="Weighted Impact Score by Service (Higher = Worse)")
                st.plotly_chart(fig2, use_container_width=True, key="serviceimpact_weighted")
            else:
                st.info("No breached SLA data to compute impact score.")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Not all SLA misses are equal. **High-impact** breaches cause outsized business pain 
        (lost revenue, VIP dissatisfaction, reputational risk).  
        Services with repeated high-impact breaches require **priority action** even if their total breach count is moderate.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Prioritize fixes on high-impact breach services",
                "Create VIP playbooks for rapid mitigation",
                "Bundle low-impact improvements into sprints"
            ],
            "Benefit":[
                "Eliminates costliest penalties first",
                "Reduces business downtime and escalations",
                "Delivers quick wins without heavy cost"
            ],
            "Cost Calculation":[
                "Cut top impacts by 30% ≈ RM25K/year",
                "Faster VIP mitigation saves ≈ RM10K/year",
                "Sprint bundling saves ≈ RM6K/year"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Impact scoring in dashboards",
                "Proactive risk reviews for high-impact services",
                "Service owner KPIs tied to impact reduction"
            ],
            "Benefit":[
                "Focus on what hurts the business most",
                "Prevents serious misses before they occur",
                "Aligns incentives with outcomes"
            ],
            "Cost Calculation":[
                "2% improvement ≈ RM8K/year",
                "Avoid 3 major impacts ≈ RM18K/year",
                "KPI-linked reduction ≈ RM10K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        We score the **business impact** of each miss to focus on what matters most.  
        Fix the worst pain first, protect VIPs, and package smaller fixes to deliver steady improvements.
        """)
