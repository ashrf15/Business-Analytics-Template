# ================================================================
# utils_scorecard/recommendation/service_desk_performance.py
# Target 6 – Service Desk Performance
# ================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ================================================================
# Helper Functions
# ================================================================

# Mesiniaga palette
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]
PRIMARY_BLUE = "#007ACC"

def _peak_low_df(df, date_col, val_col):
    """
    Returns dict with peak/low values for a numeric column grouped by date.
    Handles Timestamps safely.
    """
    try:
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
        clean_df = df.dropna(subset=[val_col, date_col])
        if clean_df.empty:
            return {"peak_val": None, "peak_date": None, "low_val": None, "low_date": None}

        peak_row = clean_df.loc[clean_df[val_col].idxmax()]
        low_row = clean_df.loc[clean_df[val_col].idxmin()]
        return {
            "peak_val": float(peak_row[val_col]),
            "peak_date": peak_row[date_col].strftime("%d/%m/%Y") if not pd.isna(peak_row[date_col]) else None,
            "low_val": float(low_row[val_col]),
            "low_date": low_row[date_col].strftime("%d/%m/%Y") if not pd.isna(low_row[date_col]) else None,
        }
    except Exception as e:
        st.warning(f"⚠️ Error in _peak_low_df for {val_col}: {e}")
        return {"peak_val": None, "peak_date": None, "low_val": None, "low_date": None}

def _fmt_int(x):
    try:
        return f"{int(round(float(x))):,}"
    except Exception:
        return "0"

def _fmt_float(x, d=2):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.00"

def render_cio_tables(title, cio_data):
    """Render CIO tables with Cost / Performance / Satisfaction sections"""
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# ================================================================
# Target 6 – Service Desk Performance
# ================================================================

def service_desk_performance(df_filtered: pd.DataFrame):

    # Normalize date
    if "report_date" in df_filtered.columns:
        df_filtered["report_date"] = pd.to_datetime(df_filtered["report_date"], errors="coerce")

    # ============================================================
    # 6a – Customer Satisfaction (Box Plot Version)
    # ============================================================
    with st.expander("📌 Customer Satisfaction Ratings"):
        if "customer_satisfaction" in df_filtered.columns and "report_date" in df_filtered.columns:
            df_filtered["month"] = (
                pd.to_datetime(df_filtered["report_date"], errors="coerce")
                .dt.to_period("M")
                .astype(str)
            )

            fig = px.box(
                df_filtered,
                x="month",
                y="customer_satisfaction",
                points="outliers",
                title="Distribution of Customer Satisfaction by Month",
                labels={"month": "Month", "customer_satisfaction": "Satisfaction (%)"},
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            fig.update_traces(marker_color=PRIMARY_BLUE, line_color=PRIMARY_BLUE)
            st.plotly_chart(fig, use_container_width=True)

            # --- Dynamic stats
            plot_df = df_filtered.dropna(subset=["customer_satisfaction", "report_date"]).copy()
            stats = _peak_low_df(plot_df, "report_date", "customer_satisfaction")
            mean_val = plot_df["customer_satisfaction"].mean() if not plot_df.empty else None
            spread = (stats["peak_val"] - stats["low_val"]) if stats["peak_val"] is not None and stats["low_val"] is not None else None

            # Monthly medians/IQR (for evidence and cost calcs)
            by_month = (
                plot_df.assign(month=plot_df["report_date"].dt.to_period("M").astype(str))
                .groupby("month")["customer_satisfaction"]
                .agg(["median", "mean", "count"])
                .reset_index()
            )
            iqr_list = []
            try:
                tmp = plot_df.assign(month=plot_df["report_date"].dt.to_period("M").astype(str))
                for m, g in tmp.groupby("month"):
                    q1 = np.nanpercentile(g["customer_satisfaction"], 25)
                    q3 = np.nanpercentile(g["customer_satisfaction"], 75)
                    iqr_list.append({"month": m, "q1": q1, "q3": q3, "iqr": q3 - q1})
                iqr_df = pd.DataFrame(iqr_list)
                if not iqr_df.empty:
                    worst_iqr = iqr_df.loc[iqr_df["iqr"].idxmax()]
                else:
                    worst_iqr = {"month": None, "iqr": None}
            except Exception:
                worst_iqr = {"month": None, "iqr": None}

            st.markdown("### Analysis – Customer Satisfaction Distribution")
            if stats["peak_val"] is not None:
                st.write(f"""
**What this graph is:** A monthly **box plot** showing the distribution of **customer satisfaction (%)**.  
**X-axis:** Calendar month.  
**Y-axis:** Satisfaction percentage across records in that month.

**What it shows in your data:**  
- **Highest recorded satisfaction:** **{_fmt_float(stats['peak_val'])}%** on **{stats['peak_date'] or 'N/A'}**.  
- **Lowest satisfaction:** **{_fmt_float(stats['low_val'])}%** on **{stats['low_date'] or 'N/A'}**.  
- **Average satisfaction:** **{_fmt_float(mean_val)}%**.  
- **Largest monthly variability (IQR):** **{_fmt_float(worst_iqr.get('iqr'))}%** in **{worst_iqr.get('month') or 'N/A'}** (wide box = uneven experience).

**Overall:** Wide boxes/outliers flag **inconsistent experience**; tight boxes imply **steady service quality**.

**How to read it operationally:**  
- **Gap targeting:** Months with the **widest IQR** need targeted fixes (process, knowledge, or staffing).  
- **Outlier triage:** Investigate extremely low outliers for **preventable failure modes**.  
- **Replication:** Mirror practices from months with **high median** and **tight spread**.

**Why this matters:** Reducing variability improves **predictability**, **trust**, and **retention**.
""")
            else:
                st.info("No valid satisfaction data found to compute distribution metrics.")

            # --- CIO tables
            ev_line = f"Peak CSAT **{_fmt_float(stats['peak_val'])}%** ({stats['peak_date'] or 'N/A'}) vs low **{_fmt_float(stats['low_val'])}%** ({stats['low_date'] or 'N/A'}); average **{_fmt_float(mean_val)}%**; widest IQR in **{(worst_iqr.get('month') or 'N/A')}** = **{_fmt_float(worst_iqr.get('iqr'))}%**."

            # EXPANDED EXPLANATIONS + BENEFITS BELOW
            cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **Automate survey collection & consolidation** | **Phase 1:** - Enable automatic survey sends immediately after ticket closure so responses arrive while the experience is fresh and response rates are higher.<br><br>- Configure templates that match the service type so the questions feel relevant and the data is easier to compare across months.<br><br>**Phase 2:** - Centralize all survey results into a single dataset so analysts do not waste time merging files and reconciling formats.<br><br>- Apply consistent data validation rules so bad entries are flagged and corrected before reporting cycles begin.<br><br>**Phase 3:** - De duplicate responses across email chat and portal so the signal is not inflated by multiple touches from the same user.<br><br>- Schedule automated loads into reporting so dashboards refresh without manual effort. | - Fewer manual hours are spent collecting and cleaning survey data which reduces recurring operational cost for every reporting cycle.<br><br>- Faster availability of results lets managers act on problems in the same month which prevents issues from compounding into the next cycle.<br><br>- Consistent formats reduce analyst rework and improve the accuracy of month to month comparisons which strengthens decision quality.<br><br>- A single trusted dataset simplifies audit and governance which reduces stress during reviews. | **Admin hours saved** = (manual mins/response × total responses in months with wide IQR **{worst_iqr.get('month') or 'N/A'}**). | {ev_line} |
| **Target low-CSAT outliers with playbooks** | **Phase 1:** - Detect monthly outliers using the box plot whiskers and mark the cases that sit furthest from the median so attention lands on the true experience failures.<br><br>- Categorize the outliers by cause so each playbook addresses a specific and repeatable issue rather than a vague theme.<br><br>**Phase 2:** - Run fix playbooks that include knowledge updates routing tweaks and agent coaching so the same pattern is less likely to reappear next month.<br><br>- Track the use of each playbook so adoption is visible and obstacles can be removed quickly.<br><br>**Phase 3:** - Re measure the same categories in the next cycle and verify that outliers have reduced so the intervention is validated.<br><br>- Iterate the playbooks that underperform so effectiveness increases over time. | - Focused playbooks cut rework because agents stop reinventing fixes for problems that have known solutions which saves minutes on every repeat case.<br><br>- Complaint handling time decreases because similar issues are solved more reliably at the first attempt which protects capacity in busy periods.<br><br>- Consistent improvements raise the floor of user experience which narrows the IQR and stabilizes monthly satisfaction results.<br><br>- Evidence based prioritization builds credibility with stakeholders which makes future changes easier to land. | **Rework mins avoided** = (# outlier cases × avg handling mins) in worst IQR month **{worst_iqr.get('month') or 'N/A'}**. | {ev_line} |
| **Shift QA sampling to high-variance months** | **Phase 1:** - Allocate a larger share of QA reviews to months that show the widest boxes so investigation time follows the biggest opportunity for stability.<br><br>- Define clear sampling rules so the team knows why their tickets were selected which improves cooperation.<br><br>**Phase 2:** - Run deep dive root cause analysis on the reviewed tickets so training and process changes are tied to observed evidence not opinion.<br><br>- Publish short findings with owners and deadlines so actions do not stall after discovery.<br><br>**Phase 3:** - Close corrective actions and confirm that the IQR tightens in subsequent months so the loop is proven end to end.<br><br>- Adjust sampling weights quarterly so QA remains pointed at the riskiest periods. | - Concentrating QA on the most volatile months delivers faster stability because the fixes target where users are most inconsistent in their experience.<br><br>- Clear findings reduce back and forth debate which speeds the adoption of improvements and lowers coordination time.<br><br>- Tightening variability reduces the number of low score surprises which protects brand trust with internal customers.<br><br>- A responsive QA plan uses the same headcount to achieve more impact which stretches budget further. | **QA ROI** = (CSAT uplift from variance cut × volume in **{worst_iqr.get('month') or 'N/A'}**). | {ev_line} |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **CSAT-to-agent drilldowns** | **Phase 1:** - Map CSAT to agent groups and queues so performance patterns are visible at a level where coaching can be specific and actionable.<br><br>- Align the cohort definitions to your roster so attribution is fair and comparable across weeks.<br><br>**Phase 2:** - Share practices from high median months and run shadowing sessions so habits that work are copied quickly across teams.<br><br>- Document the key moves in a simple checklist so the improvements persist when staff rotate.<br><br>**Phase 3:** - Coach lower performers with targeted goals and follow up on progress so support is practical and timely.<br><br>- Review outcomes at the end of each month so adjustments happen without delay. | - Pulling medians up improves the consistency of the user experience which reduces the spread of scores and strengthens the overall trend line.<br><br>- Codified good practices reduce variability across shifts which stabilizes operational throughput and improves SLA adherence.<br><br>- Targeted coaching improves outcomes without large investments in tooling which keeps the plan cost effective.<br><br>- Regular reviews prevent drift and keep teams focused on the behaviors that move the needles. | **Uplift mins saved** = (Δresolution mins × tickets in months below avg **{_fmt_float(mean_val)}%**). | {ev_line} |
| **Variance control via knowledge gating** | **Phase 1:** - Require a knowledge base link to close for the top categories so agents follow a proven path and reduce unnecessary experimentation on users.<br><br>- Make the rule visible in the tool so compliance is easy and reminders are automatic.<br><br>**Phase 2:** - Enforce a light review cadence for high traffic articles so accuracy stays high even as systems change through the quarter.<br><br>- Track article usage so owners know which content drives outcomes and where to invest time.<br><br>**Phase 3:** - Retire stale or duplicate articles so the library remains concise and search results are not cluttered.<br><br>- Promote the best performing content so the signal is reinforced. | - Gating reduces handling variability because agents follow the same validated steps which makes cycle times more predictable.<br><br>- Fresh articles prevent regressions after system changes which protects performance during release windows.<br><br>- A smaller cleaner library saves time searching which reduces average minutes per ticket and frustration for agents.<br><br>- Elevating proven content accelerates onboarding and reduces dependency on a few experts. | **Cycle-time delta** = (pre vs post KB minutes × volume). | {ev_line} |
| **Satisfaction SLO** | **Phase 1:** - Set a minimum monthly median target so the team has a clear guardrail for acceptable experience even when volumes spike.<br><br>- Communicate the target with examples from your best months so the goal feels achievable and grounded in real data.<br><br>**Phase 2:** - Alert when the median dips below the threshold so action starts early rather than at the end of the month.<br><br>- Include automatic suggestions for likely fixes based on the month’s pattern so teams do not lose time deciding what to try first.<br><br>**Phase 3:** - Trigger a swarm on persistent dips and assign owners to changes so accountability is explicit and progress is trackable.<br><br>- Re baseline the SLO annually so it stays challenging and credible. | - Guardrails prevent silent degradation which protects the brand experience for users who rely on consistent service quality.<br><br>- Early warnings keep the team proactive which reduces the size and duration of negative swings in satisfaction.<br><br>- Structured swarms create fast learning loops which produce fixes that benefit multiple categories at once.<br><br>- Periodic re baselining keeps motivation healthy and maintains momentum. | **Breach mins avoided** linked to months under **{_fmt_float(mean_val)}%**. | {ev_line} |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **Proactive service recovery on low months** | **Phase 1:** - Reach out to detractors from the lowest scoring month to acknowledge the issue and gather context while memories are still accurate.<br><br>- Prioritize high impact users and services so the biggest risks are addressed first.<br><br>**Phase 2:** - Offer a remedy or a clear ETA and explain the steps being taken so users regain confidence in the process.<br><br>- Coordinate with owners to ensure promised fixes actually land in the agreed window.<br><br>**Phase 3:** - Confirm closure with each user and record their follow up sentiment so the loop is visible and measurable.<br><br>- Summarize what changed and publish a short note so others see that feedback leads to action. | - Targeted recovery lowers complaint rates because users feel heard and see movement which reduces escalation pressure on managers.<br><br>- Trust improves as users observe consistent follow through which increases tolerance during future incidents.<br><br>- Documented recoveries create examples that teach the team how to respond effectively which raises the standard over time.<br><br>- Measured loops ensure that the investment in outreach translates into durable improvements. | **Complaint mins avoided** estimated from low month **{stats['low_date'] or 'N/A'}** at **{_fmt_float(stats['low_val'])}%**. | {ev_line} |
| **Celebrate high-median months** | **Phase 1:** - Recognize the teams behind high median months with concrete examples of what they did differently so recognition is tied to practice not luck.<br><br>- Share the context that made the result possible so replication is realistic for other teams.<br><br>**Phase 2:** - Replicate the methods across similar queues and provide a short enablement checklist so adoption is quick and lightweight.<br><br>- Track adoption so leaders can unblock teams that struggle to implement the changes.<br><br>**Phase 3:** - Document the practices in the knowledge base so they survive staff rotations and continue to guide new joiners.<br><br>- Refresh the notes when systems evolve so the guidance stays relevant. | - Visible celebration reinforces the behaviors that drive high satisfaction which encourages teams to keep doing what works even when volumes rise.<br><br>- Replication lifts the baseline across the operation which reduces variability and makes outcomes more predictable for users.<br><br>- Lightweight enablement reduces rollout friction which preserves delivery while improvements spread.<br><br>- Durable documentation prevents knowledge loss which protects gains over the long term. | — | Peak **{_fmt_float(stats['peak_val'])}%** on {stats['peak_date'] or 'N/A'} shows what “good” looks like. |
| **Expectation-setting on variability** | **Phase 1:** - Publish the monthly CSAT with a short explanation of the main drivers so stakeholders understand what changed and why it matters.<br><br>- Use plain language so non technical audiences can engage with the data confidently.<br><br>**Phase 2:** - Note the improvements planned for the next cycle and the owners responsible so expectations are aligned and progress is easy to follow.<br><br>- Include realistic timelines so credibility is maintained.<br><br>**Phase 3:** - Update a status page as actions complete so people can self serve answers instead of opening new tickets for updates.<br><br>- Close the loop with a summary of results so the organization sees that transparency yields action. | - Transparent communication reduces anxiety and inbound queries which frees analyst and manager time for actual improvements.<br><br>- Clear plans create shared accountability which increases the likelihood that fixes are delivered on schedule.<br><br>- A living status page lowers the volume of repetitive questions which improves perceived responsiveness without adding headcount.<br><br>- Consistent updates build trust which cushions the impact of occasional low months. | **Query mins avoided** higher in wide-IQR month **{worst_iqr.get('month') or 'N/A'}**. | {ev_line} |
"""
            }
            render_cio_tables("Customer Satisfaction Ratings", cio)
        else:
            st.warning("⚠️ Missing 'customer_satisfaction' or 'report_date' columns.")

    # ============================================================
    # 6b – Net Promoter Score (NPS)
    # ============================================================
    with st.expander("📌 Net Promoter Score (NPS) for IT Services"):
        if "nps_score" in df_filtered.columns and "report_date" in df_filtered.columns:
            plot_df = (
                df_filtered.groupby("report_date")["nps_score"]
                .mean()
                .reset_index()
            )
            fig = px.line(
                plot_df,
                x="report_date",
                y="nps_score",
                markers=True,
                title="Average NPS Trend Over Time",
                labels={"report_date": "Report Date", "nps_score": "Average NPS Score"},
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)

            stats = _peak_low_df(plot_df, "report_date", "nps_score")
            mean_val = plot_df["nps_score"].mean() if not plot_df.empty else None

            st.markdown("### Analysis – Net Promoter Score")
            if stats["peak_val"] is not None:
                st.write(f"""
**What this graph is:** A **line chart** of **average NPS** over time.  
**X-axis:** Calendar date.  
**Y-axis:** Mean NPS for that date.

**What it shows in your data:**  
- **Largest NPS day:** **{_fmt_float(stats['peak_val'])}** on **{stats['peak_date'] or 'N/A'}**.  
- **Lowest NPS day:** **{_fmt_float(stats['low_val'])}** on **{stats['low_date'] or 'N/A'}**.  
- **Average NPS across period:** **{_fmt_float(mean_val)}**.

**Overall:** Rising line = improved advocacy; sharp dips often align with **incidents** or **long resolutions**.

**How to read it operationally:**  
- **Lead–lag:** Compare against response/resolution charts to find drivers.  
- **Sustainability:** Maintain gains for ≥2 cycles to treat as a real shift.  
- **Interventions:** Deploy recovery programmes immediately after dips.

**Why this matters:** NPS condenses user loyalty into a single signal that predicts **retention** and **word-of-mouth**.
""")
            else:
                st.info("No valid NPS data found for analysis.")

            ev_line = f"Peak NPS **{_fmt_float(stats['peak_val'])}** ({stats['peak_date'] or 'N/A'}) vs low **{_fmt_float(stats['low_val'])}** ({stats['low_date'] or 'N/A'}); average **{_fmt_float(mean_val)}**."

            # EXPANDED EXPLANATIONS + BENEFITS BELOW
            cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **Automate NPS capture & pipeline** | **Phase 1:** - Connect the survey tool to the ticketing platform so NPS requests are sent consistently at the right moments without manual effort.<br><br>- Standardize the question wording so scores are comparable across channels and time.<br><br>**Phase 2:** - Stream responses into the data lake with metadata such as service owner and priority so analysis can be sliced without extra joins.<br><br>- Apply validation on ingestion so malformed records are caught early and corrected quickly.<br><br>**Phase 3:** - Build auto refreshed dashboards that surface trends and dips so leaders do not wait for monthly packs to act.<br><br>- Set access controls so sensitive comments are visible to the right roles only. | - Automating the pipeline removes repetitive work which reduces recurring operational cost for analysts and coordinators each reporting period.<br><br>- Faster visibility of dips enables earlier interventions that prevent dissatisfaction from spreading across more users which limits downstream support cost.<br><br>- Clean consistent data improves the reliability of trend analysis which reduces wasted time debating the numbers and accelerates decision making.<br><br>- Controlled access reduces risk during audits which lowers the cost of compliance. | **Admin mins saved** = (manual mins/response × #responses) around dip dates **{stats['low_date'] or 'N/A'}**. | {ev_line} |
| **Focus retention spend around dips** | **Phase 1:** - Identify the specific drivers present on low NPS days by linking comments to operational events so spending is directed at the real causes of churn risk.<br><br>- Quantify affected user segments so the scale of the response matches the impact.<br><br>**Phase 2:** - Deploy offers and fixes that remove the friction causing the dip so users experience immediate relief and feel valued.<br><br>- Coordinate with owners to ensure changes are live quickly and monitored for effect.<br><br>**Phase 3:** - Measure uplift in NPS and usage from the targeted cohort so the return on spend is visible and defensible.<br><br>- Retire ineffective interventions and double down on those with proven impact. | - Targeted spend reduces churn risk by addressing the specific issues that drive detractor behavior which protects revenue and reputation.<br><br>- Visible recovery improves user confidence which reduces complaint volume and the cost of handling escalations.<br><br>- Measuring uplift ensures the budget flows to the actions that actually work which increases efficiency over time.<br><br>- Evidence based choices build stakeholder support for future investments in user experience. | **Avoided churn value** = (at-risk users × LTV) keyed to low **{_fmt_float(stats['low_val'])}**. | {ev_line} |
| **Reduce noise in survey ops** | **Phase 1:** - De duplicate overlapping survey channels so users do not receive multiple requests for the same event which reduces fatigue and improves data quality.<br><br>- Map each survey to a clear purpose so teams know which signal to use in which decision.<br><br>**Phase 2:** - Normalize scales and scoring rules so results align and can be compared or aggregated without complicated conversions.<br><br>- Document the definitions so new joiners read the numbers the same way as existing staff.<br><br>**Phase 3:** - Validate samples for representativeness and add guardrails against over sampling a single department so conclusions reflect the full user base.<br><br>- Review sampling quarterly so design keeps pace with organizational change. | - Cleaner survey operations remove false alarms that waste manager time and distract teams from real issues which improves operational focus.<br><br>- Consistent scales make the story clear which speeds leadership discussions and supports faster action on real drivers.<br><br>- Representative samples increase confidence in decisions which reduces the need for costly re analysis later.<br><br>- Reduced fatigue improves response rates which strengthens the reliability of ongoing measurement. | **Rework mins avoided** in months around volatility. | {ev_line} |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **Correlate NPS with resolution time** | **Phase 1:** - Join NPS responses with ticket resolution durations so the relationship between speed and sentiment is quantified for your environment.<br><br>- Include service type and priority so elasticity can be modeled accurately for each context.<br><br>**Phase 2:** - Build a simple model that estimates NPS change per minute of resolution time so targets are grounded in expected impact.<br><br>- Validate the model against recent months so confidence is high before adoption.<br><br>**Phase 3:** - Set SLOs that reflect the elasticity by category so effort is focused where faster resolution most improves advocacy.<br><br>- Review the model quarterly so it stays aligned with reality. | - Understanding elasticity directs operational improvements to the queues that deliver the biggest NPS gains which maximizes impact per minute saved.<br><br>- Evidence based SLOs prevent over engineering in queues where speed has little sentiment payoff which protects capacity for higher value work.<br><br>- Regular review keeps the relationship accurate as user expectations evolve which sustains the link between operations and loyalty.<br><br>- Clear targets ease prioritization during crunch periods which stabilizes performance. | **Minutes to save** = (Δres time × tickets on dip dates **{stats['low_date'] or 'N/A'}**). | {ev_line} |
| **Promoter flywheel** | **Phase 1:** - Identify promoters on high days and capture what went right in their journeys so the organization learns which practices create advocacy.<br><br>- Ask permission to use anonymized quotes so successes can be shared safely.<br><br>**Phase 2:** - Turn the themes into short testimonials and internal case studies so teams can model their behavior on proven wins.<br><br>- Share with new hires during onboarding so culture compounds from day one.<br><br>**Phase 3:** - Share back outcomes with teams whose work created promoters so they see the impact of their effort and stay motivated.<br><br>- Refresh stories each quarter so examples remain current. | - Reinforcing successful behaviors increases the proportion of promoters which strengthens morale and creates a positive service culture.<br><br>- Concrete stories make abstract metrics tangible which accelerates adoption of good practices across teams.<br><br>- Onboarding with wins reduces ramp time for new staff which helps maintain service quality during growth.<br><br>- Regular celebration improves engagement which correlates with better operational performance. | — | High day **{stats['peak_date'] or 'N/A'}** at **{_fmt_float(stats['peak_val'])}** proves excellence. |
| **Detractor rapid-response** | **Phase 1:** - Call detractors within twenty four hours to acknowledge the issue and gather details while the context is still fresh so recovery starts quickly.<br><br>- Prioritize by severity and customer tier so resources are used where risk is highest.<br><br>**Phase 2:** - Resolve the root cause or provide a concrete workaround so the user’s immediate pain is reduced and confidence begins to recover.<br><br>- Coordinate with engineering or vendors if dependencies exist so the fix is not delayed by unclear ownership.<br><br>**Phase 3:** - Close the loop with the user and record whether their sentiment improved so the team learns which actions work best.<br><br>- Aggregate themes for systemic fixes so fewer detractors are created in the future. | - Rapid response prevents negative word of mouth from spreading which protects reputation and reduces the likelihood of escalations that consume leadership time.<br><br>- Concrete fixes reduce repeat contacts which saves agent minutes and keeps queues healthy during busy periods.<br><br>- Closing the loop builds trust which increases willingness to respond to future surveys and provide constructive feedback.<br><br>- Aggregated learning targets root causes that generate multiple detractors which multiplies the impact of each improvement. | **Complaint mins avoided** around **{stats['low_date'] or 'N/A'}**. | {ev_line} |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **VIP outreach on dips** | **Phase 1:** - Flag VIP users and business critical services on days where NPS dips so high risk relationships receive priority attention.<br><br>- Assign a named owner so accountability is clear and communication is consistent.<br><br>**Phase 2:** - Provide senior oversight and faster lanes for fixes so delays are minimized for the most sensitive accounts.<br><br>- Offer status calls for complex issues so expectations remain aligned.<br><br>**Phase 3:** - Confirm outcomes with stakeholders and document what worked so playbooks for VIP care improve over time.<br><br>- Track the rate of future escalations from the same accounts so effectiveness is measured. | - Focused outreach protects strategic relationships which reduces business risk and avoids costly escalations that can derail leadership time.<br><br>- Faster recovery for VIPs preserves operational continuity in critical areas which improves perception of IT as a trusted partner.<br><br>- Structured follow up prevents issues from silently lingering which increases satisfaction and reduces repeat contacts.<br><br>- Documented learning improves future handling which compounds benefits across the year. | **Escalation mins avoided** during low **{_fmt_float(stats['low_val'])}** periods. | {ev_line} |
| **Celebrate promoter months** | **Phase 1:** - Thank users who provided positive feedback so goodwill is reinforced and participation remains high for future surveys.<br><br>- Share the operational improvements that contributed to the uplift so success is linked to concrete changes not luck.<br><br>**Phase 2:** - Institutionalize the practices that created promoter months by embedding them into SOPs so they survive staff rotations.<br><br>- Provide quick refresher sessions so the habits stay active.<br><br>**Phase 3:** - Monitor whether the uplift persists after institutionalization so the practices are proven to be durable and not one offs.<br><br>- Adjust where the effect fades so standards stay strong. | - Recognition builds advocacy loops where satisfied users become allies for IT which reduces resistance during future changes and outages.<br><br>- Codifying winning practices keeps performance resilient during hiring and turn over which stabilizes user experience across seasons.<br><br>- Monitoring persistence keeps the focus on outcomes which ensures energy is spent on what continues to work.<br><br>- Regular refreshers maintain skills at scale which sustains promoter trends. | — | Peak **{_fmt_float(stats['peak_val'])}** shows what to amplify. |
| **Transparent comms during volatility** | **Phase 1:** - Publish the drivers behind volatility using plain language summaries so stakeholders understand what happened without needing to parse technical detail.<br><br>- Share the immediate actions already underway so confidence rises quickly after a dip.<br><br>**Phase 2:** - Roadmap medium term fixes with simple milestones so people can track progress and avoid duplicate questions during the work.<br><br>- Include dependencies and owners so alignment across teams improves.<br><br>**Phase 3:** - Report progress and outcomes after each milestone so the organization sees movement and can course correct if needed.<br><br>- Archive updates so patterns are visible across quarters. | - Transparent updates reduce uncertainty which directly lowers the number of “why so low” queries that consume analyst and manager time.<br><br>- Clear roadmaps align teams and cut coordination delays which improves the speed of problem resolution and stabilizes sentiment sooner.<br><br>- Regular progress reports build credibility which lowers the odds of escalations during ongoing remediation.<br><br>- Historical records accelerate future diagnostics which shortens the response during the next period of volatility. | **Query mins avoided** post-update after dips. | {ev_line} |
"""
            }
            render_cio_tables("Net Promoter Score (NPS)", cio)
        else:
            st.warning("⚠️ Missing 'nps_score' or 'report_date' columns.")

    # ============================================================
    # 6c – Service Desk Response Times
    # ============================================================
    with st.expander("📌 Service Desk Response Time"):
        if "service_desk_response_time" in df_filtered.columns and "report_date" in df_filtered.columns:
            plot_df = (
                df_filtered.groupby("report_date")["service_desk_response_time"]
                .mean()
                .reset_index()
            )
            fig = px.line(
                plot_df,
                x="report_date",
                y="service_desk_response_time",
                markers=True,
                title="Average Service Desk Response Time Over Time",
                labels={
                    "report_date": "Report Date",
                    "service_desk_response_time": "Response Time (mins)",
                },
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)

            stats = _peak_low_df(plot_df, "report_date", "service_desk_response_time")
            mean_val = plot_df["service_desk_response_time"].mean() if not plot_df.empty else None

            st.markdown("### Analysis – Response Time")
            if stats["peak_val"] is not None:
                st.write(f"""
**What this graph is:** A **line chart** of **average response time (mins)** per day.  
**X-axis:** Calendar date.  
**Y-axis:** Minutes to first response.

**What it shows in your data:**  
- **Fastest response:** **{_fmt_float(stats['low_val'])} mins** on **{stats['low_date'] or 'N/A'}**.  
- **Slowest response:** **{_fmt_float(stats['peak_val'])} mins** on **{stats['peak_date'] or 'N/A'}**.  
- **Average response:** **{_fmt_float(mean_val)} mins**.

**Overall:** A rising line signals **under-capacity** or **routing issues**; a falling line reflects **process control**.

**How to read it operationally:**  
- **Gap = risk:** The difference between slowest and fastest days shows **exposure to SLA breach**.  
- **Lead–lag with intake:** Align peaks with ticket spikes to justify staffing changes.  
- **Control:** Keep daily values close to the average to **stabilize experience**.

**Why this matters:** Faster, predictable first responses are strongly linked to **higher CSAT** and **lower escalation rates**.
""")
            else:
                st.info("No valid response time data found.")

            ev_line = f"Fastest **{_fmt_float(stats['low_val'])} mins** ({stats['low_date'] or 'N/A'}) vs slowest **{_fmt_float(stats['peak_val'])} mins** ({stats['peak_date'] or 'N/A'}); average **{_fmt_float(mean_val)} mins**."

            # EXPANDED EXPLANATIONS + BENEFITS BELOW
            cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **SLA breach early-warning alerts** | **Phase 1:** - Set a threshold at the average of **{_fmt_float(mean_val)}** minutes plus a policy buffer so alerts trigger before a breach becomes likely.<br><br>- Calibrate thresholds per queue so sensitivity reflects real patterns rather than a one size rule.<br><br>**Phase 2:** - Notify owners in real time through the collaboration tool so action starts immediately without checking multiple dashboards.<br><br>- Provide context in the alert such as current queue age and volume so responders know what lever to pull first.<br><br>**Phase 3:** - Auto escalate if no improvement is detected within a set window so issues do not linger silently in busy periods.<br><br>- Review alert performance monthly so noise is controlled and attention stays focused. | - Early warnings avoid penalties and rework because teams respond before targets are breached which protects budget and reputation.<br><br>- Real time context reduces decision time which shortens queues faster and lowers the average response for the day.<br><br>- Automated escalation ensures accountability which prevents issues from being lost when workloads surge.<br><br>- Regular tuning keeps alerts useful which sustains long term value from the system. | **Penalty minutes avoided** = (# breaches prevented × mins over **{_fmt_float(mean_val)}**). | {ev_line} |
| **Shift optimization by peak days** | **Phase 1:** - Map the slowest response days to intake data so staffing decisions are justified by demand not guesswork.<br><br>- Identify whether the problem is start times or break timing so the fix is precise and minimally disruptive.<br><br>**Phase 2:** - Re time rosters and breaks to cover the true peaks so queues do not build early in the day and spill into the afternoon.<br><br>- Pilot for one roster cycle and compare response metrics so the change is proven before expanding.<br><br>**Phase 3:** - Recheck monthly as seasonality shifts so coverage stays aligned with reality and does not drift over time.<br><br>- Keep a lightweight change log so learning accumulates across quarters. | - Better coverage reduces overtime because fewer long queues need late day catch up which protects cost and morale.<br><br>- Balanced analyst load lowers burnout and error rates which improves quality and reduces rework minutes later in the process.<br><br>- Faster first responses improve SLA attainment which reduces penalty exposure and strengthens stakeholder confidence.<br><br>- A measured pilot approach limits risk while still enabling timely improvements. | **Overtime hours saved** tied to days near **{stats['peak_date'] or 'N/A'}** at **{_fmt_float(stats['peak_val'])} mins**. | {ev_line} |
| **First-touch macros & routing** | **Phase 1:** - Create macros for the top intents so agents can respond quickly with accurate information that moves the case forward immediately.<br><br>- Include prompts for required details so back and forth loops are minimized.<br><br>**Phase 2:** - Implement skill based routing so tickets land with the correct team on the first attempt and do not idle during reassignment.<br><br>- Provide a rapid correct route option so mistakes are fixed in seconds not hours.<br><br>**Phase 3:** - Review missed routing patterns each month so forms and rules are refined and drift is corrected early.<br><br>- Retire low performing macros so the catalog stays sharp and easy to navigate. | - Standardized first touches reduce handling variance which shortens time to first response for the majority of tickets and stabilizes service perception.<br><br>- Correct placement lowers handoffs which saves minutes and reduces user frustration from repeated introductions.<br><br>- Ongoing review keeps the system tuned which protects gains as volumes and categories evolve.<br><br>- A focused macro library makes it easier for new agents to be fast which reduces ramp time and training cost. | **Minutes saved** = (response delta vs **{_fmt_float(mean_val)}** × ticket volume). | {ev_line} |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **Live wallboard with queue SLAs** | **Phase 1:** - Visualize per queue response time and SLA countdowns so teams see risk building in real time and can intervene early.<br><br>- Keep the board simple and focused so attention is not diluted by low value metrics.<br><br>**Phase 2:** - Alert on breaches and define who acts so there is no ambiguity when the line is crossed.<br><br>- Capture the reason for each breach so learning feeds back into process changes.<br><br>**Phase 3:** - Activate surge capacity when thresholds are hit so queues are cleared quickly and momentum is restored.<br><br>- Review surge triggers quarterly so the bar remains effective. | - Earlier intervention keeps performance steadier across the day which reduces variability that frustrates users and managers.<br><br>- Clear accountability reduces delay between detection and action which protects SLA outcomes and reduces incident volume linked to long waits.<br><br>- Structured surge rules enable predictable recovery which stabilizes operations during peak periods.<br><br>- Continuous learning from breach reasons improves processes and prevents repeats which compounds benefits. | **ΔAverage response** from peak **{_fmt_float(stats['peak_val'])}** towards **{_fmt_float(mean_val)}** × volume. | {ev_line} |
| **Intake smoothing (WIP limits)** | **Phase 1:** - Cap concurrent triage items per analyst so people focus on finishing first touches rather than starting many and finishing few.<br><br>- Visualize personal WIP so self management is easy and transparent.<br><br>**Phase 2:** - Send overflow to a visible queue that the team can swarm when capacity frees up so no ticket is hidden from view.<br><br>- Provide guidelines for when to pull from overflow so fairness and speed are balanced.<br><br>**Phase 3:** - Tune caps based on observed throughput so the limit fits your context and encourages flow rather than blocking it.<br><br>- Revisit quarterly as skills and volumes change. | - Higher focus reduces partial work which shortens time to first response and improves the predictability of the user experience.<br><br>- Visible overflow prevents tickets from aging unnoticed which protects SLA metrics and reduces recovery firefighting.<br><br>- Adaptive caps let teams sustain performance as staffing and demand shift which keeps operations resilient.<br><br>- Better flow improves agent satisfaction which supports retention and consistent quality. | **Throughput gain mins** = (Δresponses/day × avg mins). | {ev_line} |
| **After-action review of slowest days** | **Phase 1:** - Inspect the causes behind **{stats['peak_date'] or 'N/A'}** and similar slow days so fixes target real bottlenecks such as access delays vendor waits or tool outages.<br><br>- Include data from staffing and change calendars so correlations are explicit.<br><br>**Phase 2:** - Fix the identified bottlenecks with owners timelines and specific changes so accountability is clear and progress is trackable.<br><br>- Communicate the changes to all affected teams so behaviors adjust in step with process updates.<br><br>**Phase 3:** - Verify improvement in the following weeks by comparing against the original slow day metrics so the effect is proven and durable.<br><br>- Add successful fixes to SOPs so benefits persist across rotations. | - Removing recurrent blockers prevents the same delays from recurring which steadily lowers the average response time over the month.<br><br>- Clear ownership and communication reduce coordination friction which speeds the impact of fixes and keeps teams aligned.<br><br>- Verification ensures energy is invested in solutions that actually work which increases the efficiency of continuous improvement.<br><br>- Institutionalizing fixes protects gains during staffing changes which stabilizes the service level. | **Minutes reclaimed** = (**{_fmt_float(stats['peak_val'])} − {_fmt_float(mean_val)}**) × tickets that day. | {ev_line} |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence |
|---|---|---|---|---|
| **Proactive delay messaging** | **Phase 1:** - Notify users when a response exceeds **{_fmt_float(mean_val)}** minutes so expectations are reset early and frustration does not build in silence.<br><br>- Include a short explanation that focuses on next steps rather than excuses so trust is maintained.<br><br>**Phase 2:** - Provide an ETA and the immediate next action so users know when to expect movement and what they can do to help progress.<br><br>- Offer a quick path to add attachments or details so the next touch is productive.<br><br>**Phase 3:** - Link to self service for common requests so some users can resolve without waiting which reduces queue pressure for everyone.<br><br>- Monitor feedback on messages and refine tone so communication stays helpful. | - Proactive updates reduce chasers and duplicate contacts which saves agent time and keeps queues smaller for the rest of the day.<br><br>- Clear ETAs improve perceived fairness which raises satisfaction even before the technical fix is complete.<br><br>- Easy contribution of details speeds resolution on the next touch which shortens the overall journey for the user.<br><br>- Self service links convert a portion of waits into instant outcomes which improves sentiment at low cost. | **Query mins avoided** on days near **{stats['peak_date'] or 'N/A'}**. | {ev_line} |
| **Recognize fast responders** | **Phase 1:** - Publish a simple leaderboard that highlights consistent fast responders so the team sees that speed and quality are valued together.<br><br>- Ensure the metric balances speed with accuracy so the incentive is healthy.<br><br>**Phase 2:** - Reward consistency with small recognitions that encourage sustained behavior across weeks not just single day sprints.<br><br>- Invite top performers to share their routines so peers can adopt practical tips.<br><br>**Phase 3:** - Share the tips in a short guide and revisit them quarterly so practices evolve with the tools and queues.<br><br>- Keep the tone positive so the program motivates rather than shames. | - Recognition nudges faster responses across the team which improves average times without adding headcount or tools.<br><br>- Balanced metrics protect quality which prevents rework that would otherwise erode speed gains and satisfaction.<br><br>- Peer tips translate into actionable habits that new agents can apply immediately which shortens ramp time.<br><br>- Regular refresh keeps momentum which preserves culture and performance benefits. | — | Fastest day **{stats['low_date'] or 'N/A'}** at **{_fmt_float(stats['low_val'])} mins** shows attainable speed. |
| **VIP fast lane** | **Phase 1:** - Tag VIP users and key services in the system so their tickets are visible and prioritized during intake without manual scanning.<br><br>- Define clear eligibility so the lane is used appropriately and stays credible.<br><br>**Phase 2:** - Apply priority triage and assign senior agents so complex or high impact issues move quickly and receive experienced attention.<br><br>- Monitor lane volume so standard queues are not starved of capacity.<br><br>**Phase 3:** - Audit outcomes monthly to ensure the lane is delivering faster responses and higher satisfaction for the intended group.<br><br>- Adjust rules when misuse or drift is detected so fairness is maintained. | - Protecting key relationships lowers escalation risk and preserves trust with stakeholders who have disproportionate business impact which stabilizes sponsorship for IT initiatives.<br><br>- Faster handling of VIP issues prevents operational disruptions that could ripple across many users which reduces downstream tickets and noise.<br><br>- Regular audits keep the lane efficient and fair which protects team morale and prevents abuse of priority rules.<br><br>- Clear criteria and measurement make the program defensible during governance reviews which maintains organizational confidence. | **Escalation mins avoided** strongest on slow days (**{stats['peak_date'] or 'N/A'}**). | {ev_line} |
"""
            }
            render_cio_tables("Service Desk Response Time", cio)
        else:
            st.warning("⚠️ Missing 'service_desk_response_time' or 'report_date' columns.")
