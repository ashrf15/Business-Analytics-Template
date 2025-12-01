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


# 🔹 Module 7: Change Window Utilization & Compliance
def window_utilization(df_filtered):

    
    st.markdown("""
    This section evaluates how well change executions **adhere to planned maintenance windows**, 
    where breaches occur, and which time periods or categories are most at risk.  
    It focuses on **window compliance rate**, **trend over time**, and **execution timing** patterns.
    """)

    # Normalize common columns if present
    # Expected optional columns: Window_Compliance (Yes/No/True/False), Window_Type, Implemented_Date, Start_Time, End_Time, Duration_Hours, Breach_Reason, Category
    if "Window_Compliance" in df_filtered.columns:
        df_filtered["Window_Compliance_Flag"] = (
            df_filtered["Window_Compliance"].astype(str).str.strip().str.lower().map({"yes": True, "true": True, "no": False, "false": False})
        )

    if "Implemented_Date" in df_filtered.columns:
        df_filtered["Implemented_Date"] = pd.to_datetime(df_filtered["Implemented_Date"], errors="coerce")
        df_filtered["Month"] = df_filtered["Implemented_Date"].dt.to_period("M").astype(str)
        df_filtered["Hour"] = df_filtered["Implemented_Date"].dt.hour

    # ---------------------- Subtarget 7a ----------------------
    with st.expander("📌 Overall Window Compliance & Split by Window Type"):
        have_basic = "Window_Compliance_Flag" in df_filtered.columns
        have_type = "Window_Type" in df_filtered.columns

        if have_basic:
            # Pie: overall compliance
            comp_counts = df_filtered["Window_Compliance_Flag"].value_counts(dropna=False).reset_index()
            comp_counts.columns = ["Compliant", "Count"]
            fig1 = px.pie(
                comp_counts, names="Compliant", values="Count",
                title="Overall Window Compliance (Compliant vs Non-Compliant)",
                color_discrete_sequence=["#0b5394", "#e06666"]
            )
            st.plotly_chart(fig1, use_container_width=True)

            total = comp_counts["Count"].sum()
            compliant = comp_counts.loc[comp_counts["Compliant"] == True, "Count"].sum()
            noncompliant = total - compliant
            comp_rate = (compliant / total * 100) if total > 0 else 0

            st.markdown("#### Analysis – Compliance Overview")
            st.write(f"""
            - Total executed changes analyzed: **{total}**  
            - Compliant (within window): **{compliant}**  
            - Non-compliant (outside window): **{noncompliant}**  
            - Overall compliance rate: **{comp_rate:.1f}%**  

            📊 **Client takeaway:** Maintaining **≥90% window compliance** is common best practice. 
            Breaches increase risk of user disruption, unplanned overtime, and incident follow-ups.
            """)

            # Bar: compliance by window type (if present)
            if have_type:
                df_filtered["Window_Type"] = df_filtered["Window_Type"].astype(str).str.strip().str.title()
                comp_by_type = (
                    df_filtered.groupby("Window_Type")["Window_Compliance_Flag"]
                    .mean().reset_index().rename(columns={"Window_Compliance_Flag": "Compliance_Rate"})
                )
                comp_by_type["Compliance_Rate"] *= 100

                fig2 = px.bar(
                    comp_by_type, x="Window_Type", y="Compliance_Rate",
                    title="Compliance Rate by Window Type (%)",
                    color="Compliance_Rate", color_continuous_scale="Greens"
                )
                st.plotly_chart(fig2, use_container_width=True)

                if not comp_by_type.empty:
                    best = comp_by_type.loc[comp_by_type["Compliance_Rate"].idxmax()]
                    worst = comp_by_type.loc[comp_by_type["Compliance_Rate"].idxmin()]
                    avg = comp_by_type["Compliance_Rate"].mean()

                    st.markdown("#### Analysis – Window Type Compliance Split")
                    st.write(f"""
                    - Highest compliance: **{best['Window_Type']}** at **{best['Compliance_Rate']:.1f}%**  
                    - Lowest compliance: **{worst['Window_Type']}** at **{worst['Compliance_Rate']:.1f}%**  
                    - Average compliance across all window types: **{avg:.1f}%**

                    📊 **Client takeaway:** If **Business Hours** or **Ad-Hoc** types underperform, stricter scheduling and 
                    pre-approvals are needed to avoid peak-hour disruption.
                    """)

            # CIO Table for 7a
            cio_7a = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Numeric Example) | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|----------------------------------------------|--------------------------------|
                | Enforce low-cost “standard change” windows | Phase 1: define standard windows → Phase 2: auto-route standard changes → Phase 3: monthly audit | Reduces overtime & emergency handling | If 30 out-of-window changes avoid 1h overtime at RM80/h → **RM2,400 saved/period** | Pie shows non-compliant share; type bar highlights weak window types. |
                | Batch similar changes into shared windows | Phase 1: classify by category → Phase 2: batch scheduler → Phase 3: measure compliance uplift | Cuts repeated setup & validation | 10 similar changes × 0.4h saved = **4h per batch** | Lower-performing window types benefit from batching. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Introduce window-booking with conflict checks | Phase 1: calendar integration → Phase 2: prevent overlaps → Phase 3: escalate conflicts | Fewer last-minute reschedules | 25% fewer clashes → faster throughput | Type split shows inconsistent adherence; booking mitigates. |
                | Auto-deny requests lacking assigned window | Phase 1: form validation → Phase 2: rejection with guidance → Phase 3: monitor exceptions | Improves discipline & planning | Indirect; fewer escalations | Non-compliant fraction indicates weak gating. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Publish window policy & expected behavior | Phase 1: policy page → Phase 2: workflow prompts → Phase 3: periodic refreshers | Reduces confusion & surprise outages | Low cost; fewer complaints | Pie/bar evidence suggests users experience out-of-window changes. |
                | Stakeholder sign-off for exceptions | Phase 1: require business approval → Phase 2: capture reason → Phase 3: report monthly | Builds trust in exceptions | N/A – governance benefit | Non-compliant segment implies unvetted exceptions. |
                """
            }
            render_cio_tables("CIO Recommendations – Compliance & Window Types", cio_7a)
        else:
            st.warning("⚠️ 'Window_Compliance' column not found (expected Yes/No or True/False).")


    # ---------------------- Subtarget 7b ----------------------
    with st.expander("📌 Compliance Trend Over Time & Breach Reasons"):
        have_trend = {"Window_Compliance_Flag", "Implemented_Date"}.issubset(df_filtered.columns)
        have_reason = "Breach_Reason" in df_filtered.columns

        if have_trend:
            monthly_comp = (
                df_filtered.groupby("Month")["Window_Compliance_Flag"].mean()
                .reset_index().rename(columns={"Window_Compliance_Flag": "Compliance_Rate"})
            )
            monthly_comp["Compliance_Rate"] *= 100

            fig3 = px.line(
                monthly_comp, x="Month", y="Compliance_Rate", markers=True,
                title="Monthly Window Compliance Trend (%)"
            )
            st.plotly_chart(fig3, use_container_width=True)

            if not monthly_comp.empty:
                best_m = monthly_comp.loc[monthly_comp["Compliance_Rate"].idxmax()]
                worst_m = monthly_comp.loc[monthly_comp["Compliance_Rate"].idxmin()]
                avg_m = monthly_comp["Compliance_Rate"].mean()

                st.markdown("#### Analysis – Compliance Trend")
                st.write(f"""
                - Best month: **{best_m['Month']}** at **{best_m['Compliance_Rate']:.1f}%**  
                - Worst month: **{worst_m['Month']}** at **{worst_m['Compliance_Rate']:.1f}%**  
                - Average monthly compliance: **{avg_m:.1f}%**  

                📊 **Client takeaway:** Dips often correlate with **major release cycles** or **staff constraints**. 
                Proactive booking and freeze periods stabilize compliance.
                """)

        if have_reason:
            df_filtered["Breach_Reason"] = df_filtered["Breach_Reason"].astype(str).str.strip().str.title()
            reason_counts = df_filtered.loc[df_filtered.get("Window_Compliance_Flag") == False, "Breach_Reason"] \
                                        .value_counts().reset_index()
            if not reason_counts.empty:
                reason_counts.columns = ["Breach_Reason", "Count"]
                fig4 = px.bar(
                    reason_counts, x="Breach_Reason", y="Count", color="Count",
                    color_continuous_scale="Reds", title="Top Reasons for Window Breach"
                )
                st.plotly_chart(fig4, use_container_width=True)

                st.markdown("#### Analysis – Breach Drivers")
                top_reason = reason_counts.iloc[0]["Breach_Reason"]
                top_count = reason_counts.iloc[0]["Count"]
                st.write(f"""
                - Most frequent breach reason: **{top_reason}** with **{top_count}** occurrences.  
                - Concentration of a few breach drivers suggests **process gaps** (e.g., late approvals, vendor dependencies).

                📊 **Client takeaway:** Target the top-2 reasons with **clear SOPs, templates, and escalation paths** to see the fastest improvement.
                """)

        if not have_trend and not have_reason:
            st.info("No trend or breach-reason columns found (expected 'Implemented_Date' and/or 'Breach_Reason').")

        # CIO Table for 7b
        cio_7b = {
            "cost": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Numeric Example) | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|----------------------------------------------|--------------------------------|
            | Freeze periods around critical months | Phase 1: identify non-compliance dips → Phase 2: schedule freeze → Phase 3: monitor | Avoids costly out-of-window escalations | If 8 breaches avoided × 1h overtime × RM80 = **RM640 saved/month** | Trend line dips show months with higher breaches. |
            | Pre-approve recurring changes | Phase 1: whitelist templates → Phase 2: standing approvals → Phase 3: quarterly review | Cuts admin overhead | 30 templates × 0.25h = **7.5h saved/quarter** | Breach reasons indicate “late approvals” root cause. |
            """,
            "performance": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | Escalate top-2 breach drivers with owners | Phase 1: assign owner per reason → Phase 2: weekly action → Phase 3: publish outcomes | Faster resolution of systemic issues | 40% fewer breaches for top-2 reasons | Reasons bar shows concentrated drivers. |
            | Auto-suggest compliant windows on request form | Phase 1: calendar lookup → Phase 2: rules for service criticality → Phase 3: validation | Higher first-time compliance | Reduced rework; lower rescheduling | Trend + reasons suggest planning guidance gaps. |
            """,
            "satisfaction": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | Notify stakeholders when non-compliance is requested | Phase 1: warn on form → Phase 2: capture business sign-off → Phase 3: report | Transparency for exceptions | Lower complaint volume | Trend dips and reason “business urgency” imply communication gaps. |
            | Post-mortems for repeated reasons | Phase 1: short RCAs → Phase 2: fix playbooks → Phase 3: measure drop | Builds trust & predictability | Minimal effort; high trust ROI | Repeated bars in top reasons justify short RCAs. |
            """
        }
        render_cio_tables("CIO Recommendations – Compliance Trend & Breach Drivers", cio_7b)


    # ---------------------- Subtarget 7c ----------------------
    with st.expander("📌 Execution Timing Patterns (Hour-of-Day & Duration)"):
        # Hour analysis
        hour_ready = {"Hour", "Window_Compliance_Flag"}.issubset(df_filtered.columns)
        duration_ready = "Duration_Hours" in df_filtered.columns

        if hour_ready:
            by_hour = df_filtered.groupby(["Hour", "Window_Compliance_Flag"]).size().reset_index(name="Count")
            fig5 = px.bar(
                by_hour, x="Hour", y="Count", color="Window_Compliance_Flag", barmode="group",
                title="Change Executions by Hour (Compliant vs Non-Compliant)"
            )
            st.plotly_chart(fig5, use_container_width=True)

            if not by_hour.empty:
                worst_hour_row = by_hour[by_hour["Window_Compliance_Flag"] == False].sort_values("Count", ascending=False).head(1)
                if not worst_hour_row.empty:
                    worst_hour = int(worst_hour_row.iloc[0]["Hour"])
                    worst_count = int(worst_hour_row.iloc[0]["Count"])
                else:
                    worst_hour, worst_count = None, 0

                st.markdown("#### Analysis – Hour-of-Day Risk")
                st.write(f"""
                - Non-compliance peaks around **{worst_hour if worst_hour is not None else 'N/A'}:00** with **{worst_count}** breaches.  
                - Overnight windows typically have higher compliance than **business-hour** changes.

                📊 **Client takeaway:** Scheduling guidance should **discourage high-risk hours** for non-urgent changes, 
                and force approvals for day-time exceptions.
                """)

        if duration_ready:
            df_filtered["Duration_Hours"] = pd.to_numeric(df_filtered["Duration_Hours"], errors="coerce")
            dur_df = df_filtered.dropna(subset=["Duration_Hours"])
            if not dur_df.empty:
                fig6 = px.histogram(
                    dur_df, x="Duration_Hours", nbins=20, color_discrete_sequence=["#1a73e8"],
                    title="Distribution of Change Execution Durations (Hours)"
                )
                st.plotly_chart(fig6, use_container_width=True)

                mean_d = dur_df["Duration_Hours"].mean()
                p90_d = dur_df["Duration_Hours"].quantile(0.90)

                st.markdown("#### Analysis – Duration Insights")
                st.write(f"""
                - Average execution duration: **{mean_d:.2f} hours**  
                - 90th percentile duration: **{p90_d:.2f} hours**  

                📊 **Client takeaway:** Long-duration changes correlate with higher risk of **window breaches** and **user impact**. 
                These should be split into smaller, staged deployments where possible.
                """)

        if not hour_ready and not duration_ready:
            st.info("No hour/duration fields found (expected 'Implemented_Date' for hour; 'Duration_Hours' for length).")

        # CIO Table for 7c
        cio_7c = {
            "cost": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Numeric Example) | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|----------------------------------------------|--------------------------------|
            | Split long changes into smaller tasks | Phase 1: identify >P90 duration → Phase 2: split plan → Phase 3: staged deploy | Fewer overruns → less overtime | If 6 long changes reduced by 1h @ RM80/h = **RM480 saved** | Duration histogram shows right-tail of long executions. |
            | Avoid high-risk hours for non-urgent changes | Phase 1: define allowed hours → Phase 2: form validation → Phase 3: audit exceptions | Less business-hour cost & disruption | 4 breaches avoided × 1h overtime × RM80 = **RM320** | Hour chart shows breach clustering by hour. |
            """,
            "performance": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | Auto-suggest best execution hours per service | Phase 1: build usage profiles → Phase 2: recommend low-traffic hours → Phase 3: A/B test | Improves first-time compliance | 20% fewer reschedules | Hour-of-day grouping reveals optimal hours. |
            | Pre-implementation duration estimate check | Phase 1: force duration ETA → Phase 2: validate against window length → Phase 3: flag risks | Fewer overruns & breaches | Reduced rework & delays | Duration right-tail indicates poor estimation. |
            """,
            "satisfaction": """
            | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | Notify business for day-time changes with impact | Phase 1: pop-up consent → Phase 2: stakeholder sign-offs → Phase 3: status updates | Reduces surprise & complaints | Indirect: lower incident queries | Hour chart shows day-time breach clusters; comms offsets impact. |
            | Publish upcoming window schedule & expected durations | Phase 1: monthly schedule page → Phase 2: per-change ETA → Phase 3: post-change summary | Better planning & trust | Low cost, high goodwill | Duration distribution supports setting realistic expectations. |
            """
        }
        render_cio_tables("CIO Recommendations – Execution Timing & Duration", cio_7c)
