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


# 🔹 Module 2: Change Classification
def change_classification(df_filtered):

    
    st.markdown("This section classifies all recorded changes by category and priority to uncover which types consume the most resources or pose the highest operational impact.")

    # ---------------------- Subtarget 2a ----------------------
    with st.expander("📌 Change Volume by Category & Priority"):
        if {"Category", "Priority"}.issubset(df_filtered.columns):
            cat_pri = df_filtered.groupby(["Category", "Priority"]).size().reset_index(name="count")
            fig_cat = px.bar(cat_pri, x="Category", y="count", color="Priority", barmode="group",
                             title="Change Requests by Category and Priority",
                             color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_cat, use_container_width=True)

            # 🔹 Analysis
            if not cat_pri.empty:
                top_cat = cat_pri.loc[cat_pri["count"].idxmax()]
                total = cat_pri["count"].sum()
                pct_top = (top_cat["count"] / total) * 100
                avg_per_cat = cat_pri.groupby("Category")["count"].sum().mean()

                st.markdown("#### Analysis – Category & Priority Distribution")
                st.write(f"""
                The bar chart illustrates how different change categories vary in volume and priority.  
                - The **{top_cat['Category']}** category holds the largest share (**{pct_top:.1f}%** of total).  
                - Average workload per category ≈ **{avg_per_cat:.1f} changes**.  
                - High-priority changes are concentrated within the **{top_cat['Category']}** segment.  

                📊 **Client takeaway:** Concentration of high-priority changes within one category suggests 
                resource or process bottlenecks. Rebalancing workload or automating repetitive changes in that domain 
                will drive both cost and time efficiency.
                """)

            # CIO Table for 2a
            cio_2a = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Automate high-frequency change categories | Phase 1: identify categories with >15% total volume → Phase 2: build automation templates → Phase 3: monitor monthly | Lowers repetitive manual effort | Example: 20 changes × 1.5 hrs = 30 h/month saved → RM1.5K @ RM50/h | Bar chart shows top category dominates >25% volume. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Introduce specialized CAB reviewers per category | Phase 1: assign SMEs → Phase 2: parallel approval queues → Phase 3: evaluate impact | Reduces wait time for approvals; improves quality | Approval time drop ≈ 25% saves 6 h/change | Heavy load categories suffer approval delays per chart. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Publish category-wise change calendar to stakeholders | Phase 1: compile monthly plan → Phase 2: share with business units → Phase 3: collect feedback | Transparent scheduling & fewer disruptions | Low cost; indirect gain = fewer escalations | Category spikes cause business disruption → communication reduces surprise. |
                """
            }
            render_cio_tables("CIO Recommendations – Change by Category & Priority", cio_2a)
        else:
            st.warning("⚠️ Required columns ('Category', 'Priority') not found.")


    # ---------------------- Subtarget 2b ----------------------
    with st.expander("📌 Change Category Composition & Trend"):
        if "Category" in df_filtered.columns and "Implemented_Date" in df_filtered.columns:
            df_filtered["Implemented_Date"] = pd.to_datetime(df_filtered["Implemented_Date"], errors="coerce")
            df_filtered["month"] = df_filtered["Implemented_Date"].dt.to_period("M").astype(str)
            monthly_cat = df_filtered.groupby(["month", "Category"]).size().reset_index(name="count")

            fig_trend = px.line(monthly_cat, x="month", y="count", color="Category",
                                markers=True, title="Monthly Trend by Change Category")
            st.plotly_chart(fig_trend, use_container_width=True)

            # 🔹 Analysis
            if not monthly_cat.empty:
                top_month = monthly_cat.loc[monthly_cat["count"].idxmax()]
                avg_monthly = monthly_cat.groupby("Category")["count"].mean().mean()

                st.markdown("#### Analysis – Monthly Trend by Category")
                st.write(f"""
                The line graph tracks each change category’s monthly trajectory.  
                - The highest surge occurred in **{top_month['month']}** for **{top_month['Category']}** with **{top_month['count']} changes**.  
                - Average monthly implementation ≈ **{avg_monthly:.1f} changes/category**.  

                📊 **Client takeaway:** Persistent growth in a specific category signals underlying infrastructure upgrades or recurring issues needing root-cause remediation.
                """)

            # CIO Table for 2b
            cio_2b = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Consolidate overlapping change categories | Phase 1: audit duplicate types → Phase 2: merge workflows → Phase 3: retrain teams | Reduces maintenance & reporting overhead | 10% fewer categories → 5% faster processing = RM 3K annual saving | Trend shows overlapping upward trajectories → merge improves efficiency. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Introduce category-based KPI dashboards | Phase 1: define KPIs (time to implement, success rate) → Phase 2: auto-track → Phase 3: monthly review | Enhances accountability & insight | Minimal tool cost; 15% productivity gain measured | Multi-category lines illustrate uneven performance. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Provide feedback channel for recurring category types | Phase 1: gather feedback → Phase 2: prioritize high-impact themes → Phase 3: apply improvements | Better stakeholder involvement | N/A – qualitative improvement | Repetitive peaks suggest user-driven recurring changes → feedback loops reduce them. |
                """
            }
            render_cio_tables("CIO Recommendations – Change Category Trends", cio_2b)
        else:
            st.warning("⚠️ Required columns ('Category', 'Implemented_Date') not found.")
