# utils_service_desk_pfomance/recommendation_performance/ticket_volume.py

import streamlit as st
import plotly.express as px
import pandas as pd

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)



def ticket_volume(df_filtered):

    # ---------------------- 1a ----------------------
    with st.expander("📌 Number of Tickets Opened"): 
        if "created_time" in df_filtered.columns:
            df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date
            trend = df_filtered.groupby("created_date").size().reset_index(name="ticket_count")

            # Format dates to Malaysian format (DD/MM/YYYY)
            trend["created_date_str"] = pd.to_datetime(trend["created_date"]).dt.strftime("%d/%m/%Y")

            # --- Graph 1: Tickets opened over time (line chart)
            fig = px.line(trend, x="created_date_str", y="ticket_count", title="Tickets Opened Over Time")
            st.plotly_chart(fig, use_container_width=True)

            # 🔹 Dynamic analysis for tickets opened over time
            if not trend.empty:
                total_tickets = trend["ticket_count"].sum()
                avg_tickets = trend["ticket_count"].mean()
                max_row = trend.loc[trend["ticket_count"].idxmax()]
                min_row = trend.loc[trend["ticket_count"].idxmin()]
                change_pct = ((max_row["ticket_count"] - min_row["ticket_count"]) / max(min_row["ticket_count"], 1)) * 100

                st.markdown("### Analysis of Tickets Opened Over Time")
                st.write(f"""
                **What this graph is:** A throughput chart showing how many tickets were **opened each day**.  
                - **X-axis:** Calendar date (DD/MM/YYYY).  
                - **Y-axis:** Count of tickets that moved into an opened state on that date.

                **What it shows in your data:**  
                Across the period, a total of **{total_tickets:,} tickets** were opened, with a daily average of approximately **{avg_tickets:.1f} tickets**.  
                The highest opening activity occurred on **{max_row['created_date_str']}**, with **{max_row['ticket_count']} tickets opened**, while the lowest was on **{min_row['created_date_str']}**, with **{min_row['ticket_count']} tickets opened**.  
                Between peak and trough the relative change is about **{change_pct:.1f}%**.

                Overall, the opening pattern indicates {"consistent demand" if change_pct < 20 else "a volatile inflow pattern"}. Peaks (e.g., **{max_row['created_date_str']}**) may reflect incidents, deployments, or cyclical demand; troughs (e.g., **{min_row['created_date_str']}**) often align with weekends, holidays, or lower business activity.

                **How to read it operationally:**  
                1) **Stability vs. volatility:** Large swings mean staffing and SLA risk on spike days.  
                2) **Bottleneck detection:** Sustained high-intake sequences require matching capacity or triage.  
                3) **Momentum:** Compare early vs late periods to spot rising pressure on the desk.  
                4) **Fairness & staff load:** Pair with the per-technician chart to confirm whether intake surges were absorbed evenly.

                **Why this matters:** Inflow sets the workload baseline. When openings routinely exceed closures, backlog grows and SLA risk climbs; steadier inflow enables predictable staffing and better customer experience.
                """)

            else:
                st.info("No data available to generate analysis.")

            # --- Graph 2: Tickets opened by department (bar chart)
            if "department" in df_filtered.columns:
                dept_summary = df_filtered.groupby("department").size().reset_index(name="ticket_count")

                # Add selector: Top 10 Highest or Lowest departments
                option = st.radio(
                    "Select Department View:",
                    ("Top 10 Highest", "Top 10 Lowest"),
                    horizontal=True
                )

                if option == "Top 10 Highest":
                    dept_top10 = dept_summary.sort_values("ticket_count", ascending=False).head(10)
                    title = "Top 10 Departments with Highest Tickets Opened"
                else:
                    dept_top10 = dept_summary.sort_values("ticket_count", ascending=True).head(10)
                    title = "Top 10 Departments with Lowest Tickets Opened"

                fig_dept = px.bar(
                    dept_top10,
                    x="department",
                    y="ticket_count",
                    title=title,
                    text="ticket_count"
                )
                fig_dept.update_traces(textposition="outside")
                st.plotly_chart(fig_dept, use_container_width=True)

                # 🔹 Department-level analysis
                if not dept_top10.empty:
                    max_dept = dept_top10.loc[dept_top10["ticket_count"].idxmax()]
                    min_dept = dept_top10.loc[dept_top10["ticket_count"].idxmin()]

                    st.markdown("### Analysis of Departments with Tickets Opened")
                    st.write(f"""
                    **What this graph is:** A throughput allocation chart showing how many tickets were **opened by department**.  
                    - **X-axis:** Department.  
                    - **Y-axis:** Count of tickets opened (with labels showing the exact count).

                    **What it shows in your data:**  
                    This view displays **{title.lower()}**. The department with the highest volume is **{max_dept['department']}** with **{max_dept['ticket_count']} tickets**, while the lowest in this selection is **{min_dept['department']}** with **{min_dept['ticket_count']} tickets**.

                    Overall, the distribution indicates that workload is **concentrated** in certain departments (e.g., **{max_dept['department']}**), which may reflect system reliance, user population size, or local process issues. Lower bars can indicate lighter demand or under-reporting.

                    **How to read it operationally:**  
                    1) **Focus areas:** High bars are priority candidates for root-cause and enablement.  
                    2) **Capacity fit:** Align staffing hours and skills with high-volume departments.  
                    3) **Change impact:** Watch for shifts after rollouts or policy changes.  
                    4) **Equity:** Ensure low-volume areas aren’t masked by intake channels or access friction.

                    **Why this matters:** Knowing **where** demand originates guides targeted fixes, training, and automation—unlocking the fastest path to lower cost and higher satisfaction.
                    """)


            # --- Evidence strings for CIO tables (still used later)
            peak_evidence = f"Graph shows peak on {max_row['created_date_str']} with {max_row['ticket_count']} tickets compared to low on {min_row['created_date_str']} with {min_row['ticket_count']} tickets."
            avg_evidence = f"Average daily volume = {avg_tickets:.1f} tickets; peak deviation highlights workload surges."

            # Department-level evidence (depends on Top 10 selection)
            if option == "Top 10 Highest":
                dept_top = dept_top10.loc[dept_top10["ticket_count"].idxmax()]
                dept_bottom = dept_top10.loc[dept_top10["ticket_count"].idxmin()]
                dept_evidence = (
                    f"Department analysis (Top 10 Highest) shows **{dept_top['department']}** as the highest with "
                    f"**{dept_top['ticket_count']} tickets**, while **{dept_bottom['department']}** has the lowest with "
                    f"**{dept_bottom['ticket_count']} tickets** in this group."
                )
            else:
                dept_top = dept_top10.loc[dept_top10["ticket_count"].idxmax()]
                dept_bottom = dept_top10.loc[dept_top10["ticket_count"].idxmin()]
                dept_evidence = (
                    f"Department analysis (Top 10 Lowest) shows **{dept_top['department']}** as the highest within this "
                    f"group at **{dept_top['ticket_count']} tickets**, while **{dept_bottom['department']}** recorded only "
                    f"**{dept_bottom['ticket_count']} tickets**."
                )

            resolution_evidence = f"Average resolution time = {df_filtered['resolution_time'].mean():.2f} hours across {len(df_filtered)} tickets."
            sla_evidence = f"Spike on {max_row['created_date_str']} with {max_row['ticket_count']} tickets indicates SLA breach risk compared to average {avg_tickets:.1f} tickets/day."

            cio_1a = {
            "cost": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | **Automate triage for high-volume request types** | **Phase 1:** Identify top ticket categories contributing to peaks.<br><br>**Phase 2:** Deploy rule-based intake forms and auto-routing.<br><br>**Phase 3:** Monitor and refine automation rules quarterly.<br><br>This eliminates repetitive manual intake and reduces errors. | - Saves staff hours spent on manual categorization.<br><br>- Reduces misroutes and rework handoffs that inflate cost.<br><br>- Lowers first-response latency during spikes (overtime avoidance).<br><br>- Stabilizes intake quality for cleaner downstream processing.<br><br>- Frees senior staff for higher-value work. | **Formula:** Hours Saved = Reduction% × Avg Response Time × Total Tickets.<br><br>Dataset: 15% reduction × {df_filtered['resolution_time'].mean():.2f} hrs × {len(df_filtered)} tickets = **{df_filtered['resolution_time'].mean() * len(df_filtered) * 0.15:.2f} hrs saved**. | {peak_evidence} |
            | **Adjust staffing schedules to demand patterns** | **Phase 1:** Analyze line/bar charts to spot peak weeks/months.<br><br>**Phase 2:** Shift staffing hours to align with high-volume periods.<br><br>**Phase 3:** Reassess quarterly to refine allocation.<br><br>This ensures resources match workload demand. | - Reduces overtime hours and premium pay during spikes.<br><br>- Cuts idle time in troughs via smarter rosters.<br><br>- Minimizes SLA penalty exposure by matching capacity to load.<br><br>- Improves staff wellbeing, lowering attrition cost.<br><br>- Increases utilization of contracted hours. | **Formula:** Overtime Savings = (Overtime Hours Avoided × Avg Hourly Rate).<br><br>Dataset: peak = {max_row['ticket_count']} vs avg = {avg_tickets:.1f} tickets → excess workload reallocation possible. | {avg_evidence} |
            | **Eliminate duplicate ticket categories** | **Phase 1:** Review frequency counts by category.<br><br>**Phase 2:** Merge overlapping categories into standardized groups.<br><br>**Phase 3:** Implement routing rules for consistency.<br><br>This reduces rework and simplifies intake. | - Fewer misclassifications reduce clarification back-and-forth.<br><br>- Less analyst time spent correcting categories.<br><br>- More accurate reporting → better cost targeting.<br><br>- Simplified KB and forms reduce maintenance overhead.<br><br>- Faster onboarding for new analysts. | **Formula:** Time Saved = Duplicates × Avg Handling Time × Ticket Volume.<br><br>Dataset: {df_filtered['department'].nunique()} departments may include redundant categories. | {dept_evidence} |
            | **Automate ticket acknowledgments** | **Phase 1:** Configure system to send confirmation messages upon ticket creation.<br><br>**Phase 2:** Customize acknowledgment templates by category.<br><br>**Phase 3:** Review usage and customer feedback.<br><br>This lowers follow-up calls and reduces handling costs. | - Reduces inbound “status check” contacts (call/chat deflection).<br><br>- Prevents duplicate submissions by reassuring users.<br><br>- Cuts manual comms time per ticket.<br><br>- Improves perceived responsiveness with minimal cost.<br><br>- Standardizes messaging to reduce error risk. | **Formula:** Savings = Avoided duplicate tickets × Avg Handling Time.<br><br>Dataset: spike days (above mean) indicate potential duplicates avoided. | {peak_evidence} |
            | **Reallocate resources from lowest-volume departments** | **Phase 1:** Identify departments with consistently low ticket volumes.<br><br>**Phase 2:** Shift part of their support resources to busier departments.<br><br>**Phase 3:** Reassess quarterly to maintain balance.<br><br>This prevents underutilization. | - Converts idle time to productive coverage in hotspots.<br><br>- Lowers reliance on overtime in high-volume areas.<br><br>- Improves ROI on existing headcount.<br><br>- Increases speed-to-answer where it matters most.<br><br>- Preserves service quality in low-volume areas via shared pools. | **Formula:** Savings = (Idle Hours × Avg Hourly Rate).<br><br>Dataset: departments with minimal tickets reflect resource underutilization. | {dept_evidence} |
            | **Target cost audits at high-volume departments** | **Phase 1:** Focus cost reviews on top 3 highest ticket-generating departments.<br><br>**Phase 2:** Identify inefficiencies unique to these groups.<br><br>**Phase 3:** Implement process improvements.<br><br>This directly reduces workload where impact is greatest. | - Concentrates savings on the biggest cost drivers.<br><br>- Rapid payback due to scale effects (Pareto 80/20).<br><br>- Surfaces automation and policy changes with outsized ROI.<br><br>- Improves forecasting accuracy for budget planning.<br><br>- Reduces escalations tied to chronic failure modes. | **Formula:** Cost Avoidance = (# Tickets Reduced × Avg Handling Cost).<br><br>Dataset: {dept_top['department']} recorded {dept_top['ticket_count']} tickets — priority candidate. | {dept_evidence} |
            """,
            "performance": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | **Implement dynamic routing to skill-based groups** | **Phase 1:** Map categories to skills.<br><br>**Phase 2:** Create routing rules to minimize reassignments.<br><br>**Phase 3:** Track and refine rules based on SLA adherence.<br><br>This minimizes handling delays. | - Cuts reassignment loops and wait time.<br><br>- Improves first-touch resolution probability.<br><br>- Raises SLA-on-time percentage.<br><br>- Reduces variance in cycle time (more predictability).<br><br>- Increases analyst engagement by aligning skills to work. | **Formula:** Hours Saved = Reduction% × Avg Resolution Time × Tickets.<br><br>If routing reduces resolution by 10% → 0.10 × {df_filtered['resolution_time'].mean():.2f} × {len(df_filtered)} = **{df_filtered['resolution_time'].mean() * len(df_filtered) * 0.10:.2f} hrs saved**. | {resolution_evidence} |
            | **Expand knowledge base with FAQs** | **Phase 1:** Identify most frequent categories.<br><br>**Phase 2:** Build articles, guides, and videos.<br><br>**Phase 3:** Integrate knowledge base into service portal.<br><br>This empowers users and reduces repetitive ticket creation. | - Increases self-service and agent assist speed.<br><br>- Shortens TTFR/MTTR across common issues.<br><br>- Reduces reopen rates via better guidance.<br><br>- Scales expertise without adding headcount.<br><br>- Supports training for new joiners. | **Formula:** Savings = Avg Time Saved per Repeated Ticket × #Tickets.<br><br>Dataset categories show concentration in top 5 areas → high self-service potential. | {dept_evidence} |
            | **Introduce real-time workload dashboards** | **Phase 1:** Build visual dashboards to monitor daily ticket load.<br><br>**Phase 2:** Provide supervisors with live monitoring.<br><br>**Phase 3:** Adjust staff allocation dynamically.<brDashboards improve visibility and accountability. | - Enables rapid intervention when queues spike.<br><br>- Improves assignment balance in-shift (less over-WIP).<br><br>- Raises forecast accuracy for the next day/week.<br><br>- Reduces SLA breaches through earlier action.<br><br>- Increases transparency for management reviews. | **Formula:** Productivity Gain = Reduction in Idle Time × Avg Hourly Rate.<br><br>Dataset shows idle periods after peak surges. | {avg_evidence} |
            | **Apply predictive analytics for peak forecasting** | **Phase 1:** Use historical ticket data to model peak cycles.<br><br>**Phase 2:** Integrate forecasts into scheduling.<br><br>**Phase 3:** Revalidate predictions monthly.<br><br>This anticipates demand and prevents overload. | - Proactive staffing prevents backlog growth.<br><br>- Better change/maintenance timing around predicted peaks.<br><br>- Higher SLA adherence with fewer emergency shifts.<br><br>- Smoother cycle times and steadier throughput.<br><br>- Reduces firefighting and context switching. | **Formula:** SLA Gain = Tickets Resolved within SLA ÷ Total Tickets.<br><br>Peaks align with SLA breaches — predictive allocation improves ratio. | {sla_evidence} |
            | **Benchmark performance by department** | **Phase 1:** Compare SLA compliance rates across departments.<br><br>**Phase 2:** Identify best practices from top performers.<br><br>**Phase 3:** Roll out improvements to weaker departments.<br><br>This standardizes efficiency. | - Elevates lagging areas with proven practices.<br><br>- Reveals hidden constraints (tools, policy, skills).<br><br>- Creates fair targets and healthy competition.<br><br>- Improves consistency across the enterprise.<br><br>- Simplifies executive reporting. | **Formula:** SLA Gain = (Improved SLA% × Tickets per Department).<br><br>Dataset: variation between high vs low ticket departments shows unequal performance. | {dept_evidence} |
            | **Introduce department-specific KPIs** | **Phase 1:** Develop KPIs aligned with each department’s ticket profile.<br><br>**Phase 2:** Track monthly.<br><br>**Phase 3:** Adjust strategies where KPIs fall short.<br><br>Tailored KPIs address each department’s challenges. | - Focuses each team on the few metrics that matter.<br><br>- Drives targeted improvements vs. generic pushes.<br><br>- Improves accountability with clear ownership.<br><br>- Enhances early-warning signals for leadership.<br><br>- Links performance to operational levers. | **Formula:** Performance Uplift = (Improved KPI × Ticket Volume).<br><br>Dataset: {dept_top['department']} leads in volume but may lag in SLA adherence. | {dept_evidence} |
            """,
            "satisfaction": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |----------------|----------------------|----------|------------------|--------------------------------|
            | **Provide transparent ticket status updates** | **Phase 1:** Enable customer self-service portals with live ticket tracking.<br><br>**Phase 2:** Automate real-time status notifications.<br><br>**Phase 3:** Gather customer satisfaction survey feedback.<br><br>This reduces frustration from uncertainty. | - Lowers inbound “check status” contacts (less friction).<br><br>- Builds trust with predictable, proactive updates.<br><br>- Improves CSAT/NPS through perceived responsiveness.<br><br>- Reduces escalation triggers caused by silence gaps.<br><br>- Enhances transparency for VIP stakeholders. | **Formula:** Complaints Avoided × Avg Handling Cost per Complaint.<br><br>Dataset: peaks correlate with higher inquiries → avoided through visibility. | {peak_evidence} |
            | **Introduce SLA-based priority tiers** | **Phase 1:** Define SLA categories (critical, high, normal, low).<br><br>**Phase 2:** Automate prioritization by SLA.<br><br>**Phase 3:** Monitor SLA breaches monthly.<br><br>Customers experience faster resolutions for critical tickets. | - Aligns expectations and response with customer impact.<br><br>- Reduces dissatisfaction for high-impact users.<br><br>- Cuts escalations by making “what comes first” explicit.<br><br>- Improves fairness and transparency of service.<br><br>- Strengthens compliance reporting. | **Formula:** SLA Penalty Avoided = (# SLA Breaches Avoided × Avg Penalty Cost).<br><br>Dataset shows spikes where SLA is most at risk. | {sla_evidence} |
            | **Send proactive communication during peaks** | **Phase 1:** Identify peak periods from trend data.<br><br>**Phase 2:** Send pre-emptive communication (e.g., “We are experiencing high volume”).<br><br>**Phase 3:** Follow up post-resolution to rebuild trust.<br><br>This lowers customer frustration. | - Manages expectations and reduces complaint volume.<br><br>- Improves sentiment even when delays persist.<br><br>- Demonstrates ownership and accountability.<br><br>- Decreases repeat contacts and status chasing.<br><br>- Protects brand perception during incidents. | **Formula:** Escalation Cost Avoided = (# Escalations Prevented × Avg Escalation Cost).<br><br>Dataset: backlog correlates with surges → fewer escalations if managed proactively. | {peak_evidence} |
            | **Offer self-service resolution tools** | **Phase 1:** Deploy chatbots or guided troubleshooting tools.<br><br>**Phase 2:** Integrate with knowledge base.<br><br>**Phase 3:** Track usage and resolution rates.<br><br>This empowers customers to resolve issues independently. | - Shorter time-to-relief without queueing for agents.<br><br>- Reduces new ticket creation for known issues.<br><br>- 24/7 availability improves perceived reliability.<br><br>- Standardizes fixes to reduce reopen rates.<br><br>- Scales support at low marginal cost. | **Formula:** Cost Avoidance = (# Self-Resolved Tickets × Avg Resolution Cost).<br><br>Dataset categories show repetitive low-level tickets suitable for automation. | {dept_evidence} |
            | **Department-specific customer engagement** | **Phase 1:** Identify departments with high customer dissatisfaction from survey trends.<br><br>**Phase 2:** Conduct focus sessions to gather feedback.<br><br>**Phase 3:** Implement department-tailored improvements.<br><br>Aligns service quality with customer expectations. | - Targets pain points where sentiment is weakest.<br><br>- Converts feedback into concrete service changes.<br><br>- Raises satisfaction in the highest-volume areas first.<br><br>- Increases retention of key internal customers.<br><br>- Creates a repeatable governance loop. | **Formula:** CSAT Uplift = (Improved CSAT% × Tickets for Department).<br><br>Dataset shows variation in satisfaction across departments. | {dept_evidence} |
            | **Recognize high-performing departments publicly** | **Phase 1:** Identify departments with top satisfaction and SLA compliance.<br><br>**Phase 2:** Publicize their performance internally.<br><br>**Phase 3:** Replicate their methods in lower-performing teams.<br><br>Recognition boosts morale. | - Reinforces behaviors that drive high CSAT and SLA.<br><br>- Encourages knowledge sharing and mentorship.<br><br>- Improves culture and motivation across teams.<br><br>- Creates positive competition tied to outcomes.<br><br>- Helps retain high performers. | **Formula:** Productivity Gain = (Improvement in Low Depts × Ticket Volume).<br><br>Dataset: {dept_top['department']} shows volume leadership; recognition builds positive culture. | {dept_evidence} |
            """
        }

            render_cio_tables("Number of Tickets Opened", cio_1a)



    # ---------------------- 1b ----------------------
    with st.expander("📌 Number of Tickets Closed"):
        if "resolved_time" in df_filtered.columns:
            # Convert and group data
            df_filtered["resolved_date"] = pd.to_datetime(df_filtered["resolved_time"], errors="coerce").dt.date
            closed = df_filtered.groupby("resolved_date").size().reset_index(name="ticket_closed")

            # Create bar chart for closures over time
            fig = px.bar(
                closed,
                x="resolved_date",
                y="ticket_closed",
                title="Tickets Closed Over Time",
                labels={"resolved_date": "Resolved Date", "ticket_closed": "Number of Tickets Closed"},
            )
            st.plotly_chart(fig, use_container_width=True)

            # ✅ NEW: compute metrics safely BEFORE using them
            if not closed.empty:
                total_tickets = int(closed["ticket_closed"].sum())
                avg_tickets = float(closed["ticket_closed"].mean())
                max_idx = closed["ticket_closed"].idxmax()
                min_idx = closed["ticket_closed"].idxmin()
                max_day = closed.loc[max_idx]
                min_day = closed.loc[min_idx]

                trend_desc = ""
                if closed["ticket_closed"].iloc[-1] > closed["ticket_closed"].iloc[0]:
                    trend_desc = "an upward trend overall"
                elif closed["ticket_closed"].iloc[-1] < closed["ticket_closed"].iloc[0]:
                    trend_desc = "a downward trend overall"
                else:
                    trend_desc = "a relatively stable trend over the observed period"

                # (Optional: if you ever need formatted strings directly)
                # max_day_fmt = pd.to_datetime(max_day["resolved_date"]).strftime("%d/%m/%Y")
                # min_day_fmt = pd.to_datetime(min_day["resolved_date"]).strftime("%d/%m/%Y")

                st.markdown("### Analysis of Ticket Closed Over Time")
                st.write(f"""
                        **What this graph is:** A throughput chart showing how many tickets were **completed/closed each day**.  
                        - **X-axis:** Calendar date (DD/MM/YYYY).  
                        - **Y-axis:** Count of tickets that moved to a closed state on that date.

                        **What it shows in your data:**  
                        The bar chart illustrates the **daily number of tickets closed** over time, where the x-axis represents dates 
                        (in Malaysian date format, DD/MM/YYYY) and the y-axis shows the count of closed tickets.

                        Across the period, a total of **{total_tickets:,} tickets** were closed, with a daily average of approximately 
                        **{avg_tickets:.1f} tickets**. The highest closure activity occurred on **{max_day['resolved_date'].strftime('%d/%m/%Y')}**, 
                        with **{max_day['ticket_closed']} tickets closed**, while the lowest was on **{min_day['resolved_date'].strftime('%d/%m/%Y')}**, 
                        with only **{min_day['ticket_closed']} tickets closed**.

                        Overall, the closure rate indicates {trend_desc}. Peaks such as on **{max_day['resolved_date'].strftime('%d/%m/%Y')}** 
                        may reflect focused resolution efforts, deadlines, or backlog clearance, whereas dips such as 
                        **{min_day['resolved_date'].strftime('%d/%m/%Y')}** could suggest weekends, holidays, or resourcing gaps.

                        **How to read it operationally:**  
                        1) **Stability vs. volatility:** Widely varying bar heights = volatile throughput, which raises SLA risk after intake spikes.  
                        2) **Bottleneck detection:** Runs of low bars after high intake days point to **clearance delays** (capacity, dependencies, or prioritization).  
                        3) **Momentum:** Compare the first and last week’s average bar heights to sense improving or degrading throughput (more tall bars late = improving).  
                        4) **Fairness & staff load:** Use the second chart (per-technician closure rate) to spot **over-concentration** on a few people, which can mask systemic issues.

                        **Why this matters:** The gap between **“tickets opened” (inflow)** and **“tickets closed” (outflow)** is what creates backlog. Sustained days where closed < opened will **push backlog up**; sustained days where closed > opened will **burn it down**. This chart is therefore your fastest visual monitor of whether the service desk is **keeping pace**.
                        """)
            else:
                st.info("No valid 'resolved_time' values after parsing; cannot compute closures or analysis.")

            # --- 2nd graph: Closure rate per technician ---
            if "technician" in df_filtered.columns:
                tech_closed = df_filtered.groupby("technician").size().reset_index(name="tickets_closed")
                tech_closed["closure_rate"] = tech_closed["tickets_closed"] / tech_closed["tickets_closed"].sum() * 100

                fig2 = px.bar(
                    tech_closed.sort_values("tickets_closed", ascending=False),
                    x="technician",
                    y="tickets_closed",
                    title="Tickets Closed per Technician",
                    labels={"technician": "Technician", "tickets_closed": "Number of Tickets Closed"},
                    text="closure_rate"
                )
                fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)

            # Dynamic analysis generation
            if not closed.empty:
                total_tickets = closed["ticket_closed"].sum()
                avg_tickets = closed["ticket_closed"].mean()
                max_day = closed.loc[closed["ticket_closed"].idxmax()]
                min_day = closed.loc[closed["ticket_closed"].idxmin()]

                trend_desc = ""
                if closed["ticket_closed"].iloc[-1] > closed["ticket_closed"].iloc[0]:
                    trend_desc = "an upward trend overall"
                elif closed["ticket_closed"].iloc[-1] < closed["ticket_closed"].iloc[0]:
                    trend_desc = "a downward trend overall"
                else:
                    trend_desc = "a relatively stable trend over the observed period"

                st.markdown("### Analysis of Tickets Closed per Technician")
                st.write(f"""
                **What this graph is:** A throughput allocation chart showing how many tickets were **closed by each technician**.  
                - **X-axis:** Technician name.  
                - **Y-axis:** Count of tickets each technician closed (with percentage labels indicating share of total closures).

                **What it shows in your data:**  
                The bar chart illustrates the **distribution of closed tickets across {tech_closed.shape[0]} technicians**. Across the period, the team closed a total of **{int(tech_closed['tickets_closed'].sum()) if tech_closed.shape[0] else 0:,} tickets**, with an average of approximately **{(tech_closed['tickets_closed'].mean() if tech_closed.shape[0] else 0):.1f} tickets per technician**.  
                The highest individual throughput was by **{(tech_closed.sort_values('tickets_closed', ascending=False).iloc[0]['technician'] if tech_closed.shape[0] and int(tech_closed['tickets_closed'].sum())>0 else '—')}**, closing **{(int(tech_closed.sort_values('tickets_closed', ascending=False).iloc[0]['tickets_closed']) if tech_closed.shape[0] and int(tech_closed['tickets_closed'].sum())>0 else 0)} tickets** (≈**{(((int(tech_closed.sort_values('tickets_closed', ascending=False).iloc[0]['tickets_closed']))/(int(tech_closed['tickets_closed'].sum()))) * 100) if (tech_closed.shape[0] and int(tech_closed['tickets_closed'].sum())>0) else 0:.1f}%** of all closures), while the lowest was by **{(tech_closed.sort_values('tickets_closed', ascending=False).iloc[-1]['technician'] if tech_closed.shape[0] and int(tech_closed['tickets_closed'].sum())>0 else '—')}**, with **{(int(tech_closed.sort_values('tickets_closed', ascending=False).iloc[-1]['tickets_closed']) if tech_closed.shape[0] and int(tech_closed['tickets_closed'].sum())>0 else 0)} tickets**.

                Overall, the allocation indicates **{trend_desc}**. A standout like the top closer may reflect specialization, higher assignment volume, or stronger resolution efficiency, whereas lower bars may signal onboarding, part-time allocation, or mismatched task routing.

                **How to read it operationally:**  
                1) **Stability vs. volatility:** Large height gaps between bars = uneven throughput, which can mask process issues and concentrate risk.  
                2) **Bottleneck detection:** If most closures cluster under a few names, investigate routing rules, queue ownership, and skill coverage.  
                3) **Momentum:** Re-plot this weekly to observe whether lower-throughput technicians are catching up after coaching or assignment tuning.  
                4) **Fairness & staff load:** Persistent over-concentration can inflate burnout risk and SLA exposure when top closers are unavailable.

                **Why this matters:** Service reliability depends on **capacity that’s both sufficient and distributed**. A team where closures are balanced will be more resilient to absences, surge days, and complex inflow patterns; persistent imbalance suggests **training needs, routing adjustments, or workload redistribution** to protect SLA performance.
                """)

        # Calculate supporting metrics from dataset
        total_tickets = closed["ticket_closed"].sum()
        avg_tickets = closed["ticket_closed"].mean()
        max_day = closed.loc[closed["ticket_closed"].idxmax()]

        cio_1b = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|-------------|----------|------------------|---------------------------------|
| Streamline ticket closure workflows | **Phase 1 – Map & Diagnose:** Inventory current closure steps, handoffs, and policy variances; flag duplicate approvals and low-value checks. <br><br> **Phase 2 – Standardize & Simplify:** Define a single “definition of done”, remove redundant steps, introduce templates/macros/checklists to reduce clicks and rework. <br><br> **Phase 3 – Automate & Govern:** Enforce validations at closure, auto-populate fields, and track compliance via daily exceptions to lock in the time savings. | - Lowers operational overhead.<br><br>- Creates more predictable workload distribution across the service desk.<br><br>- Reduces overtime.<br><br>- Improves workforce allocation. | Savings = (Average minutes saved per ticket × Tickets closed). <br><br> For example, if 5 minutes are saved per ticket and {total_tickets:,} tickets were closed, the savings equal (5 × {total_tickets:,}) minutes, or {round((total_tickets * 5) / 60, 2)} staff hours. | The bar chart shows large spikes on peak days such as **{max_day['resolved_date'].strftime('%d/%m/%Y')}**, indicating batch closure efforts. Standardizing workflows would smooth out these fluctuations. |
| Automate ticket triage and routing | **Phase 1 – Evidence Review:** Analyse historical labels, queues, and SLA breaches to find misroutes and slow paths. <br><br> **Phase 2 – Rules & Taxonomy:** Create routing rules (or ML model) using category, priority, skills, and availability; codify edge cases. <br><br> **Phase 3 – Deploy & Tune:** Auto-assign and priority-stamp new tickets; review weekly drift and refine rules to keep queues balanced. | - Delivers significant time savings per ticket.<br><br>- Lowers cost per resolution.<br><br>- Reduces escalations that require expensive resources. | Cost reduction = (Reduced handling time per ticket × Number of tickets). Using daily averages, {avg_tickets:.1f} tickets closed × 3 minutes saved = {round(avg_tickets*3,1)} minutes saved daily. | The chart indicates delays where closures lag behind openings. Automating triage would prevent prolonged queues visible in these dips. |
| Introduce targeted backlog clearance sprints | **Phase 1 – Size & Segment:** Quantify aged backlog by priority, customer, and SLA risk; identify “quick win” cohorts. <br><br> **Phase 2 – Plan the Sprint:** Reserve off-peak windows, assign focused squads, and set burn-down targets with clear exit criteria. <br><br> **Phase 3 – Execute & Sustain:** Run daily stand-ups, track burn-down vs. plan, and feed learnings into routing and standards to prevent re-accumulation. | - Prevents long-term cost escalation linked to aging tickets.<br><br>- Improves resource planning.<br><br>- Converts idle backlog time into productive closure gains. | Cost avoidance = (Escalation cost per ticket × Number of tickets exceeding SLA). Dataset trends show backlogs after spikes like **{max_day['resolved_date'].strftime('%d/%m/%Y')}**, implying at least (tickets opened – tickets closed) tickets at risk. | Graph evidence shows dips following peak days where closures did not match the opening rate, confirming the need for structured backlog clearance. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|-------------|----------|------------------|---------------------------------|
| Implement real-time closure monitoring | **Phase 1 – Define KPIs:** Lock metrics for throughput, lead time, SLA at risk, and WIP limits. <br><br> **Phase 2 – Instrument & Visualise:** Build a live dashboard with hour/day granularity and threshold-based alerts. <br><br> **Phase 3 – Act & Review:** Establish a daily/weekly cadence to act on alerts and publish trend deltas to drive accountability. | - Increases accountability.<br><br>- Enables quicker corrective action.<br><br>- Reduces delays in ticket processing. | Efficiency gain = (Tickets closed on time ÷ Total tickets closed). From the dataset, {total_tickets:,} tickets were closed; by improving on-time closure rates, measurable efficiency gains can be tracked. | The graph shows noticeable lags after peak closure days, confirming that reactive monitoring is insufficient and real-time visibility is needed. |
| Conduct root cause analysis of closure delays | **Phase 1 – Identify Cohorts:** Isolate delayed tickets by category, assignee, and dependency. <br><br> **Phase 2 – Diagnose:** Apply 5 Whys/Pareto to pinpoint policy gaps, tooling blockers, or knowledge gaps. <br><br> **Phase 3 – Fix & Validate:** Implement targeted fixes (KB updates, workflow edits, SLA rules) and confirm via before/after cycle-time reduction. | - Eliminates recurring inefficiencies.<br><br>- Reduces staff burnout.<br><br>- Creates a more predictable closure cycle. | Savings = (Delay days reduced × Avg. daily cost per ticket). Reducing closure lag by 1 day across delayed tickets directly lowers SLA breach costs visible in the dataset. | Evidence from the chart shows tickets closed trailing significantly after spikes in openings, highlighting structural delay causes that require deeper analysis. |
| Cross-train agents on high-demand issue categories | **Phase 1 – Skill Matrix:** Map demand vs. skills to find thin coverage areas. <br><br> **Phase 2 – Train & Shadow:** Run short targeted modules and shadowing on peak categories with hands-on playbooks. <br><br> **Phase 3 – Rotate & Certify:** Implement rotation, certify competency, and refresh quarterly to keep coverage resilient. | - Speeds responses on high-demand categories.<br><br>- Reduces backlog accumulation.<br><br>- Improves workforce flexibility. | Efficiency gain = (Tickets resolved without delay × Avg. resolution cost). With {avg_tickets:.0f} tickets processed on average per day, reducing reliance on specialists converts backlog hours into productive time. | The closure chart shows imbalances in daily activity, supporting the need for broader skill distribution among staff. |
| Balance technician workloads based on closure rate | **Phase 1 – Baseline:** Quantify closure share per technician and set guardrails (min/max share, WIP caps). <br><br> **Phase 2 – Rebalance:** Adjust routing rules, queues, and schedules to equalise load without breaking expertise lanes. <br><br> **Phase 3 – Monitor Drift:** Track weekly variance and auto-correct via dynamic assignment when thresholds are breached. | - Improves fairness across the team.<br><br>- Reduces attrition risk.<br><br>- Strengthens team resilience. | Productivity gain = (Tickets redistributed ÷ Avg closure time per ticket). Dataset shows certain technicians closing disproportionately high ticket volumes, indicating clear rebalancing potential. | The technician graph highlights disparities in closure rates, confirming the need for workload balancing strategies. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|-------------|----------|------------------|---------------------------------|
| Enhance proactive customer updates | **Phase 1 – Map Journeys:** Identify silence gaps from intake to closure by priority and SLA. <br><br> **Phase 2 – Automate Notices:** Trigger status updates at SLA milestones with plain-language templates and next-step clarity. <br><br> **Phase 3 – Measure Impact:** Track deflection rate and post-resolution CSAT/NPS to fine-tune cadence and content. | - Builds customer trust.<br><br>- Reduces inbound complaint volume.<br><br>- Helps customers feel valued even when resolution is slower. | Improved NPS = (Post-resolution satisfaction survey increase). With {total_tickets:,} tickets closed, linking satisfaction scores to closure rates provides measurable improvements. | The chart’s backlog dips correlate with dissatisfaction risk, confirming the need for proactive updates during low-closure periods. |
| Prioritize and fast-track critical tickets | **Phase 1 – Define Criticality:** Create a simple matrix for impact × urgency with explicit routing/SLA rules. <br><br> **Phase 2 – Build Fast Lane:** Separate queue, senior ownership, and escalation timers for P1/P2; pre-approve required actions. <br><br> **Phase 3 – Audit & Improve:** Review critical-path breaches weekly and harden controls where slippage occurs. | - Delivers faster service for urgent issues.<br><br>- Reduces churn risk.<br><br>- Lowers escalation costs. | Cost avoidance = (Escalations prevented × Avg. escalation cost). Evidence of backlog on {max_day['resolved_date'].strftime('%d/%m/%Y')} shows critical tickets were likely delayed, making prioritization vital. | Evidence in the dataset shows slow closures after high-volume spikes, suggesting critical issues risk being trapped in general queues. |
| Conduct post-resolution feedback analysis | **Phase 1 – Instrument:** Deploy short, context-aware surveys tied to category and resolution time. <br><br> **Phase 2 – Analyse:** Mine comments for themes and sentiment; link to agent/process signals. <br><br> **Phase 3 – Close the Loop:** Publish fixes, update playbooks, and verify uplift in subsequent cohorts. | - Improves service quality via customer voice integration.<br><br>- Lifts satisfaction scores.<br><br>- Directs investment toward the highest-impact fixes. | Cost justification = (Improved retention rate × Customer lifetime value). Linking survey results to periods of low closure volume highlights the cost of dissatisfaction. | Chart variability shows inconsistent resolution volumes, suggesting equally inconsistent satisfaction levels, reinforcing the need for feedback mechanisms. |
| Recognize and incentivize top-performing technicians | **Phase 1 – Define Fair Metrics:** Blend throughput with quality (reopen rate/CSAT) to avoid perverse incentives. <br><br> **Phase 2 – Design Program:** Offer tiered recognition (spot awards, peer kudos, growth paths) tied to transparent criteria. <br><br> **Phase 3 – Communicate & Iterate:** Share wins, rotate spotlights, and recalibrate quarterly to maintain credibility. | - Strengthens employee engagement.<br><br>- Improves service quality.<br><br>- Increases customer satisfaction through motivated teams. | ROI = (Improved productivity ÷ Incentive cost). Data shows clear outperformance by certain technicians, making targeted recognition impactful. | The technician graph demonstrates standout performers, supporting a structured recognition program tied to satisfaction outcomes. |
"""
}


        render_cio_tables("Number of Tickets Closed", cio_1b)



    # ---------------------- 1c ----------------------
    with st.expander("📌 Tickets Currently Open"):
        if "request_status" in df_filtered.columns:
            open_tickets = df_filtered[df_filtered["request_status"].str.lower() == "open"]

            if not open_tickets.empty:
                count = open_tickets.groupby("Priority").size().reset_index(name="open_tickets")
                fig = px.bar(
                    count,
                    x="Priority",
                    y="open_tickets",
                    title="Open Tickets by Priority",
                    labels={"Priority": "Ticket Priority", "open_tickets": "Number of Open Tickets"}
                )
                st.plotly_chart(fig, use_container_width=True)

                # --- Dynamic analysis for Open Tickets ---
                max_open = count.loc[count["open_tickets"].idxmax()]
                min_open = count.loc[count["open_tickets"].idxmin()]
                st.markdown("### Analysis of Open Tickets")
                st.write(f"""
                **What this graph is:** A throughput allocation chart showing how many tickets are **currently open by priority**.  
                - **X-axis:** Ticket priority.  
                - **Y-axis:** Count of open tickets at this moment.

                **What it shows in your data:**  
                The highest open load is **{max_open['Priority']}** with **{max_open['open_tickets']} tickets**, while the lowest is **{min_open['Priority']}** with **{min_open['open_tickets']} tickets**.

                Overall, the open-queue mix suggests where **risk and attention** should be directed first—higher priority buckets with larger bars carry the greatest SLA and customer impact.

                **How to read it operationally:**  
                1) **Triage:** Pull highest-priority items first and verify ownership/next action.  
                2) **Aging:** Pair with age buckets to surface near-breach items.  
                3) **Resourcing:** Shift experienced analysts toward the heaviest high-priority segment.  
                4) **Prevention:** Map repetitive items in large buckets to knowledge base or automation.

                **Why this matters:** The **shape of the open queue** is tomorrow’s SLA performance. Tight control here reduces breach probability, escalations, and customer dissatisfaction.
                """)

                tickets_open_analysis_available = True
            else:
                st.info("✅ Currently, there are no open tickets in the dataset.")
                st.markdown("### Analysis of Open Tickets")
                st.write("Graph not available because there are no tickets with 'Open' status in the dataset.")
                tickets_open_analysis_available = False
        else:
            st.warning("⚠️ Column 'request_status' not found in dataset.")
            tickets_open_analysis_available = False


        # --- New Graph: Closure vs Opening Rate ---
        # --- Closure vs Opening Rate Graph ---
        if {"request_status", "created_time"} <= set(df_filtered.columns):
            df_rate = df_filtered.copy()

            # Parse created_time
            df_rate["created_time"] = pd.to_datetime(df_rate["created_time"], errors="coerce")

            # ✅ Pick resolved_time if available, else fall back to completed_time
            closure_column = None
            if "resolved_time" in df_rate.columns:
                closure_column = "resolved_time"
            elif "completed_time" in df_rate.columns:
                closure_column = "completed_time"

            if closure_column:
                df_rate[closure_column] = pd.to_datetime(df_rate[closure_column], errors="coerce")

                # Opened = count by created_time
                opened = (
                    df_rate.groupby(df_rate["created_time"].dt.date)
                    .size()
                    .reset_index(name="opened")
                    .rename(columns={"created_time": "date"})
                )

                # Closed = count by resolved_time/completed_time
                closed = (
                    df_rate.dropna(subset=[closure_column])
                    .groupby(df_rate[closure_column].dt.date)
                    .size()
                    .reset_index(name="closed")
                    .rename(columns={closure_column: "date"})
                )

                # ✅ Merge on the single unified "date"
                rate = pd.merge(opened, closed, on="date", how="outer") \
                        .fillna(0).sort_values("date")

                # Plot
                fig2 = px.line(
                    data_frame=rate,
                    x="date",
                    y=["opened", "closed"],
                    title="Closure vs Opening Rate Over Time",
                    labels={
                        "value": "Number of Tickets",
                        "date": "Date",
                        "variable": "Metric"
                    }
                )
                st.plotly_chart(fig2, use_container_width=True)

                # Mark availability
                closure_vs_opening_available = True

                # --- Dynamic Analysis ---
                max_open = rate.loc[rate["opened"].idxmax()]
                max_closed = rate.loc[rate["closed"].idxmax()]

                st.markdown("### Analysis of Closure vs Opening Rate")
                st.write(f"""
                **What this graph is:** A dual throughput chart comparing **opened** (inflow) and **closed** (outflow) tickets per day.  
                - **X-axis:** Calendar date.  
                - **Y-axis:** Counts for each daily metric (opened, closed).

                **What it shows in your data:**  
                Largest intake day: **{max_open['date']}** with **{int(max_open['opened'])} opened**.  
                Largest closure day: **{max_closed['date']}** with **{int(max_closed['closed'])} closed**.  
                Averages over the period are **{rate['opened'].mean():.1f} opened/day** vs **{rate['closed'].mean():.1f} closed/day**.

                Overall, when the closed line persistently tracks **below** the opened line, the process is under-capacity and backlog grows; when it meets or exceeds openings, backlog burns down and stability improves.

                **How to read it operationally:**  
                1) **Gap = backlog delta:** The vertical distance between lines is the daily backlog change.  
                2) **Lead–lag:** Closures peaking after openings implies reactive sprints, not smooth flow.  
                3) **Recovery strength:** Faster crossover after spikes = healthier system.  
                4) **Control:** Target near-parallel lines with minimal gap via routing, WIP limits, and surge capacity.

                **Why this matters:** Balance between inflow and outflow is the **heartbeat** of the desk. Keeping outflow at or above inflow prevents aging, protects SLA, and steadies customer experience.
                """)


            else:
                st.warning("⚠️ No closure-related column ('resolved_time' or 'completed_time') found in dataset.")
                closure_vs_opening_available = False

        else:
            st.warning("⚠️ Required columns ('request_status', 'created_time') not found for closure vs opening analysis.")
            closure_vs_opening_available = False

        # --- CIO Recommendations (uses real values from the graphs) ---
        # Precompute real metrics for f-strings (safe guards included)
        try:
            # From "Open Tickets by Priority"
            total_open_now = int(count["open_tickets"].sum()) if tickets_open_analysis_available else 0
            top_priority_row = count.sort_values("open_tickets", ascending=False).iloc[0] if tickets_open_analysis_available and not count.empty else None
            low_priority_row = count.sort_values("open_tickets", ascending=True).iloc[0] if tickets_open_analysis_available and not count.empty else None
            top_priority_name = str(top_priority_row["Priority"]) if top_priority_row is not None else "—"
            top_priority_open = int(top_priority_row["open_tickets"]) if top_priority_row is not None else 0
            low_priority_name = str(low_priority_row["Priority"]) if low_priority_row is not None else "—"
            low_priority_open = int(low_priority_row["open_tickets"]) if low_priority_row is not None else 0
        except Exception:
            total_open_now = 0
            top_priority_name, top_priority_open = "—", 0
            low_priority_name, low_priority_open = "—", 0

        try:
            # From "Closure vs Opening Rate"
            opened_total = int(rate["opened"].sum()) if closure_vs_opening_available else 0
            closed_total = int(rate["closed"].sum()) if closure_vs_opening_available else 0
            opened_avg = float(rate["opened"].mean()) if closure_vs_opening_available else 0.0
            closed_avg = float(rate["closed"].mean()) if closure_vs_opening_available else 0.0
            backlog_delta_total = int(opened_total - closed_total) if closure_vs_opening_available else 0

            # Peak days (already computed above in your code)
            peak_open_date = pd.to_datetime(max_open["date"]).strftime("%d/%m/%Y") if closure_vs_opening_available else "—"
            peak_open_val = int(max_open["opened"]) if closure_vs_opening_available else 0
            peak_closed_date = pd.to_datetime(max_closed["date"]).strftime("%d/%m/%Y") if closure_vs_opening_available else "—"
            peak_closed_val = int(max_closed["closed"]) if closure_vs_opening_available else 0

            # What closed on the peak-open day?
            try:
                closed_on_peak_open = int(rate.loc[rate["date"] == max_open["date"], "closed"].fillna(0).astype(int).values[0])
            except Exception:
                closed_on_peak_open = 0
        except Exception:
            opened_total = closed_total = 0
            opened_avg = closed_avg = 0.0
            backlog_delta_total = 0
            peak_open_date = peak_closed_date = "—"
            peak_open_val = peak_closed_val = 0
            closed_on_peak_open = 0

        cio_recs = {"cost": "", "performance": "", "satisfaction": ""}

        if tickets_open_analysis_available and closure_vs_opening_available:
            cio_recs["cost"] = f"""
            | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |---|---|---|---|---|
            | Rationalize low-impact open tickets via auto-closure with customer nudge | **Phase 1 – Define Thresholds:** Set inactivity windows and reminder cadence; exclude VIP/critical.<br><br>**Phase 2 – Automate Notices:** Send reminder + self-reopen link; log acknowledgements.<br><br>**Phase 3 – Enforce & Tune:** Auto-close after final nudge; monitor reopen rate and refine thresholds. | - Reduces administrative touches on stale tickets.<br><br>- Shrinks queue size to focus analysts on high-impact work.<br><br>- Cuts overtime during peaks by removing “dead work”.<br><br>- Stabilizes WIP, reducing SLA breach exposure. | **Hours saved (monthly)** = (# auto-closed × admin mins ÷ 60).<br><br>Example: if **10%** of current open (**{total_open_now}**) are stale → **{int(0.10*total_open_now)}** tickets × 4 mins ≈ **{(0.10*total_open_now*4)/60:.1f} hrs** saved. | **Open by Priority** shows **{top_priority_name} = {top_priority_open}** open vs **{low_priority_name} = {low_priority_open}**; long-aging low-priority items are prime auto-close candidates. |
            | Automate Tier-0/Tier-1 fixes for top repetitive categories | **Phase 1 – Identify Candidates:** Rank frequent simple categories; collect required fields/screenshots.<br><br>**Phase 2 – Build Flows/Bots:** Guided steps with validations and KB links; enable attachments.<br><br>**Phase 3 – Launch & Iterate:** Track deflection %, expand to next categories. | - Avoids human handling on simple cases (time and cost).<br><br>- Faster time-to-relief improves user experience.<br><br>- Frees skilled analysts for complex work.<br><br>- Reduces reopen due to standardized fixes. | **Time avoided (daily)** = (tickets automated × avg handling mins).<br><br>Using inflow avg **{opened_avg:.1f}**/day: if **25%** are Tier-0 → **{0.25*opened_avg:.1f}** × 6 mins ≈ **{(0.25*opened_avg*6)/60:.1f} hrs/day**. | **Closure vs Opening** shows avg opened **{opened_avg:.1f}** vs closed **{closed_avg:.1f}**; automation narrows this gap on surge days like **{peak_open_date} ({peak_open_val} opened, {closed_on_peak_open} closed)**. |
            | Shift and staff to the observed priority mix | **Phase 1 – Baseline Demand:** Measure open counts by priority across dayparts to find persistent hotspots.<br><br>**Phase 2 – Align Rosters:** Stagger shifts/skills to cover high-priority windows; add overlap buffers.<br><br>**Phase 3 – Review & Tune:** Weekly breach-risk review by priority; adjust staffing and on-call rules. | - Targets coverage to where risk is highest.<br><br>- Reduces overtime and escalations by matching capacity to load.<br><br>- Improves predictability and SLA compliance.<br><br>- Increases utilisation of standard hours. | **Overtime savings** = (overtime hrs avoided × hourly rate).<br><br>Backlog delta over period = **{backlog_delta_total}** (opened−closed). Staffing to lift close rate by **+{max(1, int(0.1*closed_avg))}**/day could erase this in **≈{(backlog_delta_total/max(1,int(0.1*closed_avg))):,}** days. | **Open by Priority** concentration: **{top_priority_name} = {top_priority_open}** open now; **Closure vs Opening** avg opened **{opened_avg:.1f}** vs closed **{closed_avg:.1f}** indicates capacity shortfall. |
            | Targeted backlog clearance sprint | **Phase 1 – Size & Segment:** Quantify aged backlog and segment by priority/SLA risk.<br><br>**Phase 2 – Sprint Plan:** Off-peak sessions with defined burn-down targets.<br><br>**Phase 3 – Lock-in Gains:** Feed learnings into routing/automation to prevent re-accumulation. | - Rapidly reduces SLA exposure from aging tickets.<br><br>- Recovers customer trust via visible progress.<br><br>- Lowers carrying cost of old tickets.<br><br>- Creates data to improve upstream flow. | **Burn-down effort** = (tickets to clear × mins per ticket ÷ 60).<br><br>If clearing **50%** of current open (**{total_open_now}**) at 8 mins each → **{int(0.5*total_open_now)}** × 8 / 60 ≈ **{(0.5*total_open_now*8)/60:.1f} hrs**. | Evidence of under-capacity: peak open day **{peak_open_date}** had **{peak_open_val} opened** but only **{closed_on_peak_open} closed**, contributing to **{backlog_delta_total}** net backlog. |
            """

            cio_recs["performance"] = f"""
            | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |---|---|---|---|---|
            | WIP limits by priority | **Phase 1 – Set Guardrails:** Define max in-progress per analyst per priority.<br><br>**Phase 2 – Enforce in Tooling:** Block starts beyond limits; overflow queues are visible.<br><br>**Phase 3 – Inspect & Adapt:** Track cycle time/throughput and adjust limits quarterly. | - Cuts multitasking and context switching.<br><br>- Shortens cycle time and increases daily closures.<br><br>- Stabilises throughput during spikes.<br><br>- Reduces SLA breaches from over-commitment. | **Throughput lift (daily)** = Δclosed/day × avg hrs/ticket.<br><br>If limits lift close rate from **{closed_avg:.1f}** to **{closed_avg+1:.1f}**/day with 1.2 hrs/ticket → **≈1.2 hrs/day** capacity recovered. | **Closure vs Opening** averages: opened **{opened_avg:.1f}** vs closed **{closed_avg:.1f}**; persistent gap indicates over-WIP and flow instability. |
            | Aging guardrails with auto-escalation | **Phase 1 – Age Buckets:** Set 0–1d, 2–3d, 4–7d, >7d thresholds per priority.<br><br>**Phase 2 – Triggers:** Auto-escalate or swarm when a ticket crosses a bucket; notify owners.<br><br>**Phase 3 – Prevent Recurrence:** Capture reasons, fix blockers, and tighten rules. | - Prevents silent aging and SLA breaches.<br><br>- Concentrates expertise on near-breach items.<br><br>- Increases first-time-right by timely intervention.<br><br>- Improves on-time closure rate. | **Breach hours prevented** = (# escalated before breach × avg overage hrs).<br><br>Using backlog delta **{backlog_delta_total}**, even preventing **20%** from breaching at 2 hrs overage saves **{int(0.2*backlog_delta_total)*2} hrs**. | Peak intake **{peak_open_date}: {peak_open_val} opened** vs **{closed_on_peak_open} closed** shows aging risk after surges. |
            | Fast-lane for critical symptoms | **Phase 1 – Define Symptoms:** P1/P2 keywords and impact signals for fast routing.<br><br>**Phase 2 – Dedicated Lane:** Senior ownership, pre-approved actions, tighter SLAs.<br><br>**Phase 3 – Audit Outcomes:** Weekly performance review and triage refinement. | - Shorter time-to-restore on high-impact cases.<br><br>- Protects SLA and customer trust during crises.<br><br>- Reduces escalations and incident blast radius.<br><br>- Improves service resilience. | **Impact hours saved** = (Δresolution hrs × # fast-lane tickets).<br><br>If **{top_priority_open}** open in **{top_priority_name}** get 0.5 hr faster resolution → **{0.5*top_priority_open:.1f} hrs** saved. | **Open by Priority** concentration in **{top_priority_name} ({top_priority_open})** validates need for a protected lane. |
            | Surge playbook & swarming | **Phase 1 – Playbook:** Predefine triggers, roles, and checklists.<br><br>**Phase 2 – Swarm Activation:** Cross-functional huddles at trigger; cap parallel work; unblock dependencies fast.<br><br>**Phase 3 – Recovery Audit:** Measure time-to-recover and update playbook. | - Faster recovery after spikes.<br><br>- Reduces backlog growth on high intake days.<br><br>- Improves cross-team coordination and learning.<br><br>- Stabilizes post-incident operations. | **Recovery gain** = (baseline recovery time − actual) × incidents.<br><br>On **{peak_open_date}**, opened **{peak_open_val}**; if swarming raises same-day closures from **{closed_on_peak_open}** to **{closed_on_peak_open+5}**, **+5** tickets/day capacity gained. | **Closure vs Opening** shows surges (e.g., **{peak_open_date}**) where openings outpace closures. |
            """

            cio_recs["satisfaction"] = f"""
            | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |---|---|---|---|---|
            | Priority-aware proactive updates | **Phase 1 – Map Cadence:** Define update intervals by priority and SLA stage.<br><br>**Phase 2 – Automate Messaging:** Include status, ETA, owner, next action; capture replies in-ticket.<br><br>**Phase 3 – Measure & Refine:** Track complaint deflection and CSAT uplift. | - Fewer “chase” contacts and repeat calls.<br><br>- Higher perceived responsiveness during spikes.<br><br>- Lower escalation probability for critical users.<br><br>- Builds trust through predictable comms. | **Contact deflection (daily)** = (repeat contacts avoided × mins ÷ 60).<br><br>If updates cut repeats by **20%** of inflow (**{opened_avg:.1f}**/day) at 6 mins each → **{(0.2*opened_avg*6)/60:.1f} hrs/day** saved. | On **{peak_open_date}**, **{peak_open_val} opened** vs **{closed_on_peak_open} closed**—transparent updates mitigate anxiety during such gaps. |
            | Self-service progress tracker | **Phase 1 – Expose Stages:** Show triage/diagnosis/fix/validation and ETA in portal.<br><br>**Phase 2 – Connect Signals:** Sync from ITSM fields and checklists; enable comments.<br><br>**Phase 3 – Observe & Improve:** Monitor views and call deflection; iterate UX/FAQs. | - Reduces “status check” calls and emails.<br><br>- Increases user confidence and satisfaction.<br><br>- Shortens resolution by clarifying next steps.<br><br>- Scales support without linearly adding headcount. | **Time saved (daily)** = (status calls avoided × avg duration).<br><br>With **{total_open_now}** open now, if **10%** would call (3 mins) → **{(0.10*total_open_now*3)/60:.1f} hrs/day** saved. | Elevated open queue (**{total_open_now}** tickets) makes visibility crucial to keep sentiment stable. |
            | VIP assurance route | **Phase 1 – Identify VIPs:** Maintain allowlist and tailored SLAs.<br><br>**Phase 2 – Notify & Own:** Auto-ping senior analysts on new VIP tickets; assign an owner.<br><br>**Phase 3 – Close the Loop:** Provide executive summaries and review breaches. | - Protects key relationships and executive trust.<br><br>- Cuts escalations and reputational risk.<br><br>- Improves outcomes for high-impact tickets.<br><br>- Signals priority handling during spikes. | **Escalation cost avoided** = (# VIP escalations avoided × cost/escalation).<br><br>If VIPs are **5%** of inflow (**{opened_avg:.1f}**/day) and avoiding 1 escalation/day saves MYR 300 → **MYR 300/day** avoided. | Surges like **{peak_open_date}** (opened **{peak_open_val}**, closed **{closed_on_peak_open}**) heighten VIP risk; a dedicated lane offsets this. |
            """

        elif closure_vs_opening_available:
            cio_recs["cost"] = f"""
            | Recommendations             | Explanation                                                                | Benefits                        | Cost Calculation                                          | Evidence & Graph Interpretation                            |
            | --------------------------- | -------------------------------------------------------------------------- | ------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------- |
            | Optimize staffing patterns  | **Phase 1 – Analyse Spikes:** Identify dayparts where opened ≫ closed.<br><br>**Phase 2 – Replan Shifts:** Align rosters and add overlap on peak inflow windows.<br><br>**Phase 3 – Monitor & Adjust:** Review weekly backlog delta and tune coverage. | - Reduces overtime and backlog growth.<br><br>- Matches capacity to demand for steadier throughput.<br><br>- Lowers SLA penalty exposure on surge days. | **Overtime savings** = (overtime hrs reduced × hourly rate).<br><br>Backlog delta = **{backlog_delta_total}** over the period; lifting close rate by **+1/day** reduces backlog duration by **{max(1, backlog_delta_total):,}** days. | **Closure vs Opening** avg opened **{opened_avg:.1f}** vs closed **{closed_avg:.1f}**; peak **{peak_open_date}** had **{peak_open_val} opened** but **{closed_on_peak_open} closed**. |
            | Automate repetitive tasks   | **Phase 1 – Select Candidates:** Pinpoint high-volume, low-complexity drivers.<br><br>**Phase 2 – Build Automations:** Templates, bots, or scripts for common steps.<br><br>**Phase 3 – Scale:** Measure deflection and expand. | - Lowers manual effort and handling time.<br><br>- Improves resilience during surges.<br><br>- Frees experts for complex incidents. | **Savings (daily)** = (# tickets automated × avg mins ÷ 60).<br><br>If **25%** of avg opened (**{opened_avg:.1f}**) at 6 mins → **{(0.25*opened_avg*6)/60:.1f} hrs/day** saved. | The persistent gap opened **{opened_avg:.1f}** vs closed **{closed_avg:.1f}** shows automation headroom. |
            | Defer low-impact work during surges | **Phase 1 – Classify Backlog:** Tag by business impact; defer low-impact when opened≫closed.<br><br>**Phase 2 – Schedule Off-Peak:** Move deferred cohorts to off-peak windows with clear SLAs.<br><br>**Phase 3 – Post-Mortem:** Review deferrals and refine criteria. | - Protects critical capacity and reduces overtime.<br><br>- Avoids SLA breaches on high-impact tickets.<br><br>- Smooths workload for the team. | **Overtime avoided** = (hours shifted off-peak × overtime rate).<br><br>On **{peak_open_date}** the gap was **{peak_open_val - closed_on_peak_open}** tickets; deferring **50%** low-impact avoids processing **{int(0.5*(peak_open_val - closed_on_peak_open))}** tickets at overtime. | Peak imbalance evident: **{peak_open_date}** opened **{peak_open_val}**, closed **{closed_on_peak_open}**. |
            """

            cio_recs["performance"] = f"""
            | Recommendations            | Explanation                                                                 | Benefits                   | Cost Calculation                                | Evidence & Graph Interpretation                         |
            | -------------------------- | --------------------------------------------------------------------------- | -------------------------- | ----------------------------------------------- | ------------------------------------------------------- |
            | Process balancing          | **Phase 1 – Establish Targets:** Set closed≥opened goals with daily caps.<br><br>**Phase 2 – Execute Controls:** Use WIP limits and surge capacity during spikes.<br><br>**Phase 3 – Review Variance:** Inspect misses and remove bottlenecks. | - Improves throughput and predictability.<br><br>- Reduces backlog volatility.<br><br>- Enhances SLA conformance. | **Efficiency** = (closed ÷ opened) × 100%.<br><br>Current avg: **{(closed_avg/max(0.1, opened_avg))*100:.1f}%**. Target ≥100% to burn backlog. | **Closure vs Opening** averages show shortfall: opened **{opened_avg:.1f}**, closed **{closed_avg:.1f}**. |
            | Prioritize ticket routing  | **Phase 1 – Define Rules:** Route critical/recurring issues to faster paths.<br><br>**Phase 2 – Implement:** Update assignment/queue logic.<br><br>**Phase 3 – Validate:** Track SLA hit rate and rework. | - Faster resolution for high-impact work.<br><br>- Fewer reassignments and handoff delays.<br><br>- Lower SLA breach count. | **Time saved (per day)** = (Δmins per ticket × critical volume ÷ 60).<br><br>If 10 critical/day save 12 mins → **2.0 hrs/day**. | Peak day **{peak_open_date}** indicates routing stress when **{peak_open_val}** tickets arrive. |
            | Surge playbook & swarming  | **Phase 1 – Playbook:** Triggers, roles, and checklists.<br><br>**Phase 2 – Swarm Activation:** Cross-functional huddles; unblock dependencies fast.<br><br>**Phase 3 – Recovery Audit:** Measure time-to-recover and update playbook. | - Faster recovery; reduced backlog growth.<br><br>- Better cross-team coordination.<br><br>- Fewer lingering aged tickets. | **Recovery gain** = (baseline − actual) × incidents.<br><br>Boosting same-day closures from **{closed_on_peak_open}** to **{closed_on_peak_open+5}** on peaks yields **+5 tickets/day**. | Surge imbalance visible on **{peak_open_date}** (opened **{peak_open_val}**, closed **{closed_on_peak_open}**). |
            """

            cio_recs["satisfaction"] = f"""
            | Recommendations              | Explanation                                                                 | Benefits                              | Cost Calculation                                         | Evidence & Graph Interpretation                                      |
            | ---------------------------- | --------------------------------------------------------------------------- | ------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- |
            | Customer assurance messaging | **Phase 1 – Draft Playbooks:** Clear, empathetic surge messages.<br><br>**Phase 2 – Trigger at Gaps:** Send updates when openings exceed closures.<br><br>**Phase 3 – Measure Impact:** Monitor complaints and churn proxies. | - Reduces anxiety and churn risk.<br><br>- Lowers complaint volume during delays.<br><br>- Preserves trust under load. | **Churn/complaints avoided** estimated from contact deflection.<br><br>If updates deflect **15%** of repeats on avg inflow (**{opened_avg:.1f}**) at 6 mins → **{(0.15*opened_avg*6)/60:.1f} hrs/day** saved. | Large opened–closed gaps on **{peak_open_date}** ( **{peak_open_val}** vs **{closed_on_peak_open}** ) increase perception risk without comms. |
            | Proactive surge communication| **Phase 1 – Pre-announce:** Warn of delays during planned spikes.<br><br>**Phase 2 – Live Status:** Publish queue health and ETA ranges.<br><br>**Phase 3 – Retrospective:** Share recovery summary and improvements. | - Manages expectations; fewer escalations.<br><br>- Fewer repeat contacts and status chasing.<br><br>- Better sentiment post-incident. | **Value** = complaints avoided × resolution cost.<br><br>Assume 5 complaints/day avoided at MYR 50 handling → **MYR 250/day**. | Spikes like **{peak_open_date}** show need for expectation-setting when closures lag (**{closed_on_peak_open}**). |
            | Priority-specific ETA commitments | **Phase 1 – Define ETAs:** Realistic, priority-based ETA bands in surge conditions.<br><br>**Phase 2 – Communicate & Track:** Display ETAs in portal/emails and track adherence.<br><br>**Phase 3 – Calibrate:** Adjust bands using actual closure performance. | - Clear expectations reduce escalations and repeat contacts.<br><br>- Improves perceived fairness and transparency.<br><br>- Supports VIP/SLA management. | **Contact deflection** = (repeat contacts avoided × mins ÷ 60).<br><br>If ETAs cut repeats by **10%** of inflow (**{opened_avg:.1f}**) at 6 mins → **{(0.10*opened_avg*6)/60:.1f} hrs/day** saved. | When closures trail openings (avg **{opened_avg:.1f}** vs **{closed_avg:.1f}**), explicit ETAs maintain trust. |
            """

        else:
            st.info("No recommendations related to open tickets or closure vs opening rate are available because the required data is missing.")

        # --- Render CIO tables ---
        if any(cio_recs.values()):
            render_cio_tables("Tickets Operational Analysis", cio_recs)


                    

    # ---------------------- 1d ----------------------
    with st.expander("📌 Ticket Backlog (Unresolved Tickets)"):

        if {"created_time"} <= set(df_filtered.columns):
            df_backlog = df_filtered.copy()

            # Parse created_time
            df_backlog["created_time"] = pd.to_datetime(df_backlog["created_time"], errors="coerce")

            # ✅ Pick resolved_time if available, else fall back to completed_time
            closure_column = None
            if "resolved_time" in df_backlog.columns:
                closure_column = "resolved_time"
            elif "completed_time" in df_backlog.columns:
                closure_column = "completed_time"

            if closure_column:
                df_backlog[closure_column] = pd.to_datetime(df_backlog[closure_column], errors="coerce")

                # Opened = count by created_time
                opened = (
                    df_backlog.groupby(df_backlog["created_time"].dt.date)
                    .size()
                    .reset_index(name="opened")
                    .rename(columns={"created_time": "date"})
                )

                # Closed = count by resolved_time/completed_time
                closed = (
                    df_backlog.dropna(subset=[closure_column])
                    .groupby(df_backlog[closure_column].dt.date)
                    .size()
                    .reset_index(name="closed")
                    .rename(columns={closure_column: "date"})
                )

                # ✅ Merge timeline
                rate = pd.merge(opened, closed, on="date", how="outer") \
                        .fillna(0).sort_values("date")

                # --- Backlog Calculation ---
                rate["backlog"] = (rate["opened"] - rate["closed"]).cumsum()

                # --- Graph: Backlog Trend ---
                fig_backlog = px.line(
                    data_frame=rate,
                    x="date",
                    y="backlog",
                    title="📈 Ticket Backlog Over Time",
                    labels={
                        "backlog": "Cumulative Backlog (Unresolved Tickets)",
                        "date": "Date"
                    }
                )
                st.plotly_chart(fig_backlog, use_container_width=True, key="ticket_backlog")

                # --- Dynamic Insights from Data ---
                peak_backlog = rate.loc[rate["backlog"].idxmax()]
                latest_backlog = rate.iloc[-1]
                avg_backlog = rate["backlog"].mean()

                st.markdown("### What is Ticket Backlog?")
                st.write("""
                Ticket backlog represents **all unresolved tickets** that have not yet been completed or closed.  
                It is a measure of **pending workload** and helps assess whether the service desk is keeping pace with incoming requests.
                """)

                # --- Replace the existing analysis block under "### 🔎 Analysis of Backlog Trend"
                st.markdown("### Analysis of Backlog Trend")
                st.write(f"""
                What this graph is: A cumulative backlog chart showing unresolved tickets (opened minus closed, cumulatively) over time.

                X-axis: Calendar date.
                Y-axis: Cumulative backlog size (number of unresolved tickets).

                What it shows in your data:
                Backlog peak: {peak_backlog['date']} with {int(peak_backlog['backlog'])} unresolved.
                Latest backlog: {latest_backlog['date']} with {int(latest_backlog['backlog'])} unresolved.
                Average backlog over the period: {avg_backlog:.1f} tickets/day.

                Overall, when the backlog line rises, intake is outpacing closure and unresolved work is accumulating; when it flattens or falls, outflow is keeping up and the desk is stabilizing.

                How to read it operationally:
                Gap = pace shortfall: The day-to-day rise rate indicates how quickly debt is accumulating.
                Lead–lag: Peaks soon after large intake days imply reactive recovery rather than smooth flow.
                Recovery strength: Faster drops after peaks signal effective staffing, routing, or sprints.
                Control: Hold backlog under a defined control limit via WIP caps, priority routing, and surge capacity.

                Why this matters: Backlog is operational debt. Keeping it low prevents SLA breaches, escalations, and user dissatisfaction while protecting cost and throughput.
                """)



                # --- Dynamic Recommendation Tables (only Explanation & Benefits rewritten) ---
                # --- Dynamic Recommendation Tables (only Explanation & Benefits rewritten) ---
                cio_1d = {
                    "cost": f"""
                | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |---|---|---|---|---|
                | Backlog burn-down sprints prioritised by **age × business impact** | **Phase 1 – Quantify & Segment:** Build a backlog view by age bucket and business impact so the oldest, highest-impact tickets are unmistakably visible. <br><br>**Phase 2 – Plan Focused Sprints:** Schedule 2–3 tightly scoped sessions with a fixed sprint lane and clear exit criteria to prevent scope creep. <br><br>**Phase 3 – Execute & Sustain:** Track burn-down daily, publish wins, and feed root causes back into routing/automation to stop re-accumulation. | - Reduces the cost of carry by removing the most expensive aged items first.<br><br>- Compresses overtime spend by resolving clusters efficiently.<br><br>- Lowers future penalties by shrinking the pool of near-breach tickets.<br><br>- Improves agent productivity by eliminating context-switching in a controlled sprint lane. | **Hours released** = (tickets closed in sprint × avg resolution hrs). If cost fields exist, multiply by rate. | Backlog **peaked at {int(peak_backlog['backlog'])}** on **{peak_backlog['date']}**; sprinting the oldest items will bend the curve down faster than FIFO. |
                | Deduplicate and merge linked tickets | **Phase 1 – Detect Duplicates:** Use similarity on title/description to identify candidate clusters and nominate a master ticket. <br><br>**Phase 2 – Merge & Close:** Link children to the master, move relevant notes/files, and close duplicates with an audit trail. <br><br>**Phase 3 – Prevent:** Add form validations and KB prompts to reduce future duplicate submissions. | - Eliminates duplicated analyst effort across cases.<br><br>- Reduces communication loops with requesters.<br><br>- Consolidates history so fixes are applied once and propagated.<br><br>- Lowers processing cost per incident and cleans metrics for accurate reporting. | **Time saved** = (duplicates linked × (avg handling time − batch close time)). | Periods of high backlog suggest duplicate reports of the same issue; post-linking, backlog drops without added capacity. |
                | Automate low-complexity backlog categories | **Phase 1 – Select Candidates:** Identify categories with deterministic steps and known fixes inside the backlog. <br><br>**Phase 2 – Build Guided Flows:** Design self-serve or agent-assist automations that validate inputs and apply the fix consistently. <br><br>**Phase 3 – Drain & Expand:** Run off-peak automation waves to drain simple items, then expand to adjacent categories. | - Converts repetitive manual work into zero/low-touch resolution.<br><br>- Accelerates time-to-clear so analysts can focus on complex, higher-value tasks.<br><br>- Reduces reopens via standardized execution.<br><br>- Shrinks operating cost on the heaviest, simplest cohorts. | **Hours avoided** = (automated backlog tickets × avg handling hrs). | The backlog **average of {avg_backlog:.1f}**/day indicates a stable pool of simple items suitable for automation. |
                """,
                    "performance": f"""
                | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |---|---|---|---|---|
                | Oldest-first within SLA risk (OF-SLAR) | **Phase 1 – Compute Risk Rank:** Combine ticket age with time-to-breach so high-risk items float to the top of every queue. <br><br>**Phase 2 – Enforce Pull Order:** Configure work boards to pull strictly by risk rank, with exceptions logged and reviewed. <br><br>**Phase 3 – Validate Outcomes:** Monitor mean/95th-percentile age and breach count to verify aging tails are collapsing. | - Lowers mean and tail age simultaneously, improving predictability.<br><br>- Protects SLA by resolving imminent breaches first.<br><br>- Reduces firefighting by preventing conversion of aging items into escalations.<br><br>- Improves flow uniformity across teams. | **SLA hours protected** = (at-risk tickets resolved pre-breach × avg overage hrs). | Latest backlog is **{int(latest_backlog['backlog'])}**; applying OF-SLAR reduces aging tails visible in the trend line. |
                | Control-limit trigger with intake gating | **Phase 1 – Set Control Bands:** Define an upper backlog limit based on capacity and acceptable risk. <br><br>**Phase 2 – Triggered Gating:** When the limit is exceeded, deflect non-urgent intake to self-service/callbacks and throttle sources until the backlog returns within bounds. <br><br>**Phase 3 – Review & Reset:** After recovery, recalibrate limits and sources to prevent recurrence. | - Prevents runaway queues during spikes.<br><br>- Stabilizes flow so closures catch up sooner.<br><br>- Reduces SLA exposure by prioritizing essential intake.<br><br>- Preserves analyst focus for high-impact work during constraint periods. | **Overtime avoided** = (hours not added to queue × overtime rate). | On the peak date (**{peak_backlog['date']}**), backlog exceeded normal levels; gating would have prevented further growth. |
                | Daily 20-minute “aging swarm” | **Phase 1 – Define Threshold:** Identify p80/p90 age and assemble a rotating swarm squad targeting items beyond that mark. <br><br>**Phase 2 – Rapid Unblocks:** In short, time-boxed huddles, resolve dependencies, make calls, and take decisive next actions. <br><br>**Phase 3 – Institutionalize:** Track before/after age metrics and bake swarm cadence into team rituals. | - Produces fast wins on the worst aging tail.<br><br>- Reduces queue anxiety by creating visible daily progress.<br><br>- Increases first-time-right by clearing blockers synchronously.<br><br>- Improves throughput without major staffing changes. | **Δp80 age hours** × (tickets above threshold). | Post-swarm, the backlog line should show sharper downward steps after each session. |
                """,
                    "satisfaction": f"""
                | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |---|---|---|---|---|
                | Backlog-aware ETA and apology cadence | **Phase 1 – Identify At-Risk Cohorts:** Target tickets older than N days or inside near-breach windows. <br><br>**Phase 2 – Communicate Clearly:** Send specific ETAs, reasons for delay, and next actions; include apology tokens if policy allows. <br><br>**Phase 3 – Measure Impact:** Track complaint volume and sentiment change to tune cadence and content. | - Reduces complaint and chase-contact volume by setting expectations.<br><br>- Preserves trust during delays with transparent reasoning.<br><br>- Lowers repeat contact load on agents.<br><br>- Improves CSAT by acknowledging and addressing inconvenience. | **Complaints avoided** × avg handling minutes. | With backlog currently **{int(latest_backlog['backlog'])}**, silence will erode trust; proactive comms stabilise sentiment. |
                | VIP/critical fast-lane through backlog | **Phase 1 – Mark Priority:** Maintain a VIP/critical allowlist with explicit response/restore targets inside the backlog. <br><br>**Phase 2 – Assign Senior Owners:** Route these items immediately to experienced analysts with escalation paths pre-agreed. <br><br>**Phase 3 – Review Outcomes:** Audit breaches and document improvements to harden the lane. | - Protects revenue and executive relationships.<br><br>- Reduces high-impact escalations.<br><br>- Improves perceived fairness for critical users.<br><br>- Concentrates expertise where the business impact is greatest. | **Churn/impact hours avoided** where tracked. | Peak backlog periods (e.g., **{peak_backlog['date']}**) risk delaying high-impact items; fast-lane reduces that risk. |
                | “Waiting on customer” clock pause | **Phase 1 – Detect Stalls:** Identify tickets aging due to missing requester inputs. <br><br>**Phase 2 – Pause & Notify:** Pause SLA clocks with explicit “waiting on customer” status and notify the requester with exactly what’s needed. <br><br>**Phase 3 – Resume & Audit:** Resume the clock on response and review patterns to improve forms and guidance. | - Prevents artificial SLA breaches from customer-side waits.<br><br>- Improves perceived fairness of metrics.<br><br>- Reduces unnecessary agent follow-ups.<br><br>- Educates users to provide complete information earlier. | **Breach hours avoided** = (re-categorized waits × overage hrs). | If backlog is inflated by requester inactivity, pausing the clock will prevent misleading backlog growth signals. |
                """
                }

                render_cio_tables("Ticket Backlog (Unresolved Tickets)", cio_1d)



            else:
                st.warning("⚠️ No closure-related column ('resolved_time' or 'completed_time') found in dataset.")
        else:
            st.warning("⚠️ 'created_time' column not found for backlog analysis.")
