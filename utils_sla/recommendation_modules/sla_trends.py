import streamlit as st
import plotly.express as px
import pandas as pd

def _nonempty(obj):
    return obj is not None and hasattr(obj, "__len__") and len(obj) > 0

def sla_trend(df):
    st.subheader("3️⃣ SLA Performance Trend")

    with st.expander("🔎 Detailed Insights: SLA Performance Trend"):
        st.markdown("### 📊 Graphs")

        if {"date","met"}.issubset(df.columns):
            df_time = df.dropna(subset=["date"]).copy()
            if not df_time.empty:
                df_time["month"] = pd.to_datetime(df_time["date"], errors="coerce").dt.to_period("M")
                trend = df_time.groupby("month")["met"].mean().reset_index()
                trend["month"] = trend["month"].astype(str)
                trend["Compliance_%"] = (trend["met"] * 100).round(1)
                fig1 = px.line(trend, x="month", y="Compliance_%", markers=True,
                               title="Monthly SLA Compliance Trend (%)")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No dated records available for trend view.")
        else:
            st.info("Date/Met columns missing for trend analysis.")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Trend analysis reveals **improvements or slippage** month-to-month.  
        A downward trend often aligns with **ticket spikes, staff churn, or infrastructure instability**.  
        Sustained declines should trigger **capacity planning review** and corrective actions in the struggling services.
        """)

        # 💰 CIO: Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Pre-buffer staff during seasonal spikes",
                "Introduce demand-based ticket deflection (FAQs/Chatbots)",
                "Prioritize automation backlog on SLA types with decline"
            ],
            "Benefit":[
                "Avoids overtime & SLA penalties",
                "Reduces volume entering queues",
                "Targets the biggest gap for ROI"
            ],
            "Cost Calculation":[
                "10% fewer breaches ≈ RM15K/year",
                "15% ticket deflection ≈ RM12K/year",
                "Automating top-2 gaps ≈ RM8K/year saved"
            ]
        }))

        # 🚀 CIO: Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":[
                "Weekly SLA trend standup with owners",
                "Real-time ‘at risk’ alerts (SLA burn-down)",
                "Goal-based OKRs tied to trend reversal"
            ],
            "Benefit":[
                "Creates accountability & rapid adjustments",
                "Prevents breaches instead of reacting late",
                "Aligns teams on measurable turnarounds"
            ],
            "Cost Calculation":[
                "2% uplift from faster reactions ≈ RM6K/year",
                "15% fewer breaches from alerts ≈ RM10K/year",
                "OKR-driven improvements ≈ RM9K/year"
            ]
        }))

        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        The line shows if performance is **getting better or worse** each month.  
        If it dips, we add staff at busy times, reduce incoming tickets with self-service, and focus improvements where the drop is largest.
        """)
