# utils_asset_inventory/recommendation_assets/asset_assignments.py
import re
import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------
# Column normalization & synonym resolution
# ------------------------------------------------------------
def _canonize(name: str) -> str:
    """lowercase, strip, collapse non-alnum to single underscore"""
    name = str(name)
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name

def _normalize_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_canonize(c) for c in df.columns]
    return df

def _resolve(df: pd.DataFrame, candidates) -> str | None:
    """Return first present canonical column from candidates (list of strings)."""
    for c in candidates:
        cc = _canonize(c)
        if cc in df.columns:
            return cc
    return None

def _fail_info(df: pd.DataFrame, label: str, tried: list[str]):
    missing = ", ".join([f"`{_canonize(t)}`" for t in tried])
    st.warning(f"Could not find a suitable **{label}** column. Looked for: {missing}")

def _fmt_int(n) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"

def _fmt_float(x, places=1) -> str:
    try:
        return f"{float(x):.{places}f}"
    except Exception:
        return "0"

# ------------------------------------------------------------
# Helper for CIO tables
# ------------------------------------------------------------
def render_cio_tables(title, cio):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio.get("cost", ""), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio.get("performance", ""), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio.get("satisfaction", ""), unsafe_allow_html=True)

# ------------------------------------------------------------
# Target 4 – Asset Assignments
# ------------------------------------------------------------
def asset_assignments(df_filtered: pd.DataFrame):
    # Work on a normalized copy (column names canonicalized)
    raw_df = df_filtered.copy()
    df = _normalize_df_columns(df_filtered)

    # 🔁 Common synonym bundles (expanded to match your CSV)
    owner_syns       = [
        "owner", "assigned_to", "user", "custodian", "employee", "end_user", "assignee",
        "previous owner", "previous_owner", "update by", "updated_by", "updated by"
    ]
    asset_id_syns    = [
        "asset_id", "assetid", "asset_id_", "asset", "device_id", "serial_number",
        "serial number", "asset code", "asset code id"
    ]
    dept_syns        = ["department", "dept", "functional_department", "division", "team"]
    jml_status_syns  = ["jml_status", "jml status", "movement_status", "joiner_mover_leaver", "jml"]
    jml_date_syns    = ["jml_date", "jml date", "movement_date", "status_date", "effective_date"]
    region_syns      = ["region", "site_region", "area", "zone"]
    status_syns      = ["asset_status", "status", "device_status", "hardware_status"]

    # --------------------------------------------------------
    # 4a. Assets per User / Owner
    # --------------------------------------------------------
    with st.expander("📌 Assets per User / Owner"):
        col_owner = _resolve(df, owner_syns)
        col_asset = _resolve(df, asset_id_syns)

        if col_owner and col_asset:
            owner_ct = (
                df.groupby(col_owner)[col_asset]
                  .nunique()
                  .reset_index(name="asset_count")
            )
            if owner_ct.empty:
                st.info("No rows available after grouping owners.")
            else:
                top25 = owner_ct.sort_values("asset_count", ascending=False).head(25)
                fig = px.bar(
                    top25, x=col_owner, y="asset_count", text="asset_count",
                    title="Top 25 Users by Assigned Assets",
                    labels={col_owner: "Owner", "asset_count": "Assets"}
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                total_assigned = int(owner_ct["asset_count"].sum())
                avg_per_user   = float(owner_ct["asset_count"].mean()) if len(owner_ct) else 0.0
                peak_row       = owner_ct.iloc[owner_ct["asset_count"].idxmax()]
                low_row        = owner_ct.iloc[owner_ct["asset_count"].idxmin()]

                st.markdown("### Analysis – User Ownership Distribution")
                st.write(f"""
**What this graph is:** A bar chart showing **how many unique assets are assigned per user (Owner)**.  
**X-axis:** Owner (user).  
**Y-axis:** Number of uniquely assigned assets.

**What it shows in your data:**  
- Largest holder: **{peak_row[col_owner]}** with **{_fmt_int(peak_row['asset_count'])} assets**.  
- Smallest holder: **{low_row[col_owner]}** with **{_fmt_int(low_row['asset_count'])} assets**.  
- **Total assigned (unique across users):** {_fmt_int(total_assigned)}. **Average per user:** {_fmt_float(avg_per_user)}.

**Overall:** A steep left-skew implies **concentration risk** (some users hold many devices). A flatter shape suggests **balanced allocation**.

**How to read it operationally:**  
- **Peaks:** Audit high-holders for idle or duplicate devices.  
- **Plateaus:** Treat as baseline; keep lifecycle records tight.  
- **Downswings:** Check whether under-equipped roles are blocked.

**Why this matters:** Misallocated hardware becomes **cost debt**—unnecessary purchases, loss risk, and slower resolution.
""")

                evidence_4a = f"Peak owner **{peak_row[col_owner]} = {_fmt_int(peak_row['asset_count'])}**; lowest **{low_row[col_owner]} = {_fmt_int(low_row['asset_count'])}**; avg/user **{_fmt_float(avg_per_user)}**."

                # === Expanded CIO tables (Explanation & Benefits elaborated) ===
                cio_4a = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Reclaim idle assets from high-holders** | **Phase 1 – Identify:** Use the chart to list users above the average of **{_fmt_float(avg_per_user)}** and those in the top decile by number of devices, then pull endpoint usage logs and last-seen dates to distinguish genuinely active devices from idle units. <br><br> **Phase 2 – Verify:** Contact owners and managers with a pre-filled checklist that captures business justification, project code and device purpose, and set a clear response deadline so non-responses are auto-escalated. <br><br> **Phase 3 – Reassign:** Scan in recovered units to a central pool, tag physical condition, refresh the image and publish the stock with a ready-to-deploy status so field teams can book immediately. | - Unlocks immediate capital expenditure avoidance because existing devices are redeployed instead of buying new units. <br><br> - Reduces storage, insurance and maintenance overhead because fewer dormant devices sit in the storeroom. <br><br> - Improves asset visibility which lowers the probability of emergency purchases and last minute rentals. <br><br> - Increases refresh agility because a healthy pool enables faster swaps when incidents occur. | **Savings = (Reclaimed units × Unit price).** | Largest holder **{peak_row[col_owner]}** has **{_fmt_int(peak_row['asset_count'])}** versus average **{_fmt_float(avg_per_user)}**. |
| **Automate leaver returns** | **Phase 1 – Trigger:** When HR marks a leaver, automatically create a return ticket that includes the expected device list, pre-generated shipping label and clear instructions for the user and the manager. <br><br> **Phase 2 – Track:** Capture courier milestones and perform serial validation at receipt, and route exceptions such as missing accessories to finance or security with predefined actions. <br><br> **Phase 3 – Close:** Grade the device, refresh the image and publish it back to the ready pool with a turnaround SLA, then close the loop with HR and the manager. | - Shrinks loss risk and write offs because devices are collected predictably and traced at each step. <br><br> - Accelerates redeployment to teams with live demand which improves time to value. <br><br> - Reduces manual coordination effort for IT and HR because the workflow is automated. <br><br> - Strengthens audit readiness because every return has a verifiable trail. | **Savings = (Leaver assets returned × Unit price).** | Ownership skew evidences redeploy potential. |
| **Cap assignments per role** | **Phase 1 – Policy:** Define role based caps such as one device for standard users and two devices for mobile or VIP roles, and document explicit exceptions for lab gear and test devices. <br><br> **Phase 2 – Exceptions:** Implement a lightweight approval flow that requires a project ID, a business justification and an expiry date so exceptions are time bound. <br><br> **Phase 3 – Audit:** Run a quarterly variance report that highlights users above cap and records actions taken to reclaim or justify the variance. | - Prevents silent sprawl that inflates budgets because excess devices are flagged early. <br><br> - Improves fairness and planning because allocation rules are visible and enforced. <br><br> - Simplifies license and spare strategies because device counts align with actual role needs. <br><br> - Reduces end of year surprises because hidden inventory is eliminated. | **Savings = (Excess devices above cap × Unit price).** | Bar distribution shows where caps will bite. |
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Centralized assignment register** | **Phase 1 – Source:** Establish a single system of record that owns the truth for the relationship between owner and device and define it as authoritative for service desk and audits. <br><br> **Phase 2 – Automate:** Connect event hooks on handover, return and repair so the registry updates automatically without spreadsheet merges or email approvals. <br><br> **Phase 3 – Expose:** Provide fast search and API endpoints so agents and auditors can retrieve accurate context in seconds. | - Accelerates triage because agents see the correct device and owner instantly. <br><br> - Reduces mismatches and rework because duplicate or stale records are eliminated. <br><br> - Cuts time spent digging through multiple tools which improves first response times. <br><br> - Stabilizes downstream reporting because the data source is consistent. | **Time saved = (Lookup minutes saved × Tickets/month).** | Clear owner to asset mapping enables speed ups. |
| **Exception alerts for high-holders** | **Phase 1 – Thresholds:** Auto flag users above the mean plus a selected standard deviation or above the role cap so exceptions are systematic. <br><br> **Phase 2 – Review:** Run a monthly review with owners and managers that offers one click dispositions such as keep, reclaim or replace. <br><br> **Phase 3 – Act:** Schedule pickups and reassignments directly from the review output so decisions become actions. | - Drives proactive control which stops drift before it becomes a budget problem. <br><br> - Maintains a healthy ready pool which shortens lead times for swaps. <br><br> - Improves SLA predictability because device availability is steady. <br><br> - Reduces manual hunting because alerts concentrate attention on outliers. | **Benefit = (Excess found × time per case).** | Peak holder **{peak_row[col_owner]}** stands out in the chart. |
| **Self-check acknowledgements** | **Phase 1 – Quarterly:** Ask owners to confirm holdings via a simple link that is pre filled with serials and photos so validation is quick. <br><br> **Phase 2 – Chase:** Send auto reminders and escalate to managers for non responders to ensure closure. <br><br> **Phase 3 – Close:** Correct records and align accessories and licenses so inventory and entitlements match reality. | - Keeps data fresh which reduces incident back and forth when users request help. <br><br> - Enables smoother audits because ownership is verified regularly. <br><br> - Lowers disputes over who has what because confirmations create shared evidence. <br><br> - Increases confidence in asset counts which improves forecasting. | **Benefit = (Audit hours avoided × rate).** | Distribution supports periodic attestation. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **My-Assets portal** | **Phase 1 – View:** Provide a user portal that shows assigned devices, linked accessories and warranty dates so users know exactly what they hold. <br><br> **Phase 2 – Actions:** Enable self service return, replace and loaner requests with auto generated labels and clear pickup instructions. <br><br> **Phase 3 – SLA:** Display ETAs and live status so users have transparency throughout the process. | - Reduces “where is my device” calls because users can self check their portfolio. <br><br> - Improves perceived responsiveness because requests are initiated without waiting for the helpdesk. <br><br> - Increases trust because progress is visible and predictable. <br><br> - Decreases escalations because timelines and ownership are clear. | **Value = (Calls avoided × handling time).** | Ownership picture is clear from the chart. |
| **Fairness reporting** | **Phase 1 – Publish:** Share department and role allocation statistics with context on job requirements so stakeholders understand the why. <br><br> **Phase 2 – Explain:** Document the caps and the exception process so decisions are consistent. <br><br> **Phase 3 – Review:** Collect feedback and fine tune thresholds based on operational impact. | - Reduces complaints about perceived bias because the criteria are transparent. <br><br> - Aligns expectations between IT and the business because the rules are visible. <br><br> - Strengthens partnership with leaders because trade offs are data driven. <br><br> - Stabilizes demand because exception requests drop when standards feel fair. | **Value = (Escalations avoided × cost).** | Skew vs average **{_fmt_float(avg_per_user)}** guides messaging. |
| **Rapid swap process** | **Phase 1 – Loaners:** Maintain a small loaner pool per major site that is pre imaged and ready to ship with accessories. <br><br> **Phase 2 – Courier:** Enable same day or next day swap workflows with serial capture at both ends to protect chain of custody. <br><br> **Phase 3 – Close:** Return the old device for sanitization and publish it back to the pool so cycles stay tight. | - Reduces downtime for end users because replacements arrive quickly. <br><br> - Helps critical roles recover faster which protects business throughput. <br><br> - Decreases emergency purchases because a pool is always available. <br><br> - Improves user confidence because incidents end with a predictable fix. | **Benefit = (Downtime hours saved × hourly value).** | Reclaimed pool from high holders fuels swap speed. |
"""
                }
                render_cio_tables("CIO – Assets per User / Owner", cio_4a)

        else:
            _fail_info(df, "Owner", owner_syns)
            _fail_info(df, "Asset ID", asset_id_syns)

    # --------------------------------------------------------
    # 4b. Assets per Department
    # --------------------------------------------------------
    with st.expander("📌 Assets per Department"):
        col_dept = _resolve(df, dept_syns)
        col_asset = _resolve(df, asset_id_syns)

        if col_dept and col_asset:
            dept_ct = df.groupby(col_dept)[col_asset].nunique().reset_index(name="asset_count")
            dept_ct = dept_ct.sort_values("asset_count", ascending=False)
            if dept_ct.empty:
                st.info("No rows available after grouping departments.")
            else:
                fig = px.bar(
                    dept_ct, x=col_dept, y="asset_count", text="asset_count",
                    title="Assets by Department",
                    labels={col_dept: "Department", "asset_count": "Assets"}
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                top = dept_ct.iloc[0]
                low = dept_ct.iloc[-1]
                total = int(dept_ct["asset_count"].sum())
                avg  = float(dept_ct["asset_count"].mean())

                st.markdown("### Analysis – Departmental Allocation")
                st.write(f"""
**What this graph is:** A bar chart showing **unique asset holdings by department**.  
**X-axis:** Department.  
**Y-axis:** Number of uniquely assigned assets.

**What it shows in your data:**  
- Peak department: **{top[col_dept]}** with **{_fmt_int(top['asset_count'])} assets**.  
- Lowest department: **{low[col_dept]}** with **{_fmt_int(low['asset_count'])} assets**.  
- **Total across departments:** {_fmt_int(total)}. **Average per department:** {_fmt_float(avg)}.

**Overall:** High concentration suggests **role intensity** or **imbalance**; an even spread hints at **standardized provisioning**.

**How to read it operationally:**  
- **Peaks:** Validate true demand and reclaim spare devices.  
- **Plateaus:** Use as baseline for quarterly forecasting.  
- **Downswings:** Check onboarding/approval bottlenecks.

**Why this matters:** Skew without governance becomes **budget debt**—maintenance spikes, uneven SLA risk, perception gaps.
""")

                evidence_4b = f"Top dept **{top[col_dept]} = {_fmt_int(top['asset_count'])}**; lowest **{low[col_dept]} = {_fmt_int(low['asset_count'])}**; avg/department **{_fmt_float(avg)}**."

                # === Expanded CIO tables (Explanation & Benefits elaborated) ===
                cio_4b = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Rebalance inter-department** | **Phase 1 – Detect:** Use the department bars to spot surplus versus shortage and overlay request backlog and project timing to confirm where needs are real. <br><br> **Phase 2 – Transfer:** Move spares from **{top[col_dept]}** to under equipped groups using serial validation and receipt confirmation so inventory remains auditable. <br><br> **Phase 3 – Track:** Measure post transfer utilization and the number of new purchases deferred by department to prove impact. | - Avoids new purchases because spare devices are consumed first. <br><br> - Reduces storage and idle depreciation because inventory sits where demand exists. <br><br> - Improves utilization which directly lowers urgent spend. <br><br> - Decreases inter team friction because requests are fulfilled faster. | **Savings = (Transfers × Unit price).** | Peak **{top[col_dept]} = {_fmt_int(top['asset_count'])}** vs low **{low[col_dept]} = {_fmt_int(low['asset_count'])}**. |
| **Bundle quarterly requests** | **Phase 1 – Forecast:** Use the average of **{_fmt_float(avg)}** per department and historical peaks to size quarterly orders by line. <br><br> **Phase 2 – Pool:** Batch departmental buys to unlock tiered discounts and commit delivery windows with suppliers. <br><br> **Phase 3 – Validate:** Compare actual consumption to the forecast each quarter and tune assumptions to reduce variance. | - Achieves better pricing because suppliers reward consolidated volumes. <br><br> - Delivers predictable arrivals because schedules are agreed up front. <br><br> - Reduces ad hoc orders which takes pressure off finance and logistics. <br><br> - Stabilizes working capital because spend follows a clear cadence. | **Savings = (Discount % × Batched units).** | Department bars provide forecast baselines. |
| **Decommission fringe stock** | **Phase 1 – Identify:** Flag long idle devices and models with low demand or high support cost that persist in specific departments. <br><br> **Phase 2 – Retire/Sell:** Follow policy to resell, harvest parts or eco dispose and record serials for traceability. <br><br> **Phase 3 – Replace:** Where needed, replace outliers with standardized models to simplify support. | - Frees space and recovers cash or reusable parts for service. <br><br> - Trims storage and maintenance cost because aging stock is removed. <br><br> - Simplifies the toolchain and training footprint for engineers. <br><br> - Reduces incident variance because the portfolio becomes simpler. | **Net = (Proceeds − Prep/handling cost).** | Tail of small bars points to low value stock. |
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Dept asset audits** | **Phase 1 – Review:** Validate allocations against headcount and job roles to catch ghosts and misassigned devices. <br><br> **Phase 2 – Fix:** Correct owners, retire ghost records and align accessories to the right people. <br><br> **Phase 3 – KPI:** Track accuracy percentage and update latency to keep data fresh. | - Produces cleaner data which accelerates provisioning and reduces escalations. <br><br> - Stabilizes onboarding and offboarding because records are current. <br><br> - Improves ticket routing because owner and device context is correct. <br><br> - Reduces time wasted reconciling spreadsheets. | **Time saved = (Audit hours avoided × rate).** | Spread across departments shows audit scope. |
| **Capacity aligned SLAs** | **Phase 1 – Tier:** Classify departments by criticality and demand variability so service levels are realistic. <br><br> **Phase 2 – Calibrate:** Define response and loaner SLAs per tier and site to match capacity to need. <br><br> **Phase 3 – Monitor:** Use breach heatmaps to focus improvements where risk concentrates. | - Delivers predictable service for critical functions because promises match capacity. <br><br> - Optimizes staffing because coverage follows demand patterns. <br><br> - Shortens mean time to restore because hotspots receive priority. <br><br> - Builds credibility because targets are met more consistently. | **Benefit = (Breach reduction × penalty).** | Peak departments drive SLA exposure. |
| **Standardized request bundles** | **Phase 1 – Templates:** Define department and role kits with default approvals and prepopulated specs. <br><br> **Phase 2 – Approvals:** Auto approve baseline kits and route only exceptions to managers to shorten cycle time. <br><br> **Phase 3 – Measure:** Track cycle time and first week incident rate to improve kits. | - Speeds onboarding because users receive standard configurations quickly. <br><br> - Reduces back and forth between requesters and approvers. <br><br> - Lowers early life incidents because standard images are tested. <br><br> - Simplifies support because kits are predictable. | **Time saved = (ΔCycle time × requests).** | Bars show dominant department demand profiles. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Fairness dashboard** | **Phase 1 – Publish:** Provide visible allocation statistics and the rationale so stakeholders understand distribution choices. <br><br> **Phase 2 – Context:** Add role requirements and project phases so spikes and dips have clear explanations. <br><br> **Phase 3 – Feedback:** Review the dashboard with business leaders and capture adjustments. | - Increases trust because decisions are transparent and repeatable. <br><br> - Reduces complaints because context is visible to everyone. <br><br> - Aligns expectations which reduces escalations about perceived bias. <br><br> - Improves collaboration because trade offs are explicit. | **Value = (Complaints avoided × cost/case).** | Visual spread communicates the fairness story. |
| **Loaner pools at big depts** | **Phase 1 – Stage:** Maintain loaners at **{top[col_dept]}** and similar hubs where demand is concentrated. <br><br> **Phase 2 – Automate:** Provide quick approvals for time critical roles with pre booked courier slots. <br><br> **Phase 3 – Track:** Monitor turnaround and reuse rates to size the pool accurately. | - Reduces downtime for heavy demand departments because swaps happen fast. <br><br> - Smooths peak handling because capacity is pre positioned. <br><br> - Increases user confidence during crunch periods because support feels present. <br><br> - Improves device reuse which stretches budgets. | **Benefit = (Downtime hours saved × hourly value).** | Peak department is ideal for hosting loaners. |
| **Proactive comms on shortages** | **Phase 1 – Notify:** Publish ETAs when demand exceeds supply so teams can plan around delays. <br><br> **Phase 2 – Alternatives:** Offer swaps, loaners or reassignments to keep work moving while awaiting stock. <br><br> **Phase 3 – Review:** Track backlog burn down and communicate progress weekly. | - Creates predictability which reduces frustration and follow up emails. <br><br> - Lowers escalation volume because risks are communicated early. <br><br> - Maintains stakeholder trust during shortfalls because options are provided. <br><br> - Improves delivery planning because dependencies are visible. | **Value = (Follow-ups avoided × cost/call).** | Bars highlight where shortages will occur. |
"""
                }
                render_cio_tables("CIO – Assets per Department", cio_4b)

        else:
            _fail_info(df, "Department", dept_syns)
            _fail_info(df, "Asset ID", asset_id_syns)

    # --------------------------------------------------------
    # 4c. Assignment History / JML Movements
    # --------------------------------------------------------
    with st.expander("📌 Assignment History / JML Movements"):
        MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]

        col_jml = _resolve(df, jml_status_syns)
        col_jml_date = _resolve(df, jml_date_syns)

        if col_jml and col_jml_date:
            df[col_jml_date] = pd.to_datetime(df[col_jml_date], errors="coerce")

            jml_ct = df.groupby(col_jml).size().reset_index(name="count")
            fig = px.pie(
                jml_ct,
                names=col_jml,
                values="count",
                title="Joiner / Mover / Leaver Distribution",
                color_discrete_sequence=MES_BLUE
            )
            st.plotly_chart(fig, use_container_width=True)

            total = int(jml_ct["count"].sum())
            peak = jml_ct.iloc[jml_ct["count"].idxmax()]
            smallest = jml_ct.iloc[jml_ct["count"].idxmin()] if len(jml_ct) else None
            peak_pct = (float(peak["count"]) / total * 100.0) if total else 0.0
            small_txt = (
                f"Largest slice: {peak[col_jml]} with {_fmt_int(peak['count'])} ({peak_pct:.1f}%).\n"
                f"Smallest slice: {smallest[col_jml]} with {_fmt_int(smallest['count'])}."
                if smallest is not None
                else f"Largest slice: {peak[col_jml]} with {_fmt_int(peak['count'])} ({peak_pct:.1f}%)."
            )

            st.markdown("#### Analysis – JML Share (Pie)")
            st.write(
                "What this graph is: A pie chart showing the distribution of JML statuses (Joiner, Mover, Leaver).\n"
                f"X-axis: Not applicable (categorical slices: {col_jml}).\n"
                "Y-axis: Share of events by status (count-based).\n"
                "What it shows in your data:\n"
                f"{small_txt}\n"
                f"Total JML transactions: {_fmt_int(total)}.\n"
                "Overall, an outsized Leaver or Joiner slice signals surge-driven workload for returns or onboarding."
            )
            st.write(
                "How to read it operationally:\n"
                "Capacity plan team tasks to the dominant slice (onboarding vs. offboarding).\n"
                "Use mover proportion to recapture duplicates and right-size assignments.\n"
                "Track month-on-month shifts in the mix for early heads-up."
            )
            st.write(
                "Why this matters: Getting the mix right reduces day-1 delays, minimizes lost assets, and stabilizes fulfillment SLAs."
            )

            trend = (
                df.dropna(subset=[col_jml_date])
                .groupby(df[col_jml_date].dt.to_period("M"))
                .size()
                .reset_index(name="count")
            )
            trend["month"] = trend[col_jml_date].astype(str)

            fig2 = px.line(
                trend,
                x="month",
                y="count",
                title="JML Activity Over Time",
                markers=True
            )
            fig2.update_traces(line=dict(color=MES_BLUE[0]), marker=dict(color=MES_BLUE[0]))
            st.plotly_chart(fig2, use_container_width=True)

            if not trend.empty:
                peak_row = trend.iloc[trend["count"].idxmax()]
                low_row = trend.iloc[trend["count"].idxmin()]
                avg_month = float(trend["count"].mean())
                largest_txt = f"Largest month: {peak_row['month']} with {_fmt_int(peak_row['count'])} JML events."
                smallest_txt2 = f"Smallest month: {low_row['month']} with {_fmt_int(low_row['count'])}."
            else:
                largest_txt = "Largest month: —"
                smallest_txt2 = "Smallest month: —"
                avg_month = 0.0

            st.markdown("#### Analysis – JML Throughput (Line)")
            st.write(
                "What this graph is: A line chart showing monthly JML activity volume.\n"
                "X-axis: Calendar month.\n"
                "Y-axis: Count of JML events per month.\n"
                "What it shows in your data:\n"
                f"{largest_txt}\n"
                f"{smallest_txt2}\n"
                f"Averages over the period: {avg_month:.1f} JML/month.\n"
                "Overall, spikes indicate hiring waves or offboarding cycles; flat periods imply stable staffing."
            )
            st.write(
                "How to read it operationally:\n"
                "Peaks = surge windows: pre-stage kits, courier slots, and imaging capacity.\n"
                "Lead–lag of HR plans vs. JML spikes reveals forecast accuracy.\n"
                "Faster recovery after spikes = healthier end-to-end flow."
            )
            st.write(
                "Why this matters: Aligning capacity to JML cadence prevents day-1 failures, protects SLA, and reduces backlog."
            )

            st.markdown("### Analysis – JML Movements")
            st.write(f"""
**What this graph is:** A **pie chart** for **JML status share** and a **line chart** for **monthly JML volume**.  
**Pie:** Share by `{col_jml}`.  
**Line:** **X-axis:** Calendar month; **Y-axis:** JML events.

**What it shows in your data:**  
- **Total JML transactions:** {_fmt_int(total)}.  
- Dominant status: **{peak[col_jml]}** with **{_fmt_int(peak['count'])}** events{f"; smallest status: {smallest[col_jml]} ({_fmt_int(smallest['count'])})" if smallest is not None else ""}.  
- {largest_txt} {smallest_txt2} Average per month: {avg_month:.1f}.

**Overall:** Peaks in the line indicate **hiring waves or offboarding cycles**; plateaus suggest **stable staffing**.

**How to read it operationally:**  
- **Peaks:** Prepare imaging, courier returns, and pool sizing.  
- **Plateaus:** Lock in lead times and steady staffing.  
- **Downswings:** Use buffer to clear returns & reconcile registry.

**Why this matters:** JML without tight control leads to **loss and delay debt**—missing devices, slow day-1, and SLA hits.
""")

            evidence_4c = (
                f"JML dominant status **{peak[col_jml]} = {_fmt_int(peak['count'])}**; "
                f"total={_fmt_int(total)}; {largest_txt}"
            )

            cio_4c = {
                "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Automate leaver collection** | **Phase 1 – Trigger:** When the HRIS flags a leaver, automatically initiate return tasks with the expected device list, a printable pickup label and step by step guidance for the user so the process starts without manual emails. <br><br> **Phase 2 – Logistics:** Book the courier, capture doorstep pickup events and verify serials on receipt with photos, routing exceptions such as missing items to finance or security for resolution. <br><br> **Phase 3 – Scan-in:** Perform serial checks and functional grading, then publish the device into the ready pool with visibility for service desk scheduling. | - Lowers write offs because devices are consistently collected and validated. <br><br> - Accelerates redeployment to teams that need equipment which avoids new purchases. <br><br> - Reduces manual coordination effort across HR and IT because tasks are automated. <br><br> - Improves compliance posture because there is a complete chain of custody. | **Savings = (Leaver count in peak month × Unit price)** → peak month **{peak_row['month'] if not trend.empty else '—'}** × unit_cost. | {evidence_4c} |
| **Day-1 readiness packs** | **Phase 1 – Pre-stage:** Build device kits sized to forecasted joiners with imaged hardware and pre packed accessories so dispatch is plug and play. <br><br> **Phase 2 – Confirm:** Validate addresses and handover slots to avoid failed deliveries and rework. <br><br> **Phase 3 – KPI:** Track ready on start percentage and dead on arrival rate and use the metrics to iterate the kit. | - Cuts setup delays for new hires because equipment works out of the box. <br><br> - Lifts time to productive for managers and teams because waiting is minimized. <br><br> - Reduces urgent day one tickets because common issues are removed in advance. <br><br> - Enhances brand perception for IT because the experience feels professional. | **Benefit = (Setup hours saved per joiner × Joiner volume in peak month).** | {largest_txt} |
| **Policy for movers** | **Phase 1 – Checklist:** When roles change, reconcile devices, licenses and data access against the new job requirements so excess is visible. <br><br> **Phase 2 – Returns:** Schedule pickup for redundant gear and accessories with a simple acknowledgment flow. <br><br> **Phase 3 – Reassign:** Right size the hardware to the new role and close the loop in inventory so records stay accurate. | - Recovers duplicates that drive hidden cost and clutter. <br><br> - Reduces shadow stock because devices return to the shared pool. <br><br> - Improves performance fit for the employee which reduces future tickets. <br><br> - Stabilizes license counts because entitlements match real users. | **Savings = (Duplicates recovered × Unit price).** | Pie shows mover proportion within total {_fmt_int(total)}. |
""",
                "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **JML Kanban** | **Phase 1 – Visualize:** Map the flow from intake to ready and then to issued or returned with explicit work in progress limits so teams avoid overload. <br><br> **Phase 2 – Flow control:** Match technician capacity to forecasted spikes and reroute work across sites during surge weeks to balance queues. <br><br> **Phase 3 – Retro:** Run retrospectives to reduce cycle time variance and fix failure modes such as missed courier bookings or imaging errors. | - Produces faster throughput because bottlenecks are visible and managed. <br><br> - Reduces blockers because work in progress is controlled. <br><br> - Keeps delivery predictable even during hiring or offboarding waves. <br><br> - Improves cross team coordination because everyone sees the same board. | **Throughput gain = (ΔCycle time × JML count in peak month).** | {largest_txt} |
| **SLA clocks for J/M/L** | **Phase 1 – Define:** Set response and fulfillment timers by status and criticality so expectations are explicit. <br><br> **Phase 2 – Monitor:** Trigger breach alerts with root cause tagging such as stock, courier or approvals so fixes target the right constraints. <br><br> **Phase 3 – Improve:** Address systematic bottlenecks and reset timers when performance stabilizes. | - Lowers breach rates because risk is surfaced early and acted on. <br><br> - Stabilizes service because timers match real capacity. <br><br> - Reduces escalations around reorganizations and recruitment drives. <br><br> - Drives continuous improvement because data informs change. | **Benefit = (Breach reduction × penalty exposure).** | Line cadence identifies high risk windows. |
| **Return verification** | **Phase 1 – Proof:** Capture photo and serial at pickup and at receipt to end disputes about condition or ownership. <br><br> **Phase 2 – Exceptions:** Auto chase overdue returns and provide manager visibility so actions occur. <br><br> **Phase 3 – Stock:** Grade, sanitize and publish ready devices back to the pool with a timestamp. | - Makes inventory cleaner because records match reality. <br><br> - Speeds redeployment which shrinks time devices spend idle. <br><br> - Simplifies audits for finance and security because evidence is built in. <br><br> - Reduces repeat follow ups because status is transparent. | **Time saved = (Manual reconciliation hours × rate).** | {smallest_txt2} |
""",
                "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Proactive comms** | **Phase 1 – Notify:** Share JML dates, ETAs and steps with users in plain language so expectations are aligned. <br><br> **Phase 2 – Track:** Provide self service milestone tracking for imaging, courier and receipt so users can check progress. <br><br> **Phase 3 – Feedback:** Capture CSAT and comments and feed them into process improvements. | - Reduces status chases because users already know what is happening. <br><br> - Creates clearer expectations which reduces anxiety during transitions. <br><br> - Improves perceived reliability of IT because updates are timely. <br><br> - Increases engagement because users see their feedback change the process. | **Value = (Follow-ups avoided × cost/call).** | {largest_txt} |
| **Loaner guarantees** | **Phase 1 – Pool:** Size loaner inventory for joiner surges and stage kits at hubs to minimize shipping time. <br><br> **Phase 2 – SLA:** Publish guaranteed issue and collect windows so users know the service promise. <br><br> **Phase 3 – Reuse:** Swap the original device back into the pool once setup completes to keep the pool healthy. | - Reduces downtime and stress on day one because a working device is guaranteed. <br><br> - Maintains consistent service during stock tight periods because a buffer exists. <br><br> - Protects delivery schedules for critical teams because coverage is prioritized. <br><br> - Improves overall satisfaction because surprises are removed. | **Benefit = (Downtime hours saved × users in peak).** | {largest_txt} |
| **Transparent dashboards** | **Phase 1 – Publish:** Show JML volumes, mix and backlog with simple visuals so stakeholders see the load. <br><br> **Phase 2 – Flags:** Highlight risks and actions per month so leaders understand where help is needed. <br><br> **Phase 3 – Reviews:** Run a weekly cadence with HR and operations to align plans. | - Increases trust through visibility because data replaces guesses. <br><br> - Reduces escalations because progress and blockers are tracked openly. <br><br> - Creates shared ownership of outcomes across HR and IT. <br><br> - Improves planning accuracy because everyone works from the same numbers. | **Value = (Escalations avoided × handling cost).** | {evidence_4c} |
"""
            }
            render_cio_tables("CIO – JML Movements", cio_4c)

        else:
            _fail_info(df, "JML Status", jml_status_syns)
            _fail_info(df, "JML Date", jml_date_syns)

    # --------------------------------------------------------
    # 4d. Asset Status by Region / Location
    # --------------------------------------------------------
    with st.expander("📌 Asset Status by Region / Location"):
        col_region = _resolve(df, region_syns)
        col_status = _resolve(df, status_syns)

        if col_region and col_status:
            region_ct = (
                df.groupby([col_region, col_status])
                  .size()
                  .reset_index(name="count")
            )
            if region_ct.empty:
                st.info("No rows available to chart after grouping.")
            else:
                fig = px.bar(
                    region_ct, x=col_region, y="count", color=col_status,
                    title="Asset Status by Region", barmode="group",
                    labels={col_region: "Region", col_status: "Asset Status", "count": "Assets"}
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                top_r = region_ct.iloc[region_ct["count"].idxmax()]
                total = int(region_ct["count"].sum())
                avg   = float(region_ct["count"].mean())

                st.markdown("### Analysis – Regional Status Mix")
                st.write(f"""
**What this graph is:** A grouped bar chart showing **asset counts by Region**, split by **Asset Status**.  
**X-axis:** Region.  
**Y-axis:** Asset count.  
**Color:** Status (e.g., In Use, Idle, Retired).

**What it shows in your data:**  
- Highest combination: **{top_r[col_region]} × {top_r[col_status]}** with **{_fmt_int(top_r['count'])}** assets.  
- **Total combinations shown:** {_fmt_int(total)}. **Average per bar:** {_fmt_float(avg)}.

**Overall:** Taller clusters indicate **inventory hubs**; gaps between statuses reveal **utilization imbalances** across regions.

**How to read it operationally:**  
- **Peaks:** Stage spares & maintenance capability at high-density hubs.  
- **Plateaus:** Calibrate regional ETAs and SLAs.  
- **Downswings:** Serve through pooled dispatch instead of local stock.

**Why this matters:** Misplaced stock becomes **logistics debt**—slower turnaround, higher freight, avoidable downtime.
""")

                evidence_4d = f"Peak combo **{top_r[col_region]} × {top_r[col_status]} = {_fmt_int(top_r['count'])}**; avg/bar **{_fmt_float(avg)}**."

                cio_4d = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Rebalance regional stock** | **Phase 1 – Detect:** Use the grouped bars to find surplus hubs and under served regions and overlay incident and work order volume to validate where supply is misaligned with demand. <br><br> **Phase 2 – Transfer:** Plan bulk moves with route optimization and full chain of custody logging so movement cost is minimized and accountability is maintained. <br><br> **Phase 3 – Review:** Measure post move utilization and the number of new buys deferred by region to confirm savings. | - Defers or avoids purchases because surplus stock is consumed where it is needed. <br><br> - Reduces storage and idle depreciation because assets are held closer to users. <br><br> - Cuts avoidable freight from shipping single units back and forth because pooling is smarter. <br><br> - Improves financial predictability because regional buffers are right sized. | **Savings = (Transfers × Unit price) − (Move cost).** | {evidence_4d} |
| **Batch logistics windows** | **Phase 1 – Schedule:** Establish fixed weekly or bi weekly lanes to high volume hubs so shipping becomes predictable. <br><br> **Phase 2 – Consolidate:** Pick and pack in waves to reduce per unit shipping and handling cost. <br><br> **Phase 3 – Score:** Track cost per move and SLA adherence by lane to optimize frequency. | - Lowers per shipment rates because carriers price predictable lanes better. <br><br> - Reduces surcharges from urgent one off shipments because fewer ad hoc runs are needed. <br><br> - Improves planning for local teams because arrivals are scheduled. <br><br> - Simplifies reconciliation for finance because bills align to lane schedules. | **Savings = (Ad hoc premium avoided × shipments).** | Recurrent high bars identify lane targets. |
| **Local liquidation of excess** | **Phase 1 – Identify:** Find long idle units at hubs with high storage costs and low forecasted demand. <br><br> **Phase 2 – Dispose/Sell:** Use policy compliant resale, parts harvest or eco disposal with full serial capture. <br><br> **Phase 3 – Replace:** Where needed, standardize with current models to simplify the fleet. | - Frees space and recovers value that can be reinvested. <br><br> - Trims storage and maintenance cost because obsolete stock is removed. <br><br> - Simplifies the spares and training footprint for operations. <br><br> - Reduces incident risk from aging devices that underperform. | **Net = (Sale proceeds − handling).** | Peak sites indicate liquidation candidates. |
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Regional repair hubs** | **Phase 1 – Pick:** Choose the densest regions as service hubs using the bars to maximize coverage. <br><br> **Phase 2 – Equip:** Stage spares, tools and imaging stations sized to local incident levels. <br><br> **Phase 3 – SLA:** Set and track turnaround KPIs by hub with clear ownership. | - Delivers faster repairs and lower mean time to restore because work is local. <br><br> - Reduces cross region shipments which shortens queues and saves cost. <br><br> - Increases first time fix rates because technicians specialize by platform. <br><br> - Raises resilience during surges because hubs can borrow capacity from neighbors. | **Benefit = (ΔMTTR × incidents × hourly rate).** | Peak region and status combination drives hub ROI. |
| **Buffer stock policy** | **Phase 1 – Set:** Define minimum and maximum levels per region linked to demand variability and seasonality. <br><br> **Phase 2 – Replenish:** Use Kanban or reorder points to trigger refills automatically at the right time. <br><br> **Phase 3 – Review:** Recalibrate buffers quarterly to reflect project phases and growth. | - Creates predictable service levels because stock outs are rare. <br><br> - Reduces emergency shipments because regions carry appropriate buffers. <br><br> - Smooths dispatch to sites with frequent incidents because spares are on hand. <br><br> - Improves planning because buffer performance is measured. | **Benefit = (Stock-out reduction × downtime cost).** | Distribution shows where buffers matter most. |
| **Site-tiered SLAs** | **Phase 1 – Tier:** Define different SLAs for hub and spoke regions so promises reflect distance and capacity. <br><br> **Phase 2 – ETA:** Communicate realistic delivery and repair windows per region to set expectations accurately. <br><br> **Phase 3 – Monitor:** Use breach heatmaps to focus improvements in the toughest locations. | - Improves planning and reduces surprises for business users because service windows are honest. <br><br> - Concentrates improvement work where it yields the biggest impact. <br><br> - Increases adherence because targets are achievable. <br><br> - Reduces escalation risk because stakeholders understand the constraints. | **Benefit = (Breach reduction × penalty).** | Variance by region justifies SLA tiers. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Regional ETA transparency** | **Phase 1 – Publish:** Provide region specific ETAs and queue position so users can plan their work. <br><br> **Phase 2 – Update:** Show live stock and courier status so changes are visible without contacting support. <br><br> **Phase 3 – Notify:** Send proactive delay alerts when lanes slip so expectations are reset. | - Cuts “any update” calls because information is self served. <br><br> - Improves trust and planning because timelines are clear. <br><br> - Reduces escalations on delays because surprises are minimized. <br><br> - Raises satisfaction because communication is consistent. | **Value = (Follow-ups avoided × cost/call).** | Clear regional patterns support communications. |
| **On-site swap clinics** | **Phase 1 – Events:** Run periodic swap and repair days at hubs to clear backlogs and fix chronic issues. <br><br> **Phase 2 – Playbooks:** Execute standard fixes and quick swaps with parts and images staged. <br><br> **Phase 3 – Measure:** Track same day resolution percentage and reuse the best playbooks. | - Dramatically reduces downtime for local users because issues are resolved on the spot. <br><br> - Increases the visible presence of IT which boosts confidence. <br><br> - Compresses long standing queues which improves morale. <br><br> - Creates repeatable patterns that can be scaled to other hubs. | **Benefit = (Downtime hours saved × users).** | Hubs identified by the tallest bars. |
| **Queue visibility by region** | **Phase 1 – Dashboard:** Show requests, ETAs and capacity per region with VIP and critical flags. <br><br> **Phase 2 – Prioritize:** Route high impact tickets into fast lanes while protecting fairness across sites. <br><br> **Phase 3 – Review:** Level load weekly by moving stock or work between regions. | - Improves perceived fairness and control because users see where they stand. <br><br> - Reduces surprise delays because constraints are visible early. <br><br> - Aligns demand and capacity because decisions are data driven. <br><br> - Increases satisfaction among VIP users because priority is explicit. | **Value = (Escalations avoided × cost).** | Region and status split explains wait dynamics. |
"""
                }
                render_cio_tables("CIO – Asset Status by Region", cio_4d)

        else:
            _fail_info(df, "Region", region_syns)
            _fail_info(df, "Asset Status", status_syns)
