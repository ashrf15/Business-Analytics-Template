import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────
# Helper to render CIO tables with 3 nested expanders
# ─────────────────────────────────────────────────────────────
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Priority normalization + fixed order (align to your values)
# ─────────────────────────────────────────────────────────────
PRIORITY_ORDER = ["P1", "P2", "P3", "P5", "Service Request"]

def normalize_priority(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()

    # Remove leading "Priority" text and normalize whitespace
    s = (s.str.replace(r"^priority\s*", "", case=False, regex=True)
           .str.replace(r"\s+", " ", regex=True))

    # Standardize P-levels
    s = s.str.upper()
    s = s.str.replace(r"^P0$", "P1", regex=True)  # optional up-map
    # NOTE: If you don't want to remap P4, comment out the next line
    s = s.str.replace(r"^P4$", "P3", regex=True)

    # Harmonize Service Request variants
    s = s.str.replace(r"^(SR|SERVICE\s*REQ(?:UEST)?)$", "Service Request", case=False, regex=True)

    # Only keep the target categories; others -> NaN (excluded downstream)
    s = s.where(s.isin(PRIORITY_ORDER))

    # Return as ordered categorical => stable, aligned plotting
    return pd.Categorical(s, categories=PRIORITY_ORDER, ordered=True)

# ─────────────────────────────────────────────────────────────
# Main SLA section
# ─────────────────────────────────────────────────────────────
def sla(df_filtered: pd.DataFrame):

    # -------------------------------
    # Subtarget 6(a): SLA Performance Metrics
    # -------------------------------
    with st.expander("📌 SLA Performance Metrics"):
        st.markdown("This section evaluates SLA adherence for **response** and **resolution** across different priorities and categories.")

        # Prep stats holders so they exist even if some charts are skipped
        avg_met_pct = 0.0
        best_week_date_str = "-"
        best_week_met_pct = 0.0
        worst_week_date_str = "-"
        worst_week_met_pct = 0.0
        overall_sla_pct = 0.0
        best_priority = "-"
        best_priority_pct = 0.0
        worst_priority = "-"
        worst_priority_pct = 0.0
        avg_priority_pct = 0.0

        # --- Graph 1: Stacked Bar Chart (Weekly SLA % met vs breached)
        if "created_time" in df_filtered.columns and "sla_met" in df_filtered.columns:
            work = df_filtered.copy()
            work["created_date"] = pd.to_datetime(work["created_time"], errors="coerce").dt.to_period("W").dt.start_time
            sla_weekly = work.groupby("created_date", dropna=True)["sla_met"].mean().reset_index()
            sla_weekly["breach"] = 1 - sla_weekly["sla_met"]

            if not sla_weekly.empty:
                avg_met_pct = float(sla_weekly["sla_met"].mean() * 100)
                best_week = sla_weekly.loc[sla_weekly["sla_met"].idxmax()]
                worst_week = sla_weekly.loc[sla_weekly["sla_met"].idxmin()]
                best_week_date_str = best_week["created_date"].date().isoformat()
                worst_week_date_str = worst_week["created_date"].date().isoformat()
                best_week_met_pct = float(best_week["sla_met"] * 100)
                worst_week_met_pct = float(worst_week["sla_met"] * 100)

            # Pretty legend labels + fixed colors
            plot_df = sla_weekly.rename(columns={"sla_met": "SLA Met", "breach": "Breached"})
            fig = px.bar(
                plot_df,
                x="created_date",
                y=["SLA Met", "Breached"],
                title="Weekly SLA Compliance Trend (Met vs Breached)",
                labels={"value": "Proportion", "created_date": "Week"},
                barmode="stack",
                color_discrete_map={"SLA Met": "#0469FF", "Breached": "#AAD0FF"}  # green / red
            )
            fig.update_yaxes(range=[0, 1], tickformat=".0%")
            fig.update_layout(legend_title_text="Status")
            st.plotly_chart(fig, use_container_width=True)

            st.write(f"""**What this graph is:** A weekly stacked bar showing **SLA met vs breached** proportions.  
- **X-axis:** Week start date.  
- **Y-axis:** Proportion of tickets (0–1), stacked as **met** then **breach**.

**What it shows in your data:**  
Average adherence across weeks is **{avg_met_pct:.2f}%**.  
Best week reached **{best_week_met_pct:.2f}%** (week starting **{best_week_date_str}**),  
while the worst week dropped to **{worst_week_met_pct:.2f}%** (week starting **{worst_week_date_str}**).

Overall, taller green segments indicate **strong SLA control**, while taller red segments flag **capacity/process strain**.

**How to read it operationally:**  
1) **Peaks:** Reinforce practices from high-adherence weeks (staffing, routing, runbooks).  
2) **Plateaus:** Standardize controls to hold performance above target.  
3) **Downswings:** Trigger corrective actions (swarming, escalation rules, auto-triage).  
4) **Mix:** Cross-check with intake volume to separate demand spikes from execution gaps.

**Why this matters:** SLA adherence protects **costs, contracts, and customer trust**. Weekly visibility shows where to intervene before penalties and dissatisfaction escalate.
""")
        else:
            st.write(f"""**What this graph is:** A weekly stacked bar showing **SLA met vs breached** proportions.  
- **X-axis:** Week start date.  
- **Y-axis:** Proportion of tickets (0–1), stacked as **met** then **breach**.

**What it shows in your data:**  
No weekly SLA rows are available in the current selection (average adherence **{avg_met_pct:.2f}%** over 0 weeks). This usually means there are **no tickets** in the chosen date range or all rows are **NA after filtering**.

**How to read it operationally:**  
1) **Peaks:** (Not applicable—no data).  
2) **Plateaus / Downswings:** Adjust date filters or ensure `sla_met` is present.  
3) **Mix:** Verify preprocessing for SLA flags.

**Why this matters:** Without valid weekly rows, we can’t assess contract health—review filters or data readiness.
""")

        # --- Graph 2: Gauge / KPI Widget for SLA Performance
        if "sla_met" in df_filtered.columns:
            overall_sla_pct = float(pd.to_numeric(df_filtered["sla_met"], errors="coerce").mean() * 100)

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall_sla_pct,
                title={"text": "Overall SLA Adherence (%)"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "green" if overall_sla_pct >= 80 else "red"}
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Analysis – Overall SLA KPI")
            st.write(f"""**What this graph is:** A KPI gauge showing **overall SLA adherence**.  
- **X-axis:** N/A (single KPI).  
- **Y-axis:** Percentage scale (0–100%).

**What it shows in your data:**  
Overall adherence is **{overall_sla_pct:.2f}%**.  
Response performance is healthier than resolution (response typically high, resolution materially lower), implying **fast acknowledgement** but **slow fix throughput**.

Overall, a high gauge value signals **predictable delivery**, while a low value signals **systemic breach risk**.

**How to read it operationally:**  
1) **Peaks:** Capture what worked (assignment rules, staffing windows) and codify it.  
2) **Plateaus:** Maintain controls; watch for leading indicators of drift.  
3) **Downswings:** Add surge capacity and tighten escalation triggers.  
4) **Mix:** Pair this KPI with intake vs closure charts to confirm capacity fit.

**Why this matters:** The KPI is the executive **contract health** signal. Sustained under-target adherence drives **penalties, rework cost, and churn**.
""")

        # --- Graph 3: SLA by Priority/Category (aligned to P1,P2,P3,P5,Service Request)
        if "priority" in df_filtered.columns and "sla_met" in df_filtered.columns:
            dfp = df_filtered.copy()
            dfp["priority_std"] = normalize_priority(dfp["priority"])

            # Aggregate mean SLA by fixed buckets; keep empty buckets for visibility
            priority_sla = (dfp.groupby("priority_std", observed=True)["sla_met"]
                              .mean()
                              .reindex(PRIORITY_ORDER)
                              .reset_index())

            # % labels; show "–" if no data in that bucket
            label_pct = priority_sla["sla_met"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "–")

            fig = px.bar(
                priority_sla,
                x="priority_std",
                y="sla_met",
                title="SLA Adherence by Priority",
                text=label_pct,
                labels={"priority_std": "Priority", "sla_met": "Adherence (0–1)"},
                category_orders={"priority_std": PRIORITY_ORDER},
            )
            fig.update_traces(textposition="outside")
            fig.update_yaxes(range=[0, 1], tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

            # Stats for narrative (skip NaNs robustly)
            if priority_sla["sla_met"].notna().any():
                _idxmax = priority_sla["sla_met"].idxmax()
                _idxmin = priority_sla["sla_met"].idxmin()
                best_priority = str(priority_sla.loc[_idxmax, "priority_std"])
                worst_priority = str(priority_sla.loc[_idxmin, "priority_std"])
                best_priority_pct = float(priority_sla.loc[_idxmax, "sla_met"] * 100)
                worst_priority_pct = float(priority_sla.loc[_idxmin, "sla_met"] * 100)
                avg_priority_pct = float(priority_sla["sla_met"].mean(skipna=True) * 100)
            else:
                best_priority = worst_priority = "-"
                best_priority_pct = worst_priority_pct = avg_priority_pct = 0.0

            st.markdown("### Analysis – SLA Adherence by Priority")
            st.write(f"""**What this graph is:** A bar chart comparing **average SLA adherence by priority**.  
- **X-axis:** Priority (fixed order: {", ".join(PRIORITY_ORDER)}).  
- **Y-axis:** Adherence proportion (0–1), labeled as a percentage.

**What it shows in your data:**  
Best priority bucket: **{best_priority}** at **{best_priority_pct:.1f}%**.  
Weakest bucket: **{worst_priority}** at **{worst_priority_pct:.1f}%**.  
Overall average across priorities: **{avg_priority_pct:.1f}%**.

Overall, taller bars = **more targets met**; shorter bars = **risk pockets** needing routing and capacity fixes.

**How to read it operationally:**  
1) **Peaks:** Replicate staffing/triage patterns from best-performing priority.  
2) **Plateaus:** Ensure consistent guardrails (WIP limits, escalation SLAs).  
3) **Downswings:** Add fast-lane rules and senior ownership for weak priorities.  
4) **Mix:** Compare with breach reasons to align fixes where impact is highest.

**Why this matters:** Priority adherence aligns service with **business impact**. Fixing weak buckets reduces **escalations, penalties, and dissatisfaction** where it hurts most.
""")

        # ---------------- CIO Tables for 6(a) ----------------
        cio_6a = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Tighten surge controls in worst week | **Phase 1 – Identify:** Use worst week **{worst_week_date_str}** at **{worst_week_met_pct:.2f}%** SLA.<br><br>**Phase 2 – Act:** add surge staffing, fast-lane routing, and auto-triage for that week pattern.<br><br>**Phase 3 – Verify:** compare next similar week against baseline. | - Cuts overtime by dealing with the surge in standard hours rather than paying premium rates.<br><br>- Reduces penalties by preventing a repeat of breach patterns seen in the worst week window.<br><br>- Avoids backlog carryover that would otherwise inflate costs in the following weeks.<br><br>- Stabilizes daily operations so supervisors spend less time firefighting and more time coordinating planned work.<br><br>- Makes outcomes more predictable which improves budgeting accuracy for the month.<br><br>- Provides a tested playbook that can be reused whenever the same risk indicators appear. | **Penalties avoided/week** = (breach_rate_baseline − breach_rate_after) × weekly_tickets × penalty_per_breach. Here breach_rate_baseline = **{100 - worst_week_met_pct:.2f}%** from the chart. | Weekly stacked bars show the **lowest adherence** in week starting **{worst_week_date_str}**, confirming where costs spike. |
| Standardize best-week playbook | **Phase 1 – Extract:** from best week **{best_week_date_str}** at **{best_week_met_pct:.2f}%** SLA, document staffing windows, routing rules, and runbooks.<br><br>**Phase 2 – Rollout:** apply to all weeks near average adherence **{avg_met_pct:.2f}%**.<br><br>**Phase 3 – Audit:** track cost deltas. | - Replicates a proven low-cost configuration that already delivered high compliance.<br><br>- Reduces variance across weeks which smooths spend and capacity planning.<br><br>- Lowers rework because best-practice steps reduce handoffs and misrouting.<br><br>- Accelerates new team members’ ramp-up as they follow a clearly defined operating model.<br><br>- Decreases escalation volume by keeping performance consistently close to the best-week baseline.<br><br>- Improves forecasting confidence for leadership because weekly results become more stable. | **Hours saved/week** = (avg_breach_hours − best_week_breach_hours) × weeks_applied. Use best-week breach rate **{100 - best_week_met_pct:.2f}%** as the achievable benchmark. | Stacked chart identifies a **repeatable high-compliance pattern** in **{best_week_date_str}** to standardize. |
| Priority-mix rebalancing | **Phase 1 – Target:** lift weak priority **{worst_priority}** at **{worst_priority_pct:.1f}%** toward average **{avg_priority_pct:.1f}%**.<br><br>**Phase 2 – Rebalance:** adjust queues/skills to shift time from strong buckets like **{best_priority}** (**{best_priority_pct:.1f}%**).<br><br>**Phase 3 – Measure:** weekly cost variance. | - Reduces penalties concentrated in the weak priority by shortening cycle time where impact is highest.<br><br>- Makes staffing more efficient by aligning senior attention to the highest impact work.<br><br>- Decreases rework and churn because misprioritized tickets stop aging into breaches.<br><br>- Increases predictability of contract outcomes across the full mix of priorities.<br><br>- Supports better customer perception for urgent items that drive satisfaction and renewals.<br><br>- Builds a repeatable mechanism for tuning the mix as demand patterns change. | **Cost delta/week** = (overtime_hours_reduced × hourly_rate) driven by narrowing the gap: **{avg_priority_pct:.1f}% − {worst_priority_pct:.1f}%**. | Priority chart shows **weakest bucket {worst_priority}** vs **best {best_priority}**, grounding the expected lift. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Weekly SLA control limits | **Phase 1 – Set limits:** minimum SLA target around **{avg_met_pct:.2f}%**; alert when a week trends toward **{worst_week_met_pct:.2f}%**.<br><br>**Phase 2 – Actions:** enable swarms/escalations; freeze non-urgent changes.<br><br>**Phase 3 – Review:** trend back to mean. | - Narrows the gap between best and worst weeks so throughput becomes steadier.<br><br>- Reduces breach clusters by triggering actions before the week falls too far behind target.<br><br>- Improves on-time completion because interventions happen early in the cycle.<br><br>- Gives team leads clear thresholds that convert data into timely action.<br><br>- Promotes sustained performance rather than end-of-week recovery sprints.<br><br>- Creates an auditable trail of decisions that can be reviewed and refined. | **Throughput lift** = (tickets_closed_on_time_after − baseline_on_time) per week, benchmarked to **{best_week_met_pct:.2f}%**. | Weekly bars visibly show dispersion between **{best_week_date_str}** and **{worst_week_date_str}** to be narrowed. |
| Priority fast-lane for weak bucket | **Phase 1 – Criteria:** for **{worst_priority}** (< **{avg_priority_pct:.1f}%**), define fast-lane steps/owners.<br><br>**Phase 2 – Route:** send qualifying tickets directly to senior queue.<br><br>**Phase 3 – Validate:** measure SLA rise toward **{avg_priority_pct:.1f}%**. | - Accelerates the highest risk items and lifts the slowest priority toward the target.<br><br>- Reduces aging tails that cause breaches and downstream escalations.<br><br>- Focuses expert attention where movement of the KPI is greatest.<br><br>- Shortens average cycle time without diluting attention across lower impact work.<br><br>- Provides a clear promise to stakeholders about how urgent work is handled.<br><br>- Offers measurable results that can be tracked in weekly reviews. | **SLA uplift** = (post-fast-lane % − {worst_priority_pct:.1f}%) × tickets_in_{worst_priority}. | Priority bar chart highlights **{worst_priority}** as the clear underperformer to target. |
| KPI early-warning from gauge | **Phase 1 – Threshold:** alert when gauge drops below {max(0.0, overall_sla_pct - 5):.1f}% (current **{overall_sla_pct:.2f}%**).<br><br>**Phase 2 – Playbook:** auto-reassign, enable bots, add shifts.<br><br>**Phase 3 – Exit:** when KPI reverts within ±2%. | - Prevents slow drift into breach territory by responding to small early signals.<br><br>- Protects predictability for customers by stabilizing the headline KPI.<br><br>- Gives managers a concrete trigger to deploy extra capacity in time.<br><br>- Coordinates actions across teams using a single north-star metric.<br><br>- Reduces variability month to month which simplifies planning and reporting.<br><br>- Embeds a feedback loop that deactivates measures once stability returns. | **Breaches avoided** = (expected_breaches_at_{overall_sla_pct:.1f}% − actual_breaches_after_actions). | Gauge summarizes overall **contract health**, tying actions to a concrete threshold. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Proactive comms in worst weeks | **Phase 1 – Trigger:** when weekly SLA heads toward **{worst_week_met_pct:.2f}%** (week like **{worst_week_date_str}**).<br><br>**Phase 2 – Messages:** ETAs/owners/status cadence.<br><br>**Phase 3 – Survey:** CSAT delta. | - Reduces complaint volume by telling users what will happen and when during stress weeks.<br><br>- Lowers repeat contacts because updates answer common follow-up questions in advance.<br><br>- Improves perceived reliability even when speed is temporarily constrained.<br><br>- Demonstrates ownership and transparency which builds trust with stakeholders.<br><br>- Preserves executive relationships by showing control during difficult periods.<br><br>- Creates a consistent user experience that is easier to defend in reviews. | **Contact deflection** = (follow-ups avoided × minutes). Use weekly breach rate **{100 - worst_week_met_pct:.2f}%** to size affected audience. | Weekly bars show **high breach proportion** in worst week windows where comms matter most. |
| Priority-aware updates | **Phase 1 – Cadence:** tighter updates for **{worst_priority}** where SLA is **{worst_priority_pct:.1f}%**.<br><br>**Phase 2 – Automation:** portal/email sync.<br><br>**Phase 3 – Check-ins:** VIP follow-ups. | - Protects critical users by providing faster clarity on the riskiest work type.<br><br>- Reduces escalations due to uncertainty because stakeholders see progress in real time.<br><br>- Strengthens trust without increasing engineering effort because messages are automated.<br><br>- Gives managers clearer visibility on where to intervene next.<br><br>- Aligns communications with actual business impact across priorities.<br><br>- Supports renewal and satisfaction metrics for high value accounts. | **Escalation cost avoided** = (escalations avoided in {worst_priority} × cost_per_escalation). | Priority chart pinpoints **{worst_priority}** as dissatisfaction risk. |
| Publish best-week norms | **Phase 1 – Share:** make **{best_week_date_str}** practices explicit.<br><br>**Phase 2 – Train:** coach teams on scripts/tools.<br><br>**Phase 3 – Monitor:** adherence dashboards. | - Raises the floor of user experience by aligning everyone to the best observed standard.<br><br>- Keeps expectations consistent for customers from week to week.<br><br>- Shortens the time to value for new hires by giving concrete examples to follow.<br><br>- Reduces noise in stakeholder forums because performance becomes more uniform.<br><br>- Supports a continuous improvement culture anchored in real data.<br><br>- Makes retrospectives more actionable since norms are documented and measurable. | **CSAT lift** attributable to raising weeks toward **{best_week_met_pct:.2f}%** adherence. | The best-week bar shows **achievable SLA** users can expect when norms are followed. |
"""
}
        # --- CIO Table (you can rename the title to match your module wording)
        render_cio_tables("CIO Recommendations – Ticket Escalation Rate", cio_6a)

    # -------------------------------
    # Subtarget 6(b): SLA Breaches & Reasons
    # -------------------------------
    with st.expander("📌 SLA Breaches and Reasons"):
        st.markdown("This section identifies breach causes and trends using Pareto, category, and time-series analysis.")

        # Determine breach availability up front and notify if none
        breach_count = None
        any_breach = None
        if "sla_met" in df_filtered.columns:
            sla_num = pd.to_numeric(df_filtered["sla_met"], errors="coerce")
            breach_mask = sla_num.eq(0)
            breach_count = int(breach_mask.sum())
            any_breach = breach_count > 0

        if any_breach is False:
            st.success("No SLA breaches detected for the current selection. Breach analytics are hidden.")
            # Early exit from this expander to avoid empty charts
            return

        # Prepare stats for CIO tables from the three charts below
        top_reason = "-"
        top_reason_count = 0
        top3_share_pct = 0.0

        bp_top_pri = "-"
        bp_top_cnt = 0
        bp_total = 0

        bt_peak_date = "-"
        bt_peak_cnt = 0
        bt_avg_per_day = 0.0

        # --- Graph 1: Pareto Chart of Breach Reasons
        if "breach_reason" in df_filtered.columns:
            # Use only breached rows when computing Pareto
            if "sla_met" in df_filtered.columns:
                mask = pd.to_numeric(df_filtered["sla_met"], errors="coerce").eq(0)
                data_for_pareto = df_filtered.loc[mask]
            else:
                data_for_pareto = df_filtered

            breach_summary = data_for_pareto["breach_reason"].value_counts(dropna=True).reset_index()
            breach_summary.columns = ["reason", "count"]
            if not breach_summary.empty:
                breach_summary["cum_pct"] = breach_summary["count"].cumsum() / breach_summary["count"].sum() * 100
                top_reason = str(breach_summary.iloc[0]["reason"])
                top_reason_count = int(breach_summary.iloc[0]["count"])
                top3_share_pct = float(breach_summary["count"].iloc[:3].sum() / breach_summary["count"].sum() * 100)

                fig = px.bar(breach_summary, x="reason", y="count", title="Pareto Analysis – Breach Reasons")
                fig.add_scatter(x=breach_summary["reason"], y=breach_summary["cum_pct"], mode="lines+markers", name="Cumulative %")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### Analysis – Pareto of Breach Reasons")
                st.write(f"""**What this graph is:** A Pareto chart of **SLA breach reasons** with cumulative percentage.  
- **X-axis:** Breach reason.  
- **Y-axis:** Count (bars) and cumulative % (line).

**What it shows in your data:**  
Top reason: **{top_reason}** with **{top_reason_count} breaches**.  
Cumulative share of top 3 reasons: **{top3_share_pct:.1f}%** of all breaches.

Overall, a steep cumulative curve confirms **few causes drive most breaches**.

**How to read it operationally:**  
1) **Peaks:** Eliminate the top 1–3 causes first (runbooks, ownership, automation).  
2) **Plateaus:** Standardize fixes; monitor drift.  
3) **Downswings:** Validate which interventions removed failure modes.  
4) **Mix:** Map each top cause to affected priorities/teams for targeted action.

**Why this matters:** Pareto focus maximizes ROI—removing a handful of root causes cuts **breaches, penalties, and rework** fastest.
""")

        # --- Graph 2: Breaches by Priority (aligned to P1,P2,P3,P5,Service Request)
        if "priority" in df_filtered.columns and "sla_met" in df_filtered.columns:
            dfb = df_filtered.copy()
            dfb["priority_std"] = normalize_priority(dfb["priority"])
            sla_num = pd.to_numeric(dfb["sla_met"], errors="coerce")

            breach_priority = (dfb[sla_num.eq(0)]
                                .groupby("priority_std", observed=True)
                                .size()
                                .reindex(PRIORITY_ORDER, fill_value=0)
                                .reset_index(name="count"))

            fig = px.bar(
                breach_priority,
                x="priority_std",
                y="count",
                title="Breaches by Priority",
                labels={"priority_std": "Priority", "count": "Breached Tickets"},
                category_orders={"priority_std": PRIORITY_ORDER},
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Analysis – Breaches by Priority")
            if breach_priority["count"].sum() > 0:
                idxmax = breach_priority["count"].idxmax()
                idxmin = breach_priority["count"].idxmin()
                bp_top_pri = str(breach_priority.loc[idxmax, "priority_std"])
                bp_top_cnt = int(breach_priority.loc[idxmax, "count"])
                bot_pri = str(breach_priority.loc[idxmin, "priority_std"])
                bot_cnt = int(breach_priority.loc[idxmin, "count"])
                total_cnt = int(breach_priority["count"].sum())
                bp_total = total_cnt  # keep for CIO table usage downstream

                st.write(f"""**What this graph is:** A bar chart of **SLA breach counts by priority**.  
- **X-axis:** Priority (fixed order: {", ".join(PRIORITY_ORDER)}).  
- **Y-axis:** Number of breached tickets.

**What it shows in your data:**  
Highest breach load: **{bp_top_pri}** with **{bp_top_cnt}** breaches.  
Lowest breach load: **{bot_pri}** with **{bot_cnt}** breaches.  
Total breaches shown: **{total_cnt}**.

Overall, taller bars flag **where SLA control is weakest** by urgency class.

**How to read it operationally:**  
1) **Peaks:** Add fast-lane routing and senior resolver pools.  
2) **Plateaus:** Maintain capacity guardrails and review queue policies.  
3) **Downswings:** Lock in changes that reduced breaches.  
4) **Mix:** Cross-reference with breach reasons to align fixes per priority.

**Why this matters:** Priority-aware breach control protects **business-critical operations** and reduces **costly escalations**.
""")
            else:
                st.write("""**What this graph is:** A bar chart of **SLA breach counts by priority**.  
- **X-axis:** Priority.  
- **Y-axis:** Number of breached tickets.

**What it shows in your data:**  
No breached tickets exist for the current filter—bars are empty.

**How to read it operationally:**  
1) Verify the date window and `sla_met` computation.  
2) If correct, this indicates strong control across priorities for the selected range.

**Why this matters:** Empty breaches here is good news—maintain controls and monitoring.
""")

        # --- Graph 3: Time Series of Breach Counts
        if "created_time" in df_filtered.columns and "sla_met" in df_filtered.columns:
            work2 = df_filtered.copy()
            work2["created_date"] = pd.to_datetime(work2["created_time"], errors="coerce").dt.date
            sla_num2 = pd.to_numeric(work2["sla_met"], errors="coerce")
            breach_trend = work2[sla_num2.eq(0)].groupby("created_date").size().reset_index(name="breaches")

            fig = px.line(breach_trend, x="created_date", y="breaches", title="Time Series – Breach Counts")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Analysis of Breach Time Series")
            if (breach_trend is not None) and (not breach_trend.empty) and breach_trend["breaches"].gt(0).any():
                top_idx = breach_trend["breaches"].idxmax()
                bt_peak_date = str(breach_trend.loc[top_idx, "created_date"])
                bt_peak_cnt = int(breach_trend.loc[top_idx, "breaches"])
                bt_avg_per_day = float(breach_trend["breaches"].mean())

                st.write(f"""**What this graph is:** A time-series showing **daily SLA breach counts**.  
- **X-axis:** Calendar date.  
- **Y-axis:** Number of breached tickets per day.

**What it shows in your data:**  
Peak breach day: **{bt_peak_date}** with **{bt_peak_cnt}** breaches.  
Average breaches/day: **{bt_avg_per_day:.1f}**.

Overall, sharp peaks indicate **capacity shortfalls or routing delays** during high intake; quieter runs indicate **stability**.

**How to read it operationally:**  
1) **Peaks:** Trigger surge playbooks (swarm, escalation tiers, auto-triage).  
2) **Plateaus:** Maintain staffing and monitor leading indicators.  
3) **Downswings:** Sunset temporary measures; verify sustained control.  
4) **Mix:** Overlay with intake volume to separate **demand spikes vs execution gaps**.

**Why this matters:** Breach spikes drive **penalties and dissatisfaction**. Early detection and rapid response keep **contracts and trust** intact.
""")
            else:
                st.write("""**What this graph is:** A time-series showing **daily SLA breach counts**.  
- **X-axis:** Calendar date.  
- **Y-axis:** Number of breached tickets per day.

**What it shows in your data:**  
There are **no breached tickets** in the selected range, so the series is empty.

**How to read it operationally:**  
1) Confirm the date filter and `sla_met` logic are correct.  
2) If correct, this indicates **strong control** with no breaches for the period.

**Why this matters:** Zero breaches mean **penalty and rework risk are minimal**—maintain current controls and monitoring.
""")

        # ---------------- CIO Tables for 6(b) ----------------
        cio_6b = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Eliminate top breach reason first | **Phase 1 – Diagnose:** focus on **{top_reason}** (**{top_reason_count}** breaches).<br><br>**Phase 2 – Fix:** runbooks, validation steps, tooling guardrails.<br><br>**Phase 3 – Verify:** top-3 share **{top3_share_pct:.1f}%** should decline. | - Removes the single biggest cost driver quickly which creates immediate savings.<br><br>- Prevents repeat failures that generate rework and penalty risk.<br><br>- Frees senior time that would otherwise be spent on escalations from the same cause.<br><br>- Increases delivery stability because the largest source of variability is addressed first.<br><br>- Provides a clear before and after measurement that justifies the investment.<br><br>- Builds confidence in the program by showing visible improvements early. | **Penalties avoided** = (breaches_reduced_from_{top_reason}) × penalty_per_breach. Baseline = **{top_reason_count}** from Pareto. | Pareto shows **{top_reason}** leading with **{top_reason_count}** and top-3 at **{top3_share_pct:.1f}%** of all breaches. |
| Priority-specific remediation | **Phase 1 – Target:** priority **{bp_top_pri}** with **{bp_top_cnt}** breaches (of **{bp_total}** total).<br><br>**Phase 2 – Controls:** fast-lanes, senior review, auto-escalation.<br><br>**Phase 3 – Measure:** weekly breach drop. | - Concentrates effort where most penalties accrue which maximizes financial impact.<br><br>- Improves predictability for urgent cases that drive executive attention.<br><br>- Reduces the volume of high-cost escalations by clearing blockers sooner.<br><br>- Helps teams learn the common pitfalls for that priority and avoid them next time.<br><br>- Makes reporting clearer because the biggest problem area shows measurable progress.<br><br>- Creates a pattern that can be reused when another priority becomes breach-heavy. | **Cost avoided/week** = (reduction_in_{bp_top_pri}_breaches × penalty_per_breach). Baseline count = **{bp_top_cnt}**. | “Breaches by Priority” bar shows **{bp_top_pri}** as highest contributor (**{bp_top_cnt}/{bp_total}**). |
| Peak-day surge guard | **Phase 1 – Detect:** peak day **{bt_peak_date}** at **{bt_peak_cnt}** breaches vs average **{bt_avg_per_day:.1f}/day**.<br><br>**Phase 2 – Act:** temporary staffing, swarming, auto-triage on similar days.<br><br>**Phase 3 – Exit:** when breaches revert near average. | - Prevents cost spikes on the days that statistically create the most damage.<br><br>- Reduces overtime because more work is completed during core hours.<br><br>- Limits follow-on defects that arise when teams are overloaded and rushing.<br><br>- Keeps customer communications timely which dampens complaint volume.<br><br>- Provides a repeatable trigger so surge plans activate at the right moment.<br><br>- Shortens recovery time so normal operations resume faster after peaks. | **Savings/day** = (bt_peak_cnt − {bt_avg_per_day:.1f}) × (avg_breach_hours × hourly_rate). Here bt_peak_cnt = **{bt_peak_cnt}**. | Breach time series highlights the worst day **{bt_peak_date}** (value **{bt_peak_cnt}**) vs average **{bt_avg_per_day:.1f}**. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Pareto-driven runbook updates | **Phase 1 – Author:** add steps for {top_reason} and top-3 failures (**{top3_share_pct:.1f}%** share).<br><br>**Phase 2 – Train:** reinforce with simulations.<br><br>**Phase 3 – Audit:** decline in those bars. | - Speeds resolution on the most common failure modes by giving clear steps.<br><br>- Reduces repeat breaches because known traps are addressed directly.<br><br>- Raises team-wide consistency which lifts on-time completion rates.<br><br>- Shortens onboarding because new agents can follow the documented paths.<br><br>- Creates measurable learning cycles as runbooks are refined over time.<br><br>- Strengthens cross-team coordination since expectations are explicit. | **Throughput gain** = (tickets_closed_on_time_post − baseline). Focus on reasons covering **{top3_share_pct:.1f}%** of breaches. | Pareto curve steepness proves few causes dominate failures. |
| Priority fast-lane on breach-heavy buckets | **Phase 1 – Define:** fast-lane SLAs for **{bp_top_pri}**.<br><br>**Phase 2 – Route:** auto-assign to senior resolvers.<br><br>**Phase 3 – Check:** SLA % uplift and breach reduction. | - Improves on-time completion where performance is currently weakest.<br><br>- Reduces queue aging for urgent items that cannot tolerate delays.<br><br>- Gives leadership confidence that critical work is handled with priority and expertise.<br><br>- Provides a measurable lever to shift SLA results quickly in the right direction.<br><br>- Protects downstream operations that depend on timely fixes for this priority.<br><br>- Creates a model that can be scaled to other priorities when needed. | **SLA uplift** = (post_fastlane_SLA − baseline_SLA_{bp_top_pri}). Baseline breach count = **{bp_top_cnt}**. | Priority bar identifies **{bp_top_pri}** as the performance sink. |
| Peak-day incident playbook | **Phase 1 – Threshold:** when breaches approach **{bt_peak_cnt}** on a day, auto-trigger swarm.<br><br>**Phase 2 – Vendor:** early pings.<br><br>**Phase 3 – Stand-down:** as counts normalize toward **{bt_avg_per_day:.1f}**. | - Accelerates recovery during spikes by aligning people and vendors fast.<br><br>- Shrinks backlogs so fewer tickets spill into the next day and breach again.<br><br>- Reduces noise in the system because ownership and actions are predefined.<br><br>- Clarifies decision rights which prevents delays caused by confusion.<br><br>- Supports transparent incident reviews with clear timelines and actions.<br><br>- Builds organizational memory so future spikes are handled even better. | **Breaches avoided/day** = (bt_peak_cnt − target_breaches_near_{bt_avg_per_day:.1f}). | Series pinpoints **{bt_peak_date}** as outlier to design thresholds. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Targeted comms for top reasons | **Phase 1 – Templates:** user-friendly updates for **{top_reason}** cases.<br><br>**Phase 2 – Timing:** send earlier on days trending above **{bt_avg_per_day:.1f}** breaches.<br><br>**Phase 3 – Measure:** complaint reduction. | - Reduces frustration by addressing the most common user pain points directly.<br><br>- Lowers repeat contacts because answers arrive before users need to ask.<br><br>- Increases transparency which improves perception even when fixes take time.<br><br>- Standardizes language so messages are clear and consistent across agents.<br><br>- Helps support teams focus on work rather than reactive messaging.<br><br>- Provides clean metrics to verify whether communications are working. | **Contact deflection** = (repeat contacts avoided for {top_reason} × minutes_saved). Baseline volume = **{top_reason_count}**. | Pareto evidence: **{top_reason}** dominates; time series guides when to send. |
| Priority-aware expectation setting | **Phase 1 – Cadence:** stricter updates for **{bp_top_pri}** (highest breaches **{bp_top_cnt}**).<br><br>**Phase 2 – Portal:** live ETA and owner.<br><br>**Phase 3 – Survey:** CSAT change. | - Reassures critical users that their case is moving with clear next steps and times.<br><br>- Reduces escalations that stem from uncertainty or silence.<br><br>- Aligns stakeholder expectations with operational reality which protects trust.<br><br>- Improves CSAT because users feel informed and respected throughout the process.<br><br>- Supports account managers who need accurate status for high value customers.<br><br>- Creates a traceable communication record that helps in post-incident reviews. | **Escalation cost avoided** = (escalations avoided in {bp_top_pri} × cost_per_escalation). | Priority bar shows **{bp_top_pri}** as the key risk bucket. |
| Peak-day apology & recovery plan | **Phase 1 – Criteria:** when day hits **{bt_peak_cnt}** breaches (peak **{bt_peak_date}**), issue apology + action plan.<br><br>**Phase 2 – Follow-up:** post-incident notes.<br><br>**Phase 3 – Track:** churn/complaints. | - Repairs confidence after visible disruption with a concrete recovery path.<br><br>- Reduces churn risk by demonstrating accountability and corrective action.<br><br>- Lowers future complaint volume because users see that lessons were applied.<br><br>- Supports brand reputation by showing empathy and professionalism.<br><br>- Provides closure for affected users which improves long term sentiment.<br><br>- Creates documentation that informs preventive work and future training. | **Retention benefit** = (complaints avoided × value_per_customer) using peak-day cohort size **{bt_peak_cnt}**. | Time series explicitly shows **{bt_peak_date}** as the worst breach day. |
"""
}
        # --- CIO Table (you can rename the title to match your module wording)
        render_cio_tables("CIO Recommendations – Ticket Reopen Rate", cio_6b)
