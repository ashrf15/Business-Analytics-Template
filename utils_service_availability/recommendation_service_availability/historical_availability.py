# utils_service_availability/recommendation_service_availability/historical_trends.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from textwrap import dedent  # for cleaning indentation in markdown strings


# ============================================================
# Helper Function for CIO Tables
# ============================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(dedent(cio_data["cost"]), unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(dedent(cio_data["performance"]), unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(dedent(cio_data["satisfaction"]), unsafe_allow_html=True)


# ============================================================
# 4️⃣ Historical Availability Trends
# ============================================================
def historical_availability(df: pd.DataFrame):

    # ======================================
    # 4a. Monthly Availability Trend
    # ======================================
    with st.expander("📌 Monthly Availability Trends"):
        required = {"report_date", "uptime_percentage", "estimated_cost_downtime"}
        if required.issubset(df.columns):
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
            df["month"] = df["report_date"].dt.to_period("M").astype(str)

            monthly = (
                df.groupby("month")
                .agg(
                    avg_uptime=("uptime_percentage", "mean"),
                    total_cost=("estimated_cost_downtime", "sum"),
                )
                .reset_index()
                .sort_values("month")
            )

            # --- Graph 1: Average Uptime over Months
            fig1 = px.line(
                monthly,
                x="month",
                y="avg_uptime",
                title="Average Uptime Percentage Over Time (Monthly)",
                markers=True,
                labels={"month": "Month", "avg_uptime": "Average Uptime (%)"},
            )
            st.plotly_chart(fig1, use_container_width=True)

            # === Analysis (Graph 1 only: Uptime line) ===
            peak_u = monthly.loc[monthly["avg_uptime"].idxmax()]
            low_u = monthly.loc[monthly["avg_uptime"].idxmin()]
            avg_u_all = float(monthly["avg_uptime"].mean())
            rng_u = float(peak_u["avg_uptime"] - low_u["avg_uptime"])

            st.markdown("### Analysis — Average Uptime (Line)")
            st.markdown(
                dedent(
                    f"""
                    **What this graph is:** A monthly time-series line chart showing **average uptime (%)**.  
                    **X-axis:** Calendar month.  
                    **Y-axis:** Average uptime percentage (higher is better).

                    **What it shows in your data:**  
                    - **Largest uptime month:** **{peak_u['month']}** at **{peak_u['avg_uptime']:.2f}%**  
                    - **Lowest uptime month:** **{low_u['month']}** at **{low_u['avg_uptime']:.2f}%**  
                    - **Average across period:** **{avg_u_all:.2f}%**; **Range:** **{rng_u:.2f} pp**

                    **How to read it operationally:**  
                    - **Gap to target:** The vertical gap from your SLA/SLO to the line quantifies shortfall.  
                    - **Lead–lag vs change windows:** If dips line up with deployments, tighten release guardrails.  
                    - **Recovery strength:** Faster rebound after troughs indicates healthier incident handling.  
                    - **Control:** Keep the line high and flat via WIP limits, golden paths, and freeze criteria.

                    **Why this matters:** Uptime is the heartbeat of reliability. Elevating and stabilizing it prevents SLA penalties, ticket surges, and customer churn.
                    """
                )
            )

            ev_u = (
                f"Uptime peak **{peak_u['month']} = {peak_u['avg_uptime']:.2f}%**, "
                f"low **{low_u['month']} = {low_u['avg_uptime']:.2f}%**, "
                f"avg **{avg_u_all:.2f}%**, range **{rng_u:.2f} pp**."
            )

            # --- Graph 2: Monthly Downtime Cost
            fig2 = px.bar(
                monthly,
                x="month",
                y="total_cost",
                title="Monthly Downtime Cost (RM)",
                labels={"month": "Month", "total_cost": "Total Downtime Cost (RM)"},
                text="total_cost",
            )
            fig2.update_traces(texttemplate="RM %{text:,.0f}", textposition="outside")
            st.plotly_chart(fig2, use_container_width=True)

            # === Analysis (Graph 2 only: Cost bars) ===
            peak_c = monthly.loc[monthly["total_cost"].idxmax()]
            low_c = monthly.loc[monthly["total_cost"].idxmin()]
            avg_cost_all = float(monthly["total_cost"].mean())
            sum_cost_all = float(monthly["total_cost"].sum())
            share_peak = (
                float(peak_c["total_cost"]) / sum_cost_all * 100.0
                if sum_cost_all > 0
                else 0.0
            )

            st.markdown("### Analysis — Monthly Downtime Cost (Bars)")
            st.markdown(
                dedent(
                    f"""
                    **What this graph is:** A monthly bar chart showing **total downtime cost (RM)**.  
                    **X-axis:** Calendar month.  
                    **Y-axis:** Total estimated downtime cost in RM (lower is better).

                    **What it shows in your data:**  
                    - **Peak cost month:** **{peak_c['month']}** at **RM {peak_c['total_cost']:,.0f}** (**{share_peak:.1f}%** of period total **RM {sum_cost_all:,.0f}**)  
                    - **Lowest cost month:** **{low_c['month']}** at **RM {low_c['total_cost']:,.0f}**  
                    - **Average monthly cost:** **RM {avg_cost_all:,.0f}**

                    **How to read it operationally:**  
                    - **Spike triage:** For **{peak_c['month']}**, cluster incidents by root cause and neutralize top drivers.  
                    - **Plateau capture:** Replicate practices from low-cost months (**{low_c['month']}**)—release rhythm, maintenance windows.  
                    - **Outliers vs trend:** If costs rise while uptime holds, investigate partial outages or high-value single incidents.  
                    - **Budget steering:** Focus remediation where bars are tallest; validate compression next cycle.

                    **Why this matters:** Every RM in these bars is lost productivity or revenue. Attacking peak months first accelerates cost recovery and stabilizes experience.
                    """
                )
            )

            ev_c = (
                f"Cost peak **{peak_c['month']} = RM {peak_c['total_cost']:,.0f}** "
                f"({share_peak:.1f}% of **RM {sum_cost_all:,.0f}**), "
                f"low **{low_c['month']} = RM {low_c['total_cost']:,.0f}**, "
                f"avg **RM {avg_cost_all:,.0f}**."
            )

            # ---------- CIO tables (3+ rows; phased; real values; explicit evidence) ----------
            diff_cost = float(peak_c["total_cost"] - low_c["total_cost"])
            diff_uptime = float(peak_u["avg_uptime"] - low_u["avg_uptime"])  # used conceptually

            cio_4a = {
                "cost": f"""
    | Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
    |---|---|---|---|---|
    | Eliminate **peak-cost month** drivers (**{peak_c['month']}**) | **Phase 1:** Cluster all incidents that occurred in **{peak_c['month']}** by root cause so that you can clearly see which technical or process failures created the spike in downtime cost.<br><br>**Phase 2:** From that clustered view, fix the top two or three dominant causes using specific actions such as patching, configuration correction or failover improvements so that the biggest contributors are removed first.<br><br>**Phase 3:** In the next **{peak_c['month']}** cycle, re-measure both uptime and downtime cost to confirm whether the corrective actions have actually reduced the peak and stabilised the month. | - Focuses attention on the single most expensive month so that cost reduction starts where the financial pain is highest.<br><br>- Allows removal of a small number of root causes that drive a large portion of the loss so that improvements are tangible within a short period.<br><br>- Creates a clear before and after comparison that can be shown to management so that future investments in reliability are easier to justify.<br><br> | **Upper bound savings:** Current peak cost = **RM {peak_c['total_cost']:,.0f}**. | {ev_c} |
    | Copy the **best-practice month** | **Phase 1:** Document what was done differently in high-uptime and low-cost months like **{peak_u['month']}** and **{low_c['month']}**, including release timing, maintenance activities and incident handling behaviours.<br><br>**Phase 2:** Turn these observed behaviours into standard windows, checklists and operating procedures that can be consistently applied in other months.<br><br>**Phase 3:** Audit adherence to these practices in subsequent periods so that you can verify whether copying this pattern leads to similar stability and cost outcomes. | - Reuses proven ways of working from the best months so that other periods can benefit from the same discipline and scheduling approach.<br><br>- Reduces variability between months because teams are no longer improvising and instead follow a standard pattern that has already worked.<br><br>- Supports knowledge transfer across teams and shifts so that successful practices are not locked inside a single month or a single group of people.<br><br> | **Expected reduction:** Peak−Low = **RM {diff_cost:,.0f}**. | {ev_u} / {ev_c} |
    | Smooth seasonal risk | **Phase 1:** Identify all months where average uptime falls below **{avg_u_all:.2f}%** and flag them as higher seasonal risk periods for further analysis.<br><br>**Phase 2:** For those months, add extra capacity where needed and freeze or tighten risky changes so that the known weak periods are better protected.<br><br>**Phase 3:** After implementing these actions, check whether downtime cost has reduced in those specific months to confirm that seasonal risk is being smoothed out. | - Prevents the same seasonal patterns from causing repeated performance drops and financial losses every year.<br><br>- Allows more intelligent allocation of resources by strengthening periods that historically perform poorly instead of treating all months the same.<br><br>- Helps business stakeholders plan around known challenging periods because the risk and mitigation actions are made visible in advance.<br><br> | **Pool:** Sum of costs in below-average months (from bars). | {ev_u} / {ev_c} |
    | Price-tag planned work | **Phase 1:** Estimate the outage minutes and associated financial impact for each planned maintenance or change activity before deciding when to schedule it.<br><br>**Phase 2:** Wherever possible, move these activities into months similar to **{low_c['month']}**, where historical cost and disruption are lower, so that the relative impact is minimized.<br><br>**Phase 3:** After execution, compare the actual cost and incident behaviour with previous months to validate that the chosen timing reduced the financial impact. | - Helps decision makers understand the true cost of planned work so that scheduling decisions are based on data rather than guesswork.<br><br>- Minimises disruption to revenue and productivity by aligning high impact work with times when the business can better absorb it.<br><br>- Supports more constructive conversations with business stakeholders because timing choices can be shown to protect their operations.<br><br> | **Avoided cost = Planned minutes × (RM/min)**; compare months pre/post. | {ev_c} |
    | Rapid rollback policy | **Phase 1:** Define clear technical and business triggers that indicate a change is negatively affecting stability and should be rolled back quickly, and make sure all teams understand them.<br><br>**Phase 2:** Train teams on canary releases, automated checks and rollback runbooks so that reversing a bad change is fast, safe and consistent in execution.<br><br>**Phase 3:** Measure how long it takes to roll back problematic changes and aim to reduce this time window in each quarter so that incidents become shorter and less expensive. | - Turns long-running change-related incidents into shorter, contained events so that downtime costs do not escalate unnecessarily.<br><br>- Increases confidence in the release process because everyone knows that there is a safe and tested escape path if something goes wrong.<br><br>- Enables teams to be more responsive and experimental while still protecting uptime and cost, because failed changes can be rolled back quickly and reliably.<br><br> | **Upper bound:** Portion of **RM {peak_c['total_cost']:,.0f}** tied to failed changes. | {ev_c} |
    """,
                "performance": f"""
    | Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
    |---|---|---|---|---|
    | Uptime floor & SLOs | **Phase 1:** Define a minimum monthly uptime floor that is at or above **{avg_u_all:.2f}%** so that everyone is clear on the lowest acceptable performance level.<br><br>**Phase 2:** Use forecasting and alerting to project when current incident patterns might cause a breach of this floor and trigger early intervention actions.<br><br>**Phase 3:** Review performance against these SLOs every month and adjust processes or capacity where services consistently sit close to the floor. | - Keeps reliability from drifting downwards because there is a visible lower boundary that triggers action once it is approached.<br><br>- Improves planning by connecting day to day operational behaviours with a clear monthly target that stakeholders understand.<br><br>- Helps align technical decisions with business expectations because the floor reflects what is needed to meet contracts and internal commitments.<br><br> | **Minutes saved:** (ΔUptime × total hours) × exposure. | {ev_u} |
    | Incident timeboxing | **Phase 1:** Set explicit targets for how long incidents are allowed to remain open each month for key service categories, turning vague expectations into measurable goals.<br><br>**Phase 2:** Create on-call escalation rules that ensure incidents are handed over quickly to the right experts when they approach those time limits.<br><br>**Phase 3:** Conduct postmortems for incidents that breach the timebox and adjust processes or staffing so that similar overruns are less likely in the future. | - Directly reduces the length of individual incidents so that less productive time is lost whenever something breaks.<br><br>- Exposes bottlenecks in the incident process and encourages teams to streamline handoffs and approvals.<br><br>- Builds a culture of urgency and discipline around resolving user-impacting issues within agreed time frames.<br><br> | **Saved minutes:** (Old MTTR − New MTTR) × incidents. | {ev_c} |
    | Capacity guardrails | **Phase 1:** Examine CPU, memory and network usage during months with lower uptime to see whether capacity issues correlate with the dips.<br><br>**Phase 2:** Implement autoscaling rules, throttling or configuration limits so that services are less likely to hit hard capacity ceilings during peak load.<br><br>**Phase 3:** Re-test availability during busy periods after these changes to confirm that capacity is no longer a primary driver of uptime drops. | - Prevents saturation-related outages that can suddenly take services offline when demand spikes.<br><br>- Creates more predictable performance under load so that business teams can plan peak activities without fear of system failure.<br><br>- Helps prioritise infrastructure investment because it becomes clear which services genuinely need more resources and which only needed tuning.<br><br> | **Upper bound:** Cost in capacity-related months. | {ev_u} / {ev_c} |
    | Change hygiene calendar | **Phase 1:** Use historical data to map out which months have been stable and which have been unstable, especially around major release periods.<br><br>**Phase 2:** Schedule high risk or complex releases into historically stable months and avoid stacking many changes within the same risky window.<br><br>**Phase 3:** Use canary deployments and gradual rollouts in these planned windows to further reduce the likelihood of widespread issues. | - Reduces the probability that changes will cause outages in months that are already fragile or heavily loaded with business activity.<br><br>- Encourages better coordination between product, change and operations teams because timing decisions are based on real history rather than convenience.<br><br>- Leads to a more even reliability trend across the year because large shocks from clustered changes are avoided.<br><br> | **Incidents prevented:** change-induced × MTTR. | {ev_u} |
    """,
                "satisfaction": f"""
    | Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
    |---|---|---|---|---|
    | Publish monthly reliability memo | **Phase 1:** Prepare a short monthly memo that summarises uptime and downtime cost using the graphs and key numbers that business users can easily understand.<br><br>**Phase 2:** Include a simple explanation of what went well, what did not go well and what actions are being taken so that stakeholders are not surprised by any trends.<br><br>**Phase 3:** Track customer satisfaction and escalation patterns after the memos to see whether clearer communication is reducing noise and confusion. | - Builds trust because users can see that reliability performance is being measured, understood and shared openly.<br><br>- Reduces rumours and guesswork around system stability because there is an official narrative backed by data.<br><br>- Helps stakeholders feel like partners in the improvement journey rather than outsiders who only hear about problems when they escalate.<br><br> | **Complaints avoided × handling cost** (post-memo trend). | {ev_u} / {ev_c} |
    | Pre-emptive comms for risky months | **Phase 1:** Use historical trends to identify months that regularly sit below **{avg_u_all:.2f}%** uptime and label them as higher risk periods in your communication plans.<br><br>**Phase 2:** Ahead of those months, brief key users on potential risks, likely ETAs and available workarounds so they can plan their activities accordingly.<br><br>**Phase 3:** After the period, review how many escalations and complaints occurred and adjust the communication approach based on what worked well. | - Reduces surprise and frustration when issues happen in months that have historically been problematic because expectations were set early.<br><br>- Helps users organise critical work around risk windows so that they are less exposed to potential downtime.<br><br>- Demonstrates that IT teams are proactively managing risk rather than simply reacting when things break.<br><br> | **Escalations avoided × cost**. | {ev_u} |
    | Customer-ready maintenance windows | **Phase 1:** Align planned maintenance windows with months like **{low_c['month']}**, where historical cost and disruption have been lower and easier for the business to absorb.<br><br>**Phase 2:** Communicate the planned work, expected impact and ETAs in simple language that business stakeholders can understand without technical detail.<br><br>**Phase 3:** After maintenance, confirm completion status and any improvements, and collect feedback on whether the timing and communication were acceptable. | - Reduces the perceived disruption of maintenance because it is executed in periods where users can tolerate it more easily.<br><br>- Improves the relationship with customers since they can see that their operational rhythms are being taken into account when maintenance is scheduled.<br><br>- Leads to fewer complaints and escalations about planned downtime because it feels controlled and well communicated rather than arbitrary.<br><br> | **Deflected calls × handling mins**; correlate with low-cost months. | {ev_c} |
    """
            }
            render_cio_tables("CIO – Monthly Availability Trends", cio_4a)
        else:
            st.warning(f"⚠️ Missing required columns: {required - set(df.columns)}")

    # ======================================
    # 4b. Comparative Analysis (Improvement/Degradation)
    # ======================================
    with st.expander("📌 Comparative Analysis – Improvement or Degradation Over Time"):
        required = {"report_date", "uptime_percentage", "service_name"}
        if required.issubset(df.columns):
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
            df["month"] = df["report_date"].dt.to_period("M").astype(str)

            monthly_service = (
                df.groupby(["month", "service_name"], as_index=False)
                .agg(avg_uptime=("uptime_percentage", "mean"))
            )

            fig = px.line(
                monthly_service,
                x="month",
                y="avg_uptime",
                color="service_name",
                markers=True,
                title="Service Uptime Comparison Over Time",
                labels={"avg_uptime": "Average Uptime (%)", "month": "Month"},
            )
            st.plotly_chart(fig, use_container_width=True)

            # Identify trends
            trend_df = (
                monthly_service.groupby("service_name")["avg_uptime"]
                .agg(["first", "last"])
                .reset_index()
            )
            trend_df["change"] = trend_df["last"] - trend_df["first"]

            improved = trend_df[trend_df["change"] > 0].sort_values(
                "change", ascending=False
            )
            degraded = trend_df[trend_df["change"] < 0].sort_values("change")

            best_gain = improved.iloc[0] if not improved.empty else None
            worst_drop = degraded.iloc[0] if not degraded.empty else None

            st.markdown("### Analysis — Comparative Uptime Trends")
            if best_gain is not None and worst_drop is not None:
                st.markdown(
                    dedent(
                        f"""
                        **What this graph is:** A **multi-line chart** comparing **average uptime (%)** by **service** across months to reveal improvements and degradations.  
                        - **X-axis:** Calendar month.  
                        - **Y-axis:** Average uptime percentage per service.

                        **What it shows in your data:**  
                        - **Most improved service:** **{best_gain['service_name']}** with a **+{best_gain['change']:.2f}%** uptime gain from first to last month.  
                        - **Most degraded service:** **{worst_drop['service_name']}** with a **{worst_drop['change']:.2f}%** drop over the same span.  
                        - Divergence between lines indicates different reliability trajectories by ownership, release cadence, or architecture.

                        **How to read it operationally:**  
                        1. **Risers:** Capture practices from improving services and standardize them (release rhythm, maintenance windows).  
                        2. **Fallers:** Trigger root-cause analysis on the steepest declines (e.g., **{worst_drop['service_name']}**).  
                        3. **Flat lines:** If flat below target, set an immediate uplift plan; if flat above target, protect the status quo.  
                        4. **Crossovers:** When a previously strong service dips below peers, review recent changes and capacity.

                        **Why this matters:** Trend direction predicts **future risk**. Acting early on degrading services prevents SLA penalties and compounding cost, while institutionalizing what works sustains high performance across the portfolio.
                        """
                    )
                )
            else:
                st.info("Not enough data to determine improvement or degradation trends.")

            # ---------- CIO tables (each 3–5 rows, concise with phases, formulas from dataset) ----------
            most_imp_name = best_gain["service_name"] if best_gain is not None else "N/A"
            most_imp_change = float(best_gain["change"]) if best_gain is not None else 0.0
            most_deg_name = (
                worst_drop["service_name"] if worst_drop is not None else "N/A"
            )
            most_deg_change = (
                float(worst_drop["change"]) if worst_drop is not None else 0.0
            )

            cio_4b = {
                "cost": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Redirect spend to **degrading services** | **Phase 1:** Temporarily pause non-critical enhancements on services that are already improving so that limited budget and attention are not spread too thin across the entire portfolio.<br><br>**Phase 2:** Reallocate operations and reliability budget toward fallers such as **{most_deg_name}**, which show the steepest decline of **{most_deg_change:.2f}%**, so that the most at-risk services are stabilised first.<br><br>**Phase 3:** Review this allocation every quarter and rotate focus as new degradations or improvements appear in the trend lines. | - Directs money and effort to the services that are currently generating the highest risk and potential loss instead of over-investing in already healthy areas.<br><br>- Improves cost efficiency because corrective actions are applied where they can prevent further erosion of uptime and SLA performance.<br><br>- Prevents hidden financial exposure by stopping declining services from quietly becoming chronic sources of penalties and unplanned operational cost.<br><br> | **Avoided loss (upper bound):** Sum of costs in months where **{most_deg_name}** declined (dataset aggregation). | The line for **{most_deg_name}** shows **{most_deg_change:.2f}%** drop from first→last month. |
| Predictive maintenance on fallers | **Phase 1:** Automatically flag services whose uptime drops for two or more consecutive months so that they are clearly identified as candidates for deeper maintenance review.<br><br>**Phase 2:** For these flagged services, schedule pre-emptive hardware replacements, patching or configuration clean-up rather than waiting for full outages to occur.<br><br>**Phase 3:** After the maintenance cycle, compare downtime and uptime trends in the next month to validate that the intervention reversed or slowed the decline. | - Reduces the likelihood of sudden, high-impact failures on services that are already showing early warning signs in their trend lines.<br><br>- Shifts operational behaviour from reactive firefighting to planned prevention, which usually costs less and disrupts users less.<br><br>- Shortens restoration time and reduces overtime costs because incidents are less frequent and often less severe when underlying weaknesses are treated early.<br><br> | **Minutes avoided:** prior outage minutes in declining months (per service). | Declining slope is visible for fallers. |
| Targeted rollback insurance | **Phase 1:** For faller services, enforce stricter requirements that every major change includes a tested rollback plan that can be executed quickly if performance degrades after deployment.<br><br>**Phase 2:** Use canary releases and error-budget based gates for these services so that problematic changes can be detected early and rolled back before they cause long, visible incidents.<br><br>**Phase 3:** Audit change records monthly to ensure that exceptions to rollback policies are rare and to understand how often rollback insurance prevents extended downtime. | - Limits the financial and operational impact of bad releases because failing changes are reversed before they create long spikes in downtime cost.<br><br>- Protects SLA performance for services that are already trending down by making change-related risk more controllable.<br><br>- Enables clearer accountability because teams must plan for failure scenarios in advance rather than improvising during live incidents.<br><br> | **Upper bound:** Minutes during drop months × RM/min (penalty exposure if applicable). | Drops often coincide with release events on the lines. |
| Cost gating for non-impacting work | **Phase 1:** For services with degrading trends, introduce a formal decision step that checks whether proposed changes are essential for stability or business outcomes before approving them.<br><br>**Phase 2:** Defer non-essential or cosmetic work on these faller services until their stability metrics have returned to acceptable levels and cost risk is lower.<br><br>**Phase 3:** Revisit the deferred backlog after one or two stable cycles and re-prioritise items based on the latest trend and risk profile. | - Ensures that limited engineering and financial capacity is used to restore stability rather than on work that users will not notice while availability is still poor.<br><br>- Avoids opportunity cost by freeing up time and budget that can be used on corrective actions with clear impact on uptime and SLA.<br><br>- Accelerates recovery for degraded services because teams are not distracted by low-value projects and can focus on reliability first.<br><br> | **Opportunity cost saved:** deferred non-essentials (budget itemization). | Divergence pinpoints focus areas. |
| Replicate ops from **{most_imp_name}** | **Phase 1:** Analyse operational practices on the riser service **{most_imp_name}**, which improved by **+{most_imp_change:.2f}%**, to understand how on-call patterns, change discipline and maintenance routines differ from others.<br><br>**Phase 2:** Pilot these proven practices on one or two faller services with similar technology stacks so that adoption effort is manageable and measurable.<br><br>**Phase 3:** If the pilots show uplift, roll out the same operating model more widely and track results through simple scorecards. | - Leverages real success stories inside the organisation rather than importing untested frameworks or theories from outside.<br><br>- Reduces time to benefit because teams copy processes that have already delivered measurable reliability improvements.<br><br>- Gradually standardises high quality operational behaviours across services so that the overall portfolio becomes more stable and predictable.<br><br> | **Expected benefit:** Uptime shift potential ≈ **+{most_imp_change:.2f}%** on pilot cohort. | Riser line evidences workable practices. |
""",
                "performance": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| RCA sprint for **{most_deg_name}** | **Phase 1:** Run a focused two-week root cause analysis sprint on the months where **{most_deg_name}** shows its biggest drop so that all contributing factors are clearly identified.<br><br>**Phase 2:** Prioritise and fix the highest impact causes across configuration, infrastructure, code or process, and document exactly what has changed.<br><br>**Phase 3:** Monitor uptime after these changes with additional guardrails to ensure that the service returns to a healthy trajectory and does not slip back. | - Stops the worst degradation early before it turns into a long-term pattern that is harder and more expensive to correct.<br><br>- Improves the quality of fixes because they are based on structured analysis rather than assumptions or guesswork.<br><br>- Rebuilds confidence in the affected service as stakeholders can see a clear plan, a defined timeframe and post-fix improvement in the trend line.<br><br> | **KPI:** Δuptime post-fix (percentage points) vs baseline. | Largest negative Δ (**{most_deg_change:.2f}%**) marks priority. |
| Clone practices from **{most_imp_name}** | **Phase 1:** Compare release cadence, testing discipline, maintenance windows and incident handling between **{most_imp_name}** and other services to identify practical differences that may explain the uplift.<br><br>**Phase 2:** Implement those specific practices, such as more disciplined canary releases or better maintenance timing, for a selected group of lagging services.<br><br>**Phase 3:** Track uptime and incident trends for these services and adjust the cloned practices if some elements need tailoring to local constraints. | - Lifts lagging services by borrowing methods that have already proven effective in the same organisation and technology environment.<br><br>- Reduces performance variance across the portfolio because weaker services start to behave more like the stronger ones.<br><br>- Avoids unnecessary over-engineering because re-used practices are already known and lightweight for teams to operate.<br><br> | **Throughput gain:** incidents↓ × MTTR↓ (dataset per service). | Clear positive Δ (**+{most_imp_change:.2f}%**) on riser. |
| On-call & paging refinement | **Phase 1:** Review how incidents for faller services are currently escalated and identify delays caused by unclear on-call rotations or weak notification rules.<br><br>**Phase 2:** Redesign on-call schedules and paging thresholds so that the right people are alerted quickly and consistently when availability starts to drop.<br><br>**Phase 3:** Monitor response times and adjust schedules or rules if incidents are still waiting too long for a meaningful response. | - Speeds up the start of incident handling so that issues are contained before they cause large uptime drops.<br><br>- Reduces stress and confusion during outages because everyone knows who is responsible and how they will be notified.<br><br>- Improves overall service performance as more incidents are resolved within target timeframes and fewer linger unresolved.<br><br> | **Minutes saved:** (Old MTTR − New MTTR) × incident count. | Steeper drops need faster response. |
| Capacity sanity checks | **Phase 1:** For degrading services, validate whether their underlying infrastructure and platform capacity still match current user load and growth patterns.<br><br>**Phase 2:** Where gaps are found, apply targeted changes such as scaling up, load balancing or performance tuning instead of blanket upgrades.<br><br>**Phase 3:** Test the services again during peak load to confirm that the capacity changes have stabilised uptime and eliminated previous bottlenecks. | - Ensures that declining availability is not simply the result of underpowered systems trying to handle increased demand.<br><br>- Aligns infrastructure investment with real performance needs by using detailed utilisation data rather than broad assumptions.<br><br>- Enhances user experience during peak times because services are less likely to slow down or fail when many people use them at once.<br><br> | **Upper bound:** Minutes in decline months attributed to saturation. | Declines can indicate load stress patterns. |
| Owner scorecards | **Phase 1:** Publish simple scorecards that show monthly changes in uptime for each service by named owner so that trends and accountability are transparent.<br><br>**Phase 2:** Recognise owners whose services improve and coach those whose services are consistently degrading so that support and expectations are balanced.<br><br>**Phase 3:** Refresh goals and targets each quarter to keep owners focused on continuing improvements rather than only short bursts of activity. | - Encourages service owners to treat reliability as an ongoing responsibility rather than a one-time project.<br><br>- Helps leadership understand which parts of the organisation are driving positive change and which need more support or intervention.<br><br>- Supports a culture where improvements are measured and celebrated across the portfolio, not just within isolated teams.<br><br> | **Portfolio KPI:** count of risers vs fallers; **minutes saved** post-interventions. | Divergence/convergence trends visible. |
""",
                "satisfaction": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate wins from risers | **Phase 1:** When services like **{most_imp_name}** show clear improvements, prepare short, non-technical summaries that explain what changed and how it helped users.<br><br>**Phase 2:** Share these stories in customer meetings, newsletters or portals so that clients see evidence of progress rather than only hearing about issues.<br><br>**Phase 3:** Track satisfaction scores and qualitative comments after these communications to understand how well the good news is landing. | - Builds confidence among users that reliability is moving in the right direction and that problems are being actively addressed.<br><br>- Balances the narrative so that stakeholders hear about improvements as well as outages, which supports more realistic expectations.<br><br>- Helps account managers and service owners demonstrate value and justify ongoing investment in reliability improvements.<br><br> | **CSAT uplift:** survey delta post-communication (month over month). | Riser line demonstrates real improvement. |
| Honest roadmap for fallers | **Phase 1:** For faller services such as **{most_deg_name}**, acknowledge the decline openly in simple language and describe the main user impacts without hiding the issues.<br><br>**Phase 2:** Present a clear and time-bound recovery plan, including technical actions and expected milestones, so that users know what will change and when.<br><br>**Phase 3:** Provide regular updates against this plan and adjust the roadmap transparently if new findings appear. | - Reduces frustration and rumours because users feel that problems are recognised and taken seriously rather than ignored or minimised.<br><br>- Preserves credibility with customers, even when performance is temporarily poor, because communication is honest and forward-looking.<br><br>- Keeps affected users productive by giving them realistic expectations and, where possible, documented workarounds to manage through the degradation period.<br><br> | **Escalations avoided × handling cost**; **deflected tickets** via workarounds. | Fall line shows visible degradation. |
| Prioritized support channels | **Phase 1:** For services that are degrading, set up specialist support lanes or SME queues that directly handle cases from the most affected user groups.<br><br>**Phase 2:** Publish FAQs and quick guidance for these users so that simple questions and issues can be resolved without waiting in general queues.<br><br>**Phase 3:** Collect feedback on these channels and refine the scope or staffing if some users still feel underserved. | - Helps high value or heavily impacted users get faster help during periods when service stability is weaker than usual.<br><br>- Reduces noise in general support channels because many targeted questions are handled in specialised lanes or via self-help content.<br><br>- Protects overall satisfaction and productivity for critical users while reliability work is still in progress behind the scenes.<br><br> | **Benefit:** deflected tickets × handling cost; **time-to-resolution** improvement. | Degradation correlates with user pain. |
| Transparent release notes | **Phase 1:** For changes that affect availability, publish short release notes that link incidents and visible behaviour to specific changes in plain business language.<br><br>**Phase 2:** When issues occur, explain what remediation has been applied and what additional safeguards will be in place for future releases.<br><br>**Phase 3:** Commit follow-up actions in writing and close the loop once those actions are delivered and observed in the trend. | - Improves transparency by clearly connecting reliability events with the change pipeline, which users often suspect but cannot see.<br><br>- Reduces speculation and blame cycles because there is a documented explanation of what happened and what is being done to prevent recurrence.<br><br>- Supports stronger long-term relationships with customers who value openness and structured learning from mistakes.<br><br> | **Retention value:** churn risk reduction after notes. | Drops often follow release events; transparency helps. |
| Celebrate recoveries | **Phase 1:** When a previously degrading service returns to stable or improving uptime, formally communicate this recovery and highlight the key fixes that made it possible.<br><br>**Phase 2:** Thank affected users for their patience and explain how the improvements will change their day-to-day experience going forward.<br><br>**Phase 3:** Set the next reliability target for that service so that the team remains focused on continuous improvement instead of slipping back. | - Closes the narrative loop for users who experienced pain, showing that their issues have led to concrete action and results.<br><br>- Encourages adoption and confidence in the recovered service because people understand that it is now safer to rely on it again.<br><br>- Reinforces good operational behaviours and motivates teams to keep investing in reliability rather than treating the recovery as the final goal.<br><br> | **Qualitative:** CSAT trend improvement post-recovery. | Line rebounds validate actions. |
"""
            }

            render_cio_tables("CIO – Comparative Trend Analysis", cio_4b)
        else:
            st.warning(f"⚠️ Missing required columns: {required - set(df.columns)}")
