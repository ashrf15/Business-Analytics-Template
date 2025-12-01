import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose

# ---------- Safe format helpers ----------
def fmt0(x):
    """Return integer-like string or '0' when NaN/inf."""
    try:
        x = float(x)
        if np.isfinite(x):
            return f"{int(round(x))}"
    except Exception:
        pass
    return "0"

def fmt1(x):
    """Return 1-decimal string or '–' when NaN/inf."""
    try:
        x = float(x)
        if np.isfinite(x):
            return f"{x:.1f}"
    except Exception:
        pass
    return "–"

# ---------- CIO tables expander ----------
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# ---------- Target 5: Incident Trends ----------
def incident_trends(df_filtered):

    if "created_time" not in df_filtered.columns:
        st.warning("⚠️ 'created_time' column not found in dataset.")
        return

    # Build daily series
    df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date
    daily = df_filtered.groupby("created_date").size().reset_index(name="ticket_count")
    daily["created_date"] = pd.to_datetime(daily["created_date"])
    daily = daily.sort_values("created_date")

    # ---------------------- Subtarget 5a ----------------------
    with st.expander("📌 Daily / Weekly / Monthly Ticket Trends"):
        # Graph 1: Daily
        fig_daily = px.line(
            daily, x="created_date", y="ticket_count",
            title="Daily Ticket Volume Trend",
            labels={"created_date": "Date", "ticket_count": "Tickets / day"}
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        # Analysis – Daily
        max_day = None
        min_day = None
        avg_day_val = 0.0
        if not daily.empty:
            max_day = daily.loc[daily["ticket_count"].idxmax()]
            min_day = daily.loc[daily["ticket_count"].idxmin()]
            avg_day_val = float(daily["ticket_count"].mean())

            st.markdown("#### Analysis of Daily Ticket Volume Trend (Line)")
            st.write(
                f"""
What this graph is: A throughput chart showing **daily tickets opened** over time.

X-axis: Calendar date.
Y-axis: Tickets created per day.

What it shows in your data:
Largest intake day: {max_day['created_date'].strftime('%Y-%m-%d')} with {int(max_day['ticket_count'])} opened.
Smallest intake day: {min_day['created_date'].strftime('%Y-%m-%d')} with {int(min_day['ticket_count'])} opened.
Average over the period: {fmt1(avg_day_val)} tickets/day.

Overall, when the line lifts far above {fmt1(avg_day_val)}, intake outpaces capacity; when it runs below, the team can stabilize backlog.

How to read it operationally:
Gap = backlog delta: The distance above {fmt1(avg_day_val)} marks stress; below it marks recovery capacity.
Lead–lag: Single-day spikes often require next-day surge capacity.
Control: Use caps/WIP limits when sequences of high days cluster.

Why this matters: Daily volatility drives **short-term backlog risk** and **SLA exposure**; catching spikes early prevents spillover.
"""
            )

        # Graph 2: 7-day rolling
        daily["rolling_7d"] = daily["ticket_count"].rolling(7).mean()
        fig_roll = px.line(
            daily, x="created_date", y="rolling_7d",
            title="7-Day Rolling Average of Ticket Volume",
            labels={"created_date": "Date", "rolling_7d": "Tickets / day (7d avg)"}
        )
        st.plotly_chart(fig_roll, use_container_width=True)

        # Analysis – 7-day rolling
        max_roll_val = 0.0
        max_roll_date = None
        roll_avg_val = 0.0
        if daily["rolling_7d"].notna().any():
            max_roll_val = float(daily["rolling_7d"].max())
            max_roll_date = daily.loc[daily["rolling_7d"].idxmax(), "created_date"]
            roll_avg_val = float(daily["rolling_7d"].mean())

            st.markdown("#### Analysis of 7-Day Rolling Average (Line)")
            st.write(
                f"""
What this graph is: A smoothed trend showing the **7-day rolling average** of tickets.

X-axis: Calendar date.
Y-axis: 7-day average tickets/day.

What it shows in your data:
Highest sustained period: {max_roll_date.strftime('%Y-%m-%d')} with ~{fmt1(max_roll_val)} tickets/day (7-day average).
Overall 7-day mean across the series: {fmt1(roll_avg_val)} tickets/day.

Overall, a rising rolling curve means **prolonged high demand**; a falling curve means cooling load.

How to read it operationally:
Peaks: Pre-book surge capacity and triage scripts until the rolling line dips back toward ~{fmt1(roll_avg_val)}.
Plateaus: Lock in processes that hold the line stable.
Control: Retire surge measures only after the rolling line normalizes.

Why this matters: Sustained demand—not single spikes—creates **structural load**, inflating **cycle time, cost, and breach risk**.
"""
            )

        # Graph 3: Weekly totals (ISO week; Monday start)
        daily["week_start"] = daily["created_date"] - pd.to_timedelta(daily["created_date"].dt.weekday, unit="D")
        weekly = (
            daily.groupby("week_start", as_index=False)["ticket_count"]
            .sum()
            .rename(columns={"ticket_count": "tickets_week"})
        )
        fig_week = px.bar(
            weekly, x="week_start", y="tickets_week",
            title="Weekly Ticket Volume (Sum by ISO Week)",
            labels={"week_start": "Week starting", "tickets_week": "Tickets / week"}
        )
        st.plotly_chart(fig_week, use_container_width=True)

        # Analysis – Weekly
        wk_peak = None
        wk_min = None
        wk_avg_val = 0.0
        if not weekly.empty:
            wk_peak = weekly.loc[weekly["tickets_week"].idxmax()]
            wk_min = weekly.loc[weekly["tickets_week"].idxmin()]
            wk_avg_val = float(weekly["tickets_week"].mean())

            st.markdown("#### Analysis of Weekly Ticket Volume (Bar)")
            st.write(
                f"""
What this graph is: A weekly aggregate of **total tickets per ISO week**.

X-axis: Week starting date (Monday).
Y-axis: Tickets per week.

What it shows in your data:
Busiest week: {wk_peak['week_start'].strftime('%Y-%m-%d')} with {int(wk_peak['tickets_week'])} tickets.
Quietest week: {wk_min['week_start'].strftime('%Y-%m-%d')} with {int(wk_min['tickets_week'])} tickets.
Average per week: {fmt1(wk_avg_val)} tickets/week.

Overall, bars significantly above {fmt1(wk_avg_val)} mark **capacity stress windows** that warrant planned surge measures.

How to read it operationally:
Peaks: Pre-approve overtime/automation for weeks like {wk_peak['week_start'].strftime('%Y-%m-%d')}.
Plateaus: Use steady weeks near {fmt1(wk_avg_val)} to clear backlog and perform maintenance.
Control: Align rosters and vendor SLAs to weekly demand shape.

Why this matters: Weekly sums match **planning cadence** for shifts and budgets better than dailies alone.
"""
            )

        # Graph 4: Monthly totals
        daily["month"] = daily["created_date"].dt.to_period("M")
        monthly = daily.groupby("month", as_index=False)["ticket_count"].sum()
        monthly["month_str"] = monthly["month"].dt.strftime("%Y-%m")
        fig_month = px.bar(
            monthly, x="month_str", y="ticket_count",
            title="Monthly Ticket Volume",
            labels={"month_str": "Month", "ticket_count": "Tickets / month"}
        )
        st.plotly_chart(fig_month, use_container_width=True)

        # Analysis – Monthly
        m_peak = None
        m_min = None
        m_avg_val = 0.0
        if not monthly.empty:
            m_peak = monthly.loc[monthly["ticket_count"].idxmax()]
            m_min = monthly.loc[monthly["ticket_count"].idxmin()]
            m_avg_val = float(monthly["ticket_count"].mean())

            st.markdown("#### Analysis of Monthly Ticket Volume (Bar)")
            st.write(
                f"""
What this graph is: An aggregate showing **total tickets per month**.

X-axis: Year–Month.
Y-axis: Total tickets.

What it shows in your data:
Busiest month: {m_peak['month'].strftime('%Y-%m')} with {int(m_peak['ticket_count'])} tickets.
Quietest month: {m_min['month'].strftime('%Y-%m')} with {int(m_min['ticket_count'])} tickets.
Average per month: {fmt1(m_avg_val)} tickets.

Overall, high bars concentrate **budget pressure and SLA risk**, while low bars are **recovery windows**.

How to read it operationally:
Peaks: Shift preventive effort and major releases out of {m_peak['month'].strftime('%Y-%m')}.
Plateaus: Set monthly control limits around ~{fmt1(m_avg_val)}.
Control: Use monthly view for headcount and vendor capacity planning.

Why this matters: Monthly volume guides **capacity & cost forecasts** at the executive cadence.
"""
            )

        # ------------- CIO Table for 5a (uses computed values) -------------
        _max_day_val = int(max_day["ticket_count"]) if max_day is not None else 0
        _max_day_date = max_day["created_date"].strftime("%Y-%m-%d") if max_day is not None else "-"
        _max_roll_val = float(max_roll_val) if daily["rolling_7d"].notna().any() else 0.0
        _max_roll_date = max_roll_date.strftime("%Y-%m-%d") if daily["rolling_7d"].notna().any() else "-"
        _wk_peak_val = int(wk_peak["tickets_week"]) if wk_peak is not None else 0
        _wk_peak_start = wk_peak["week_start"].strftime("%Y-%m-%d") if wk_peak is not None else "-"
        _wk_avg_val = float(wk_avg_val) if wk_peak is not None else 0.0
        _m_peak_val = int(m_peak["ticket_count"]) if m_peak is not None else 0
        _m_peak_month = m_peak["month"].strftime("%Y-%m") if m_peak is not None else "-"
        _m_avg_val = float(m_avg_val) if m_peak is not None else 0.0

        cio_5a = {
    "cost": f"""
| Recommendation | Explanation (phased) | Benefits | Cost calculation (uses real values from graphs) | Evidence & graph interpretation |
|---|---|---|---|---|
| Surge-handling playbook & temporary staffing | **Phase 1 – Identify surges:** Use weekly peak {_wk_peak_start} ({_wk_peak_val} tickets) and 7-day peak {_max_roll_date} (~{fmt1(_max_roll_val)}/day). <br><br>**Phase 2 – Deploy levers:** pre-approved OT blocks, queue triage, chatbot deflection. <br><br>**Phase 3 – Retire:** scale down when rolling average reverts toward {fmt1(_wk_avg_val)}/week average. | - This approach prevents last-minute overtime spikes by replacing firefighting with pre-planned capacity.<br><br>- Work stays inside standard hours more often, which lowers labor cost volatility.<br><br>- Backlog does not snowball into the following week, so downstream work becomes cheaper to complete. | Hours saved = (excess weekly tickets above avg) × avg_resolution_hours = ({_wk_peak_val} − {fmt1(_wk_avg_val)}) × avg_resolution_hours. Multiply by hourly_rate to monetize. | Weekly bar shows {_wk_peak_start} = {_wk_peak_val} vs avg {fmt1(_wk_avg_val)}. Rolling peak on {_max_roll_date} confirms sustained strain. |
| Automation for bursty categories | **Phase 1 – Pinpoint burst drivers:** correlate daily peak {_max_day_date} ({_max_day_val}) to top categories. <br><br>**Phase 2 – Build flows:** macros/self-serve for top two categories. <br><br>**Phase 3 – Measure:** compare post-automation daily average vs baseline {fmt1(avg_day_val)}. | - Automation shortens repetitive tasks so each ticket consumes fewer minutes.<br><br>- The cost per ticket drops because less human effort is needed.<br><br>- Senior staff get time back for complex cases that actually require judgment. | Time avoided = tickets_automated × minutes_saved. For peak day cohort use {_max_day_val} × minutes_saved (from category time studies). | Daily peak {_max_day_date}={_max_day_val} indicates where automation removes repeat toil. |
| Preventive scheduling around peak months | **Phase 1 – Block risky changes:** avoid high-impact work in {_m_peak_month} ({_m_peak_val} tickets). <br><br>**Phase 2 – Pull forward prevention:** patching, KB updates in sub-average months (~{fmt1(_m_avg_val)}). <br><br>**Phase 3 – Review:** month-on-month variance. | - Shifting heavy work away from peak demand months reduces the number of incidents created by changes.<br><br>- Teams spend fewer hours fixing avoidable issues and more time on planned work.<br><br>- The monthly cost curve becomes flatter and easier to forecast. | Avoided tickets = ({_m_peak_val} − {fmt1(_m_avg_val)}) × reduction_rate. Hours saved = avoided_tickets × avg_resolution_hours. | Monthly bar peak {_m_peak_month}={_m_peak_val} vs avg {fmt1(_m_avg_val)} demonstrates planning anchor. |
""",
    "performance": f"""
| Recommendation | Explanation (phased) | Benefits | Cost calculation (uses real values from graphs) | Evidence & graph interpretation |
|---|---|---|---|---|
| Backlog control on weekly peaks | **Phase 1 – WIP caps:** set intake throttles during weeks like {_wk_peak_start}. <br><br>**Phase 2 – Surge sprints:** daily burn-downs until weekly bars fall near {fmt1(_wk_avg_val)}. <br><br>**Phase 3 – Audit:** lead/lag vs 7-day curve. | - Keeping weekly closures at or above new openings stops backlog growth during peak weeks.<br><br>- Lead times stabilize because work-in-progress stays within limits.<br><br>- Teams can plan daily output with more confidence. | Throughput lift = Δ tickets closed/week after caps. Target = {_wk_peak_val}→≈{fmt1(_wk_avg_val)}. | Weekly column shows {_wk_peak_val} vs avg {fmt1(_wk_avg_val)}; rolling line confirms sustained need. |
| Rolling-trigger playbooks | **Phase 1 – Thresholds:** trigger when 7-day avg ≥ {fmt1(max(_max_roll_val, 1))}. <br><br>**Phase 2 – Actions:** reassignments, auto-responses, vendor swarms. <br><br>**Phase 3 – Exit:** when rolling avg returns within ±10% of baseline {fmt1(roll_avg_val)}. | - Playbooks shorten recovery time when demand stays high for several days.<br><br>- Fewer tickets breach SLA because risk is addressed earlier.<br><br>- Cycle time becomes steadier across the period. | Breaches avoided = baseline_breaches_at_peak − breaches_post_playbook (measured on windows around {_max_roll_date}). | Peak rolling date {_max_roll_date} at ~{fmt1(_max_roll_val)}/day is the activation case. |
| Category-ranked prevention | **Phase 1 – Rank months:** use {_m_peak_month} to pick top categories. <br><br>**Phase 2 – Fix:** root-cause, standard changes. <br><br>**Phase 3 – Validate:** track monthly bar drop toward {fmt1(_m_avg_val)}. | - Removing the root causes in the noisiest categories reduces incoming volume at the source.<br><br>- Mean time to resolve improves because the team deals with fewer distractions.<br><br>- SLA headroom increases, which protects critical work from delays. | Hours saved = (tickets_reduced in {_m_peak_month}) × avg_resolution_hours. | {_m_peak_month}={_m_peak_val} vs average {fmt1(_m_avg_val)} isolates where prevention pays. |
""",
    "satisfaction": f"""
| Recommendation | Explanation (phased) | Benefits | Cost calculation (uses real values from graphs) | Evidence & graph interpretation |
|---|---|---|---|---|
| Peak-window status page & ETAs | **Phase 1 – Templates:** publish ETAs when daily > {fmt1(avg_day_val)} or week >= {_wk_peak_val}. <br><br>**Phase 2 – Automation:** push updates during {_wk_peak_start}. <br><br>**Phase 3 – Survey:** CSAT delta. | - Clear and proactive updates reduce complaint tickets and repeat follow-ups during high load.<br><br>- Users understand what is happening and when to expect progress, which preserves trust even when work takes longer. | Contact deflection = (follow-ups avoided × minutes). Use counts on {_max_day_date} ({_max_day_val}) to estimate avoided contacts. | Daily/weekly peaks ({_max_day_date}, {_wk_peak_start}) define when comms have biggest impact. |
| VIP queue protection in peak weeks | **Phase 1 – Tag VIPs:** route away from overloaded slots in {_wk_peak_start}. <br><br>**Phase 2 – Senior owner:** fast-lane steps. <br><br>**Phase 3 – Audit:** breach rate vs non-VIP. | - Priority handling keeps key accounts moving when volume spikes.<br><br>- Escalations drop because issues are handled before they stall.<br><br>- Customers perceive higher quality because responses remain timely for their most important cases. | Escalation cost avoided = (#VIP tickets × escalation_rate × cost_per_escalation). | Weekly peak {_wk_peak_start}={_wk_peak_val} signals highest VIP risk. |
| Self-service deflection for top FAQs | **Phase 1 – Identify FAQs:** from peak day {_max_day_date}. <br><br>**Phase 2 – Publish flows:** portal steps & chat prompts. <br><br>**Phase 3 – Iterate:** measure deflection vs baseline {fmt1(avg_day_val)}. | - Users get faster answers to common requests without waiting in the queue.<br><br>- The team receives fewer tickets during surges and can focus on complex incidents.<br><br>- People feel more in control because they can solve simple issues themselves. | Tickets avoided = deflection_rate × {_max_day_val} (peak day cohort). | Peak day {_max_day_date} volume of {_max_day_val} exposes FAQ candidates. |
"""
}
        render_cio_tables("CIO Recommendations - Daily / Weekly / Monthly Ticket Trends", cio_5a)

    # ---------------------- Subtarget 5b ----------------------
    with st.expander("📌 Seasonal or Recurring Patterns"):
        # Graph 1: Seasonal Decomposition
        resid_peak_date_str, resid_peak_val = "-", 0.0
        try:
            if len(daily) > 30:
                decomposition = seasonal_decompose(
                    daily.set_index("created_date")["ticket_count"],
                    model="additive", period=30
                )
                comp_df = pd.DataFrame({
                    "Trend": decomposition.trend,
                    "Seasonal": decomposition.seasonal,
                    "Residual": decomposition.resid
                })
                st.line_chart(comp_df)

                # Analysis – Decomposition
                st.markdown("#### Analysis of Seasonal Decomposition (Line)")
                resid_series = decomposition.resid.dropna()
                if not resid_series.empty:
                    resid_peak_idx = resid_series.idxmax()
                    resid_peak_val = float(resid_series.max())
                    resid_peak_date_str = resid_peak_idx.strftime("%Y-%m-%d")

                st.write(
                    f"""
What this graph is: A decomposition separating **Trend**, **Seasonal**, and **Residual** components of ticket volume.

X-axis: Calendar date.
Y-axis: Tickets (split into components).

What it shows in your data:
Residual peak (unexplained spike): {resid_peak_date_str} at +{fmt1(resid_peak_val)} tickets (above expected).
Trend shows long-run movement; Seasonal shows repeating short-term cycles.

Overall, large Residual spikes point to **event-driven incidents** (e.g., outages), while strong Seasonal bands imply **predictable cycles**.

How to read it operationally:
Peaks: Investigate residual spike dates like {resid_peak_date_str} for change/outage correlation.
Control: If seasonality is stable, pre-position staff and comms in those windows.

Why this matters: Knowing whether demand is systematic vs event-driven shapes **prevention vs rapid response** investments.
"""
                )
        except Exception as e:
            st.warning("Could not perform seasonal decomposition. Error: " + str(e))

        # Graph 2: Heatmap Day-of-Week × Week-of-Year
        daily["dow"] = daily["created_date"].dt.day_name()
        daily["week"] = daily["created_date"].dt.isocalendar().week
        pivot = daily.pivot_table(index="dow", columns="week", values="ticket_count", aggfunc="mean")
        fig_heat = px.imshow(
            pivot, aspect="auto",
            title="Heatmap of Tickets (Day of Week × Week of Year)",
            labels={"x": "ISO Week", "y": "Day of Week", "color": "Avg Tickets / day"}
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Analysis – Heatmap
        max_val = float(np.nanmax(pivot.values)) if pivot.size else 0.0
        min_val = float(np.nanmin(pivot.values)) if pivot.size else 0.0
        st.markdown("#### Analysis of Weekly/Day Heatmap (Image)")
        st.write(
            f"""
What this graph is: A density heatmap of **tickets by weekday vs week-of-year**.

X-axis: Week number (ISO).
Y-axis: Day of week.
Color: Average tickets per day.

What it shows in your data:
Busiest cell ≈ {fmt0(max_val)} tickets/day (hot zone).
Quietest cell ≈ {fmt0(min_val)} tickets/day (cool zone).

Overall, hotter cells reveal **recurring pressure windows**, while cooler cells indicate **low-risk windows**.

How to read it operationally:
Peaks: Add on-call coverage and pre-triage scripts in hot cells.
Downswings: Schedule changes/training in cool cells to minimize impact.
Control: Validate that hot cells shrink after interventions.

Why this matters: Time-of-week patterns enable **precision scheduling** that reduces **overtime, breaches, and frustration** without over-staffing.
"""
        )

        # ------------- CIO Table for 5b (uses decomposition & heatmap) -------------
        cio_5b = {
    "cost": f"""
| Recommendation | Explanation (phased) | Benefits | Cost calculation (uses real values from graphs) | Evidence & graph interpretation |
|---|---|---|---|---|
| Preventive change scheduling (avoid risky changes in hot windows) | **Phase 1 – Correlate:** map residual spike {resid_peak_date_str} (+{fmt1(resid_peak_val)}) to change logs. <br><br>**Phase 2 – Blackout:** prohibit high-risk changes in hot cells (≈{fmt0(max_val)}/day). <br><br>**Phase 3 – Enforce:** CAB checks. | - Avoiding risky changes during high-intensity windows prevents incident surges that would otherwise consume many recovery hours.<br><br>- Less rework is needed after releases, so cost per delivered change drops.<br><br>- Daily operations also run more smoothly because interruptions become rarer. | Hours avoided = prevented_incidents × avg_resolution_hours. Estimate prevented_incidents from residual spike (+{fmt1(resid_peak_val)}) and hot-cell delta (≈{fmt0(max_val)}−{fmt0(min_val)}). | Decomposition residual peak {resid_peak_date_str} and heatmap hot cells (≈{fmt0(max_val)}/day) pinpoint risky windows. |
| Staggered releases by weekday intensity | **Phase 1 – Profile:** use heatmap to rank weekdays by load. <br><br>**Phase 2 – Stagger:** schedule releases on cool days (~{fmt0(min_val)}/day). <br><br>**Phase 3 – Monitor:** compare incidents pre/post. | - Placing releases on quieter days reduces the chance of compounding failures.<br><br>- Daily volume charts become flatter, which makes operations calmer.<br><br>- Engineers can focus better on release quality because the rest of the system is under less stress. | Avoided tickets = (release_count × incident_rate_reduction). Hours saved = avoided_tickets × avg_resolution_hours. | Heatmap shows cool vs hot bands enabling stagger rules. |
| Event-driven postmortems | **Phase 1 – Detect:** when residual > +2σ (e.g., {resid_peak_date_str} +{fmt1(resid_peak_val)}). <br><br>**Phase 2 – Fix:** apply mitigations (runbooks, guards). <br><br>**Phase 3 – Verify:** next similar window shows lower residuals. | - Focused postmortems stop the same expensive spikes from happening again.<br><br>- Predictability improves because known failure modes are removed.<br><br>- Teams spend less time firefighting and more time on proactive improvements. | Savings = (recurring spike tickets avoided × avg_resolution_hours). Use residual peak magnitude (+{fmt1(resid_peak_val)}) as baseline. | Residual spikes quantify the “unexpected” portion to target. |
""",
    "performance": f"""
| Recommendation | Explanation (phased) | Benefits | Cost calculation (uses real values from graphs) | Evidence & graph interpretation |
|---|---|---|---|---|
| Hot-cell surge coverage | **Phase 1 – Identify:** cells ≈{fmt0(max_val)}/day. <br><br>**Phase 2 – Staff:** add overlap or on-call for those weekday×week slots. <br><br>**Phase 3 – Review:** ensure cell intensity trends toward mid-band. | - Additional coverage during predictable peaks accelerates first responses and shortens queues.<br><br>- SLA breaches fall because tickets do not sit unattended.<br><br>- Cycle times become steadier across weeks. | Breaches avoided = baseline_breaches_in_hot_cells − post_coverage_breaches. | Heatmap hot cells quantify where coverage pays off most. |
| Seasonal prep calendar | **Phase 1 – Forecast:** if seasonal band evident, pre-position scripts/staff. <br><br>**Phase 2 – Execute:** time-boxed sprints in those windows. <br><br>**Phase 3 – Retrospect:** residual shrink vs prior season. | - Preparing for seasonal peaks reduces recovery time after busy periods.<br><br>- Backlog grows more slowly because the team enters the window with the right tools and staffing.<br><br>- Overall throughput improves across the season. | Throughput lift = Δ tickets closed/day in seasonal windows. | Seasonal component + residual comparison shows effect. |
| Residual watchlist alerts | **Phase 1 – Alert:** trigger when residual > +threshold (e.g., +{fmt1(max(2.0, resid_peak_val/2))}). <br><br>**Phase 2 – Actions:** auto-swarm, vendor pings. <br><br>**Phase 3 – Normalize:** exit when residual reverts near 0. | - Early alerts surface anomalies before they spread across the queue.<br><br>- Teams intervene sooner, which prevents long chains of delay.<br><br>- Overall performance becomes more resilient to unexpected events. | Hours saved = anomaly_duration × avg_recovery_hours_saved. | Decomposition residual quantifies anomaly magnitude/duration. |
""",
    "satisfaction": f"""
| Recommendation | Explanation (phased) | Benefits | Cost calculation (uses real values from graphs) | Evidence & graph interpretation |
|---|---|---|---|---|
| Proactive status comms in hot windows | **Phase 1 – Templates:** ready messages for hot cells (≈{fmt0(max_val)}/day). <br><br>**Phase 2 – Trigger:** auto-send when entering hot cell or residual spike ({resid_peak_date_str}). <br><br>**Phase 3 – Evaluate:** complaint delta. | - Users receive updates before they need to chase, so repeat contacts fall.<br><br>- Expectations are clear during the busiest periods and trust remains intact even when queues are long. | Contact deflection = (repeat contacts avoided × minutes). Use hot-cell volume ≈{fmt0(max_val)} to estimate avoided contacts. | Heatmap & residual pinpoint when users most need comms. |
| Customer-safe scheduling | **Phase 1 – Select cool days:** ~{fmt0(min_val)}/day windows for customer-visible work. <br><br>**Phase 2 – Notify:** advance notices & rollbacks. <br><br>**Phase 3 – Survey:** CSAT delta. | - Scheduling visible work on quieter days limits perceived disruption.<br><br>- Customers report higher satisfaction because changes feel orderly and well communicated. | Retained revenue = (CSAT lift × customer LTV). | Cool cells from heatmap justify scheduling choices. |
| Post-incident apology tokens | **Phase 1 – Criteria:** when residual spike > +{fmt1(max(2.0, resid_peak_val/2))}. <br><br>**Phase 2 – Outreach:** message & goodwill tokens. <br><br>**Phase 3 – Track:** churn/complaint reductions. | - Timely outreach and small gestures repair trust after noticeable incidents.<br><br>- Escalation risk decreases because customers feel acknowledged and supported. | Cost vs benefit = token_cost − (escalations avoided × cost_per_escalation). | Residual spikes identify which days deserve make-good. |
"""
}
        render_cio_tables("CIO Recommendations - Seasonal or Recurring Patterns", cio_5b)
