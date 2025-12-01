import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("💰 Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("⚙️ Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("💬 Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# 🔹 Module 1: Change Overview
def change_overview(df_filtered):

    if "Implemented_Date" not in df_filtered.columns:
        st.warning("⚠️ 'Implemented_Date' column not found in dataset.")
        return

    df_filtered["Implemented_Date"] = pd.to_datetime(df_filtered["Implemented_Date"], errors="coerce")
    df_filtered["implemented_date"] = df_filtered["Implemented_Date"].dt.date
    daily = df_filtered.groupby("implemented_date").size().reset_index(name="change_count")
    daily["implemented_date"] = pd.to_datetime(daily["implemented_date"])
    daily = daily.sort_values("implemented_date")

    
    st.markdown("This section provides a comprehensive look at total submitted, implemented, and backlog changes across time to identify growth patterns and operational workload.")

    # ---------------------- Subtarget 1a ----------------------
    with st.expander("📌 Daily / Monthly Change Volume Overview"):
        # --- Graph 1: Daily line chart
        fig_daily = px.line(daily, x="implemented_date", y="change_count",
                            title="Daily Implemented Changes Trend",
                            color_discrete_sequence=["#0b5394"])
        st.plotly_chart(fig_daily, use_container_width=True)

        # 🔹 Analysis for Graph 1
        if not daily.empty:
            max_day = daily.loc[daily["change_count"].idxmax()]
            min_day = daily.loc[daily["change_count"].idxmin()]
            avg_day = daily["change_count"].mean()

            st.markdown("#### Analysis – Daily Trend")
            st.write(f"""
            The **daily trend line** represents the total number of implemented changes per day.  
            - Peak activity occurred on **{max_day['implemented_date'].strftime('%Y-%m-%d')}**, when **{max_day['change_count']} changes** were deployed.  
            - The lowest recorded activity was **{min_day['implemented_date'].strftime('%Y-%m-%d')}** with only **{min_day['change_count']} changes**.  
            - On average, approximately **{avg_day:.1f} changes** were implemented daily.

            📊 **Client takeaway**: This graph helps identify deployment bursts or quiet periods, indicating when IT operations were most or least active.
            """)

        # --- Graph 2: Monthly totals
        daily["month"] = daily["implemented_date"].dt.to_period("M")
        monthly = daily.groupby("month")["change_count"].sum().reset_index()
        monthly["month"] = monthly["month"].dt.strftime("%Y-%m")
        fig_month = px.bar(monthly, x="month", y="change_count",
                           title="Monthly Implemented Changes Volume",
                           color_discrete_sequence=["#1a73e8"])
        st.plotly_chart(fig_month, use_container_width=True)

        if not monthly.empty:
            max_month = monthly.loc[monthly["change_count"].idxmax()]
            min_month = monthly.loc[monthly["change_count"].idxmin()]
            avg_month = monthly["change_count"].mean()

            st.markdown("#### Analysis – Monthly Totals")
            st.write(f"""
            The **monthly totals** reveal how the change volume fluctuated month-to-month.  
            - The busiest month recorded **{max_month['change_count']} changes** in **{max_month['month']}**.  
            - The lowest was **{min_month['change_count']} changes** in **{min_month['month']}**.  
            - The average monthly implementation rate was **{avg_month:.0f} changes**.

            📊 **Client takeaway**: These insights enable capacity forecasting — knowing high-implementation months helps teams plan staffing and scheduling better.
            """)

        # CIO Table for 1a
        cio_1a = {
            "cost": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Numeric Example) | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|----------------------------------------------|--------------------------------|
            | Optimize resource allocation during high-volume change periods | Phase 1: Identify peak implementation months → Phase 2: adjust staff scheduling → Phase 3: monitor for overtime reduction | Reduces excess labor cost and resource burnout | Example: 15% reduction in overtime hours × 160 hours × RM50/hr = **RM1,200 saved/month** | Graph shows peak month of high workload (e.g., May = 42 changes). Adjusting staff cuts unplanned overtime. |
            """,
            "performance": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | Automate recurring low-risk changes | Phase 1: Identify repetitive low-impact changes → Phase 2: script or template automation → Phase 3: review success metrics | Frees engineers for high-value tasks | If 20% of monthly 80 changes automated → 16 changes saved × 2h each = 32h saved | The recurring baseline in monthly volume suggests automation opportunity. |
            """,
            "satisfaction": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | Communicate deployment schedules to stakeholders | Phase 1: share upcoming change calendar → Phase 2: real-time update dashboards → Phase 3: track feedback | Reduces user surprise and post-change issues | Improved feedback ratings and fewer duplicate service calls | Volume spikes indicate poor scheduling communication — better awareness prevents friction. |
            """
        }
        render_cio_tables("CIO Recommendations – Change Volume Management", cio_1a)


    # ---------------------- Subtarget 1b ----------------------
    with st.expander("📌 Change Backlog and Implementation Ratio"):
        if "Status" in df_filtered.columns:
            df_filtered["status_clean"] = df_filtered["Status"].astype(str).str.lower()
            df_filtered["implemented_flag"] = df_filtered["status_clean"].eq("implemented")
            daily_backlog = df_filtered.groupby("implemented_date")["implemented_flag"].agg(["sum", "count"])
            daily_backlog["pending"] = daily_backlog["count"] - daily_backlog["sum"]
            daily_backlog = daily_backlog.reset_index()

            # Graph 1: Implemented vs Pending
            fig_backlog = px.bar(
                daily_backlog, x="implemented_date",
                y=["sum", "pending"],
                title="Implemented vs Pending Changes Over Time",
                labels={"value": "Count", "implemented_date": "Date", "variable": "Status"},
                color_discrete_sequence=["#0b5394", "#c9daf8"]
            )
            st.plotly_chart(fig_backlog, use_container_width=True)

            total_impl = daily_backlog["sum"].sum()
            total_pending = daily_backlog["pending"].sum()
            impl_ratio = (total_impl / (total_impl + total_pending) * 100) if (total_impl + total_pending) > 0 else 0

            st.markdown("#### Analysis – Implementation Ratio")
            st.write(f"""
            - Total implemented changes: **{total_impl}**
            - Total pending changes: **{total_pending}**
            - Overall implementation ratio: **{impl_ratio:.1f}%**

            📊 **Client takeaway**: Maintaining a consistent implementation rate ensures backlog doesn’t accumulate and disrupt future planning cycles.
            """)

            # CIO Table for 1b
            cio_1b = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Prioritize automation for low-risk approvals | Phase 1: Identify non-critical changes pending > 7 days → Phase 2: automate routine approvals → Phase 3: monitor outcome | Reduces manual overhead in approval processing | If 25% of 40 backlog items automated = 10 × 1.5h each = 15h saved weekly | Graph shows a persistent pending portion indicating delayed processing. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Introduce change backlog SLA (auto alert after threshold) | Phase 1: Define SLA (e.g. 5 days) → Phase 2: trigger automated reminders → Phase 3: enforce accountability | Increases throughput and consistency | Reduction in average backlog duration from 12 → 8 days = 33% faster throughput | Ratio chart shows backlog spikes exceeding SLA windows. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Improve communication between requestors & implementers | Phase 1: escalation channels → Phase 2: weekly status review → Phase 3: publish backlog dashboard | Builds transparency and trust | Low cost (internal coordination) – value in reduced dissatisfaction reports | Persistent backlog indicates misalignment in change communication. |
                """
            }
            render_cio_tables("CIO Recommendations – Change Backlog Management", cio_1b)
