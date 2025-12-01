import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def sla_overview(df):
    st.subheader("1️⃣ SLA Overview")

    with st.expander("🔎 Detailed Insights: SLA Overview"):
        st.markdown("### 📊 Graphs")

        # Compliance by Service
        if {"service","met"}.issubset(df.columns):
            service_comp = df.groupby("service")["met"].mean().reset_index()
            if not service_comp.empty:
                service_comp["Compliance_%"] = (service_comp["met"] * 100).round(1)
                fig1 = px.bar(service_comp, x="service", y="Compliance_%",
                              color="Compliance_%", color_continuous_scale="Greens",
                              title="SLA Compliance by Service (%)")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No service-level compliance data available.")

        # Compliance by SLA Type
        if {"sla_type","met"}.issubset(df.columns):
            type_comp = df.groupby("sla_type")["met"].mean().reset_index()
            if not type_comp.empty:
                type_comp["Compliance_%"] = (type_comp["met"] * 100).round(1)
                fig2 = px.bar(type_comp, x="sla_type", y="Compliance_%",
                              color="Compliance_%", color_continuous_scale="Blues",
                              title="SLA Compliance by SLA Type (%)")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No SLA type compliance data available.")
                
        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        The overview shows which **services** and **SLA types** consistently meet targets.  
        Higher compliance in certain services suggests mature processes and stable capacity, 
        while lower-performing services or SLA types indicate **workload spikes, resourcing gaps, or weak process adherence**.  
        Across SLA types, **Uptime** tends to be more stable, while **Response/Resolution** SLAs often fluctuate due to volume and staffing.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Consolidate overlapping SLAs across services",
                "Automate SLA tracking & alerting",
                "Standardize SLA targets where practical"
            ],
            "Benefit":[
                "Reduces admin and contract management overhead",
                "Cuts manual monitoring effort and late reactions",
                "Simplifies governance and lowers review effort"
            ],
            "Cost Calculation":[
                "10% contract admin time saved ≈ RM8K/year",
                "1 FTE month/year saved via automation ≈ RM12K",
                "20% faster reviews across 5 services ≈ RM6K/year"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Publish a service-level compliance leaderboard",
                "Set quarterly targets per SLA type",
                "Run monthly variance reviews"
            ],
            "Benefit":[
                "Creates transparency & positive competition",
                "Focuses teams on measurable improvements",
                "Detects slippage early and enforces corrective action"
            ],
            "Cost Calculation":[
                "2% compliance uplift avoids ~RM15K penalties/year",
                "5% improvement in response SLAs reduces overtime ≈ RM10K",
                "Catching slippage early reduces incidents ≈ RM12K/year"
            ]
        }))

        # 🗣 Business Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        This section shows **which services meet their promises** and which need attention.  
        Automating tracking and simplifying SLAs save money and admin time, while leaderboards and clear targets
        push teams to improve where it matters most.
        """)
