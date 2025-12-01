import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def sla_exceptions(df):
    st.subheader("4️⃣ SLA Exceptions")

    with st.expander("🔎 Detailed Insights: SLA Exceptions"):
        st.markdown("### 📊 Graphs")

        # Breaches by Service
        if {"service","met"}.issubset(df.columns):
            svc = df.groupby("service")["met"].apply(lambda x: (~x).sum()).reset_index(name="Breaches")
            if not svc.empty:
                fig1 = px.bar(svc, x="service", y="Breaches", color="Breaches",
                              color_continuous_scale="Reds", title="SLA Breaches by Service")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No service breach data available.")

        # Breaches by SLA Type
        if {"sla_type","met"}.issubset(df.columns):
            slat = df.groupby("sla_type")["met"].apply(lambda x: (~x).sum()).reset_index(name="Breaches")
            if not slat.empty:
                fig2 = px.bar(slat, x="sla_type", y="Breaches", color="Breaches",
                              color_continuous_scale="Reds", title="SLA Breaches by SLA Type")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No SLA type breach data available.")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Exceptions show **where** and **what kind** of promises are most often missed.  
        Concentration of breaches in certain services or SLA types indicates **systemic issues** (e.g., chronic under-staffing, tool gaps, or vendor problems).  
        This view should feed directly into **capacity planning** and **improvement backlog**.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Focus fixes on top 2 breach-heavy services",
                "Rebalance workloads across teams",
                "Negotiate vendor support for weak areas"
            ],
            "Benefit":[
                "Maximum penalty avoidance ROI",
                "Reduces overtime & queue spikes",
                "Removes bottlenecks at lowest internal cost"
            ],
            "Cost Calculation":[
                "30% fewer breaches in top areas ≈ RM20K/year",
                "10% overtime reduction ≈ RM7K/year",
                "Vendor credits/support ≈ RM10K benefit"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Exception reviews with service owners",
                "Pre-emptive capacity holds during peaks",
                "Publish exception heatmap monthly"
            ],
            "Benefit":[
                "Creates ownership and targeted actions",
                "Prevents repeated misses at known peaks",
                "Drives transparency & sustained improvements"
            ],
            "Cost Calculation":[
                "15% fewer repeats ≈ RM8K/year",
                "Peak holds avoid ~RM12K penalties",
                "Visibility uplifts compliance ≈ RM6K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        This shows **where SLAs are being missed** most often.  
        We fix the biggest problem areas first, share the results openly, and staff up during busy periods to stop repeats.
        """)
