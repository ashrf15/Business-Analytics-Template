import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def root_cause(df):
    st.subheader("5️⃣ Root Cause Analysis")

    with st.expander("🔎 Detailed Insights: Root Causes of SLA Breaches"):
        st.markdown("### 📊 Graphs")

        if {"breach_reason","met"}.issubset(df.columns):
            reasons = df[df["met"] == False]["breach_reason"].value_counts().reset_index()
            reasons.columns = ["breach_reason","count"]
            if not reasons.empty:
                fig1 = px.bar(reasons, x="breach_reason", y="count", color="count",
                              color_continuous_scale="Reds", title="Top SLA Breach Reasons")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No recorded breach reasons to visualize.")
        else:
            st.info("Breach_Reason/Met columns missing for root cause view.")
            
        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Common root causes include **High Volume (demand spikes)**, **Resource Shortage**, **Infrastructure Failures**, 
        and **3rd Party Delays**.  
        Each cause implies a different response: capacity management and self-service for volume, 
        hiring or cross-training for resource gaps, resilience improvements for infra, and stronger contracts/escalations for vendors.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Deflect FAQs with self-service and chatbots",
                "Cross-train staff across services",
                "Harden critical infrastructure components"
            ],
            "Benefit":[
                "Lowers incoming volume and queue time",
                "Reduces dependency on specific FTEs",
                "Avoids outages & high-cost breaches"
            ],
            "Cost Calculation":[
                "15% deflection ≈ RM12K/year",
                "10% FTE flexibility saves ≈ RM8K",
                "Avoid 2 infra-related breaches ≈ RM10K/year"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Real-time vendor escalation rules",
                "Capacity forecasting model by service",
                "RCA on every repeated breach cause"
            ],
            "Benefit":[
                "Faster vendor-time recovery",
                "Prepares teams for spikes",
                "Prevents repeated issues"
            ],
            "Cost Calculation":[
                "20% faster vendor recovery ≈ RM6K/year",
                "10% fewer peak breaches ≈ RM9K/year",
                "Repeat breach reduction ≈ RM7K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        We identify **why** SLAs are missed (volume, resources, systems, vendors).  
        Then we match each cause with a fix: deflect tickets, add skills, strengthen systems, and escalate vendors faster.
        """)
