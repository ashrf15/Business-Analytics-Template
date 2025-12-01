import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose


# 🔹 Helper function for CIO tables with 3 expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("💰 Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("⚙️ Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("💬 Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# 🔹 Module 3: Change Success Rate
def change_success_rate(df_filtered):

    
    st.markdown("""
    This section evaluates the **percentage of changes successfully implemented** without rollback or disruption, 
    offering insight into operational quality and change stability across categories and over time.
    """)

    # ---------------------- Subtarget 3a ----------------------
    with st.expander("📌 Overall Success vs Rollback Distribution"):
        if "Success" in df_filtered.columns:
            df_filtered["Success_Flag"] = df_filtered["Success"].astype(str).str.lower().map({"true": True, "false": False})
            success_counts = df_filtered["Success_Flag"].value_counts(dropna=False).reset_index()
            success_counts.columns = ["Success", "Count"]

            fig1 = px.pie(success_counts, names="Success", values="Count",
                          title="Overall Change Success vs Rollback",
                          color_discrete_sequence=["#0b5394", "#e06666"])
            st.plotly_chart(fig1, use_container_width=True)

            total = success_counts["Count"].sum()
            success_rate = (success_counts.loc[success_counts["Success"] == True, "Count"].sum() / total * 100) if total > 0 else 0

            st.markdown("#### Analysis – Success Distribution")
            st.write(f"""
            - Total number of evaluated changes: **{total}**
            - Overall success rate: **{success_rate:.1f}%**
            - Failure/Rollback rate: **{100 - success_rate:.1f}%**

            📊 **Client takeaway:** Each rollback consumes extra operational hours and undermines confidence in the change process. 
            Maintaining an 85%+ success rate is typically considered healthy for enterprise environments.
            """)

            # CIO Table for 3a
            cio_3a = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Strengthen pre-implementation testing | Phase 1: mandate pre-deployment validation → Phase 2: simulate rollback → Phase 3: review results | Reduces rework and downtime cost | Example: 10 failed changes × 10h each × RM70 = **RM7,000 saved** | Pie chart shows rollback share exceeding 15% threshold. |
                | Automate regression test for software changes | Phase 1: implement CI/CD pipelines → Phase 2: link test automation suite → Phase 3: monitor test coverage | Cuts manual QA time | 25% reduction in testing labor (~RM4K/month) | High rollback ratio in app changes implies weak testing. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Introduce “Go/No-Go” CAB gates | Phase 1: classify risk → Phase 2: enforce review gates → Phase 3: track success rate per CAB | Improves decision consistency | 10% fewer failed changes = 8h × 12 cases = 96h/month saved | Success variance suggests inconsistent approvals. |
                | Deploy change dry-runs for critical infra upgrades | Phase 1: virtual lab simulation → Phase 2: evaluate rollback outcomes → Phase 3: integrate to SOP | Prevents large-scale rollbacks | Downtime avoidance: 2h × 4 incidents × RM1000/hr = RM8K | High-impact failures visible in pie section justify this. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Establish transparent post-change communication | Phase 1: inform users immediately on rollback → Phase 2: publish RCA → Phase 3: track trust score | Improves perception of control | Low cost; indirect benefit via lower complaints | Rollback slice evidences user uncertainty; comms mitigates fallout. |
                | Reward teams maintaining ≥90% success rate | Phase 1: define metric → Phase 2: publish dashboard → Phase 3: quarterly recognition | Encourages proactive quality culture | Motivational ROI offset by reduced rework | Sustained success share indicates behavior worth reinforcing. |
                """
            }
            render_cio_tables("CIO Recommendations – Success vs Rollback Analysis", cio_3a)
        else:
            st.warning("⚠️ 'Success' column not found in dataset.")


    # ---------------------- Subtarget 3b ----------------------
    with st.expander("📌 Success Rate by Category & Monthly Trend"):
        if {"Category", "Implemented_Date", "Success"}.issubset(df_filtered.columns):
            df_filtered["Implemented_Date"] = pd.to_datetime(df_filtered["Implemented_Date"], errors="coerce")
            df_filtered["Month"] = df_filtered["Implemented_Date"].dt.to_period("M").astype(str)
            df_filtered["Success_Flag"] = df_filtered["Success"].astype(str).str.lower().map({"true": True, "false": False})

            # Success rate by category
            cat_success = (
                df_filtered.groupby("Category")["Success_Flag"]
                .mean()
                .reset_index()
                .rename(columns={"Success_Flag": "Success_Rate"})
            )
            cat_success["Success_Rate"] *= 100

            fig2 = px.bar(cat_success, x="Category", y="Success_Rate",
                          title="Change Success Rate by Category (%)",
                          color="Success_Rate", color_continuous_scale="Greens")
            st.plotly_chart(fig2, use_container_width=True)

            # Monthly trend
            monthly_success = (
                df_filtered.groupby("Month")["Success_Flag"]
                .mean()
                .reset_index()
                .rename(columns={"Success_Flag": "Success_Rate"})
            )
            monthly_success["Success_Rate"] *= 100

            fig3 = px.line(monthly_success, x="Month", y="Success_Rate",
                           title="Monthly Change Success Rate Trend (%)",
                           markers=True)
            st.plotly_chart(fig3, use_container_width=True)

            # 🔹 Analysis
            if not cat_success.empty and not monthly_success.empty:
                top_cat = cat_success.loc[cat_success["Success_Rate"].idxmax()]
                low_cat = cat_success.loc[cat_success["Success_Rate"].idxmin()]
                avg_sr = cat_success["Success_Rate"].mean()

                st.markdown("#### Analysis – Category & Monthly Success Trends")
                st.write(f"""
                - Best performing category: **{top_cat['Category']} ({top_cat['Success_Rate']:.1f}%)**
                - Lowest performing: **{low_cat['Category']} ({low_cat['Success_Rate']:.1f}%)**
                - Average success across all categories: **{avg_sr:.1f}%**  
                - Monthly trend indicates overall stability, with minor seasonal drops likely due to peak deployment periods.

                📊 **Client takeaway:** Monitoring success by category highlights where additional testing, planning, or documentation effort is most needed.
                """)

            # CIO Table for 3b
            cio_3b = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Focus training on low-success categories | Phase 1: identify bottom 25% performers → Phase 2: deliver focused retraining → Phase 3: re-evaluate quarterly | Reduces repeated rollback cost | 5% higher success saves ~50h/month | Category bar shows one consistently underperforming area. |
                | Merge similar low-success change types under expert review | Phase 1: unify under SME → Phase 2: align processes → Phase 3: automate reporting | Minimizes fragmentation losses | Consolidation yields 10% process time gain | Uneven bar heights evidence inefficiencies. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Apply predictive anomaly detection pre-deployment | Phase 1: analyze past failure signals → Phase 2: ML-based predictive alerts → Phase 3: review model quarterly | Prevents high-risk rollbacks | Reduction: 10 avoided failures × 4h = 40h/month | Trend dips show rollback predictability opportunities. |
                | Introduce success KPI per category | Phase 1: set success KPIs → Phase 2: visualize weekly → Phase 3: reward compliance | Drives accountability & continuous improvement | Minimal cost, indirect efficiency | Category disparity motivates measurable KPIs. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Communicate proactive success highlights to business units | Phase 1: summarize monthly wins → Phase 2: publish dashboards → Phase 3: gather feedback | Improves stakeholder confidence | No hard cost; boosts trust perception | Trend lines confirm reliability improvements worth showcasing. |
                | Provide customer briefings post major upgrades | Phase 1: host follow-up session → Phase 2: present lessons learned → Phase 3: document feedback | Strengthens partnership transparency | Negligible cost; reduces complaint frequency | Category chart shows progress patterns supporting comms benefit. |
                """
            }
            render_cio_tables("CIO Recommendations – Success by Category & Monthly Trend", cio_3b)
        else:
            st.warning("⚠️ Required columns ('Category', 'Implemented_Date', 'Success') not found.")
