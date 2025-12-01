import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from statsmodels.tsa.seasonal import seasonal_decompose
import numpy as np

# Mesiniaga theme
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

# ─────────────────────────────────────────────
# Helper: force any time-like series → hours(float)
# ─────────────────────────────────────────────
def _to_hours(s: pd.Series) -> pd.Series:
    """
    Coerce a resolution-time series into hours (float).
    Accepts timedelta, strings like '1 days 02:03:04', or numeric.
    """
    if s is None:
        return pd.Series(dtype="float64")
    # timedelta dtype → hours
    if pd.api.types.is_timedelta64_dtype(s):
        return s / pd.Timedelta(hours=1)
    # try parse as timedelta-like strings
    s_td = pd.to_timedelta(s, errors="coerce")
    if s_td.notna().any():
        return s_td / pd.Timedelta(hours=1)
    # fallback: numeric
    return pd.to_numeric(s, errors="coerce")

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def technician_performance(df_filtered):

    # ==========================
    # 📌 Tickets Assigned per Agent
    # ==========================
    with st.expander("📌 Tickets Assigned per Agent"):
        if "technician" in df_filtered.columns:
            ticket_counts = df_filtered.groupby("technician").size().reset_index(name="tickets")

            # --- Graph 1: Bar chart
            fig_bar = px.bar(
                ticket_counts, x="technician", y="tickets",
                title="Tickets Assigned per Agent", text="tickets",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            fig_bar.update_traces(textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True)

            # Analysis for Graph 1 (Bar)
            if not ticket_counts.empty:
                total_tix = int(ticket_counts["tickets"].sum())
                avg_tix = float(ticket_counts["tickets"].mean())
                max_row = ticket_counts.loc[ticket_counts["tickets"].idxmax()]
                min_row = ticket_counts.loc[ticket_counts["tickets"].idxmin()]
                st.markdown("### Analysis of Tickets Assigned per Agent (Bar)")
                st.write(f"""
**What this graph is:** A bar chart comparing **tickets assigned (workload inflow)** across agents.  
**X-axis:** Agent (technician).  
**Y-axis:** Count of tickets assigned.

**What it shows in your data:**  
- **Highest workload agent:** **{max_row['technician']}** with **{int(max_row['tickets']):,}** assigned.  
- **Lowest workload agent:** **{min_row['technician']}** with **{int(min_row['tickets']):,}** assigned.  
- **Average across agents:** **{avg_tix:.1f}** tickets; **Total:** **{total_tix:,}**.

**Overall:** Large spread between agents indicates **routing imbalance** and potential burnout risk.

**How to read it operationally:**  
- **Gap = imbalance:** The difference between the tallest and shortest bars shows **assignment skew**.  
- **Lead–lag in effort:** Pair this with resolution time to see if high assignment agents also **resolve slower**.  
- **Recovery strength:** Revisit routing weekly; if spread persists, **rebalance skills/coverage**.  
- **Control:** Use skill-based rules and caps per agent per day.

**Why this matters:** Balanced inflow reduces overtime and keeps SLA predictable.
""")

            # --- Graph 2: Box plot (distribution across agents)
            fig_box = px.box(
                ticket_counts, y="tickets",
                title="Distribution of Tickets Assigned per Agent",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # Analysis for Graph 2 (Box)
            if not ticket_counts.empty:
                q1 = ticket_counts["tickets"].quantile(0.25)
                q3 = ticket_counts["tickets"].quantile(0.75)
                iqr = q3 - q1
                median_val = ticket_counts["tickets"].median()
                st.markdown("### Analysis of Distribution of Tickets Assigned (Box)")
                st.write(f"""
**What this graph is:** A box plot summarizing **how ticket loads vary across agents**.  
**X-axis:** (implicit: agents).  
**Y-axis:** Tickets assigned per agent.

**What it shows in your data:**  
- **Median:** **{median_val:.1f}**; **IQR (Q1→Q3):** **{q1:.1f} → {q3:.1f}** (width **{iqr:.1f}**).  
- Points far above whiskers indicate agents with **unusually high load**.

**Overall:** A **wide IQR** or many outliers means **uneven allocation**.

**How to read it operationally:**  
- **Gap = risk:** Wider boxes/outliers = **higher variance** in load.  
- **Lead–lag:** Outliers that persist month to month signal **systemic routing issues**.  
- **Recovery strength:** Narrowing IQR post-intervention shows **stabilizing workload**.  
- **Control:** Add guardrails: **daily max assignments** per agent.

**Why this matters:** Lower variance produces steadier throughput and fewer escalations.
""")

            # --- Graph 3: Heatmap (assignments over time by agent)
            if "created_time" in df_filtered.columns:
                df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date
                heatmap_data = df_filtered.groupby(["created_date", "technician"]).size().reset_index(name="count")
                heatmap_pivot = heatmap_data.pivot(index="created_date", columns="technician", values="count").fillna(0)
                fig_heatmap = px.imshow(
                    heatmap_pivot.T,
                    title="Assignments Over Time per Agent",
                    labels=dict(x="Date", y="Agent", color="Tickets"),
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

                # Analysis for Graph 3 (Heatmap)
                pivot_vals = heatmap_pivot.stack()
                if not pivot_vals.empty:
                    peak_idx = pivot_vals.idxmax()
                    peak_val = int(pivot_vals.max())
                    peak_date, peak_tech = peak_idx[0], peak_idx[1]
                    daily_tot = heatmap_pivot.sum(axis=1).rename("total")
                    mean_daily = float(daily_tot.mean())
                    st.markdown("### Analysis of Assignments Over Time per Agent (Heatmap)")
                    st.write(f"""
**What this graph is:** A heatmap of **daily assignment intensity** by agent.  
**X-axis:** Calendar date.  
**Y-axis:** Agent.  
**Color:** Tickets assigned (darker = more).

**What it shows in your data:**  
- **Peak cell:** **{peak_tech}** on **{peak_date}** with **{peak_val}** assignments.  
- **Average daily total (all agents):** **{mean_daily:.1f}** tickets/day.

**Overall:** Dark vertical bands indicate **surge days**; dark rows indicate **consistently high-load agents**.

**How to read it operationally:**  
- **Gap = surge delta:** Darker days above the average require **surge staffing** or deferral.  
- **Lead–lag:** If dark bands are followed by lighter bands, teams are **catching up** next day.  
- **Recovery strength:** Faster return to pale colors signals **healthy flow**.  
- **Control:** Pre-announce surge windows and pre-route to balanced coverage.

**Why this matters:** Heat patterns reveal when/where to deploy buffers and automation.
""")

            # ------- CIO for 4(a) with real values -------
            if not ticket_counts.empty:
                max_agent = str(max_row["technician"])
                max_val = int(max_row["tickets"])
                min_agent = str(min_row["technician"])
                min_val = int(min_row["tickets"])
            else:
                max_agent, max_val, min_agent, min_val, total_tix, avg_tix = "N/A", 0, "N/A", 0, 0, 0.0

            cio_4a = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Balanced ticket routing** | **Phase 1 – Instrument:** Track per-agent inflow daily and persist the counts to a simple telemetry table that includes agent, date, and category. This establishes a transparent baseline and exposes persistent imbalances rather than one-off spikes. <br><br>**Phase 2 – Automate:** Round-robin plus skill tags should assign tickets automatically while enforcing a hard cap of daily assignments per agent. The automation must log exceptions and provide a visible queue so leads can review why a case bypassed the rule. <br><br>**Phase 3 – Calibrate:** Tune caps weekly by comparing inflow, completion rate, and breach risk, and then adjust thresholds to match real demand. Document every parameter change so future reviews can trace cause and effect. | - It lowers overtime by spreading work more evenly across agents.<br><br>- It reduces burnout risk for top-loaded agents and stabilizes productivity.<br><br>- It makes spend more predictable because fewer shifts require premium rates.<br><br>- It prevents backlog snowballing by keeping daily inflow within fair limits. | **OT savings ≈ (excess tickets on {max_agent} above mean × avg mins/ticket ÷ 60 × hourly rate)**. Here excess ≈ **{max_val - int(round(avg_tix))}** vs mean **{avg_tix:.1f}**. | Bar shows **{max_agent} = {max_val}** vs **{min_agent} = {min_val}**; total **{total_tix:,}**, avg **{avg_tix:.1f}**/agent. |
| **Cross-train under-loaded agents** | **Phase 1 – Identify:** Quantify shortfalls on low-load agents such as {min_agent} relative to the team mean and rank by category demand. This isolates the exact skills that would unlock the most capacity. <br><br>**Phase 2 – Upskill:** Build short, focused modules on the top two categories from {max_agent}’s queue and include shadowing plus checklists. The aim is safe, repeatable performance within two weeks. <br><br>**Phase 3 – Rotate:** Introduce a weekly rotation that places newly trained agents on real cases with senior oversight. Capture outcomes and adjust the curriculum based on error trends and handle time. | - It reduces dependency on a few specialists by growing coverage depth.<br><br>- It removes bottlenecks when demand shifts because more agents can handle the work.<br><br>- It trims the need for temporary hires during spikes by using internal capacity first.<br><br>- It improves resilience when people are on leave or rotation. | **Avoided temp cost = (tickets shifted to {min_agent} × avg handle mins ÷ 60 × temp rate)**. Use shortfall ≈ **{int(round(avg_tix)) - min_val}** vs mean. | Box plot spread + bar gap confirm imbalance. |
| **Surge buffers on peak days** | **Phase 1 – Forecast:** Use heatmap signals and daily averages (≈{avg_tix:.1f} per agent) to predict specific surge dates such as {peak_date if 'peak_date' in locals() else 'n/a'}. Publish a short plan that names owners, start times, and exit criteria. <br><br>**Phase 2 – Pre-staff:** Schedule overlap shifts or standby capacity on forecast days and pre-stage macro replies and triage scripts. Confirm that tooling access and approvals are ready before the surge window opens. <br><br>**Phase 3 – Review:** Measure next-day backlog deltas and compare to forecast. Retire temporary measures when metrics return to baseline and record lessons learned for the next peak. | - It prevents sudden backlog jumps by matching staffing to known peaks.<br><br>- It reduces weekend overtime by clearing more work during normal hours.<br><br>- It improves user experience because response times remain steady on busy days.<br><br>- It gives team leads control to plan coverage rather than react late. | **Savings = (surge tickets handled during shift × mins/ticket ÷ 60 × OT rate avoided)**; use peak cell **{peak_val if 'peak_val' in locals() else 0}** as proxy. | Heatmap peak **{(peak_tech if 'peak_tech' in locals() else 'n/a')}={peak_val if 'peak_val' in locals() else 0}** on **{(peak_date if 'peak_date' in locals() else 'n/a')}**; daily avg ≈ **{mean_daily if 'mean_daily' in locals() else 0:.1f}**. |
""",
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Skill-based routing** | **Phase 1 – Map:** Build a matrix of categories to required skills for each agent and validate it against recent resolution notes. This makes routing rules explicit and testable. <br><br>**Phase 2 – Route:** Deploy first-time-right assignment that prefers agents with matching skills and available capacity. Record every override so patterns can be reviewed. <br><br>**Phase 3 – Tune:** Reassign rules based on outcomes such as reopen rate and handle time, and prune rules that no longer add value. | - It speeds up first responses because tickets land with the right agent the first time.<br><br>- It cuts handoffs which lowers rework and delays.<br><br>- It increases daily throughput because less time is wasted switching context.<br><br>- It improves consistency of outcomes across categories. | **Throughput gain = (Δtickets/day after routing × days)**, anchored on high-load agent gap (**{max_val - int(round(avg_tix))}**). | Bar skew + box variance show mis-routing. |
| **Real-time load dashboard** | **Phase 1 – Visualize:** Build a live view that shows inflow, open, and closure rate per agent with clear capacity markers. Use the same definitions that appear in reports to avoid metric drift. <br><br>**Phase 2 – Alert:** Trigger notifications when caps are exceeded or when queues age past thresholds. Alerts must include a suggested action and a link to the case list. <br><br>**Phase 3 – Act:** Auto-reassign or call a short huddle to rebalance and then record the outcome so you can prove the intervention worked. | - It reduces queue aging by surfacing hotspots immediately.<br><br>- It smooths flow by triggering quick reassignments when caps are breached.<br><br>- It keeps SLA predictable because imbalances are corrected during the day.<br><br>- It gives managers a single view to coordinate actions. | **Minutes saved = (alerts triggered × reassign mins avoided)** using daily avg **{avg_tix:.1f}** baseline. | Heatmap bands expose surge windows. |
| **Assignment caps** | **Phase 1 – Set:** Define a maximum number of tickets per day per agent based on historic throughput and complexity. Communicate the policy and exceptions in writing. <br><br>**Phase 2 – Enforce:** Route excess tickets to a standby pool with clear ownership and time-boxed pickup rules. Log every spillover so cap values can be audited. <br><br>**Phase 3 – Review:** Evaluate cap effectiveness weekly by checking cycle time and breach rate. Adjust caps or staffing where data shows persistent strain. | - It tightens the spread of workload so cycle time becomes steadier.<br><br>- It reduces firefighting because agents are not overloaded early in the day.<br><br>- It protects quality by keeping focus on a manageable number of tickets.<br><br>- It provides a clear rule to govern daily intake. | **Cycle-time benefit = (Δmedian tickets/agent × avg mins) ÷ day** vs current median **{median_val if 'median_val' in locals() else 0:.1f}**. | Box median/IQR quantify variance. |
""",
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Transparent assignment logic** | **Phase 1 – Publish:** Document how routing works and where exceptions apply, and make this visible to both agents and stakeholders. Clear rules reduce confusion and perceived unfairness. <br><br>**Phase 2 – Monitor:** Track fairness KPIs such as variance from mean load per agent and publish them in the dashboard. Visibility keeps behavior aligned. <br><br>**Phase 3 – Survey:** Gather periodic sentiment on perceived fairness and use the feedback to adjust routing rules or communication. | - It reduces “why me” escalations because the process is clear and auditable.<br><br>- It sets realistic expectations on response order which calms users.<br><br>- It increases trust in support when fairness metrics are visible.<br><br>- It helps agents accept routing decisions because criteria are objective. | **Complaints avoided × handling mins**; size by bar spread (from **{min_val}** to **{max_val}**). | Bar + box highlight fairness gaps. |
| **Priority pairing** | **Phase 1 – Identify:** Maintain a current list of VIP and critical tickets and confirm impact tiers with business owners. This ensures priority is rooted in agreed criteria. <br><br>**Phase 2 – Route:** Send these tickets to balanced-load, skilled agents and equip them with fast-lane macros and escalation paths. <br><br>**Phase 3 – Track:** Compare CSAT and wait time for VIPs versus the general queue and refine rules when gaps persist. | - It lowers wait times for critical users when volume spikes.<br><br>- It raises CSAT by ensuring high impact issues get fast attention.<br><br>- It reduces VIP escalations because progress is visible sooner.<br><br>- It keeps non-VIP work moving by preventing queue gridlock. | **Penalty/churn avoided** tied to peak-day **{peak_val if 'peak_val' in locals() else 0}** absorption. | Heatmap surges drive risk windows. |
| **Customer continuity** | **Phase 1 – Cohort:** Route repeat users to consistent agents and record the pairing in the CRM or ticketing profile. Continuity reduces rediscovery time. <br><br>**Phase 2 – Measure:** Track reopen rate and CSAT for paired users, and compare against a non-paired control group. <br><br>**Phase 3 – Adjust:** Rebalance pairings if load skews or if metrics show no improvement, and keep a small buffer pool to handle absences. | - It speeds diagnosis because the agent already knows the user’s context.<br><br>- It increases first-pass yield by avoiding repeated discovery steps.<br><br>- It improves sentiment because users feel recognized and supported.<br><br>- It trims handle time on repeat incidents through familiarity. | **Reopens avoided × mins** using avg **{avg_tix:.1f}** routing baseline. | Persistent dark rows indicate stable pairings. |
"""
}
            render_cio_tables("CIO Recommendations of Tickets Assigned per Agent", cio_4a)

    # ==========================
    # 📌 Agent Workload (Open Tickets per Agent)
    # ==========================
    with st.expander("📌 Agent Workload (Open Tickets per Agent)"):
        if "technician" in df_filtered.columns and "request_status" in df_filtered.columns:
            # Normalize and define "open"
            rs_norm = df_filtered["request_status"].astype(str).str.lower()
            closed_statuses = {"closed", "resolved"}  # treat "onhold" as open by default
            df_filtered["is_open"] = ~rs_norm.isin(closed_statuses)

            # Graph 1: Tickets assigned per technician (again for context)
            ticket_counts2 = df_filtered.groupby("technician").size().reset_index(name="tickets")
            fig_bar2 = px.bar(
                ticket_counts2, x="technician", y="tickets",
                title="Tickets Assigned per Technician",
                text="tickets",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            fig_bar2.update_traces(textposition="outside")
            st.plotly_chart(fig_bar2, use_container_width=True)

            # Analysis for Graph 1 (context bar)
            if not ticket_counts2.empty:
                total_tix2 = int(ticket_counts2["tickets"].sum())
                avg_tix2 = float(ticket_counts2["tickets"].mean())
                max_row2 = ticket_counts2.loc[ticket_counts2["tickets"].idxmax()]
                min_row2 = ticket_counts2.loc[ticket_counts2["tickets"].idxmin()]
                st.markdown("### Analysis of Tickets Assigned (Context Bar)")
                st.write(f"""
**What this graph is:** A bar chart showing **total assignments** per agent for context.  
**X-axis:** Agent.  
**Y-axis:** Tickets assigned.

**What it shows in your data:**  
- **Highest:** **{max_row2['technician']}** with **{int(max_row2['tickets']):,}**.  
- **Lowest:** **{min_row2['technician']}** with **{int(min_row2['tickets']):,}**.  
- **Average:** **{avg_tix2:.1f}**; **Total:** **{total_tix2:,}**.

**Overall:** Use this as the baseline against current open load to spot **throughput gaps**.
""")

            # Graph 2: Open tickets per technician
            workload = (
                df_filtered[df_filtered["is_open"]]
                .groupby("technician")
                .size()
                .reset_index(name="open_tickets")
            )
            fig_workload = px.bar(
                workload, x="technician", y="open_tickets",
                title="Open Tickets per Technician",
                text="open_tickets",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            fig_workload.update_traces(textposition="outside")
            st.plotly_chart(fig_workload, use_container_width=True)

            # Analysis for Graph 2 (Open bar)
            if not workload.empty:
                total_open = int(workload["open_tickets"].sum())
                avg_open = float(workload["open_tickets"].mean())
                max_open_row = workload.loc[workload["open_tickets"].idxmax()]
                min_open_row = workload.loc[workload["open_tickets"].idxmin()]
                st.markdown("### Analysis of Open Tickets per Technician (Bar)")
                st.write(f"""
**What this graph is:** A bar chart showing **current unresolved workload** per agent.  
**X-axis:** Agent (technician).  
**Y-axis:** Number of open (unresolved) tickets.

**What it shows in your data:**  
- **Highest open load:** **{max_open_row['technician']}** with **{int(max_open_row['open_tickets']):,}** open.  
- **Lowest open load:** **{min_open_row['technician']}** with **{int(min_open_row['open_tickets']):,}** open.  
- **Average open per agent:** **{avg_open:.1f}**; **Total open:** **{total_open:,}**.

**Overall:** A few agents holding much higher open counts indicates **SLA risk** and requires rebalancing.

**How to read it operationally:**  
- **Gap = backlog exposure:** Tallest minus shortest bars reflect **risk concentration**.  
- **Lead–lag:** Compare with assignments; if open >> assigned for an agent, **throughput is constrained**.  
- **Recovery strength:** Monitor whether tall bars shrink post-reassignment.  
- **Control:** Daily **auto-reassign** and WIP limits per agent.

**Why this matters:** Balanced open queues reduce breach probability and improve responsiveness.
""")

            # Graph 3: Average resolution time per technician (robust column detection)
            metric_col = None
            for cand in ["time_elapsed_hours", "time_elapsed", "resolution_time"]:
                if cand in df_filtered.columns:
                    metric_col = cand
                    break

            if metric_col and "technician" in df_filtered.columns:
                tmp = df_filtered.copy()
                # ✅ normalize to hours(float)
                tmp[metric_col] = _to_hours(tmp[metric_col])

                res_time = (
                    tmp.groupby("technician", as_index=False)[metric_col]
                      .mean()
                      .rename(columns={metric_col: "time_elapsed_hours"})
                )

                fig_res_time = px.bar(
                    res_time,
                    x="technician",
                    y="time_elapsed_hours",
                    title="Average Resolution Time per Technician",
                    labels={"time_elapsed_hours": "Avg Resolution Time (hrs)", "technician": "Technician"},
                    text="time_elapsed_hours",
                    color_discrete_sequence=MES_BLUE, template="plotly_white"
                )
                fig_res_time.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                st.plotly_chart(fig_res_time, use_container_width=True)

                # Analysis for Graph 3 (Avg resolution time)
                if not res_time.empty:
                    overall_mean_rt = float(res_time["time_elapsed_hours"].mean())
                    fastest = res_time.loc[res_time["time_elapsed_hours"].idxmin()]
                    slowest = res_time.loc[res_time["time_elapsed_hours"].idxmax()]
                    st.markdown("### Analysis of Average Resolution Time per Technician (Bar)")
                    st.write(f"""
**What this graph is:** A bar chart of **average resolution time** by agent.  
**X-axis:** Agent.  
**Y-axis:** Average resolution time (hours).

**What it shows in your data:**  
- **Fastest:** **{fastest['technician']}** at **{fastest['time_elapsed_hours']:.2f} hrs**.  
- **Slowest:** **{slowest['technician']}** at **{slowest['time_elapsed_hours']:.2f} hrs**.  
- **Overall mean across agents:** **{overall_mean_rt:.2f} hrs**.

**Overall:** Large spread implies **skill/process variability** or **complexity mix** differences.

**How to read it operationally:**  
- **Gap = efficiency delta:** Slowest minus fastest shows **coaching/automation headroom**.  
- **Lead–lag:** If slowest also has high open load, **reassign/support**.  
- **Recovery strength:** Track after coaching to confirm **downward trend**.  
- **Control:** Standard playbooks, KB snippets, and macros.

**Why this matters:** Faster, consistent resolution protects SLA and reduces cost per ticket.
""")

                # Graph 3b: Trend line per technician (normalize first)
                if "created_time" in df_filtered.columns:
                    df_rt = df_filtered.copy()
                    df_rt[metric_col] = _to_hours(df_rt[metric_col])

                    df_rt["created_month"] = pd.to_datetime(
                        df_rt["created_time"], errors="coerce"
                    ).dt.to_period("M").astype(str)

                    monthly_res = df_rt.dropna(subset=["created_month", metric_col]).groupby(
                        ["created_month", "technician"], as_index=False
                    )[metric_col].mean().rename(columns={metric_col: "avg_res_time"})

                    if not monthly_res.empty:
                        monthly_res["created_month_dt"] = pd.to_datetime(monthly_res["created_month"], format="%Y-%m", errors="coerce")
                        monthly_res = monthly_res.sort_values(["technician", "created_month_dt"])

                        fig_res_trend = px.line(
                            monthly_res, x="created_month", y="avg_res_time", color="technician",
                            title="Resolution Time Trend per Technician",
                            labels={"avg_res_time": "Avg Resolution Time (hrs)", "created_month": "Month"},
                            color_discrete_sequence=MES_BLUE, template="plotly_white"
                        )
                        st.plotly_chart(fig_res_trend, use_container_width=True)

                        # Analysis for Graph 3b (Trend)
                        mom = monthly_res.copy()
                        mom["pct_change"] = mom.groupby("technician")["avg_res_time"].pct_change() * 100.0
                        spike_line = ""
                        if mom["pct_change"].notna().any():
                            spike_row = mom.loc[mom["pct_change"].idxmax()]
                            spike_line = f"**Largest MoM spike:** **{spike_row['technician']}** +**{spike_row['pct_change']:.1f}%** to **{spike_row['avg_res_time']:.2f} hrs** in **{spike_row['created_month']}**."

                        st.markdown("### Analysis of Resolution Time Trend per Technician (Line)")
                        st.write(f"""
**What this graph is:** A multi-line trend of **monthly average resolution time** for each agent.  
**X-axis:** Month.  
**Y-axis:** Average resolution time (hours).

**What it shows in your data:**  
{spike_line if spike_line else "- No measurable month-over-month spike detected."}

**Overall:** Rising lines = **worsening speed**; falling lines = **improvement**.

**How to read it operationally:**  
- **Gap = pattern risk:** Long rising runs point to **systemic issues**.  
- **Lead–lag:** Post-spike recovery speed reflects **resilience**.  
- **Control:** Capture best-month practices and replicate.

**Why this matters:** Stabilizing trends reduces SLA breaches and escalations.
""")

            # ------- CIO for 4(b) with real values -------
            if not workload.empty:
                w_max_t = str(max_open_row["technician"])
                w_max_v = int(max_open_row["open_tickets"])
                w_min_t = str(min_open_row["technician"])
                w_min_v = int(min_open_row["open_tickets"])
            else:
                w_max_t, w_max_v, w_min_t, w_min_v, total_open, avg_open = "N/A", 0, "N/A", 0, 0, 0.0

            cio_4b = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Auto-rebalance open queues** | **Phase 1 – Detect:** Flag agents whose open count exceeds the mean (**{avg_open:.1f}**) by a configurable threshold and generate a case list ready for reassignment. This ensures movement happens before aging becomes critical. <br><br>**Phase 2 – Reassign:** Spill excess items to qualified low-load agents using pre-agreed rules and capture the handoff rationale in the ticket. <br><br>**Phase 3 – Verify:** Check next-day backlog deltas and confirm that reassignments actually reduced aging without spiking reopen rates. | - It cuts overtime by moving excess work before it ages into the weekend.<br><br>- It lowers carry-over cost because fewer tickets linger unresolved.<br><br>- It makes peak handling cheaper since reassignments happen during standard hours.<br><br>- It protects team morale by avoiding chronic overload on a few agents. | **Savings = (tickets rebalanced × mins/ticket ÷ 60 × OT rate)**; target tall-bar delta **{w_max_v - int(round(avg_open))}** on **{w_max_t}**. | Open bar shows **{w_max_t}={w_max_v}** vs **{w_min_t}={w_min_v}**; total open **{total_open:,}**. |
| **Aging-aware WIP limits** | **Phase 1 – Set:** Define a maximum open count per agent and mark any case above the p80 age as must-pull within the next interval. This aligns work with risk. <br><br>**Phase 2 – Gate:** Pause low-value intake when agents are above cap and route new work to a buffered pool until recovery. <br><br>**Phase 3 – Review:** Inspect weekly p80 age trends and adjust limits or staffing if the age tail refuses to shrink. | - It prevents silent aging by forcing attention to older riskier tickets.<br><br>- It reduces SLA breaches because long-waiting items are pulled forward in time.<br><br>- It minimizes end-week rushes that create quality issues.<br><br>- It keeps work visible so leaders can intervene early. | **Penalty avoided = (# breaches avoided × penalty)** sized from cases over cap on **{w_max_t}**. | Excess bars flag cap breach risk. |
| **Hot-handoff for stalled items** | **Phase 1 – Flag:** Detect tickets with no progress for more than N hours and enrich them with last action, owner, and blockers. This makes the stall visible and actionable. <br><br>**Phase 2 – Pair:** Create a short, time-boxed session between a senior and the owner to decide and execute the next concrete step. <br><br>**Phase 3 – Log:** Capture stall causes so systemic blockers can be eliminated and future stalls decline. | - It unblocks stuck tickets quickly which lowers dwell time.<br><br>- It reduces rework by getting the right help at the right moment.<br><br>- It keeps momentum so queues do not freeze behind stalled items.<br><br>- It builds a data trail that shows systemic blockers to fix. | **Minutes saved = (stalled items × avg dwell trimmed)** using open excess **{w_max_v - int(round(avg_open))}**. | Tallest open bar indicates stall likelihood. |
""",
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Dynamic load balancing** | **Phase 1 – Telemetry:** Stream live open and closed counts per agent with age buckets and SLA risk. This provides a single operational truth. <br><br>**Phase 2 – Policy:** Automatically reassign items when agents exceed caps or when age thresholds are crossed, and notify both owners. <br><br>**Phase 3 – Audit:** Measure the change in daily throughput and breach rate after policy triggers to confirm impact and tune thresholds. | - It lifts daily throughput by routing work to where capacity exists.<br><br>- It removes bottlenecks that form when one queue runs hot.<br><br>- It creates a predictable burn-down so teams can plan work.<br><br>- It smooths handoffs by using data rather than ad hoc requests. | **Throughput lift = (Δclosed/day after policy × days)** vs mean. | Open spread shows headroom. |
| **Idle-time harvest** | **Phase 1 – Surface:** Identify agents under the mean (**{avg_open:.1f}**) and present a ready-to-pull list sorted by risk and size. <br><br>**Phase 2 – Feed:** Pre-stage the next item for those agents so they can pick up quickly without context switching. <br><br>**Phase 3 – Track:** Monitor SLA catch-up and adjust the feed mix if progress stalls. | - It improves utilization by filling small idle windows with ready work.<br><br>- It clears tickets that are near SLA limits faster.<br><br>- It balances experience across the team through steady exposure to work.<br><br>- It reduces context switching because items are pre-staged. | **Utilization gain = (idle hrs captured × rate)** using low bar (**{w_min_t}={w_min_v}**). | Low bars indicate latent capacity. |
| **Priority-first routing** | **Phase 1 – Reorder:** Sort queues by SLA and impact tiers so high-risk items are visible at the top of every list. <br><br>**Phase 2 – Enforce:** Apply queue rules that prevent low-priority work from displacing urgent items unless explicitly approved. <br><br>**Phase 3 – Monitor:** Review breach trends and adjust rules when patterns show unintended side effects. | - It lowers breach rate by placing high-impact items at the front of the line.<br><br>- It improves on-time delivery during load spikes.<br><br>- It makes decision making simpler because routing rules are explicit.<br><br>- It keeps stakeholder risk visible and under control. | **Penalty avoided = (breaches avoided × penalty)** after routing. | Tall bars plus SLA tail confirm need. |
""",
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Proactive backlog alerts** | **Phase 1 – Thresholds:** Define alert points at mean plus N and specify which user cohorts should be notified. Clear rules avoid mixed messages. <br><br>**Phase 2 – Message:** Send a concise ETA and next action so users know when to expect movement and what they can do meanwhile. <br><br>**Phase 3 – Review:** Track complaint trends and refine the cadence if noise remains high. | - It reduces follow-up chaser messages because users know the plan and timing.<br><br>- It calms sentiment by showing ownership during busy periods.<br><br>- It increases transparency so customers feel progress is underway.<br><br>- It turns potential escalations into informed waiting. | **Handling time avoided = (complaints avoided × mins)** sized from tall-bar days (**{w_max_t}**). | Open bar concentration implies anxiety risk. |
| **VIP fast lane** | **Phase 1 – Tag:** Keep a live list of VIP or critical users and confirm it with account owners to prevent drift. <br><br>**Phase 2 – Route:** Assign these cases to low-load, skilled agents and use expedited callbacks to maintain momentum. <br><br>**Phase 3 – Confirm:** Verify with a short follow-up message that fixes met expectations and capture feedback. | - It protects key relationships by cutting VIP wait times when queues are long.<br><br>- It reduces escalations from strategic accounts because outcomes are faster.<br><br>- It preserves brand perception during incidents that attract attention.<br><br>- It ensures service recovery feels intentional and responsive. | **Escalation cost avoided** where tracked; sized on excess **{w_max_v - int(round(avg_open))}**. | Tallest bars are highest risk for VIPs. |
| **Status cadence by age** | **Phase 1 – Schedule:** Define an update rhythm based on ticket age bands so long-running cases never go silent. <br><br>**Phase 2 – Automate:** Use portal or email pushes that are templated and easy to localize by category. <br><br>**Phase 3 – Monitor:** Compare CSAT and inbound contact volumes before and after rollout and adjust cadence to minimize noise. | - It reduces uncertainty by keeping users informed at regular intervals.<br><br>- It lowers inbound calls and emails because updates arrive proactively.<br><br>- It improves CSAT as expectations align with actual progress.<br><br>- It signals control and professionalism during long fixes. | **Time saved = (status calls avoided × mins)** as open falls toward mean. | Declining bars should track fewer calls. |
"""
}


            render_cio_tables("CIO Recommendations – Agent Workload", cio_4b)

    # ==========================
    # 📌 Average Resolution Time per Agent
    # ==========================
    with st.expander("📌 Average Resolution Time per Agent"):
        # Accept either 'resolution_time' or 'time_elapsed' as resolution measure
        resolution_col = None
        if "resolution_time" in df_filtered.columns:
            resolution_col = "resolution_time"
        elif "time_elapsed" in df_filtered.columns:
            resolution_col = "time_elapsed"

        if "technician" in df_filtered.columns and resolution_col is not None:
            dfr = df_filtered.copy()
            # ✅ normalize to hours(float)
            dfr[resolution_col] = _to_hours(dfr[resolution_col])

            # --- Graph 1: Bar average resolution time
            avg_time = dfr.groupby("technician")[resolution_col].mean().reset_index().sort_values(resolution_col, ascending=False)
            fig_res_bar = px.bar(
                avg_time, x="technician", y=resolution_col,
                title="Average Resolution Time per Agent",
                labels={resolution_col: "Avg Resolution Time (hrs)", "technician": "Technician"},
                text=resolution_col,
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            fig_res_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig_res_bar, use_container_width=True)

            # Structured analysis for Bar
            if not avg_time.empty:
                total_agents = len(avg_time)
                overall_mean = float(dfr[resolution_col].mean())
                overall_median = float(dfr[resolution_col].median())
                overall_std = float(dfr[resolution_col].std(ddof=0)) if dfr[resolution_col].notna().sum() > 1 else 0.0
                top_row = avg_time.iloc[0]
                bot_row = avg_time.iloc[-1]
                st.markdown("### Analysis of Average Resolution Time per Agent (Bar)")
                st.write(f"""
**What this graph is:** A bar chart showing **mean resolution time** by agent.  
**X-axis:** Agent.  
**Y-axis:** Average resolution time (hours).

**What it shows in your data:**  
- **Slowest agent:** **{top_row['technician']}** at **{top_row[resolution_col]:.2f} hrs**.  
- **Fastest agent:** **{bot_row['technician']}** at **{bot_row[resolution_col]:.2f} hrs**.  
- **Overall mean/median/std:** **{overall_mean:.2f} / {overall_median:.2f} / {overall_std:.2f} hrs**.

**Overall:** The spread quantifies **coaching/automation upside**.

**How to read it operationally:**  
- **Gap = efficiency delta:** Slowest − fastest shows headroom.  
- **Lead–lag:** Cross-check with assignments and open load to triage causes.  
- **Recovery strength:** Re-measure after coaching/macro rollouts.  
- **Control:** Normalize frequent fixes via KB/macros.

**Why this matters:** Lower, tighter bars lower cost and breach risk.
""")

            # --- Graph 2: Box plot per agent
            fig_res_box = px.box(
                dfr, x="technician", y=resolution_col, points="outliers",
                title="Resolution Time Variation per Agent",
                labels={resolution_col: "Resolution Time (hrs)", "technician": "Technician"},
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig_res_box, use_container_width=True)

            # Structured analysis for Box
            if dfr[resolution_col].notna().any():
                outlier_rows = []
                for tech, grp in dfr.groupby("technician"):
                    vals = grp[resolution_col].dropna().values
                    if len(vals) == 0:
                        continue
                    q1 = np.percentile(vals, 25)
                    q3 = np.percentile(vals, 75)
                    iqr = q3 - q1
                    lf = q1 - 1.5 * iqr
                    uf = q3 + 1.5 * iqr
                    outliers = ((vals < lf) | (vals > uf)).sum()
                    med = np.median(vals)
                    outlier_rows.append((tech, med, iqr, outliers))
                outlier_rows.sort(key=lambda x: x[3], reverse=True)
                top_outlier_line = (
                    f"Most outliers on **{outlier_rows[0][0]}** (median **{outlier_rows[0][1]:.2f} hrs**, IQR **{outlier_rows[0][2]:.2f}**, outliers **{outlier_rows[0][3]}**)."
                    if outlier_rows else "No outliers detected."
                )

                st.markdown("### Analysis of Resolution Time Variation per Agent (Box)")
                st.write(f"""
**What this graph is:** A box plot showing **distribution + outliers** of resolution time per agent.  
**X-axis:** Agent.  
**Y-axis:** Resolution time (hours).

**What it shows in your data:**  
- {top_outlier_line}

**Overall:** Many outliers or wide IQRs highlight **instability** and rework risk.

**How to read it operationally:**  
- **Gap = stability delta:** Wide boxes mean inconsistent execution.  
- **Lead–lag:** Post-macro rollout, IQR should **tighten**.  
- **Control:** Audit top-outlier agents’ workflows.

**Why this matters:** Less spread → more predictable SLA and happier customers.
""")

            # --- Graph 3: Trend line monthly (if created_time exists)
            if "created_time" in dfr.columns:
                dfr["created_month"] = pd.to_datetime(dfr["created_time"], errors="coerce").dt.to_period("M").astype(str)
                monthly_res2 = dfr.dropna(subset=["created_month", resolution_col]).groupby(
                    ["created_month", "technician"], as_index=False
                )[resolution_col].mean().rename(columns={resolution_col: "avg_res_time"})

                if not monthly_res2.empty:
                    monthly_res2["created_month_dt"] = pd.to_datetime(monthly_res2["created_month"], format="%Y-%m", errors="coerce")
                    monthly_res2 = monthly_res2.sort_values(["technician", "created_month_dt"])

                    fig_res_trend2 = px.line(
                        monthly_res2, x="created_month", y="avg_res_time", color="technician",
                        title="Resolution Time Trend per Agent",
                        labels={"avg_res_time": "Avg Resolution Time (hrs)", "created_month": "Month"},
                        color_discrete_sequence=MES_BLUE, template="plotly_white"
                    )
                    st.plotly_chart(fig_res_trend2, use_container_width=True)

                    # Structured analysis for Trend
                    mom2 = monthly_res2.copy()
                    mom2["pct_change"] = mom2.groupby("technician")["avg_res_time"].pct_change() * 100.0
                    if mom2["pct_change"].notna().any():
                        sr = mom2.loc[mom2["pct_change"].idxmax()]
                        spike_line2 = f"**Largest MoM spike:** **{sr['technician']}** +**{sr['pct_change']:.1f}%** to **{sr['avg_res_time']:.2f} hrs** in **{sr['created_month']}**."
                    else:
                        spike_line2 = "- No measurable month-over-month spike detected."

                    st.markdown("### Analysis of Resolution Time Trend (Line)")
                    st.write(f"""
**What this graph is:** A trend of **monthly average resolution time** per agent.  
**X-axis:** Month.  
**Y-axis:** Average resolution time (hours).

**What it shows in your data:**  
{spike_line2}

**Overall:** Lines trending down reflect **learning/automation**; uptrends require attention.

**How to read it operationally:**  
- **Gap = improvement headroom:** Use best months as a target.  
- **Lead–lag:** Watch if interventions reduce spikes the following month.  
- **Control:** Lock in best practices that precede declines.

**Why this matters:** Trend control keeps SLA steady and cost/unit down.
""")

            # ------- CIO for 4(c) with real values -------
            if 'avg_time' in locals() and not avg_time.empty:
                slow_t, slow_v = str(top_row["technician"]), float(top_row[resolution_col])
                fast_t, fast_v = str(bot_row["technician"]), float(bot_row[resolution_col])
            else:
                slow_t, slow_v, fast_t, fast_v, overall_mean = "N/A", 0.0, "N/A", 0.0, 0.0

            cio_4c = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **KB & macro optimization** | **Phase 1 – Mine:** Analyze repetitive fixes from the slowest agent’s queue (**{slow_t}**) to identify steps that can be scripted. Use sample tickets and note exact fields and replies. <br><br>**Phase 2 – Macro:** Convert multi-step actions into guided one-click macros with embedded validations and required fields. <br><br>**Phase 3 – Rollout:** Publish the macros, train agents in a short session, and track the change in average time over two weeks to confirm impact. | - It cuts minutes per ticket by turning multi-step fixes into guided one-click actions.<br><br>- It narrows variation between agents so results are more predictable.<br><br>- It raises first-pass yield because required information is captured correctly at the start.<br><br>- It absorbs peaks without extra headcount by shaving time off high-volume tasks. | **Savings = (Δhrs per ticket × tickets/month × rate)**; set Δhrs = (**{slow_v:.2f} − {fast_v:.2f}**) using fast agent **{fast_t}** as benchmark. | Bar shows **{slow_t}={slow_v:.2f}h** vs **{fast_t}={fast_v:.2f}h**; mean **{overall_mean if 'overall_mean' in locals() else 0:.2f}h**. |
| **Standardized workflows** | **Phase 1 – Map:** Document step-by-step flows for the top categories, including decision points and data requirements. This makes hidden work explicit. <br><br>**Phase 2 – Guardrails:** Add checklists and auto-validation to prevent missing information or incorrect sequencing. <br><br>**Phase 3 – Audit:** Review error and reopen trends weekly to confirm that the workflow reduces variation and rework. | - It reduces missed steps and rework so tickets close faster and stay closed.<br><br>- It shortens cycle times which makes planning and staffing more accurate.<br><br>- It speeds new-joiner ramp-up because the correct method is embedded in the flow.<br><br>- It delivers consistent quality across shifts which stabilizes SLA outcomes. | **Cost avoidance = (reopens avoided × avg rework hrs × rate)**; tie to box outlier counts. | Box plot shows high spread/outliers. |
| **Tooling uplift for slow paths** | **Phase 1 – Pinpoint:** Identify the longest sub-tasks within the slow agent’s cases and quantify the time spent. <br><br>**Phase 2 – Automate:** Build scripts or integrations that remove manual steps such as copy-paste or system hopping. <br><br>**Phase 3 – Verify:** Measure the reduction in task duration and confirm that quality remains stable or improves. | - It removes manual bottlenecks like copy and paste or repeated lookups.<br><br>- It pulls in the right-hand tail of very long tickets so averages improve.<br><br>- It frees senior time for complex issues instead of routine toil.<br><br>- It improves predictability because there are fewer fragile manual steps. | **Minutes saved = (task mins saved × frequency)** drawn from slow agent delta **{(slow_v - fast_v):.2f}h**. | Bar + trend expose slow paths and spikes. |
""",
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Coaching for slowest agents** | **Phase 1 – Shadow:** Review ten recent tickets for **{slow_t}** and note specific behaviors that extend time. <br><br>**Phase 2 – Coach:** Address the top two bottlenecks with concrete practice, scripts, or checklists that can be applied immediately. <br><br>**Phase 3 – Re-measure:** Compare two-week averages before and after coaching to ensure the change is durable. | - It targets the exact behaviors that drive delays such as late escalations or incomplete notes.<br><br>- It pulls close times down toward the team baseline without extra hiring.<br><br>- It reduces escalations that consume senior attention and delay others.<br><br>- It lifts SLA hit rate by fixing root behaviors quickly. | **Gain = (({slow_v:.2f} − target hrs) × tickets) × rate** with target anchored to **{fast_v:.2f}h**. | Bar spread quantifies headroom. |
| **Category-specific macros** | **Phase 1 – Create:** Build macros for the top five categories based on the most common paths and required fields. <br><br>**Phase 2 – Enforce:** Make macros the default path for those categories and log any manual deviations. <br><br>**Phase 3 – Monitor:** Track median time by category and reduce steps where data shows friction. | - It shrinks decision time because the next step is pre-wired for common cases.<br><br>- It improves data capture quality which avoids back-and-forth clarifications.<br><br>- It reduces variation across agents which makes outcomes steadier.<br><br>- It raises first-touch completion so median time falls even under load. | **Time saved = (Δmedian hrs × tickets in category)**. | Box and median shifts validate impact. |
| **SLO-driven sequencing** | **Phase 1 – Queue:** Order work by time-to-breach so agents always see the most time-sensitive cases first. <br><br>**Phase 2 – Act:** Swarm near-breach items with quick unblocks and senior attention to prevent last-minute crises. <br><br>**Phase 3 – Track:** Monitor breach rate and adjust thresholds to keep risk inside acceptable bands. | - It prevents last-minute firefighting by working the right items first.<br><br>- It stabilizes daily throughput so fewer tickets spill over to the next day.<br><br>- It cuts penalty exposure by keeping focus on near-breach work.<br><br>- It gives leads a clear lever to control daily risk. | **Penalty avoided = (breaches avoided × penalty)** post sequencing. | Trend spikes precede breach clusters. |
""",
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Uniform SLA targets** | **Phase 1 – Align:** Set team-wide SLA targets per category and communicate them to both agents and stakeholders. <br><br>**Phase 2 – Coach:** Work with outliers to meet targets using examples from peers who already perform well. <br><br>**Phase 3 – Publish:** Share a weekly heatmap so improvements are visible and drift is caught early. | - It removes ambiguity for both users and agents so expectations match reality.<br><br>- It gives customers predictable ETAs which reduces frustration.<br><br>- It builds trust because performance is tracked and visible.<br><br>- It helps managers spot drift quickly when a cohort falls behind target. | **ROI = (SLA compliance uplift × retention value)** grounded on mean **{overall_mean if 'overall_mean' in locals() else 0:.2f}h**. | Bars trending down should align with CSAT up. |
| **Post-resolution survey hooks** | **Phase 1 – Auto-send:** Trigger a short survey immediately after closure with clear, context-aware questions. <br><br>**Phase 2 – Tag:** Record agent and category so insights can be routed to the right owners. <br><br>**Phase 3 – Improve:** Act on low scores within the same week and verify whether fixes change scores in the next cohort. | - It creates a fast feedback loop that highlights friction you can fix this week.<br><br>- It directs coaching to specific interactions rather than general advice.<br><br>- It reduces repeat defects that drive complaints and reopens.<br><br>- It turns anecdotes into measurable themes that guide the roadmap. | **Value = (complaints avoided × mins)** after macro/coaching rollouts. | Falling means should track CSAT lift. |
| **Expectation management** | **Phase 1 – ETA bands:** Provide estimated time ranges based on historical means and complexity, and explain what the numbers mean. <br><br>**Phase 2 – Update:** Send proactive updates when delays occur and include the reason and the next checkpoint. <br><br>**Phase 3 – Review:** Compare promised versus actual times and refine bands to stay credible. | - It cuts “any update” noise by setting clear timelines up front.<br><br>- It keeps customers feeling in control during longer fixes through proactive updates.<br><br>- It reduces complaint volume as uncertainty drops.<br><br>- It improves NPS and CSAT because surprises are replaced with steady communication. | **Time saved = (complaints avoided × mins)** as averages converge to target. | Trend stabilization reduces inbound. |
"""
}

            render_cio_tables("CIO Recommendations – Resolution Time", cio_4c)

        else:
            st.warning("⚠️ Resolution time analysis not available: required columns (`technician`, `resolution_time` or `time_elapsed`) missing.")

    # ==========================
    # 📌 Customer Satisfaction Ratings per Agent
    # ==========================
    with st.expander("📌 Customer Satisfaction Ratings per Agent"):
        if "technician" in df_filtered.columns and "csat" in df_filtered.columns:
            # Graph 1: Bar (avg CSAT per agent)
            avg_csat = df_filtered.groupby("technician")["csat"].mean().reset_index()
            fig_csat_bar = px.bar(
                avg_csat, x="technician", y="csat",
                title="Customer Satisfaction per Agent",
                text="csat",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            fig_csat_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig_csat_bar, use_container_width=True)

            # Analysis for Graph 1 (CSAT bar)
            if not avg_csat.empty:
                csat_mean = float(avg_csat["csat"].mean())
                best_csat = avg_csat.loc[avg_csat["csat"].idxmax()]
                worst_csat = avg_csat.loc[avg_csat["csat"].idxmin()]
                st.markdown("### Analysis of Customer Satisfaction per Agent (Bar)")
                st.write(f"""
**What this graph is:** A bar chart of **average CSAT** by agent.  
**X-axis:** Agent.  
**Y-axis:** Average CSAT score.

**What it shows in your data:**  
- **Highest CSAT:** **{best_csat['technician']}** at **{best_csat['csat']:.2f}**.  
- **Lowest CSAT:** **{worst_csat['technician']}** at **{worst_csat['csat']:.2f}**.  
- **Overall mean:** **{csat_mean:.2f}**.

**Overall:** Variance signals **coaching/consistency** opportunities.

**How to read it operationally:**  
- **Gap = quality delta:** High minus low marks the training gap.  
- **Lead–lag:** Tie to resolution speed and open load to explain dips.  
- **Control:** Standardize comms cadence and closure notes.

**Why this matters:** Higher CSAT reduces complaints and churn.
""")

            # Graph 2: Heatmap CSAT over time
            if "created_time" in df_filtered.columns:
                df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date
                csat_trend = df_filtered.groupby(["created_date", "technician"])["csat"].mean().reset_index()
                csat_pivot = csat_trend.pivot(index="created_date", columns="technician", values="csat").fillna(0)
                fig_csat_heat = px.imshow(
                    csat_pivot.T,
                    title="CSAT Trends per Agent Over Time",
                    labels=dict(x="Date", y="Agent", color="CSAT"),
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_csat_heat, use_container_width=True)

                # Analysis for Graph 2 (CSAT heatmap)
                pv2 = csat_pivot.stack()
                if not pv2.empty:
                    peak_idx2 = pv2.idxmax()
                    peak_val2 = float(pv2.max())
                    peak_date2, peak_tech2 = peak_idx2[0], peak_idx2[1]
                    st.markdown("### Analysis of CSAT Trends per Agent (Heatmap)")
                    st.write(f"""
**What this graph is:** A heatmap of **daily CSAT** by agent.  
**X-axis:** Date.  
**Y-axis:** Agent.  
**Color:** CSAT score (higher = better).

**What it shows in your data:**  
- **Peak cell:** **{peak_tech2}** on **{peak_date2}** with **CSAT {peak_val2:.2f}**.

**Overall:** Warm bands = **strong satisfaction**; cool bands = **attention points**.

**How to read it operationally:**  
- **Gap = experience delta:** Cold stretches need comms/tone coaching.  
- **Lead–lag:** Compare to open load; high load often depresses CSAT.  
- **Control:** Trigger coaching when a rolling window dips below target.

**Why this matters:** Sustained warmth correlates with loyalty and fewer escalations.
""")

            # Graph 3: Scatter CSAT vs resolution time
            if "resolution_time" in df_filtered.columns:
                # If resolution_time might be timedelta/strings, normalize for correlation axis scale (hours)
                sc = df_filtered[["resolution_time", "csat", "technician"]].dropna().copy()
                sc["resolution_time"] = _to_hours(sc["resolution_time"])

                fig_scatter = px.scatter(
                    sc, x="resolution_time", y="csat", color="technician",
                    title="CSAT vs Resolution Time per Agent", trendline="ols",
                    color_discrete_sequence=MES_BLUE, template="plotly_white"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

                # Analysis for Graph 3 (Scatter)
                corr_line = ""
                if not sc.empty:
                    corr = float(pd.to_numeric(sc["resolution_time"], errors="coerce").corr(sc["csat"]))
                    corr_line = f"**Correlation (resolution→CSAT): {corr:.2f}** (negative is good)."
                st.markdown("### Analysis of CSAT vs Resolution Time (Scatter)")
                st.write(f"""
**What this graph is:** A scatter plot of **CSAT** against **resolution time**, colored by agent.  
**X-axis:** Resolution time (hours).  
**Y-axis:** CSAT.

**What it shows in your data:**  
- {corr_line if corr_line else "No correlation computed (insufficient data)."}

**Overall:** Faster resolution typically **raises CSAT** up to a point; overly fast but incomplete fixes can hurt.

**How to read it operationally:**  
- **Gap = trade-off:** Find the **sweet spot** band for your context.  
- **Lead–lag:** If CSAT dips **after** spikes in time, capacity constraints are biting.  
- **Control:** Use macros and status cadences to keep time inside the sweet spot.

**Why this matters:** Higher CSAT at steady speed is the customer outcome you’re paid for.
""")

            # ------- CIO for 4(d) with real values -------
            if "resolution_time" in df_filtered.columns and "csat" in df_filtered.columns:
                rt_hours = _to_hours(df_filtered["resolution_time"])
                rt_mean = float(rt_hours.dropna().mean()) if rt_hours.notna().any() else 0.0
                csat_overall = float(df_filtered["csat"].dropna().mean()) if df_filtered["csat"].notna().any() else 0.0
            else:
                rt_mean, csat_overall = 0.0, 0.0

            if not avg_csat.empty:
                best_t, best_v = str(best_csat["technician"]), float(best_csat["csat"])
                worst_t, worst_v = str(worst_csat["technician"]), float(worst_csat["csat"])
            else:
                best_t, best_v, worst_t, worst_v, csat_mean = "N/A", 0.0, "N/A", 0.0, 0.0

            cio_4d = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Focused coaching for low-CSAT agents** | **Phase 1 – Diagnose:** Review recent calls and tickets for **{worst_t}** to identify patterns such as unclear summaries or missed expectation setting. <br><br>**Phase 2 – Coach:** Provide targeted guidance on tone, clarity, and forward-looking statements, and practice with real examples. <br><br>**Phase 3 – Re-score:** Measure the CSAT change two weeks after coaching and confirm that the improvement holds. | - It reduces escalations and rework that start with unclear communication.<br><br>- It lowers complaint-handling time for leads by fixing issues earlier.<br><br>- It standardizes tone and clarity so users experience consistent service.<br><br>- It lifts CSAT quickly without increasing average handle time. | **Savings = (escalations avoided × mins/escalation × rate)** sized by CSAT gap (**{best_v:.2f} − {worst_v:.2f}**). | Bar shows **best {best_t}={best_v:.2f}** vs **worst {worst_t}={worst_v:.2f}**; mean **{(avg_csat['csat'].mean() if not avg_csat.empty else 0):.2f}**. |
| **Automated survey + reminders** | **Phase 1 – Trigger:** Send a survey automatically on closure using short, relevant questions that match the case type. <br><br>**Phase 2 – Remind:** Nudge non-responders at T+24h with a single follow-up to avoid fatigue while improving response rates. <br><br>**Phase 3 – Mine:** Use basic text analytics to extract themes and route insights to the right owners. | - It replaces manual outreach with automation which frees analyst time for insights.<br><br>- It raises response rates so signals are statistically stronger.<br><br>- It accelerates detection of issues while they are still actionable.<br><br>- It improves trend visibility because sampling bias is reduced. | **Cost reduction = (manual survey hrs replaced × rate)** with volume tied to closes. | Heatmap coverage improves; fewer blind spots. |
| **Resolution-note templates** | **Phase 1 – Standardize:** Provide a clear structure for summaries, steps taken, and prevention tips so notes are complete and easy to read. <br><br>**Phase 2 – Localize:** Tailor templates by category and include fields that force the right level of detail. <br><br>**Phase 3 – Track:** Measure CSAT uplift per template and refine content based on feedback. | - It cuts follow-up questions by making outcomes and next steps obvious.<br><br>- It educates users so repeat incidents are less likely.<br><br>- It reduces reopen risk caused by unclear or missing details.<br><br>- It creates reusable knowledge assets that compound over time. | **Time saved = (follow-ups avoided × mins)**; link to correlation vs mean time **{rt_mean:.2f}h**. | Scatter indicates speed–CSAT relationship to tune notes. |
""",
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Best-practice playbooks** | **Phase 1 – Capture:** Document techniques from top agent **{best_t}** including phrases, triage steps, and closure patterns that correlate with high CSAT. <br><br>**Phase 2 – Share:** Package them into scripts and macros and make them easy to access inside the workflow. <br><br>**Phase 3 – Monitor:** Track the change in CSAT and handle time after rollout and update playbooks when data shows drift. | - It scales what already works so average CSAT improves across the team.<br><br>- It reduces time per ticket by guiding agents through proven steps.<br><br>- It shrinks performance variance between agents as playbooks standardize actions.<br><br>- It ramps new hires faster because learning is structured. | **Gain = (CSAT uplift × retention value)** using baseline **{csat_overall:.2f}**. | Bars converge upward after rollout. |
| **Load-aware comms cadence** | **Phase 1 – Detect:** Identify agents with high open load where silence is most damaging to sentiment. <br><br>**Phase 2 – Push:** Apply a proactive status cadence to those queues so users receive updates without asking. <br><br>**Phase 3 – Review:** Compare CSAT deltas before and after cadence and keep the practice where it clearly helps. | - It protects sentiment during spikes by setting expectations early.<br><br>- It deflects status-check calls that would slow down resolution work.<br><br>- It reduces escalations that often start with silence or uncertainty.<br><br>- It keeps CSAT stable even when demand is temporarily high. | **Time saved = (calls avoided × mins)** on tall-bar agents. | Open vs CSAT trends align improvements. |
| **Speed guardrails** | **Phase 1 – Band:** Define a realistic sweet-spot window for resolution time based on history and case complexity. <br><br>**Phase 2 – Alert:** Notify agents when cases sit outside the band so they can accelerate or slow down to maintain quality. <br><br>**Phase 3 – Fix:** Apply macros or reassignment to bring cases back into the target zone and confirm the effect in trends. | - It prevents rushed or dragged resolutions that harm satisfaction.<br><br>- It alerts teams early so they can correct course before sentiment drops.<br><br>- It keeps most tickets inside a time window where quality and speed balance well.<br><br>- It gives leaders a simple rule to prioritize interventions. | **Penalty avoidance = (CSAT dip cases avoided × value)** using scatter banding. | Scatter reveals optimum region. |
""",
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Recognize high-CSAT agents** | **Phase 1 – Publish:** Share a monthly leaderboard that highlights consistent performance and explains the criteria. <br><br>**Phase 2 – Reward:** Offer small, visible rewards such as badges or bonuses that reinforce desired behaviors. <br><br>**Phase 3 – Mentor:** Pair top performers with lower scorers for short mentoring sessions and measure the transfer effect. | - It boosts motivation and reinforces behaviors that drive strong outcomes.<br><br>- It creates positive peer pressure to maintain high standards.<br><br>- It lifts the floor through mentoring that transfers practical techniques.<br><br>- It reduces attrition risk for top performers who feel valued. | **ROI = (uplift in CSAT × retention value)** led by **{best_t}**. | Bar highlights star performers. |
| **Customer-agent continuity** | **Phase 1 – Route:** Where practical, send repeat users to agents with strong CSAT and relevant history. This preserves context and reduces friction. <br><br>**Phase 2 – Monitor:** Track changes in reopen and CSAT rates for these users and compare against a control group. <br><br>**Phase 3 – Adjust:** Rebalance when loads skew or results plateau and keep a record of pairings for coverage planning. | - It carries context forward so users do not need to re-explain details.<br><br>- It shortens diagnosis time because history is understood.<br><br>- It raises satisfaction through familiarity and consistent communication.<br><br>- It reduces friction and handle time on repeat incidents. | **Value = (reopens avoided × mins + upsell/renewal impact)**. | Heat patterns warm under continuity. |
| **Expectation setting at open** | **Phase 1 – Send:** Provide an ETA and clear next steps at ticket creation so users know what will happen first. <br><br>**Phase 2 – Update:** When delays occur, give a succinct reason and a new checkpoint time instead of vague apologies. <br><br>**Phase 3 – Review:** Compare promised versus actual timelines and refine estimates to stay credible over time. | - It makes the journey predictable from the first message which calms users.<br><br>- It cuts complaint volume that is driven by uncertainty.<br><br>- It smooths the experience during unavoidable delays by keeping users informed.<br><br>- It builds trust that the case is owned and progressing. | **Time saved = (complaints avoided × mins)** when trend stabilizes. | Scatter/CSAT bars improve as ETAs normalize. |
"""
}

            render_cio_tables("CIO Recommendations – Customer Satisfaction", cio_4d)
