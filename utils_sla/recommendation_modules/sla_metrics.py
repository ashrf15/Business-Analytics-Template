import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def sla_metrics(df):
    st.subheader("2️⃣ SLA Metrics")

    with st.expander("🔎 Detailed Insights: SLA Metrics"):
        st.markdown("### 📊 Graphs")

        # Target vs Achieved by SLA Type
        if {"sla_type","target","achieved"}.issubset(df.columns):
            by_type = df.groupby("sla_type")[["target","achieved"]].mean().reset_index()
            if not by_type.empty:
                by_type["Gap"] = (by_type["achieved"] - by_type["target"]).round(1)
                fig1 = px.bar(by_type, x="sla_type", y=["target","achieved"],
                              barmode="group", title="Average Target vs Achieved by SLA Type")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No SLA type metric data available.")

        # Average Achieved by Service
        if {"service","achieved"}.issubset(df.columns):
            by_service = df.groupby("service")["achieved"].mean().reset_index()
            if not by_service.empty:
                fig2 = px.bar(by_service, x="service", y="achieved",
                              color="achieved", color_continuous_scale="Greens",
                              title="Average Achieved (%) by Service")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No service-level achievement data available.")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        The metrics view compares **targets vs actuals** and identifies where achievements consistently miss targets.
        **Response** and **Resolution** SLAs typically see bigger gaps under high ticket volumes, 
        while **Uptime** SLAs depend on infrastructure stability and vendor reliability.  
        Any persistent negative gap is a **cost driver** (overtime, penalties) and should be prioritized.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Auto-triage low-complexity tickets",
                "Introduce ‘virtual queue’ for overflow periods",
                "Align staffing to peak demand windows"
            ],
            "Benefit":[
                "Cuts time spent on routine work, reduces backlog",
                "Reduces wait-time spikes that trigger SLA breaches",
                "Avoids overtime and rework from under-staffing peaks"
            ],
            "Cost Calculation":[
                "30% of tickets × 10m saved ≈ 50h/month (RM3.4K)",
                "20% fewer breaches avoids penalties ≈ RM12K/year",
                "Peak resourcing saves ~RM8K/year in overtime"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Per-metric SLOs with SRE-style error budgets",
                "Pre-approved playbooks for common incidents",
                "Auto-escalate critical SLA types in backlog"
            ],
            "Benefit":[
                "Balances reliability with delivery speed",
                "Accelerates response & resolution consistency",
                "Prevents critical SLA breaches during spikes"
            ],
            "Cost Calculation":[
                "2% higher adherence ≈ RM10K saved/year",
                "15% faster MTTR saves ≈ RM9K/year",
                "10% fewer critical breaches ≈ RM15K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        We compare **targets** with what was actually achieved to spot where promises are missed.
        Automating simple cases, preparing playbooks, and staffing at peak hours help teams **hit targets** more consistently,
        saving money and improving service.
        """)
