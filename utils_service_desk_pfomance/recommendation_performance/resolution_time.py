import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import plotly.graph_objects as go

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def resolution_time(df_filtered):

#-------------------------------------------------------------------------------------------------------------------------
    #1. Average Response Time
    with st.expander("📌 Average Response Time"):
        if "response_time_elapsed" in df_filtered.columns:
            # ✅ Convert timedelta → minutes
            if pd.api.types.is_timedelta64_dtype(df_filtered["response_time_elapsed"]):
                df_filtered["response_time_minutes"] = (
                    df_filtered["response_time_elapsed"].dt.total_seconds() / 60
                )
            else:
                df_filtered["response_time_minutes"] = df_filtered["response_time_elapsed"]

            # ---------- MOVED: compute stats immediately so they're available for all analyses ----------
            avg_response = df_filtered["response_time_minutes"].mean()
            max_response = df_filtered["response_time_minutes"].max()
            min_response = df_filtered["response_time_minutes"].min()
            # -----------------------------------------------------------------------------------------

            # Line Chart - Response Time Trend
            if "created_time" in df_filtered.columns:
                line_fig = px.line(
                    df_filtered,
                    x="created_time",
                    y="response_time_minutes",
                    title="Response Time Over Time",
                    labels={"response_time_minutes": "Response Time (minutes)", "created_time": "Created Date"},
                )
                st.plotly_chart(line_fig, use_container_width=True)

                # Dynamic Line Chart Analysis
                st.markdown("#### Analysis of Response Time Over Time")
                st.write(f"""
                **What this graph is:** A time-series chart showing **response time per ticket** over time.  
                - **X-axis:** Created Date.  
                - **Y-axis:** Response Time (minutes).

                **What it shows in your data:**  
                The dataset records an **average response time of {avg_response:.2f} minutes**.  
                The **fastest response** observed is **{min_response:.2f} minutes**, while the **slowest response** reaches **{max_response:.2f} minutes**.

                Overall, periods of spikes reflect **workload pressure or process delays**, while flatter segments imply **stable handling**.

                **How to read it operationally:**  
                1) **Peaks:** Investigate high points for staffing gaps, triage delays, or incidents.  
                2) **Plateaus:** Use as baselines to set realistic SLA targets.  
                3) **Downswings:** Capture what worked (playbooks, routing, staffing) and standardize.  
                4) **Mix:** Compare peaks to intake/load to confirm capacity fit.

                **Why this matters:** Response time is the **first impression** of service quality. Shorter, steadier response times reduce escalations, protect SLA, and improve satisfaction.
                """)


            # Box Plot - Spread of Response Times
            box_fig = px.box(
                df_filtered,
                y="response_time_minutes",
                title="Response Time Distribution (Box Plot)",
                labels={"response_time_minutes": "Response Time (minutes)"},
            )
            st.plotly_chart(box_fig, use_container_width=True)

            st.markdown("#### Analysis of Response Time Distribution")
            st.write(f"""
            **What this graph is:** A distribution chart showing **response time spread** across tickets.  
            - **X-axis:** (Not applicable).  
            - **Y-axis:** Response Time (minutes).

            **What it shows in your data:**  
            The **median response** is **{df_filtered["response_time_minutes"].median():.2f} minutes**, with the middle half of tickets spanning the interquartile range.  
            Outliers above roughly **{max_response*0.8:.2f} minutes** indicate **unusually slow responses**.

            Overall, a wider box and many outliers signal **inconsistent handling** and potential **process variation**.

            **How to read it operationally:**  
            1) **Peaks:** Target outliers for root-cause (handoffs, vendor waits).  
            2) **Plateaus:** Narrow boxes suggest consistent execution — preserve these practices.  
            3) **Downswings:** After changes, a tighter spread confirms improvement.  
            4) **Mix:** Pair with agent/category cuts to locate variability sources.

            **Why this matters:** Compressing the spread (fewer outliers) **lowers the mean**, stabilizes SLA, and lifts customer trust.
            """)

            # Histogram - Distribution Shape
            hist_fig = px.histogram(
                df_filtered,
                x="response_time_minutes",
                nbins=30,
                title="Distribution of Response Times (Histogram)",
                labels={"response_time_minutes": "Response Time (minutes)"},
            )
            st.plotly_chart(hist_fig, use_container_width=True)

            st.markdown("#### Analysis of Response Time Distribution (Histogram)")
            st.write(f"""
            **What this graph is:** A frequency chart showing **how often each response time range occurs**.  
            - **X-axis:** Response Time (minutes).  
            - **Y-axis:** Ticket count per bin.

            **What it shows in your data:**  
            The most common response time cluster is around **{df_filtered["response_time_minutes"].mode()[0]:.2f} minutes**.  
            A **right-hand tail** confirms a subset of **delayed responses**.

            Overall, a tall early cluster with a long tail means **most tickets are quick**, but **a few delayed cases** inflate averages.

            **How to read it operationally:**  
            1) **Peaks:** The tallest bins represent the dominant operating point — protect it.  
            2) **Plateaus:** Broad distributions mean inconsistent flow — standardize playbooks.  
            3) **Downswings:** After interventions, tail shrinkage validates improvement.  
            4) **Mix:** Cross-filter by category/agent to pinpoint where the tail originates.

            **Why this matters:** Trimming the tail (slow cases) produces **big wins** in SLA compliance and user satisfaction.
            """)
            
            # ✅ Dynamic statistics (now safe with floats)
            st.markdown(f"""
            ** Key Stats:**
            - Average Response Time: **{avg_response:.2f} minutes**
            - Fastest Response: **{min_response:.2f} minutes**
            - Slowest Response: **{max_response:.2f} minutes**
            """)


            st.write(
                f"""
                - The **average response time** is **{avg_response:.2f} minutes**.  
                - The **fastest response recorded** was **{min_response:.2f} minutes**, 
                while the **longest delay** was **{max_response:.2f} minutes**.  
                - Response times fluctuate, with certain periods reflecting delays that likely impact customer satisfaction.  
                - Outliers suggest inconsistent handling across different agents or issues.  
                - Lower response times reflect efficient initial engagement.  
                """
            )

            cio_response = {
                "cost": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |---|---|---|---|---|
            | **Automate initial acknowledgment** | **Phase 1 – Configure Triggers:** Set event rules so every new ticket gets an instant auto-ack with ticket ID and ETA window. <br><br>**Phase 2 – Personalize by Type:** Templates per category/priority with self-service links to reduce duplicate “status check” contacts. <br><br>**Phase 3 – Optimize:** Track open rate and duplicate-ticket reduction monthly and iterate wording/timing. | • Reduces repeated manual acknowledgments during peak periods.<br><br>• Decreases early anxiety that drives follow-up contacts.<br><br>• Standardizes first contact quality even when queues are busy. | **Savings** = minutes_saved_per_ticket × {len(df_filtered)} tickets × rate. Use the observed mean **{avg_response:.2f} min** as the baseline for measurable reduction. | Line shows spikes and boxplot’s tail; auto-ack dampens perceived delay where responses reach **{max_response:.2f} min**. |
            | **Skill-based smart routing** | **Phase 1 – Map Skills:** Link frequent categories to expert queues. <br><br>**Phase 2 – Auto-Assign:** Use rules/ML that factor availability and queue depth to prevent ping-pong. <br><br>**Phase 3 – Audit:** Quarterly misroute review → micro-training or rule updates. | • Cuts reassignment loops that inflate first response time.<br><br>• Improves first-touch accuracy for complex categories.<br><br>• Stabilizes variability across shifts and teams. | **Hours Saved** = reassignment_minutes/60 × tickets_rerouted × rate. Upper-tail cases near **{max_response:.2f} min** indicate avoidable routing latency. | Histogram shows a right-tail cluster; mismatched assignment is a common driver of the slow cohort. |
            | **Peak-window staffing & overlaps** | **Phase 1 – Detect Peaks:** Use response time spikes to identify day/hour windows. <br><br>**Phase 2 – Stagger Shifts:** Add 30–60 min overlaps before expected peaks. <br><br>**Phase 3 – Rebalance Monthly:** Compare planned vs actual and nudge coverage. | • Shrinks peak delays that create SLA risk.<br><br>• Converts overtime into regular staffed minutes.<br><br>• Improves predictability under recurring demand spikes. | **Savings** = overtime_hours_avoided × hourly_rate. Difference between peak **{max_response:.2f} min** and mean **{avg_response:.2f} min** sizes the gap. | Time-series peaks mark under-coverage windows; flattening those lowers average and tail. |
            | **First-question macros & forms** | **Phase 1 – Standardize:** Capture must-ask fields by category (serial, site, access). <br><br>**Phase 2 – Embed:** Guided forms/macros in intake and first reply. <br><br>**Phase 3 – Measure:** Rework cycles and clarification threads. | • Reduces back-and-forth and clarification loops.<br><br>• Speeds up triage by collecting complete data early.<br><br>• Lowers handle minutes per ticket for high-volume categories. | **Minutes Saved** = (clarification_threads_reduced × avg_minutes_per_thread). Use median vs mean gap to estimate avoidable rework. | Boxplot shows spread (median **{df_filtered["response_time_minutes"].median():.2f} min** vs mean **{avg_response:.2f} min**), implying rework inflation. |
            """,
                "performance": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |---|---|---|---|---|
            | **Live SLA timers & breach alerts** | **Phase 1 – Define Targets:** Convert policy to per-ticket timers. <br><br>**Phase 2 – Instrument:** Dash tiles + T-minus alerts at 80/90% of SLA. <br><br>**Phase 3 – Cadence:** Weekly breach review with cause codes. | • Moves work from reactive chasing to proactive control.<br><br>• Lifts on-time responses for tight priorities.<br><br>• Creates clear evidence for coaching and audits. | **SLA%** = tickets_within_SLA / total. Use slowest **{max_response:.2f} min** to identify breach-prone windows. | Spikes in the time-series align with risk; alerting narrows variance. |
            | **Micro-training for first responders** | **Phase 1 – Diagnose:** Response time by agent/category; find lagging cohorts. <br><br>**Phase 2 – Drill:** 15-minute scenario sessions + checklists. <br><br>**Phase 3 – Validate:** Re-measure and publish best-practice snippets. | • Compresses the right tail of slow responses.<br><br>• Raises baseline speed without additional headcount.<br><br>• Lowers escalation volume by improving first touch. | **ROI** = (minutes_saved × wage_rate) − training_cost. Fastest **{min_response:.2f} min** shows attainable standard. | Variability in boxplot suggests skill spread across staff. |
            | **Workload balance dashboard** | **Phase 1 – Expose:** Per-agent queue/WIP and SLA clocks. <br><br>**Phase 2 – Reassign:** Alerts on overload with one-click rebalance. <br><br>**Phase 3 – Track:** Pre/post variance in response time. | • Prevents starving tickets behind overloaded agents.<br><br>• Smooths response time across the team.<br><br>• Protects SLAs during intake spikes. | **Time Saved** = idle_or_wait_minutes_reduced × rate. | Histogram unevenness flags imbalance driving long waits. |
            """,
                "satisfaction": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
            |---|---|---|---|---|
            | **Proactive updates on delays** | **Phase 1 – Triggers:** Notify when response > baseline or awaiting info. <br><br>**Phase 2 – Templates:** Clear ETA and next step with self-service links. <br><br>**Phase 3 – Feedback:** CSAT on delayed cases. | • Reduces complaint volume from users waiting in silence.<br><br>• Lowers repeated “any update?” inquiries.<br><br>• Improves perceived responsiveness during busy periods. | **Avoided contacts** = inquiries_deflected × handling_cost. Tail above ~**{(max_response*0.8):.2f} min** indicates where to trigger. | Boxplot tail and histogram right-tail show who would benefit most from proactive comms. |
            | **Personalized first contact** | **Phase 1 – Context:** Pull user profile and asset data. <br><br>**Phase 2 – Tone:** Short, friendly, confirm understanding. <br><br>**Phase 3 – Review:** CSAT by template. | • Reduces clarification loops by aligning on facts early.<br><br>• Speeds initial progress with accurate context.<br><br>• Improves CSAT for first-touch interactions. | **CSAT Gain** = ΔCSAT × tickets. | Median vs mean gap implies preventable clarification loops. |
            | **Self-service status tracking** | **Phase 1 – Expose:** Stage, owner and ETA in portal. <br><br>**Phase 2 – Notify:** Automatic updates for ETA changes. <br><br>**Phase 3 – Measure:** Views vs inbound status calls. | • Deflects routine status calls to the portal.<br><br>• Increases user sense of control for in-progress cases.<br><br>• Smooths demand during high-volume days. | **Deflection** = calls_reduced × handling_cost; focus on days with **{max_response:.2f} min** peaks. | Time-series peaks correlate with status-check demand. |
            """
            }


            # ✅ Render CIO Tables
            render_cio_tables("Average Response Time", cio_response)

        else:
            st.warning("⚠️ Column 'response_time_elapsed' not found in uploaded dataset.")

#-----------------------------------------------------------------------------------------------------------
    # 2. Ticket Resolution Performance
    with st.expander("📌 Average Resolution Time"):
        if "resolution_time" in df_filtered.columns and "created_time" in df_filtered.columns:
            # Ensure created_date for grouping
            df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date

            # If resolution_time is a timedelta, convert to hours; otherwise assume numeric hours
            if pd.api.types.is_timedelta64_dtype(df_filtered["resolution_time"]):
                df_filtered["resolution_time_hours"] = df_filtered["resolution_time"].dt.total_seconds() / 3600.0
            else:
                df_filtered["resolution_time_hours"] = pd.to_numeric(df_filtered["resolution_time"], errors="coerce")

            # Guard: drop NA resolution_time_hours for calculations/plots
            df_res = df_filtered.dropna(subset=["resolution_time_hours", "created_date"]).copy()

            # --- Prepare aggregated trend
            res_trend = df_res.groupby("created_date")["resolution_time_hours"].mean().reset_index().sort_values("created_date")

            # --- Graph 1: Line Chart (Resolution time trend)
            fig_line = px.line(
                res_trend,
                x="created_date",
                y="resolution_time_hours",
                title="Average Resolution Time Over Time",
                markers=True,
                labels={"created_date": "Created Date", "resolution_time_hours": "Average Resolution Time (hours)"}
            )
            st.plotly_chart(fig_line, use_container_width=True)

            # --- Detailed analysis for Line Chart
            st.markdown("#### Analysis of Average Resolution Time Over Time (Line Chart)")
            if not res_trend.empty:
                overall_avg = res_trend["resolution_time_hours"].mean()
                first_row = res_trend.iloc[0]
                last_row = res_trend.iloc[-1]
                pct_change = ((last_row["resolution_time_hours"] - first_row["resolution_time_hours"]) / max(first_row["resolution_time_hours"], 1e-9)) * 100
                peak_row = res_trend.loc[res_trend["resolution_time_hours"].idxmax()]
                trough_row = res_trend.loc[res_trend["resolution_time_hours"].idxmin()]
                st.write(f"""
                **What this graph is:** A time-series chart showing **average resolution time per day**.  
                - **X-axis:** Created Date.  
                - **Y-axis:** Average Resolution Time (hours).

                **What it shows in your data:**  
                Overall mean is **{overall_avg:.2f} hours**. Earliest day **{first_row['created_date']}** averages **{first_row['resolution_time_hours']:.2f} hrs**, latest day **{last_row['created_date']}** averages **{last_row['resolution_time_hours']:.2f} hrs**.  
                Change from first to last is **{pct_change:.1f}%**. Peak is **{peak_row['created_date']}** at **{peak_row['resolution_time_hours']:.2f} hrs**; trough is **{trough_row['created_date']}** at **{trough_row['resolution_time_hours']:.2f} hrs**.

                Overall, rising segments indicate **capacity constraints or complex incidents**, while declines indicate **process gains or lighter load**.

                **How to read it operationally:**  
                1) **Peaks:** Schedule post-incident reviews; tighten escalations and runbooks.  
                2) **Plateaus:** Use as steady-state baselines for planning.  
                3) **Downswings:** Capture the practices responsible (keep doing those).  
                4) **Mix:** Compare with intake to confirm throughput vs demand.

                **Why this matters:** Resolution time maps directly to **user downtime and cost**. Lowering it reduces penalties, churn, and operational drag.
                """)

            else:
                st.info("No resolution time trend data to analyze.")

            # --- Graph 2: Box Plot (Distribution of resolution times)
            fig_box = px.box(
                df_res,
                y="resolution_time_hours",
                points="outliers",
                title="Distribution of Resolution Times (Outliers Highlighted)",
                labels={"resolution_time_hours": "Resolution Time (hours)"}
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # --- Detailed analysis for Box Plot
            st.markdown("#### Analysis of Distribution of Resolution Times (Box Plot)")
            if not df_res["resolution_time_hours"].empty:
                q1 = df_res["resolution_time_hours"].quantile(0.25)
                median = df_res["resolution_time_hours"].median()
                q3 = df_res["resolution_time_hours"].quantile(0.75)
                iqr = q3 - q1
                upper_fence = q3 + 1.5 * iqr
                outliers_count = (df_res["resolution_time_hours"] > upper_fence).sum()
                st.write(f"""
                **What this graph is:** A distribution chart showing **spread and outliers in resolution time**.  
                - **X-axis:** (Not applicable).  
                - **Y-axis:** Resolution Time (hours).

                **What it shows in your data:**  
                Q1 = **{q1:.2f} hrs**, median = **{median:.2f} hrs**, Q3 = **{q3:.2f} hrs** (IQR = **{iqr:.2f} hrs**).  
                There are **{outliers_count}** outlier day(s) above **{upper_fence:.2f} hrs**.

                Overall, the right-skew and outliers imply **a minority of slow cases** lifting the average.

                **How to read it operationally:**  
                1) **Peaks:** Audit outliers for dependency or escalation delays.  
                2) **Plateaus:** A tighter box implies stable operations — standardize it.  
                3) **Downswings:** After fixes, fewer outliers confirm impact.  
                4) **Mix:** Break down by category/priority to localize variability.

                **Why this matters:** Compressing spread (fewer extremes) raises predictability, improves SLA adherence, and reduces fire-fighting.
                """)

            else:
                st.info("Insufficient resolution time values to build a box plot analysis.")

            # --- Graph 3: Bar Chart (Resolution time by category)
            if "category" in df_res.columns:
                res_by_cat = df_res.groupby("category")["resolution_time_hours"].mean().reset_index().sort_values("resolution_time_hours", ascending=False)
                fig_bar = px.bar(
                    res_by_cat,
                    x="category",
                    y="resolution_time_hours",
                    text="resolution_time_hours",
                    title="Average Resolution Time by Category",
                    labels={"resolution_time_hours": "Avg Resolution Time (hours)", "category": "Category"}
                )
                fig_bar.update_traces(texttemplate='%{text:.2f}', textposition="outside")
                st.plotly_chart(fig_bar, use_container_width=True)

                # --- Detailed analysis for Bar Chart
                st.markdown("#### Analysis of Average Resolution Time by Category (Bar Chart)")
                if not res_by_cat.empty:
                    top_cat = res_by_cat.iloc[0]
                    bottom_cat = res_by_cat.iloc[-1]
                    overall_mean_cat = res_by_cat["resolution_time_hours"].mean()
                    st.write(f"""
                    **What this graph is:** A category comparison showing **average resolution time per category**.  
                    - **X-axis:** Category.  
                    - **Y-axis:** Average Resolution Time (hours).

                    **What it shows in your data:**  
                    Highest average: **{top_cat['category']}** at **{top_cat['resolution_time_hours']:.2f} hrs**.  
                    Lowest average: **{bottom_cat['category']}** at **{bottom_cat['resolution_time_hours']:.2f} hrs**.  
                    Overall category mean: **{overall_mean_cat:.2f} hrs**.

                    Overall, high-average categories likely indicate **complex work or cross-team dependencies**, while low ones reflect **well-tooled flows**.

                    **How to read it operationally:**  
                    1) **Peaks:** Prioritize improvement for top-avg categories (playbooks, automation).  
                    2) **Plateaus:** Maintain practices in steady performers.  
                    3) **Downswings:** Track whether changes bring long-avg categories down.  
                    4) **Mix:** Pair with volume to size total time savings.

                    **Why this matters:** Targeting the **slowest categories** yields the **largest time and cost reduction** for the desk.
                    """)

                else:
                    st.info("No category-level resolution data available for analysis.")
            else:
                st.info("Category column not present — skipping category breakdown chart and analysis.")

            # --- Overall Dynamic Summary (integrated decision view)
            st.markdown("### Integrated Findings & Recommendation Lead")
            st.write(f"""
            - Overall average resolution time (all tickets): **{df_res['resolution_time_hours'].mean():.2f} hours**.  
            - Observed issues: right-skewed distribution with **{(df_res['resolution_time_hours'] > df_res['resolution_time_hours'].quantile(0.75) + 1.5*(df_res['resolution_time_hours'].quantile(0.75)-df_res['resolution_time_hours'].quantile(0.25))).sum()}** extreme outliers.  
            - Immediate actions: investigate the top peak dates and top categories identified above, run RCA (root-cause analysis) for the outlier tickets, and implement targeted training or vendor follow-ups to remove bottlenecks.
            """)

            # --- CIO Tables (kept unchanged content but placed inside expanders using helper)
            cio_2b = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Automate repetitive fixes | **Phase 1 – Identify:** Mine commands/runbooks used repeatedly with prerequisites and rollback. <br><br>**Phase 2 – Build & Gate:** Scripts with validation and logging plus approvals for sensitive steps. <br><br>**Phase 3 – Deploy & Tune:** Roll out in low-risk windows and refine based on success metrics. | • Converts repeated manual steps into near zero-touch execution.<br><br>• Reduces variance across agents for the same issues.<br><br>• Scales instantly during peak demand without extra staffing. | **Savings** = avg_minutes_saved/60 × tickets_eligible × rate. Baseline mean = **{df_res['resolution_time_hours'].mean():.2f} h**; tail beyond **{upper_fence:.2f} h** shows room. | Box plot: Q1 **{q1:.2f}**, median **{median:.2f}**, Q3 **{q3:.2f}**, tail > **{upper_fence:.2f} h** with **{outliers_count}** outlier days. |
| Outsource non-core slow categories | **Phase 1 – Select:** Use bar chart outliers to find high-time and low-strategic categories. <br><br>**Phase 2 – Contract:** Define clear SLAs, inputs and escalation paths. <br><br>**Phase 3 – Govern:** Monthly scorecards with re-bid triggers for persistent misses. | • Avoids expensive internal hours for non-strategic work.<br><br>• Accelerates overall flow by removing chronic long cases.<br><br>• Converts fixed cost into variable cost aligned to volume. | **Net Savings** = (hours_saved_internal − vendor_hours) × rate. Target categories like **{top_cat['category']}** at **{top_cat['resolution_time_hours']:.2f} h** avg. | Category bar: worst **{top_cat['category']}** vs best **{bottom_cat['category']}** (**{bottom_cat['resolution_time_hours']:.2f} h**). |
| Closure simplification & prefill | **Phase 1 – Map:** Remove redundant fields and approvals. <br><br>**Phase 2 – Prefill:** Pull intake and CMDB fields into the closure form. <br><br>**Phase 3 – Verify:** Measure the reduction in closure minutes. | • Cuts admin minutes per ticket at the end of the process.<br><br>• Speeds finalization so throughput rises in busy periods.<br><br>• Reduces reopen risk caused by missing closure information. | **Hours Saved** = (closure_mins_baseline − closure_mins_new)/60 × N_tickets. Use total tickets plotted = **{len(df_res)}**. | Spread between median **{median:.2f} h** and mean **{df_res['resolution_time_hours'].mean():.2f} h** suggests admin friction. |
| Vendor dependency acceleration | **Phase 1 – Tag:** Identify categories with vendor waits. <br><br>**Phase 2 – Escalation SLAs:** Add T-1 and T-0 vendor actions. <br><br>**Phase 3 – Review:** Monthly vendor latency report with actions. | • Shortens long stalls triggered by third-party delays.<br><br>• Reduces extreme outliers that drive breaches.<br><br>• Protects SLA performance during external dependencies. | **Penalty Avoided** = breaches_reduced × penalty_per_breach. Use outliers above **{upper_fence:.2f} h** as breach-risk proxy. | Boxplot tail and peak dates in the line trend indicate vendor-linked delays. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Early swarming on predicted outliers | **Phase 1 – Predict:** Flag cases above median plus two standard deviations at intake. <br><br>**Phase 2 – Swarm:** Engage a multi-skill team from the first hour. <br><br>**Phase 3 – Close loop:** Document blockers removed and keep playbooks updated. | • Compresses the right tail of cycle times for complex cases.<br><br>• Reduces SLA breaches on high-risk tickets.<br><br>• Improves predictability of daily throughput. | **Hours Reduced** = (p90 − target_p90) × count_p90. Current p90≈**{df_res['resolution_time_hours'].quantile(0.9):.2f} h**. | Gap median **{median:.2f} h** → p90 **{df_res['resolution_time_hours'].quantile(0.9):.2f} h** shows blocker load. |
| Problem classification & taxonomy | **Phase 1 – Standardize:** Create concise, non-overlapping problem codes. <br><br>**Phase 2 – Enforce:** Guided forms prevent ambiguous labels. <br><br>**Phase 3 – Review:** Fix areas with frequent relabels. | • Speeds routing to the right owner on first attempt.<br><br>• Reduces handoffs that inflate cycle time.<br><br>• Improves forecasting and automation targeting. | **Efficiency** = resolution_days_reduced × tickets. | Category bar reveals inconsistent high averages that need sharper taxonomy. |
| Continuous skill uplift | **Phase 1 – Locate gaps:** Analyze resolution time by agent and category. <br><br>**Phase 2 – Micro-learning:** Short scenario drills and shadowing. <br><br>**Phase 3 – Institutionalize:** Promote best-practice runbooks. | • Raises baseline capability across the team.<br><br>• Lowers escalation volume over time.<br><br>• Builds resilience that does not depend on a few experts. | **ROI** = hours_saved × rate − training_cost. | Outliers (**{outliers_count}**) imply uneven technique causes long cases. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Scheduled updates for long cases | **Phase 1 – Cadence:** Send updates every 4–8 hours beyond baseline with ETA and next step. <br><br>**Phase 2 – Automate:** Drive reminders from the case clock. <br><br>**Phase 3 – Sentiment:** Track CSAT and complaints for aged cohorts. | • Reduces uncertainty for users during extended fixes.<br><br>• Cuts complaint volume by maintaining communication.<br><br>• Improves perceived control throughout the resolution. | **Cost Avoidance** = complaints_avoided × escalation_cost. Focus on outliers above **{upper_fence:.2f} h**. | Line peaks and boxplot tail identify cohorts needing frequent updates. |
| Expectation setting by category | **Phase 1 – Publish bands:** Provide typical, slow and fast ETAs per category. <br><br>**Phase 2 – Alert:** Notify when a case crosses its ETA band. <br><br>**Phase 3 – Recalibrate:** Compare promised vs actual times each month. | • Aligns user expectations with real delivery times.<br><br>• Converts delays into managed experiences with clear ETAs.<br><br>• Reduces escalations driven by surprise. | **Retention Value** = retained_users × avg_value; use worst category **{top_cat['category']}** to size impact. | Category bar shows where expectations most often miss (**{top_cat['resolution_time_hours']:.2f} h**). |
| Post-resolution feedback loop | **Phase 1 – Targeted surveys:** Focus on slow or complex categories. <br><br>**Phase 2 – Analyze:** Convert themes into process or tool changes. <br><br>**Phase 3 – Close the loop:** Communicate improvements to users. | • Produces sustained CSAT gains with visible action.<br><br>• Reduces repeat defects through structured feedback.<br><br>• Guides the roadmap for automation and training. | **Value** = ΔCSAT × ticket_volume(category). | Worst vs best category gap (**{top_cat['resolution_time_hours']:.2f} h** vs **{bottom_cat['resolution_time_hours']:.2f} h**) prioritizes where to listen first. |
"""
}


            # Render the CIO tables using your helper so they appear in 3 nested expanders
            render_cio_tables("Average Resolution Time", cio_2b)


        else:
            st.warning("⚠️ Column 'resolution_time' or 'created_time' not found in uploaded dataset.")

    #--------------------------------------------

    # 3. Average resolution time by FCR & SLA Adherence
    with st.expander("📌 SLA Adherence & FCR Comparison"):
        # local import to ensure 'go' is available even if not imported at module top
        import plotly.graph_objects as go

        # -----------------------------
        # Defensive column presence
        # -----------------------------
        has_sla_met = "sla_met" in df_filtered.columns
        has_response_time = "response_time_minutes" in df_filtered.columns or "response_time_elapsed" in df_filtered.columns
        has_resolution_time = "resolution_time" in df_filtered.columns or "resolution_time_hours" in df_filtered.columns
        has_sla_response_col = (
            "sla_response_time" in df_filtered.columns
            or "sla_response_time_minutes" in df_filtered.columns
            or "sla_response_time_elapsed" in df_filtered.columns
        )
        has_sla_resolution_col = (
            "sla_resolution_time" in df_filtered.columns
            or "sla_resolution_time_hours" in df_filtered.columns
            or "sla_resolution_time_elapsed" in df_filtered.columns
        )

        # Ensure created_date exists for time series grouping
        if "created_time" in df_filtered.columns:
            df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date
        else:
            df_filtered["created_date"] = pd.NaT

        # --- Prepare response_time_minutes if not already present ---
        if "response_time_minutes" not in df_filtered.columns and "response_time_elapsed" in df_filtered.columns:
            col = df_filtered["response_time_elapsed"]
            if pd.api.types.is_timedelta64_dtype(col):
                df_filtered["response_time_minutes"] = col.dt.total_seconds() / 60.0
            else:
                df_filtered["response_time_minutes"] = pd.to_numeric(col, errors="coerce")

        # --- Prepare resolution_time_hours if not already present ---
        if "resolution_time_hours" not in df_filtered.columns:
            if "resolution_time" in df_filtered.columns:
                col = df_filtered["resolution_time"]
                if pd.api.types.is_timedelta64_dtype(col):
                    df_filtered["resolution_time_hours"] = col.dt.total_seconds() / 3600.0
                else:
                    df_filtered["resolution_time_hours"] = pd.to_numeric(col, errors="coerce")
            else:
                df_filtered["resolution_time_hours"] = pd.NA

        # --- Prepare SLA reference values (minutes or hours) if available ---
        # SLA response time (minutes)
        sla_response_minutes = None
        if "sla_response_time_minutes" in df_filtered.columns:
            sla_response_minutes = pd.to_numeric(df_filtered["sla_response_time_minutes"], errors="coerce")
        elif "sla_response_time" in df_filtered.columns:
            col = df_filtered["sla_response_time"]
            if pd.api.types.is_timedelta64_dtype(col):
                sla_response_minutes = col.dt.total_seconds() / 60.0
            else:
                sla_response_minutes = pd.to_numeric(col, errors="coerce")
        elif "sla_response_time_elapsed" in df_filtered.columns:
            col = df_filtered["sla_response_time_elapsed"]
            if pd.api.types.is_timedelta64_dtype(col):
                sla_response_minutes = col.dt.total_seconds() / 60.0
            else:
                sla_response_minutes = pd.to_numeric(col, errors="coerce")

        # SLA resolution time (hours)
        sla_resolution_hours = None
        if "sla_resolution_time_hours" in df_filtered.columns:
            sla_resolution_hours = pd.to_numeric(df_filtered["sla_resolution_time_hours"], errors="coerce")
        elif "sla_resolution_time" in df_filtered.columns:
            col = df_filtered["sla_resolution_time"]
            if pd.api.types.is_timedelta64_dtype(col):
                sla_resolution_hours = col.dt.total_seconds() / 3600.0
            else:
                sla_resolution_hours = pd.to_numeric(col, errors="coerce")
        elif "sla_resolution_time_elapsed" in df_filtered.columns:
            col = df_filtered["sla_resolution_time_elapsed"]
            if pd.api.types.is_timedelta64_dtype(col):
                sla_resolution_hours = col.dt.total_seconds() / 3600.0
            else:
                sla_resolution_hours = pd.to_numeric(col, errors="coerce")

        # --- Create sla_met if not present and we have reference + actuals ---
        if not has_sla_met:
            if "response_time_minutes" in df_filtered.columns and sla_response_minutes is not None:
                df_filtered["sla_met"] = (pd.to_numeric(df_filtered["response_time_minutes"], errors="coerce") <= sla_response_minutes).astype(int)
                has_sla_met = True
            elif "resolution_time_hours" in df_filtered.columns and sla_resolution_hours is not None:
                df_filtered["sla_met"] = (pd.to_numeric(df_filtered["resolution_time_hours"], errors="coerce") <= sla_resolution_hours).astype(int)
                has_sla_met = True
            else:
                has_sla_met = "sla_met" in df_filtered.columns

        # --- Working copy & numeric safety ---
        df_sla = df_filtered.copy()
        if "sla_met" in df_sla.columns:
            df_sla["sla_met"] = pd.to_numeric(df_sla["sla_met"], errors="coerce")

                # ---------- Graph A: Gauge + SLA Trend (fixed ordering) ----------
        if has_sla_met and "created_date" in df_sla.columns:
            sla_trend = (
                df_sla.groupby("created_date", dropna=True)["sla_met"]
                .mean().reset_index().sort_values("created_date")
            )

            # --- Compute robust metrics FIRST ---
            if not sla_trend.empty:
                latest_sla_pct = float(sla_trend["sla_met"].iloc[-1] * 100)
                overall_sla_pct = float(sla_trend["sla_met"].mean() * 100)
                first_sla_pct   = float(sla_trend["sla_met"].iloc[0] * 100)
                pct_change      = ((latest_sla_pct - first_sla_pct) / max(first_sla_pct, 1e-9)) * 100
                breaches_count  = int((pd.to_numeric(df_sla["sla_met"], errors="coerce") == 0).sum())

                max_day_idx = sla_trend["sla_met"].idxmax()
                min_day_idx = sla_trend["sla_met"].idxmin()
                max_day_date = sla_trend.loc[max_day_idx, "created_date"]
                min_day_date = sla_trend.loc[min_day_idx, "created_date"]
                max_day_pct  = float(sla_trend.loc[max_day_idx, "sla_met"] * 100)
                min_day_pct  = float(sla_trend.loc[min_day_idx, "sla_met"] * 100)
            else:
                # Safe defaults when we have no trend rows
                latest_sla_pct = overall_sla_pct = first_sla_pct = pct_change = 0.0
                breaches_count = 0
                max_day_date = min_day_date = "—"
                max_day_pct = min_day_pct = 0.0

            # --- Graph 1 : Gauge (latest) ---
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=float(latest_sla_pct),
                title={'text': "Current SLA Adherence (%)"},
                gauge={'axis': {'range': [0, 100]}}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            # --- Analyses (now use the precomputed metrics) ---
            st.markdown("#### Analysis of Current SLA Adherence (Gauge)")
            st.write(f"""
What this graph is: A gauge displaying the **most recent SLA adherence percentage**.

X-axis: (Not applicable).
Y-axis: (Not applicable).

What it shows in your data:
Latest adherence: {latest_sla_pct:.1f}%.
Period average: {overall_sla_pct:.1f}%.
Change from first recorded period: {pct_change:.1f}% relative.

Overall, when the gauge is materially below the period average, the operation is **under strain**; when it meets or exceeds the average, the operation is **stable or improving**.

How to read it operationally:
Trigger point: Set a minimum acceptable gauge level based on commitments (e.g., 95%); below that, trigger surge actions.
Drift detection: Compare gauge vs. 7/30-day averages to detect adverse trends early.
Root-cause: If the gauge drops sharply, inspect intake spikes or staffing shortfalls on the same dates.
Control: Keep the latest value inside a narrow band around target using routing, WIP limits, and fast-lanes.

Why this matters: This single number is a **contract health** snapshot; keeping it near or above target prevents penalties, escalations, and reputational damage.
""")

            # --- Graph 2 : Trend line ---
            fig_line_sla = px.line(
                sla_trend,
                x="created_date",
                y="sla_met",
                title="SLA Adherence Trend Over Time",
                labels={"created_date": "Created Date", "sla_met": "SLA Adherence (proportion)"}
            )
            st.plotly_chart(fig_line_sla, use_container_width=True)

            st.markdown("#### Analysis of SLA Adherence Trend Over Time (Line)")
            if not sla_trend.empty:
                st.write(f"""
What this graph is: A time-series showing **daily SLA adherence proportion**.

X-axis: Calendar date.
Y-axis: SLA adherence (proportion 0–1).

What it shows in your data:
Best day: {max_day_date} at {max_day_pct:.1f}% adherence.
Weakest day: {min_day_date} at {min_day_pct:.1f}% adherence.
Period average: {overall_sla_pct:.1f}% with a start→end change of {pct_change:.1f}%.
Total breached tickets across the dataset: {breaches_count}.

Overall, sustained troughs indicate **breach-prone sequences** that require capacity or routing changes; recoveries show **effective interventions**.

How to read it operationally:
Gap vs. target: The vertical gap to your SLA target is the daily non-compliance risk.
Lead–lag: Drops following intake spikes imply reactive mode; faster rebounds indicate healthy recovery.
Recovery strength: Shorter time from trough to baseline reflects operational resilience.
Control: Keep the line close to a target band by enforcing WIP limits, escalation triggers, and surge capacity.

Why this matters: Adherence trend is the **heartbeat** of contractual performance; controlling it stabilizes penalties, user trust, and executive confidence.
""")
            else:
                st.info("Not enough data to render the SLA adherence trend analysis.")
        else:
            st.info("SLA metric ('sla_met') not present and could not be computed from available SLA reference columns. Skipping gauge and trend.")


        # ---------- Graph B: SLA by Priority (stacked/segmented) ----------
        if "priority" in df_sla.columns and has_sla_met:
            sla_by_priority = df_sla.groupby("priority")["sla_met"].mean().reset_index().sort_values("sla_met", ascending=False)
            fig_bar_sla = px.bar(
                sla_by_priority,
                x="priority",
                y="sla_met",
                title="SLA Adherence by Priority",
                labels={"priority": "Priority", "sla_met": "SLA Adherence (proportion)"},
                text="sla_met"
            )
            fig_bar_sla.update_traces(texttemplate='%{text:.1%}', textposition="outside")
            st.plotly_chart(fig_bar_sla, use_container_width=True)

            # Priority analysis
            st.markdown("#### Analysis of SLA Adherence by Priority (Bar)")
            if not sla_by_priority.empty:
                best = sla_by_priority.iloc[0]
                worst = sla_by_priority.iloc[-1]
                avg_priority = float(sla_by_priority["sla_met"].mean())
                st.write(f"""
    What this graph is: A category comparison of **SLA adherence by priority level**.

    X-axis: Priority.
    Y-axis: SLA adherence (proportion 0–1).

    What it shows in your data:
    Highest adherence: {best['priority']} at {best['sla_met']:.2f}.
    Lowest adherence: {worst['priority']} at {worst['sla_met']:.2f}.
    Average across priorities: {avg_priority:.2f}.

    Overall, a wide spread between best and worst priorities signals **policy or capacity misalignment** across priority bands.

    How to read it operationally:
    Peaks: Replicate routing/ownership patterns from {best['priority']} to weaker bands.
    Plateaus: Standardize mid-performers to lift the floor uniformly.
    Downswings: For {worst['priority']}, add fast-lanes and targeted escalation rules.
    Control: Align staffing and skills with the observed priority mix to keep adherence balanced.

    Why this matters: Harmonizing adherence across priorities **protects critical users** while raising the **overall compliance baseline**.
    """)
            else:
                st.info("Not enough data to analyze SLA by priority.")
        else:
            st.info("Priority column not present or SLA metric unavailable — skipping priority breakdown.")

        # ---------- Graph C: Average Resolution Time by FCR vs Non-FCR ----------
        # FCR column exists in list — check variants
        fcr_col = None
        if "fcr" in df_filtered.columns:
            fcr_col = "fcr"
        elif "FCR" in df_filtered.columns:
            fcr_col = "FCR"

        if fcr_col and "resolution_time_hours" in df_filtered.columns:
            # normalize FCR values to boolean-like (1/0)
            df_sla["fcr_flag"] = (
                df_sla[fcr_col].astype(str).str.strip().str.lower()
                .replace({"true": "1", "false": "0", "yes": "1", "no": "0"})
                .map({"1": 1, "0": 0}).fillna(0).astype(int)
            )
            res_by_fcr = df_sla.groupby("fcr_flag")["resolution_time_hours"].mean().reset_index()
            res_by_fcr["fcr_label"] = res_by_fcr["fcr_flag"].map({1: "FCR", 0: "Non-FCR"})

            fig_fcr = px.bar(
                res_by_fcr,
                x="fcr_label",
                y="resolution_time_hours",
                text="resolution_time_hours",
                title="Average Resolution Time: FCR vs Non-FCR",
                labels={"resolution_time_hours": "Avg Resolution Time (hours)", "fcr_label": "FCR Status"}
            )
            fig_fcr.update_traces(texttemplate='%{text:.2f}', textposition="outside")
            st.plotly_chart(fig_fcr, use_container_width=True)

            # derive metrics used in the analysis text
            fcr_row = res_by_fcr.loc[res_by_fcr["fcr_flag"] == 1]
            nonfcr_row = res_by_fcr.loc[res_by_fcr["fcr_flag"] == 0]
            fcr_avg = float(fcr_row["resolution_time_hours"].iloc[0]) if not fcr_row.empty else float("nan")
            nonfcr_avg = float(nonfcr_row["resolution_time_hours"].iloc[0]) if not nonfcr_row.empty else float("nan")
            diff = (nonfcr_avg - fcr_avg) if (pd.notna(fcr_avg) and pd.notna(nonfcr_avg)) else float("nan")
            pct_diff = (diff / fcr_avg * 100) if (pd.notna(diff) and pd.notna(fcr_avg) and fcr_avg != 0) else float("nan")

            # FCR analysis
            st.markdown("#### Analysis of Average Resolution Time — FCR vs Non-FCR (Bar)")
            st.write(f"""
    What this graph is: A comparison of **average resolution time for FCR vs Non-FCR tickets**.

    X-axis: FCR status.
    Y-axis: Average resolution time (hours).

    What it shows in your data:
    FCR average: {fcr_avg:.2f} hrs.
    Non-FCR average: {nonfcr_avg:.2f} hrs.
    Gap (Non-FCR − FCR): {diff:.2f} hrs ({pct_diff:.1f}% relative to FCR).

    Overall, a higher Non-FCR average indicates **handoffs, escalations, or complexity** beyond first contact.

    How to read it operationally:
    Peaks: Target Non-FCR cohorts with enablement to convert more cases to FCR.
    Plateaus: Preserve the practices that keep FCR time low and steady.
    Downswings: Use the gap metric to verify improvement after training/tools.
    Control: Expand decision trees and knowledge content to lift FCR sustainably.

    Why this matters: Moving more work to **first-contact resolution** reduces total time and cost, while improving first-touch experience.
    """)
        else:
            st.info("FCR column or resolution_time_hours missing — skipping FCR vs Non-FCR chart.")

        # ---------- CIO Tables (≥3 recs each; phased; detailed benefits; real values) ----------
        # Extract priority metrics if available for evidence/cost wording
        if "priority" in df_sla.columns and has_sla_met:
            sla_by_priority_safe = df_sla.groupby("priority")["sla_met"].mean().reset_index().sort_values("sla_met", ascending=False)
            if not sla_by_priority_safe.empty:
                best = sla_by_priority_safe.iloc[0]
                worst = sla_by_priority_safe.iloc[-1]
                avg_priority_val = float(sla_by_priority_safe["sla_met"].mean())
                best_priority_name  = str(best["priority"])
                best_priority_val   = float(best["sla_met"])
                worst_priority_name = str(worst["priority"])
                worst_priority_val  = float(worst["sla_met"])
            else:
                best_priority_name = worst_priority_name = "—"
                best_priority_val = worst_priority_val = avg_priority_val = 0.0
        else:
            best_priority_name = worst_priority_name = "—"
            best_priority_val = worst_priority_val = avg_priority_val = 0.0

        # Safeguards for earlier variables
        latest_sla_pct = float(latest_sla_pct) if "latest_sla_pct" in locals() else 0.0
        overall_sla_pct = float(overall_sla_pct) if "overall_sla_pct" in locals() else 0.0
        breaches_count = int(breaches_count) if "breaches_count" in locals() else 0
        max_day_date = max_day_date if "max_day_date" in locals() else "—"
        min_day_date = min_day_date if "min_day_date" in locals() else "—"
        max_day_pct = float(max_day_pct) if "max_day_pct" in locals() else 0.0
        min_day_pct = float(min_day_pct) if "min_day_pct" in locals() else 0.0
        diff = float(diff) if "diff" in locals() and not pd.isna(diff) else 0.0
        pct_diff = float(pct_diff) if "pct_diff" in locals() and not pd.isna(pct_diff) else 0.0
        fcr_avg = float(fcr_avg) if "fcr_avg" in locals() and not pd.isna(fcr_avg) else 0.0
        nonfcr_avg = float(nonfcr_avg) if "nonfcr_avg" in locals() and not pd.isna(nonfcr_avg) else 0.0

        cio_sla = {
            "cost": f"""
        | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
        |---|---|---|---|---|
        | Automate SLA monitoring & alerts | **Phase 1 – Map Rules:** Response and resolution timers with thresholds. <br><br>**Phase 2 – Alerting:** Owner nudges at T-1 and T-0 with suggested actions. <br><br>**Phase 3 – Govern:** Weekly breach cohort review and structural fixes. | • Lowers penalty exposure by catching at-risk items in time.<br><br>• Reduces manual tracking effort for team leads.<br><br>• Decreases escalation time by standardizing triggers. | **Savings** = penalties_avoided. If breaches drop 20% from **{breaches_count}**, savings scale with your penalty schedule. | Best day **{max_day_date}** **{max_day_pct:.1f}%** vs worst **{min_day_date}** **{min_day_pct:.1f}%** shows volatility that automation can smooth. |
        | Resource realignment to weak bands | **Phase 1 – Detect:** Overlay adherence dips with intake and staffing. <br><br>**Phase 2 – Replan:** Stagger shifts and overlaps in weak windows. <br><br>**Phase 3 – Validate:** Track rebound toward the period average. | • Substitutes overtime with regular scheduled capacity.<br><br>• Prevents breach clusters on consistently weak days.<br><br>• Improves cost predictability across reporting periods. | **Cost↓** = overtime_avoided × wage. Aim to raise weak days from **{min_day_pct:.1f}%** toward period avg **{overall_sla_pct:.1f}%**. | Priority spread: **{worst_priority_name}={worst_priority_val:.2f}** vs **{best_priority_name}={best_priority_val:.2f}** indicates misalignment. |
        | Legacy backlog amnesty + RCA payback | **Phase 1 – Isolate:** Aged tickets that depress daily SLA. <br><br>**Phase 2 – Amnesty:** Reset or close with stakeholder sign-off while logging causes. <br><br>**Phase 3 – Payback:** Implement fixes that prevent re-accumulation. | • Removes recurring penalty risk from stale items.<br><br>• Frees analyst hours for current demand.<br><br>• Lifts reported adherence while long-term fixes land. | **Savings** = recurring_penalty_per_ticket × legacy_ticket_count (focus near **{min_day_date}**, **{min_day_pct:.1f}%**). | Trough clusters on the trend drive down averages; clearing legacy tail lifts line toward **{overall_sla_pct:.1f}%**. |
        | FCR conversion incentives | **Phase 1 – Diagnose:** Determine root causes for Non-FCR such as handoffs and missing data. <br><br>**Phase 2 – Enable:** Decision trees, KB and forms to raise FCR rate. <br><br>**Phase 3 – Reward:** Recognize teams that sustain FCR gains. | • Lowers total handling time by reducing multi-touch cases.<br><br>• Shrinks queues by resolving on first contact.<br><br>• Improves adherence at a lower unit cost. | **Hours saved** = gap × Non-FCR_volume × rate; current gap **{diff:.2f} h** ({pct_diff:.1f}%). | FCR **{fcr_avg:.2f} h** vs Non-FCR **{nonfcr_avg:.2f} h** quantifies the opportunity. |
        """,
            "performance": f"""
        | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
        |---|---|---|---|---|
        | Root-cause analysis on breaches | **Phase 1 – Code Causes:** Capacity, routing, dependency and data quality. <br><br>**Phase 2 – Fix Top-2:** Cross-team actions with SLAs. <br><br>**Phase 3 – Verify:** Re-measure on the same segments. | • Removes systemic failure modes behind repeated breaches.<br><br>• Raises the mean adherence across the period.<br><br>• Reduces firefighting through targeted corrections. | **Efficiency** = breaches_avoided × avg_ticket_cost. If 25% of **{breaches_count}** are avoided, savings follow proportionally. | Gauge at **{latest_sla_pct:.1f}%** vs average **{overall_sla_pct:.1f}%** and trough **{min_day_date}** **{min_day_pct:.1f}%** show fix targets. |
        | Escalation tiers by priority | **Phase 1 – Triggers:** T-1 and T-0 per priority band. <br><br>**Phase 2 – Auto-route:** Senior queue at T-1 and swarm at T-0. <br><br>**Phase 3 – Review:** Tighten thresholds weekly. | • Improves performance for the most critical users.<br><br>• Reduces last-minute breaches by standardizing actions.<br><br>• Creates repeatable discipline for peak risk moments. | **SLA uplift** = Δadherence × tickets_in_priority. If **{worst_priority_name}** rises from **{worst_priority_val:.2f}** to **{best_priority_val:.2f}**, gain = **{(best_priority_val - worst_priority_val):.2f}** points. | Priority bar shows wide spread requiring tiered intervention. |
        | Forecast-based capacity moves | **Phase 1 – Model:** Use the trend to forecast low-adherence days. <br><br>**Phase 2 – Pre-position:** Temporary capacity or deflection tactics. <br><br>**Phase 3 – Backtest:** Compare forecast error to outcomes and recalibrate. | • Reduces depth and duration of troughs in adherence.<br><br>• Stabilizes SLA without relying on emergency overtime.<br><br>• Improves planning accuracy for peak periods. | **Value** = breaches_avoided_on_forecasted_days × penalty. | Worst day **{min_day_date}** **{min_day_pct:.1f}%** is a template for what to forecast and pre-empt. |
        """,
            "satisfaction": f"""
        | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
        |---|---|---|---|---|
        | Customer SLA dashboards | **Phase 1 – Expose:** Stage, owner and SLA clock to users. <br><br>**Phase 2 – Alerts:** Proactive nudges when risk thresholds cross. <br><br>**Phase 3 – Feedback:** CSAT after resolution to refine cadence. | • Reduces “any update?” contacts with transparent status.<br><br>• Increases trust during periods of slower performance.<br><br>• Provides structured input for improving communication cadence. | **Avoided cost** = complaints_avoided × escalation_cost; size on worst day **{min_day_date}** **{min_day_pct:.1f}%**. | Trend troughs correlate with complaint risk; visibility mitigates impact below **{overall_sla_pct:.1f}%**. |
        | Priority-aware guarantees | **Phase 1 – Publish:** Realistic response and resolution bands per priority. <br><br>**Phase 2 – Notify:** Advance alerts ahead of potential misses with recovery steps. <br><br>**Phase 3 – Recalibrate:** Compare promised vs actual each month. | • Aligns expectations with real delivery capability.<br><br>• Turns potential breaches into managed experiences.<br><br>• Reduces escalations that arise from surprise. | **Retention** = retained_customers × avg_revenue; track improvement from **{latest_sla_pct:.1f}%** toward **{overall_sla_pct:.1f}%**. | Priority variance (**{best_priority_name}: {best_priority_val:.2f}** vs **{worst_priority_name}: {worst_priority_val:.2f}**) justifies differentiated messaging. |
        | VIP assurance lane | **Phase 1 – Identify:** Define a VIP cohort with tighter timers. <br><br>**Phase 2 – Own:** Named owners and pre-escalation alerts. <br><br>**Phase 3 – Report:** Executive summaries of risks and breaches. | • Protects high-value relationships during operational dips.<br><br>• Reduces churn risk by giving VIPs faster action paths.<br><br>• Improves perceived responsiveness for critical accounts. | **Savings** = VIP_escalations_avoided × cost_per_escalation; baseline VIP risk tied to worst priority **{worst_priority_val:.2f}**. | On weak days (**{min_day_date}**), VIPs are disproportionately impacted and assurance lanes mitigate that risk. |
        """
        }

        # render CIO tables (3 nested expanders)
        render_cio_tables("SLA Adherence & FCR Insights", cio_sla)
