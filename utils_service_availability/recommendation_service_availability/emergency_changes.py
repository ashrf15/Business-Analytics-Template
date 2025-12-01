# utils_service_availability/recommendation_service_availability/emergency_changes.py

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# Company visual theme (white + blue)
px.defaults.template = "plotly_white"
PRIMARY_BLUE = "#004C99"
SECONDARY_BLUE = "#007ACC"
MES_BLUE_SEQ = [PRIMARY_BLUE, SECONDARY_BLUE, "#3399FF", "#66B2FF", "#9BD1FF"]

# ============================================================
# Helper Function to Render CIO Tables
# ============================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# Small helpers
def _to_num(s):
    return pd.to_numeric(s, errors="coerce")

# ============================================================
# 7️⃣ Emergency Changes and Their Impact
# ============================================================
def emergency_changes(df: pd.DataFrame):

    # ----------------------------------------------
    # 7a. Emergency Changes Made to Services
    # ----------------------------------------------
    with st.expander("📌 Emergency Changes Made to Services"):
        # Adapt column name if change_type missing
        if "change_type" not in df.columns and "maintenance_type" in df.columns:
            df = df.copy()
            df["change_type"] = df["maintenance_type"]

        required = {"report_date", "service_name", "change_type"}
        if required.issubset(df.columns):
            df = df.copy()
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
            df["month"] = df["report_date"].dt.to_period("M").astype(str)

            emer_df = df[df["change_type"].astype(str).str.lower().eq("emergency")].copy()
            if emer_df.empty:
                st.info("✅ No emergency changes recorded in this dataset.")
            else:
                monthly = emer_df.groupby("month", as_index=False)["change_type"].count()
                monthly = monthly.rename(columns={"change_type": "emergency_count"})

                # (Optional) compute RM/min for emergencies if cost & downtime available
                has_costmins = {"estimated_cost_downtime", "downtime_minutes"}.issubset(emer_df.columns)
                avg_rm_per_min_em = np.nan
                total_em_rm = np.nan
                total_em_min = np.nan
                if has_costmins:
                    emer_df["estimated_cost_downtime"] = _to_num(emer_df["estimated_cost_downtime"])
                    emer_df["downtime_minutes"] = _to_num(emer_df["downtime_minutes"])
                    total_em_rm = float(emer_df["estimated_cost_downtime"].sum())
                    total_em_min = float(emer_df["downtime_minutes"].sum())
                    if total_em_min > 0:
                        avg_rm_per_min_em = total_em_rm / total_em_min

                # --- Graph: Emergency changes per month (Mesiniaga theme)
                fig = px.bar(
                    monthly,
                    x="month",
                    y="emergency_count",
                    text="emergency_count",
                    title="Emergency Changes per Month",
                    labels={"month": "Month", "emergency_count": "Count of Emergency Changes"},
                    color_discrete_sequence=[PRIMARY_BLUE],
                    template="plotly_white",
                )
                fig.update_traces(textposition="outside", cliponaxis=False)
                st.plotly_chart(fig, use_container_width=True)

                # --- Analysis (OWN analysis for this graph in required template)
                total = int(monthly["emergency_count"].sum())
                avg = float(monthly["emergency_count"].mean())
                peak = monthly.loc[monthly["emergency_count"].idxmax()]
                low = monthly.loc[monthly["emergency_count"].idxmin()]

                st.markdown("### Analysis — Emergency Changes per Month (Graph 1)")
                st.write("""**What this graph is:** A **monthly bar chart** showing the **count of emergency changes** executed in production.  
**X-axis:** Calendar month.  
**Y-axis:** Number of emergency changes per month.

**What it shows in your data:**  
- **Total emergency changes:** **{total}** across the period.  
- **Peak month:** **{peak['month']}** with **{int(peak['emergency_count'])}** emergency changes.  
- **Lowest month:** **{low['month']}** with **{int(low['emergency_count'])}** emergency changes.  
- **Average pace:** **{avg:.1f}** emergency changes/month.{"  \n- **Emergency downtime & cost totals:** " + (f"**{int(total_em_min):,} min**, **RM {total_em_rm:,.0f}**, **Avg RM/min ≈ {avg_rm_per_min_em:,.2f}**." if has_costmins else "")}

**Overall:** A higher emergency change count signals a **reactive posture**; a lower, stable count implies that risk is being **absorbed by planned work** instead of firefighting.

**How to read it operationally:**  
- **Gap to target:** Compare monthly bars to your internal target range; months above target require **pre-prod rigor** and **change freezes**.  
- **Lead–lag to incidents:** Align spikes with incident surges; if correlated, convert hot fixes into **planned engineering**.  
- **Recovery strength:** Monitor whether counts **fall back** after process fixes; a persistent plateau indicates **structural issues**.  
- **Control:** Reduce hot-fix frequency by **smoke tests**, **canary gates**, and **CAB exceptions** that still apply basic guardrails.

**Why this matters:** Emergency changes have **higher failure probability**, consume **overtime**, and happen during **sensitive hours**. Driving them down unlocks **cost savings**, **stability**, and **stakeholder confidence**."""
                )

                # --- CIO Table (≥3 recs/pillar, phased, real numbers referenced)
                rmmin_snip = f"Avg RM/min≈RM {avg_rm_per_min_em:,.2f}" if has_costmins and avg_rm_per_min_em == avg_rm_per_min_em else "RM/min (from data)"
                peak_month = str(peak["month"])
                peak_cnt = int(peak["emergency_count"])
                low_month = str(low["month"])
                low_cnt = int(low["emergency_count"])

                # Compute average downtime per emergency month for use in CIO table
                avg_d = np.nan
                if "downtime_minutes" in emer_df.columns:
                    tmp_d = (
                        emer_df
                        .copy()
                        .assign(downtime_minutes=_to_num(emer_df["downtime_minutes"]))
                        .groupby("month", as_index=False)["downtime_minutes"]
                        .sum()
                    )
                    if not tmp_d.empty:
                        avg_d = float(tmp_d["downtime_minutes"].mean())

                cio_7a = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Convert emergencies into planned work | **Phase 1 – Backlog:** For **{peak_month}** which has a peak of **{peak_cnt}** emergency changes, record each hot fix as a formal backlog item with a clear owner, due date, and description so that none of the urgent work is forgotten once the pressure moment is over.<br><br>**Phase 2 – Scheduling:** Move these backlog items into upcoming sprints or maintenance windows and treat them as standard changes so that they follow normal risk assessment, testing, and deployment practices instead of being rushed into production.<br><br>**Phase 3 – Verification:** In the next **{peak_month}** cycle, compare emergency change volume and total downtime against the previous cycle so that you can confirm whether converting these items into planned work reduces reactive activity. | - Reduces overtime during firefighting periods because work is shifted from chaotic last minute pushes into scheduled windows where staffing is more controlled and predictable.<br><br>- Lowers the number of urgent coordination calls because teams can plan and communicate around known change slots instead of repeatedly reacting to unexpected emergencies.<br><br>- Reduces after hours disruption for engineers and business stakeholders because fewer changes are pushed into nights and weekends when the risk and fatigue are higher.<br><br>- Gradually shifts the culture from reactive crisis handling toward proactive planning which supports long term cost efficiency and operational stability.<br><br> | **RM saved = minutes_shifted_to_off-peak × {rmmin_snip}**; if available, use emergency minutes **{int(total_em_min) if has_costmins else 0:,}** from the dataset. | Peak bar **{peak_month} = {peak_cnt}** shows reactive work concentration; converting these reduces reactivity. |
| Pre-deployment smoke tests | **Phase 1 – Test suite:** Build a small but targeted smoke test suite that focuses on the most common failure modes observed in **{peak_month}** so that the riskiest behaviours are checked before a change is pushed even when time is limited.<br><br>**Phase 2 – Gate:** Require that every urgent change passes this smoke test pack in a staging or canary environment before it is allowed to go fully into production so that the worst defects are caught early.<br><br>**Phase 3 – Audit:** Each month, review any production failures that still happened despite passing smoke tests and update the test suite so that it remains aligned with real issues and does not become outdated. | - Reduces the number of failed hot fixes because more defects are detected in a simple pre deployment check instead of appearing in front of users.<br><br>- Lowers rollback minutes and rework because fewer emergency changes will need to be reversed or re patched after causing visible issues in production.<br><br>- Improves confidence among engineers and stakeholders that even urgent changes follow a minimum level of safety validation before they are deployed.<br><br>- Creates a continuous improvement loop where every escape teaches the team how to strengthen the smoke tests for the next cycle.<br><br> | **RM avoided = rollback_minutes_prevented × {rmmin_snip}** using observed rollback minutes (if tracked). | Elevated emergency frequency implies inadequate pre-flight checks in peak months. |
| Emergency-change freeze in peak hours | **Phase 1 – Define:** Identify peak revenue or business hours and define a clear rule that emergency changes in those windows are only permitted for genuine P1 scenarios where significant impact is already occurring, while all lower priority urgent work must wait for off peak slots.<br><br>**Phase 2 – Exception path:** Document what qualifies as a P1 emergency, who can approve an exception, and how decisions are logged so that the process is transparent and traceable.<br><br>**Phase 3 – Review:** At the end of each month, review all exceptions to understand whether they were justified, what outcomes they produced, and whether the criteria or process needs to be tightened. | - Shifts risk away from the busiest and most sensitive business hours so that fewer users experience disruption during critical periods of the day.<br><br>- Lowers the probability of financial penalties and reputational damage because high risk changes are not executed during peak transaction or usage windows without very strong justification.<br><br>- Helps teams plan work more calmly because they know that most emergency like changes will be executed during controlled off peak times rather than during stressful peak activity periods.<br><br>- Increases visibility and discipline around true emergencies because every exception is tracked, justified, and reviewed afterwards.<br><br> | **ΔCost = (Peak−Off-peak) RM/min × emergency_minutes**; use dataset minutes **{int(total_em_min) if has_costmins else 0:,}** where available. | Bars quantify monthly frequency; apply time-based guardrails in months like **{peak_month}**. |
| Owner-level cost visibility | **Phase 1 – Attribute:** Break down emergency minutes and estimated cost by service and service owner so that each owner sees the financial impact associated with their area in months like **{peak_month}** and **{low_month}**.<br><br>**Phase 2 – Targets:** Agree on realistic monthly reduction targets for emergency minutes and costs with each owner so that responsibilities and expectations are clearly defined.<br><br>**Phase 3 – Governance:** Use recurring governance forums to review performance against targets, discuss corrective actions, and escalate where commitments are not being met. | - Makes emergency related cost and downtime visible to the people who are best placed to fix the underlying issues so action is more likely to be taken.<br><br>- Encourages proactive behaviour from service owners because they are measured and recognised based on how they reduce emergency events and their financial impact over time.<br><br>- Aligns budgets and investment decisions with real outcomes because spending can be directed toward the services that generate the highest emergency cost and show the most potential for improvement.<br><br>- Helps leadership quickly see where strong ownership exists and where additional support, coaching, or structural change might be required.<br><br> | **RM saved = Δemergency_minutes × {rmmin_snip}** per owner; use total **{int(total_em_min) if has_costmins else 0:,} min** to size opportunity. | Recurrent high bars indicate governance gaps; attribution closes the loop. |
| Weekly emergency review board | **Phase 1 – Inspect:** Hold a short weekly review where all emergencies from the last week are summarised, including cause, duration, impact, and whether they could have been avoided or planned differently.<br><br>**Phase 2 – Actions:** For each pattern that appears more than once, create clear follow up actions such as fixes, process changes, or automation work and log them in a tracked backlog so that they do not get lost.<br><br>**Phase 3 – Track:** Publish a simple burn down chart of outstanding emergency related actions and show how weekly emergency counts change over time so that the organisation can see progress. | - Drives continuous learning from every emergency because each event is discussed, understood, and translated into concrete improvement actions.<br><br>- Reduces the long term run rate of emergencies as recurring root causes are systematically addressed and turned into planned changes or design fixes.<br><br>- Makes emergency work more transparent across teams and management so that hidden issues do not accumulate silently until they become major crises.<br><br>- Provides a clear narrative to stakeholders that the organisation is not only reacting to emergencies but also actively working to prevent them in future weeks.<br><br> | **Benefit = incidents_prevented × avg_downtime_min × {rmmin_snip}** where available. | Spike/valley pattern justifies a regular cadence of reviews. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Strengthen change control for emergencies | **Phase 1 – Risk score:** Even when time is tight, apply a simple but consistent risk score to each emergency change and ensure at least one accountable approver validates the risk level so that unsafe changes are less likely to be rushed through.<br><br>**Phase 2 – Checklist:** Use a short mandatory checklist that covers backup creation, verification steps, and rollback points so that essential safeguards are not skipped even under pressure.<br><br>**Phase 3 – Telemetry:** Require that basic monitoring and key metrics are actively watched after deployment so that any degradation is detected quickly and can trigger a rollback. | - Reduces the number of unstable emergency deployments because even urgent work passes through a lightweight risk and quality filter before reaching production.<br><br>- Lowers the chance that changes will cause cascading failures because backups and rollback points are always considered and prepared in advance.<br><br>- Improves mean time to recover because teams monitor the system closely after emergency changes and can react rapidly to unexpected behaviour.<br><br>- Standardises how emergencies are handled so that outcomes are more predictable across different teams and shifts.<br><br> | **MTTR reduction × incident_count** on months like **{peak_month}**. | Fluctuation in monthly bars suggests control gaps during peaks. |
| Golden-path runbooks for hot fixes | **Phase 1 – Standardize:** Develop clear golden path runbooks that describe step by step how to perform the most common emergency changes for each key service class so that engineers know exactly what to do when time is limited.<br><br>**Phase 2 – Drill:** Use quarterly simulations or game days to practice executing these runbooks under realistic conditions so that teams are confident and fluent in using them.<br><br>**Phase 3 – Update:** Keep the runbooks updated whenever platforms, tools, or architectures change so that instructions remain accurate and effective. | - Accelerates the execution of hot fixes because engineers do not need to improvise procedures during stressful situations and can follow a proven path instead.<br><br>- Reduces human error because consistent and tested steps are followed rather than relying on memory or ad hoc decisions when pressure is high.<br><br>- Ensures more consistent outcomes across different teams and shifts because everyone is working from the same agreed golden path.<br><br>- Helps new team members become productive more quickly during emergencies because they can rely on clear documentation instead of tribal knowledge.<br><br> | **Time saved/change × #emergency_changes** (use total **{total}**). | Repeated emergencies benefit from templated steps. |
| Canary deployment for emergency patches | **Phase 1 – Scope:** Define a safe subset of nodes, users, or regions that can receive emergency patches first so that the impact of any defects is limited to a controlled audience.<br><br>**Phase 2 – Ramp:** When metrics and user experience stay healthy, progressively expand the deployment to more nodes or users, following a clear ramp up plan that can be paused at any sign of trouble.<br><br>**Phase 3 – Abort:** Configure automated or manual rollback triggers when key metrics degrade so that the patch can be reversed quickly before it harms the full environment. | - Limits the blast radius of bad emergency patches because they are first tested in a controlled slice of the environment instead of being rolled out everywhere at once.<br><br>- Reduces the severity of incidents caused by emergency changes because problems are discovered and contained early in the rollout process.<br><br>- Builds confidence that the organisation can respond quickly to critical issues without having to choose between speed and safety.<br><br>- Provides more observability into how emergency patches behave in real conditions which allows better tuning and better decisions for subsequent steps.<br><br> | **Downtime avoided = bad_window_min × {rmmin_snip}**. | Peak months imply higher risk of wide-impact pushes. |
| Telemetry gates pre/post change | **Phase 1 – KPIs:** Define a small set of critical KPIs such as latency, error rate, and resource saturation that will be used as guardrails before and after emergency changes so that everyone knows what healthy looks like.<br><br>**Phase 2 – Block:** Before rollout, block or delay changes if pre change metrics already show instability and automatically stop rollout if these KPIs degrade beyond defined thresholds while the change is being deployed.<br><br>**Phase 3 – Verify:** After the change, require that KPIs remain within acceptable ranges for a minimum observation period before the incident is considered fully resolved and closed. | - Protects availability by preventing changes from being applied when the system is already unstable or becomes unstable during deployment.<br><br>- Reduces the length and severity of outages because automatic or procedural gates stop harmful changes from continuing to roll out when problems are detected early.<br><br>- Makes the decision to continue, pause, or roll back a change more objective and more data driven which improves consistency during stressful incidents.<br><br>- Reinforces a culture where real time data is central to change decisions especially when risk is high.<br><br> | **Incidents_prevented × avg_downtime_min** using months near **{avg_d:.1f} min** baseline. | Uptime (graph 1) dips correspond to high downtime bars (graph 2). |
| Service-level throttles during emergencies | **Phase 1 – Controls:** Design technical controls, such as rate limiting or feature flags, that allow you to temporarily reduce non critical load or disable non essential features during emergency work so that the core system is less stressed.<br><br>**Phase 2 – Monitor:** While throttles are active, closely monitor key SLO metrics to ensure that critical journeys remain within acceptable performance and error ranges even if overall load is constrained.<br><br>**Phase 3 – Restore:** Once stability is confirmed, gradually remove throttles and restore normal service levels while watching metrics so that users return to full functionality safely. | - Keeps the most important user journeys available during emergency changes by shedding or slowing less critical traffic instead of allowing the whole system to fail under pressure.<br><br>- Reduces visible error rates for customers by prioritising core functions over optional features when the system is under strain.<br><br>- Provides a safety mechanism that can be activated quickly whenever capacity or stability is threatened which lowers the risk of full outages.<br><br>- Helps teams understand how the system behaves under controlled throttling which can inform longer term capacity and resilience planning.<br><br> | **ΔUptime% → downtime_min_saved × {rmmin_snip}**. | Lower dips when throttles applied during high-risk months. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Real-time comms during emergencies | **Phase 1 – Status:** Maintain a live status page or communication channel that shows the current state of the emergency, the systems affected, and the approximate ETA so that users can quickly understand what is happening.<br><br>**Phase 2 – Guidance:** Provide clear and simple workarounds and indicate which user groups are impacted so that people can adjust their work and avoid repeatedly calling support for the same information.<br><br>**Phase 3 – Closure:** After the issue is resolved, publish a short closure message summarising the fix and next steps so that users know the situation is stable again. | - Reduces the number of inbound tickets and calls during emergencies because many users get the information they need directly from the status updates.<br><br>- Lowers user anxiety and frustration because they can see that the problem is recognised and being worked on rather than feeling that nothing is happening behind the scenes.<br><br>- Enables users to make better decisions about their own work because they understand which functions are affected and for how long they are likely to be affected.<br><br>- Improves the perceived professionalism of the service team because communication appears structured and timely even under stress.<br><br> | **Ticket_deflection × handling_cost** during months like **{peak_month}**. | Users feel impact most during peaks; transparency reduces follow-ups. |
| Post-change customer note | **Phase 1 – Explain:** After a major emergency change, send a short note to affected customers that explains in plain language what went wrong, what was done to fix it, and what is being changed to prevent future recurrences.<br><br>**Phase 2 – Timeline:** Include a concise timeline of key events such as detection, mitigation, fix deployment, and verification so that customers understand how quickly and systematically the issue was addressed.<br><br>**Phase 3 – Assurance:** Clearly describe which safeguards are now in place and invite customers to contact a defined channel if they have further concerns. | - Helps restore trust because customers see that the team acknowledges the impact and is transparent about the cause and remediation steps.<br><br>- Reduces repeat queries about the same incident because the main questions are anticipated and answered proactively in the communication.<br><br>- Improves retention and long term relationships because customers feel that their experience is taken seriously and that the provider is committed to continuous improvement.<br><br>- Provides a structured opportunity for customers to give feedback which can further improve processes and communication for future events.<br><br> | **Retention/CSAT uplift** measured after peak months. | High-frequency months require explicit transparency. |
| Preferred-time emergency windows (when possible) | **Phase 1 – Identify:** Work with key customers to identify their most critical operating hours and any preferred windows where emergency actions would cause the least disruption to their business.<br><br>**Phase 2 – Align:** For emergency work that can be delayed by a few hours without severe risk, schedule it within these preferred windows and confirm the plan with stakeholders so that everyone knows what to expect.<br><br>**Phase 3 – Review:** After a few cycles, review whether the chosen windows are still appropriate and adjust them based on customer feedback and usage patterns. | - Reduces the perceived pain of emergency work because customers see that their specific schedules and business peaks are being respected where possible.<br><br>- Protects the most critical workloads of key customers by avoiding disruptive changes at times when they are most dependent on the service.<br><br>- Builds stronger relationships as customers feel they are being treated as partners in managing risk rather than passive recipients of unexpected downtime.<br><br>- Provides both sides with a predictable framework for handling necessary urgent work which reduces conflict and last minute negotiation.<br><br> | **Visible_minutes_avoided × {rmmin_snip}**. | Align timing where counts are highest (e.g., **{peak_month}**). |
| “What changed” digest | **Phase 1 – Weekly:** Prepare a simple weekly digest that summarises all emergency and urgent changes, including what changed, why it was needed, and whether there were any user visible effects so that stakeholders stay informed.<br><br>**Phase 2 – Channels:** Share this digest through channels that users and business owners already follow, such as email, Teams, or a portal announcement page so that it is easy to access.<br><br>**Phase 3 – Metrics:** Track open and read rates as well as feedback on usefulness so that the format can be improved over time. | - Lowers anxiety and speculation because users are not left guessing about what is happening and what might have affected them.<br><br>- Reduces ad hoc questions to support teams about recent changes because the main details are already packaged and distributed in a predictable rhythm.<br><br>- Helps stakeholders plan better because they have visibility of change activity that might relate to performance or behaviour they observe in their own systems.<br><br>- Reinforces transparency and creates a habit of communication that builds trust over the long term.<br><br> | **Ticket_deflection × handling_cost**. | Frequent urgencies create uncertainty; digest reduces noise. |
| Feedback loop with support | **Phase 1 – Capture:** After emergency changes, capture common user pain points and frequent questions reported to the support team, tagging them by root cause and change window so that patterns can be analysed.<br><br>**Phase 2 – Act:** Turn these recurring issues into updated knowledge base articles, improved workarounds, or additional changes so that future users can get faster and more accurate help.<br><br>**Phase 3 – Measure:** Track reductions in repeat contacts and average time to answer for these topics to see how much the feedback loop is improving the experience. | - Ensures that real user experience during and after emergencies feeds directly into better documentation, processes, and product fixes.<br><br>- Reduces the number of repeated contacts about the same issues because the knowledge base becomes richer and more closely aligned with actual user problems.<br><br>- Shortens support interactions because agents have better and more focused content to share with users who are affected by similar incidents in the future.<br><br>- Shows users that their feedback leads to visible changes which encourages them to share information that can further strengthen the service.<br><br> | **Repeat_contact_drop × handling_cost**. | Peak months correlate with call spikes; loops reduce pressure. |
"""
                }

                render_cio_tables("CIO – Emergency Changes Made to Services", cio_7a)
        else:
            st.warning(f"⚠️ Missing required columns: {required - set(df.columns)}")

    # ----------------------------------------------
    # 7b. Impact of Emergency Changes on Service Availability
    # ----------------------------------------------
    with st.expander("📌 Impact of Emergency Changes on Service Availability"):
        required = {"report_date", "service_name", "change_type", "uptime_percentage", "downtime_minutes"}
        # adapt again if needed
        if "change_type" not in df.columns and "maintenance_type" in df.columns:
            df = df.copy()
            df["change_type"] = df["maintenance_type"]

        if required.issubset(df.columns):
            emer_df = df[df["change_type"].astype(str).str.lower().eq("emergency")].copy()
            if emer_df.empty:
                st.info("✅ No emergency change data found for impact analysis.")
            else:
                emer_df["report_date"] = pd.to_datetime(emer_df["report_date"], errors="coerce")
                emer_df["month"] = emer_df["report_date"].dt.to_period("M").astype(str)
                emer_df["uptime_percentage"] = _to_num(emer_df["uptime_percentage"])
                emer_df["downtime_minutes"] = _to_num(emer_df["downtime_minutes"])

                impact = emer_df.groupby("month", as_index=False).agg(
                    avg_uptime=("uptime_percentage", "mean"),
                    total_downtime=("downtime_minutes", "sum")
                )

                # Calculate RM/min for emergencies if cost column exists
                avg_rm_per_min = np.nan
                total_cost = np.nan
                tot_min_all = float(impact["total_downtime"].sum())
                if "estimated_cost_downtime" in emer_df.columns:
                    emer_df["estimated_cost_downtime"] = _to_num(emer_df["estimated_cost_downtime"])
                    total_cost = float(emer_df["estimated_cost_downtime"].sum())
                    if tot_min_all > 0:
                        avg_rm_per_min = total_cost / tot_min_all

                # --- Graph 1: Average Uptime during emergency months
                fig1 = px.line(
                    impact,
                    x="month",
                    y="avg_uptime",
                    title="Average Uptime During Emergency Change Months",
                    markers=True,
                    labels={"month": "Month", "avg_uptime": "Average Uptime (%)"},
                    color_discrete_sequence=[PRIMARY_BLUE],
                    template="plotly_white",
                )
                st.plotly_chart(fig1, use_container_width=True)

                # --- Analysis for Graph 1 (own analysis)
                peak_u = impact.loc[impact["avg_uptime"].idxmax()]
                low_u = impact.loc[impact["avg_uptime"].idxmin()]
                mean_u = float(impact["avg_uptime"].mean())
                st.markdown("### Analysis — Average Uptime (Graph 1)")
                st.write(
f"""**What this graph is:** A **line chart** of **average uptime (%)** by month **that had emergency changes**.  
**X-axis:** Calendar month.  
**Y-axis:** Mean uptime percentage for those months.

**What it shows in your data:**  
- **Highest uptime month:** **{peak_u['month']}** at **{float(peak_u['avg_uptime']):.2f}%**.  
- **Lowest uptime month:** **{low_u['month']}** at **{float(low_u['avg_uptime']):.2f}%**.  
- **Average across emergency months:** **{mean_u:.2f}%**.

**Overall:** Uptime volatility across emergency months indicates **availability risk**; sustained dips below **{mean_u:.2f}%** signal the need for **pre-change gates** and **faster rollback**.

**How to read it operationally:**  
- **Gap = risk delta:** Distance from your target SLO to the line reflects exposure in emergency months.  
- **Lead–lag:** If uptime dips **after** emergency spikes, add **post-deploy checks** and **rollback triggers**.  
- **Recovery strength:** Faster rebounds after dips mean healthier incident handling; slow rebounds indicate **latent faults**.  
- **Control:** Keep the series near a **high, flat line** via freeze policies, canaries, and owner reviews.

**Why this matters:** Protecting uptime in emergency periods preserves **SLA attainment**, reduces complaint volume, and stabilizes customer experience."""
                )

                # --- Graph 2: Total downtime minutes during emergency months
                fig2 = px.bar(
                    impact,
                    x="month",
                    y="total_downtime",
                    text="total_downtime",
                    title="Total Downtime During Emergency Change Months (Minutes)",
                    labels={"month": "Month", "total_downtime": "Downtime (Minutes)"},
                    color_discrete_sequence=[SECONDARY_BLUE],
                    template="plotly_white",
                )
                fig2.update_traces(texttemplate="%{text:.0f}", textposition="outside", cliponaxis=False)
                st.plotly_chart(fig2, use_container_width=True)

                # --- Analysis for Graph 2 (own analysis that references graph above)
                peak_d = impact.loc[impact["total_downtime"].idxmax()]
                min_d = impact.loc[impact["total_downtime"].idxmin()]
                avg_d = float(impact["total_downtime"].mean())
                st.markdown("### Analysis — Total Downtime (Graph 2)")
                cost_line = f"Total **RM {total_cost:,.0f}**, **Avg RM/min ≈ {avg_rm_per_min:,.2f}**." if avg_rm_per_min == avg_rm_per_min else "Cost per minute can be computed when available."
                st.write(
f"""**What this graph is:** A **bar chart** of **total downtime minutes** in months that contained emergency changes.  
**X-axis:** Calendar month.  
**Y-axis:** Total downtime accumulated (minutes).

**What it shows in your data:**  
- **Highest downtime month:** **{peak_d['month']}** with **{int(peak_d['total_downtime'])} minutes**.  
- **Lowest downtime month:** **{min_d['month']}** with **{int(min_d['total_downtime'])} minutes**.  
- **Average downtime per emergency month:** **{avg_d:.1f} minutes**.  
- **Emergency-month cost profile:** {cost_line}

**Overall:** As the **downtime bars** rise, the **uptime line above** typically dips; this inverse pattern (graph 1 vs graph 2) is the signature of **high-risk emergency changes**.

**How to read it operationally:**  
- **Compression target:** Shorten the **{peak_d['month']}** window first; each minute removed saves **RM/min** at the observed rate.  
- **Timing lens:** Rebase emergency actions to off-peak to reduce **revenue-time overlap**.  
- **Guardrails:** Enforce **auto-rollback** and **SLO gates** so bars cannot climb unchecked.

**Why this matters:** Downtime concentrated in a few emergency months drives **disproportionate cost and user pain**; compressing those windows yields the fastest ROI and visible reliability gains."""
                )

                # --- CIO Table (≥3 recs/pillar, phased, using real values)
                rmmin_txt = f"Avg RM/min≈RM {avg_rm_per_min:,.2f}" if avg_rm_per_min == avg_rm_per_min else "RM/min (from data)"
                cio_7b = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Reduce emergency frequency via pre-prod validation | **Phase 1 – Simulate:** Use the failures that appeared in **{peak_d['month']}** as scenarios in a staging or test environment and replay them under synthetic load so that you fully understand how they arise before making changes.<br><br>**Phase 2 – Gate:** Introduce a rule that no production push, even in an emergency, is allowed until these scenarios pass in non production so that obvious regressions are caught early.<br><br>**Phase 3 – Track:** Compare emergency counts and downtime minutes for the following cycles to see whether better pre production validation is reducing the need for urgent production fixes. | - Reduces the number of emergencies that are caused by defects which could have been identified with basic simulation and testing before deployment.<br><br>- Lowers overtime and stress on engineers because fewer last minute fixes are needed when issues are caught and corrected earlier in the process.<br><br>- Decreases the amount of downtime during revenue hours because the production environment receives more stable changes that have been tested under realistic conditions.<br><br>- Builds stronger discipline around validation so that even urgent changes maintain a minimum quality bar before reaching customers.<br><br> | **RM saved = minutes_avoided × {rmmin_txt}** using high month **{peak_d['month']} ({int(peak_d['total_downtime'])} min)** as baseline. | Tallest downtime bar in **{peak_d['month']}** quantifies the reduction target. |
| Automated rollback on SLO breach | **Phase 1 – Define:** Select a small set of critical SLO metrics such as availability, latency, and error rate, and define clear thresholds that represent unacceptable degradation during or after a change so that there is no confusion about when the system is at risk.<br><br>**Phase 2 – Automate:** Implement logic that automatically triggers a rollback when these thresholds are breached during an emergency change without waiting for manual approval so that harmful changes are reversed quickly.<br><br>**Phase 3 – Audit:** After each rollback event, compare the time to rollback and total downtime against previous incidents to ensure that the automation is shortening bad windows. | - Caps the worst case duration of outages because the system automatically returns to the last known good state as soon as critical metrics cross defined boundaries.<br><br>- Reduces dependence on manual human intervention at stressful moments which lowers the risk of slow responses or incorrect decisions when people are under pressure.<br><br>- Improves SLA compliance because extended bad windows are avoided and incidents are kept shorter and more controlled.<br><br>- Provides real data about how often rollbacks are triggered and how much downtime they prevent which supports better decision making about future automation investments.<br><br> | **RM avoided = bad_window_min × {rmmin_txt}**; use prior peaks to size bad_window_min. | Uptime dips in months with large bars show extended bad windows. |
| Off-peak gating for emergencies | **Phase 1 – Classify:** Differentiate true P1 emergencies that must be handled immediately from lower priority urgent changes that can be safely delayed to off peak times and document examples and criteria so decisions are consistent.<br><br>**Phase 2 – Schedule:** For non P1 items, commit to executing them in off peak windows within the same day wherever possible and communicate these planned times to stakeholders so that expectations are managed.<br><br>**Phase 3 – Review:** At the end of each month, examine whether off peak gating was respected, how many exceptions were made, and what impact this had on downtime and user experience. | - Reduces the amount of downtime that occurs during the most valuable business hours because many urgent but not truly critical changes are moved to lower impact times.<br><br>- Decreases the number of escalations and complaints during peak usage periods because fewer disruptive changes happen when customers are heavily relying on the service.<br><br>- Allows more thoughtful execution of urgent work because it is done in calmer off peak conditions where there is slightly more time to validate and monitor the change.<br><br>- Provides teams with data on how many emergencies are genuinely time critical compared to those that could safely be handled in a controlled window.<br><br> | **ΔRM/min (peak→off-peak) × window_minutes**; minutes from **{peak_d['month']}** = **{int(peak_d['total_downtime'])}**. | High downtime months signal mis-timed pushes. |
| Owner-level cost dashboards | **Phase 1 – Attribute:** Use emergency change data to calculate total downtime minutes and estimated cost by service and owner for each month so that the financial footprint of emergencies is clearly visible per area.<br><br>**Phase 2 – Target:** Work with each owner to set achievable monthly reduction goals in terms of downtime minutes, emergency count, or cost so that everyone has a measurable objective tied to their domain.<br><br>**Phase 3 – Incent:** Share these dashboards in governance forums, recognise owners who show strong improvements, and support those who are behind with problem solving and additional resources. | - Encourages owners to actively manage emergency related risk in their services because they can see how it affects costs, SLAs, and their own performance metrics.<br><br>- Helps leadership focus investment and support on the services where improvements will deliver the largest reduction in downtime cost.<br><br>- Promotes healthy competition and a sense of ownership among teams as improvements and cost reductions become visible and celebrated.<br><br>- Creates a consistent way of tracking progress over time so that the organisation can see whether emergency risks are moving in the right direction across the portfolio.<br><br> | **RM saved = Δemergency_minutes × {rmmin_txt}** portfolio-wide. | Concentration of minutes in few months highlights ownership gaps. |
| Convert top issues to planned epics | **Phase 1 – Identify:** Analyse the incidents and downtime in **{peak_d['month']}** to find a small set of recurring problem themes that generate a large share of emergency change activity and downtime minutes.<br><br>**Phase 2 – Roadmap:** Turn these themes into structured engineering epics with clear objectives, scope, and timelines so that work on them is planned, prioritised, and visible in delivery cycles rather than treated as scattered urgent tasks.<br><br>**Phase 3 – Verify:** After the epics are delivered, compare emergency incidents and downtime related to these themes against prior months to ensure that the structural fixes have reduced the need for urgent interventions. | - Moves effort away from repeatedly patching symptoms and towards solving the underlying design or process issues that create emergencies in the first place.<br><br>- Lowers long term cost and stress because recurring emergency patterns are gradually eliminated and do not keep resurfacing each month.<br><br>- Provides a clear story to stakeholders about how a cluster of high impact issues is being addressed strategically instead of only through repeated tactical responses.<br><br>- Helps engineering teams focus their limited time on the changes that will make the biggest difference to downtime and reliability rather than on scattered minor fixes.<br><br> | **Benefit = incidents_prevented × avg_minutes × {rmmin_txt}**. | Pattern shows recurring urgent themes in high bars. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Canary + progressive rollout | **Phase 1 – Subset:** Start emergency deployments by releasing changes to a small subset of nodes, regions, or users so that behaviour can be observed in a limited and controlled context before scaling up.<br><br>**Phase 2 – Ramp:** When key metrics stay stable and no major issues are reported, gradually increase the number of nodes or users that receive the change by following predefined stepwise ramp plans.<br><br>**Phase 3 – Abort:** If metrics degrade or issues are reported at any stage in the rollout, immediately stop further expansion and roll back the change to minimise impact. | - Stabilises uptime during emergency changes because issues are discovered early in the rollout process instead of after the change has reached the entire environment.<br><br>- Reduces the blast radius of failed emergency deployments because only a small portion of users or infrastructure experiences negative effects before a rollback is triggered.<br><br>- Provides clearer data on how a change behaves under real conditions which improves both debugging and decisions about whether to proceed or revert.<br><br>- Makes emergency responses more resilient and controlled without significantly slowing down the time needed to address critical problems.<br><br> | **ΔDowntime_min in peak month × {rmmin_txt}** comparing before and after canary adoption. | Larger bars indicate global rollout risks mitigated by canaries. |
| SLO gates pre/post change | **Phase 1 – KPIs:** Select the most important KPIs that represent user experience, such as availability, key transaction success rate, or response time, and set clear SLO thresholds that must be respected before and after emergency changes.<br><br>**Phase 2 – Block:** Do not start or continue a deployment if these metrics are already below acceptable levels, and pause or roll back changes if metrics fall below thresholds during or immediately after the emergency change process.<br><br>**Phase 3 – Verify:** Only close incidents and consider the emergency work complete once the KPIs have returned to healthy levels and stayed there for a defined stabilisation period. | - Preserves availability during risky periods by preventing emergency changes from being executed when the environment is already unstable or vulnerable.<br><br>- Reduces the number of prolonged incidents because once metrics indicate a problem deployments are halted and reversed before damage spreads or extends in time.<br><br>- Makes incident response more objective since decisions to proceed or roll back rely on quantitative data rather than subjective judgement under stress.<br><br>- Improves the reliability of emergency handling over time as the organisation learns which SLO thresholds best protect user experience during changes.<br><br> | **Incidents_prevented × avg_downtime_min** using months near **{avg_d:.1f} min** baseline. | Uptime (graph 1) dips correspond to high downtime bars (graph 2). |
| Emergency runbooks with timeboxes | **Phase 1 – SOPs:** Create emergency runbooks that clearly define the steps for diagnosing and fixing incidents and include explicit maximum time limits for each step so that teams know when to escalate or roll back instead of continuing indefinitely.<br><br>**Phase 2 – Tools:** Provide scripts and automation that support key runbook steps such as backups, verifications, or rollbacks so that they can be executed quickly and consistently under pressure.<br><br>**Phase 3 – Drill:** Run regular simulations where teams practice following these timeboxed runbooks so that the process becomes familiar and effective in real incidents. | - Speeds up emergency handling because engineers have a pre agreed path and time limit for each action rather than improvising or getting stuck on a single step.<br><br>- Reduces the risk of long outages caused by hesitation or indecision because timeboxes define when to move to the next action or trigger a rollback if progress is not made.<br><br>- Increases consistency across teams and shifts because everyone follows the same tested playbook and uses the same tools for critical operations.<br><br>- Improves training and readiness because new staff can learn from and practice with the same structured runbooks used during actual emergencies.<br><br> | **Time saved/change × #changes** (refer to monthly counts from 7a). | Repeated emergencies benefit from standardized flows. |
| Service throttling during changes | **Phase 1 – Controls:** Design and implement technical mechanisms that allow non critical features or heavy optional workloads to be throttled, paused, or deprioritised during emergency changes so that the system has more capacity to handle core functions.<br><br>**Phase 2 – Monitor:** While throttling is in effect, monitor key SLOs to ensure that the critical user journeys remain healthy even if some less important features are temporarily constrained.<br><br>**Phase 3 – Normalize:** After stability is achieved, gradually remove the throttling, returning the system to normal behaviour while continuing to watch metrics for any delayed effects. | - Maintains higher uptime for essential services and transactions during emergency periods by reducing the burden of non critical workloads on the system.<br><br>- Reduces visible failures for end users because core paths stay available and responsive even if certain optional features are momentarily restricted.<br><br>- Provides an additional safety lever that can be used repeatedly in high risk situations which increases operational resilience with minimal long term impact.<br><br>- Gives teams valuable insight into which functions are truly critical to protect and which can be temporarily limited without significantly harming overall user satisfaction.<br><br> | **ΔUptime% × total_minutes_in_month × value/min**; relate to **{mean_u:.2f}%** average. | Downtime spikes often occur under load pressure. |
| Post-change RCAs within 48h | **Phase 1 – Triage:** Within 48 hours of an emergency change that affected uptime, conduct a structured review to identify the root causes, contributing factors, and decision points that led to the incident so that the understanding remains fresh and detailed.<br><br>**Phase 2 – Actions:** Translate key findings into specific corrective actions, assign clear owners and due dates, and record them in a trackable system so that they are not forgotten after the crisis has passed.<br><br>**Phase 3 – Verify:** Check in the next cycle whether similar incidents reoccurred and whether mean time to recover and downtime decreased and adjust actions if the expected improvements did not appear. | - Prevents the same weaknesses from causing repeat incidents because lessons learned are converted into real changes rather than staying only in post incident discussions.<br><br>- Steadily improves the organisation’s ability to recover from emergencies as the most painful and time consuming aspects of past incidents are addressed through targeted actions.<br><br>- Increases accountability and follow through since each action has an owner and timeframe that can be reviewed in governance forums.<br><br>- Contributes to a culture of continuous learning where emergencies are seen as opportunities to strengthen systems and processes rather than just one off crises.<br><br> | **Repeat_incidents_drop × avg_minutes × {rmmin_txt}**. | Bar clusters by month indicate recurring issues needing fast RCAs. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Live status page + ETAs | **Phase 1 – Publish:** Maintain a live status page that shows which services are affected by an emergency, the current state of those services, and initial ETAs so that stakeholders can check on progress without contacting support.<br><br>**Phase 2 – Update:** As the situation evolves, update milestones and ETAs so that users can see whether the resolution is on track or if timelines have changed and this reduces uncertainty and speculation.<br><br>**Phase 3 – Close:** When the incident is resolved, clearly mark it as closed, summarise what actions were taken, and point to any additional communications or RCAs so that the story is complete. | - Reduces inbound tickets and calls because users have a central and always available source of truth about the emergency.<br><br>- Creates a calmer environment for both users and support staff because progress is visible and expectations are managed with updated ETAs instead of silence.<br><br>- Builds trust in the service provider because openness during difficult moments is often seen as a sign of maturity and accountability.<br><br>- Helps internal teams as well because everyone shares the same view of incident status which improves coordination and decision making.<br><br> | **Ticket_deflection × handling_cost** for high months like **{peak_d['month']}**. | High-downtime months drive contact spikes; visibility deflects calls. |
| Workarounds for critical journeys | **Phase 1 – Identify:** Use data from **{peak_d['month']}** to identify which user journeys were most affected by downtime and which of those journeys are most critical to business operations so that effort is focused on the right areas.<br><br>**Phase 2 – Guide:** Develop and publish clear step by step workaround instructions that help users continue or partially continue those critical tasks during similar incidents in the future.<br><br>**Phase 3 – Track:** Monitor how often these workarounds are used and how they affect ticket volumes and user productivity so that you know if they are effective or need to be improved. | - Keeps users more productive during periods of degraded service because they have practical alternatives they can apply while waiting for full restoration.<br><br>- Reduces the sense of helplessness that often accompanies outages because users feel supported with concrete options instead of just being told to wait.<br><br>- Decreases pressure on support teams because many users can move forward using documented steps instead of requiring individual coaching through each case.<br><br>- Provides feedback on which processes are most sensitive to downtime which can inform future automation or prioritisation decisions.<br><br> | **Visible_minutes_avoided × {rmmin_txt}** in peak months. | Large bars indicate high user impact where workarounds help most. |
| Post-change customer note & timeline | **Phase 1 – Summarize:** After significant emergencies that affected uptime, send a concise summary that explains what failed, what impact users experienced, and what was done to fix the issue in straightforward language.<br><br>**Phase 2 – Prevent:** Include a short description of the preventive measures being taken so that users see how the incident is being used to improve the service rather than being treated as an isolated event.<br><br>**Phase 3 – Invite:** Provide a clear and appropriate channel for feedback or questions so that customers know how to respond if they still have concerns or if they notice lingering effects. | - Restores credibility after an outage because users see that the provider is willing to explain the situation instead of hiding behind technical jargon or silence.<br><br>- Reduces repeated queries about the incident because the main points are proactively answered which saves time for both users and support staff.<br><br>- Helps lift satisfaction over time because customers recognise that issues are taken seriously and are followed by meaningful improvements.<br><br>- Creates a record that can be referred back to in future discussions about reliability which makes conversations more factual and less emotional.<br><br> | **Retention/CSAT uplift** measured after communication. | Uptime dips need transparent follow-up to rebuild trust. |
| Customer co-planned emergency windows | **Phase 1 – Engage:** Work closely with critical customers to understand their most sensitive business cycles and co design acceptable emergency change windows that minimise disruption for both parties.<br><br>**Phase 2 – Lock:** Record these windows in shared calendars, send recurring reminders, and align internal processes so that teams automatically use these windows when emergency work for those customers is required.<br><br>**Phase 3 – Review:** At least quarterly, review whether the agreed windows are still appropriate based on changing customer needs and adjust as necessary to keep alignment strong. | - Reduces friction and conflict when emergency work must be carried out because customers have already been involved in choosing the least harmful times.<br><br>- Protects revenue and critical operations for key accounts because emergency activities are less likely to clash with their peak business periods.<br><br>- Deepens relationships with important customers by showing a willingness to design operational processes around their realities instead of only around internal convenience.<br><br>- Lowers churn risk for high value accounts because they experience the provider as a partner in managing risk rather than as a source of unpredictable disruption.<br><br> | **Churn avoided × ACV** for critical accounts. | Focus co-planning on months with larger bars like **{peak_d['month']}**. |
| Feedback loop via support analytics | **Phase 1 – Capture:** Tag support tickets and complaints related to each emergency by month, service, and cause so that you can analyse how users experienced the downtime shown in the graphs.<br><br>**Phase 2 – Prioritize:** Use these tags to identify the most common or most painful themes from the user perspective and prioritise fixes or communication improvements that address those themes.<br><br>**Phase 3 – Measure:** Track changes in repeat contact rates and complaint counts after the fixes and communication improvements are implemented so that you know whether the feedback loop is working. | - Ensures that technical improvements are guided by real user pain rather than only by internal assumptions about what matters most.<br><br>- Reduces repeated contacts and frustration because the issues that generate the most complaints are directly targeted for improvement in subsequent changes or documentation updates.<br><br>- Helps support teams feel more effective because the recurring problems they handle are gradually reduced instead of endlessly repeated.<br><br>- Closes the loop between reliability data and customer sentiment which improves prioritisation for both technical and communication work in future cycles.<br><br> | **Repeat_contact_drop × handling_cost** referencing peak months. | Complaint spikes map to downtime spikes—closing loop reduces repeats. |
"""
                }
                render_cio_tables("CIO – Impact of Emergency Changes on Service Availability", cio_7b)
        else:
            st.warning(f"⚠️ Missing required columns: {required - set(df.columns)}")
