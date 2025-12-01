import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .incident_overview import render_cio_tables

def incident_classification(df_filtered):
    # ------------------ 2a Categories ------------------
    with st.expander("📌 Categories of Incidents (Service Category)"):
        if "service_category" in df_filtered.columns:
            cat = df_filtered["service_category"].fillna("Unknown")
            counts = cat.value_counts().reset_index()
            counts.columns = ["service_category", "count"]

            # --- Graph: Top Categories (bar)
            topN = counts.head(20).copy()
            fig = px.bar(
                topN,
                x="service_category", y="count",
                title="Top Categories (count)",
                text="count"
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # --- Analysis for Categories bar
            st.markdown("### Analysis – Incident Categories (Top 20)")
            if not counts.empty:
                total_inc = int(counts["count"].sum())
                top = counts.iloc[0]
                top_name = str(top["service_category"])
                top_cnt = int(top["count"])
                top_share = top_cnt / total_inc if total_inc else 0.0
                top3_share = counts["count"].iloc[:3].sum() / total_inc if total_inc else 0.0
                tail_share = counts["count"].iloc[10:].sum() / total_inc if (total_inc and len(counts) > 10) else 0.0

                st.write(f"""
**What this graph is:** A bar chart showing **incident volume by service category** (Top 20).  
- **X-axis:** Service categories (sorted by volume).  
- **Y-axis:** Number of incidents per category.

**What it shows in your data:**  
Largest category: **{top_name}** with **{top_cnt}** incidents (**{top_share:.1%}** of **{total_inc}** total).  
Top-3 categories together account for **{top3_share:.1%}** of all incidents.  
The **long tail beyond Top 10** represents **{tail_share:.0%}** of volume.

Overall, tall bars reveal **dominant demand drivers** to standardize/automate first; short bars form the **long tail** of sporadic requests.

**How to read it operationally:**  
1) **Peaks:** Build playbooks/automation for the top categories to remove repetitive effort fast.  
2) **Plateaus:** Keep routing and ownership clean so mid-volume categories don’t leak into escalations.  
3) **Downswings:** When a category drops, capture the change (fix/KB/process) and replicate elsewhere.  
4) **Mix:** Pair categories with **priority/age/SLA** so critical work isn’t drowned by high volume.

**Why this matters:** Concentration in a few categories enables **fast cost, performance, and CSAT gains**—fix the vital few to reduce rework and breaches.
""")

            # --- CIO table (uses real values above)
            if not counts.empty:
                top5_vol = int(counts["count"].iloc[:5].sum())
                cio = {
                    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Automate repetitive high-volume categories | **Phase 1 – Identify:** Mine the top drivers by volume, such as **{top_name}**, and confirm with stakeholders that these patterns are stable and suitable for automation. <br><br>**Phase 2 – Build:** Design scripted or self-service flows that mirror how agents resolve these incidents today while keeping each step simple and intuitive for end users. <br><br>**Phase 3 – Govern:** Monitor deflection percentage, review exceptions where automation fails, and ensure agents can quickly take over when automated flows cannot complete a request. | - This reduces manual effort because routine tickets in **{top_name}** are handled automatically instead of requiring agent time.<br><br>- It reduces overtime during spike days because fewer tickets need manual work when the incident volume is high.<br><br>- It lowers cost per ticket over time as more incidents are deflected and the average handling time per ticket decreases.<br><br>- It allows experienced staff to focus on complex and high-impact incidents instead of repetitive low-value work.<br><br> | **Savings** = tickets_automated × avg_handling_hours × rate. Size automation using **{top_cnt}** tickets in **{top_name}** (share **{top_share:.1%}** of **{total_inc}**). | Bar shows **{top_name}** dominates with **{top_cnt}** incidents; top-3 cover **{top3_share:.1%}**—rich automation surface. |
| Optimize staffing for top categories | **Phase 1 – Plan:** Use the category mix and historical volume to plan rosters so staff capacity matches the load in the highest volume categories. <br><br>**Phase 2 – Allocate:** Pre-assign clear owners and backups for top categories so tickets are picked up quickly without confusion or re-routing. <br><br>**Phase 3 – Review:** Compare planned capacity against actual volume weekly and adjust shift patterns or headcount where the gap is persistent. | - This reduces reactive overtime because peaks in the highest volume categories are anticipated and properly staffed.<br><br>- It stabilizes throughput by ensuring that top categories always have enough capacity to handle daily demand.<br><br>- It improves predictability of operations because managers can see where capacity is tight and respond before backlogs grow.<br><br>- It helps maintain consistent service quality across months instead of swinging between overloaded and underutilized teams.<br><br> | **Overtime avoided** = max(0, surge_volume − planned_capacity) × hours/ticket × overtime_rate; surge_volume guided by top-3 share (**{top3_share:.1%}** of **{total_inc}**). | Tall bars in top categories show persistent concentration needing planned capacity. |
| Streamline closure steps for frequent categories | **Phase 1 – Map:** Document the current closure steps for top categories and identify fields, approvals, and checks that are duplicated or rarely used. <br><br>**Phase 2 – Automate:** Configure forms to prefill fields from intake data or knowledge base content and remove steps that do not add value. <br><br>**Phase 3 – Measure:** Track the change in closure lead time per category and confirm that data quality and compliance are still maintained. | - This reduces per-ticket administration time because agents spend less effort filling unnecessary or duplicated fields.<br><br>- It accelerates ticket closure, which improves overall throughput and helps keep queues shorter.<br><br>- It lowers rework because required information is prefilled and less likely to be missed or entered incorrectly.<br><br>- It frees up agent capacity to focus on diagnosis and resolution instead of manual documentation work.<br><br> | **Hours saved** = (baseline_closure_mins − new_mins)/60 × volume(top-5=**{top5_vol}**). | Concentration in top-5 (**{top5_vol}** tickets) means small per-ticket wins scale materially. |
| Fast-track low-complexity variants | **Phase 1 – Segment:** Within the top categories, clearly define what qualifies as a low-complexity request and validate that these cases rarely need escalation. <br><br>**Phase 2 – Route:** Configure rules so low-complexity tickets are automatically assigned to L1 teams with clear scripts and standard responses. <br><br>**Phase 3 – Audit:** Review error rates, rework, and escalations regularly to ensure quality remains acceptable in the fast-track lane. | - This reduces handling cost for simple requests because they are resolved quickly by L1 using predefined scripts.<br><br>- It clears capacity for higher complexity work by keeping simple tickets away from senior engineers.<br><br>- It shortens resolution time for users with straightforward issues because they are not stuck behind complex work in the queue.<br><br>- It improves overall operational flow because fast-moving tickets do not clog shared queues and increase wait times for others.<br><br> | **Cost avoided** = low_complexity_tickets × (mins_saved/60) × rate; bound using long-tail share **{tail_share:.0%}** to avoid overload. | Long-tail categories plus simple variants inside top drivers are ideal fast-lane candidates. |
| Improve first-contact resolution (FCR) in top categories | **Phase 1 – KB:** Capture the most common fixes in a simple knowledge base for agents and users, focusing first on **{top_name}** and other high-volume categories. <br><br>**Phase 2 – Coach:** Train agents on how to use the knowledge base and guide conversations so that issues are resolved during the first interaction. <br><br>**Phase 3 – Track:** Monitor FCR percentage and reopen rates per category and refine content or coaching where results are weak. | - This reduces repeat handling because more tickets are solved completely during the first interaction with the user.<br><br>- It lowers total ticket volume over time because issues are fully resolved and do not come back as reopens or new incidents.<br><br>- It decreases escalation load on higher tiers as fewer cases need to be passed to senior teams.<br><br>- It improves user satisfaction because customers get quicker, clearer resolutions without multiple contacts.<br><br> | **Hours avoided** = reopens_avoided × avg_resolution_hours. Use top category (**{top_name}**) as the pilot. | Recurring dominance of **{top_name}** implies repeated patterns suitable for FCR uplift. |
""",
                    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| WIP limits by category | **Phase 1 – Set:** Define realistic work-in-progress limits for each category based on complexity, average handling time, and available staff. <br><br>**Phase 2 – Enforce:** Implement pull-based work so agents only pick up new tickets when they have capacity within the WIP limit. <br><br>**Phase 3 – Inspect:** Regularly review aging and lead time metrics to refine WIP limits and rules where queues still grow. | - This smooths workflow because teams avoid taking on more tickets than they can actively progress.<br><br>- It reduces ticket aging as agents focus on finishing current work before starting new tasks.<br><br>- It improves predictability of closure rates because workload is better matched to team capacity.<br><br>- It helps highlight bottlenecks when WIP limits are consistently reached, prompting structural fixes instead of firefighting.<br><br> | **Throughput gain** = (post-WIP closures/day − baseline) × days for top categories. | Top bars indicate overload risk without WIP, especially in **{top_name}**. |
| Prioritize business-critical categories | **Phase 1 – Classify:** Agree with business stakeholders on which categories represent high impact or critical services. <br><br>**Phase 2 – Route:** Configure routing so high-impact categories go to experienced teams or follow fast-lane rules with clear SLAs. <br><br>**Phase 3 – Verify:** Track SLA performance and escalations for these categories to confirm that the new routing improves outcomes. | - This lifts SLA adherence where business impact is greatest because critical tickets receive faster and more focused attention.<br><br>- It reduces escalations from key stakeholders who previously experienced delays on high-impact issues.<br><br>- It improves the stability of core services by ensuring that incidents affecting them are handled quickly and consistently.<br><br>- It helps align operations with business priorities instead of treating all categories with the same urgency.<br><br> | **SLA savings** = overdue_avoided × penalty_per_breach in top categories. | Category concentration shows where SLA failures hurt most. |
| Category performance dashboard | **Phase 1 – Instrument:** Build a dashboard that shows trends, aging, and SLA metrics by category so performance can be monitored in one place. <br><br>**Phase 2 – Alert:** Configure threshold-based alerts for spikes in volume, aging, or SLA breaches so leaders can react quickly. <br><br>**Phase 3 – Act:** Use the insights from the dashboard to decide when to surge staff, update processes, or launch automation initiatives. | - This enables faster interventions because leaders can see issues by category without manually compiling data.<br><br>- It reduces the risk of unnoticed backlogs as alerts signal when metrics exceed agreed thresholds.<br><br>- It supports continuous improvement by making trend analysis straightforward during reviews.<br><br>- It provides a common view for operations and business stakeholders, which improves alignment and decision making.<br><br> | **Efficiency gain** = (closure_rate_improvement × category_volume). | Persistent dominance in top-3 (**{top3_share:.1%}**) warrants live monitoring. |
| Swarm the top category during surges | **Phase 1 – Trigger:** Define a clear surge threshold for **{top_name}** and other key categories based on normal daily volume and acceptable queue size. <br><br>**Phase 2 – Staff:** When the threshold is hit, temporarily assign extra cross-functional staff to clear the backlog in the affected category. <br><br>**Phase 3 – Retrospect:** After the surge, review what caused the spike and identify process or technology fixes to prevent recurrence. | - This rapidly reduces backlogs when volume spikes occur in **{top_name}** or similar categories.<br><br>- It protects SLA performance by preventing long waits during temporary demand shocks.<br><br>- It lowers stress on the core team because additional staff share the load during intense periods.<br><br>- It helps uncover structural issues that caused the surge, leading to more permanent performance improvements later.<br><br> | **Hours reduced** = extra_staff × hours_per_ticket × surge_days. | Tallest bar (**{top_name}** = **{top_cnt}**) is the natural target for swarming. |
| Monitor category trend shifts monthly | **Phase 1 – Compare:** Review month-over-month volume changes in the top ten categories and note any unusually fast growth or decline. <br><br>**Phase 2 – Explain:** Discuss with support teams and business owners why these changes occurred and confirm whether they reflect real demand shifts or data issues. <br><br>**Phase 3 – Decide:** Adjust capacity, automation focus, or process changes where sustained shifts are observed. | - This prevents surprises by catching growth in certain categories before it becomes unmanageable.<br><br>- It enables proactive capacity planning because teams can see where demand is rising and allocate resources earlier.<br><br>- It reduces wasted effort on categories that are shrinking, allowing resources to be redeployed to higher-value areas.<br><br>- It improves strategic planning by linking category trends to product, service, or infrastructure changes in the environment.<br><br> | **Value** = (opened_closed_delta × hours_per_ticket) across categories with shifts. | Long-tail share (**{tail_share:.0%}**) can hide growth pockets—keep watch. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish resolution plans for top categories | **Phase 1 – Draft:** For **{top_name}** and other major categories, write clear resolution plans that describe typical steps, timelines, and possible workarounds. <br><br>**Phase 2 – Communicate:** Share these plans on the portal, in email templates, and in agent scripts so users know what to expect. <br><br>**Phase 3 – Update:** Regularly update the plans as root causes change or improvements are implemented and inform users about these updates. | - This improves transparency because users can see how their issue will be handled and how long it is likely to take.<br><br>- It reduces uncertainty and anxiety, which lowers the number of repeated follow-up contacts from users asking for updates.<br><br>- It builds trust since users perceive that incidents are managed in a structured and predictable way.<br><br>- It supports agents by giving them a consistent message to share with customers for common scenarios in **{top_name}** and similar categories.<br><br> | **Savings** = followups_avoided × handling_cost; audience size proxied by **{top_cnt}** incidents in **{top_name}**. | Largest category (**{top_name}**) impacts the widest user base—clear plans matter most here. |
| Proactive user updates during spikes | **Phase 1 – Detect:** Use monitoring or dashboards to detect spikes in incident volume for major categories before backlogs become critical. <br><br>**Phase 2 – Notify:** Send proactive messages to affected users explaining the situation, expected delays, and any available workarounds. <br><br>**Phase 3 – Measure:** Track complaint and escalation trends during spikes to verify that proactive communication is reducing negative feedback. | - This reduces inbound complaints because users are informed early and do not need to chase the service desk for updates.<br><br>- It improves user perception of reliability, even when delays occur, because communication feels timely and honest.<br><br>- It lowers workload on front-line agents by decreasing repeated status enquiries during busy periods.<br><br>- It helps protect brand reputation when high-impact incidents occur across a large user base.<br><br> | **Avoided cost** = complaints_avoided × escalation_cost; trigger when top-3 share (**{top3_share:.1%}**) surges. | Concentration in a few categories means comms scales to many users quickly. |
| VIP fast-lane within top categories | **Phase 1 – Tag:** Identify VIP users and tag their incidents within **{top_name}** and other critical categories so they can be recognized instantly. <br><br>**Phase 2 – Route:** Route VIP tickets to senior resolvers or specialized queues with stricter ETAs and clearer escalation paths. <br><br>**Phase 3 – Audit:** Regularly compare VIP SLA performance against general tickets to ensure the fast-lane is delivering the intended protection. | - This protects key accounts by ensuring that their incidents are always handled with higher priority and faster response.<br><br>- It reduces the risk of losing important customers due to repeated or prolonged service issues.<br><br>- It improves relationship quality with strategic stakeholders because they see tangible attention to their needs.<br><br>- It helps management track whether commitments made to VIP customers are being honored in daily operations.<br><br> | **Retention value** = VIP_breaches_avoided × revenue_at_risk. | Top-category congestion risks VIP dissatisfaction without a fast-lane. |
| Self-service for frequent issues | **Phase 1 – Curate:** Identify the most common questions or fixes in the top categories and create simple self-service articles or guided flows. <br><br>**Phase 2 – Launch:** Promote these self-service options through the portal, chatbots, or email templates so users know they exist. <br><br>**Phase 3 – Track:** Measure deflection rates, search usage, and feedback scores to see whether users can resolve issues without opening tickets. | - This provides faster answers because users can solve common issues immediately without waiting for an agent.<br><br>- It reduces ticket volume, which eases pressure on support teams and shortens queues for issues that truly require human attention.<br><br>- It improves user satisfaction when self-service content is clear and solves the problem on the first attempt.<br><br>- It creates a reusable knowledge foundation that can be extended to new services or categories as they grow.<br><br> | **Savings** = deflected_tickets × avg_handling_hours × rate; scope with **{top5_vol}** tickets. | Repetition in top categories screams for self-service coverage. |
| Communicate wins (category reduction) | **Phase 1 – Compare:** Measure before-and-after volumes for key categories when improvements or fixes are deployed. <br><br>**Phase 2 – Share:** Present these improvements in dashboards, newsletters, or town halls so both users and staff can see the impact. <br><br>**Phase 3 – Sustain:** Embed the successful changes into standard practice and keep monitoring to ensure volumes do not silently climb again. | - This improves trust because customers can see that reported issues lead to visible and sustained improvements.<br><br>- It reduces “any update” queries since users understand that the environment is actively managed and getting better.<br><br>- It boosts morale for support teams by making their impact visible and appreciated across the organization.<br><br>- It encourages collaboration on future initiatives because stakeholders see evidence that changes produce real benefits.<br><br> | **Value** = inquiries_avoided × cost_per_inquiry after volume drops. | Trend down in top bars shows tangible progress users should see. |
"""
                }

                render_cio_tables("Category Insights", cio)
        else:
            st.warning("Column 'service_category' is required for this section.")


    # ------------------ 2b Incidents by Priority/Level ------------------
    with st.expander("📌 Incidents by Priority (Level)"):
        if "level" in df_filtered.columns:
            lvl = df_filtered["level"].fillna("Not Assigned")
            counts = lvl.value_counts().reset_index()
            counts.columns = ["level", "count"]

            # --- Graph 1: Volume by Level
            fig = px.bar(counts, x="level", y="count", title="Incidents by Level", text="count")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # If everything is Not Assigned, warn and stop deeper analysis
            if len(counts) == 1 and str(counts.iloc[0]["level"]).strip().lower() in ["not assigned", "unknown", "na"]:
                st.warning("⚠️ All incidents are marked as 'Not Assigned'. Analysis and recommendations cannot be provided without Level assignment.")
            else:
                # --- Analysis for Graph 1
                st.markdown("### Analysis – Volume by Level")
                total_inc_lvl = int(counts["count"].sum())
                top_lvl = counts.iloc[0]
                low_lvl = counts.iloc[-1]
                st.write(f"""
**What this graph is:** A bar chart showing **incident distribution by Level (priority tier)**.  
- **X-axis:** Level values (e.g., L1, L2, P1, P2).  
- **Y-axis:** Number of incidents per Level.

**What it shows in your data:**  
Highest load at **{top_lvl['level']}** with **{int(top_lvl['count'])}** incidents (**{top_lvl['count']/total_inc_lvl:.1%}** of **{total_inc_lvl}**).  
Lowest load at **{low_lvl['level']}** with **{int(low_lvl['count'])}** incidents.

Overall, tall bars pinpoint **where operational load and SLA risk concentrate**; short bars indicate **niche/residual load**.

**How to read it operationally:**  
1) **Peaks:** Rebalance staffing, enforce WIP caps, and add fast-lane routing for SLA-risk Levels.  
2) **Plateaus:** Maintain assignment discipline and guardrails to keep flow steady.  
3) **Downswings:** Preserve practices that reduced queue size for specific Levels.  
4) **Mix:** Pair Level with **SLA adherence and aging** so urgent work isn’t delayed by volume.

**Why this matters:** Misaligned Level load drives **aging, breaches, and escalations**. Tackling top Levels first preserves **cost, performance, and satisfaction**.
""")

                # --- Graph 2: Resolution SLA by Level (if available)
                by_lvl = None
                if {"sla_resolution_time", "resolved_time", "created_time"} <= set(df_filtered.columns):
                    dfl = df_filtered.copy()
                    dfl["created_time"] = pd.to_datetime(dfl["created_time"], errors="coerce")
                    dfl["resolved_time"] = pd.to_datetime(dfl["resolved_time"], errors="coerce")
                    dfl["resolution_hours"] = (dfl["resolved_time"] - dfl["created_time"]).dt.total_seconds() / 3600
                    valid = dfl.dropna(subset=["resolution_hours", "sla_resolution_time", "level"]).copy()
                    if not valid.empty:
                        # ensure timedelta to hours
                        valid["sla_resolution_hours"] = valid["sla_resolution_time"].dt.total_seconds() / 3600
                        valid["met_sla"] = valid["resolution_hours"] <= valid["sla_resolution_hours"]
                        by_lvl = valid.groupby("level")["met_sla"].mean().reset_index()
                        by_lvl["SLA %"] = (by_lvl["met_sla"] * 100).round(1)

                        fig2 = px.bar(by_lvl, x="level", y="SLA %", title="Resolution SLA Adherence by Level",
                                      text="SLA %")
                        fig2.update_traces(textposition="outside")
                        st.plotly_chart(fig2, use_container_width=True)

                        # --- Analysis for Graph 2
                        st.markdown("### Analysis – Resolution SLA by Level")
                        best_row = by_lvl.loc[by_lvl["met_sla"].idxmax()]
                        worst_row = by_lvl.loc[by_lvl["met_sla"].idxmin()]
                        avg_sla = by_lvl["met_sla"].mean() * 100
                        st.write(f"""
**What this graph is:** A bar chart comparing **resolution SLA adherence** by Level.  
- **X-axis:** Level.  
- **Y-axis:** SLA adherence (% of tickets resolved within SLA).

**What it shows in your data:**  
Best Level: **{best_row['level']}** at **{best_row['SLA %']:.1f}%**.  
Weakest Level: **{worst_row['level']}** at **{worst_row['SLA %']:.1f}%**.  
Average across Levels: **{avg_sla:.1f}%**.

Overall, tall bars = **more targets met**; short bars = **risk pockets** needing routing, staffing or runbook fixes.

**How to read it operationally:**  
1) **Peaks:** Replicate the practices of the best Level (ownership, fast lanes, vendor SLAs).  
2) **Plateaus:** Standardize mid-performers to lift the floor.  
3) **Downswings:** Add escalation tiers and senior ownership for weak Levels.  
4) **Mix:** Cross-reference with volume bars to size total SLA impact.

**Why this matters:** Level-specific SLA protects **business-critical users** and raises the **compliance baseline**.
""")

                # --- CIO tables (use real values from graphs)
                # values reused in tables:
                top_level_name = str(top_lvl["level"])
                top_level_cnt = int(top_lvl["count"])

                if by_lvl is not None and not by_lvl.empty:
                    best_level = str(best_row["level"])
                    best_sla = float(best_row["SLA %"])
                    worst_level = str(worst_row["level"])
                    worst_sla = float(worst_row["SLA %"])
                    avg_sla_pct = float(avg_sla)
                else:
                    best_level = "-"
                    best_sla = 0.0
                    worst_level = "-"
                    worst_sla = 0.0
                    avg_sla_pct = 0.0

                cio = {
                    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Optimize staffing for high-volume Levels | **Phase 1 – Plan:** Use historical incident counts to size capacity for each Level, ensuring that heavy Levels like **{top_level_name}** with **{top_level_cnt}** cases have enough staff. <br><br>**Phase 2 – Assign:** Define clear ownership and backup arrangements so that tickets in these Levels are picked up quickly without bouncing between queues. <br><br>**Phase 3 – Review:** Compare planned capacity with actual incident patterns weekly and adjust shifts or assignments where gaps persist. | - This reduces reactive overtime because peaks in high-volume Levels are anticipated rather than handled at the last minute.<br><br>- It lowers cost per incident by matching staffing to demand so fewer tickets wait in queues and require catch-up work later.<br><br>- It stabilizes work for agents because they face more predictable loads instead of sudden uncontrolled spikes.<br><br>- It minimizes the need for expensive emergency measures such as temporary contractors when volume is misjudged.<br><br> | **Overtime avoided** = max(0, surge_incidents − planned_capacity) × hours_per_ticket × overtime_rate; surge guided by **{top_level_name}** share (**{top_lvl['count']/total_inc_lvl:.1%}**). | Volume bar shows **{top_level_name}** dominates counts; mismatched staffing inflates cost. |
| Automate low-priority Level flows | **Phase 1 – Select:** Identify low-priority Levels where incidents are repetitive and have low business risk, making them suitable for automation. <br><br>**Phase 2 – Script:** Build bots, FAQs, or guided flows that handle common requests end to end for these Levels without agent intervention. <br><br>**Phase 3 – Measure:** Monitor deflection rates, error cases, and customer feedback to ensure automation quality remains acceptable. | - This frees higher-skilled analysts to focus on urgent and complex Levels while routine low-priority work is automated.<br><br>- It reduces average handling time for low-priority tickets because automated flows complete tasks faster than manual processing.<br><br>- It lowers overall operational cost as more of the simple workload is shifted away from human agents.<br><br>- It keeps queues for low-priority Levels under control so they do not quietly consume capacity needed elsewhere.<br><br> | **Savings** = tickets_deflected × avg_handling_hours × rate; size using small-Level volumes to start. | Tail Levels with repeat patterns are visible in the bar distribution. |
| Gate non-urgent intake during spikes | **Phase 1 – Policy:** Agree on clear rules that allow non-urgent Levels to be deferred temporarily when critical Levels experience spikes. <br><br>**Phase 2 – Implement:** Configure queues, forms, or communication so non-urgent requests are clearly marked and scheduled into future slots during peak periods. <br><br>**Phase 3 – Monitor:** Track aging and satisfaction for deferred tickets to ensure delays remain reasonable and well communicated. | - This prevents critical Levels from being crowded out by low-priority work when the system is under stress.<br><br>- It reduces costly escalations that arise when critical tickets are delayed due to unfiltered intake of non-urgent issues.<br><br>- It makes use of available capacity more intelligently by shifting non-urgent work to quieter periods.<br><br>- It maintains a better overall cost profile because teams do not need to hire or extend shifts solely to handle avoidable congestion.<br><br> | **Hours saved** = deferred_nonurgent × (mins_saved/60) × rate during peak weeks. | Volume peaks in higher Levels and weak SLA pockets (worst Level **{worst_level}** at **{worst_sla:.1f}%**) justify gating. |
""",
                    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Enforce strict triage guardrails | **Phase 1 – Define:** Create clear, written criteria for each Level based on impact and urgency so intake staff know exactly how to classify incidents. <br><br>**Phase 2 – Validate:** Embed these rules in forms or automation so misclassifications are reduced at the point of ticket creation. <br><br>**Phase 3 – Audit:** Review samples of tickets every week to spot misclassified incidents and refine the criteria where needed. | - This improves SLA compliance because incidents are routed correctly from the start and reach the right teams faster.<br><br>- It reduces rework where tickets previously had to be re-leveled and re-assigned after being picked up by the wrong team.<br><br>- It shortens lead time for critical incidents by preventing them from being buried in queues meant for less urgent work.<br><br>- It increases confidence among support teams that the work arriving in their queue matches their mandate and skill set.<br><br> | **SLA uplift** = breaches_avoided × penalty; target weak Level (**{worst_level}**, **{worst_sla:.1f}%**). | SLA bar shows **{worst_level}** trailing the field; mis-triage likely contributes. |
| Live dashboards by Level | **Phase 1 – Instrument:** Build a dashboard showing volume, aging, and SLA adherence by Level so performance can be tracked in real time. <br><br>**Phase 2 – Alert:** Configure threshold alerts that notify managers when specific Levels approach critical aging or breach risks. <br><br>**Phase 3 – Act:** Use the dashboard to trigger interventions such as reassigning staff, escalating issues, or adjusting priorities. | - This enables managers to see where problems are forming across Levels before they become severe backlogs.<br><br>- It supports more accurate staffing decisions because leaders can see which Levels are consuming the most effort over time.<br><br>- It reduces blind spots by providing a single view across all Levels instead of relying on anecdotal feedback.<br><br>- It helps track the impact of process changes by showing how metrics shift after new policies or tools are introduced.<br><br> | **Efficiency gain** = (closure_rate_improvement × volume(Level=**{top_level_name}**)). | Peaks in **{top_level_name}** require dynamic balancing to avoid backlog. |
| Swarm critical Levels on demand | **Phase 1 – Trigger:** Define specific surge criteria for critical Levels so the team knows when a swarm action should be initiated. <br><br>**Phase 2 – Staff:** Mobilize cross-functional resources from other queues or teams to temporarily focus on the overloaded Level. <br><br>**Phase 3 – Retrospect:** After the swarm, analyze root causes and agree actions that reduce the likelihood of the same surge happening again. | - This reduces SLA breaches in critical Levels by rapidly clearing backlogs when demand spikes unexpectedly.<br><br>- It improves response times for high-impact tickets because additional capacity is focused where it matters most.<br><br>- It reduces strain on the core team by sharing surge workload with other parts of the organization.<br><br>- It generates insights about systemic weaknesses revealed during surges, which can guide long-term performance improvements.<br><br> | **Hours reduced** = extra_staff × hours_per_ticket × spike_days; focus where SLA is weakest (**{worst_level}** = **{worst_sla:.1f}%**). | Weak SLA pockets combined with high volume are prime swarm candidates. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| VIP fast-lane in critical Levels | **Phase 1 – Tag:** Work with account and business teams to identify VIP users and ensure their tickets at critical Levels are clearly marked in the system. <br><br>**Phase 2 – Route:** Configure routing so VIP incidents are handled by experienced staff or dedicated queues with tighter ETAs. <br><br>**Phase 3 – Review:** Regularly compare VIP SLA and satisfaction scores against the overall population to confirm the fast-lane is effective. | - This protects strategic customers by ensuring their critical issues are always treated with elevated urgency.<br><br>- It reduces the risk of churn among high-value clients who are sensitive to service disruptions.<br><br>- It strengthens relationships with key stakeholders because their issues receive visible and consistent attention.<br><br>- It provides management with clear evidence that commitments made to VIP customers are being honored operationally.<br><br> | **Retention value** = VIP_breaches_avoided × revenue_at_risk; benchmark against avg Level SLA (**{avg_sla_pct:.1f}%**). | SLA chart shows variability across Levels (best **{best_level}** **{best_sla:.1f}%**, worst **{worst_level}** **{worst_sla:.1f}%**). |
| Proactive updates by Level | **Phase 1 – Detect:** Use aging and SLA indicators to identify tickets at each Level that are at risk of delay or breach. <br><br>**Phase 2 – Notify:** Send structured updates to affected users that explain the status, next steps, and expected timelines. <br><br>**Phase 3 – Measure:** Track follow-up enquiries and complaints to see whether proactive updates are reducing repeated contacts. | - This cuts follow-up volume because users feel informed and no longer need to chase the service desk for news.<br><br>- It improves trust by showing that the team is actively monitoring and managing tickets rather than letting them stall unnoticed.<br><br>- It reduces frustration for users when delays are unavoidable because expectations are managed early and clearly.<br><br>- It supports agents by reducing the number of low-value “any update” interactions they must handle.<br><br> | **Avoided costs** = followups_avoided × handling_cost; scale to high-volume Level **{top_level_name}**. | High volume at **{top_level_name}** means comms has outsized CSAT impact. |
| Publish Level-based SLA performance | **Phase 1 – Report:** Prepare simple, regular summaries that show SLA performance by Level for internal stakeholders and, where appropriate, for customers. <br><br>**Phase 2 – Explain:** Provide short explanations for underperformance at specific Levels and describe the actions being taken to improve. <br><br>**Phase 3 – Track:** Monitor improvements month over month to demonstrate progress and keep attention on weak areas. | - This increases transparency and helps stakeholders understand where service is strong and where it needs improvement.<br><br>- It encourages constructive dialogue about priorities and investments because decisions are grounded in shared data.<br><br>- It supports accountability by making it clear which Levels are not meeting agreed targets and who owns the remediation actions.<br><br>- It can improve satisfaction over time as customers see that problems are acknowledged and actively managed rather than ignored.<br><br> | **Value** = (CSAT uplift % × tickets in Level). | SLA bars (best **{best_level}** **{best_sla:.1f}%**, worst **{worst_level}** **{worst_sla:.1f}%**) show clear disclosure targets. |
"""
                }
                render_cio_tables("Level Insights", cio)

        else:
            st.info("No 'level' column to evaluate incidents by priority.")
