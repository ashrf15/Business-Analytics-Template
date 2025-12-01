import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Mesiniaga theme ---
BLUE_TONES = [
    "#004C99",  # deep brand navy
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]
px.defaults.template = "plotly_white"


# --- Utility formatters ---
def _fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return "0"


def _fmt_float(x, p=2):
    try:
        return f"{float(x):.{p}f}"
    except Exception:
        return "0.00"


# --- Main Function ---
def customer_satisfaction(df_filtered):

    # -------------------------------
    # Subtarget 3(a): Customer Feedback Scores
    # -------------------------------
    with st.expander("📌 Customer Feedback Scores"):
        if "feedback_score" in df_filtered.columns and "created_time" in df_filtered.columns:

            # Prep dates
            df_local = df_filtered.copy()
            df_local["created_time"] = pd.to_datetime(df_local["created_time"], errors="coerce")
            df_local = df_local.dropna(subset=["created_time"])
            df_local["created_date"] = df_local["created_time"].dt.date

            # Guard for no rows post-coercion
            if df_local.empty:
                st.info("Feedback score timestamps are not parseable. Data is not available, so there will be no analysis.")
            else:
                # ── Graph 1: Average Feedback per Month (Bar) ──
                monthly = (
                    df_local
                    .groupby(df_local["created_time"].dt.to_period("M"))["feedback_score"]
                    .mean()
                    .reset_index()
                    .rename(columns={"created_time": "month"})
                )
                monthly["month_str"] = monthly["month"].astype(str)

                if monthly.empty or monthly["feedback_score"].isna().all():
                    st.info("Monthly feedback aggregation produced no values. No analysis for this graph.")
                else:
                    fig1 = px.bar(
                        monthly,
                        x="month_str",
                        y="feedback_score",
                        title="Average Feedback Score per Month",
                        color_discrete_sequence=BLUE_TONES,
                        text="feedback_score",
                    )
                    fig1.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                    st.plotly_chart(fig1, use_container_width=True)

                    # Stats
                    peak_row = monthly.loc[monthly["feedback_score"].idxmax()]
                    trough_row = monthly.loc[monthly["feedback_score"].idxmin()]
                    mean_month = monthly["feedback_score"].mean()

                    # Analysis (required format)
                    st.markdown("#### Analysis – Monthly Averages")
                    st.write(
                        f"""What this graph is: A bar chart showing the **average feedback score** by calendar month.
X-axis: Calendar month.
Y-axis: Average feedback score in that month.
What it shows in your data:
Highest month: {peak_row['month_str']} with {_fmt_float(peak_row['feedback_score'])}.
Lowest month: {trough_row['month_str']} with {_fmt_float(trough_row['feedback_score'])}.
Average across months: {_fmt_float(mean_month)}.
Overall: Taller bars signal stronger sentiment months; shorter bars highlight periods requiring service review or targeted fixes.
How to read it operationally:
Seasonality: Repeating low months are candidates for pre-emptive resourcing and playbooks.
Change windows: Drops after major changes (releases, policy) suggest training/comms gaps.
Focus bands: Protect top months with the practices that created them; replicate to weaker months.
Why this matters: Stabilizing monthly sentiment prevents cascades into complaints, churn risk, and escalations while guiding investment to the right time windows."""
                    )

                    # CIO Table (≥3 recs, phased, benefits expanded, cost uses real values)
                    st.markdown("**CIO – Monthly Averages**")
                    st.markdown(
                        f"""| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Stabilize weak months with pre-emptive playbooks | **Phase 1 – Detect:** Flag months below baseline (≤ {_fmt_float(mean_month)}). <br><br>**Phase 2 – Prepare:** Staff surge + targeted runbooks one week before month start. **Phase 3 – Verify:** Monitor live scores and adjust within the month. | Reduces sentiment dips before they trigger complaints; smooths workload; better predictability of service quality. | **Hours saved** ≈ (complaints_avoided_month × handling_min/60) using trough month **{trough_row['month_str']}** baseline {_fmt_float(trough_row['feedback_score'])}. | Highest month **{peak_row['month_str']}={_fmt_float(peak_row['feedback_score'])}**, lowest **{trough_row['month_str']}={_fmt_float(trough_row['feedback_score'])}**, average {_fmt_float(mean_month)}. |
| Replicate best-practice from peak month | **Phase 1 – Mine:** Identify staffing, SLAs, and fixes used in **{peak_row['month_str']}**. <br><br>**Phase 2 – Standardize:** Document and roll to next two months. **Phase 3 – Guard:** KPI checks to sustain gains. | Lifts low months toward peak performance; reduces variance; builds repeatable operating cadence. | **Value (score uplift)** ≈ (peak − trough) = {_fmt_float(peak_row['feedback_score'] - trough_row['feedback_score'])}. Convert to **tickets avoided** by mapping score uplift to complaint rate. | Peak **{peak_row['month_str']}={_fmt_float(peak_row['feedback_score'])}** demonstrates achievable sentiment ceiling. |
| Month-ahead comms & training bursts | **Phase 1 – Content:** Short guides for top 3 pain points of low month. <br><br>**Phase 2 – Delivery:** Email/portal + in-app nudges prior to low month. **Phase 3 – Measure:** Track score change and contact rate. | Cuts “how-to” tickets; improves first-contact resolution; creates perception of proactive support. | **Tickets deflected** ≈ (pre-month views × CTR × deflection_rate). Map to trough month **{trough_row['month_str']}**. | Trough gap to average ( {_fmt_float(mean_month - trough_row['feedback_score'])} ) justifies pre-emptive enablement. |"""
                    )

                # ── Graph 2: Daily Trend (Line) ──
                daily = (
                    df_local.groupby("created_date")["feedback_score"]
                    .mean()
                    .reset_index()
                    .rename(columns={"feedback_score": "avg_score"})
                )
                if daily.empty or daily["avg_score"].isna().all():
                    st.info("Daily feedback trend produced no values. No analysis for this graph.")
                else:
                    fig2 = px.line(
                        daily,
                        x="created_date",
                        y="avg_score",
                        title="Feedback Score Trend Over Time (Daily Avg)",
                        color_discrete_sequence=BLUE_TONES,
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # Stats
                    peak_d = daily.loc[daily["avg_score"].idxmax()]
                    trough_d = daily.loc[daily["avg_score"].idxmin()]
                    avg_daily = daily["avg_score"].mean()
                    latest_row = daily.iloc[-1]

                    st.markdown("#### Analysis – Daily Trend")
                    st.write(
                        f"""What this graph is: A line chart showing the **daily average feedback score** across the period.
X-axis: Calendar date.
Y-axis: Daily average feedback score.
What it shows in your data:
Highest day: {peak_d['created_date']} with {_fmt_float(peak_d['avg_score'])}.
Lowest day: {trough_d['created_date']} with {_fmt_float(trough_d['avg_score'])}.
Average daily score: {_fmt_float(avg_daily)}; Latest day: {latest_row['created_date']} = {_fmt_float(latest_row['avg_score'])}.
Overall: Sustained dips signal service incidents or policy friction; sustained rises indicate process maturity or successful releases.
How to read it operationally:
Spike forensics: Investigate sharp drops to assign corrective actions fast.
Smoothing: If volatility is high, implement guardrails (change windows, checklists).
Reinforcement: When scores rise after changes, lock-in the practices behind those gains.
Why this matters: Faster detection and response to sentiment drops prevents compounding complaints and protects SLA/retention."""
                    )

                    # CIO table
                    st.markdown("**CIO – Daily Trend**")
                    st.markdown(
                        f"""| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Daily sentiment watch with auto-alarms | **Phase 1 – Thresholds:** Alert when daily avg < {_fmt_float(avg_daily)} − 1σ. <br><br>**Phase 2 – Response:** Duty lead investigates within same day. **Phase 3 – Review:** Add fix to runbook if repeat. | Earlier detection, fewer downstream complaints, quicker stabilization after incidents. | **Complaints avoided (h)** ≈ alerts_triggered × (avg_handling_min/60). Size around low day **{trough_d['created_date']}={_fmt_float(trough_d['avg_score'])}** vs average {_fmt_float(avg_daily)}. | Peak **{peak_d['created_date']}={_fmt_float(peak_d['avg_score'])}** vs trough **{trough_d['created_date']}={_fmt_float(trough_d['avg_score'])}** shows actionable range. |
| Change window guardrails | **Phase 1 – Gate:** Major changes only on stable-day windows. <br><br>**Phase 2 – Checklists:** Pre/post checks tied to sentiment. **Phase 3 – Backout:** Quick rollback criteria. | Reduces severity/duration of sentiment dips; protects daily experience during high-risk periods. | **Hours saved** ≈ (dip_days_reduced × avg_contacts/day × handling_min/60). | Volatility around the line indicates exposure to change-induced dips. |
| Positive-deviance replication | **Phase 1 – Identify:** Practices on the best days. <br><br>**Phase 2 – Standardize:** Convert to SOPs. **Phase 3 – Train:** Circulate to all teams. | Lifts average performance by replicating successes; reduces variation across shifts/teams. | **Score uplift** ≈ (target_uplift_per_day) summed across days < {_fmt_float(avg_daily)}. | Best day **{peak_d['created_date']}** is the reference blueprint for replication. |"""
                    )

                # ── Graph 3: Distribution (Box) ──
                if df_local["feedback_score"].dropna().empty:
                    st.info("Feedback score distribution has no data. No analysis for this graph.")
                else:
                    fig3 = px.box(
                        df_local,
                        y="feedback_score",
                        title="Feedback Score Distribution & Variability",
                        color_discrete_sequence=BLUE_TONES,
                        points="outliers",
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                    # Stats for distribution
                    s = df_local["feedback_score"].dropna()
                    med = float(np.median(s))
                    p10 = float(np.percentile(s, 10))
                    p90 = float(np.percentile(s, 90))
                    s_min, s_max = float(np.min(s)), float(np.max(s))
                    iqr = float(np.percentile(s, 75) - np.percentile(s, 25))

                    st.markdown("#### Analysis – Distribution")
                    st.write(
                        f"""What this graph is: A box plot showing the **distribution and variability** of feedback scores.
X-axis: (single series).
Y-axis: Feedback score values with quartiles and outliers.
What it shows in your data:
Median: {_fmt_float(med)}; P10: {_fmt_float(p10)}; P90: {_fmt_float(p90)}; IQR: {_fmt_float(iqr)}.
Extremes: Min {_fmt_float(s_min)} to Max {_fmt_float(s_max)}.
Overall: A wide IQR and distant outliers indicate inconsistency; a tight box indicates stable delivery.
How to read it operationally:
Tail analysis: Investigate drivers of low outliers to prevent repeat dips.
Standardization: Reduce spread by standard operating procedures and checklists.
Expectation setting: If variability cannot be fully removed, communicate realistic ETAs/features to reduce dissatisfaction.
Why this matters: Variability drives unpredictability; compressing spread protects perceived reliability and CSAT."""
                    )

                    # CIO table
                    st.markdown("**CIO – Distribution & Variability**")
                    st.markdown(
                        f"""| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Standardize top contact drivers | **Phase 1 – Identify:** Categories behind P10 tail ({_fmt_float(p10)}). <br><br>**Phase 2 – SOPs:** Step-by-step fixes and comms. **Phase 3 – Audit:** Weekly review of tail recurrence. | Compresses low tail; reduces repeat complaints; raises median toward a stable band. | **Score uplift** ≈ (median_target − current_median) where current_median = {_fmt_float(med)}. Map uplift to **tickets avoided** using historical elasticity. | Wide spread (IQR {_fmt_float(iqr)}) and low tail (P10 {_fmt_float(p10)}) show standardization headroom. |
| Outlier triage lane | **Phase 1 – Flag:** Real-time detection of scores below {_fmt_float(p10)}. <br><br>**Phase 2 – Route:** Senior handler lane. **Phase 3 – Learn:** Post-mortem to KB. | Faster recovery for worst experiences; fewer viral complaints; institutional learning from extremes. | **Hours saved** ≈ (outliers_per_period × extra_handling_min/60). | Presence of low outliers (min {_fmt_float(s_min)}) validates a specialized triage. |
| Consistency coaching for teams | **Phase 1 – Benchmark:** Team-level spread vs median. <br><br>**Phase 2 – Coach:** Micro-sessions for high-variance teams. **Phase 3 – Re-measure:** Spread reduction. | Reduces variance between shifts/teams; increases predictability of outcomes for customers. | **Variance reduction** ≈ (IQR_before − IQR_after); monetize via complaint rate drop. Baseline IQR = {_fmt_float(iqr)}. | Box width and outliers quantify current inconsistency to target. |"""
                    )
        else:
            st.warning("Feedback score data not available in uploaded dataset.")

    # -------------------------------
    # Subtarget 3(b): Net Promoter Score (NPS)
    # -------------------------------
    with st.expander("📌 Net Promoter Score (NPS)"):
        if "nps_category" in df_filtered.columns and "created_time" in df_filtered.columns:

            dfn = df_filtered.copy()
            dfn["created_time"] = pd.to_datetime(dfn["created_time"], errors="coerce")
            dfn = dfn.dropna(subset=["created_time"])
            dfn["created_date"] = dfn["created_time"].dt.date
            dfn["nps_category"] = dfn["nps_category"].astype(str)

            if dfn.empty:
                st.info("NPS timestamps are not parseable. Data is not available, so there will be no analysis.")
            else:
                # ── Graph 1: Category Distribution (Bar) ──
                nps_counts = dfn["nps_category"].value_counts().reset_index()
                nps_counts.columns = ["Category", "Count"]

                if nps_counts.empty:
                    st.info("NPS distribution has no values. No analysis for this graph.")
                else:
                    fig1 = px.bar(
                        nps_counts,
                        x="Category",
                        y="Count",
                        color="Category",
                        title="NPS Distribution",
                        color_discrete_sequence=BLUE_TONES,
                        text="Count",
                    )
                    fig1.update_traces(textposition="outside")
                    st.plotly_chart(fig1, use_container_width=True)

                    promoters = int((dfn["nps_category"].str.lower() == "promoter").sum())
                    detractors = int((dfn["nps_category"].str.lower() == "detractor").sum())
                    passives = int((dfn["nps_category"].str.lower() == "passive").sum())
                    total = promoters + detractors + passives
                    nps_score = ((promoters - detractors) / total * 100) if total > 0 else None
                    top_cat = nps_counts.iloc[0]["Category"]
                    top_val = int(nps_counts.iloc[0]["Count"])

                    st.markdown("#### Analysis – NPS Category Distribution")
                    st.write(
                        f"""What this graph is: A bar chart showing **counts of NPS categories** (Promoter, Passive, Detractor).
X-axis: NPS category.
Y-axis: Number of responses.
What it shows in your data:
Promoters: {_fmt_int(promoters)}; Passives: {_fmt_int(passives)}; Detractors: {_fmt_int(detractors)}; Total: {_fmt_int(total)}.
Top category: {top_cat} with {_fmt_int(top_val)}.
Computed NPS: {(_fmt_float(nps_score,1) if nps_score is not None else '—')}.
Overall: A healthy mix skews to Promoters; a large Detractor bar means urgent service issues.
How to read it operationally:
Close the loop: Call back Detractors within 24–48 hours with fixes.
Activate fans: Invite Promoters to testimonials or early programs.
Shift the middle: Convert Passives via targeted improvements and communication.
Why this matters: NPS correlates with growth and retention; moving responses from Detractor → Passive → Promoter compounds ROI."""
                    )

                    st.markdown("**CIO – NPS Distribution**")
                    st.markdown(
                        f"""| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Detractor callback program | **Phase 1 – Identify:** Daily list of Detractors ({_fmt_int(detractors)}). <br><br>**Phase 2 – Response:** Contact within 48h with resolution path. **Phase 3 – Verify:** Confirm fix and re-survey. | Converts negative experiences; prevents churn; reduces complaint volume. | **Retention value** ≈ detractors_saved × avg_contract_value; baseline detractors = {_fmt_int(detractors)}. | Detractor bar size {_fmt_int(detractors)} signals immediate outreach pool. |
| Passive conversion offers | **Phase 1 – Target:** Passives ({_fmt_int(passives)}) with small friction. <br><br>**Phase 2 – Offer:** Quick wins (guides/features). **Phase 3 – Measure:** Re-contact NPS after 30 days. | Moves fence-sitters to Promoters; low cost with measurable uplift; improves word-of-mouth. | **Uplift (pp)** ≈ (converted_passives/total) × 100; total = {_fmt_int(total)}. | Passive bar {_fmt_int(passives)} shows mid-tier opportunity size. |
| Promoter advocacy program | **Phase 1 – Invite:** Promoters ({_fmt_int(promoters)}). <br><br>**Phase 2 – Enable:** Referral kits/case studies. **Phase 3 – Reward:** Recognition/early access. | Amplifies positive reach; builds brand trust; low incremental cost. | **Value** ≈ referrals × conversion_rate × LTV, seeded by {_fmt_int(promoters)} promoters. | Promoter bar {_fmt_int(promoters)} = the engine for advocacy. |"""
                    )

                # ── Graph 2: NPS Trend by Category (Line) ──
                nps_trend = dfn.groupby(["created_date", "nps_category"]).size().reset_index(name="count")
                if nps_trend.empty:
                    st.info("NPS trend produced no values. No analysis for this graph.")
                else:
                    fig2 = px.line(
                        nps_trend,
                        x="created_date",
                        y="count",
                        color="nps_category",
                        title="NPS Trend Over Time",
                        color_discrete_sequence=BLUE_TONES,
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # Stats for trend
                    peak_idx = nps_trend["count"].idxmax()
                    peak_row = nps_trend.loc[peak_idx]
                    avg_per_day = nps_trend.groupby("nps_category")["count"].mean().to_dict()
                    latest_by_cat = (
                        nps_trend.sort_values("created_date").groupby("nps_category").tail(1)[["nps_category", "count"]]
                    )
                    latest_pairs = ", ".join([f"{r['nps_category']}={_fmt_int(r['count'])}" for _, r in latest_by_cat.iterrows()])

                    st.markdown("#### Analysis – NPS Trend")
                    st.write(
                        f"""What this graph is: A multi-line chart showing **daily counts** for each NPS category.
X-axis: Calendar date.
Y-axis: Daily response counts per category.
What it shows in your data:
Peak day: {peak_row['created_date']} – {peak_row['nps_category']} with {_fmt_int(peak_row['count'])}.
Average per day (by category): {', '.join([f"{k}={_fmt_float(v)}" for k,v in avg_per_day.items()])}.
Latest day by category: {latest_pairs}.
Overall: Rising Detractors day-over-day indicates active service issues; rising Promoters shows improving satisfaction or successful initiatives.
How to read it operationally:
Lead indicators: Treat rising Detractor line as an early alarm for service health.
Capacity: If Promoter counts fall when volume rises, check wait times or handling capacity.
Campaigns: Track whether targeted fixes visibly shift lines within a week.
Why this matters: By seeing category lines move in near-real-time, you can act before monthly scores deteriorate."""
                    )

                    st.markdown("**CIO – NPS Trend**")
                    st.markdown(
                        f"""| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Real-time detractor surge response | **Phase 1 – Thresholds:** Alert if Detractors/day > rolling 7-day mean. <br><br>**Phase 2 – Swarm:** Assign senior handler pool. **Phase 3 – Repair loop:** KB/runbook update within 72h. | Contains spikes before they turn systemic; reduces complaint inflow; protects weekly NPS. | **Complaints avoided (h)** ≈ (surge_days × avg_contacts × handling_min/60). Baseline from peak **{peak_row['created_date']} / {peak_row['nps_category']}={_fmt_int(peak_row['count'])}**. | Peak line point shows real surge scale to plan against. |
| Promoter momentum tracker | **Phase 1 – Monitor:** Promoter/day trend. <br><br>**Phase 2 – Trigger:** Advocacy asks when trend rising. **Phase 3 – Sustain:** Recognize contributors. | Converts goodwill into advocacy and referrals; low friction growth lever. | **Value** ≈ (advocacy_conversions × LTV) seeded by rising Promoter average. | Average/day for Promoters is embedded in the trend table above. |
| Volume-adjusted staffing | **Phase 1 – Forecast:** Line-based daily volume. <br><br>**Phase 2 – Schedule:** Shift overlaps on anticipated busy days. **Phase 3 – Review:** SLA vs NPS trend post-adjustment. | Holds service quality under load; prevents NPS drops during spikes; improves predictability. | **OT avoided (h)** ≈ (breach_hours_prevented) derived from days where total NPS responses spike. | Trend lines reveal demand variability to align staffing. |"""
                    )

                # ── Graph 3: NPS Breakdown by Issue Type (Stacked Bar, optional) ──
                if "issue_type" in dfn.columns:
                    nps_breakdown = dfn.groupby(["issue_type", "nps_category"]).size().reset_index(name="count")
                    if nps_breakdown.empty:
                        st.info("NPS breakdown by issue type has no values. No analysis for this graph.")
                    else:
                        fig3 = px.bar(
                            nps_breakdown,
                            x="issue_type",
                            y="count",
                            color="nps_category",
                            barmode="stack",
                            title="NPS Breakdown by Issue Type",
                            color_discrete_sequence=BLUE_TONES,
                        )
                        st.plotly_chart(fig3, use_container_width=True)

                        # Stats: top issue by Detractors, by Promoters
                        det_tbl = nps_breakdown[nps_breakdown["nps_category"].str.lower() == "detractor"]
                        pro_tbl = nps_breakdown[nps_breakdown["nps_category"].str.lower() == "promoter"]
                        top_det = det_tbl.loc[det_tbl["count"].idxmax()] if not det_tbl.empty else None
                        top_pro = pro_tbl.loc[pro_tbl["count"].idxmax()] if not pro_tbl.empty else None
                        total_break = int(nps_breakdown["count"].sum())

                        st.markdown("#### Analysis – Breakdown by Issue Type")
                        det_line = (
                            f"Top detractor issue: {top_det['issue_type']} with {_fmt_int(top_det['count'])}."
                            if top_det is not None
                            else "No detractor issues found."
                        )
                        pro_line = (
                            f"Top promoter issue: {top_pro['issue_type']} with {_fmt_int(top_pro['count'])}."
                            if top_pro is not None
                            else "No promoter issues found."
                        )
                        st.write(
                            f"""What this graph is: A stacked bar showing **NPS category counts by issue type**.
X-axis: Issue type.
Y-axis: Counts, stacked by NPS category.
What it shows in your data:
{det_line}
{pro_line}
Total responses in breakdown: {_fmt_int(total_break)}.
Overall: Issue types with large Detractor stacks require root-cause fixes; those with large Promoter stacks reflect strengths to preserve.
How to read it operationally:
Targeted fixes: Prioritize top Detractor issues for RCA and SOP updates.
Preserve wins: Document what worked in top Promoter issues and replicate.
Portfolio view: Balance effort by business impact and volume per issue type.
Why this matters: Focusing on the right issue types moves NPS efficiently by addressing concentrated pain points."""
                        )

                        st.markdown("**CIO – Breakdown by Issue Type**")
                        st.markdown(
                            f"""| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| RCA on top detractor issue types | **Phase 1 – Select:** Highest detractor issue ({(top_det['issue_type'] if top_det is not None else '—')}). <br><br>**Phase 2 – Fix:** Update runbooks and validations. **Phase 3 – Recheck:** Measure detractor drop after release. | Reduces repeat negative experiences fastest; measurable NPS lift where impact is concentrated. | **Detractors reduced** ≈ before–after delta for '{(top_det['issue_type'] if top_det is not None else '—')}'. Baseline={_fmt_int(top_det['count']) if top_det is not None else '0'}. | Stack height for Detractors on the top issue evidences immediate opportunity. |
| Replicate best practice from top promoter issue | **Phase 1 – Extract:** Reasons behind high promoter counts ({(top_pro['issue_type'] if top_pro is not None else '—')}). <br><br>**Phase 2 – SOP:** Bake into standard flow. **Phase 3 – Train:** Roll to other issue types. | Spreads high-satisfaction patterns; lifts overall sentiment with low risk. | **Promoter lift** ≈ (issues_migrated × expected_promoter_gain per issue). Baseline promoter count={_fmt_int(top_pro['count']) if top_pro is not None else '0'}. | Promoter stack height signals repeatable strengths. |
| Sunsetting low-value variants | **Phase 1 – Identify:** Issue subtypes with persistent detractors and low volume. <br><br>**Phase 2 – Consolidate:** Remove or route differently. **Phase 3 – Monitor:** Verify detractor reduction. | Simplifies portfolio; reduces confusion and misroutes; concentrates effort on high-impact areas. | **Time saved (h)** ≈ (misroutes_avoided × handling_min/60) from identified low-value subtypes. | Stacks with small total but high Detractor share are prime candidates for consolidation. |"""
                        )
                else:
                    st.info("Column 'issue_type' not available; skipping NPS breakdown by issue type.")
        else:
            st.warning("NPS data not available in uploaded dataset.")
