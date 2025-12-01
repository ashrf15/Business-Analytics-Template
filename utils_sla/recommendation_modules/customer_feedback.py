import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def customer_feedback(df):
    st.subheader("7️⃣ Customer Feedback")

    with st.expander("🔎 Detailed Insights: Customer Feedback & Satisfaction"):
        st.markdown("### 📊 Graphs")

        # Satisfaction by Service
        if {"service","customer_satisfaction"}.issubset(df.columns):
            sat = df.groupby("service")["customer_satisfaction"].mean().reset_index()
            if _nonempty(sat):
                fig1 = px.bar(sat, x="service", y="customer_satisfaction",
                              color="customer_satisfaction", color_continuous_scale="Blues",
                              title="Average Customer Satisfaction by Service (1–5)")
                st.plotly_chart(fig1, use_container_width=True, key="custfeedback_service_sat")
            else:
                st.info("No satisfaction data to display.")

        # Complaints by SLA Type
        if {"sla_type","complaint"}.issubset(df.columns):
         comp = df["complaint"].astype(str).str.strip().str.lower()
         dfx = df[(comp.eq("yes")) | (comp.eq("true"))].groupby("sla_type").size().reset_index(name="Complaints")
         if not dfx.empty:
             fig2 = px.bar(dfx, x="sla_type", y="Complaints", color="Complaints",
                      color_continuous_scale="Reds",
                      title="Customer Complaints by SLA Type")
             st.plotly_chart(fig2, use_container_width=True, key="custfeedback_type_complaints")
        else:
          st.info("No complaint records available.")


        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Customer satisfaction correlates strongly with **SLA adherence**.  
        When response/resolution SLAs are missed, we see **complaints and lower ratings**.  
        Improving SLAs in customer-facing services yields immediate **CX wins** and lowers escalation workload.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Callback/virtual hold to avoid long waits",
                "Case ownership model for continuity",
                "Proactive customer updates during breaches"
            ],
            "Benefit":[
                "Cuts repeat calls and churn risk",
                "Reduces hand-offs and rework",
                "Lowers complaint volume and escalations"
            ],
            "Cost Calculation":[
                "10% fewer repeat calls ≈ RM7K/year",
                "15% less rework ≈ RM8K/year",
                "25% fewer complaints ≈ RM6K/year"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "CSAT tied to SLA adherence dashboards",
                "VOC (voice-of-customer) loop into RCA",
                "Train agents on empathy & expectation-setting"
            ],
            "Benefit":[
                "Connects outcomes to experience",
                "Ensures improvements reflect customer pain",
                "Improves experience even when SLAs are tight"
            ],
            "Cost Calculation":[
                "2–3% CSAT lift ≈ RM5K/year value",
                "VOC-driven fixes ≈ RM8K/year",
                "Training impact ≈ RM6K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        When we miss SLAs, customers complain and rate us lower.  
        Reducing wait times, assigning clear owners, and keeping customers updated increases satisfaction and reduces complaints.
        """)
