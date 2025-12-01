# utils_asset_inventory/recommendation_assets/hardware_assets.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================================================
# Visual defaults (Mesiniaga blue/white)
# ============================================================
px.defaults.template = "plotly_white"
BLUE_TONES = [
    "#004C99",  # navy blue (brand)
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # pale blue
    "#99CCFF",  # very light
]

# ============================================================
# Helpers
# ============================================================

DATE_COLS = [
    "warranty_start", "warranty_end", "return_date", "update_on",
    "latest_to_dispose", "pm_completed"
]

def _robust_to_datetime(s: pd.Series) -> pd.Series:
    """Parse a date-ish series aggressively without nuking valid rows."""
    if s.dtype.kind in ("M",):  # already datetime64
        return pd.to_datetime(s, errors="coerce")
    s2 = s.astype(str).str.strip().replace({"": np.nan, "NaT": np.nan})
    attempts = [
        dict(errors="coerce", infer_datetime_format=True),
        dict(errors="coerce", dayfirst=True, infer_datetime_format=True),
        dict(errors="coerce", format="%Y-%m-%d"),
        dict(errors="coerce", format="%d/%m/%Y"),
        dict(errors="coerce", format="%m/%d/%Y"),
    ]
    for kw in attempts:
        parsed = pd.to_datetime(s2, **kw)
        if parsed.notna().any():
            return parsed
    return pd.to_datetime(s2, errors="coerce")

def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in DATE_COLS:
        if c in out.columns:
            out[c] = _robust_to_datetime(out[c])
    return out

def _period_month(s: pd.Series) -> pd.Series:
    p = pd.to_datetime(s, errors="coerce").dt.to_period("M")
    return p.astype(str)

def _safe_nunique(df, col):
    return df[col].nunique() if col in df.columns else 0

def _exists_and_nonempty(df, col):
    return (col in df.columns) and df[col].notna().any()

def _norm_text(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().replace({"": np.nan})

def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data.get("cost", ""), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data.get("performance", ""), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data.get("satisfaction", ""), unsafe_allow_html=True)

def _analysis_block(what:str, x:str, y:str, shows:str, ops:str, why:str):
    """Standardized analysis formatter."""
    st.markdown(
f"""**What this graph is:** {what}  
**X-axis:** {x}.  
**Y-axis:** {y}.  

**What it shows in your data:**  
{shows}

**How to read it operationally:**  
{ops}

**Why this matters:** {why}
"""
    )

# ============================================================
# Target 2: Hardware Assets
# ============================================================

def asset_hardware(df_filtered: pd.DataFrame):
    df_filtered = _parse_dates(df_filtered).copy()

    # Normalize commonly-used categorical columns to avoid silent plot failures
    for c in ["asset_status", "location", "region", "brand", "model"]:
        if c in df_filtered.columns:
            df_filtered[c] = _norm_text(df_filtered[c])

    # --------------------------------------------------------
    # 2a) Hardware Registry Snapshot (summary only)
    # --------------------------------------------------------
    with st.expander("📌 Hardware Registry Snapshot"):
        st.info("Heads-up: this section is a registry snapshot and CIO tables only — no charts here.")
        notes = []
        unique_assets = _safe_nunique(df_filtered, "asset_id")

        if unique_assets:
            notes.append(f"Unique assets: **{unique_assets:,}**.")
        if "asset_status" in df_filtered.columns and df_filtered["asset_status"].dropna().shape[0] > 0:
            status_counts = df_filtered["asset_status"].value_counts(dropna=True).reset_index()
            status_counts.columns = ["asset_status", "count"]
            notes.append(
                f"Top status: **{status_counts.iloc[0]['asset_status']}** with **{int(status_counts.iloc[0]['count'])}** records."
            )
        else:
            status_counts = pd.DataFrame(columns=["asset_status","count"])
        if "location" in df_filtered.columns and df_filtered["location"].dropna().shape[0] > 0:
            loc_counts = df_filtered["location"].value_counts(dropna=True).reset_index()
            loc_counts.columns = ["location", "count"]
            notes.append(
                f"Largest location: **{loc_counts.iloc[0]['location']}** with **{int(loc_counts.iloc[0]['count'])}** assets."
            )
        else:
            loc_counts = pd.DataFrame(columns=["location","count"])

        st.markdown("### Analysis – Inventory Metadata Overview")
        st.write(f"""
**What this section is:** A registry snapshot summarizing **inventory identity, status, and site distribution**.  
- **Focus:** `asset_id` uniqueness, `asset_status` mix, and `location` clustering.  
- **Purpose:** Establish a clean baseline so downstream modules (utilization, lifecycle, warranty) operate on trustworthy data.

**What it shows in your data:**  
- **Unique assets:** **{unique_assets:,}**.  
- {("**Status distribution:** highest = **" + str(status_counts.iloc[0]['asset_status']) + f"** ({int(status_counts.iloc[0]['count'])}), lowest = **" + str(status_counts.iloc[-1]['asset_status']) + f"** ({int(status_counts.iloc[-1]['count'])}).") if not status_counts.empty else "No status data available."}  
- {("**Location spread:** largest = **" + str(loc_counts.iloc[0]['location']) + f"** ({int(loc_counts.iloc[0]['count'])}), smallest = **" + str(loc_counts.iloc[-1]['location']) + f"** ({int(loc_counts.iloc[-1]['count'])}).") if not loc_counts.empty else "No location data available."}

**How to read it operationally:**  
- **Completeness first:** empty owner/site/status fields create blind spots in every other dashboard; close these gaps before interpreting trends.  
- **Consistency next:** duplicate `asset_id`/serials inflate counts and distort spend/utilization; reconcile collisions to restore the signal.  
- **Recency matters:** stale `update_on` dates are early warnings for records that have drifted away from reality; put them on a hygiene list.

**Why this matters:** Data quality is **compound interest** for operations. Clean registry data reduces rework, speeds request fulfillment, and prevents duplicate spend; messy data does the opposite and taxes every process that depends on it.
""")

        evidence = " ".join(notes) if notes else "Registry summary rendered; insufficient metadata for highlights."
        cio_2a = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Consolidate idle stock** | **Phase 1 – Detect:** Build a filtered list of all assets whose status is not 'in use' and validate the accuracy of each record with owner and site tags so that the pool size is trustworthy. <br><br>**Phase 2 – Pool:** Centralize the idle units into a visible catalogue with consistent tagging for owner, site, and readiness so requesters can consume the pool confidently. <br><br>**Phase 3 – Govern:** Enforce a purchasing gate that blocks new buys when the pool is above a threshold and publish a dashboard so teams request from the pool first. | - Reduces immediate capital expenditure because teams draw from available stock instead of raising new purchase requests.<br><br>- Lowers storage and handling costs because excess units are moved out of ad hoc cupboards into a controlled pool with faster turnaround.<br><br>- Accelerates fulfillment because redeployments avoid vendor lead times and users receive devices sooner.<br><br>- Cuts write offs because fewer devices are forgotten or go missing once the pool has full visibility. | **Redeployable units × Unit cost**. Compute redeployable from non-'in use' count in the status chart. | {evidence} |
| **Remove duplicate IDs** | **Phase 1 – Audit:** Run automated checks to find duplicate `asset_id` or serial numbers and classify each collision with a clear rule so remediation can be tracked. <br><br>**Phase 2 – Correct:** Merge or retag records with approvals and an audit trail so history remains intact and finance can reconcile confidently. <br><br>**Phase 3 – Lock:** Add intake validation that enforces uniqueness so duplicate issues do not reappear after the clean up. | - Eliminates phantom inventory which prevents accidental double purchases and reduces confusion during audits.<br><br>- Improves reporting accuracy which helps leadership make better decisions about refresh and support plans.<br><br>- Shortens reconciliation cycles with finance and procurement because records line up across systems.<br><br>- Reduces time wasted by technicians who otherwise chase the wrong device record. | **Duplicates fixed × Avg asset value** derived from finance data. | Registry indicates ID/metadata consistency needs. |
| **Tighten mandatory fields** | **Phase 1 – Rules:** Define owner site and status as mandatory at creation and make the UI block submission until the fields are complete. <br><br>**Phase 2 – Validate:** Run nightly checks that find gaps and send targeted alerts with due dates so the right owners fix data issues quickly. <br><br>**Phase 3 – Report:** Publish exception dashboards and a weekly burn down by team so accountability is clear and performance trends are visible. | - Reduces rework during downstream processes because technicians and approvers get complete context on day one.<br><br>- Increases automation success rates because routing and approvals rely on clean owner and site fields.<br><br>- Raises trust in data so planning and forecasting become faster and less contentious.<br><br>- Cuts cycle time for requests because fewer tickets bounce between teams for clarification. | **Time saved/record × Records/month** (pull exception counts from status & location charts). | {evidence} |
"""
        , "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Mandatory metadata fields** | **Phase 1 – Enforce:** Configure the intake form and API to reject records without owner site and status so incomplete entries cannot enter the system. <br><br>**Phase 2 – Assist:** Provide defaults tooltips and picklists that make it easy for users to choose the correct values and reduce typing mistakes. <br><br>**Phase 3 – QA:** Perform weekly spot checks and coach repeat offenders so quality sticks across teams. | - Shortens intake lead time because records are right the first time and no follow up is required.<br><br>- Reduces human error because guided inputs lower variation and improve consistency for analytics.<br><br>- Raises automation hit rates because complete metadata enables straight through processing.<br><br>- Improves operational reliability because teams can locate assets quickly with correct ownership and site details. | **Lead-time saved (hrs) × Intakes/month**. | Coverage of status/location enables policy. |
| **Auto-validations** | **Phase 1 – Monitors:** Create automated monitors that detect missing or invalid owner location or status and that flag stale `update_on` values so issues surface immediately. <br><br>**Phase 2 – Alerts:** Send notifications to record owners with clear remediation steps and escalation paths so fixes happen within a defined window. <br><br>**Phase 3 – SLO:** Commit to a 48 hour fix target and track compliance so teams maintain hygiene continuously. | - Sustains data freshness which improves incident triage linked to the right assets and users.<br><br>- Reduces mean time to resolve because technicians start with accurate context and do not need to search for owners or sites.<br><br>- Lowers the number of unknown device loops because assets are identified correctly in the system.<br><br>- Creates a predictable rhythm of data maintenance which stabilizes downstream reporting. | **% clean records ↑ × Tickets avoided**. | Status/location counts exist to drive rules. |
| **Role-based views** | **Phase 1 – Lenses:** Provide filtered views by owner site and status so each team sees only what they need to action. <br><br>**Phase 2 – Bulk actions:** Enable bulk updates for common hygiene fixes so teams can correct dozens of records in one pass. <br><br>**Phase 3 – KPIs:** Track aged exceptions and throughput so leaders can spot bottlenecks and assign help quickly. | - Speeds up decision making for managers who get focused lists of what to fix next.<br><br>- Lowers time to resolve data issues because bulk tools remove repetitive manual edits.<br><br>- Drives accountability because aged items are visible and measurable by team and by site.<br><br>- Reduces context switching because teams can complete related fixes in a single session. | **Lookup time ↓ × Tickets/week**. | Groupings improve findability. |
"""
        , "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Owner visibility** | **Phase 1 – Portal:** Deliver a simple view called My assets that lists devices ownership and warranty details so users can self serve basic questions. <br><br>**Phase 2 – Notifs:** Send proactive notifications when ownership or warranty status changes so users are never surprised. <br><br>**Phase 3 – Acknowledge:** Capture digital acknowledgements for critical updates so accountability is clear. | - Reduces disputes on who owns what because users can see assigned devices in one place.<br><br>- Cuts back and forth with IT because many status questions are answered by the portal.<br><br>- Improves user confidence because information is transparent and current.<br><br>- Reduces escalation risk because important changes are acknowledged explicitly. | **Queries avoided × Handling time** estimated from historical. | {evidence} |
| **Site inventory portal** | **Phase 1 – Publish:** Show available stock by site with simple filters so non IT stakeholders can understand local capacity. <br><br>**Phase 2 – ETAs:** Display inbound replenishment windows so requesters can plan their activities with realistic dates. <br><br>**Phase 3 – Reserve:** Allow users to reserve units from the pool which reduces ad hoc emails and delays. | - Sets accurate expectations which reduces frustration and improves planning for business teams.<br><br>- Speeds fulfillment because requests can target nearby stock without extra coordination.<br><br>- Reduces status calls because ETAs and stock numbers are visible to everyone.<br><br>- Improves transparency which increases trust in the asset process. | **Calls avoided × Cost/call**. | Largest/smallest site spread above. |
| **Intake transparency** | **Phase 1 – Receipts:** Send automatic confirmations when devices are registered or become ready so users know progress without chasing. <br><br>**Phase 2 – Track:** Show a simple tracker from delivery to ready states so stakeholders can see where a device sits in the pipeline. <br><br>**Phase 3 – SLAs:** Publish intake service level objectives and surface breaches so follow ups are minimized and action is prioritized. | - Makes onboarding predictable which reduces anxiety for new joiners and project teams.<br><br>- Cuts follow ups because users can view status without contacting IT.<br><br>- Establishes clear accountability so delays are addressed quickly.<br><br>- Improves perceived professionalism which lifts satisfaction scores. | **Follow-ups avoided × Handling cost**. | Registry snapshot confirms coverage. |
"""
        }
        render_cio_tables("CIO – Hardware Registry", cio_2a)

    # --------------------------------------------------------
    # 2b) Warranty Status & Expiry Timeline
    # --------------------------------------------------------
    with st.expander("📌 Warranty Status & Expiry Timeline"):
        # Pie: warranty_status
        if "warranty_status" in df_filtered.columns and df_filtered["warranty_status"].notna().any():
            wstat = df_filtered["warranty_status"].value_counts(dropna=True).reset_index()
            wstat.columns = ["warranty_status", "count"]
            fig1 = px.pie(
                wstat, names="warranty_status", values="count",
                title="Warranty Status Distribution",
                color_discrete_sequence=BLUE_TONES,
                category_orders={"warranty_status": wstat["warranty_status"].tolist()}
            )
            st.plotly_chart(fig1, use_container_width=True)

            largest_slice = (wstat.iloc[0]["warranty_status"], int(wstat.iloc[0]["count"]))
            smallest_slice = (wstat.iloc[-1]["warranty_status"], int(wstat.iloc[-1]["count"]))
            _analysis_block(
                what="A composition chart showing the share of assets by warranty status.",
                x="Status categories",
                y="Asset counts per status",
                shows=(
                    f"Largest slice: **{largest_slice[0]}** (**{largest_slice[1]}** assets). "
                    f"Smallest slice: **{smallest_slice[0]}** (**{smallest_slice[1]}** assets). "
                    "A skew toward 'Expired' or 'Unknown' signals immediate risk and data hygiene work; "
                    "a healthy footprint shows most assets covered and a narrow 'Unknown' band."
                ),
                ops=(
                    "Prioritize actions on dominant slices for the biggest impact (extend, replace, or claim). "
                    "Investigate tiny categories to confirm whether they represent genuine edge cases or misclassification. "
                    "Track month-over-month movement between slices to validate renewal execution and detect slippage early."
                ),
                why="Warranty coverage directly influences exposure to unplanned OPEX, vendor leverage in negotiations, and user downtime during failures."
            )
        else:
            wstat = pd.DataFrame(columns=["warranty_status","count"])
            st.info("No 'warranty_status' data to chart.")

        # Bar: warranty_end by month (chronological)
        if _exists_and_nonempty(df_filtered, "warranty_end"):
            wexp = df_filtered[df_filtered["warranty_end"].notna()].copy()
            wexp["month_period"] = pd.to_datetime(wexp["warranty_end"]).dt.to_period("M")
            w_by_month = (
                wexp.groupby("month_period").size().reset_index(name="expiring")
                .sort_values("month_period")
            )
            w_by_month["month"] = w_by_month["month_period"].astype(str)
            fig2 = px.bar(
                w_by_month, x="month", y="expiring",
                title="Warranty Expiries by Month",
                text="expiring",
                labels={"month":"Month","expiring":"Assets Expiring"},
                color_discrete_sequence=BLUE_TONES
            )
            fig2.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True)

            peak_idx = w_by_month["expiring"].idxmax()
            low_idx  = w_by_month["expiring"].idxmin()
            peak_month = str(w_by_month.loc[peak_idx, "month"])
            peak_cnt   = int(w_by_month.loc[peak_idx, "expiring"])
            low_month  = str(w_by_month.loc[low_idx, "month"])
            low_cnt    = int(w_by_month.loc[low_idx, "expiring"])
            avg_pm     = float(w_by_month["expiring"].mean())

            _analysis_block(
                what="A timeline of warranty expiries grouped by calendar month.",
                x="Calendar month",
                y="Number of assets expiring",
                shows=(
                    f"Peak expiry load: **{peak_month}** with **{peak_cnt}** assets. "
                    f"Lowest month: **{low_month}** with **{low_cnt}**. "
                    f"Average across months: **{avg_pm:.1f}** expiries/month. "
                    "Clustering near specific months suggests synchronized procurement cycles or deferred renewals."
                ),
                ops=(
                    "Front-load renewal/extension decisions two months before peaks; "
                    "pre-book vendor capacity and negotiate bundles tied to those spikes; "
                    "stage loaners and spares for high-risk windows; "
                    "spread upcoming expiries by bringing forward or pushing out a subset to smooth the curve."
                ),
                why="Concentrated expiries create budget spikes and service risk. Smoothing renewals stabilizes cash flow, protects availability, and reduces firefighting."
            )
        else:
            w_by_month = pd.DataFrame(columns=["month_period","expiring","month"])
            peak_month, peak_cnt, low_month, low_cnt, avg_pm = ("—", 0, "—", 0, 0.0)
            st.warning("Column 'warranty_end' missing or empty; expiry timeline unavailable.")

        ev_pie = (f"Largest slice: **{wstat.iloc[0]['warranty_status']}** "
                  f"({int(wstat.iloc[0]['count'])})") if not wstat.empty else "No warranty status composition."
        ev_bar = (f"Expiry peak: **{peak_month}** (**{peak_cnt}**); "
                  f"Avg per month: **{avg_pm:.1f}**") if not w_by_month.empty else "No expiry timeline."
        ev_str = f"{ev_pie}. {ev_bar}"

        cio_2b = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Act before expiry** | **Phase 1 – Identify:** Generate a live list of assets expiring in the next sixty days using the monthly timeline so the team can see the true workload. <br><br>**Phase 2 – Decide:** For each asset choose whether to extend replace or repair while coverage still applies and prioritize the months with the highest expiry counts. <br><br>**Phase 3 – Track:** Update CMDB and reconcile outcomes so repeated work is avoided and lessons feed the next cycle. | - Converts unpredictable break fix spending into planned actions that fit the budget cycle.<br><br>- Avoids emergency purchases and rush shipping because plans are made before coverage ends.<br><br>- Smooths the spending curve across months which reduces cash flow shocks for finance.<br><br>- Increases leverage with vendors because negotiations use a consolidated view of upcoming demand. | **At-risk count (next 60d) × Avg repair cost**. Use the month bars to quantify at-risk inventory; e.g., peak **{peak_month} = {peak_cnt}**. | {ev_str} |
| **Bundle vendor negotiations** | **Phase 1 – Aggregate:** Group expiries by month and vendor to create volume that justifies discount discussions. <br><br>**Phase 2 – Negotiate:** Seek multi asset extensions and support bundles while focusing on peak months where leverage is strongest. <br><br>**Phase 3 – Benchmark:** Compare negotiated rates to list prices and lock a rate card for repeatable use. | - Lowers per unit extension prices because vendors respond to bundled volume and predictable schedules.<br><br>- Reduces purchase order and administrative churn because larger consolidated orders replace many small transactions.<br><br>- Speeds vendor turnaround because capacity is pre booked for the heavy months.<br><br>- Improves warranty terms because scale enables better service commitments. | **(List − Negotiated) × Assets in peak month** → peak **{peak_month}: {peak_cnt}**. | {ev_bar} |
| **Exploit claim windows** | **Phase 1 – Scan:** Detect incidents that occur on devices in the active warranty slice so claims can be filed in time. <br><br>**Phase 2 – File:** Submit return merchandise authorizations with diagnostics before expiry and track vendor cycle time to closure. <br><br>**Phase 3 – Verify:** Confirm the device is restored and post claim values to finance so savings are visible. | - Shifts costs from internal budgets to vendor coverage because valid claims are captured before deadlines.<br><br>- Cuts downtime because repairs or swaps are processed faster under warranty workflows.<br><br>- Raises the overall health of at risk cohorts because recurring faults are addressed promptly.<br><br>- Builds evidence for vendor performance reviews which supports stronger negotiations later. | **Claims filed × Avg claim value**; size “active” share from pie (**{ev_pie}**). | {ev_pie} |
"""
        , "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Auto workorders pre-expiry** | **Phase 1 – Rule:** Configure automation to create tickets forty five days before each expiry and include owner and site context so assignment is instant. <br><br>**Phase 2 – Assign:** Balance the work across technicians using the monthly workload bars so no one month overwhelms the team. <br><br>**Phase 3 – SLA:** Enforce completion before the deadline and expose exceptions so leaders can intervene early. | - Smooths technician workload which avoids overtime spikes and last minute scrambles.<br><br>- Improves predictability which allows teams to plan other work around renewal sprints.<br><br>- Reduces missed expiries because every item has a dated task and escalation path.<br><br>- Increases throughput because context rich tickets get actioned without extra clarification. | **Lead-time gain (days) × Jobs in peak month** (peak **{peak_month}: {peak_cnt}**). | {ev_bar} |
| **Renewal calendar sprints** | **Phase 1 – Sprint windows:** Create time boxed renewal sprints around peak months so focus is high and distractions are limited. <br><br>**Phase 2 – Kanban:** Maintain a clear board that shows done blocked and at risk so the team can unblock issues in daily stand ups. <br><br>**Phase 3 – Retro:** Capture lessons learned after each sprint so the process improves for the next cycle. | - Reduces variance in monthly throughput because work is batched and prioritized deliberately.<br><br>- Increases accountability because blockers and owners are visible to everyone.<br><br>- Shortens cycle time because small impediments are surfaced and removed quickly.<br><br>- Builds a repeatable playbook that becomes faster with each iteration. | **Variance↓ of monthly expiries vs baseline ({avg_pm:.1f}/month)**. | {ev_bar} |
| **SLA watch on expiring devices** | **Phase 1 – Tag:** Link expiring assets to high stakes service level commitments and VIP users so they receive priority handling. <br><br>**Phase 2 – Escalate:** Route issues on these devices to a faster queue during the risk window so outages are minimized. <br><br>**Phase 3 – Review:** Replace chronic offenders early so service remains stable. | - Prevents critical incidents from breaching contracts because at risk devices get special attention.<br><br>- Protects user productivity in key areas because issues are addressed faster during sensitive periods.<br><br>- Reduces emergency work because weak devices are swapped out before they fail.<br><br>- Increases leadership confidence because the most important users experience fewer disruptions. | **Urgent breaches avoided × Time saved** referencing expiring counts per month. | {ev_bar} |
"""
        , "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Notify owners early** | **Phase 1 – Thresholds:** Send clear alerts N days before expiry with simple recommended actions so users know exactly what to do. <br><br>**Phase 2 – Options:** Provide extend repair or replace options with timelines and FAQs so users can choose the least disruptive path. <br><br>**Phase 3 – Confirm:** Capture acknowledgement and preferred scheduling so handoffs are smooth. | - Reduces surprise failures because users are informed well before coverage ends.<br><br>- Makes planning easier for teams because swaps can align with project or travel dates.<br><br>- Lowers anxiety because timelines and steps are transparent and simple.<br><br>- Cuts escalation volume because expectations are managed proactively. | **Incidents avoided × Handling cost** correlated to expiring volume in **{peak_month} ({peak_cnt})**. | {ev_bar} |
| **Loaner pool in peak months** | **Phase 1 – Size:** Calculate the required loaner pool using peak expiry counts multiplied by expected failure rate so capacity is right sized. <br><br>**Phase 2 – Stage:** Place units at high risk sites ahead of time so response is immediate. <br><br>**Phase 3 – Track:** Measure turnaround and user feedback after swaps and tune the pool as needed. | - Cuts downtime during busy months because users receive temporary devices immediately.<br><br>- Keeps projects moving because work continues while repairs or replacements are processed.<br><br>- Improves satisfaction because disruptions feel managed and professional.<br><br>- Reveals which sites need more buffer so future cycles are smoother. | **Downtime hours avoided × Users impacted** tied to peak month load. | {ev_bar} |
| **Clear guidance portal** | **Phase 1 – Playbooks:** Publish plain language repair extend and replace flows so users can navigate without assistance. <br><br>**Phase 2 – Self-service:** Offer status tracking and simple forms so interactions are quick and consistent. <br><br>**Phase 3 – Feedback:** Collect satisfaction and suggestions to refine content continuously. | - Raises user confidence because processes are easy to understand and follow.<br><br>- Reduces follow up questions because answers live in one place with current status.<br><br>- Speeds decisions because timelines and requirements are visible.<br><br>- Improves digital literacy around lifecycle which lowers support load over time. | **Calls avoided × Cost/call** scaled by expiring cohort sizes. | {ev_str} |
"""
        }
        render_cio_tables("CIO – Warranty Status & Expiry", cio_2b)

    # --------------------------------------------------------
    # 2c) Asset Utilization
    # --------------------------------------------------------
    with st.expander("📌 Asset Utilization (asset_status)"):
        if "asset_status" in df_filtered.columns and df_filtered["asset_status"].notna().any():
            stat_cnt = df_filtered["asset_status"].value_counts(dropna=True).reset_index()
            stat_cnt.columns = ["asset_status", "count"]
            fig = px.bar(
                stat_cnt, x="asset_status", y="count",
                title="Asset Status Distribution",
                text="count",
                color_discrete_sequence=BLUE_TONES
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)

            total = int(stat_cnt["count"].sum())
            in_use_count = stat_cnt.loc[stat_cnt["asset_status"].str.lower()=="in use","count"].sum()
            pct_in_use = 100.0 * in_use_count / max(total, 1)

            top_row = stat_cnt.iloc[0]
            low_row = stat_cnt.iloc[-1]

            _analysis_block(
                what="A utilization bar chart by asset status category.",
                x="Status categories",
                y="Asset count",
                shows=(
                    f"Total classified assets: **{total}**. "
                    f"Highest status: **{top_row['asset_status']}** (**{int(top_row['count'])}**). "
                    f"Lowest status: **{low_row['asset_status']}** (**{int(low_row['count'])}**). "
                    f"In-use share (if present): **{pct_in_use:.1f}%**. "
                    "A large non-‘in use’ footprint points to latent capacity or stale records; a high active share suggests efficient deployment."
                ),
                ops=(
                    "Redeploy from non-productive statuses to meet queued demand; "
                    "freeze new purchases while the idle pool exceeds a site-level threshold; "
                    "add exception rules for assets stuck in ‘available/repair/returned’ states beyond N days; "
                    "trend the in-use ratio weekly to validate that actions are reducing waste."
                ),
                why="Higher in-use ratio converts inventory into value, shortens fulfillment time, and defers CapEx; visibility into idle cohorts prevents silent stockpiling."
            )
        else:
            stat_cnt = pd.DataFrame(columns=["asset_status","count"])
            pct_in_use = 0.0
            st.info("No 'asset_status' data.")

        ev_c = (f"In-use ≈ {pct_in_use:.1f}%. Highest status "
                f"{(stat_cnt.iloc[0]['asset_status'] if not stat_cnt.empty else '—')} "
                f"({(int(stat_cnt.iloc[0]['count']) if not stat_cnt.empty else 0)}).") if not stat_cnt.empty else "No utilization evidence."

        cio_2c = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Redeploy idle units** | **Phase 1 – Identify:** Build a query for all records where status is not 'in use' and verify which ones are genuinely available rather than stale. <br><br>**Phase 2 – Allocate:** Match these units to queued demand by site so requests are fulfilled from stock before raising new purchases. <br><br>**Phase 3 – Gate:** Introduce a rule that blocks purchase requests until the idle pool drops below a target and make the pool visible to requesters. | - Reduces capital spend because existing assets are consumed before buying new ones.<br><br>- Lowers storage and handling costs because idle items move into productive use quickly.<br><br>- Shortens lead times for users because redeployment is faster than procurement cycles.<br><br>- Improves working capital efficiency because money stays unspent when demand is met from stock. | **Idle count × Unit cost** derived from status bars (non-'in use' sum). | {ev_c} |
| **Retire long-idle** | **Phase 1 – Detect:** Use `update_on` gaps to flag assets that have been idle beyond a defined threshold and verify their physical state. <br><br>**Phase 2 – Dispose:** Execute compliant disposal or harvest parts and update records with final status so audits are clean. <br><br>**Phase 3 – Replace:** Only replace units that are critical to operations so spending is targeted. | - Shrinks carrying costs because dormant items no longer occupy space and attention.<br><br>- Reduces audit and security exposure because untracked devices are removed from the environment.<br><br>- Recovers value through parts harvesting which offsets future repair spend.<br><br>- Keeps environments tidy which simplifies logistics and inventory checks. | **Idle pool × Carrying cost/month × Months**. | Status distribution shows idle pool size. |
| **Freeze new buys where surplus** | **Phase 1 – Threshold:** Define what constitutes surplus at each site and publish the rule so teams know the bar. <br><br>**Phase 2 – Consume:** Force issuance from the surplus pool before approving new requests so stock is right sized. <br><br>**Phase 3 – Review:** Reassess monthly and adjust thresholds so policy remains practical. | - Avoids unnecessary purchases because available devices are consumed first.<br><br>- Improves utilization KPIs which signals disciplined asset management to leadership.<br><br>- Reduces one off buying patterns which simplifies vendor management and delivery scheduling.<br><br>- Keeps stock aligned to actual demand which prevents silent accumulation. | **Avoided buys × Unit cost** vs time window. | {ev_c} |
"""
        , "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Automate status updates** | **Phase 1 – Hooks:** Connect status changes to events such as preventive maintenance assignment and return so records update in real time. <br><br>**Phase 2 – Audit:** Run a weekly query to find stale states and fix them in bulk so drift is corrected quickly. <br><br>**Phase 3 – KPI:** Publish freshness by site and team so owners keep data current. | - Improves inventory accuracy because records reflect the actual lifecycle stage at all times.<br><br>- Reduces escalations where field teams cannot locate devices because status is trustworthy.<br><br>- Speeds fulfillment since accurate data allows faster routing and approvals.<br><br>- Lowers mean time to repair when incidents reference the right device details. | **Freshness delta (days) × Tickets/month**. | Status groups enable rules. |
| **Exception reporting** | **Phase 1 – Rules:** Define what counts as stuck for each status for example more than fourteen days so the metric is objective. <br><br>**Phase 2 – Escalate:** Notify owners then managers when items breach the threshold so movement happens without manual chasing. <br><br>**Phase 3 – Close:** Resolve each case with a reason code so patterns are visible for process improvement. | - Removes bottlenecks faster because exceptions trigger targeted action.<br><br>- Lowers backlog age because items cannot linger unnoticed in queues.<br><br>- Strengthens accountability because escalations and closures are tracked to individuals and teams.<br><br>- Increases throughput in requests and repairs because assets flow to the right states promptly. | **Backlog days ↓ × Items** from non-in-use statuses. | {ev_c} |
| **Pool visibility** | **Phase 1 – Dashboard:** Provide an Available now view by site and category that updates daily so requesters can self serve. <br><br>**Phase 2 – Reserve:** Allow short holds and scheduled pickups to coordinate handoffs. <br><br>**Phase 3 – SLA:** Commit to a fulfillment target and track fill rate so service remains reliable. | - Shortens lead times because users can see and claim stock immediately.<br><br>- Reduces status pings because availability is transparent to everyone.<br><br>- Increases predictability because pickups and deliveries are scheduled in windows.<br><br>- Improves planning for projects because teams can align device readiness with milestones. | **Lead time ↓ × Requests** served from pool. | {ev_c} |
"""
        , "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Publish available pool** | **Phase 1 – Portal:** Expose real time stock lists with simple filters so users find what they need quickly. <br><br>**Phase 2 – Alerts:** Notify subscribers when stock appears at their site so demand can be met faster. <br><br>**Phase 3 – Feedback:** Collect short surveys after allocation to see if the device fit the need. | - Delivers faster access to devices which reduces user downtime and frustration.<br><br>- Builds trust because availability can be verified without raising tickets.<br><br>- Improves perceived responsiveness because allocations happen quickly and predictably.<br><br>- Captures feedback that helps refine model standards and stock levels. | **Requests served faster × CSAT uplift proxy**. | {ev_c} |
| **Priority allocation** | **Phase 1 – Map:** Maintain a list of critical roles and VIPs who require priority hardware access. <br><br>**Phase 2 – Guard:** Reserve a portion of capacity for these users and enforce the rule consistently. <br><br>**Phase 3 – Audit:** Review exceptions and swap speed to ensure the policy delivers the intended outcomes. | - Reduces downtime for high impact users which protects business outcomes.<br><br>- Prevents executive escalations because priority cases are resolved quickly.<br><br>- Maintains continuity for critical operations by ensuring spare capacity is always available.<br><br>- Signals fairness because the rules are documented and reviewed. | **Hours saved × Users** prioritized. | Status distribution evidences capacity. |
| **Feedback loop** | **Phase 1 – Check-ins:** Send a brief survey after each deploy or return to capture issues while memory is fresh. <br><br>**Phase 2 – Fix:** Address mismatches quickly and document the resolution so the next allocation is better. <br><br>**Phase 3 – Learn:** Update allocation rules and playbooks based on themes from feedback. | - Improves device user fit which reduces repeat complaints and tickets.<br><br>- Creates a continuous improvement cycle that compounds benefits over time.<br><br>- Increases satisfaction because users feel heard and see changes reflected in process updates.<br><br>- Lowers total support load because recurring issues are engineered out. | **Complaints ↓ × Handling cost**. | {ev_c} |
"""
        }
        render_cio_tables("CIO – Asset Utilization", cio_2c)

    # --------------------------------------------------------
    # 2d) Location / Region Distribution
    # --------------------------------------------------------
    with st.expander("📌 Hardware by Location / Region"):
        plots = 0
        evidence_bits = []

        if "location" in df_filtered.columns and df_filtered["location"].notna().any():
            loc = df_filtered.groupby("location", dropna=True).size().reset_index(name="count").sort_values("count", ascending=False)
            fig = px.bar(
                loc.head(20), x="location", y="count",
                title="Top Locations by Asset Count",
                text="count",
                color_discrete_sequence=BLUE_TONES
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)
            plots += 1
            evidence_bits.append(f"Top location: **{loc.iloc[0]['location']}** ({int(loc.iloc[0]['count'])}).")
            top_loc = str(loc.iloc[0]['location']); top_loc_cnt = int(loc.iloc[0]['count'])
            low_loc = str(loc.iloc[-1]['location']); low_loc_cnt = int(loc.iloc[-1]['count'])
            _analysis_block(
                what="A bar chart of asset concentration by location (top 20).",
                x="Location",
                y="Asset count",
                shows=(
                    f"Highest location: **{top_loc}** (**{top_loc_cnt}**). "
                    f"Lowest among displayed: **{low_loc}** (**{low_loc_cnt}**). "
                    "A steep drop-off from the top bar to the tail indicates a hub-and-spoke footprint; a flatter profile suggests balanced deployment."
                ),
                ops="Rebalance excess from hotspots to deficit sites; stage buffer stock at high-volume locations; coordinate logistics windows to reduce repeat trips.",
                why="Geographic concentration drives logistics cost, service ETAs, and how quickly users can be unblocked when devices fail."
            )
        else:
            loc = pd.DataFrame(columns=["location","count"])

        if "region" in df_filtered.columns and df_filtered["region"].notna().any():
            reg = df_filtered.groupby("region", dropna=True).size().reset_index(name="count").sort_values("count", ascending=False)
            fig2 = px.bar(
                reg, x="region", y="count",
                title="Assets by Region",
                text="count",
                color_discrete_sequence=BLUE_TONES
            )
            fig2.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True)
            plots += 1
            evidence_bits.append(f"Top region: **{reg.iloc[0]['region']}** ({int(reg.iloc[0]['count'])}).")
            top_reg = str(reg.iloc[0]['region']); top_reg_cnt = int(reg.iloc[0]['count'])
            low_reg = str(reg.iloc[-1]['region']); low_reg_cnt = int(reg.iloc[-1]['count'])
            _analysis_block(
                what="A bar chart of asset distribution by region.",
                x="Region",
                y="Asset count",
                shows=(
                    f"Highest region: **{top_reg}** (**{top_reg_cnt}**). "
                    f"Lowest region: **{low_reg}** (**{low_reg_cnt}**). "
                    "Regional gaps often mirror support coverage gaps; large spreads justify regional hubs and tiered SLAs."
                ),
                ops="Create regional repair hubs and tiered SLAs; batch logistics to reduce trips; align engineer rosters to regional demand.",
                why="Regional coverage dictates repair throughput, transport cost, and realistic SLA commitments for end users."
            )
        else:
            reg = pd.DataFrame(columns=["region","count"])

        ev = " ".join(evidence_bits) if evidence_bits else "No location/region evidence."
        if plots == 0:
            st.info("Add 'location' and/or 'region' columns to enable charts.")

        cio_2d = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Rebalance across sites** | **Phase 1 – Detect:** Use the charts to identify sites with surplus relative to median and confirm physical counts to avoid moving ghosts. <br><br>**Phase 2 – Move:** Plan transfers to deficit sites using fixed routes and windows so transport is efficient and predictable. <br><br>**Phase 3 – Lock:** Set local stock caps and trigger notifications when caps are breached so balance is maintained. | - Lowers procurement needs because excess at hotspots is consumed by sites that are short.<br><br>- Reduces storage and transport costs because moves are batched and scheduled rather than ad hoc.<br><br>- Delivers faster local fulfillment because devices are closer to users who need them.<br><br>- Reduces emergency shipments because stock levels are controlled proactively. | **Rebalanced units × Unit cost** (use top-site surplus vs median). | {ev} |
| **Batch logistics** | **Phase 1 – Group:** Consolidate deliveries and returns by site or region to increase drop density and reduce empty trips. <br><br>**Phase 2 – Route:** Optimize run sheets and loads so vehicles and technicians follow efficient paths. <br><br>**Phase 3 – SLA:** Define windowed arrivals and on site clinics for high volume nodes so stakeholders can plan around presence. | - Cuts the number of trips required which lowers fuel time and coordination overhead per device.<br><br>- Increases predictability because partners and users know when visits will happen.<br><br>- Raises technician productivity because travel time decreases and batch work increases.<br><br>- Improves customer perception because visits are organized and punctual. | **Trips avoided × Cost/trip** estimated from grouped volumes. | {ev} |
| **Local liquidation of excess** | **Phase 1 – Identify:** Flag overstocked sites with aging inventory and confirm which units are viable for disposal or donation. <br><br>**Phase 2 – Dispose/Sell:** Execute controlled local clearance or redeploy to NGOs with proper compliance checks. <br><br>**Phase 3 – Prevent:** Apply stock caps and exception alerts so over accumulation does not return. | - Cuts storage and security risk because unnecessary devices leave the environment in a managed way.<br><br>- Generates quick cash recovery which offsets new purchases where needed.<br><br>- Frees space for productive equipment which improves operations on site.<br><br>- Reduces future write offs because aging stock is handled before it becomes obsolete. | **Units cleared × Storage cost**. | {ev} |
"""
        , "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Stage buffer stock** | **Phase 1 – Choose:** Select the top volume sites using the charts so buffer stock is placed where it helps most. <br><br>**Phase 2 – Stock:** Define min and max levels for critical spares and keep them replenished. <br><br>**Phase 3 – Refill:** Reorder on trigger and track fill rate so service remains consistent. | - Increases first time fix rates because parts and devices are on hand locally.<br><br>- Shortens response times which reduces user downtime and complaints.<br><br>- Stabilizes service delivery because stock is managed by rules not by guesswork.<br><br>- Lowers escalations because outages are resolved faster at hotspots. | **Lead time saved × Requests** at top sites. | {ev} |
| **Regional repair hubs** | **Phase 1 – Select:** Establish hubs in dense regions where volumes justify specialized tools and spares. <br><br>**Phase 2 – Equip:** Staff hubs with the right equipment and skills aligned to the local demand pattern. <br><br>**Phase 3 – Measure:** Track turnaround time and queue health to tune capacity. | - Lifts throughput because repairs happen closer to where devices operate.<br><br>- Reduces transit delay which accelerates closure times for incidents and work orders.<br><br>- Standardizes quality because specialized teams repeat similar jobs efficiently.<br><br>- Improves engineer productivity because travel is minimized and bench time is maximized. | **Turnaround days ↓ × Jobs**. | {ev} |
| **Site-level SLA** | **Phase 1 – Tier:** Define realistic ETAs by geography and access constraints so commitments reflect reality. <br><br>**Phase 2 – Publish:** Communicate SLAs by site and region and show breach dashboards so expectations are aligned. <br><br>**Phase 3 – Review:** Run monthly root cause reviews on breaches and adjust resources where gaps persist. | - Sets clear expectations which reduces frustration and follow ups from stakeholders.<br><br>- Focuses resources where the data shows consistent misses so improvements stick.<br><br>- Improves planning by business units because service windows are understood by location.<br><br>- Reduces penalties and reputational risk because breach rates trend down. | **Breach rate ↓ × Penalty**. | {ev} |
"""
        , "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Site-specific ETAs** | **Phase 1 – Calculate:** Include transit and access windows when estimating ETAs so users receive credible timelines. <br><br>**Phase 2 – Communicate:** Publish ETAs in the portal and emails so requests do not require manual chasing. <br><br>**Phase 3 – Update:** Send proactive delay alerts when conditions change so users can replan. | - Reduces complaints because timelines match what actually happens on the ground.<br><br>- Improves trust at remote sites because communication is proactive and consistent.<br><br>- Helps local teams coordinate access and resources which reduces wasted visits.<br><br>- Creates a transparent service culture which lifts satisfaction scores. | **Complaints reduced × Cost/case** proportional to site volumes. | {ev} |
| **Transparent queue** | **Phase 1 – Show:** Display per site request queues and aging so users understand their position. <br><br>**Phase 2 – Prioritize:** Apply VIP and critical rules openly so ordering is clear. <br><br>**Phase 3 – Report:** Share weekly KPIs so performance is visible and improves over time. | - Cuts status inquiries because position in queue is visible.<br><br>- Increases perceived fairness because prioritization rules are explicit and consistent.<br><br>- Eases planning for users who can infer likely completion windows.<br><br>- Encourages continuous improvement because metrics are visible to all stakeholders. | **Follow-ups avoided × Handling cost**. | {ev} |
| **Mobile swap events** | **Phase 1 – Plan:** Schedule on site swap and repair days at hub locations based on queue size and incident history. <br><br>**Phase 2 – Execute:** Complete batches of fixes and refreshes in one visit with proper checklists. <br><br>**Phase 3 – Review:** Capture CSAT and backlog burn down to measure impact and refine the approach. | - Clears backlogs quickly which resets user experience at busy sites.<br><br>- Reduces downtime because many users are served in a single coordinated effort.<br><br>- Demonstrates visible service which raises confidence in IT delivery.<br><br>- Generates insights that improve future events and day to day processes. | **Hours saved × Users served** at hub sites. | {ev} |
"""
        }
        render_cio_tables("CIO – Location Distribution", cio_2d)

    # --------------------------------------------------------
    # 2e) Age Cohorts
    # --------------------------------------------------------
    with st.expander("📌 Asset Age Cohorts (warranty_start / update_on)"):
        age_col = None
        for c in ["warranty_start", "update_on"]:
            if _exists_and_nonempty(df_filtered, c):
                age_col = c
                break
        if age_col:
            base = df_filtered[df_filtered[age_col].notna()].copy()
            base["age_years"] = (pd.Timestamp.today().normalize() - base[age_col]).dt.days / 365.25
            bins = [-0.01, 1, 2, 3, 4, 5, 10, np.inf]
            labels = ["<1y","1–2y","2–3y","3–4y","4–5y","5–10y",">10y"]
            base["age_bucket"] = pd.cut(base["age_years"], bins=bins, labels=labels, include_lowest=True, right=True)
            age_counts = base["age_bucket"].value_counts(dropna=False).reindex(labels).fillna(0).reset_index()
            age_counts.columns = ["age_bucket","count"]
            fig = px.bar(
                age_counts, x="age_bucket", y="count",
                text="count",
                title=f"Asset Age Cohorts (based on {age_col})",
                color_discrete_sequence=BLUE_TONES
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)
            median_age = float(base["age_years"].median()) if base["age_years"].notna().any() else 0.0

            if age_counts["count"].sum() > 0:
                top_bucket_idx = age_counts["count"].idxmax()
                low_bucket_idx = age_counts["count"].idxmin()
                top_bucket = age_counts.loc[top_bucket_idx, "age_bucket"]
                top_count  = int(age_counts.loc[top_bucket_idx, "count"])
                low_bucket = age_counts.loc[low_bucket_idx, "age_bucket"]
                low_count  = int(age_counts.loc[low_bucket_idx, "count"])
                shows = (
                    f"Median age: **{median_age:.1f}y**. "
                    f"Largest cohort: **{top_bucket}** (**{top_count}**). "
                    f"Smallest cohort: **{low_bucket}** (**{low_count}**). "
                    "A tail heavy in >5y devices signals rising failure risk and performance complaints; a younger tail indicates recent refresh investment."
                )
            else:
                shows = "No age distribution available."

            _analysis_block(
                what="A cohort bar chart grouping assets by age in years.",
                x="Age cohort buckets",
                y="Asset count per cohort",
                shows=shows,
                ops="Prioritize refresh on oldest cohorts; defer stable <2y to conserve CapEx; schedule preventive maintenance on 3–5y to lift reliability; align wave plans with business windows.",
                why="Aging drives higher failure likelihood, lower performance, and rising support cost; staged refresh keeps experience consistent without budget shocks."
            )

            ev_e = f"Median age ≈ {median_age:.1f}y; largest cohort = {top_bucket} ({top_count}); smallest = {low_bucket} ({low_count})." if age_counts["count"].sum() > 0 else "No age evidence."
        else:
            st.warning("No suitable date column for age calculation.")
            ev_e = "No age evidence."

        cio_2e = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Phase refresh by age** | **Phase 1 – Prioritize:** Rank cohorts by risk performance and business criticality and create a refresh list that starts with the oldest devices. <br><br>**Phase 2 – Defer:** Delay refresh for stable devices under two years old so budget is focused where risk is higher. <br><br>**Phase 3 – Track:** Measure failure and satisfaction changes after each wave so the plan is validated and refined. | - Smooths capital spending across quarters which prevents large spikes that strain budgets.<br><br>- Retires high risk gear before it fails which reduces unplanned incidents and user downtime.<br><br>- Lowers parts and repair spend because problematic cohorts leave the environment sooner.<br><br>- Aligns refresh with fiscal windows which makes approvals and scheduling easier. | **Deferred units (younger cohorts) × Unit cost**; **Replaced units (oldest cohort) × Delta OPEX**. | {ev_e} |
| **Parts harvesting** | **Phase 1 – Identify:** Find devices over five years old and list compatible components that can be safely reused. <br><br>**Phase 2 – Salvage:** Recover RAM SSD and PSU parts through a controlled process and certify them for reuse. <br><br>**Phase 3 – Catalog:** Record reuse value and success rates so savings are visible and repeatable. | - Lowers future spare procurement costs because recovered parts satisfy a portion of demand.<br><br>- Speeds repairs because common parts are on hand without waiting for orders.<br><br>- Reduces e waste which improves sustainability outcomes for the organization.<br><br>- Increases resilience during supply constraints because critical parts are locally available. | **Donor count × Parts reuse value** using >5y counts. | {ev_e} |
| **Selective warranty extensions** | **Phase 1 – Score:** Evaluate each device on age failure history and business criticality to see where extension beats replacement. <br><br>**Phase 2 – Compare:** Model the total cost of ownership for extension versus replacement and document the break even point. <br><br>**Phase 3 – Decide:** Extend when economics are favorable and set explicit sunset dates so decisions are revisited on time. | - Shifts spend from large upfront purchases to predictable operating costs where suitable.<br><br>- Buys time to plan orderly refresh for hard to replace devices which reduces disruption.<br><br>- Avoids service interruptions because borderline devices remain covered during the bridge period.<br><br>- Improves budget predictability because extension costs are known and scheduled. | **Extension cost vs Replacement cost × Units in cohort**. | {ev_e} |
"""
        , "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Preventive PM on 3–5y** | **Phase 1 – Target:** Identify mid age devices likely to suffer wear and create a preventive maintenance list. <br><br>**Phase 2 – Cadence:** Implement scheduled cleaning firmware and diagnostics to catch issues early. <br><br>**Phase 3 – Metrics:** Track failures per one hundred assets and mean time between failures to confirm the effect. | - Reduces unplanned outages because emerging problems are addressed before they cause incidents.<br><br>- Increases availability which stabilizes end user productivity.<br><br>- Makes technician workload more predictable because maintenance is planned rather than reactive.<br><br>- Improves user stability which lowers complaint volume. | **Incidents avoided × Resolution time** using cohort volumes. | {ev_e} |
| **Staged upgrades** | **Phase 1 – Wave plan:** Sequence cohorts into waves that minimize business impact and avoid peak periods. <br><br>**Phase 2 – Resourcing:** Align engineers windows and communications so each wave completes cleanly. <br><br>**Phase 3 – Validate:** Measure MTTR and CSAT changes with a rollback path for any issues. | - Increases deployment throughput because work is organized and resourced for success.<br><br>- Reduces change collisions because upgrades are coordinated to avoid conflicts.<br><br>- Lowers after hours work because waves are planned into suitable windows.<br><br>- Increases confidence because metrics demonstrate improvement after each wave. | **Deployment variance ↓ × Hours** across waves. | {ev_e} |
| **Capacity planning** | **Phase 1 – Align:** Sync refresh with project starts and hiring peaks so devices are ready when teams grow. <br><br>**Phase 2 – Buffer:** Maintain a small loaner pool and overlap windows so continuity is preserved during swaps. <br><br>**Phase 3 – Review:** Compare planned versus actual and tune cadence for the next quarter. | - Reduces disruption to delivery teams because hardware readiness matches staffing plans.<br><br>- Allocates engineers more effectively because busy periods are known in advance.<br><br>- Lowers context switching because upgrades occur in coordinated blocks.<br><br>- Improves schedule adherence because lessons are folded into the next cycle. | **Overlap hours saved × Teams**. | {ev_e} |
"""
        , "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Communicate roadmap** | **Phase 1 – Publish:** Share the cohort schedule and criteria so users know when they will be refreshed and why. <br><br>**Phase 2 – Notify:** Send pre swap notices with options and timelines so users can prepare. <br><br>**Phase 3 – Feedback:** Capture satisfaction after each wave and refine communication for the next one. | - Creates predictability which reduces escalations and last minute surprises.<br><br>- Improves acceptance of refresh because rationale and timing are transparent.<br><br>- Smooths handovers and onboarding because users are ready for the change.<br><br>- Builds goodwill because feedback is requested and acted upon. | **Escalations avoided × Cost/case** compared against cohort sizes. | {ev_e} |
| **Priority upgrades for heavy users** | **Phase 1 – Identify:** Use role and telemetry to find power users who benefit most from newer hardware. <br><br>**Phase 2 – Match:** Provide higher specification models to these users first so productivity gains are realized quickly. <br><br>**Phase 3 – Verify:** Track productivity proxies and ticket reduction to confirm the return. | - Delivers faster machines where they create the most value which lifts throughput for critical teams.<br><br>- Reduces slow device complaints because bottlenecks are addressed proactively.<br><br>- Improves morale for high demand roles which supports retention and performance.<br><br>- Focuses budget on visible wins which strengthens stakeholder support. | **Hours lost ↓ × Users** in heavy-load cohorts. | {ev_e} |
| **Loaners during swaps** | **Phase 1 – Size:** Set the loaner pool based on wave volume and expected device time out so coverage is sufficient. <br><br>**Phase 2 – Stage:** Position loaners at sites before swaps begin so users can switch with minimal delay. <br><br>**Phase 3 – Track:** Measure turnaround and communication quality to keep experiences smooth. | - Minimizes downtime during refresh which preserves business continuity.<br><br>- Keeps users productive while primary devices are serviced.<br><br>- Increases satisfaction because the process feels organized and considerate.<br><br>- Reveals bottlenecks so future swaps are even faster. | **Hours saved × Users** swapped. | {ev_e} |
"""
        }
        render_cio_tables("CIO – Age Cohorts", cio_2e)

    # --------------------------------------------------------
    # 2f) Manufacturer / Model Mix
    # --------------------------------------------------------
    with st.expander("📌 Manufacturer & Model Mix"):
        plots = 0
        evidence_bits = []

        if "brand" in df_filtered.columns and df_filtered["brand"].notna().any():
            brand = (
                df_filtered.groupby("brand", dropna=True)
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            fig = px.bar(
                brand, x="brand", y="count",
                text="count",
                title="Assets by Brand",
                color_discrete_sequence=BLUE_TONES
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)
            plots += 1
            evidence_bits.append(f"Top brand: **{brand.iloc[0]['brand']}** ({int(brand.iloc[0]['count'])}).")

            top_brand, top_brand_cnt = str(brand.iloc[0]["brand"]), int(brand.iloc[0]["count"])
            low_brand, low_brand_cnt = str(brand.iloc[-1]["brand"]), int(brand.iloc[-1]["count"])
            _analysis_block(
                what="A bar chart showing brand concentration in the fleet.",
                x="Brand",
                y="Asset count",
                shows=(
                    f"Highest brand: **{top_brand}** (**{top_brand_cnt}**). "
                    f"Lowest brand: **{low_brand}** (**{low_brand_cnt}**). "
                    "A short head with a long tail implies many fringe SKUs—expensive for spares, training, and imaging."
                ),
                ops="Consolidate purchases on top brands; eliminate fringe SKUs to reduce spares/training overhead; align vendor scorecards to concentration and failure rates.",
                why="Vendor concentration improves cost leverage, image standardization, and support efficiency; fragmentation amplifies complexity and cost."
            )
        else:
            brand = pd.DataFrame(columns=["brand","count"])

        if {"brand","model"}.issubset(df_filtered.columns) and df_filtered["model"].notna().any():
            bm = (
                df_filtered.groupby(["brand","model"], dropna=True)
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            bm["brand"] = bm["brand"].astype(str)
            bm["model"] = bm["model"].astype(str)
            fig2 = px.treemap(
                bm, path=["brand","model"], values="count",
                title="Brand → Model Composition",
                color_discrete_sequence=BLUE_TONES
            )
            st.plotly_chart(fig2, use_container_width=True)
            plots += 1
            evidence_bits.append(f"Top model: **{bm.iloc[0]['brand']} {bm.iloc[0]['model']}** ({int(bm.iloc[0]['count'])}).")

            top_model_brand = str(bm.iloc[0]["brand"]); top_model_model = str(bm.iloc[0]["model"]); top_model_cnt = int(bm.iloc[0]["count"])
            _analysis_block(
                what="A treemap visualizing composition from brand down to model.",
                x="Hierarchical path: Brand → Model",
                y="Rectangle size encodes count",
                shows=f"Most common configuration: **{top_model_brand} {top_model_model}** (**{top_model_cnt}** devices). A few dominant model blocks simplify imaging, spares, and training.",
                ops="Establish golden images and baseline packages for top SKUs; pre-stock critical spares aligned to model mix; track incident rate per model to refine standards.",
                why="Standardization reduces build variance, repair time, and incident rates; it also makes refresh waves and support onboarding far easier."
            )
        else:
            bm = pd.DataFrame(columns=["brand","model","count"])

        ev = " ".join(evidence_bits) if evidence_bits else "No model evidence."

        cio_2f = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Vendor consolidation** | **Phase 1 – Target:** Select the top brands and models such as **{(brand.iloc[0]['brand'] if not brand.empty else '—')}** and **{(bm.iloc[0]['brand']+' '+bm.iloc[0]['model'] if not bm.empty else '—')}** and define them as standards. <br><br>**Phase 2 – Deal:** Negotiate volume pricing support bundles and standardized configurations with those vendors. <br><br>**Phase 3 – Audit:** Track realized savings versus list prices and adjust refresh cadence as needed. | - Lowers unit prices because committed volume and standard builds justify better discounts.<br><br>- Improves warranty and support terms because vendors compete for standardized share of wallet.<br><br>- Simplifies procurement because fewer SKUs and templates reduce cycle time.<br><br>- Streamlines imaging and deployment because standards reduce variance. | **Negotiated discount % × Units** (brand **{(int(brand.iloc[0]['count']) if not brand.empty else 0)}**, model **{(int(bm.iloc[0]['count']) if not bm.empty else 0)}**). | {ev} |
| **Eliminate fringe SKUs** | **Phase 1 – Flag:** Identify low volume models that create outsized support overhead and document their retirement plan. <br><br>**Phase 2 – Exit:** Allow these models to churn naturally or replace them opportunistically while maintaining service. <br><br>**Phase 3 – Prevent:** Use catalogue controls to block re entry of non standard SKUs. | - Reduces spares and training complexity because technicians focus on a smaller set of devices.<br><br>- Accelerates image maintenance and patching because fewer variants require testing.<br><br>- Cuts time wasted on one off driver hunts which improves repair speed.<br><br>- Clarifies capacity planning because demand forecasts are based on fewer standardized models. | **Fringe units × Overhead cost/unit** (use lowest bars). | {ev} |
| **Timed volume buys** | **Phase 1 – Align:** Time purchases with refresh clusters and fiscal windows so orders land when deployment capacity exists. <br><br>**Phase 2 – Lock:** Secure tiered discounts and delivery slots based on the grouped volume so vendors commit capacity. <br><br>**Phase 3 – Review:** Reprice quarterly and benchmark vendor performance so deals remain competitive. | - Achieves better price leverage because orders are aggregated into meaningful volumes.<br><br>- Improves delivery predictability because slots are reserved ahead of demand peaks.<br><br>- Reduces stockouts and project delays because supply is matched to planned waves.<br><br>- Maintains commercial pressure because performance is reviewed regularly. | **Discount × Units in wave** sized by top brand/model counts. | {ev} |
"""
        , "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Golden image per model** | **Phase 1 – Build:** Create a hardened image and policy baseline for each standard model and version control the artifacts. <br><br>**Phase 2 – Validate:** Pilot with a small cohort and include rollback steps so risks are contained. <br><br>**Phase 3 – Roll:** Deploy broadly with clear versioning and change notes so teams know what is running. | - Speeds provisioning because standard images deploy quickly and reliably.<br><br>- Reduces configuration errors which improves stability for users.<br><br>- Lowers mean time to repair because technicians know the baseline state.<br><br>- Simplifies troubleshooting because variability is minimized. | **Setup time saved × Deployments** on top SKUs. | {ev} |
| **Driver/package baselines** | **Phase 1 – Curate:** Maintain model specific driver and software bundles with explicit compatibility notes. <br><br>**Phase 2 – Automate:** Pipeline updates through rings so changes move from canary to broad deployment safely. <br><br>**Phase 3 – Telemetry:** Monitor for regressions and auto rollback when issues are detected. | - Reduces incidents caused by updates because changes are staged and measured.<br><br>- Speeds fixes because known good bundles can be applied quickly.<br><br>- Maintains predictable behavior across the fleet which stabilizes user experience.<br><br>- Improves release discipline because telemetry closes the loop. | **Incident rate ↓ × Resolution time** for standardized models. | {ev} |
| **Spare pool by standard** | **Phase 1 – Stock:** Hold critical parts for top SKUs based on observed failure patterns. <br><br>**Phase 2 – Replenish:** Set min max rules and automate reorders so availability stays high. <br><br>**Phase 3 – KPI:** Track mean time to repair and fill rate by model to tune holdings. | - Lowers repair times because the right parts are ready when needed.<br><br>- Raises availability because common failures are resolved quickly.<br><br>- Reduces escalations because first time fix rates improve.<br><br>- Optimizes inventory because data guides which parts to stock. | **Repair time ↓ × Jobs** correlated to top SKUs. | {ev} |
"""
        , "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| **Consistent experience** | **Phase 1 – Match:** Map device specifications to role profiles so users receive hardware aligned to their work. <br><br>**Phase 2 – Standard:** Keep builds and versions consistent across each standard so experience is predictable. <br><br>**Phase 3 – Measure:** Collect satisfaction in week one and after major updates to confirm the promise is met. | - Reduces usability complaints because devices perform as expected for each role.<br><br>- Shortens time to productive for new hires because standard setups are familiar and stable.<br><br>- Clarifies expectations which reduces friction with support teams.<br><br>- Creates a coherent user experience that strengthens trust in IT. | **Tickets avoided × Cost/ticket** when standard builds dominate. | {ev} |
| **Predictable performance** | **Phase 1 – Bench:** Define performance KPIs for top SKUs and document acceptable variance ranges. <br><br>**Phase 2 – Publish:** Share targets with users and support so everyone knows what good looks like. <br><br>**Phase 3 – Tune:** Swap or remediate weak performers and feed findings into standards. | - Raises user confidence because performance is measured and transparent.<br><br>- Reduces slow device complaints because underperformers are addressed systematically.<br><br>- Guides procurement and refresh choices with data which improves long term outcomes.<br><br>- Stabilizes the help desk because performance questions have objective answers. | **Variance ↓ in CSAT × Users** on top models. | {ev} |
| **Clear lifecycle roadmap** | **Phase 1 – Window:** Define uniform refresh windows per standard so users know when change will occur. <br><br>**Phase 2 – Communicate:** Share the plan and eligibility criteria well ahead of action so teams can prepare. <br><br>**Phase 3 – Track:** Publish a burn down of slips and blockers so transparency drives delivery. | - Reduces disruption from ad hoc changes because refresh is scheduled and orderly.<br><br>- Helps stakeholders plan around device transitions because dates are communicated early.<br><br>- Raises adherence to timelines because progress is visible and managed.<br><br>- Increases adoption during refresh because expectations are clear and met. | **Reschedule calls ↓ × Cost/call** during standardized waves. | {ev} |
"""
        }
        render_cio_tables("CIO – Manufacturer & Model Mix", cio_2f)
