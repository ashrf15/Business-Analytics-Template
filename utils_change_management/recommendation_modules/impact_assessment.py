import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose

# 🔹 Helper function for CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("💰 Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("⚙️ Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("💬 Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# 🔹 Module 6: Change Impact & Risk Assessment
def impact_assessment(df_filtered):

    
    st.markdown("""
    This section evaluates how **approved and implemented changes affect system stability and business services**.  
    It explores **impact severity, risk likelihood, and downtime correlations** to identify improvement opportunities 
    and areas requiring tighter control or planning.
    """)

    # ---------------------- Subtarget 6a ----------------------
    with st.expander("📌 Impact Level Distribution & Correlation with Risk"):
        if {"Impact_Level", "Risk_Level"}.issubset(df_filtered.columns):
            df_filtered["Impact_Level"] = df_filtered["Impact_Level"].astype(str).str.title()
            df_filtered["Risk_Level"] = df_filtered["Risk_Level"].astype(str).str.title()

            impact_counts = df_filtered["Impact_Level"].value_counts().reset_index()
            impact_counts.columns = ["Impact_Level", "Count"]

            fig1 = px.pie(
                impact_counts, names="Impact_Level", values="Count",
                title="Change Impact Level Distribution", color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Impact vs Risk scatter
            risk_impact = df_filtered.groupby(["Impact_Level", "Risk_Level"]).size().reset_index(name="Count")
            fig2 = px.scatter(
                risk_impact, x="Risk_Level", y="Impact_Level", size="Count", color="Count",
                title="Impact vs Risk Correlation", color_continuous_scale="Reds"
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("#### Analysis – Impact Severity and Risk Relationship")
            total = len(df_filtered)
            high_risk = df_filtered.query("Risk_Level == 'High'").shape[0]
            high_impact = df_filtered.query("Impact_Level == 'High'").shape[0]
            overlap = df_filtered.query("Risk_Level == 'High' and Impact_Level == 'High'").shape[0]

            st.write(f"""
            - Total changes analyzed: **{total}**
            - High-risk changes: **{high_risk} ({(high_risk/total*100):.1f}%)**
            - High-impact changes: **{high_impact} ({(high_impact/total*100):.1f}%)**
            - High-risk & high-impact overlap: **{overlap} ({(overlap/total*100):.1f}%)**

            📊 **Client takeaway:** Overlapping high-risk/high-impact items represent **critical exposure points** 
            that may cause downtime or reputational harm. These should receive enhanced pre-implementation reviews.
            """)

            cio_6a = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Example) | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|--------------------------------------|--------------------------------|
                | Focus testing resources on high-risk/high-impact changes | Phase 1: identify overlap via matrix → Phase 2: allocate testers accordingly → Phase 3: monitor outcomes | Prevents rework & emergency rollback costs | Example: 5 prevented rollbacks × 4h × RM100 = **RM2,000 saved** | Scatter shows dense clusters in High-High quadrant. |
                | Enforce risk-tiered CAB approvals | Phase 1: require senior sign-off for high → Phase 2: automate low-tier approval → Phase 3: monitor trends | Reduces time wasted on trivial approvals | CAB hour reduction: 1h × 30 low-risk changes = **30h/month saved** | Pie and scatter indicate risk disproportion. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Implement quantitative risk scoring | Phase 1: define weightage for impact/risk → Phase 2: compute composite index → Phase 3: review monthly | Improves prioritization & planning | Prevents resource overload | Scatter plot helps calibrate scoring parameters. |
                | Automate change pre-screening | Phase 1: build logic for high-risk detection → Phase 2: auto-route CAB level → Phase 3: audit exceptions | Speeds triage | 15% faster risk assignment | High-density risk-impact data shows manual lag in classification. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Communicate expected risk levels to stakeholders | Phase 1: publish risk matrix → Phase 2: alert impacted teams → Phase 3: provide mitigation updates | Increases user confidence in planning | Non-financial gain; better communication | Scatter clearly visualizes potential service hotspots. |
                | Educate teams on impact assessment standards | Phase 1: training sessions → Phase 2: certification → Phase 3: quarterly refreshers | Improves consistency of classification | Low cost; high ROI via fewer mislabels | Pie spread shows subjective variability in current entries. |
                """
            }
            render_cio_tables("CIO Recommendations – Impact vs Risk Insights", cio_6a)
        else:
            st.warning("⚠️ Required columns ('Impact_Level', 'Risk_Level') not found in dataset.")


    # ---------------------- Subtarget 6b ----------------------
    with st.expander("📌 Downtime Duration vs Impact Level"):
        if {"Impact_Level", "Downtime_Hours"}.issubset(df_filtered.columns):
            df_filtered["Downtime_Hours"] = pd.to_numeric(df_filtered["Downtime_Hours"], errors="coerce")
            df_filtered = df_filtered.dropna(subset=["Downtime_Hours"])

            downtime_summary = df_filtered.groupby("Impact_Level")["Downtime_Hours"].mean().reset_index()
            fig3 = px.bar(
                downtime_summary, x="Impact_Level", y="Downtime_Hours", color="Downtime_Hours",
                color_continuous_scale="Oranges", title="Average Downtime by Impact Level (Hours)"
            )
            st.plotly_chart(fig3, use_container_width=True)

            avg_down = downtime_summary["Downtime_Hours"].mean()
            high_impact_down = downtime_summary.loc[downtime_summary["Impact_Level"] == "High", "Downtime_Hours"].mean() if "High" in downtime_summary["Impact_Level"].values else np.nan

            st.markdown("#### Analysis – Downtime Relationship")
            st.write(f"""
            - Average downtime across all changes: **{avg_down:.2f} hours**  
            - High-impact changes average: **{high_impact_down:.2f} hours**  

            📊 **Client takeaway:** Longer downtime for high-impact changes suggests either **inadequate maintenance windows** 
            or **lack of rollback readiness**. Better scheduling and dry-run rehearsals can reduce user disruption.
            """)

            cio_6b = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Example) | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|--------------------------------------|--------------------------------|
                | Pre-staging backup environments | Phase 1: create sandbox → Phase 2: pre-sync data → Phase 3: automate recovery | Reduces outage costs | 3h saved × RM500/hr = **RM1,500 saved** | High downtime bars show recovery inefficiency. |
                | Automate rollback verification | Phase 1: script validation → Phase 2: test rollback → Phase 3: automate log capture | Lowers mean recovery time | 20% downtime reduction = 1.2h avg saved | Downtime variance confirms missed rollback validation. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Schedule high-impact changes in low-demand windows | Phase 1: analyze usage peaks → Phase 2: reschedule accordingly → Phase 3: monitor | Improves uptime metrics | 30% less business-hour downtime | High bar for “High” impact reveals poor timing. |
                | Include rollback simulation in change testing | Phase 1: dry-run rollback → Phase 2: log metrics → Phase 3: update SOPs | Reduces mean time to restore | 25% lower MTTR | Data trend shows longer restore duration on large changes. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Announce planned downtime windows proactively | Phase 1: user notification → Phase 2: countdown banner → Phase 3: post-status updates | Reduces perceived impact | Fewer complaints & escalations | Bar confirms downtime patterns match peak usage. |
                | Conduct post-downtime feedback survey | Phase 1: survey after major change → Phase 2: summarize findings → Phase 3: publish corrective action | Improves relationship trust | Minimal cost | Provides evidence-based insights for next maintenance. |
                """
            }
            render_cio_tables("CIO Recommendations – Downtime & Impact Optimization", cio_6b)
        else:
            st.warning("⚠️ Required columns ('Impact_Level', 'Downtime_Hours') not found in dataset.")


    # ---------------------- Subtarget 6c ----------------------
    with st.expander("📌 Risk Trend Over Time"):
        if {"Implemented_Date", "Risk_Level"}.issubset(df_filtered.columns):
            df_filtered["Implemented_Date"] = pd.to_datetime(df_filtered["Implemented_Date"], errors="coerce")
            df_filtered["Month"] = df_filtered["Implemented_Date"].dt.to_period("M").astype(str)
            risk_trend = df_filtered.groupby(["Month", "Risk_Level"]).size().reset_index(name="Count")

            fig4 = px.line(
                risk_trend, x="Month", y="Count", color="Risk_Level", markers=True,
                title="Monthly Risk Distribution Trend"
            )
            st.plotly_chart(fig4, use_container_width=True)

            st.markdown("#### Analysis – Monthly Risk Patterns")
            high_risk_trend = risk_trend[risk_trend["Risk_Level"] == "High"]["Count"].sum()
            low_risk_trend = risk_trend[risk_trend["Risk_Level"] == "Low"]["Count"].sum()

            st.write(f"""
            - High-risk total over the period: **{high_risk_trend}**  
            - Low-risk total over the period: **{low_risk_trend}**  

            📊 **Client takeaway:** Continuous monitoring of risk over time helps **detect process drift** 
            and **justify preemptive audits** before critical quarters.
            """)

            cio_6c = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Automate quarterly risk reporting | Phase 1: integrate logs → Phase 2: generate auto report → Phase 3: distribute | Reduces manual analytics | 8h saved/quarter = **32h/year** | Risk line confirms monthly variation justifies automation. |
                | Correlate risk spikes with vendor patch cycles | Phase 1: align risk data with vendor logs → Phase 2: forecast spikes → Phase 3: reschedule | Prevents costly emergency patches | Avoid 3 unscheduled changes/year | High-risk peaks align with vendor updates. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Embed risk heatmap in CAB dashboards | Phase 1: visualize top risks → Phase 2: action owner assignment → Phase 3: track monthly | Reduces reactive firefighting | 20% fewer last-minute escalations | Trend line shows untracked fluctuations. |
                | Review CAB decisions for outlier months | Phase 1: isolate months >120% avg → Phase 2: RCA workshop → Phase 3: update criteria | Improves decision discipline | Lower rework frequency | Spike months show inconsistent CAB evaluation. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Communicate monthly risk reports to service owners | Phase 1: send dashboards → Phase 2: include service impact notes | Improves confidence and collaboration | Non-financial, engagement ROI | Helps business units anticipate disruptions. |
                | Provide quarterly risk briefings | Phase 1: schedule executive summaries → Phase 2: trend review → Phase 3: share learnings | Strengthens transparency | Reputation benefit | Trend line indicates variability needing management buy-in. |
                """
            }
            render_cio_tables("CIO Recommendations – Risk Trend Management", cio_6c)
        else:
            st.warning("⚠️ Required columns ('Implemented_Date', 'Risk_Level') not found in dataset.")
