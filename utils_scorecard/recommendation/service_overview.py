# utils_service_desk_pfomance/recommendation_performance/ticket_volume.py

import streamlit as st
import plotly.express as px
import pandas as pd

# ───────────────── Mesiniaga theme ─────────────────
BLUE_TONES = [
    "#004C99",  # deep brand navy
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]
px.defaults.template = "plotly_white"

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def service_overview(df_filtered):

    # ---------------------- 1a ----------------------
    # ⚠️ Per instruction: DO NOT change anything in this expander
    with st.expander("📌 Number of Tickets Opened"):
        # ✅ Updated column name from 'created_time' to 'report_date'
        if "report_date" in df_filtered.columns:
            df_filtered["created_date"] = pd.to_datetime(
                df_filtered["report_date"], errors="coerce"
            ).dt.date

            # ✅ Ensure avg_resolution_time_mins is numeric (fix Timestamp issue)
            if "avg_resolution_time_mins" in df_filtered.columns:
                df_filtered["avg_resolution_time_mins"] = pd.to_numeric(
                    df_filtered["avg_resolution_time_mins"], errors="coerce"
                )

            trend = (
                df_filtered.groupby("created_date")
                .size()
                .reset_index(name="ticket_count")
            )

            # Format dates to Malaysian format (DD/MM/YYYY)
            if not trend.empty:
                trend["created_date_str"] = pd.to_datetime(
                    trend["created_date"]
                ).dt.strftime("%d/%m/%Y")
            else:
                trend["created_date_str"] = []

            # --- Graph 1: Tickets opened over time (line chart)
            fig = px.line(
                trend,
                x="created_date_str",
                y="ticket_count",
                title="Tickets Opened Over Time",
                color_discrete_sequence=BLUE_TONES,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 🔹 Dynamic analysis (standardized format)
            if not trend.empty:
                total_tickets_o = int(trend["ticket_count"].sum())
                avg_tickets_o = float(trend["ticket_count"].mean())
                max_idx_o = trend["ticket_count"].idxmax()
                min_idx_o = trend["ticket_count"].idxmin()
                max_row = trend.loc[max_idx_o]
                min_row = trend.loc[min_idx_o]

                st.markdown("### Analysis – Tickets Opened Over Time")
                st.write(
                    f"""What this graph is: A single-stream throughput chart showing the number of tickets opened per day.
X-axis: Calendar date.
Y-axis: Daily count of opened tickets.

What it shows in your data:
Largest intake day: {max_row['created_date_str']} with {int(max_row['ticket_count'])} opened.
Lowest intake day: {min_row['created_date_str']} with {int(min_row['ticket_count'])} opened.
Averages over the period are {avg_tickets_o:.1f} opened/day across a total of {total_tickets_o} opened tickets.

Overall, sustained sequences of higher bars indicate demand spikes that can outpace capacity if unaddressed. Lower and stable bars indicate a steadier inflow that is easier to manage within baseline staffing.

How to read it operationally:
Gap-to-normal: The distance from the average line implies surge size to plan for via temporary capacity or automation.
Lead indicators: Repeating weekday or month-end spikes suggest scheduled change windows or recurring user behavior.
Spike containment: After each spike, check whether closures keep pace; if not, backlog is likely to rise.

Why this matters: Intake is the front door of the service desk. Understanding the pace and spikes of demand lets you schedule staff, activate automation, and protect SLA during peak days."""
                )
            else:
                st.info("No data available to generate analysis.")

            # --- Graph 2: Tickets opened by Service Owner (bar chart)
            option = None
            owner_top10 = pd.DataFrame()
            owner_evidence = "No service_owner column available; owner-level analysis not performed."

            if "service_owner" in df_filtered.columns:
                owner_summary = (
                    df_filtered.groupby("service_owner")
                    .size()
                    .reset_index(name="ticket_count")
                )

                # Add selector: Top 10 Highest or Lowest owners
                option = st.radio(
                    "Select Service Owner View:",
                    ("Top 10 Highest", "Top 10 Lowest"),
                    horizontal=True,
                )

                if option == "Top 10 Highest":
                    owner_top10 = (
                        owner_summary.sort_values("ticket_count", ascending=False)
                        .head(10)
                        .reset_index(drop=True)
                    )
                    title = "Top 10 Service Owners with Highest Tickets Opened"
                else:
                    owner_top10 = (
                        owner_summary.sort_values("ticket_count", ascending=True)
                        .head(10)
                        .reset_index(drop=True)
                    )
                    title = "Top 10 Service Owners with Lowest Tickets Opened"

                fig_owner = px.bar(
                    owner_top10,
                    x="service_owner",
                    y="ticket_count",
                    title=title,
                    text="ticket_count",
                    color_discrete_sequence=BLUE_TONES,
                )
                fig_owner.update_traces(textposition="outside")
                st.plotly_chart(fig_owner, use_container_width=True)

                # 🔹 Owner-level analysis (standardized format)
                if not owner_top10.empty:
                    max_owner = owner_top10.loc[owner_top10["ticket_count"].idxmax()]
                    min_owner = owner_top10.loc[owner_top10["ticket_count"].idxmin()]
                    st.markdown("### Analysis – Tickets Opened by Service Owner")
                    st.write(
                        f"""What this graph is: A bar chart of tickets opened aggregated by service owner with a focus on the selected top ten group.
X-axis: Service owner.
Y-axis: Ticket count for opened tickets.

What it shows in your data:
Highest owner in this selection: {max_owner['service_owner']} with {int(max_owner['ticket_count'])} opened.
Lowest owner in this selection: {min_owner['service_owner']} with {int(min_owner['ticket_count'])} opened.
The distribution highlights where ticket creation is concentrated across owners.

Overall, concentration at the top implies potential workload hotspots. A flatter distribution indicates a more even spread of intake across owners.

How to read it operationally:
Staffing signal: Owners with consistently high intake need appropriate resourcing and backup to avoid SLA risk.
Standardization need: Owners on the low end might be candidates to share practices or capacity.
Automation fit: High-volume owners often host repeatable categories that are ready for guided flows.

Why this matters: Owner-level intake reveals who needs help first and where automation or process clarity will pay off most."""
                    )

                    # ✅ Owner-level evidence setup
                    if option == "Top 10 Highest":
                        owner_top = owner_top10.loc[
                            owner_top10["ticket_count"].idxmax()
                        ]
                        owner_bottom = owner_top10.loc[
                            owner_top10["ticket_count"].idxmin()
                        ]
                        owner_evidence = (
                            f"Service owner analysis (Top 10 Highest) shows **{owner_top['service_owner']}** as highest with "
                            f"**{int(owner_top['ticket_count'])}** opened, while **{owner_bottom['service_owner']}** is lowest at "
                            f"**{int(owner_bottom['ticket_count'])}** within this group."
                        )
                    else:
                        owner_top = owner_top10.loc[
                            owner_top10["ticket_count"].idxmax()
                        ]
                        owner_bottom = owner_top10.loc[
                            owner_top10["ticket_count"].idxmin()
                        ]
                        owner_evidence = (
                            f"Service owner analysis (Top 10 Lowest) shows **{owner_top['service_owner']}** highest within this group at "
                            f"**{int(owner_top['ticket_count'])}** opened, while **{owner_bottom['service_owner']}** recorded only "
                            f"**{int(owner_bottom['ticket_count'])}**."
                        )
            else:
                st.info("Service Owner column not found — owner-level analysis skipped.")

            # --- Evidence strings for CIO tables
            if 'max_row' in locals() and 'min_row' in locals():
                peak_evidence = (
                    f"Peak day **{max_row['created_date_str']}** with **{int(max_row['ticket_count'])}** opened vs "
                    f"low **{min_row['created_date_str']}** with **{int(min_row['ticket_count'])}** opened."
                )
                avg_evidence = (
                    f"Average daily intake **{avg_tickets_o:.1f}**; total opened **{total_tickets_o}** over the period."
                )
            else:
                peak_evidence = "No intake timeline available."
                avg_evidence = "No intake average available."

            # --- SAFE VALUES for f-strings (avoid conditional format specifiers)
            avg_tickets_o_safe = float(avg_tickets_o) if 'avg_tickets_o' in locals() else 0.0
            peak_ticket_count_safe = int(max_row['ticket_count']) if 'max_row' in locals() else 0

            avg_resolution_time = (
                pd.to_numeric(df_filtered.get("avg_resolution_time_mins", pd.Series(dtype=float)), errors="coerce").mean()
            )
            if pd.isna(avg_resolution_time):
                avg_resolution_time = 0.0

            resolution_evidence = (
                f"Average resolution time across dataset **{avg_resolution_time:.2f} mins** from **{len(df_filtered)}** records."
            )
            sla_evidence = (
                peak_evidence
                if 'max_row' in locals()
                else "No SLA risk inference available due to missing peak day."
            )

            # --- CIO tables (unchanged per instruction for section 1a) ---
            cio_1a = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|----------------|----------------------|----------|------------------|--------------------------------|
| **Automate triage for high-volume request types** | **Phase 1 – Identify:** Use the opened-over-time trend and owner distribution to find the top categories that drive spikes. Describe each category and the common fields users omit or misfill that cause ping-pong. <br><br>**Phase 2 – Implement:** Build rule-based intake with mandatory fields, category-specific forms, and auto-routing to the right queue on first touch. <br><br>**Phase 3 – Optimize:** Review deflection and routing accuracy monthly and refine rules where misroutes or reassignments occur. This removes repetitive manual sorting and accelerates first action. | - Reduces manual categorization time during peak days which protects analyst focus on real troubleshooting.<br><br>- Lowers misrouting which eliminates rework and shortens time to first meaningful response.<br><br>- Raises throughput during surge days which stabilizes backlog growth. | Hours saved = Reduction% × Avg handling mins × Total opened. With a conservative 15% reduction and avg handling {avg_resolution_time:.2f} mins on {len(df_filtered)} tickets → **{avg_resolution_time * len(df_filtered) * 0.15:.2f} mins saved**. | {peak_evidence}  |
| **Adjust staffing schedules to demand patterns** | **Phase 1 – Analyze:** Use the daily intake chart to profile weekday and month-end patterns and quantify surge magnitude above the average. <br><br>**Phase 2 – Align:** Shift rosters and scheduled breaks so analyst presence peaks on the highest intake windows and shortens queues in real time. <br><br>**Phase 3 – Recalibrate:** Recheck patterns quarterly and refine the shift templates to follow new demand signals. | - Decreases overtime because the right capacity is online when spikes occur.<br><br>- Prevents burnout by smoothing individual load which maintains quality and reduces errors under pressure.<br><br>- Improves SLA attainment by cutting wait time right after high-intake days. | Overtime savings = Overtime hours avoided × Avg hourly rate. Excess load = peak {peak_ticket_count_safe} vs average {avg_tickets_o_safe:.1f} opened/day; schedule alignment targets this excess window. | {avg_evidence} |
| **Eliminate duplicate ticket categories** | **Phase 1 – Review:** Audit category names tied to the owners with the most opened tickets and find overlaps that confuse users. <br><br>**Phase 2 – Consolidate:** Merge synonyms into standard categories and update the portal prompts and tooltips that guide selection. <br><br>**Phase 3 – Enforce:** Add routing rules that prevent legacy categories from being used and monitor reassignment rates for leaks. | - Cuts rework created by misclassification which shortens cycle time to the right resolver group.<br><br>- Simplifies reporting which makes trends clearer for decision making across months.<br><br>- Reduces agent frustration from repeated bounces which improves morale and consistency. | Time saved = (Duplicates reduced × Avg handling mins). Owners present: **{df_filtered['service_owner'].nunique() if 'service_owner' in df_filtered.columns else 0}**; use reassignment rate reduction to quantify. | {owner_evidence} |
| **Automate ticket acknowledgments** | **Phase 1 – Configure:** Send an immediate, category-aware confirmation with next steps and required information checklists. <br><br>**Phase 2 – Personalize:** Include owner group name and expected first response window derived from historical averages. <br><br>**Phase 3 – Improve:** Track duplicate submissions per day and tighten wording where duplication persists. | - Lowers duplicate tickets created by anxious users because they receive clarity and timing up front.<br><br>- Reduces follow-up calls which saves handling minutes and keeps lines free for high-impact issues.<br><br>- Raises perceived responsiveness which protects satisfaction during busy periods. | Savings = (Duplicate tickets avoided × Avg handling mins). Use spike days above average to estimate duplication avoided relative to **{avg_tickets_o_safe:.1f}** opened/day baseline. | {peak_evidence} |
| **Reallocate resources from lowest-volume owners** | **Phase 1 – Identify:** From the owner bar chart, find owners with consistently low intake and quantify idle capacity windows. <br><br>**Phase 2 – Reassign:** Move a portion of their time to support the highest-volume owners during peak hours. <br><br>**Phase 3 – Review:** Compare throughput and backlog movement after reallocation to confirm net gain. | - Avoids idle paid hours which directly reduces cost per ticket at the desk level.<br><br>- Increases resolution speed where demand is concentrated which dampens backlog growth after spikes.<br><br>- Creates cross-skilling that strengthens resilience when individuals are unavailable. | Savings = (Idle hours shifted × Avg hourly rate). Evidence owner spread shows the gap between high and low volume producers which indicates available capacity to reassign. | {owner_evidence} |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|----------------|----------------------|----------|------------------|--------------------------------|
| **Implement dynamic routing to skill-based groups** | **Phase 1 – Map:** Link the top opened categories to resolver skills and document first-time-right criteria. <br><br>**Phase 2 – Route:** Enforce rules so tickets land with the right group on first assignment. <br><br>**Phase 3 – Refine:** Track reassignments and SLA breaches per category and tune rules monthly. | - Cuts handoff time which reduces total resolution time and improves SLA compliance.<br><br>- Increases first-time-right which stabilizes queues and reduces context switching.<br><br>- Improves predictability for owners which helps planning. | Minutes saved = 10% × Avg resolution {avg_resolution_time:.2f} × {len(df_filtered)} tickets → **{avg_resolution_time * len(df_filtered) * 0.10:.2f} mins saved**. | {resolution_evidence} |
| **Expand knowledge base with FAQs** | **Phase 1 – Prioritize:** Use the top categories and owner hotspots to pick the most repetitive issues. <br><br>**Phase 2 – Produce:** Write step-by-step guides with screenshots and short videos aligned to portal fields. <br><br>**Phase 3 – Integrate:** Surface these guides in the portal and agent console at ticket creation time. | - Speeds up resolutions for both agents and end users which reduces backlog accumulation.<br><br>- Lowers average handling time for repeatable issues which frees capacity for complex work.<br><br>- Reduces repeated tickets from the same users because they can self-serve. | Time avoided = (Self-served tickets × Avg handling mins). Choose top five categories by opened volume to estimate. | {owner_evidence} |
| **Introduce real-time workload dashboards** | **Phase 1 – Build:** Show opened today vs average, queue length, and SLA clocks on a live board. <br><br>**Phase 2 – Operate:** Supervisors rebalance and swarm based on live signals where queues spike. <br><br>**Phase 3 – Learn:** Weekly review of interventions vs outcomes to close the loop. | - Enables rapid intervention during demand spikes which prevents queue growth and SLA breaches.<br><br>- Improves responsiveness by making load visible in real time.<br><br>- Raises efficiency by aligning people to the actual work on the floor. | Productivity gain = Reduction in idle/blocked minutes × Avg hourly rate. Use deviation from **{avg_tickets_o_safe:.1f}** opened/day to size interventions. | {avg_evidence} |
| **Apply predictive analytics for peak forecasting** | **Phase 1 – Model:** Train simple seasonality or weekday models on opened counts. <br><br>**Phase 2 – Schedule:** Use forecast windows to pre-staff and pre-load knowledge for expected surges. <br><br>**Phase 3 – Validate:** Compare forecast vs actual and adjust model hyperparameters monthly. | - Enables proactive staffing changes that keep queues stable during spikes.<br><br>- Improves SLA adherence by preventing long waits at intake peaks.<br><br>- Reduces firefighting with smoother planning cycles. | SLA gain = Δ(tickets within SLA) using forecasted surge days vs baseline **{avg_tickets_o_safe:.1f}** opened/day. | {sla_evidence} |
| **Benchmark performance by service owner** | **Phase 1 – Compare:** Rank owners by SLA and mean resolution time adjusted for intake mix. <br><br>**Phase 2 – Share:** Publish best practices from top owners. <br><br>**Phase 3 – Uplift:** Coach lower performers and recheck results. | - Raises the baseline by spreading effective methods which compresses variance across teams.<br><br>- Highlights actionable gaps quickly which focuses improvements where impact is largest.<br><br>- Builds a learning culture which sustains performance. | SLA gain = (Improved SLA% × Tickets per owner). Use owner spread observed in bars to target. | {owner_evidence} |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|----------------|----------------------|----------|------------------|--------------------------------|
| **Provide transparent ticket status updates** | **Phase 1 – Expose:** Enable a portal widget that shows live status and next action. <br><br>**Phase 2 – Notify:** Send automatic status changes with expected timing based on historical averages. <br><br>**Phase 3 – Listen:** Capture feedback on clarity and adapt messages. | - Builds trust because users can see progress without calling the desk.<br><br>- Reduces follow-up inquiries which lowers load during spikes.<br><br>- Increases CSAT by setting clear expectations. | Complaints avoided × Avg handling minutes per complaint. Use spike days above average as the counterfactual. | {peak_evidence} |
| **Introduce SLA-based priority tiers** | **Phase 1 – Define:** Translate business impact into critical, high, normal, and low tiers with clear rules. <br><br>**Phase 2 – Automate:** Apply tier at intake and show it to users. <br><br>**Phase 3 – Monitor:** Track breaches by tier and tune thresholds. | - Improves satisfaction for high-impact users because they see faster responses.<br><br>- Clarifies expectations for everyone which reduces escalations.<br><br>- Aligns resources to what matters most. | SLA penalty avoided = (# breaches avoided × Avg penalty cost). Risk indicated on peak intake days vs average **{avg_tickets_o_safe:.1f}**. | {sla_evidence} |
| **Send proactive communication during peaks** | **Phase 1 – Detect:** Identify forecast or real-time peaks. <br><br>**Phase 2 – Communicate:** Pre-warn users about expected delays and provide self-help links. <br><br>**Phase 3 – Follow up:** Close the loop after resolution to restore confidence. | - Reduces complaints during busy periods because expectations are managed in advance.<br><br>- Improves perception of responsiveness when staff are stretched.<br><br>- Increases loyalty by being transparent during stress. | Escalation cost avoided = (# escalations prevented × Avg escalation cost). Compare peak vs non-peak days. | {peak_evidence} |
| **Offer self-service resolution tools** | **Phase 1 – Identify:** Pick repetitive, low-complexity categories with high opened volume. <br><br>**Phase 2 – Build:** Guided flows and chatbots that capture screenshots and key details. <br><br>**Phase 3 – Track:** Measure self-solve rate and iterate. | - Delivers faster resolutions for simple issues without analyst time.<br><br>- Reduces ticket creation volume which lowers queue length.<br><br>- Empowers users which improves satisfaction over time. | Cost avoidance = (# self-resolved × Avg resolution cost). Use top categories from owner view to size. | {owner_evidence} |
""",
            }

            render_cio_tables("Number of Tickets Opened", cio_1a)

    # ---------------------- 1b ----------------------
    with st.expander("📌 Number of Tickets Closed"):
        # ✅ FIX: define an empty DataFrame so 'closed' always exists
        closed = pd.DataFrame(columns=["report_date", "ticket_closed"])

        if "report_date" in df_filtered.columns:
            # Convert and group data
            df_filtered["report_date_parsed"] = pd.to_datetime(
                df_filtered["report_date"], errors="coerce"
            ).dt.date
            closed = (
                df_filtered.groupby("report_date_parsed")
                .size()
                .reset_index(name="ticket_closed")
            )

            # Create bar chart for closures over time
            fig = px.bar(
                closed,
                x="report_date_parsed",
                y="ticket_closed",
                title="Tickets Closed Over Time",
                labels={
                    "report_date_parsed": "Report Date",
                    "ticket_closed": "Number of Tickets Closed",
                },
                color_discrete_sequence=BLUE_TONES,
            )
            st.plotly_chart(fig, use_container_width=True)

            # ✅ NEW: compute metrics safely BEFORE using them
            if not closed.empty:
                total_tickets_c = int(closed["ticket_closed"].sum())
                avg_tickets_c = float(closed["ticket_closed"].mean())
                max_idx_c = closed["ticket_closed"].idxmax()
                min_idx_c = closed["ticket_closed"].idxmin()
                max_day = closed.loc[max_idx_c]
                min_day = closed.loc[min_idx_c]

                # Standardized analysis format
                st.markdown("### Analysis – Tickets Closed Over Time")
                st.write(
                    f"""What this graph is: A throughput chart showing the daily number of tickets that moved to a closed state.
X-axis: Calendar date.
Y-axis: Daily count of closed tickets.

What it shows in your data:
Largest closure day: {max_day['report_date_parsed'].strftime('%Y-%m-%d')} with {int(max_day['ticket_closed'])} closed.
Lowest closure day: {min_day['report_date_parsed'].strftime('%Y-%m-%d')} with {int(min_day['ticket_closed'])} closed.
Averages over the period are {avg_tickets_c:.1f} closed/day across a total of {total_tickets_c} closures.

Overall, tightly clustered bars indicate a stable flow-based process, while sporadic tall bars suggest batch closure behavior that may mask queues building earlier in the week.

How to read it operationally:
Stability lens: Large variance in bar heights signals volatile throughput and higher SLA risk after intake spikes.
Bottleneck lens: Runs of low bars after high intake days point to capacity gaps or handoff delays.
Momentum lens: Compare early vs late period bar heights to sense improving or degrading throughput.

Why this matters: Outflow is the back door of the process. When closures keep pace with openings, backlog shrinks and SLA risk drops; when closures lag, backlog grows."""
                )
            else:
                st.info(
                    "No valid 'report_date' values after parsing; cannot compute closures or analysis."
                )

            # --- New graph: Closure rate per service owner ---
            if "service_owner" in df_filtered.columns:
                owner_closed = (
                    df_filtered.groupby("service_owner")
                    .size()
                    .reset_index(name="tickets_closed")
                )
                owner_closed["closure_rate"] = (
                    owner_closed["tickets_closed"]
                    / max(owner_closed["tickets_closed"].sum(), 1)
                    * 100
                )

                fig2 = px.bar(
                    owner_closed.sort_values("tickets_closed", ascending=False),
                    x="service_owner",
                    y="tickets_closed",
                    title="Tickets Closed per Service Owner",
                    labels={
                        "service_owner": "Service Owner",
                        "tickets_closed": "Number of Tickets Closed",
                    },
                    text="closure_rate",
                    color_discrete_sequence=BLUE_TONES,
                )
                fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)

                if not owner_closed.empty:
                    top_o = owner_closed.sort_values(
                        "tickets_closed", ascending=False
                    ).iloc[0]
                    bot_o = owner_closed.sort_values(
                        "tickets_closed", ascending=False
                    ).iloc[-1]
                    st.markdown("### Analysis – Tickets Closed per Service Owner")
                    st.write(
                        f"""What this graph is: A bar chart of closures aggregated by service owner with the percentage share annotated.
X-axis: Service owner.
Y-axis: Count of tickets closed by owner.

What it shows in your data:
Highest closer: {top_o['service_owner']} with {int(top_o['tickets_closed'])} closed which is {top_o['closure_rate']:.1f}% of all closures.
Lowest closer: {bot_o['service_owner']} with {int(bot_o['tickets_closed'])} closed.

Overall, an uneven share indicates concentration of closure capacity and potential single points of failure. A more even distribution suggests resilience and shared practices.

How to read it operationally:
Load balance: Owners with a high share may need relief or automation on repetitive tasks.
Coaching signal: Owners with a low share may need training or different ticket mixes to gain momentum.
Risk lens: Over-dependency on a few owners increases vulnerability during leave or attrition.

Why this matters: Closure capacity must be resilient. Spreading capability avoids bottlenecks and sustains SLA performance."""
                    )

        # ✅ Ensure safe defaults if 'closed' is empty
        if not closed.empty:
            total_tickets_c = int(closed["ticket_closed"].sum())
            avg_tickets_c = float(closed["ticket_closed"].mean())
            max_day = closed.loc[closed["ticket_closed"].idxmax()]
            max_day_str = max_day["report_date_parsed"].strftime("%Y-%m-%d")
            max_day_val = int(max_day["ticket_closed"])
        else:
            total_tickets_c, avg_tickets_c = 0, 0.0
            max_day_str, max_day_val = "N/A", 0

        # ✅ Enhanced CIO tables with ≥3 recommendations, phased explanations, richer benefits, and real-value cost/evidence
        cio_1b = {
            "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|-------------|----------|------------------|---------------------------------|
| Streamline ticket closure workflows | **Phase 1 – Standardize:** Define a single mandatory closure checklist per category that specifies evidence, validation steps, and data fields so analysts can close without rework.<br><br>**Phase 2 – Automate:** Configure conditional transitions so tickets move to 'Resolved' and 'Closed' when checklist conditions are met and required fields are complete.<br><br>**Phase 3 – Orchestrate:** Introduce a daily 'ready-to-close' swimlane that batches low-risk verifications for a fast end-of-day drain. | - Reduces handling minutes per closure because redundant steps are removed and analysts follow a single source of truth.<br><br>- Improves predictability of daily outflow which reduces the need for end-week overtime and improves workforce utilization.<br><br>- Increases data quality at closure because structured evidence fields reduce omissions during busy windows.<br><br>- Stabilizes SLA because standardization shortens the tail of simple tickets that otherwise linger. | If **{total_tickets_c:,}** closures each save **5 mins**, staff hours saved = **{round((total_tickets_c*5)/60,2)}**. Using the observed daily average of **{avg_tickets_c:.1f}** closures, a 5-min saving equates to **{round((avg_tickets_c*5)/60,2)} hours/day**. | Peak closure day **{max_day_str}** processed **{max_day_val}** tickets, indicating batch behavior that standardized checklists and batching can compress into shorter windows. |
| Auto-complete repetitive resolution notes | **Phase 1 – Template:** Build resolution-note templates per top categories with pre-written steps, artifacts, and validations that reflect real SOPs.<br><br>**Phase 2 – Personalize:** Auto-fill dynamic tokens (CI name, incident ID, category) and require only delta edits by analysts.<br><br>**Phase 3 – Measure:** Track template usage rate and mean typing time to tune content monthly. | - Cuts manual typing time on repetitive fixes which directly reduces cycle time and frees analysts for complex work.<br><br>- Improves audit readiness because standardized notes capture evidence consistently without missing fields.<br><br>- Lowers cognitive load so analysts make fewer documentation errors and can close more tickets per hour.<br><br>- Elevates team consistency which smooths customer experience across owners. | Minutes saved = (Template uses × 2–4 mins). If templates cover **{avg_tickets_c:.1f}** average daily closures and 60% use templates at **3 mins** each → **{round(avg_tickets_c*0.60*3,2)} mins/day** saved (**{round((avg_tickets_c*0.60*3)/60,2)} hours/day**). | Owner closure distribution and daily volume variability demonstrate repeated categories suitable for templating with measurable gains at the observed throughput. |
| One-click bulk close for verified duplicates | **Phase 1 – Link:** Enforce duplicate linking to a parent ticket during triage and diagnosis.<br><br>**Phase 2 – Close in bulk:** When the parent resolves, trigger a one-click bulk close with consistent customer notifications across all children.<br><br>**Phase 3 – Review:** Reconcile duplicate patterns weekly to improve upstream deflection. | - Eliminates repeated closing actions across multiple child tickets which reduces end-of-day toil and keeps queues lean.<br><br>- Speeds SLA recovery after spikes because duplicate tails are removed in a single action rather than piecemeal edits.<br><br>- Improves customer communication quality because every linked requester receives the same clear resolution summary.<br><br>- Shrinks rework because linkage forces root-cause thinking rather than ticket-by-ticket patching. | Minutes saved = (Duplicates closed × 1–2 mins). If even 10% of **{total_tickets_c:,}** closures are duplicates at **1.5 mins** each → **{round(total_tickets_c*0.10*1.5,2)} mins** (**{round((total_tickets_c*0.10*1.5)/60,2)} hours**) saved over the period. | Variance between low and high closure days (avg **{avg_tickets_c:.1f}**, peak **{max_day_val}**) indicates duplicate tails that bulk close can compress. |
""",
            "performance": f"""
| Recommendations | Explanation | Benefits | Metric Impact | Evidence & Graph Interpretation |
|-----------------|-------------|----------|---------------|--------------------------------|
| Real-time closure monitoring dashboards | **Phase 1 – Instrument:** Build a live board showing closures today vs target, queue length, and SLA timers by owner and priority.<br><br>**Phase 2 – Act:** Supervisors rebalance work and swarm blockers when the live close rate falls below the daily target derived from historical averages.<br><br>**Phase 3 – Learn:** Review interventions weekly and lock in playbooks that consistently lift throughput. | - Increases responsiveness during the workday so small stalls do not become backlog growth by evening.<br><br>- Shortens time-in-queue because leaders can nudge and redistribute based on live signals rather than end-day reports.<br><br>- Creates accountability and shared awareness which improves cadence and reduces last-minute firefighting.<br><br>- Raises predictability by anchoring teams to daily closure targets. | Target close rate = **{avg_tickets_c:.1f}** per day baseline. A 10% uplift yields **{avg_tickets_c*1.10:.1f}** closures/day; Δ = **{(avg_tickets_c*0.10):.1f}** additional closures/day. | Peak **{max_day_str}** at **{max_day_val}** vs average **{avg_tickets_c:.1f}** shows headroom for controlled acceleration on normal days via live nudging. |
| Balance workloads among service owners | **Phase 1 – Diagnose:** Compare closure share by owner vs intake mix to identify imbalances.<br><br>**Phase 2 – Rebalance:** Reassign simple categories from the most loaded owners to partners with available capacity.<br><br>**Phase 3 – Rotate:** Run weekly rotations to spread knowledge and prevent single-point failures. | - Minimizes bottlenecks created by a few overloaded owners which increases whole-desk throughput and stabilizes SLA.<br><br>- Reduces fatigue on heavy owners which preserves accuracy and lowers error-driven rework.<br><br>- Scales capability across the team so coverage is resilient during leave or attrition.<br><br>- Aligns people to demand patterns which converts idle time to value. | Throughput gain = (Tickets reassigned × Avg handling mins). If **5** tickets/day move from top owner to partners at **10 mins** each → **50 mins/day** capacity reclaimed (**0.83 hours/day**). | Owner bar chart and daily closure spread highlight uneven distribution that rebalancing can directly address. |
| Auto-escalation for aging tickets | **Phase 1 – Thresholds:** Define age thresholds per priority where tickets auto-escalate with explicit next actions.<br><br>**Phase 2 – Workflow:** Notify supervisors and fast-lane queues automatically when thresholds are crossed.<br><br>**Phase 3 – Governance:** Review escalated outcomes weekly and refine thresholds. | - Reduces silent aging which is a leading indicator of SLA breach and customer dissatisfaction.<br><br>- Improves visibility of stuck work so help arrives sooner and cycle time compresses.<br><br>- Raises first-time-right on critical items because experts intervene earlier in the lifecycle.<br><br>- Smooths daily close rates which dampens volatility after spikes. | SLA recovery = % escalated resolved within 24h. If 20 escalations/week improve from 50%→70% within-24h, **+4** extra on-time closures/week. | Runs of low daily closures following high intake days in the bar series indicate aging risk that automation will counter. |
""",
            "satisfaction": f"""
| Recommendations | Explanation | Benefits | Impact on Customers | Evidence & Graph Interpretation |
|-----------------|-------------|----------|---------------------|--------------------------------|
| Closure confirmation with next-step clarity | **Phase 1 – Content:** Send personalized closure emails summarizing actions taken, how to reopen, and a short mobile-friendly survey link.<br><br>**Phase 2 – Timing:** Trigger instantly on status change to avoid uncertainty.<br><br>**Phase 3 – Feedback:** Track survey comments and adjust messaging. | - Reduces follow-up calls because users understand what happened and what to do next without asking the desk.<br><br>- Increases trust since updates arrive exactly when the status changes and reflect the actual fix performed.<br><br>- Improves feedback volume and quality which surfaces service gaps earlier for remediation.<br><br>- Enhances perceived professionalism through consistent documentation. | CSAT uplift = Positive responses ÷ Total responses. With **{total_tickets_c:,}** closures, even a 20% response rate yields strong signal for service recovery. | Higher closure days (e.g., **{max_day_str}**) should correlate with increased survey volume after confirmations are enabled. |
| Post-resolution micro-surveys | **Phase 1 – Design:** Create a 15-second survey optimized for mobile with 2–3 focused prompts.<br><br>**Phase 2 – Target:** Trigger for categories with high volume or recent escalations.<br><br>**Phase 3 – Action:** Close the loop within 48 hours on negative feedback. | - Raises response rates by reducing friction which improves insight density per closed ticket.<br><br>- Identifies training needs by owner which leads to targeted coaching and faster uplift.<br><br>- Demonstrates a listening culture which strengthens sentiment and reduces repeat complaints.<br><br>- Enables rapid service recovery on outliers. | Feedback rate benchmark ≥ 40% for targeted closures. With daily average **{avg_tickets_c:.1f}**, expect **{round(avg_tickets_c*0.4)}** responses/day for targeted cohorts. | Owner/day distribution shows where targeted surveying will produce the richest signals. |
| Service recovery for delayed resolutions | **Phase 1 – Detect:** Flag breached tickets at closure.<br><br>**Phase 2 – Communicate:** Issue a brief apology with a reassurance of priority on the next request.<br><br>**Phase 3 – Review:** Track complaint reduction post-gesture. | - Recovers trust after delays which lowers complaint volume and escalations in subsequent interactions.<br><br>- Differentiates service quality through transparent acknowledgment which improves loyalty with key users.<br><br>- Teaches the system where friction occurs so upstream fixes can be prioritized.<br><br>- Reduces future handling time because recovered users are less likely to re-escalate. | Retention impact = Recovered cases ÷ Total breached. If 10 breached/day → recovering 30% = **3** positive turnarounds/day. | Fluctuation between average (**{avg_tickets_c:.1f}**) and peak (**{max_day_val}**) closure days highlights windows where recovery gestures matter most. |
""",
        }

        render_cio_tables("Number of Tickets Closed", cio_1b)

    # ---------------------- 1c ----------------------
    with st.expander("📌 Tickets Currently Open"):

        # Default flags so later logic never hits UnboundLocalError
        tickets_open_analysis_available = False
        closure_vs_opening_available = False

        # ---------- Open Tickets distribution ----------
        if {"incident_count", "service_category"} <= set(df_filtered.columns):
            count = (
                df_filtered.groupby("service_category")["incident_count"]
                .sum()
                .reset_index(name="open_tickets")
            )

            fig = px.bar(
                count,
                x="service_category",
                y="open_tickets",
                title="Open Tickets by Category",
                labels={"service_category": "Category", "open_tickets": "Number of Open Tickets"},
                color_discrete_sequence=BLUE_TONES,
            )
            st.plotly_chart(fig, use_container_width=True)

            if not count.empty:
                max_open = count.loc[count["open_tickets"].idxmax()]
                min_open = count.loc[count["open_tickets"].idxmin()]
                avg_open = float(count["open_tickets"].mean())

                # Safe helpers
                avg_open_safe = float(avg_open) if 'avg_open' in locals() else 0.0
                max_open_safe = int(max_open['open_tickets']) if 'max_open' in locals() else 0
                max_open_cat  = max_open['service_category'] if 'max_open' in locals() else 'N/A'

                st.markdown("### Analysis – Open Tickets by Category")
                st.write(
                    f"""What this graph is: A bar chart showing the current open ticket load aggregated by category.
X-axis: Service category.
Y-axis: Count of currently open tickets.

What it shows in your data:
Highest open category: {max_open_cat} with {max_open_safe} open.
Lowest open category: {min_open['service_category']} with {int(min_open['open_tickets'])} open.
Average open per category is {avg_open_safe:.1f}.

Overall, concentration in a few categories indicates bottleneck risk if not actively drained. A flatter spread means load is more manageable across teams.

How to read it operationally:
Swarm triggers: Categories significantly above average should trigger focus time or swarms.
Automation target: Repetitive categories with high opens are candidates for guided flows.
Aging lens: Pair this view with age buckets to ensure older items are prioritized.

Why this matters: Open inventory is where SLA risk lives. Keeping the mix balanced and actively drained protects customer experience."""
                )
                tickets_open_analysis_available = True
            else:
                st.info("✅ No open workload detected based on incident volumes.")
        else:
            st.warning("⚠️ Columns 'incident_count' and/or 'service_category' not found; skipping open tickets distribution.")

        # ---------- Closure vs Opening Rate ----------
        if "report_date" in df_filtered.columns:
            df_rate = df_filtered.copy()
            df_rate["date"] = pd.to_datetime(
                df_rate["report_date"], errors="coerce"
            ).dt.date

            opened = None
            closed_line = None

            if "incident_count" in df_rate.columns:
                opened = (
                    df_rate.groupby("date")["incident_count"]
                    .sum()
                    .reset_index(name="opened")
                )

            if "changes_successful" in df_rate.columns:
                closed_line = (
                    df_rate.groupby("date")["changes_successful"]
                    .sum()
                    .reset_index(name="closed")
                )

            if (opened is not None) and (closed_line is not None):
                rate = (
                    pd.merge(opened, closed_line, on="date", how="outer")
                    .fillna(0)
                    .sort_values("date")
                )

                fig2 = px.line(
                    data_frame=rate,
                    x="date",
                    y=["opened", "closed"],
                    title="Closure vs Opening Rate Over Time",
                    labels={
                        "value": "Number of Tickets",
                        "date": "Date",
                        "variable": "Metric",
                    },
                    color_discrete_sequence=BLUE_TONES,
                )
                st.plotly_chart(fig2, use_container_width=True)

                closure_vs_opening_available = True

                # --- Standardized Analysis ---
                if not rate.empty:
                    max_open_d = rate.loc[rate["opened"].idxmax()]
                    max_closed_d = rate.loc[rate["closed"].idxmax()]
                    avg_open_d = float(rate["opened"].mean())
                    avg_closed_d = float(rate["closed"].mean())

                    st.markdown("### Analysis – Closure vs Opening Rate Over Time")
                    st.write(
                        f"""What this graph is: A dual throughput chart comparing opened (inflow) and closed (outflow) tickets per day.
X-axis: Calendar date.
Y-axis: Counts for each daily metric (opened, closed).

What it shows in your data:
Largest intake day: {max_open_d['date']} with {int(max_open_d['opened'])} opened.
Largest closure day: {max_closed_d['date']} with {int(max_closed_d['closed'])} closed.
Averages over the period are {avg_open_d:.1f} opened/day vs {avg_closed_d:.1f} closed/day.

Overall, when the closed line persistently tracks below the opened line, the process is under-capacity and backlog grows; when it meets or exceeds openings, backlog burns down and stability improves.

How to read it operationally:
Gap = backlog delta: The vertical distance between lines is the daily backlog change.
Lead–lag: Closures peaking after openings implies reactive sprints, not smooth flow.
Recovery strength: Faster crossover after spikes = healthier system.
Control: Target near-parallel lines with minimal gap via routing, WIP limits, and surge capacity.

Why this matters: Balance between inflow and outflow is the heartbeat of the desk. Keeping outflow at or above inflow prevents aging, protects SLA, and steadies customer experience."""
                    )
            else:
                st.warning(
                    "⚠️ Need both 'incident_count' (opened) and 'changes_successful' (closed) to render the comparison."
                )
                closure_vs_opening_available = False
        else:
            st.warning("⚠️ Column 'report_date' not found; cannot compute closure vs opening rate.")
            closure_vs_opening_available = False

        # --- CIO Recommendations with ≥3 items each, expanded phases & benefits, real-value costs/evidence
        cio_recs = {"cost": "", "performance": "", "satisfaction": ""}

        if tickets_open_analysis_available and closure_vs_opening_available:
            # Use actual numbers where possible from prior calculations
            avg_open_val = avg_open_d if 'avg_open_d' in locals() else 0.0
            avg_closed_val = avg_closed_d if 'avg_closed_d' in locals() else 0.0
            max_open_val = int(max_open_d["opened"]) if 'max_open_d' in locals() else 0
            max_closed_val = int(max_closed_d["closed"]) if 'max_closed_d' in locals() else 0

            # Safe copies for open-by-category section above
            avg_open_safe = float(avg_open) if 'avg_open' in locals() else 0.0
            max_open_safe = int(max_open['open_tickets']) if 'max_open' in locals() else 0
            max_open_cat  = max_open['service_category'] if 'max_open' in locals() else 'N/A'

            cio_recs["cost"] = f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Rationalize low-impact open tickets via auto-closure nudges | **Phase 1 – Define:** Set an aging threshold and a two-step reminder cadence with a one-click reopen link for the requester.<br><br>**Phase 2 – Enforce:** Auto-close when no response arrives after the second nudge while tagging the case for quick reopen.<br><br>**Phase 3 – Tune:** Monitor reopen rate to keep false closes below 5%. | - Reduces admin touches on inactive tickets which frees analysts to work on fresh demand that is actually waiting.<br><br>- Shrinks visible queue clutter which improves prioritization and focus on high-impact items.<br><br>- Lowers overtime during spikes because stale work is removed automatically and analysts concentrate on true workload.<br><br>- Improves metric integrity since the queue reflects real work rather than old noise. | Hours saved = (# auto-closed × admin mins ÷ 60). Apply to categories above the open average of **{avg_open_safe:.1f}** per category. If 15% of **{max_open_safe}** in {max_open_cat} auto-close at **2 mins** each → **{round(max_open_safe*0.15*2/60,2)} hours** recovered. | Open mix shows **{max_open_cat}** at **{max_open_safe}** vs average **{avg_open_safe:.1f}**; the excess is ideal for low-risk auto-closure after nudges. |
| Automate Tier-0/Tier-1 fixes for repetitive categories | **Phase 1 – Map:** Identify top repetitive categories from the open distribution.<br><br>**Phase 2 – Build:** Implement guided flows or chatbots with screenshot prompts and field validation to collect the right info up front.<br><br>**Phase 3 – Measure:** Track deflection and resolution success weekly and expand. | - Cuts human minutes on simple issues which accelerates response for complex work and protects expert bandwidth.<br><br>- Reduces new ticket creation because users self-solve common tasks correctly the first time.<br><br>- Stabilizes queues during spikes because a meaningful share of inflow is deflected before it reaches analysts.<br><br>- Improves data completeness which speeds any remaining human handling. | Time avoided = (Tickets automated × avg handling mins). If **20%** of **{max_open_safe}** in {max_open_cat} deflect at **8 mins** each → **{round(max_open_safe*0.20*8/60,2)} hours** avoided for that category. | Category concentration in the open bar chart indicates strong automation fit anchored on the observed top bucket. |
| Shift and staff to observed inflow/outflow patterns | **Phase 1 – Analyze:** Use the dual chart to profile typical daily gap between opened and closed.<br><br>**Phase 2 – Align:** Adjust start times and break patterns so the closed line meets the opened line on known surge windows.<br><br>**Phase 3 – Review:** Re-baseline quarterly as patterns evolve. | - Reduces escalations by ensuring capacity comes online during hot windows rather than after the fact.<br><br>- Uses paid hours more effectively which lowers unit cost per ticket across the week.<br><br>- Keeps backlog flat during spikes which protects SLA and customer perception.<br><br>- Improves team morale by avoiding chronic late-day crunches. | Overtime savings = (Overtime hours avoided × hourly rate) when daily closes increase toward **{avg_open_val:.1f}** to match average opened **{avg_open_val:.1f}**. Gap at peak: opened **{max_open_val}** vs closed **{max_closed_val}**. | The dual series shows averages **{avg_open_val:.1f}** vs **{avg_closed_val:.1f}** and a peak gap of **{max_open_val - max_closed_val}** tickets, quantifying the staffing delta to cover. |
"""

            cio_recs["performance"] = f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| WIP limits by priority | **Phase 1 – Set limits:** Cap in-progress work per analyst per priority to stop context switching.<br><br>**Phase 2 – Visualize:** Expose WIP and limits on team boards.<br><br>**Phase 3 – Enforce:** Pull strictly when capacity is free. | - Increases focus which shortens cycle time and reduces error rates that create rework.<br><br>- Prevents over-commitment so throughput becomes steadier and more predictable.<br><br>- Improves SLA attainment by ensuring analysts complete work rather than start too much.<br><br>- Builds a sustainable rhythm that scales. | Throughput lift = Δ(tickets/day) × Avg handling mins ÷ 60. Target lift is the observed average gap **{(avg_open_val-avg_closed_val):.1f}** tickets/day. | Repeating gaps where opened > closed in the dual chart indicate over-WIP and context switching. |
| Aging guardrails with auto-escalation | **Phase 1 – Policy:** Define age thresholds per priority.<br><br>**Phase 2 – Automation:** Auto-notify and route to swarms when thresholds hit.<br><br>**Phase 3 – Governance:** Review aged inventory daily. | - Reduces mean age and breach rates which improves predictability of outflow.<br><br>- Unlocks stuck items faster because help arrives proactively.<br><br>- Protects critical users by accelerating high-priority items before they breach.<br><br>- Keeps the backlog curve from steepening after spikes. | Breach hours prevented = (# escalated pre-breach × avg overage hrs). If 8/day prevented with **1.5 hrs** overage → **12 hrs/day** protected. | Post-spike sections where the closed line trails opened signal exactly where aging control is needed. |
| Fast-lane for critical symptoms | **Phase 1 – Rules:** Define symptom keywords that route to a senior fast-lane.<br><br>**Phase 2 – Capacity:** Reserve expert bandwidth each day.<br><br>**Phase 3 – Audit:** Validate outcomes and refine keywords. | - Lowers time-to-restore for high-impact issues which protects key services and executives.<br><br>- Concentrates expertise on the work that benefits most which increases success rates.<br><br>- Reduces noise in general queues which helps overall speed.<br><br>- Builds stakeholder confidence during incidents. | Impact hours saved = (Δresolution hrs × critical ticket count). If 3 criticals/day save **1 hr** each → **3 hrs/day** returned. | Faster crossover after spikes is expected when criticals bypass congestion; current gap size indicates improvement headroom. |
"""

            cio_recs["satisfaction"] = f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Priority-aware proactive updates | **Phase 1 – Triggers:** When open inventory rises above **{avg_open_safe:.1f}** per category or opened>closed for the day, push status updates with next actions.<br><br>**Phase 2 – Cadence:** Increase update frequency for higher priorities.<br><br>**Phase 3 – Review:** Track complaint rate vs update cadence. | - Cuts inbound chaser calls because users receive timely clarity about progress and next steps.<br><br>- Raises perceived responsiveness which sustains trust even when teams are stretched.<br><br>- Helps VIPs feel seen, reducing escalation risk and negative sentiment.<br><br>- Sets realistic expectations that align with observed capacity. | Complaint handling minutes avoided = (Complaints avoided × avg minutes). If updates prevent **10** chasers/day at **6 mins** each → **60 mins/day** avoided. | When opened exceeds closed by **{(avg_open_val-avg_closed_val):.1f}** on average, proactive updates offset perception damage during the gap. |
| Self-service progress tracker | **Phase 1 – Build:** Expose live ticket stage in the portal including owner and next action.<br><br>**Phase 2 – Educate:** Add tooltips to explain each stage.<br><br>**Phase 3 – Improve:** Use feedback to refine content. | - Reduces uncertainty and frustration because users can self-check progress without contacting the desk.<br><br>- Encourages accurate user information, improving resolution speed and reducing back-and-forth.<br><br>- Increases CSAT by giving users transparency and control over their requests.<br><br>- Lowers inbound volume, freeing time for analysts. | Time saved = (Status calls avoided × avg call duration). If **12** calls/day avoided at **4 mins** → **48 mins/day** saved. | Elevated open counts relative to closes amplify uncertainty; transparency directly counters this effect in the observed pattern. |
| VIP assurance route | **Phase 1 – Identify:** Mark VIP and business-critical services.<br><br>**Phase 2 – Operate:** Auto-notify senior analysts and set stricter update cadence.<br><br>**Phase 3 – Audit:** Review VIP breaches weekly. | - Protects high-value relationships and revenue-sensitive workflows which reduces churn risk.<br><br>- Prevents high-impact escalations that otherwise consume many staff minutes.<br><br>- Improves perception among executives during incidents which supports confidence in IT.<br><br>- Creates clear accountability for critical users. | Escalation cost avoided = (# VIP escalations avoided × cost per escalation). If 2/day avoided at **30 mins** each → **1 hr/day** saved. | Peaks where opened outpaces closed are the riskiest windows for VIP dissatisfaction; the current gap quantifies the exposure. |
"""
        elif closure_vs_opening_available:
            avg_open_val = avg_open_d if 'avg_open_d' in locals() else 0.0
            avg_closed_val = avg_closed_d if 'avg_closed_d' in locals() else 0.0

            cio_recs["cost"] = f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Optimize staffing patterns | **Phase 1 – Analyze:** Size the daily opened vs closed gap.<br><br>**Phase 2 – Align:** Shift rosters to close the gap during hot windows.<br><br>**Phase 3 – Adjust:** Re-baseline quarterly. | - Lowers overtime and stabilizes queues during spikes because capacity is online when demand hits.<br><br>- Reduces breach risk by improving closure timeliness and keeping backlog flat.<br><br>- Improves unit cost per ticket through better utilization of paid hours.<br><br>- Increases predictability for stakeholders. | Savings = (Overtime hours reduced × hourly rate) as closed approaches **{avg_open_val:.1f}** opened/day from **{avg_closed_val:.1f}** baseline. | Dual chart shows opened avg **{avg_open_val:.1f}** vs closed avg **{avg_closed_val:.1f}**, quantifying the capacity delta. |
| Automate repetitive tasks | **Phase 1 – Identify:** Target categories that recur daily.<br><br>**Phase 2 – Build:** Deliver guided flows and macros.<br><br>**Phase 3 – Measure:** Track deflection and cycle time. | - Shrinks manual effort which lowers unit cost and preserves expert time.<br><br>- Smooths outflow relative to inflow during spikes which protects SLA.<br><br>- Reduces cognitive load and error rates which avoids rework.<br><br>- Improves customer speed for simple tasks. | Savings = (# tickets automated × avg handling cost). If **10**/day automated at **8 mins** each → **80 mins/day** saved. | Gaps where closed lags opened signal the need to deflect volume on those categories. |
"""

            cio_recs["performance"] = f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Process balancing | **Phase 1 – Compare:** Track opened vs closed daily.<br><br>**Phase 2 – Balance:** Redirect work so closed ≈ opened.<br><br>**Phase 3 – Sustain:** Monitor variance. | - Improves throughput stability across the week.<br><br>- Lowers aging risk after spikes by preventing accumulation.<br><br>- Improves SLA attainment through smoother flow.<br><br>- Enables more accurate planning. | Efficiency gain = (Closed ÷ Opened) × 100% movement toward parity from current **{(avg_closed_val/avg_open_val*100 if avg_open_val>0 else 0):.1f}%**. | Dual chart highlights the imbalance windows to fix. |
| Prioritize ticket routing | **Phase 1 – Rules:** Route recurring and critical tickets faster.<br><br>**Phase 2 – Monitor:** Watch reassignments and adjust.<br><br>**Phase 3 – Improve:** Iterate monthly. | - Shortens resolution times by reducing handoffs.<br><br>- Reduces queue length and aging tails through faster first-time-right.<br><br>- Improves predictability and stakeholder confidence.<br><br>- Stabilizes daily close rates. | Time saved = (Reassignments avoided × handoff mins). If **5** handoffs/day avoided at **6 mins** → **30 mins/day** saved. | Peaks in opened vs closed trends indicate routing friction causing lag. |
"""

            cio_recs["satisfaction"] = f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Customer assurance messaging | **Phase 1 – Plan:** Pre-draft messages for surge windows.<br><br>**Phase 2 – Trigger:** Send when opened>closed trend emerges.<br><br>**Phase 3 – Review:** Measure complaint rate. | - Reduces anxiety and perceived neglect because users receive honest timelines.<br><br>- Lowers complaint volume which frees analyst time for delivery work.<br><br>- Protects CSAT during stress periods by setting expectations.<br><br>- Builds trust through transparency. | Complaint minutes avoided = (# complaints avoided × avg mins). If **6** avoided/day at **5 mins** → **30 mins/day** saved. | Opened>closed gaps visible in the series align with negative perception risk that messaging mitigates. |
| Proactive surge communication | **Phase 1 – Forecast:** Use known peaks to pre-warn.<br><br>**Phase 2 – Educate:** Provide self-help links.<br><br>**Phase 3 – Follow-up:** Close the loop post-recovery. | - Prevents dissatisfaction through expectation setting before congestion starts.<br><br>- Reduces inbound chasers which keeps lines clear for high-impact issues.<br><br>- Keeps sentiment stable even when queues are longer.<br><br>- Encourages self-service where appropriate. | Value = (Complaints avoided × resolution cost). If **8** calls/day avoided at **4 mins** → **32 mins/day** saved. | Charted surge days define when to communicate; current pattern shows predictable windows. |
"""
        else:
            st.info("No recommendations related to open tickets or closure vs opening rate are available because the required data is missing.")

        # --- Render CIO tables ---
        if any(cio_recs.values()):
            render_cio_tables("Tickets Operational Analysis", cio_recs)

    # ---------------------- 1d ----------------------
    with st.expander("📌 Ticket Backlog (Unresolved Tickets)"):

        # Use available columns: report_date (timeline), incident_count (opened), changes_successful (closed)
        if ("report_date" in df_filtered.columns) and ({"incident_count", "changes_successful"} <= set(df_filtered.columns)):
            df_backlog = df_filtered.copy()

            # Parse report_date
            df_backlog["report_date_parsed"] = pd.to_datetime(
                df_backlog["report_date"], errors="coerce"
            ).dt.date

            # Opened = sum of incident_count by report_date
            opened = (
                df_backlog.groupby("report_date_parsed")["incident_count"]
                .sum()
                .reset_index(name="opened")
            )

            # Closed = sum of changes_successful by report_date
            closed_b = (
                df_backlog.groupby("report_date_parsed")["changes_successful"]
                .sum()
                .reset_index(name="closed")
            )

            # ✅ Merge timeline
            rate = (
                pd.merge(opened, closed_b, on="report_date_parsed", how="outer")
                .fillna(0)
                .sort_values("report_date_parsed")
            )

            # --- Backlog Calculation ---
            rate["backlog"] = (rate["opened"] - rate["closed"]).cumsum()

            # --- Graph: Backlog Trend ---
            fig_backlog = px.line(
                data_frame=rate,
                x="report_date_parsed",
                y="backlog",
                title="📈 Ticket Backlog Over Time",
                labels={
                    "backlog": "Cumulative Backlog (Unresolved Tickets)",
                    "report_date_parsed": "Date",
                },
                color_discrete_sequence=BLUE_TONES,
            )
            st.plotly_chart(fig_backlog, use_container_width=True, key="ticket_backlog")

            if not rate.empty:
                # --- Dynamic Insights from Data ---
                peak_backlog = rate.loc[rate["backlog"].idxmax()]
                latest_backlog = rate.iloc[-1]
                avg_backlog = float(rate["backlog"].mean())

                st.markdown("### Analysis – Ticket Backlog Over Time")
                st.write(
                    f"""What this graph is: A cumulative line showing the unresolved ticket backlog computed as the running difference between opened and closed.
X-axis: Calendar date.
Y-axis: Cumulative count of unresolved tickets.

What it shows in your data:
Backlog peak: {peak_backlog['report_date_parsed']} with {int(peak_backlog['backlog'])} unresolved.
Latest backlog: {latest_backlog['report_date_parsed']} with {int(latest_backlog['backlog'])} unresolved.
Average backlog level: {avg_backlog:.1f}.

Overall, a rising line indicates unresolved demand building up which increases SLA risk and user frustration. A flat or declining line indicates the team is closing at or above intake.

How to read it operationally:
Prioritization lens: Focus on the oldest and most impactful items first to bend the curve down fastest.
Capacity lens: If the line rises after predictable intake spikes, add surge capacity or deflection at those times.
Quality lens: Pair backlog movement with rework or reassignment rates to find friction.

Why this matters: Backlog is deferred pain. Keeping it controlled protects SLA, response time, and customer satisfaction."""
                )

                # --- Dynamic Recommendation Tables (≥3 each, expanded phases & benefits, real values) ---
                cio_1d = {
                    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Backlog burn-down sprints prioritised by **age × business impact** | **Phase 1 – Select:** Build a sprint backlog of oldest and highest-impact tickets using age and business criticality.<br><br>**Phase 2 – Execute:** Run focused 2–3 hour swarms that pull only from this lane until finished.<br><br>**Phase 3 – Review:** Track Δbacklog and SLA risk reduction to schedule the next sprint. | - Delivers rapid reduction of carry-over work which immediately lowers SLA exposure and clears analyst headspace.<br><br>- Concentrates effort where value is highest so each hour closed returns outsized business benefit.<br><br>- Establishes a repeatable recovery mechanism after spikes which keeps stakeholders confident.<br><br>- Improves morale because visible wins are achieved daily. | Hours released = (Tickets closed in sprint × Avg resolution hrs). If a sprint closes **15** items at **0.8 hr** each → **12 hrs** returned. | Backlog peaked at **{int(peak_backlog['backlog'])}** on **{peak_backlog['report_date_parsed']}**; oldest-first targeting bends the curve fastest from this peak. |
| Deduplicate and merge linked tickets | **Phase 1 – Detect:** Use similarity on title/description to identify duplicates.<br><br>**Phase 2 – Link:** Merge to a parent incident and enforce one-source updates.<br><br>**Phase 3 – Close:** One-click child closures when the parent resolves with consistent comms. | - Eliminates repeated effort across multiple tickets reporting the same issue which returns many minutes quickly.<br><br>- Improves user communication because every related requester receives aligned status and outcomes.<br><br>- Simplifies reporting by collapsing noise into a single parent which helps true trend detection.<br><br>- Reduces escalations because updates propagate uniformly. | Time saved = (Duplicates linked × (Avg handling mins − Batch close mins)). If **10** duplicates/day save **5 mins** each → **50 mins/day** saved. | Sustained backlog above **{avg_backlog:.1f}** suggests repeated issues likely exist that consolidation will neutralize. |
| Automate low-complexity backlog categories | **Phase 1 – Identify:** Tag backlog items with known fixes and low risk.<br><br>**Phase 2 – Automate:** Run guided automation during off-peak windows to drain the queue.<br><br>**Phase 3 – Expand:** Scale categories as success is proven. | - Reduces manual cost while clearing easy items which accelerates recovery after spikes.<br><br>- Preserves expert time for complex incidents which lifts overall quality and SLA adherence.<br><br>- Stabilizes daily outflow so the backlog line flattens sooner.<br><br>- Creates a sustainable night-shift/low-load drain capability. | Hours avoided = (Automated backlog tickets × Avg handling mins ÷ 60). If **12** items automated/night at **10 mins** → **2 hrs/night** saved. | Average backlog level **{avg_backlog:.1f}** indicates a stable pool of simple items suitable for automation. |
""",
                    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Oldest-first within SLA risk (OF-SLAR) | **Phase 1 – Score:** Rank by age and time-to-breach.<br><br>**Phase 2 – Pull:** Enforce strict pull from the top of this list across owners.<br><br>**Phase 3 – Audit:** Review breaches and adjust thresholds. | - Lowers mean age and breach rate simultaneously which improves flow stability.<br><br>- Prevents silent aging that surprises stakeholders and damages credibility.<br><br>- Makes daily wins visible which sustains team momentum and predictability.<br><br>- Reduces firefighting by eliminating lurking tails. | SLA hours protected = (# at-risk resolved pre-breach × Avg overage hrs). If **6** at-risk/day prevented at **1.5 hrs** → **9 hrs/day** protected. | Latest backlog **{int(latest_backlog['backlog'])}** shows volume where OF-SLAR will immediately shift outcomes. |
| Control-limit trigger with intake gating | **Phase 1 – Limits:** Set an upper control limit for backlog based on historical mean and variance.<br><br>**Phase 2 – Gate:** When breached, deflect non-urgent intake to self-service or callback scheduling.<br><br>**Phase 3 – Recover:** Lift gating when backlog returns under control. | - Prevents runaway queues during spikes which contains SLA damage within acceptable bands.<br><br>- Protects analysts from overload which maintains quality and reduces error-driven rework.<br><br>- Returns the line under control faster which protects executive confidence.<br><br>- Creates a clear rule for when to activate surge levers. | Overtime avoided = (Hours not added to queue × overtime rate). If gating prevents **8 hrs** overtime/week, cost avoidance is directly realized. | On **{peak_backlog['report_date_parsed']}**, backlog exceeded typical levels, identifying a practical gating trigger point. |
| Daily 20-minute “aging swarm” | **Phase 1 – Cadence:** Schedule a rotating micro-squad daily.<br><br>**Phase 2 – Target:** Clear items older than a threshold (e.g., p80 age).<br><br>**Phase 3 – Track:** Measure Δold-ticket count after each swarm. | - Produces quick visible wins which reduces aging tails day by day.<br><br>- Builds shared knowledge so similar future cases are solved faster across the team.<br><br>- Keeps morale up because progress is obvious and cumulative.<br><br>- Shrinks variability in daily closure counts. | Δp80 age hours × (# tickets above threshold). If **10** items/day reduce age by **0.4 hr** → **4 hrs/day** aging removed. | Expect sharper downward steps in the backlog curve following swarm sessions, accelerating from the observed average of **{avg_backlog:.1f}**. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Backlog-aware ETA and apology cadence | **Phase 1 – Detect:** When backlog exceeds average **{avg_backlog:.1f}**, enroll affected users into proactive ETA updates.<br><br>**Phase 2 – Communicate:** Provide causes of delay and next steps with sincere apologies where appropriate.<br><br>**Phase 3 – Learn:** Capture response sentiment and iterate. | - Reduces frustration among waiting users which lowers complaint volume and repeat contacts.<br><br>- Improves perceived fairness because users see honest timelines and ownership of delays.<br><br>- Encourages cooperation when additional information is needed to progress cases.<br><br>- Restores confidence after stressful spikes. | Complaints avoided × Avg handling minutes. If **5** complaints/day avoided at **6 mins** → **30 mins/day** saved. | With current backlog **{int(latest_backlog['backlog'])}**, silence erodes trust; targeted updates stabilize sentiment until the curve declines. |
| VIP/critical fast-lane through backlog | **Phase 1 – Segmentation:** Flag VIPs and critical services in the backlog.<br><br>**Phase 2 – Routing:** Bypass normal queues with senior owner assignment.<br><br>**Phase 3 – Oversight:** Daily review of VIP aging. | - Protects revenue-sensitive work which reduces escalation impact and executive noise.<br><br>- Shortens recovery for high-impact cases which improves overall business continuity.<br><br>- Demonstrates priority discipline which boosts stakeholder confidence.<br><br>- Reduces churn risk among key users. | Churn/impact hours avoided where tracked. If **2** VIP cases/day save **1 hr** each → **2 hrs/day** business impact protected. | Peak backlog date **{peak_backlog['report_date_parsed']}** is the riskiest window for VIP delays; fast-lane coverage targets this exposure. |
| “Waiting on customer” clock pause | **Phase 1 – Policy:** Pause SLA clocks when waiting on requester input and display the state clearly.<br><br>**Phase 2 – UX:** Add portal prompts and reminders to speed responses.<br><br>**Phase 3 – Audit:** Ensure accurate tagging to prevent misuse. | - Prevents artificial breaches which makes metrics fair and credible to leadership and customers.<br><br>- Reduces analyst time spent defending metrics so time is reinvested into resolution work.<br><br>- Encourages timely responses from users because the paused state is visible and actionable.<br><br>- Improves forecasting accuracy since SLA now reflects controllable work. | Breach hours avoided = (Re-categorized waits × overage hrs). If **4** tickets/day avoid **1 hr** overage → **4 hrs/day** breach time prevented. | If backlog includes many “awaiting info” items, pausing the clock prevents misleading growth signals and aligns with observed queue composition. |
""",
                }

                render_cio_tables("Ticket Backlog (Unresolved Tickets)", cio_1d)
            else:
                st.info("No timeline could be constructed from the available data; backlog graph not rendered.")
        else:
            st.warning("⚠️ Need 'report_date', 'incident_count' (opened), and 'changes_successful' (closed) columns for backlog analysis.")
