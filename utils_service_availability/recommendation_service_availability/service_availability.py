# utils_service_availability/recommendation_service_availability/service_availability_metrics.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================================================
# Helper Function for CIO Tables
# ============================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# ============================================================
# 3️⃣ Service Availability Metrics
# ============================================================
def service_availability(df: pd.DataFrame):

    # ============================================================
    # 3a. Availability Statistics per Service
    # ============================================================
    with st.expander("📌 Availability Statistics per Service (Uptime %)"):
        required = {"service_name", "uptime_percentage"}
        if required.issubset(df.columns):
            df_plot = df.copy()
            uptime_summary = (
                df_plot.groupby("service_name", as_index=False)["uptime_percentage"]
                .mean()
                .sort_values("uptime_percentage", ascending=False)
            )

            fig = px.bar(
                uptime_summary,
                x="service_name",
                y="uptime_percentage",
                title="Average Uptime (%) per Service",
                labels={"service_name": "Service Name", "uptime_percentage": "Average Uptime (%)"},
                text="uptime_percentage"
            )
            fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            best = uptime_summary.iloc[0]
            worst = uptime_summary.iloc[-1]
            avg = uptime_summary["uptime_percentage"].mean()

            # Optional pools pulled from the same dataset (guarded)
            cost_available = "estimated_cost_downtime" in df.columns
            minutes_available = "downtime_minutes" in df.columns
            incidents_available = "incident_count" in df.columns

            if cost_available:
                svc_cost = (
                    df.groupby("service_name", as_index=False)["estimated_cost_downtime"]
                      .sum()
                      .set_index("service_name")
                )
                worst_cost_val = float(svc_cost.loc[worst["service_name"]]["estimated_cost_downtime"]) if worst["service_name"] in svc_cost.index else 0.0
                best_cost_val  = float(svc_cost.loc[best["service_name"]]["estimated_cost_downtime"]) if best["service_name"] in svc_cost.index else 0.0
                total_cost_val = float(df["estimated_cost_downtime"].fillna(0).sum())
            else:
                worst_cost_val = best_cost_val = total_cost_val = 0.0

            if minutes_available:
                svc_min = (
                    df.groupby("service_name", as_index=False)["downtime_minutes"]
                      .sum()
                      .set_index("service_name")
                )
                worst_min_val = float(svc_min.loc[worst["service_name"]]["downtime_minutes"]) if worst["service_name"] in svc_min.index else 0.0
                total_min_val = float(df["downtime_minutes"].fillna(0).sum())
            else:
                worst_min_val = total_min_val = 0.0

            st.markdown("### 📈 Analysis — Availability Performance")
            st.write(
f"""**What this graph is:** A ranked bar chart showing **average uptime (%)** by **service** across the reporting period.  
- **X-axis:** Service name.  
- **Y-axis:** Average uptime percentage.

**What it shows in your data:** The **highest uptime** is **{best['service_name']}** at **{best['uptime_percentage']:.2f}%**, and the **lowest uptime** is **{worst['service_name']}** at **{worst['uptime_percentage']:.2f}%**. The **overall average** across services is **{avg:.2f}%**.{" The lowest-uptime service also contributes RM "
+ f"{worst_cost_val:,.0f} of downtime cost" if cost_available and worst_cost_val > 0 else ""}{" and "
+ f"{int(total_min_val):,} total minutes are recorded in the period" if minutes_available and total_min_val > 0 else ""}.

**How to read it operationally:**  
1) **Close the gap:** Treat the bottom bars (below **{avg:.1f}%**) as priority candidates for reliability work.  
2) **Correlate with downtime cost:** Where available, pair low uptime with cost/minutes to size the remediation ROI.  
3) **Track compression:** Re-plot monthly; success is a tighter spread and uplift of the tail (worst performers).  
4) **Align accountability:** Assign owners to each low-uptime service with dated action plans.

**Why this matters:** Higher uptime directly lowers disruption. Focusing on the worst-performing services first maximizes business impact within the shortest time window."""
            )

            # ---------- CIO tables (3–5 rows each) ----------
            def _fmt_rm(x): 
                try: return f"RM {float(x):,.0f}"
                except: return "RM 0"

            cio_3a = {
                "cost": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Remediate **{worst['service_name']}** first | **Phase 1:** Perform a focused root-cause review on the lowest-uptime service so that you clearly understand the main technical, process and dependency issues before you allocate any budget.<br><br>**Phase 2:** Apply quick wins such as configuration corrections, patching and basic restart automation so that you can stabilize the service without large capital investment.<br><br>**Phase 3:** Validate the impact with at least 30 days of tracked uptime and document the before and after view so stakeholders can see the improvement. | - Reduces the largest chunk of avoidable disruption cost at the earliest stage and channels spending into the most problematic service first.<br><br>- Helps operations teams focus on high impact fixes instead of spreading effort thinly across many services with minor issues.<br><br>- Creates early visible wins that can be used to justify further reliability investments to business and finance stakeholders.<br><br> | **Upper-bound pool:** If this service causes **{_fmt_rm(worst_cost_val)}** (data) and **{int(worst_min_val):,}** minutes, that is the immediate cap on recoverable loss. | Bar shows **lowest uptime** at **{worst['uptime_percentage']:.2f}%**; linked minutes/cost (if present) quantify impact. |
| Top-N tail compression (below {avg:.1f}%) | **Phase 1:** List all services whose uptime sits below the current mean and make this list visible to owners and management so that the problem set is transparent.<br><br>**Phase 2:** Assign accountable owners to each low-uptime service and agree on two or three practical reliability actions that can be completed in the near term.<br><br>**Phase 3:** Graduate a service from the tail list only when it maintains uptime at or above the mean for at least two consecutive months and record this in a simple dashboard. | - Concentrates effort on the services that drag down overall reliability instead of treating every service as equal priority.<br><br>- Allows leaders to track a shrinking tail of underperforming services which is easy to explain in management reviews.<br><br>- Builds a culture of ownership where each service owner understands their target and can see when they have moved out of the risk zone.<br><br> | **Pool:** Sum of current period cost/minutes for sub-mean services (from dataset). | Multiple bars sit below average **{avg:.2f}%**. |
| Preventive maintenance calendar | **Phase 1:** Establish a simple monthly or quarterly preventive maintenance plan for the services that show unstable uptime and document the tasks and expected outcomes for each cycle.<br><br>**Phase 2:** Schedule high risk maintenance activities during off-peak periods and coordinate with business users to minimize disruption to critical operations.<br><br>**Phase 3:** After each maintenance window, compare uptime and incident behaviour against the previous period to confirm whether the maintenance is actually reducing instability. | - Lowers the probability of unplanned outages by catching failing components and configuration issues earlier in the lifecycle.<br><br>- Reduces firefighting work by shifting teams from reactive break-fix mode into planned and predictable maintenance work.<br><br>- Improves budgeting for spare parts and maintenance windows because the work is planned and evidence based rather than triggered only by emergencies.<br><br> | **Minutes avoided (upper bound):** Current downtime minutes in these services (dataset). | Variability in low-uptime bars signals maintenance need. |
| Auto-recovery scripts | **Phase 1:** Document the most common manual recovery steps for recurring faults and convert them into simple scripts or runbooks that can be triggered by operations staff.<br><br>**Phase 2:** Add guardrails such as approvals and validation checks so that the scripts do not introduce new risks while still speeding up recovery.<br><br>**Phase 3:** Measure the number of successful auto-recoveries and compare the time taken with traditional manual interventions to demonstrate efficiency gains. | - Reduces the time engineers spend repeating the same manual steps and frees them to focus on deeper problem solving.<br><br>- Shortens restore time for users because scripts execute consistently and immediately when triggered by alerts.<br><br>- Standardizes recovery actions which reduces human error and makes handover between shifts or teams much smoother.<br><br> | **Hours saved:** (Manual restore time × incident count) — using dataset incidents if available. | Low uptime often ties to repeated recoverable faults. |
| Change-freeze near peak periods | **Phase 1:** Identify time windows, such as month-end or business peak hours, where outages are especially painful and correlate them with historical low-uptime periods.<br><br>**Phase 2:** Define and communicate specific rules that restrict high-risk technical changes during these windows while still allowing essential fixes to proceed under control.<br><br>**Phase 3:** Review compliance with the freeze rules, track any exceptions granted and analyse whether breaches correlate with new incidents. | - Prevents avoidable instability during business critical periods and protects revenue and reputation at the moments that matter most.<br><br>- Reduces the number of urgent rollbacks because risky changes are moved to safer windows with more recovery headroom.<br><br>- Gives business stakeholders confidence that technology teams understand their peak cycles and are actively protecting them.<br><br> | **Upper-bound:** Minutes/cost historically seen during those windows (dataset). | Low bars often cluster around certain periods. |
""",
                "performance": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Golden-signals monitoring | **Phase 1:** Introduce monitoring for key health indicators like latency, error rate and resource saturation so that issues are detected before users feel them.<br><br>**Phase 2:** Configure meaningful thresholds and paging rules so that alerts go to the right team in time to act rather than being lost in noise.<br><br>**Phase 3:** Review these signals weekly to fine tune thresholds, remove noise and confirm they are driving faster resolution. | - Helps teams see early warning signs rather than waiting for full service outages reported by users.<br><br>- Supports shorter mean time to detect incidents because the system raises alerts when behaviour deviates from normal baselines.<br><br>- Enables more data driven discussions with vendors and internal teams because there is clear evidence of performance issues and trends.<br><br> | **Minutes saved:** MTTR↓ × incidents (from dataset if present). | Low-uptime services likely suffer slow detection. |
| Runbooks for known faults | **Phase 1:** Capture the steps engineers follow to resolve the most frequent faults in clear, simple runbooks that non-experts can follow.<br><br>**Phase 2:** Where possible, link these runbooks into tools or portals so that engineers can execute them quickly and consistently when an alert fires.<br><br>**Phase 3:** Track how often each runbook is used and adjust the content based on feedback and new learnings from incidents. | - Improves consistency of response because different engineers apply the same proven fix steps for recurring issues.<br><br>- Reduces onboarding time for new team members since they can rely on documented guidance instead of tribal knowledge.<br><br>- Shortens service restoration times because responders do not need to reinvent the process during every incident.<br><br> | **Time saved:** (Avg manual steps time × use count). | Tail bars indicate repeatable issues. |
| Capacity/right-sizing checks | **Phase 1:** Review CPU, memory, storage and network utilisation for low-uptime services to identify clear saturation or chronic under-provisioning.<br><br>**Phase 2:** Adjust capacity by scaling up, optimising configuration or tuning workloads so that the service has headroom during expected peaks.<br><br>**Phase 3:** Re-test performance and monitor whether uptime stabilises after the capacity adjustments have been deployed. | - Reduces outages caused by resource exhaustion and ensures the platform can sustain real business load patterns.<br><br>- Avoids over-spending on infrastructure by targeting upgrades where they are actually needed rather than applying blanket increases.<br><br>- Improves user experience because services remain responsive and stable during periods of high demand.<br><br> | **Upper-bound gain:** Minutes currently attributed to capacity (dataset). | Persistent low uptime can reflect saturation. |
| Ownership KPIs | **Phase 1:** Assign clear uptime and reliability targets to named owners for each critical service and communicate these targets openly.<br><br>**Phase 2:** Publish monthly performance views that show how each owner is tracking against their targets to drive transparency and accountability.<br><br>**Phase 3:** Recognise improvements and adjust targets over time so that reliability continues to trend in the right direction. | - Ensures that every important service has someone explicitly responsible for its health and improvement actions.<br><br>- Supports performance management discussions with objective data rather than subjective views of who is doing well.<br><br>- Encourages continuous improvement because owners can see their progress and benchmark against peers.<br><br> | **KPI gain:** Δuptime (%) per service × exposure. | Spread of bars shows room for owner-level uplift. |
| Release hardening | **Phase 1:** Strengthen the release process by enforcing peer review, testing and rollback plans for changes that affect availability.<br><br>**Phase 2:** Introduce strategies such as canary releases or blue green deployments so that new versions can be tested with limited impact before full rollout.<br><br>**Phase 3:** Pause or roll back changes that cause regression and only proceed once the root causes are fixed and verified. | - Reduces the number of incidents triggered by new releases and stabilizes the change pipeline.<br><br>- Protects business users from large scale outages because new versions are exposed gradually and safely.<br><br>- Increases confidence in the change process which helps both technology and business teams to support more frequent but safer releases.<br><br> | **Avoided minutes:** Regression windows historically seen. | Dips often correlate with releases. |
""",
                "satisfaction": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish uptime targets & status | **Phase 1:** Define clear uptime and availability targets for each key service and get agreement from both business and IT stakeholders.<br><br>**Phase 2:** Share simple status views that show how current uptime compares to those targets so users understand performance at a glance.<br><br>**Phase 3:** Issue short monthly progress updates that highlight improvements and explain what is being done where targets are missed. | - Builds trust because customers can see that service performance is being monitored and reported transparently.<br><br>- Reduces confusion and rumours about system reliability because there is an official single source of truth on uptime.<br><br>- Helps manage expectations by making it clear which services are still being improved and which are already stable.<br><br> | **Complaints avoided:** reduction × handling cost (track in dataset if captured). | Clear tail in uptime suggests need for comms. |
| VIP routing for low-uptime services | **Phase 1:** Identify which user groups or business units are most affected by low-uptime services and classify them as priority segments.<br><br>**Phase 2:** Provide these users with a dedicated support path or SME queue so their issues are triaged and resolved faster when outages occur.<br><br>**Phase 3:** Review performance and feedback from these groups regularly to understand whether the special handling is reducing their pain. | - Ensures that the users with the highest business impact receive faster assistance when services fail.<br><br>- Can protect key revenue streams and executive users from prolonged disruption during instability periods.<br><br>- Signals to important customers that their needs are recognised and actively managed which supports relationship retention.<br><br> | **Upper-bound benefit:** Minutes avoided for VIP cases (dataset). | Worst bar maps to highest user pain. |
| Post-incident feedback | **Phase 1:** Send short surveys or collect structured feedback after major incidents to capture user impact and perception of the response.<br><br>**Phase 2:** Convert common themes from this feedback into concrete improvement items in the backlog and assign owners and timelines.<br><br>**Phase 3:** Communicate back to users which of their suggestions have been implemented and what changes they should expect. | - Makes users feel heard and respected which can soften the negative experience of downtime.<br><br>- Directs improvement work toward areas that users actually care about instead of internal assumptions.<br><br>- Provides qualitative input that can be combined with technical metrics to guide service design decisions.<br><br> | **Retention value:** Track uplifts tied to fixes. | Tail bars predict dissatisfaction risk. |
| Expectation management during work | **Phase 1:** Before planned work or high risk changes, inform users clearly about what will happen, when it will happen and what the expected impact is.<br><br>**Phase 2:** Provide timely updates during the work, especially if timelines change or unexpected issues occur so that users are not left guessing.<br><br>**Phase 3:** After completion, share a simple summary of what was done and what benefits or improvements are expected. | - Reduces the stress and frustration users feel when systems appear to fail without explanation.<br><br>- Lowers the number of escalation calls and complaints because stakeholders know what to expect and when services will return.<br><br>- Demonstrates professionalism and control which improves the perceived quality of IT services even when downtime is unavoidable.<br><br> | **Escalations avoided:** count × handling cost. | Variability highlights where messaging matters most. |
| Recognition of improvements | **Phase 1:** Highlight success stories where uptime has improved significantly and share them with both technical teams and business stakeholders.<br><br>**Phase 2:** Acknowledge and thank the teams and individuals who contributed to these improvements so they see that their efforts are valued.<br><br>**Phase 3:** Use these stories to set new but realistic targets and motivate other service teams to replicate the same practices. | - Reinforces positive behaviour and encourages teams to continue investing effort in reliability improvements.<br><br>- Helps business users see that issues are being addressed over time rather than remaining static.<br><br>- Supports a culture of continuous improvement by celebrating progress rather than focusing only on failures.<br><br> | **Qualitative:** CSAT trend post-uplift. | Bar compression evidences progress. |
"""
            }

            render_cio_tables("CIO – Availability Statistics", cio_3a)
        else:
            st.warning(f"⚠️ Missing columns: {required - set(df.columns)}")

    # ============================================================
    # 3b. Downtime Incidents During Reporting Period
    # ============================================================
    with st.expander("📌 Downtime Incidents During the Reporting Period"):
        required = {"service_name", "downtime_minutes", "incident_count"}
        if required.issubset(df.columns):
            df_plot = df.copy()
            downtime = (
                df_plot.groupby("service_name", as_index=False)
                .agg({"downtime_minutes": "sum", "incident_count": "sum"})
            )
            downtime["avg_downtime_per_incident"] = downtime["downtime_minutes"] / downtime["incident_count"].replace(0, np.nan)
            downtime["avg_downtime_per_incident"].replace([np.inf, np.nan], 0, inplace=True)

            fig = px.bar(
                downtime.sort_values("downtime_minutes", ascending=False).head(10),
                x="service_name",
                y="downtime_minutes",
                text="downtime_minutes",
                title="Top 10 Services by Total Downtime (Minutes)",
                labels={"service_name": "Service", "downtime_minutes": "Downtime (Minutes)"}
            )
            fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            worst = downtime.sort_values("downtime_minutes", ascending=False).iloc[0]
            avg_downtime = downtime["downtime_minutes"].mean()
            avg_per_incident = downtime["avg_downtime_per_incident"].mean()

            st.markdown("### 🧭 Analysis — Downtime Trends")
            st.write(
f"""**What this graph is:** A ranked bar chart showing **total downtime minutes** by **service**, focusing on the Top 10 contributors.  
- **X-axis:** Service name.  
- **Y-axis:** Total downtime (minutes) over the reporting period.

**What it shows in your data:** The **most affected service** is **{worst['service_name']}** with **{worst['downtime_minutes']:.0f} minutes** of downtime. Across services, the **average downtime** is **{avg_downtime:.0f} minutes**, and the **average duration per incident** is **{avg_per_incident:.1f} minutes**. This concentration indicates that a small set of services drives a large share of unavailability.

**How to read it operationally:**  
1) **Stabilize the top bars:** Target the worst services first with redundancy and hardening.  
2) **Shorten restore time:** Use runbooks and automation to cut average minutes per incident.  
3) **Prevent recurrence:** Correlate incidents by root cause and eliminate repeating faults.  
4) **Verify impact:** Re-plot monthly; material progress = shrinking top bars and lower per-incident minutes.

**Why this matters:** Every minute of downtime is lost productivity and missed SLA. Tackling the largest sources first delivers the fastest, most visible business benefit."""
            )

            # ---------- CIO tables (3–5 rows each) ----------
            total_minutes_top10 = int(downtime.sort_values("downtime_minutes", ascending=False).head(10)["downtime_minutes"].sum())
            total_minutes_all   = int(downtime["downtime_minutes"].sum())
            total_incidents_all = int(downtime["incident_count"].sum())
            worst_minutes       = int(worst["downtime_minutes"])
            worst_incidents     = int(worst["incident_count"])

            cio_3b = {
                "cost": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Top-10 downtime burn-down | **Phase 1:** Build a clear remediation worklist for the ten services with the highest downtime and socialise it with stakeholders so priorities are aligned.<br><br>**Phase 2:** Assign accountable owners, define corrective actions and set realistic due dates for each of these services to reduce their downtime minutes.<br><br>**Phase 3:** Review the status of this Top-10 list every week until the bars come down and services either leave the list or show a sustained improvement trend. | - Targets investment and engineering time at the services that are responsible for the majority of downtime minutes and therefore the largest financial impact.<br><br>- Provides a simple narrative for leadership by showing how the Top-10 list shrinks over time as actions are delivered.<br><br>- Enables transparent tracking of progress and avoids dilution of effort across too many low impact tasks.<br><br> | **Upper-bound pool:** Minutes (Top-10) = **{total_minutes_top10:,}** (dataset). | Bars show heavy concentration in Top-10 minutes. |
| Runbook + auto-remediation | **Phase 1:** Identify repeating incident patterns and document the standard recovery steps in clear, step-by-step runbooks for operations teams.<br><br>**Phase 2:** Where practical, wrap those steps in simple tools or automation so they can be triggered quickly or even automatically when specific alerts fire.<br><br>**Phase 3:** Measure how often these automated or guided recoveries are used and compare the time to restore against historical manual recoveries. | - Reduces the average downtime per incident because the response is faster and more consistent across shifts and teams.<br><br>- Lowers reliance on a few expert engineers since documented steps allow more people to handle known issues confidently.<br><br>- Supports standardisation and continuous improvement by allowing teams to refine runbooks based on real usage and outcomes.<br><br> | **Recoverable minutes:** Avg per incident (**{avg_per_incident:.1f}**) × incidents (dataset). | Average per-incident minutes = **{avg_per_incident:.1f}**. |
| Scheduled preventive maintenance | **Phase 1:** Use downtime and incident history to select which services should have scheduled preventive checks and define the specific tasks to be carried out.<br><br>**Phase 2:** Execute these checks on a recurring basis and replace weak or failing components before they cause a production outage.<br><br>**Phase 3:** Compare downtime trends before and after the preventive maintenance program to confirm it is actually reducing emergency work. | - Decreases the number of unexpected failures that pull engineers into high stress emergency situations.<br><br>- Allows better planning of resources and spare parts because maintenance is structured instead of reactive.<br><br>- Helps maintain consistent service quality which in turn supports stronger SLA performance and customer trust.<br><br> | **Upper-bound:** Current minutes in those services (dataset). | Worst services show repeated high minutes. |
| Correlate incidents automatically | **Phase 1:** Implement tooling or scripts that group incidents by common attributes such as error codes, components or time windows to reveal underlying patterns.<br><br>**Phase 2:** Use these grouped clusters to identify the most frequent root causes and define structural fixes for those high volume issues.<br><br>**Phase 3:** After the fixes, monitor whether incidents in each cluster reduce and adjust correlation rules where needed. | - Reduces analyst time spent manually sorting and investigating similar incidents one by one.<br><br>- Enables more strategic fixes by highlighting problems that generate many incidents rather than rare edge cases.<br><br>- Improves communication with stakeholders because problem themes can be described clearly and backed by data.<br><br> | **Analyst hours saved:** (Manual triage time × incident count). | Many incidents (**{total_incidents_all:,}**) indicate triage load. |
| Off-peak change discipline | **Phase 1:** Analyse historical downtime to understand when services are most sensitive to changes and identify periods that should be considered high risk for deployments.<br><br>**Phase 2:** Implement governance that pushes non-urgent or high risk changes into off-peak windows where user impact is lower and recovery options are better.<br><br>**Phase 3:** Regularly review incidents linked to change windows and adjust the rules if downtime is still concentrated in risky periods. | - Reduces outages caused by poorly timed releases that collide with peak usage or critical business activities.<br><br>- Gives support teams more capacity to manage any issues that arise because changes happen at times when demand is lower.<br><br>- Provides business stakeholders with assurance that technology teams are aligning deployment timings with operational realities.<br><br> | **Upper-bound:** Peak-window minutes (dataset) avoided. | Spikes suggest timing sensitivity. |
""",
                "performance": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| MTTR reduction program | **Phase 1:** Measure current end-to-end mean time to restore for key services so everyone understands the baseline performance clearly.<br><br>**Phase 2:** Map out the main handoffs and bottlenecks in the incident process and remove unnecessary steps, delays or approvals that slow down recovery.<br><br>**Phase 3:** Put in place service level objectives for response and resolution and review them regularly to ensure they are being met and improved. | - Directly reduces the length of each outage which means fewer lost minutes for customers and internal users.<br><br>- Improves operational discipline by forcing teams to look critically at their incident handling workflows and streamline them.<br><br>- Creates a set of measurable targets that can be used to track whether process and tooling changes are paying off over time.<br><br> | **Minutes saved:** (MTTR baseline − MTTR new) × incidents. | High average per-incident minutes show MTTR headroom. |
| Resilience for **{worst['service_name']}** | **Phase 1:** Carry out a detailed technical assessment of the most affected service to understand single points of failure and key dependencies.<br><br>**Phase 2:** Design and implement resilience measures such as redundancy, failover paths or improved isolation from unstable components.<br><br>**Phase 3:** Test this resilience regularly, for example with controlled failover exercises, and monitor whether downtime minutes reduce over subsequent periods. | - Focuses engineering investment where it will have the biggest impact on reducing downtime and reputational risk.<br><br>- Lowers the operational stress associated with this high risk service because teams know there are fallback options.<br><br>- Provides a strong case study that can be replicated for other services using the same resilience patterns and designs.<br><br> | **Upper-bound:** Minutes at {worst['service_name']} = **{worst_minutes:,}**. | {worst['service_name']} tops the downtime chart. |
| Alert quality improvement | **Phase 1:** Review existing alerts and remove duplicates and low value notifications that distract engineers from real issues.<br><br>**Phase 2:** Tune thresholds and add new alerts where gaps are identified so that important events are flagged early and clearly.<br><br>**Phase 3:** Track the ratio of actionable alerts to noise and refine the configuration until the majority of alerts trigger useful action. | - Helps engineers focus their attention on real degradations instead of spending time clearing irrelevant alarms.<br><br>- Speeds up incident response because the first signals received are more likely to be meaningful indicators of real problems.<br><br>- Improves morale in operations teams as they deal with fewer false alarms and can trust the monitoring environment more.<br><br> | **Incidents influenced:** **{total_incidents_all:,}** (dataset). | Repeated incidents imply noisy/late alerting. |
| Hotspot capacity fixes | **Phase 1:** Use performance and resource data to identify specific services or components that consistently run hot during incidents or peaks.<br><br>**Phase 2:** Address these hotspots through targeted changes such as load balancing, scaling, code optimisation or infrastructure upgrades.<br><br>**Phase 3:** Validate that downtime minutes associated with those hotspots have fallen and ensure that new hotspots have not emerged elsewhere. | - Removes recurring structural weaknesses that repeatedly cause slowdowns or outages when demand rises.<br><br>- Allows more predictable performance under load which supports growth in user numbers or transaction volumes.<br><br>- Makes capacity planning more precise because real data points are used to justify each fix and investment.<br><br> | **Upper-bound:** Minutes currently tied to hotspots (dataset). | High minutes often correlate with saturation. |
| Ownership huddles | **Phase 1:** Set up short, focused weekly or bi-weekly huddles where owners of the most problematic services review downtime trends and incidents together.<br><br>**Phase 2:** Capture specific actions, deadlines and responsible parties during each huddle so that follow up is structured and traceable.<br><br>**Phase 3:** Retire services from the huddle list once they have stayed below a defined downtime threshold and bring new problem services into the forum. | - Keeps sustained attention on the small number of services that are hurting performance the most.<br><br>- Encourages collaboration and shared problem solving across teams that may otherwise work in silos.<br><br>- Provides a lightweight governance mechanism that aligns technical actions with management expectations without heavy bureaucracy.<br><br> | **Governance cost vs saved minutes:** track in dataset. | Sustained high bars require governance pressure. |
""",
                "satisfaction": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Proactive incident updates | **Phase 1:** When an outage occurs, quickly publish a concise status message that acknowledges the issue and indicates that the team is working on it.<br><br>**Phase 2:** Provide regular updates with clear estimates and any temporary workarounds so users can plan their activities around the disruption.<br><br>**Phase 3:** After resolution, share a short summary of what happened, what was fixed and what will be done to avoid repeat issues. | - Reduces user anxiety and frustration because they no longer feel left in the dark when services go down.<br><br>- Cuts down on repetitive calls and tickets asking for the same status information which saves support time.<br><br>- Strengthens the perception that IT is in control and managing the situation professionally even during outages.<br><br> | **Complaints avoided:** count × handling cost (track). | Large minutes directly impact users. |
| Priority lanes during peaks | **Phase 1:** During major incidents or peak periods, define a clear process for routing high impact users or services through a faster support path.<br><br>**Phase 2:** Make sure skilled subject matter experts are assigned to these priority lanes so complex issues can be diagnosed and resolved quickly.<br><br>**Phase 3:** Evaluate the performance of the priority lane after major events and refine the criteria used to identify which cases qualify. | - Ensures that critical business functions receive rapid support when they are most at risk from downtime.<br><br>- Can mitigate financial and reputational damage by restoring key capabilities earlier than lower impact services.<br><br>- Sends a strong message to strategic customers and executives that their issues are taken seriously and handled with urgency.<br><br> | **Upper-bound:** Minutes avoided for priority cases (dataset). | Worst services hit key users hardest. |
| Publish downtime scorecards | **Phase 1:** Create simple visual scorecards that show downtime minutes and incident counts by service for each reporting period.<br><br>**Phase 2:** Share these scorecards with business stakeholders and explain both the key issues and the improvement actions being taken.<br><br>**Phase 3:** Track how these metrics evolve over time and highlight services that have moved from red to amber or green status. | - Builds transparency and helps users understand that downtime is being measured and actively managed.<br><br>- Supports more constructive conversations with customers because both sides are looking at the same set of facts.<br><br>- Demonstrates progress visibly which can improve satisfaction even before all problems are fully resolved.<br><br> | **Retention value:** correlate CSAT uplift to minutes reduced. | Bars provide clear before/after evidence. |
| Feedback → fixes loop | **Phase 1:** After outages or sustained instability, collect user feedback on what was most painful and what would have helped them cope better.<br><br>**Phase 2:** Convert these insights into specific backlog items and let users know which of their suggestions have been prioritised.<br><br>**Phase 3:** Once changes are delivered, follow up to confirm whether the new experience matches expectations and adjust if needed. | - Aligns technical improvements directly with user expectations rather than internal assumptions about what matters most.<br><br>- Helps reduce recurring complaints because the underlying user pain points are systematically addressed.<br><br>- Keeps users engaged in the improvement journey and can turn dissatisfied customers into partners in the change process.<br><br> | **Qualitative + trend:** complaint rate ↓ post-fix. | Concentration suggests repeated pain. |
| Service-specific FAQ/workarounds | **Phase 1:** Document short, practical FAQs and workaround steps for the most common issues affecting each major service.<br><br>**Phase 2:** Make these guides easy to find in portals or chatbots so users can access them quickly during incidents.<br><br>**Phase 3:** Update and expand the content based on recurring questions and actual usage so that it stays relevant and helpful. | - Empowers users to solve minor issues themselves without always waiting for the service desk.<br><br>- Reduces ticket volumes for simple problems and allows support staff to focus on higher value activities.<br><br>- Improves the perceived responsiveness of IT because users can get answers and workarounds immediately when issues arise.<br><br> | **Deflected contacts:** count × handling cost. | Repetition in incidents invites self-service. |
"""
            }
            render_cio_tables("CIO – Downtime Incident Management", cio_3b)
        else:
            st.warning(f"⚠️ Missing columns: {required - set(df.columns)}")

    # ============================================================
    # 3c. SLA Compliance Related to Availability
    # ============================================================
    with st.expander("📌 SLA Compliance Related to Availability"):
        required = {"service_name", "sla_met", "sla_target", "uptime_percentage"}
        if required.issubset(df.columns):
            df_sla = df.copy()
            df_sla["sla_met_rate"] = df_sla["sla_met"].astype(str).str.lower().isin(["yes", "true", "1"]).astype(int)
            summary = (
                df_sla.groupby("service_name", as_index=False)
                .agg({"sla_target": "mean", "sla_met_rate": "mean", "uptime_percentage": "mean"})
            )
            summary["sla_met_rate"] *= 100

            fig = px.scatter(
                summary,
                x="uptime_percentage",
                y="sla_met_rate",
                color="service_name",
                title="SLA Compliance vs Uptime (%)",
                labels={"uptime_percentage": "Uptime (%)", "sla_met_rate": "SLA Met (%)"}
            )
            st.plotly_chart(fig, use_container_width=True)

            avg_sla = summary["sla_met_rate"].mean()
            top = summary.loc[summary["sla_met_rate"].idxmax()]
            low = summary.loc[summary["sla_met_rate"].idxmin()]

            st.markdown("### 🧩 Analysis — SLA Compliance")
            st.write(
f"""**What this graph is:** A scatter plot comparing **SLA met (%)** against **uptime (%)** for each service.  
- **X-axis:** Uptime percentage.  
- **Y-axis:** SLA met percentage.

**What it shows in your data:** The **highest SLA compliance** is **{top['service_name']}** at **{top['sla_met_rate']:.1f}%**, while the **lowest** is **{low['service_name']}** at **{low['sla_met_rate']:.1f}%**. The **average SLA met** across services is **{avg_sla:.1f}%**. Points trend upward, indicating that higher uptime typically aligns with higher SLA compliance.

**How to read it operationally:**  
1) **Bottom-left quadrant:** Low uptime and low SLA—urgent reliability work needed.  
2) **Right-low quadrant:** High uptime but low SLA—review target definitions/measurement.  
3) **Left-high quadrant:** Low uptime but decent SLA—investigate exceptions/credits.  
4) **Track shifts:** Aim to move all points toward the top-right (high uptime, high SLA).

**Why this matters:** SLAs are contractual and reputational. Improving uptime where SLA misses cluster reduces penalties and boosts customer confidence."""
            )

            # ---------- CIO tables (3–5 rows each) ----------
            cio_3c = {
                "cost": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Calibrate SLA targets to observed capability | **Phase 1:** Compare current SLA target values against actual performance data so that you understand where targets are unrealistic or too relaxed.<br><br>**Phase 2:** Decide whether to improve technical capability or renegotiate SLA numbers so that the agreed targets match what the platform can reliably deliver.<br><br>**Phase 3:** Publish the updated targets and ensure they are embedded into contracts, dashboards and reporting processes. | - Reduces the risk of paying penalties simply because targets were misaligned with real world performance rather than genuine neglect.<br><br>- Prevents over-promising to customers and sets a realistic baseline that both business and IT can commit to achieving.<br><br>- Improves planning because capacity and improvement investments can be calibrated to the correct service levels instead of arbitrary figures.<br><br> | **Upper-bound savings:** Current breach-related costs (trackable in dataset if captured). | Low-SLA points vs uptime show misalignment risk. |
| Real-time SLA dashboards | **Phase 1:** Build dashboards or reports that display live or near real-time SLA performance by service so that deviations are visible as they occur.<br><br>**Phase 2:** Configure alerts when metrics approach thresholds so teams can intervene before a formal breach happens.<br><br>**Phase 3:** Hold weekly reviews of SLA dashboards to check trends and fine tune alerting logic and escalation paths. | - Enables teams to act before an SLA is breached instead of discovering issues only in monthly reports.<br><br>- Increases operational awareness and makes SLA performance part of day to day decision making rather than an afterthought.<br><br>- Strengthens conversations with customers because you can reference real time evidence when explaining service performance.<br><br> | **Breach minutes avoided:** minutes near threshold historically (dataset). | Scatter shows spread below average **{avg_sla:.1f}%**. |
| Contracted freeze windows | **Phase 1:** Identify periods where SLA risk is highest and agree with customers which times should be protected by formal change freeze rules.<br><br>**Phase 2:** Document these windows in contracts and operating procedures so everyone understands when changes are restricted and why.<br><br>**Phase 3:** Track adherence to the freeze rules and investigate any SLA breaches that occur during exceptions to understand root causes. | - Reduces the likelihood of SLA breaches that are triggered by avoidable changes during sensitive periods.<br><br>- Provides clear boundaries to both internal teams and customers about when changes can safely occur.<br><br>- Supports fair commercial discussions because the risk of change during these windows is shared and explicitly managed.<br><br> | **Upper-bound:** Breach incidents during change windows. | Low-SLA services often tied to change cycles. |
| Evidence-based credits | **Phase 1:** Review how downtime and SLA breaches are measured across systems and ensure there is a single source of truth for calculations.<br><br>**Phase 2:** Standardise the rules for counting breaches and applying service credits so that the process is consistent and defensible.<br><br>**Phase 3:** Automate the reporting of credits and ensure that data is available to challenge incorrect claims or over-crediting. | - Avoids unnecessary financial leakage from credits granted based on inconsistent or incorrect data.<br><br>- Builds trust with customers by demonstrating that credits are calculated fairly and based on transparent evidence.<br><br>- Supports audits and contract renewals because historical credit decisions can be traced back to reliable data and rules.<br><br> | **Avoided credits:** historical over-counts (dataset). | Right-low quadrant points flag measurement issues. |
| Penalty risk register | **Phase 1:** Identify services whose SLA performance is below the average of **{avg_sla:.1f}%** and list them in a simple risk register with clear owners.<br><br>**Phase 2:** For each of these services, define mitigation actions and due dates that directly target the drivers of SLA misses.<br><br>**Phase 3:** Review the register frequently and remove services only when they sustain SLA performance at or above agreed levels. | - Brings focus to the parts of the portfolio that have the highest likelihood of generating penalties or customer dissatisfaction.<br><br>- Provides a structured way for leadership to see where SLA risk is concentrated and what is being done about it.<br><br>- Aligns technical work with contractual exposure so that time and budget are used where they reduce risk the most.<br><br> | **Upper-bound pool:** Sum of breach minutes for those services. | Clusters below average indicate risk concentration. |
""",
                "performance": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Uptime uplift on low-SLA services | **Phase 1:** Identify services with low SLA met percentages and map the main technical and operational reasons for their underperformance.<br><br>**Phase 2:** Implement targeted reliability improvements such as fixing recurring faults, enhancing monitoring or improving incident handling for these services.<br><br>**Phase 3:** Track changes in both uptime and SLA metrics over time to confirm that the interventions are moving points toward the top right of the scatter. | - Directly improves SLA scores by addressing the root causes of instability for the worst performing services.<br><br>- Provides tangible proof to customers that problem services are being worked on with clear follow through.<br><br>- Lifts overall portfolio performance because the weakest services are brought closer to the standards of the better performing ones.<br><br> | **Upper-bound:** Downtime minutes currently on those services. | Low SLA aligns with lower uptime in scatter. |
| Threshold-based paging | **Phase 1:** Define SLA buffer levels that indicate when a service is close to breaching its commitments based on current uptime and incident behaviour.<br><br>**Phase 2:** Configure paging and escalation rules that trigger when the buffer is small so that responders can take immediate action.<br><br>**Phase 3:** Monitor how many breaches are prevented due to these early warnings and adjust thresholds to balance noise and responsiveness. | - Reduces the number of last minute SLA breaches by alerting teams while there is still time to recover service quality.<br><br>- Creates a more proactive operating model where teams do not wait for formal breach reports before acting.<br><br>- Gives managers clearer visibility into which services are repeatedly operating close to their SLA limits and need deeper fixes.<br><br> | **Minutes saved:** near-breach minutes rescued (dataset). | Services near line benefit from early alerts. |
| RCA on systematic misses | **Phase 1:** Group SLA breaches by cause categories such as capacity, change, incident handling or external dependencies to identify systematic patterns.<br><br>**Phase 2:** For the top cause categories, define and implement structural fixes rather than relying only on quick workarounds.<br><br>**Phase 3:** After implementation, review whether the volume of breaches in each category has fallen and refine the categories if new patterns emerge. | - Moves the organisation away from treating each SLA miss as an isolated event and toward addressing the systemic drivers of failure.<br><br>- Improves long term performance by eliminating recurring issues that generate multiple breaches over time.<br><br>- Provides a clear story for management and auditors about how SLA risk is being reduced at a root cause level.<br><br> | **Breach count reduced:** per cause group (dataset). | Scatter dispersion shows systemic issues. |
| Test data/clock alignment | **Phase 1:** Validate that monitoring tools, ticketing systems and reporting platforms are using consistent timestamps and time zones for SLA calculations.<br><br>**Phase 2:** Correct any misalignments in data sources and adjust historical calculations where they have been distorted by time issues.<br><br>**Phase 3:** Put controls in place to ensure new systems or integrations use the same standards so that SLA reporting stays accurate. | - Avoids disputes and confusion caused by mismatched data when discussing SLA performance with customers.<br><br>- Reduces the risk of reporting false breaches that trigger unnecessary credits or reputation damage.<br><br>- Ensures that internal analytics and decisions are based on reliable, consistent timing information across all tools.<br><br> | **Avoided false misses:** count (dataset). | Misaligned targets vs uptime suggest calc issues. |
| Owner SLA drills | **Phase 1:** Schedule regular SLA risk review sessions with service owners to discuss current performance and potential upcoming challenges.<br><br>**Phase 2:** Agree on specific pre-emptive actions to mitigate identified risks, such as capacity upgrades or incident rehearsals, and document them clearly.<br><br>**Phase 3:** Track the completion and impact of these actions and update the drill process based on what works best. | - Keeps SLA health on the agenda of each service owner rather than relying only on central reporting teams.<br><br>- Encourages proactive behaviour as owners think ahead about risks instead of reacting only after breaches occur.<br><br>- Creates a feedback loop between real world performance and planning so that drills evolve with the service landscape.<br><br> | **Breach minutes avoided:** pre-emptive interventions. | Points rise as owners act. |
""",
                "satisfaction": f"""
| Recommendation | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish SLA scorecards | **Phase 1:** Generate regular scorecards that show SLA met percentages for each service in a clear and simple format for customers and internal stakeholders.<br><br>**Phase 2:** Accompany the numbers with brief explanations of major misses and the remediation plans in place to address them.<br><br>**Phase 3:** Track improvements over time and highlight when services move from poor performance into acceptable or excellent ranges. | - Increases transparency and reduces speculation because customers can see factual SLA performance data for themselves.<br><br>- Demonstrates accountability by showing not only where performance is strong but also where it is weak and what is being done about it.<br><br>- Helps to rebuild trust after issues because stakeholders can see a consistent trend of improvement backed by data.<br><br> | **Escalations avoided:** count × handling cost. | Scatter enables transparent reporting. |
| Customer-tiered comms | **Phase 1:** Define different communication approaches for various SLA tiers so that higher tier customers receive more detailed and frequent updates.<br><br>**Phase 2:** Implement automated notification workflows that trigger appropriate messages when SLA risk increases for each tier.<br><br>**Phase 3:** Periodically review customer feedback to confirm that the communications are meeting expectations and adjust tone and frequency as needed. | - Ensures that communication effort is aligned with the commercial importance of each customer segment.<br><br>- Helps protect high value relationships by giving premium customers a level of attention that matches their investment.<br><br>- Reduces unnecessary noise for lower tier customers by avoiding over-communication that they may not need or want.<br><br> | **Churn risk reduced:** proxied via CSAT trend. | Low-SLA services need stronger comms. |
| Priority handling for critical users | **Phase 1:** Work with business stakeholders to identify users or teams whose work is most sensitive to SLA performance on specific services.<br><br>**Phase 2:** Define and implement priority handling rules so that incidents affecting these users are triaged and resolved more quickly.<br><br>**Phase 3:** Monitor whether these rules are improving outcomes for critical users and refine the criteria or process where necessary. | - Provides additional protection for business processes that cannot tolerate extended downtime without serious impact.<br><br>- Demonstrates to key stakeholders that their needs have been explicitly considered in incident handling design.<br><br>- Can reduce churn or dissatisfaction among strategic accounts by improving their experience even when global issues occur.<br><br> | **Upper-bound benefit:** minutes avoided for VIP cases. | Low SLA points map to user pain. |
| Feedback-to-fix pipeline | **Phase 1:** Collect structured feedback from customers after SLA misses to understand how the outage affected them and what they most want improved.<br><br>**Phase 2:** Convert the most frequent and impactful feedback themes into backlog items and track them through to delivery.<br><br>**Phase 3:** Communicate back to customers when their feedback has led to concrete changes and show the resulting SLA improvements. | - Makes customers feel involved in shaping service improvements which can reduce frustration after negative incidents.<br><br>- Ensures that engineering effort is targeted at the aspects of service quality that customers actually care about most.<br><br>- Provides powerful stories for account managers who can show how client feedback is turned into action and better outcomes.<br><br> | **CSAT uplift:** measured post-fix. | Dispersion signals where to listen closely. |
| Celebrate SLA recoveries | **Phase 1:** When services recover from a period of poor SLA performance, prepare concise updates that explain the improvements and the actions taken.<br><br>**Phase 2:** Share these updates with both internal teams and customers and recognise the individuals and groups who contributed to the turnaround.<br><br>**Phase 3:** Use these examples as reference models when planning improvement journeys for other underperforming services. | - Reinforces positive behaviours by publicly acknowledging effective remediation work and the teams behind it.<br><br>- Helps customers see that SLA problems are not permanent and that the organisation is capable of delivering meaningful recovery.<br><br>- Builds a culture that values learning and improvement instead of only focusing on blame when things go wrong.<br><br> | **Qualitative:** CSAT/retention trend. | Upward movement in scatter evidences wins. |
"""
            }
            render_cio_tables("CIO – SLA Compliance Related to Availability", cio_3c)
        else:
            st.warning(f"⚠️ Missing columns: {required - set(df.columns)}")
