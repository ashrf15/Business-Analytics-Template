import streamlit as st
import pandas as pd
import plotly.express as px

BLUE_TONES = [
    "#004C99",  # deep brand navy
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]
px.defaults.template = "plotly_white"

# 🔹 Helper to render CIO tables
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def response_and_resolution_times(df_filtered):
    # ---------------------- 3a ----------------------
    with st.expander("📌 Average Response Time"):
        if "response_time_elapsed" in df_filtered.columns:
            df_filtered["response_hours"] = pd.to_timedelta(
                df_filtered["response_time_elapsed"], errors="coerce"
            ).dt.total_seconds() / 3600
        elif {"created_time", "responded_date"} <= set(df_filtered.columns):
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            df_filtered["responded_date"] = pd.to_datetime(df_filtered["responded_date"], errors="coerce")
            df_filtered["response_hours"] = (
                df_filtered["responded_date"] - df_filtered["created_time"]
            ).dt.total_seconds() / 3600
        else:
            df_filtered["response_hours"] = None

        r = df_filtered["response_hours"].dropna()

        if not r.empty:
            fig = px.histogram(
                df_filtered,
                x="response_hours",
                nbins=30,
                title="Response Time Distribution (hours)",
                color_discrete_sequence=BLUE_TONES
            )
            st.plotly_chart(fig, use_container_width=True)

            mean_val = float(r.mean())
            median_val = float(r.median())
            p90_val = float(r.quantile(0.9))
            max_val = float(r.max())
            count_total = int(r.shape[0])
            p90_cases = int((r >= p90_val).sum())
            sub_median_cases = int((r <= median_val).sum())

            # --- Analysis ---
            st.markdown("### Analysis")
            st.write(f"""
**What this graph is:** A histogram showing **first-response time** distribution.  
- **X-axis:** Response time in hours.  
- **Y-axis:** Count of incidents within each time bucket.

**What it shows in your data:** Median response is **{median_val:.2f}h**, with **p90 = {p90_val:.2f}h** and a maximum outlier at **{max_val:.2f}h**.  
The mean sits at **{mean_val:.2f}h**, indicating a **right-tailed** pattern driven by slow-response outliers.

Overall, a taller cluster near zero shows **fast acknowledgements**, while a long tail flags **coverage gaps and manual bottlenecks**.

**How to read it operationally:**  
1) **Peaks:** Lock in practices that created fast-response clusters (auto-ack, triage macros).  
2) **Plateaus:** Maintain stable coverage and queue hygiene to hold performance.  
3) **Downswings:** Attack tail drivers (off-hours, handoffs, missing runbooks).  
4) **Mix:** Pair with **submission time** and **priority** to ensure urgent items aren’t stuck in the tail.

**Why this matters:** Slow first responses trigger **dissatisfaction and early escalations**. Compressing the tail preserves **cost, performance, and trust**.
            """)

            # --- CIO (≥3 recs, phased explanations, expanded benefits, data-driven Cost/Evidence) ---
            cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Auto-acknowledgment for all tickets | **Phase 1 – Configure:** We enable a system generated first reply at ticket creation so every user receives an immediate acknowledgement even during peak periods or off hours. <br><br> **Phase 2 – Personalize:** We tailor templates by priority and category so the message feels relevant and includes the exact next steps the user can take right now. <br><br> **Phase 3 – Govern:** We set up bounce back monitoring and failure alerts so any delivery issues are caught and fixed quickly which prevents silent drops. | - It shifts manual first touch minutes to near zero for routine cases which lowers effort on high volume days. <br><br> - It protects user confidence during spikes because people see instant acknowledgement even when analysts are busy. <br><br> - It compresses the left side cluster and keeps the team focused on complex work instead of typing acknowledgements. | **Hours saved** ≈ (mean−median) × total = ({mean_val:.2f}−{median_val:.2f}) × {count_total} = **{(mean_val-median_val)*count_total:.2f} h** (compressing mean toward median). | Mean **{mean_val:.2f}h** > median **{median_val:.2f}h** (right-tail) indicates automation headroom toward ≤{median_val:.2f}h cluster. |
| Chatbot triage for repetitive requests | **Phase 1 – Identify:** We mine historical responses to find regex and keyword clusters that repeatedly trigger the same clarifying questions or steps. <br><br> **Phase 2 – Build:** We implement guided flows that either resolve simple issues or collect structured details to enrich tickets for faster human handling. <br><br> **Phase 3 – Deflect:** We measure deflection rates and accuracy so the bot handles the right scope and hands off gracefully when confidence is low. | - It deflects low value analyst touches so more capacity is available for incidents that need expertise. <br><br> - It stabilizes average response during off hours because the bot operates continuously without waiting for staff. <br><br> - It reduces the tail because enriched tickets start with complete context which shortens back and forth. | **Hours saved** ≈ (p90−median) × p90_cases = ({p90_val:.2f}−{median_val:.2f}) × {p90_cases} = **{(p90_val-median_val)*p90_cases:.2f} h** (pulling tail toward median). | Tail cohort size **{p90_cases}** at **≥{p90_val:.2f}h** are prime deflection targets. |
| Align staffing to peak hours | **Phase 1 – Analyze:** We compare response timestamps against submission patterns to expose off hour and day of week gaps that slow first touch. <br><br> **Phase 2 – Schedule:** We adjust shift starts and overlaps so a responder is always available when demand peaks. <br><br> **Phase 3 – Review:** We inspect weekly changes in mean versus median and iterate the schedule until the tail shrinks and stability holds. | - It reduces overtime spikes because coverage exists at the right moments instead of after queues form. <br><br> - It narrows the tail without over staffing normal hours because capacity is placed where it is needed. <br><br> - It improves SLA stability which reduces escalations from impatient users. | **OT avoided (h)** ≈ (p90−median) × p90_cases = ({p90_val:.2f}−{median_val:.2f}) × {p90_cases} = **{(p90_val-median_val)*p90_cases:.2f} h**. | Right-tail gap from median **{median_val:.2f}h** to p90 **{p90_val:.2f}h** evidences off-hour drag. |
| Triage macros for frequent categories | **Phase 1 – Template:** We write short targeted replies and diagnostic questions for the top repeating categories so analysts can respond in one click. <br><br> **Phase 2 – Embed:** We add these macros into the console with variables so messages fill correctly without copy and paste. <br><br> **Phase 3 – QA:** We audit macro usage and outcomes to retire ineffective text and amplify the ones that speed resolution. | - It removes typing and decision overhead for common scenarios which increases throughput at the same headcount. <br><br> - It keeps tone and instructions consistent which reduces confusion and follow up questions. <br><br> - It smooths daily variability because early replies are standardized and fast. | **Hours saved** ≈ sub_median_cases × micro_saving_h = **{sub_median_cases} × micro_saving_h** (measure in pilot). | Dense cluster near low hours (≤{median_val:.2f}h) indicates many cases fit templated replies. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| SLA-aware response prioritization | **Phase 1 – Compute:** We calculate time remaining to the response SLA for every ticket and create a simple urgency score that blends time risk with complexity. <br><br> **Phase 2 – Queue:** We present a dynamic top of list so analysts always see the items that most need a fast first touch. <br><br> **Phase 3 – Escalate:** We trigger pre breach actions to avoid late first responses when the timer is almost consumed. | - It raises on time responses because attention is consistently directed to the highest risk items. <br><br> - It collapses the nearly late tail which protects downstream resolution work from starting too late. <br><br> - It delivers steadier output because the team is guided by a clear and simple rule. | **Hours saved** ≈ (p90−median) × p90_cases = ({p90_val:.2f}−{median_val:.2f}) × {p90_cases} = **{(p90_val-median_val)*p90_cases:.2f} h**. | Tail cohort size **{p90_cases}** and tail height **{p90_val:.2f}h** justify urgency-based routing. |
| Follow-the-sun coverage | **Phase 1 – Map:** We identify time zones and teams that can receive handoffs so responses continue while one region sleeps. <br><br> **Phase 2 – Extend:** We formalize regional handoffs with clear acceptance windows and communication protocols. <br><br> **Phase 3 – Calibrate:** We track the length of the tail month over month and tune the split as demand shifts. | - It smooths global response times because someone is always online to answer. <br><br> - It reduces overnight lags which improves user experience across regions. <br><br> - It increases SLA compliance without needing heavy overtime in a single region. | **Hours saved** ≈ (mean−median) × total = ({mean_val:.2f}−{median_val:.2f}) × {count_total} = **{(mean_val-median_val)*count_total:.2f} h**. | Mean **{mean_val:.2f}h** > median **{median_val:.2f}h** indicates timezone and coverage imbalance. |
| Real-time response monitor | **Phase 1 – Alert:** We set thresholds for tail growth and issue alerts when the distribution shifts right so leaders can intervene. <br><br> **Phase 2 – Act:** We reassign items or trigger surge coverage so waiting tickets receive a quick first touch. <br><br> **Phase 3 – Learn:** We annotate root causes such as events or outages so the team can prevent repeats. | - It enables earlier corrections so small delays do not become long tails that are expensive to recover. <br><br> - It reduces outliers and breaches which keeps the histogram compact and predictable. <br><br> - It strengthens operational control because signals are acted on in the same day. | **Hours saved** ≈ alerts_triggered × average_overtime_avoided_h (quantify in pilot). | Variance across histogram buckets shows uncontrolled drift on some days. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Proactive first-contact messages | **Phase 1 – Draft:** We prepare short messages that set expectations and propose the next action the user can take while waiting. <br><br> **Phase 2 – Target:** We send these messages to tickets at risk of entering the tail so anxiety is reduced early. <br><br> **Phase 3 – Measure:** We track inquiry rate drop to confirm that the messages reduce follow ups. | - It cuts follow up contacts because users receive useful guidance before they ask. <br><br> - It reduces escalations because people feel informed and see that work has started. <br><br> - It protects sentiment during busy periods because communication is timely and clear. | **Hours saved** ≈ (follow-ups_avoided × handling_min/60) focused on p90 cohort (**{p90_cases}**). | Tail wait ≥ p90 **{p90_val:.2f}h** correlates with inquiry bursts. |
| Transparent response SLAs | **Phase 1 – Publish:** We publish response targets by type and priority so expectations are clear from the start. <br><br> **Phase 2 – Track:** We show promise versus actual so gaps are visible and can be corrected. <br><br> **Phase 3 – Iterate:** We adjust targets that are unrealistic so confidence is not eroded by missed promises. | - It reduces expectation mismatch complaints because people know the standard and see progress. <br><br> - It builds trust through transparency which is valued when delays happen. <br><br> - It helps managers plan because timelines are predictable and visible. | **Value (h)** ≈ (complaints_avoided × handling_min/60). | Wide spread (mean {mean_val:.2f}h vs median {median_val:.2f}h) shows expectation risk. |
| VIP response lanes | **Phase 1 – Tag:** We mark VIPs and critical accounts so their tickets get an immediate first touch. <br><br> **Phase 2 – Route:** We route VIP tickets to senior responders with clear timers and checkpoints. <br><br> **Phase 3 – Report:** We track VIP SLA deltas to prove value and adjust the policy. | - It prevents high impact escalations from key customers which protects relationships and revenue. <br><br> - It demonstrates control to leadership because sensitive cases move quickly. <br><br> - It reduces noise on command channels because fewer executive follow ups are needed. | **Penalty avoided** = vip_breaches_prevented × penalty_per_breach. | VIPs are disproportionately harmed by outliers up to **{max_val:.2f}h**. |
"""
            }
            render_cio_tables("Response Time", cio)
        else:
            st.info("Cannot compute response time from available data.")

    # ---------------------- 3b ----------------------
    with st.expander("📌 Average Resolution Time"):
        if "time_elapsed" in df_filtered.columns:
            df_filtered["resolution_hours"] = pd.to_timedelta(
                df_filtered["time_elapsed"], errors="coerce"
            ).dt.total_seconds() / 3600
        elif {"created_time", "resolved_time"} <= set(df_filtered.columns):
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            df_filtered["resolved_time"] = pd.to_datetime(df_filtered["resolved_time"], errors="coerce")
            df_filtered["resolution_hours"] = (
                df_filtered["resolved_time"] - df_filtered["created_time"]
            ).dt.total_seconds() / 3600
        else:
            df_filtered["resolution_hours"] = None

        r = df_filtered["resolution_hours"].dropna()

        if not r.empty:
            fig = px.box(
                df_filtered,
                y="resolution_hours",
                points="outliers",
                title="Resolution Time (hours) – Variation",
                color_discrete_sequence=BLUE_TONES
            )
            st.plotly_chart(fig, use_container_width=True)

            mean_val = float(r.mean())
            median_val = float(r.median())
            p90_val = float(r.quantile(0.9))
            max_val = float(r.max())
            count_total = int(r.shape[0])
            p90_cases = int((r >= p90_val).sum())

            # --- Analysis ---
            st.markdown("### Analysis")
            st.write(f"""
**What this graph is:** A box plot showing **end-to-end resolution times**.  
- **X-axis:** (single series).  
- **Y-axis:** Resolution time in hours (distribution with outliers).

**What it shows in your data:** Median resolution is **{median_val:.2f}h**, **p90 = {p90_val:.2f}h**, and the maximum outlier reaches **{max_val:.2f}h**.  
The mean sits at **{mean_val:.2f}h**, with visible spread and outliers driving the right tail.

Overall, a taller box/long whiskers indicate **process variability**, while distant points signal **exception cases** that inflate SLA risk.

**How to read it operationally:**  
1) **Peaks:** Codify what enabled fast resolutions (templates, runbooks, owner continuity).  
2) **Plateaus:** Hold steady-state practices that keep variability contained.  
3) **Downswings:** Target outlier drivers (handoffs, vendor waits, missing diagnostics).  
4) **Mix:** Pair with **category/priority/age** to isolate chronic slow lanes.

**Why this matters:** Long tails are **expensive**—they cause **breaches, escalations, and rework**. Compressing variance protects **cost, performance, and satisfaction**.
            """)

            # --- CIO (≥3 recs, phased explanations, expanded benefits, data-driven Cost/Evidence) ---
            cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Standardize resolution workflows | **Phase 1 – Codify:** We define golden path steps for the highest volume categories so analysts know the exact sequence that works. <br><br> **Phase 2 – Embed:** We add checklists and prefilled fields in the console so required data is captured correctly without backtracking. <br><br> **Phase 3 – Assure:** We run weekly quality checks on exceptions to keep the workflow lean as systems and products change. | - It cuts rework because missing or wrong steps are eliminated which shortens total handling time. <br><br> - It reduces handoffs because the path is clear which lowers delays and confusion. <br><br> - It stabilizes unit cost per ticket which makes planning and staffing more accurate. | **Hours saved** ≈ (mean−median) × total = ({mean_val:.2f}−{median_val:.2f}) × {count_total} = **{(mean_val-median_val)*count_total:.2f} h**. | Mean **{mean_val:.2f}h** > median **{median_val:.2f}h** and long whiskers or outliers show inefficiency spread. |
| Automate repetitive fixes | **Phase 1 – Detect:** We isolate frequent low complexity patterns that are safe to automate end to end or with guided steps. <br><br> **Phase 2 – Script:** We implement self healing or runbooks that execute the fix with guardrails to prevent errors. <br><br> **Phase 3 – Guard:** We monitor fallbacks and quality so automation scope grows safely over time. | - It offloads routine labor which frees engineers to focus on complex and high value work. <br><br> - It compresses the right tail because slow repeats are removed from the human queue. <br><br> - It reduces breach exposure because long cases are less likely to come from repetitive patterns. | **Hours saved** ≈ (p90−median) × p90_cases = ({p90_val:.2f}−{median_val:.2f}) × {p90_cases} = **{(p90_val-median_val)*p90_cases:.2f} h**. | p90 **{p90_val:.2f}h** with **{p90_cases}** tickets marks the slow cohort. |
| Knowledge base integration | **Phase 1 – Curate:** We collect proven fixes with diagnostics and prerequisites so analysts can follow a reliable recipe. <br><br> **Phase 2 – Surface:** We enable context aware search in the agent console so the right article appears without leaving the ticket. <br><br> **Phase 3 – Iterate:** We track article usage and time to resolve so content improves where it matters. | - It accelerates first time fix because guidance is available at the exact moment it is needed. <br><br> - It lowers spread across analysts which creates more predictable outcomes. <br><br> - It reduces escalations and rework because steps are complete and verified. | **Hours saved** ≈ (Δhours_per_ticket × adoption_rate × {count_total}). | Wide IQR and whiskers show uneven knowledge reuse across agents. |
| Owner continuity on long cases | **Phase 1 – Flag:** We detect items with many handoffs that risk context loss and delays. <br><br> **Phase 2 – Assign:** We assign a single owner who remains accountable from investigation to closure. <br><br> **Phase 3 – Track:** We measure handoffs and time deltas so the continuity model is tuned. | - It reduces context loss so progress is faster and fewer loops occur. <br><br> - It lowers reopen rates because one person ensures quality before closure. <br><br> - It tightens p90 and maximum durations which protects SLA and reputation. | **Hours saved** ≈ (handoffs_avoided × mins_per_handoff/60) on p90 set (**{p90_cases}**). | Outliers to **{max_val:.2f}h** often correlate with multi handoffs. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Fast-lane for simple tickets | **Phase 1 – Define:** We set clear simplicity rules so easy items bypass deep queues. <br><br> **Phase 2 – Route:** We auto route qualifying items to a quick resolution lane with the right skills. <br><br> **Phase 3 – Audit:** We check misroutes and refine rules so the lane remains accurate. | - It increases throughput because easy work does not wait behind complex cases. <br><br> - It prevents simple items from inflating averages which keeps medians tight. <br><br> - It holds daily output steady because short wins are delivered continuously. | **Hours saved** ≈ (Δhours_simple × simple_volume). | Outliers arise from mixing simple with complex in the same queue which the spread reveals. |
| Swarm complex incidents | **Phase 1 – Trigger:** We use the p90 threshold of **{p90_val:.2f}h** to trigger a short multi skill swarm for cases trending long. <br><br> **Phase 2 – Mobilize:** We bring the right expertise together at once so blockers are removed in one session. <br><br> **Phase 3 – Close:** We capture the fix in a brief post mortem so similar cases complete faster next time. | - It shrinks the extreme tail which reduces breach risk on hard cases. <br><br> - It increases predictability because complex items receive decisive attention. <br><br> - It accelerates learning because knowledge is captured while the context is fresh. | **Hours saved** ≈ ({p90_val:.2f}−target_p90) × {p90_cases}. | Median {median_val:.2f}h vs p90 {p90_val:.2f}h shows a tail gap that needs intervention. |
| Real-time aging monitor | **Phase 1 – Surface:** We highlight near breach and aging items in a live view so owners see risk early. <br><br> **Phase 2 – Escalate:** We nudge vendors and approvals with templates that include impact and deadlines. <br><br> **Phase 3 – Measure:** We track breach rate and recovery speed to ensure the monitor drives action. | - It raises SLA hit rate because attention arrives before the clock expires. <br><br> - It reduces firefighting because recoveries start earlier in the day. <br><br> - It smooths weekly flow because age is kept under control. | **Penalty avoided** = breaches_prevented × penalty_per_breach. | Outliers up to **{max_val:.2f}h** indicate aging blind spots. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Milestone updates for long cases | **Phase 1 – Define:** We set clear checkpoints such as triage fix and verify and decide when each triggers an update. <br><br> **Phase 2 – Notify:** We send ETA and status at milestones so users see visible progress. <br><br> **Phase 3 – Review:** We monitor inquiry drop to confirm that updates reduce uncertainty. | - It lowers follow up contacts because users receive timely information without asking. <br><br> - It reduces complaint volume because expectations are managed transparently. <br><br> - It builds trust because communication is consistent during lengthy work. | **Hours saved** ≈ (inquiries_avoided × handling_min/60) concentrated in p90 cohort (**{p90_cases}**). | Tail beyond **{p90_val:.2f}h** is where inquiries concentrate. |
| Publish realistic ETAs | **Phase 1 – Set:** We derive ETAs from the median of **{median_val:.2f}h** per type so promises match typical performance. <br><br> **Phase 2 – Track:** We compare promise with actual and show the variance so teams see where to improve. <br><br> **Phase 3 – Adjust:** We tune ETAs and processes that repeatedly misfire so promises remain credible. | - It cuts disappointment from over promising which protects satisfaction scores. <br><br> - It improves perceived reliability because timelines are grounded in data. <br><br> - It helps managers plan around realistic delivery windows. | **Value (h)** ≈ (complaints_avoided × handling_min/60). | Gap mean {mean_val:.2f}h to median {median_val:.2f}h shows the risk of optimistic ETAs. |
| VIP prioritization | **Phase 1 – Tag:** We identify high impact customers and services that require accelerated handling. <br><br> **Phase 2 – Route:** We route VIP items to senior owners with fast checkpoints and clear escalation paths. <br><br> **Phase 3 – Report:** We monitor VIP breach deltas to ensure the policy delivers measurable benefit. | - It prevents high cost escalations and churn by resolving critical issues faster. <br><br> - It preserves relationships and revenue because sensitive work receives priority. <br><br> - It demonstrates control to key stakeholders which reduces unplanned pressure. | **Penalty avoided** = vip_breaches_prevented × penalty_per_breach. | Extreme outliers **{max_val:.2f}h** pose VIP reputation risk. |
"""
}
            render_cio_tables("Resolution Time", cio)
        else:
            st.info("No resolution durations derivable from available data.")

    # ---------------------- 3c ----------------------
    with st.expander("📌 SLA Adherence"):
        sla_frames = []

        # Response SLA
        if {"sla_response_time", "responded_date", "created_time"} <= set(df_filtered.columns):
            df_filtered["sla_response_hours"] = pd.to_timedelta(
                df_filtered["sla_response_time"], errors="coerce"
            ).dt.total_seconds() / 3600
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            df_filtered["responded_date"] = pd.to_datetime(df_filtered["responded_date"], errors="coerce")
            df_filtered["response_hours"] = (
                df_filtered["responded_date"] - df_filtered["created_time"]
            ).dt.total_seconds() / 3600
            valid_resp = df_filtered.dropna(subset=["response_hours", "sla_response_hours"])
            if not valid_resp.empty:
                resp_pct = float((valid_resp["response_hours"] <= valid_resp["sla_response_hours"]).mean() * 100)
                sla_frames.append(("Response SLA %", round(resp_pct, 1)))
        else:
            valid_resp = pd.DataFrame()

        # Resolution SLA
        if {"sla_resolution_time", "resolved_time", "created_time"} <= set(df_filtered.columns):
            df_filtered["sla_resolution_hours"] = pd.to_timedelta(
                df_filtered["sla_resolution_time"], errors="coerce"
            ).dt.total_seconds() / 3600
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            df_filtered["resolved_time"] = pd.to_datetime(df_filtered["resolved_time"], errors="coerce")
            df_filtered["resolution_hours"] = (
                df_filtered["resolved_time"] - df_filtered["created_time"]
            ).dt.total_seconds() / 3600
            valid_res = df_filtered.dropna(subset=["resolution_hours", "sla_resolution_hours"])
            if not valid_res.empty:
                res_pct = float((valid_res["resolution_hours"] <= valid_res["sla_resolution_hours"]).mean() * 100)
                sla_frames.append(("Resolution SLA %", round(res_pct, 1)))
        else:
            valid_res = pd.DataFrame()

        if sla_frames:
            sla_df = pd.DataFrame(sla_frames, columns=["Metric", "Percent"])
            fig = px.bar(
                sla_df,
                x="Metric",
                y="Percent",
                title="SLA Adherence (%)",
                text="Percent",
                range_y=[0, 100],
                color_discrete_sequence=BLUE_TONES
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # --- Analysis ---
            st.markdown("### Analysis of SLA Adherence (%)")
            for m, p in sla_frames:
                st.write(f"""
**What this graph is:** A KPI bar showing **{m}** adherence.  
- **X-axis:** SLA metric type.  
- **Y-axis:** Percentage of tickets meeting SLA (0–100%).

**What it shows in your data:** **{m} = {p:.1f}%** of tickets met the defined target.  
Values near 100% indicate **strong control**; materially lower values indicate **chronic breach risk**.

Overall, higher bars reflect **predictable delivery**, while shorter bars expose **timing and capacity gaps**.

**How to read it operationally:**  
1) **Peaks:** Capture and standardize practices from high-performing metrics.  
2) **Plateaus:** Maintain guardrails and monitor for drift below target.  
3) **Downswings:** Add surge capacity, tighten routing, and deploy early-warning alerts.  
4) **Mix:** Compare **response vs resolution** to isolate whether delays happen **upfront** or **during fix**.

**Why this matters:** SLA is the **contractual heartbeat**. Falling short drives **penalties, rework, and dissatisfaction**; sustaining high adherence preserves **cost, performance, and trust**.
                """)

            # Compute breach metrics for Cost/Evidence
            if not valid_resp.empty:
                resp_total = int(valid_resp.shape[0])
                resp_breaches = int((valid_resp["response_hours"] > valid_resp["sla_response_hours"]).sum())
                resp_overage_avg = float(
                    (valid_resp.loc[valid_resp["response_hours"] > valid_resp["sla_response_hours"], "response_hours"]
                     - valid_resp.loc[valid_resp["response_hours"] > valid_resp["sla_response_hours"], "sla_response_hours"]).mean()
                ) if resp_breaches else 0.0
                resp_pct_val = float((valid_resp["response_hours"] <= valid_resp["sla_response_hours"]).mean() * 100)
            else:
                resp_total = resp_breaches = 0
                resp_overage_avg = 0.0
                resp_pct_val = 0.0

            if not valid_res.empty:
                res_total = int(valid_res.shape[0])
                res_breaches = int((valid_res["resolution_hours"] > valid_res["sla_resolution_hours"]).sum())
                res_overage_avg = float(
                    (valid_res.loc[valid_res["resolution_hours"] > valid_res["sla_resolution_hours"], "resolution_hours"]
                     - valid_res.loc[valid_res["resolution_hours"] > valid_res["sla_resolution_hours"], "sla_resolution_hours"]).mean()
                ) if res_breaches else 0.0
                res_pct_val = float((valid_res["resolution_hours"] <= valid_res["sla_resolution_hours"]).mean() * 100)
            else:
                res_total = res_breaches = 0
                res_overage_avg = 0.0
                res_pct_val = 0.0

            # --- CIO (≥3 recs, phased explanations, expanded benefits, data-driven Cost/Evidence) ---
            cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Early SLA alerts at 50% time used | **Phase 1 – Instrument:** We create timers at 50 70 and 90 percent of the SLA so risk is visible before the final minutes. <br><br> **Phase 2 – Route:** We automatically bubble at risk items to available owners so someone with capacity can act. <br><br> **Phase 3 – Resolve:** We escalate blockers early to vendors or approvers so the clock does not expire while waiting. | - It prevents last minute scrambles that cause costly breaches and overtime. <br><br> - It smooths daily workload because risk is handled steadily instead of in end of day bursts. <br><br> - It reduces penalties and rework because tickets are handled within the window more consistently. | **Penalty avoided** ≈ (breaches_prevented_resp × penalty_per_breach) + (breaches_prevented_res × penalty_per_breach). Current breaches: response **{resp_breaches}**, resolution **{res_breaches}**. | Bars show Response SLA **{resp_pct_val:.1f}%** ({resp_breaches}/{resp_total} breaches) and Resolution SLA **{res_pct_val:.1f}%** ({res_breaches}/{res_total} breaches). |
| Targeted process improvement by category | **Phase 1 – Pinpoint:** We identify the categories that contribute the most to SLA misses so work focuses where returns are highest. <br><br> **Phase 2 – Fix:** We update runbooks or tighten vendor SLAs and remove steps that cause recurring waiting time. <br><br> **Phase 3 – Verify:** We track weekly breach trends to confirm the changes reduce misses and sustain gains. | - It lowers repeat breaches because the root causes in the worst categories are addressed directly. <br><br> - It reduces rework and fire drill labor which cuts hidden costs that do not create value. <br><br> - It improves predictability and stakeholder confidence because metrics move in the right direction and stay there. | **Hours saved** ≈ (resp_breaches × {resp_overage_avg:.2f} h) + (res_breaches × {res_overage_avg:.2f} h) = **{resp_breaches*resp_overage_avg + res_breaches*res_overage_avg:.2f} h**. | Average overage on breached cases: Response **{resp_overage_avg:.2f}h**, Resolution **{res_overage_avg:.2f}h**. |
| Optimize staffing during SLA crunch periods | **Phase 1 – Detect:** We locate times of day and week when breaches spike so staffing gaps are explicit. <br><br> **Phase 2 – Staff:** We add short overlapping shifts in those windows so tickets move before timers expire. <br><br> **Phase 3 – Tune:** We rebalance monthly as patterns change so coverage remains efficient. | - It reduces overtime and breaches because capacity exists when clocks are tight. <br><br> - It keeps adherence steady across days so peaks do not cause avoidable misses. <br><br> - It improves queue predictability which helps leaders manage commitments. | **OT avoided (h)** ≈ (resp_breaches × {resp_overage_avg:.2f}) + (res_breaches × {res_overage_avg:.2f}) = **{resp_breaches*resp_overage_avg + res_breaches*res_overage_avg:.2f} h**. | Breach counts: Resp **{resp_breaches}/{resp_total}**, Res **{res_breaches}/{res_total}**; overages indicate crunch windows. |
| Pre-emptive vendor escalations | **Phase 1 – Threshold:** We escalate when vendor waiting time threatens the SLA so delays are confronted early. <br><br> **Phase 2 – Contracts:** We ensure contracts include clocks for vendor responses so accountability is clear. <br><br> **Phase 3 – Audit:** We run vendor scorecards so slow partners improve or the work is reassigned. | - It lowers external waiting time which directly reduces resolution misses. <br><br> - It decreases penalty exposure when third parties contribute to delay. <br><br> - It improves overall control because dependencies are actively managed. | **Penalty avoided** = vendor_breaches_prevented × penalty_per_breach. | Resolution SLA **{res_pct_val:.1f}%** < 100% suggests vendor and prerequisite risks. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| SLA-aware ticket routing | **Phase 1 – Score:** We compute an urgency score that divides remaining SLA time by estimated complexity so the most at risk items surface first. <br><br> **Phase 2 – Queue:** We always sort by this score so agents work the right item next. <br><br> **Phase 3 – Inspect:** We track reassignment rate and fix patterns that cause misroutes. | - It raises adherence because work order matches risk instead of arrival time. <br><br> - It reduces last minute chaos which stabilizes performance across shifts. <br><br> - It improves flow because the queue is always prioritized by impact. | **Hours saved** ≈ (resp_breaches × {resp_overage_avg:.2f}) + (res_breaches × {res_overage_avg:.2f}) = **{resp_breaches*resp_overage_avg + res_breaches*res_overage_avg:.2f} h**. | Evidence: current breach overages Response **{resp_overage_avg:.2f}h**, Resolution **{res_overage_avg:.2f}h**. |
| Dynamic reallocation of staff | **Phase 1 – Signal:** We visualize a live queue heatmap so leaders see which queues are hot and which are cool. <br><br> **Phase 2 – Shift:** We reassign people from cool to hot queues in the same day which drains risk before breaches occur. <br><br> **Phase 3 – Review:** We compare weekly SLA lift to ensure the shifts produce measurable improvement. | - It smooths throughput without adding headcount because capacity is moved to where it matters. <br><br> - It reduces breaches by reacting to spikes in hours instead of days. <br><br> - It speeds recovery after events which keeps stakeholders calm. | **Hours saved** = (aging_drop × hrs/ticket) observed during reallocation weeks. | SLA bars quantify the gap and the reallocation aims to raise the lower bar toward 100 percent. |
| Track SLA adherence over time | **Phase 1 – Trend:** We track adherence by week and month so performance drift is visible early. <br><br> **Phase 2 – Trigger:** We set alerts when trends decline so counter measures start immediately. <br><br> **Phase 3 – Act:** We apply staffing or process changes and validate that the trend recovers. | - It detects problems while they are still small which makes fixes cheaper and faster. <br><br> - It maintains predictability by avoiding long periods of unobserved decline. <br><br> - It supports continuous improvement because changes are measured and sustained. | **Penalty avoided** = breaches_prevented × penalty_per_breach; breach baseline: Resp **{resp_breaches}**, Res **{res_breaches}**. | Persistent sub 100 percent bars indicate chronic drift that needs control. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Proactive SLA breach comms | **Phase 1 – Detect:** We watch pre breach signals and identify tickets likely to miss the target. <br><br> **Phase 2 – Notify:** We send a revised ETA with an apology and the next action so users understand the plan. <br><br> **Phase 3 – Measure:** We track changes in complaint rates to fine tune timing and content. | - It reduces complaints and escalations because communication happens before frustration peaks. <br><br> - It preserves trust during misses because users feel informed and respected. <br><br> - It speeds closure after breaches because expectations and next steps are clear. | **Hours saved** ≈ (complaints_avoided × handling_min/60) targeting breached cohorts (Resp **{resp_breaches}**, Res **{res_breaches}**). | Breach counts and overages (Resp **{resp_overage_avg:.2f}h**, Res **{res_overage_avg:.2f}h**) identify impacted users. |
| Transparent SLA dashboards | **Phase 1 – Publish:** We provide real time SLA views by queue so users and managers can see performance without opening a ticket. <br><br> **Phase 2 – Explain:** We include short guidance on what to expect and how priorities are handled which reduces uncertainty. <br><br> **Phase 3 – Learn:** We collect feedback and improve the dashboard so information remains useful. | - It reduces follow ups because status and trends are visible on demand. <br><br> - It increases perceived reliability because transparency shows control. <br><br> - It strengthens satisfaction because communication is self service and consistent. | **Hours saved** = inquiry_drop × handling_min/60 across breached queues. | SLA bars (Resp **{resp_pct_val:.1f}%**, Res **{res_pct_val:.1f}%**) show where transparency matters most. |
| Service credits for SLA misses | **Phase 1 – Define:** We set clear thresholds for automatic goodwill credits so outcomes are fair and fast. <br><br> **Phase 2 – Offer:** We apply credits automatically on qualifying misses which avoids long disputes and back and forth. <br><br> **Phase 3 – Track:** We monitor churn and complaints to verify that credits reduce friction more than they cost. | - It preserves loyalty because customers see tangible acknowledgement when service falls short. <br><br> - It reduces formal disputes and administrative time because compensation is clear and automatic. <br><br> - It speeds agreement on next steps which helps teams focus on restoring service. | **Cost trade-off** = credit_cost << churn and escalation cost; breaches baseline Resp **{resp_breaches}**, Res **{res_breaches}**. | Evidence of misses via SLA bars and overage metrics above. |
"""
}
            render_cio_tables("SLA Adherence", cio)
        else:
            st.info("No SLA fields available to compute adherence.")
