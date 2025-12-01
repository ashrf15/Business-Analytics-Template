import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def service_improvement(df):
    st.subheader("8️⃣ Service Improvement Initiatives")

    with st.expander("🔎 Detailed Insights: Improvement Roadmap & Status"):
        st.markdown("### 📊 Graphs")

        # Improvement opportunities: where compliance is lowest
        if {"service","set"}.issubset(df.columns):
            svc_comp = df.groupby("service")["met"].mean().reset_index()
            if _nonempty(svc_comp):
                svc_comp["compliance_%"] = (svc_comp["met"] * 100).round(1)
                svc_comp.sort_values("compliance_%", inplace=True)
                fig1 = px.bar(svc_comp, x="service", y="compliance_%", color="compliance_%",
                              color_continuous_scale="Reds",
                              title="Improvement Priority: Lowest Compliance Services First")
                st.plotly_chart(fig1, use_container_width=True, key="improve_priority_services")
            else:
                st.info("No service compliance data to rank improvements.")

        # SLA_Type improvement priority
        if {"sla_type","met"}.issubset(df.columns):
            stype = df.groupby("sla_type")["met"].mean().reset_index()
            if _nonempty(stype):
                stype["compliance_%"] = (stype["met"] * 100).round(1)
                stype.sort_values("compliance_%", inplace=True)
                fig2 = px.bar(stype, x="sla_type", y="compliance_%", color="compliance_%",
                              color_continuous_scale="Reds",
                              title="Improvement Priority by SLA Type")
                st.plotly_chart(fig2, use_container_width=True, key="improve_priority_types")
            else:
                st.info("No SLA type compliance data to rank improvements.")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Improvement should be **portfolio-managed**: tackle the biggest compliance gaps first 
        (by service and SLA type), then sustain gains with standardization and automation.  
        This avoids spreading teams too thin and focuses the budget on **highest ROI**.
        """)

        # 💰 CIO: Cost Reduction (project-style table)
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Automate top 2 SLA types with most breaches",
                "Unify monitoring/alerting across services",
                "Rationalize vendor SLAs & support tiers"
            ],
            "Benefit":[
                "Removes the largest recurring manual effort",
                "Reduces tooling costs and false negatives",
                "Lowers contract cost and simplifies governance"
            ],
            "Cost Calculation":[
                "30% fewer manual tasks ≈ RM18K/year",
                "1 tool consolidation ≈ RM12K/year",
                "10% vendor cost reduction ≈ RM20K/year"
            ]
        }))

        # 🚀 CIO: Performance Improvement (project-style table)
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "SRE-style reliability goals with error budgets",
                "Playbook library with automation hooks",
                "Quarterly service reviews with OKRs"
            ],
            "Benefit":[
                "Balances new features with reliability",
                "Faster, safer incident handling",
                "Sustained improvements and accountability"
            ],
            "Cost Calculation":[
                "3% compliance uplift ≈ RM12K/year",
                "20% faster incident handling ≈ RM10K/year",
                "OKR-driven gains ≈ RM8K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        We invest where the **gaps are largest** to get the best value.
        Automating repetitive work, standardizing tools, and setting clear quarterly goals help lift SLA performance across the board.
        """)
