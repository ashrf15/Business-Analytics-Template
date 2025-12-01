# utils_asset_inventory/recommendation_assets/asset_lifecycle.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# Mesiniaga visual theme (blue + white)
# ============================================================
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

# ============================================================
# Helper for CIO tables
# ============================================================
def render_cio_tables(title, cio):
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(cio.get("cost", "Data not available."), unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(cio.get("performance", "Data not available."), unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(cio.get("satisfaction", "Data not available."), unsafe_allow_html=True)

# Small formatters
def _fmt_int(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"

def _fmt_float(x, d=1):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.0"

# ============================================================
# Target 5 – Asset Lifecycle Management
# ============================================================
def asset_lifecycle(df_filtered: pd.DataFrame):
    df = df_filtered.copy()

    # --------------------------------------------------------
    # 5a. Asset Procurement Timeline
    # --------------------------------------------------------
    with st.expander("📌 Asset Procurement Timeline"):
        date_col = None
        for c in ["purchase_date", "procurement_date", "warranty_start", "jml_date"]:
            if c in df.columns:
                date_col = c
                break

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            by_month = (
                df[df[date_col].notna()]
                .groupby(df[date_col].dt.to_period("M"))
                .size()
                .reset_index(name="procured")
            )
            by_month["month"] = by_month[date_col].astype(str)

            fig = px.bar(
                by_month, x="month", y="procured", text="procured",
                title=f"Assets Procured by Month ({date_col})",
                labels={"month": "Month", "procured": "Assets"},
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            if not by_month.empty:
                total = int(by_month["procured"].sum())
                peak = by_month.loc[by_month["procured"].idxmax()]
                low = by_month.loc[by_month["procured"].idxmin()]
                avg = by_month["procured"].mean()
                variance = by_month["procured"].var(ddof=0) if len(by_month) > 1 else 0

                st.markdown("### Analysis – Procurement Trend")
                st.write(f"""
**What this graph is:** A monthly bar chart showing **asset procurement volume** from **`{date_col}`**.  
- **X-axis:** Calendar month.  
- **Y-axis:** Number of assets procured.

**What it shows in your data:** Procurement peaked in **{peak['month']}** with **{int(peak['procured'])}** assets and was lowest in **{low['month']}** with **{int(low['procured'])}**. **Total recorded procurements:** **{_fmt_int(total)}**. **Average:** **{_fmt_float(avg)}/month**.

**Overall:** Taller bars indicate **ordering cycles or budget releases**; dips suggest **freeze/stock-out** periods.

**How to read it operationally:**  
1) **Peaks:** Align deliveries, staging capacity, and tagging teams ahead of peak months.  
2) **Plateaus:** Standardize replenishment cadence with vendors.  
3) **Downswings:** Validate if delays are vendor-, approval-, or demand-driven.  
4) **Mix:** Cross-check against **department demand** to prioritize allocations.

**Why this matters:** Procurement rhythm drives **cash flow, deployment speed, and user readiness**. Getting the timing right reduces **rush costs** and **deployment bottlenecks**.
""")
                evidence_5a = f"Peak {peak['month']} = {int(peak['procured'])}; Low {low['month']} = {int(low['procured'])}; Total = {_fmt_int(total)}; Avg = {_fmt_float(avg)}; Var = {_fmt_float(variance,2)}."
            else:
                st.info("No valid procurement dates found.")
                evidence_5a = "Empty procurement data."
        else:
            st.warning("No procurement date column found.")
            evidence_5a = "Date column missing."

        cio_5a = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Evenly distribute procurement** | **Phase 1 – Measure:** Quantify the month-to-month volatility using the variance value (**Var={_fmt_float(variance,2)}**) and set a realistic baseline around the historical mean of **{_fmt_float(avg)}** units per month so teams have a clear capacity target. <br><br>**Phase 2 – Plan:** Break up large peak-month requisitions into smaller pre-approved mini batches that land earlier or later while still meeting project milestones so imaging and logistics are not overwhelmed. <br><br>**Phase 3 – Enforce:** Introduce quarterly order caps with a documented exception path so last-minute spikes are challenged and only approved when they demonstrably protect business outcomes. | - Cash outflows are smoothed, enabling finance to forecast and allocate budgets more accurately across quarters. <br><br> - Premium freight and overtime are reduced because workload is spread across weeks instead of compressed into surge days. <br><br> - Staging and imaging workloads are stabilized, which lowers rework and defect rates during busy periods. <br><br> - Emergency purchases become less likely because inventory arrives on a cadence aligned to operational capacity. | **Rush-fee avoided = (Rush premium × units shifted from peak {int(peak['procured'])})**. | {evidence_5a} |
| **Centralize vendor negotiation** | **Phase 1 – Aggregate:** Consolidate fragmented orders into committed blocks clustered around **{peak['month']}** so the combined volume qualifies for tiered pricing and delivery guarantees. <br><br>**Phase 2 – Bid:** Run a structured competitive event with standard specifications and fixed delivery windows so vendors quote apples-to-apples including service and warranty addenda. <br><br>**Phase 3 – Review:** Track the realized discount against block size each quarter so you can recalibrate the sourcing strategy with evidence. | - Pricing leverage increases, directly reducing unit cost at a constant specification level. <br><br> - Lead times become predictable, preventing downstream schedule slippage during high-demand periods. <br><br> - Warranty and support terms improve as vendors compete for consolidated spend. <br><br> - Transactional overhead falls because one larger PO replaces many small approvals and receipts. | **Savings = (Discount% × {_fmt_int(total)} units)**. | Peak and total volume justify bulk terms. |
| **Optimize stock forecasting** | **Phase 1 – Model:** Build a simple seasonal or time-series model on the monthly procurement series and include known drivers like project calendars and JML peaks so reorder points reflect reality. <br><br>**Phase 2 – Calibrate:** Monitor forecast error each month and tune safety stock so the model remains reliable as demand patterns evolve. <br><br>**Phase 3 – Act:** Adjust order triggers and vendor buffers ahead of high-risk months so supply is positioned before the surge hits. | - Overstock is reduced, cutting carrying cost and obsolescence risk for fast-moving device categories. <br><br> - Stock-outs are avoided, preventing productivity loss and emergency escalations during new-hire waves. <br><br> - Utilization of staging areas improves because arrivals match processing capacity. <br><br> - Approval cycles accelerate as budget holders see quantified forecasts tied to outcomes. | **Error cost = (|Forecast−Actual| × holding/stock-out cost)**. | Variability (**Var={_fmt_float(variance,2)}**) indicates forecast need. |
| **Co-term procurement & refresh** | **Phase 1 – Align:** Map procurement windows to planned refresh waves so devices flow in a steady pipeline instead of arriving in a single cliff month. <br><br>**Phase 2 – Phase:** Spread deliveries to avoid overloading imaging and QA capacity so quality stays consistent under load. <br><br>**Phase 3 – Monitor:** Compare planned throughput to actual burn weekly and rebalance caps so the schedule remains achievable. | - Overtime and courier premiums decline because work is sequenced rather than spiking unpredictably. <br><br> - Installation quality stays steady, reducing early-life incident rates after rollout. <br><br> - Fire drills are prevented, protecting BAU and user perception. <br><br> - Cash flow becomes more predictable as purchasing aligns with controlled execution. | **Overtime avoided = (Peak variance × hours/unit × rate)**. | Peak {peak['month']} bar drives workload spikes. |
| **Pre-approved mini-batches** | **Phase 1 – Frame:** Establish standing PO bands such as 10, 25, and 50 units with pre-agreed pricing so procurement can be executed quickly when thresholds are hit. <br><br>**Phase 2 – Trigger:** Auto-release a batch when backlog or JML forecast crosses the threshold so supply keeps pace with real demand. <br><br>**Phase 3 – Audit:** Review quarterly uptake and realized savings so the bands and triggers remain effective. | - Response to demand swings accelerates because small batches can be released without waiting for new approvals. <br><br> - Emergency buys decrease because capacity is topped up proactively based on rules. <br><br> - Issuance lead time stays predictable, improving stakeholder confidence during onboarding waves. <br><br> - Governance is preserved because exceptions are tracked while routine replenishment is streamlined. | **Emergency premium avoided = (Urgent units avoided × premium)**. | Low month {low['month']} suggests buffer opportunities. |
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Automate procurement scheduling** | **Phase 1 – Calendarize:** Publish monthly order cut-offs that align with finance cycles and vendor manufacturing slots so internal teams know exactly when to submit requests. <br><br>**Phase 2 – Integrate:** Connect to vendor portals or APIs for acknowledgements, advance shipping notices, and delivery slot reservations so updates flow automatically. <br><br>**Phase 3 – Track:** Visualize the SLA from purchase order to goods receipt with alerts so slippage is caught before it impacts deployments. | - End-to-end lead time shortens as manual handoffs and status chasing are eliminated. <br><br> - On-time-to-need performance rises, protecting downstream imaging and issuance schedules. <br><br> - Email noise decreases because system updates replace ad hoc follow-ups. <br><br> - A single source of truth is established for operations and finance. | **Lead-time gain = (Baseline − Actual) × {_fmt_int(total)} units**. | Monthly bars form the cadence baseline. |
| **Track procurement SLAs** | **Phase 1 – Define:** Set explicit SLAs for acknowledge, ship, and deliver events per vendor so expectations are contractual. <br><br>**Phase 2 – Alert:** Notify owners before and at breach time with reason codes so delays are investigated immediately. <br><br>**Phase 3 – Improve:** Use quarterly business reviews to fix systemic causes like paperwork, packaging, or lane capacity. | - Schedule slips decline because teams act on early warnings rather than discovering problems on delivery day. <br><br> - Predictability improves for downstream deployments, lowering rework and rescheduling. <br><br> - Vendor accountability strengthens because performance is measured and reviewed. <br><br> - Process bottlenecks surface and can be engineered out. | **Breach cost avoided = (Breaches reduced × penalty)**. | Peaks correlate with higher breach risk. |
| **Integrate with asset registry** | **Phase 1 – Auto-ingest:** Capture serials, tags, and warranty metadata into the registry at goods receipt so data is right at source. <br><br>**Phase 2 – Validate:** Route mismatches or missing fields into an exceptions queue so corrections happen before deployment. <br><br>**Phase 3 – Publish:** Expose ready-to-deploy counts by site so field teams can schedule with confidence. | - Provisioning speeds up because devices appear as ready without manual data entry. <br><br> - “Unknown device” hunts are eliminated because records are complete and consistent. <br><br> - Auditability increases since the chain from PO to asset record is clean. <br><br> - Analytics quality improves across all downstream dashboards. | **Time saved = (Minutes saved per asset × {_fmt_int(total)})**. | Volume proves ROI of automation. |
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Communicate procurement status** | **Phase 1 – Dashboard:** Publish a simple ETA dashboard by month and vendor so stakeholders know when stock is due. <br><br>**Phase 2 – Notify:** Send proactive alerts when shipments slip or split so plans can be adjusted without friction. <br><br>**Phase 3 – Resolve:** Provide a clear escalation path with revised ETAs so confidence remains high during peak **{peak['month']}**. | - Follow-up calls and chats decline because status is visible in one place. <br><br> - Expectations are set accurately, reducing frustration when dates move. <br><br> - Trust in IT delivery increases because updates arrive before stakeholders need to ask. <br><br> - Project schedules stay on track as impacted teams can replan promptly. | **Value = (Calls avoided × handling time)** tied to peak {peak['month']}. | {evidence_5a} |
| **Publish annual refresh plan** | **Phase 1 – Draft:** Translate the device strategy into monthly targets and clearly show the rationale so teams understand the why and the when. <br><br>**Phase 2 – Align:** Validate the plan with department heads and finance windows so execution fits real constraints. <br><br>**Phase 3 – Track:** Show progress against plan with corrective actions so stakeholders see issues being managed. | - Business users gain predictability, reducing last-minute swaps and escalations. <br><br> - Perceived fairness improves because criteria and schedule are transparent. <br><br> - Change adoption becomes smoother as people can prepare for downtime and data migration. <br><br> - Adoption rises because the plan feels orderly and justified. | **Value = (Escalations avoided × cost/case)**. | Bars define the planning envelope. |
| **Department allocation previews** | **Phase 1 – Pre-assign:** Publish tentative allocations before stock lands so managers know what to expect. <br><br>**Phase 2 – Confirm:** Adjust the last mile based on the latest demand signals so the fit is right. <br><br>**Phase 3 – Post:** Provide visibility of shipments and receipts by site so ownership is clear. | - Onboarding delays are reduced because equipment is earmarked ahead of need. <br><br> - Disputes over priority are minimized because allocations are visible and rule-based. <br><br> - Day-one readiness improves for new joiners and projects. <br><br> - Rework declines because the right departments receive the right SKUs. | **Value = (Onboarding delay hours avoided × rate)**. | Procurement peaks map to allocation windows. |
"""
        }
        render_cio_tables("CIO – Procurement Timeline", cio_5a)

    # --------------------------------------------------------
    # 5b. Asset Age Distribution
    # --------------------------------------------------------
    with st.expander("📌 Asset Age Distribution"):
        if "warranty_start" in df.columns:
            df["warranty_start"] = pd.to_datetime(df["warranty_start"], errors="coerce")
            today = pd.Timestamp.today().normalize()
            df["asset_age_years"] = ((today - df["warranty_start"]).dt.days / 365.25).round(1)
            age = df["asset_age_years"].dropna()
            total_age = int(age.shape[0])
            gt5 = int((age > 5).sum())
            between3_5 = int(((age > 3) & (age <= 5)).sum())

            fig = px.histogram(
                age, x="asset_age_years", nbins=20,
                title="Distribution of Asset Age (Years)",
                labels={"asset_age_years": "Age (years)"},
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not age.empty:
                avg_age = round(age.mean(), 1)
                oldest = round(age.max(), 1)
                youngest = round(age.min(), 1)
                st.markdown("### Analysis – Asset Aging")
                st.write(f"""
**What this graph is:** A histogram showing **asset age distribution** derived from **`warranty_start`**.  
- **X-axis:** Asset age (years).  
- **Y-axis:** Number of assets in each age bucket.

**What it shows in your data:** **Average age = {avg_age} years**, **youngest = {youngest} years**, **oldest = {oldest} years**. **Observed total with age data = {_fmt_int(total_age)}**.

**Overall:** A concentration toward higher ages signals **refresh pressure**; a younger skew indicates **recent investments** and **lower failure risk**.

**How to read it operationally:**  
1) **Peaks:** Identify the modal age band and plan targeted refresh or warranty extensions.  
2) **Plateaus:** Maintain balanced inflow of new assets to prevent future bulges.  
3) **Downswings:** Validate if retirements or reallocations caused troughs.  
4) **Mix:** Overlay **failure/repair rates** to prioritize high-risk age bands.

**Why this matters:** Aging fleets drive **higher repair cost, downtime, and user friction**. Managing age mix protects **budget and uptime**.
""")
                evidence_5b = f"Avg={avg_age}y; Min={youngest}y; Max={oldest}y; Count={_fmt_int(total_age)}; >5y={_fmt_int(gt5)}; 3–5y={_fmt_int(between3_5)}."
            else:
                st.info("No valid age data found.")
                evidence_5b = "Empty age data."
        else:
            st.warning("No 'warranty_start' column found.")
            evidence_5b = "Column missing."

        cio_5b = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Replace aged assets (>5y)** | **Phase 1 – Identify:** Use the histogram to isolate **{_fmt_int(gt5)}** devices older than five years and verify their operational status and role so the list represents real risk. <br><br>**Phase 2 – Prioritize:** Rank candidates by role criticality, performance symptoms, and failure history so the highest impact replacements go first. <br><br>**Phase 3 – Execute:** Roll replacements in manageable waves with change windows and back-out plans so the business experiences minimal disruption. | - Emergency repair spending declines because high-risk devices are proactively retired before failure. <br><br> - User downtime decreases as performance and stability improve with newer hardware. <br><br> - Sporadic spending converts into a predictable CapEx curve that is easier to approve and manage. <br><br> - Ticket noise from chronic offenders drops, freeing technician time for higher-value work. | **CapEx shift = ({_fmt_int(gt5)} × unit price) − (expected repair cost >5y)**. | {evidence_5b} |
| **Extend warranty for 3–5y band** | **Phase 1 – Target:** Focus on **{_fmt_int(between3_5)}** mid-life devices that show increasing risk but are not yet slated for refresh so you can bridge them safely. <br><br>**Phase 2 – Compare:** Quantify the extension fee against projected failure likelihood and average repair cost so decisions are data-driven. <br><br>**Phase 3 – Contract:** Negotiate bundled extensions that include clear response SLAs so coverage is predictable during busy seasons. | - Replacement can be deferred where insuring is cheaper than buying new, conserving capital for critical needs. <br><br> - Operational risk during project periods is cushioned because vendor coverage absorbs failures. <br><br> - Support budgets stabilize as costs become predictable and scheduled. <br><br> - Device usefulness is extended without compromising reliability for users. | **Decision metric = (Ext cost × {_fmt_int(between3_5)}) vs (Expected failures × repair cost)**. | {evidence_5b} |
| **Harvest parts from retirees** | **Phase 1 – Select:** Identify oldest or failed units that are uneconomical to repair and tag them as donors with clear criteria so salvage is consistent. <br><br>**Phase 2 – Recover:** Standardize RAM, SSD, and PSU harvesting with serial linkage so provenance is auditable. <br><br>**Phase 3 – Track:** Measure parts yield and redeployment speed so the value of the program is visible and optimizable. | - Spares procurement costs drop because common components are sourced internally. <br><br> - Repair lead time shortens because parts are available on hand. <br><br> - E-waste and disposal spend are reduced, supporting ESG objectives. <br><br> - Resilience increases during supply constraints because critical spares are locally stocked. | **Recovered value = (Reusable parts × avg part value)**. | Oldest cohort ({oldest}y) supports harvesting. |
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Preventive PM for 3–5y** | **Phase 1 – Calendar:** Build a preventive maintenance calendar focused on thermals, storage health, and batteries so wear items are addressed early. <br><br>**Phase 2 – Scope:** Define checklists and component refresh thresholds so technicians know exactly what to do. <br><br>**Phase 3 – Review:** Track failures per one thousand units and MTBF to tune the cadence with evidence. | - Late-life incident rates decline because emerging faults are caught before escalation. <br><br> - MTBF becomes more predictable, aiding staffing and spares planning. <br><br> - Engineer workload is smoothed across months, reducing burnout and overtime. <br><br> - Device stability improves, reducing user friction. | **Benefit = (Incidents avoided in 3–5y × resolution hrs)**. | {evidence_5b} |
| **Age-gated deployment policy** | **Phase 1 – Caps:** Define which roles can receive devices above or below age thresholds so performance is aligned to work demands. <br><br>**Phase 2 – Enforce:** Route exceptions through an approval workflow that factors role urgency and risk so deviations are intentional. <br><br>**Phase 3 – Audit:** Review the policy quarterly with real ticket data so thresholds stay relevant. | - Power users receive newer hardware, maximizing productivity where impact is highest. <br><br> - Preventable performance tickets are curbed by avoiding mis-matched devices. <br><br> - Rework and swaps decrease because assignments follow clear rules. <br><br> - Governance becomes transparent and easier to support. | **Benefit = (Productivity hours gained × users)**. | Average age {avg_age}y guides thresholds. |
| **Age-aware spares sizing** | **Phase 1 – Model:** Estimate failure probability by age band using historical incidents so sizing is evidence based. <br><br>**Phase 2 – Size:** Set site-level loaner and spare targets that match the expected curve so service remains responsive. <br><br>**Phase 3 – Adjust:** Rebalance after refresh waves and seasonality so coverage stays right-sized. | - Swap lead time is reduced, directly cutting MTTR. <br><br> - SLA protection improves during higher-risk months for older fleets. <br><br> - User continuity improves because loaners are available when needed. <br><br> - Excess carrying cost is avoided by tuning stock to risk. | **Benefit = (ΔMTTR × incidents × rate)**. | Oldest={oldest}y implies higher spares need. |
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Communicate refresh roadmap** | **Phase 1 – Publish:** Share the age-based schedule and the selection logic so people understand timing and priorities. <br><br>**Phase 2 – Notify:** Provide lead time and offer options for scheduling so users can plan around work commitments. <br><br>**Phase 3 – Track:** Measure satisfaction before and after swaps so messaging and logistics improve each wave. | - Expectations are set, reducing uncertainty and escalations. <br><br> - Surprise outages are prevented because timing is known in advance. <br><br> - Perceived fairness increases as decisions are criteria-driven and transparent. <br><br> - Trust in IT strengthens because feedback is visibly acted upon. | **Value = (Complaints avoided × cost/case)**. | {evidence_5b} |
| **Priority upgrades for heavy users** | **Phase 1 – Tag:** Identify high throughput roles and frequent travelers so priorities reflect business impact. <br><br>**Phase 2 – Match:** Allocate newer devices with performance headroom to these users so productivity lifts are immediate. <br><br>**Phase 3 – Validate:** Track ticket rate and simple productivity proxies to confirm the benefit. | - Perceived performance improves for users who feel device limits most strongly. <br><br> - Repeat tickets decline as bottlenecks are removed. <br><br> - Retention of key talent is supported through reliable tools. <br><br> - Visible wins build support for the broader refresh program. | **Value = (Hours saved × hourly value)**. | Younger cohorts better fit intense roles. |
| **Loaners during swap windows** | **Phase 1 – Pool:** Maintain a ready loaner pool sized to refresh cadence so users always have a fallback. <br><br>**Phase 2 – SLA:** Offer same-day or next-day swap targets so downtime is minimal. <br><br>**Phase 3 – Reclaim:** Close the loop quickly and return devices to the pool so availability remains high. | - Business disruption during swaps is minimized, keeping projects on schedule. <br><br> - User productivity is maintained while primary devices are serviced. <br><br> - Confidence in IT increases because the process feels organized and considerate. <br><br> - Stock health is preserved by ensuring fast turnaround of loaners. | **Benefit = (Downtime hours avoided × users)**. | Age peaks define swap timing. |
"""
        }
        render_cio_tables("CIO – Asset Age Distribution", cio_5b)

    # --------------------------------------------------------
    # 5c. Asset Retirement & Disposal
    # --------------------------------------------------------
    with st.expander("📌 Asset Retirement & Disposal"):
        if "disposal" in df.columns and df["disposal"].notna().any():
            disp_ct = df["disposal"].value_counts().reset_index()
            disp_ct.columns = ["disposal_status", "count"]
            total_disp = int(disp_ct["count"].sum())
            peak = disp_ct.loc[disp_ct["count"].idxmax()]
            p_share = (peak["count"] / max(total_disp, 1)) * 100

            fig = px.pie(
                disp_ct, names="disposal_status", values="count",
                title="Disposal Status Breakdown",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Analysis – Disposal Trend")
            st.write(f"""
**What this graph is:** A pie chart showing **distribution of asset disposal statuses** from **`disposal`**.  
- **Slices:** Disposal status categories.  
- **Values:** Share of assets under each status.

**What it shows in your data:** Dominant status **{peak['disposal_status']}** with **{int(peak['count'])}** assets (**{_fmt_float(p_share)}%**). **Total disposals recorded = {_fmt_int(total_disp)}**.

**Overall:** Larger slices highlight **where the process is concentrated** (e.g., pending vs completed) and potential **throughput constraints**.

**How to read it operationally:**  
1) **Peaks:** Unblock approvals/logistics for the largest status to accelerate flow.  
2) **Plateaus:** Standardize documentation and vendor pickups to keep pace.  
3) **Downswings:** Validate if records are missing or if disposal slowed.  
4) **Mix:** Track **data-wipe certifications** per status for compliance.

**Why this matters:** Disposal done right reduces **storage cost, compliance risk, and data exposure**—and recovers value where possible.
""")
            evidence_5c = f"Peak status {peak['disposal_status']} = {int(peak['count'])} ({_fmt_float(p_share)}%); Total = {_fmt_int(total_disp)}."
        else:
            st.info("No disposal data available.")
            evidence_5c = "Missing disposal records."

        cio_5c = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Recycle components** | **Phase 1 – Assess:** Evaluate each retired unit with a quick diagnostic checklist to identify reusable components so salvage decisions are consistent. <br><br>**Phase 2 – Harvest:** Standardize the removal of RAM, SSD, and PSU parts and record serial linkage so traceability is preserved. <br><br>**Phase 3 – Track:** Measure parts yield percentage and reuse rate across tickets so the financial impact is visible. | - Cash spend on spares decreases because common components are sourced from retirees. <br><br> - Repair turnaround shortens because parts are immediately available from on-hand stock. <br><br> - Disposal costs are offset with recovered value, improving overall economics. <br><br> - E-waste handling fees trend down as more material is reused. | **Recovered value = (Parts yield × avg part value)**. | {evidence_5c} |
| **Bulk disposal contracts** | **Phase 1 – Bundle:** Accumulate disposal lots by site and month to reach recycler price tiers so unit economics improve. <br><br>**Phase 2 – Tender:** Source certified recyclers who commit to certificates of assurance and fixed pickup windows so compliance and logistics are reliable. <br><br>**Phase 3 – Settle:** Negotiate scrap credits and transport terms so value recovery is maximized. | - Per-device logistics and administration cost decreases because pickups are consolidated. <br><br> - Storage space is freed faster, reducing carrying cost and operational clutter. <br><br> - Clearance activities become more predictable, helping sites plan. <br><br> - Scrap value improves because larger lots command stronger pricing. | **Credit = (Scrap rate × batch size)**. | Dominant status highlights batching potential. |
| **Certify data destruction** | **Phase 1 – Verify:** Enforce wipe logs and chain-of-custody per unit so evidence exists for every device. <br><br>**Phase 2 – Certify:** Store tamper-proof certificates of assurance by serial so auditors can retrieve documents quickly. <br><br>**Phase 3 – Store:** Maintain a searchable archive so compliance teams can respond instantly to audits. | - Legal and regulatory exposure is minimized because proof of data destruction is readily available. <br><br> - Reputational risk is reduced by demonstrating disciplined handling of sensitive hardware. <br><br> - Audit responses are faster, lowering the cost of compliance activities. <br><br> - Process variability declines as standardized steps are followed across sites. | **Risk avoided = (Penalty × incidents avoided)**. | Status mix demands provable data wipes. |
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Track disposal milestones** | **Phase 1 – Stages:** Map the lifecycle from request to pickup to wipe to certificate so each stage has clear entry and exit criteria. <br><br>**Phase 2 – SLA:** Set target days for each stage and monitor drift so bottlenecks are visible. <br><br>**Phase 3 – Alert:** Escalate stagnant items to owners and managers automatically so queues move. | - Total cycle time to clearance shortens, freeing space and reducing distraction. <br><br> - Warehouses remain organized, improving safety and operational flow. <br><br> - Throughput stays steady so BAU operations are not interrupted by ad hoc disposal. <br><br> - Accountability increases because stage owners are clearly identified. | **Days saved = (Baseline days − Actual) × {_fmt_int(total_disp)}**. | Peak status shows where time accumulates. |
| **Automate disposal workflow** | **Phase 1 – Triggers:** Initiate disposal when assets meet age or condition thresholds or when refresh completes so owners do not forget. <br><br>**Phase 2 – Tasks:** Use pre-filled forms and pickup labels to eliminate manual re-entry so errors fall. <br><br>**Phase 3 – Evidence:** Auto-attach certificates of assurance to asset records so documentation is complete by default. | - Administrative effort decreases, allowing teams to focus on value-add work. <br><br> - Compliance improves because required artifacts are created and stored automatically. <br><br> - Closure accelerates, improving visibility for finance and security. <br><br> - Variance decreases as the workflow is standardized across sites. | **Processing time delta × {_fmt_int(total_disp)}**. | Concentration of cases makes automation pay off. |
| **Exception queue for pending** | **Phase 1 – Detect:** Identify long-pending buckets and responsible owners so attention is directed to the true blockers. <br><br>**Phase 2 – Escalate:** Notify approvers and logistics with SLA clocks so actions are prioritized. <br><br>**Phase 3 – Clear:** Run a weekly review to burn down the queue so stock and space are recovered. | - Bottlenecks are unblocked, converting stranded assets into cash or cleared space. <br><br> - Storage costs fall as dwell time shortens. <br><br> - Stakeholder confidence improves because visible queues are actively managed. <br><br> - Repeat delays are prevented as root causes are addressed through governance. | **Storage cost avoided = (Avg days reduced × items × rate)**. | Large slice pinpoints the queue to clear. |
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Report eco-disposal metrics** | **Phase 1 – Publish:** Share reuse and recycle percentages by month and site so progress is visible. <br><br>**Phase 2 – Compare:** Benchmark against internal targets and external peers so goals feel meaningful. <br><br>**Phase 3 – Improve:** Set realistic quarterly ramps and communicate plans so stakeholders see momentum. | - ESG progress is demonstrated to employees and customers, supporting brand reputation. <br><br> - Sustainability reporting becomes simpler because metrics are curated. <br><br> - Site participation is motivated by transparent performance comparisons. <br><br> - Partner interest in circular programs increases as data shows commitment. | **CSR value proxy = (ESG index delta × weight)**. | Evidence slice supports ESG storytelling. |
| **Communicate safe data wipe** | **Phase 1 – Notify:** Inform device owners and managers that certificates are available so concerns are proactively addressed. <br><br>**Phase 2 – Portal:** Provide certificate downloads by serial so self-service is easy. <br><br>**Phase 3 – Archive:** Maintain long-term access for audits so retrieval is effortless. | - Anxiety about data exposure is reduced because proof is accessible on demand. <br><br> - Inbound queries to the service desk decline as users self-serve documentation. <br><br> - Operational maturity is demonstrated, improving trust with regulated teams. <br><br> - Due diligence for customers or compliance reviews is accelerated. | **Inquiries avoided × handling time**. | Certificates tied to disposal statuses. |
| **Pickup scheduling transparency** | **Phase 1 – Calendar:** Publish recycler pickup slots so sites can plan staffing and access. <br><br>**Phase 2 – Confirmations:** Send emails or SMS with site instructions so coordination is smooth. <br><br>**Phase 3 – Live:** Provide delay alerts with new ETAs so disruptions are managed in real time. | - Failed pickups decrease, saving time for both recycler and site teams. <br><br> - Local admin experience improves because expectations are clear. <br><br> - Throughput increases as pickup days are fully utilized. <br><br> - Reschedule overhead declines because changes are communicated early. | **Value = (Reschedules avoided × cost/event)**. | Status mix reveals where communications help most. |
"""
        }
        render_cio_tables("CIO – Asset Retirement & Disposal", cio_5c)

    # --------------------------------------------------------
    # 5d. Replacement or Upgrade Plans
    # --------------------------------------------------------
    with st.expander("📌 Replacement or Upgrade Planning"):
        col = None
        for c in ["warranty_end", "latest_to_dispose", "return_date"]:
            if c in df.columns:
                col = c
                break
        if col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            tmp = df[df[col].notna()].copy()
            tmp["month"] = tmp[col].dt.to_period("M").astype(str)
            timeline = tmp.groupby("month").size().reset_index(name="count")

            fig = px.line(
                timeline, x="month", y="count", markers=True,
                title=f"Upcoming Replacements by {col}",
                labels={"month": "Month", "count": "Assets"},
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not timeline.empty:
                peak = timeline.loc[timeline["count"].idxmax()]
                low = timeline.loc[timeline["count"].idxmin()]
                total = int(timeline["count"].sum())
                avg = float(timeline["count"].mean())

                st.markdown("### Analysis – Upcoming Replacements")
                st.write(f"""
**What this graph is:** A monthly line chart of **scheduled replacements/returns** derived from **`{col}`**.  
- **X-axis:** Calendar month.  
- **Y-axis:** Number of assets scheduled.

**What it shows in your data:** **Peak = {peak['month']}** with **{int(peak['count'])}** assets; **Lowest = {low['month']}** with **{int(low['count'])}**. **Total scheduled = {_fmt_int(total)}**, **Average = {_fmt_float(avg)} / month**.

**Overall:** Clustering in certain months signals **maintenance load, lease/refresh deadlines**, and the need for **staging capacity**.

**How to read it operationally:**  
1) **Peaks:** Pre-stage inventory, imaging, and bookings; coordinate vendor lead times.  
2) **Plateaus:** Keep a continuous pipeline to avoid last-minute rush.  
3) **Downswings:** Use quieter months for pilots and complex rollouts.  
4) **Mix:** Map against **department needs and budget windows**.

**Why this matters:** Well-timed replacements reduce **downtime, disruption, and overtime costs**, while keeping users **productive and satisfied**.
""")
                evidence_5d = f"Peak {peak['month']} = {int(peak['count'])}; Low {low['month']} = {int(low['count'])}; Total = {_fmt_int(total)}; Avg = {_fmt_float(avg)}."
            else:
                st.info("No replacement data found.")
                evidence_5d = "Empty replacement data."
        else:
            st.warning("No relevant replacement date column found.")
            evidence_5d = "Missing date columns."

        cio_5d = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Schedule phased replacements** | **Phase 1 – Plan:** Distribute the replacement workload to hover around the monthly mean of **{_fmt_float(avg)}** units while honoring lease and warranty deadlines so field capacity is not exceeded. <br><br>**Phase 2 – Gate:** Set weekly and site caps with scheduling rules so technicians and logistics can execute predictably. <br><br>**Phase 3 – Review:** Compare planned burn-down to actual each week and adjust caps so backlogs do not accumulate. | - Overtime and after-hours courier fees fall because work happens inside standard operating windows. <br><br> - Staging rooms avoid clogging, preserving space and reducing handling. <br><br> - Incidental travel is cut as visits are planned in efficient waves. <br><br> - Cost per swap remains consistent because throughput is steady. | **Overtime avoided = (Peak {int(peak['count'])} − Avg {_fmt_float(avg)}) × hours/unit × rate**. | {evidence_5d} |
| **Utilize vendor trade-ins** | **Phase 1 – Bundle:** Consolidate returns in peak windows to qualify for stronger credit tables and document acceptable cosmetic grades so disputes are minimized. <br><br>**Phase 2 – Negotiate:** Lock value bands and turnaround times with vendors so credits land when new POs are raised. <br><br>**Phase 3 – Apply:** Offset new purchase orders with credit notes so net CapEx is reduced. | - Net purchase cost decreases because trade-in credits directly offset new devices. <br><br> - Disposal accelerates as returns move through a single integrated flow. <br><br> - Environmental impact is reduced by channeling devices through certified partners. <br><br> - Lifecycle cadence is maintained without adding separate logistics overhead. | **Net CapEx = (New cost − Trade-in credit × units)**. | Peak month defines trade-in batch size. |
| **Align warranty expiries** | **Phase 1 – Co-term:** Group renewals into manageable cohorts so workload and risk are balanced. <br><br>**Phase 2 – Offset:** Move non-critical units earlier or later so a single cliff month like **{peak['month']}** is avoided. <br><br>**Phase 3 – Monitor:** Track renewal conversion and failure rates after decisions so the strategy remains sound. | - Risk concentration is avoided, preventing overwhelm of vendors and internal teams. <br><br> - Negotiating leverage improves because cohorts create predictable volume. <br><br> - Renewal OPEX is smoothed, keeping monthly budgets stable. <br><br> - Coverage continuity is ensured for critical devices during busy periods. | **Renewal cost delta = (Staggered vs Cliff month {peak['month']})**. | Peak evidences expiry clustering. |
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Pre-stage replacement units** | **Phase 1 – Image:** Maintain golden images per model and pre-install role packages so devices are ready to deploy upon arrival. <br><br>**Phase 2 – QA:** Run smoke tests for battery, thermals, and ports so early defects are filtered out. <br><br>**Phase 3 – Stage:** Organize ready racks by site and week so field teams can execute high-throughput swap days. | - Swap time per user shrinks, directly cutting downtime. <br><br> - Early-life defects in production drop because QA intercepts faulty units. <br><br> - Daily throughput becomes predictable, improving calendar planning with sites. <br><br> - First-time-right rates increase, lowering rework. | **Downtime hours saved = (Δswap time × {_fmt_int(total)})**. | {evidence_5d} |
| **Track replacement cycle time** | **Phase 1 – Measure:** Capture timestamps from request to ready to completed so you can see where time accumulates. <br><br>**Phase 2 – SLA:** Set monthly targets with reason codes so misses are diagnosable. <br><br>**Phase 3 – Improve:** Fix stock, courier, or approval bottlenecks based on evidence so the cycle compresses. | - Device delivery speeds up, keeping users productive. <br><br> - Queues of open tickets are reduced, simplifying portfolio management. <br><br> - Capacity needs surface early, supporting resource planning. <br><br> - Continuous improvement is institutionalized as data becomes visible. | **Avg cycle time (pre vs post)**. | Timeline reveals load windows to optimize. |
| **Blackout change windows** | **Phase 1 – Avoid:** Define periods where replacements should not occur such as finance closing or product launch windows so risk is controlled. <br><br>**Phase 2 – Coordinate:** Align with other change events so collisions do not occur across teams. <br><br>**Phase 3 – Enforce:** Route exceptions through CAB approvals so deviations are deliberate and logged. | - Failed changes and rollbacks are reduced because risky windows are protected. <br><br> - Critical business moments are shielded from disruption, preserving trust. <br><br> - After-hours firefighting declines as work is scheduled away from hotspots. <br><br> - Stakeholder confidence in rollout discipline improves. | **Benefit = (Incidents avoided × hours × rate)**. | Peak month needs stricter controls. |
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Notify users early** | **Phase 1 – Schedule:** Offer user-friendly time windows and on-site clinics so people can choose slots that fit their work. <br><br>**Phase 2 – Remind:** Send T-7 and T-1 reminders with clear preparation steps like backup and availability so appointments stick. <br><br>**Phase 3 – Confirm:** Run a short post-swap survey and a fix-forward loop so any issues are closed quickly. | - Disruption and missed appointments are minimized because expectations are set and reinforced. <br><br> - Perceived reliability improves as the process feels structured and predictable. <br><br> - Rework is reduced because users arrive prepared, speeding handovers. <br><br> - Satisfaction scores rise as feedback leads to rapid adjustments. | **Missed hours avoided = (Users × avg hrs disrupted)**. | {evidence_5d} |
| **Choice bundles** | **Phase 1 – Offer:** Provide role-based device bundles within approved SKUs such as battery-focused or portability-focused so users choose what best fits their job. <br><br>**Phase 2 – Approve:** Auto-approve selections inside guardrails and log exceptions so governance is maintained. <br><br>**Phase 3 – Track:** Measure satisfaction uplift and early-life incident rates so options are refined. | - User-device fit improves, reducing complaints and shadow purchases. <br><br> - Returns and configuration rework decrease because choices are pre-vetted. <br><br> - Perceived autonomy increases, boosting acceptance of the program. <br><br> - Standards remain intact while meaningful flexibility is offered. | **Value = (CSAT uplift × weight)**. | Timeline shapes when to offer bundles. |
| **On-site swap clinics in peak** | **Phase 1 – Staff:** Stand up mobile desks at locations with high scheduled counts so throughput is concentrated. <br><br>**Phase 2 – Script:** Provide common fixes and accessories on hand so most issues are resolved same day. <br><br>**Phase 3 – Measure:** Track same-day completion rate and rework so the clinic model continuously improves. | - Turnaround accelerates dramatically as many users are served in one coordinated event. <br><br> - Logistics hops are reduced, saving time and cost. <br><br> - Face-to-face support increases trust and satisfaction. <br><br> - Bulk insights are captured, improving future waves. | **Benefit = (Same-day rate increase × tickets)**. | Peak {peak['month']} ideal for clinics. |
"""
        }
        render_cio_tables("CIO – Replacement & Upgrade Plans", cio_5d)
