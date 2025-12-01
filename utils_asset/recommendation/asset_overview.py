# utils_asset_inventory/recommendation_assets/asset_overview.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================
# Shared CIO table renderer
# ============================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# ============================================
# Target 1: Asset Overview
# ============================================
def asset_overview(df_filtered):

    # ---------------------- 1a ----------------------
    with st.expander("📌 Total Number of IT Assets"):
        if "asset_id" in df_filtered.columns:
            total_assets = df_filtered["asset_id"].nunique()
        else:
            total_assets = len(df_filtered)

        st.metric("Total Assets", f"{total_assets:,}")

        # --- Graph 1: Growth Trend (based on warranty_start or update_on)
        date_col = None
        for c in ["warranty_start", "update_on"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                date_col = c
                break

        if date_col:
            df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors="coerce")
            trend = (
                df_filtered.groupby(df_filtered[date_col].dt.to_period("M"))
                .size()
                .reset_index(name="asset_count")
            )
            trend["month"] = trend[date_col].astype(str)

            fig = px.area(
                trend,
                x="month",
                y="asset_count",
                title=f"Asset Intake Over Time ({date_col})",
                labels={"month": "Month", "asset_count": "Assets Added"},
            )
            st.plotly_chart(fig, use_container_width=True)

            if not trend.empty:
                max_row = trend.loc[trend["asset_count"].idxmax()]
                min_row = trend.loc[trend["asset_count"].idxmin()]
                total_added = trend["asset_count"].sum()
                avg_added = trend["asset_count"].mean()

                st.markdown("### Analysis of Asset Intake Trend")
                st.write(f"""
**What this graph is:** An area chart showing **monthly asset intake** based on `{date_col}`.  
- **X-axis:** Calendar month.  
- **Y-axis:** Number of assets added in that month.

**What it shows in your data:** Intake peaked in **{max_row['month']}** with **{int(max_row['asset_count'])} assets**,  
while the lowest month was **{min_row['month']}** with **{int(min_row['asset_count'])}** assets.  
Average intake is **{avg_added:.1f} assets/month** across **{len(trend)} months** (total added: **{int(total_added)}**).

Overall, a rising envelope indicates **demand or refresh acceleration** (risk of budget/capacity strain),  
while a flat or falling envelope indicates **procurement stabilization**.

**How to read it operationally:**  
1) **Peaks:** Align bulk buys/rollouts and secure volume pricing.  
2) **Plateaus:** Standardize intake cadence; monitor supplier SLAs.  
3) **Downswings:** Validate whether constraints (budget, supply chain) or efficiencies caused the drop.  
4) **Mix:** Pair with utilization and incidents to ensure high-intake months don’t create idle or low-quality stock.

**Why this matters:** Asset intake drives **CapEx and lifecycle workload**. Controlling the curve prevents overspend, idle inventory, and support spikes.
                """)
            else:
                st.info("No data available to plot the intake trend.")
        else:
            st.warning("No suitable date column found for asset trend.")

        evidence = f"Total assets {total_assets:,} – based on {date_col if date_col else 'available records'}."

        # 👉 pull concrete numbers from the plotted trend for formulas/evidence
        if date_col and not trend.empty:
            peak_month_str = str(max_row["month"])
            peak_month_count = int(max_row["asset_count"])
            low_month_str = str(min_row["month"])
            low_month_count = int(min_row["asset_count"])
            months_span = len(trend)
            avg_added_float = float(avg_added)
            total_added_int = int(total_added)
        else:
            # graceful fallbacks if no date column/empty trend
            peak_month_str = "—"
            peak_month_count = 0
            low_month_str = "—"
            low_month_count = 0
            months_span = 0
            avg_added_float = 0.0
            total_added_int = 0

        cio_1a = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|----------------------|----------|------------------|--------------------------------|
| **Optimize purchase timing** | **Phase 1 – Detect Cycles:** Use the intake trend to map high and low months such as peak **{peak_month_str}** and low **{low_month_str}** so procurement can see predictable demand rhythms clearly. <br><br> **Phase 2 – Shift Buys:** Move non urgent procurement into lower activity windows to obtain better supplier flexibility and reduce pressure on receiving and imaging teams. <br><br> **Phase 3 – Review Semi-Annually:** Refit the timing window every six months so purchase plans keep pace with changing headcount and project intake. | - Smooths monthly cash outflow which makes budget execution more predictable for finance. <br><br> - Improves negotiation leverage because orders are bundled into quieter periods where suppliers can commit to better prices. <br><br> - Reduces rush order premiums because fewer purchases are forced into end of month or end of quarter spikes. <br><br> - Aligns deliveries with deployment bandwidth so devices do not queue in stores waiting for setup. | **Variance reduction × Avg cost/asset.** Use avg intake **{avg_added_float:.1f}/month** across **{months_span}** months to size the swing. | Intake peaked at **{peak_month_count}** vs low **{low_month_count}**; the area chart visualizes timing opportunity. |
| **Reallocate idle inventory** | **Phase 1 – Identify:** Compare high intake months such as **{peak_month_str}** to subsequent deployment and utilization logs to locate devices that remain unassigned or underused. <br><br> **Phase 2 – Redeploy:** Move idle stock to backlogged teams using a simple request and approval workflow so assets start generating value. <br><br> **Phase 3 – Track:** Audit post move utilization monthly and close the loop with stakeholders if redeployment targets are not met. | - Defers new purchases because existing assets are reused before buying more units. <br><br> - Raises utilization percentage which increases the return on invested capital for hardware already paid for. <br><br> - Reduces storage and holding costs because fewer boxes sit in the storeroom waiting for deployment. <br><br> - Shortens time to value because users get devices sooner without waiting for the next procurement cycle. | **Idle units × Avg asset value.** Use total added **{total_added_int}** and utilization % deltas to quantify. | Peaks in the intake curve indicate possible stock accumulation windows. |
| **Procurement forecasting** | **Phase 1 – Model:** Fit intake versus drivers such as headcount growth and refresh policy so the forecast reflects real demand rather than guesswork. <br><br> **Phase 2 – Align:** Co plan with HR and project managers to avoid last minute spikes by freezing required volumes earlier in the quarter. <br><br> **Phase 3 – Alert:** Trigger early buy signals when forecasted demand exceeds thresholds so sourcing can secure supply. | - Prevents overbuying because purchases are tied to validated drivers rather than ad hoc requests. <br><br> - Reduces expedited shipping because orders are placed earlier and arrive before deadlines. <br><br> - Stabilizes supplier lead times which reduces stockouts at go live. <br><br> - Improves budget predictability because variance between plan and actual narrows over time. | **Forecast error × Avg procurement value.** Base on monthly avg **{avg_added_float:.1f}** and peak **{peak_month_count}**. | Stable segments vs spikes in the area chart reveal where forecast misses occurred. |
| **Bundle volume contracts** | **Phase 1 – Aggregate:** Pool the quarter’s demand rather than issuing fragmented purchase orders so suppliers can quote aggressive tiers. <br><br> **Phase 2 – Negotiate:** Use the peak month requirement as leverage to secure tiered discounts and improved service levels that cover the entire bundle. <br><br> **Phase 3 – Benchmark:** Reprice quarterly against market references to lock in savings and surface drift early. | - Lowers the unit price because larger committed volumes attract better discounts. <br><br> - Simplifies invoicing which reduces administrative time in finance and procurement. <br><br> - Reduces operational overhead because deliveries and serial capture can be planned in larger predictable waves. <br><br> - Increases supplier accountability because performance is tied to a consolidated agreement with clear penalties. | **(List price − Negotiated price) × Units.** Units informed by total added **{total_added_int}**. | Evidenced by sustained intake across **{months_span}** months, supporting volume tiers. |
| **Balance intake vs deployment capacity** | **Phase 1 – Map Capacity:** Compare monthly intake to deployment throughput so leadership can see where arrivals exceed setup capacity. <br><br> **Phase 2 – Smooth Flow:** Cap intake at the deployable rate plus a buffer and shift excess to the next window to avoid spikes. <br><br> **Phase 3 – Kaizen:** Remove bottlenecks in imaging, delivery, and handover so sustainable throughput rises over time. | - Cuts warehousing cost because fewer pallets are staged waiting for engineers. <br><br> - Reduces dead capital because devices move from invoice to productive use faster. <br><br> - Avoids support spikes from mass drops because users receive devices in waves with adequate hypercare. <br><br> - Improves time to productivity for end users because rollout cadence matches resource capacity. | **(Intake − Deployable rate) × Carrying cost.** Use avg **{avg_added_float:.1f}/month** as baseline. | Any month where intake >> normal average signals risk of buildup. |
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|----------------------|----------|------------------|--------------------------------|
| **Automate intake logging** | **Phase 1 – Auto-capture:** Scan goods received notes and delivery documents to auto create asset records with serial and SKU so no unit is missed at intake. <br><br> **Phase 2 – CMDB Sync:** Enforce mapping to configuration management fields so lineage and ownership are correct from day one. <br><br> **Phase 3 – Validate Weekly:** Reconcile exceptions each week so inaccuracies do not accumulate. | - Delivers faster onboarding because records are created at the dock rather than days later. <br><br> - Reduces missed or duplicate records which improves audit readiness. <br><br> - Creates cleaner data lineage which helps warranty and service requests later in the lifecycle. <br><br> - Accelerates reporting service level agreements because datasets are up to date without manual rework. | **Time saved × Assets/month.** With avg **{avg_added_float:.1f}** new assets monthly. | Smooth sections in the intake trend imply operational readiness for automation. |
| **Load-leveling of deployment** | **Phase 1 – Even Cadence:** Break large drops such as **{peak_month_str}** into weekly waves so engineering workload is balanced. <br><br> **Phase 2 – Staff Rota:** Align engineers and handover resources to the wave plan so each window has enough hands. <br><br> **Phase 3 – Review:** Compare planned versus actual each cycle and correct gaps such as late deliveries or site access issues. | - Prevents engineer overload which reduces configuration mistakes under time pressure. <br><br> - Delivers steadier throughput so queues do not balloon after peak arrivals. <br><br> - Lowers overtime because hours are distributed more evenly across the month. <br><br> - Improves change control adherence because each wave follows a standard checklist. | **Overtime avoided × Hourly rate.** Peak **{peak_month_count}** vs avg **{avg_added_float:.1f}** quantifies stress. | Peak-to-average gap in the area chart shows where to level load. |
| **Supplier feed integration** | **Phase 1 – EDI/API:** Ingest advanced shipment notices and serial ranges directly from vendors so intake is pre registered before delivery. <br><br> **Phase 2 – SKU Normalization:** Map vendor part numbers to internal taxonomies so reporting stays consistent across suppliers. <br><br> **Phase 3 – Monitors:** Alert on mismatches between shipment data and physical scans so discrepancies are fixed immediately. | - Reduces manual keying which lowers error rates in master data. <br><br> - Improves accuracy for warranty start and entitlement which avoids future disputes. <br><br> - Accelerates intake processing because boxes can be booked in faster on arrival. <br><br> - Reduces downstream support issues because assets carry correct attributes from the start. | **Errors avoided × Correction time.** Volume based on **{total_added_int}** new assets. | Consistent intake patterns justify automating upstream signals. |
| **Post-intake QA gates** | **Phase 1 – Spot Checks:** Validate a proportion of units per intake batch to catch defects early before they reach users. <br><br> **Phase 2 – Defect Loop:** Return or repair faulty units before deployment so quality issues do not propagate. <br><br> **Phase 3 – Trend:** Track defect ratio by supplier and model so recurring problems are escalated or removed from the catalog. | - Prevents faulty rollouts which would generate incident spikes after go live. <br><br> - Reduces user disruption because problematic devices are intercepted before assignment. <br><br> - Preserves trust in refresh programs because early experiences are smooth. <br><br> - Lowers total cost of ownership because defective items are addressed under supplier obligations. | **(Incidents avoided × Avg resolution cost).** Size by months with high intake like **{peak_month_str}**. | Spikes followed by support issues often trace to weak QA. |
| **Lifecycle tagging at intake** | **Phase 1 – Tag Policy:** Enforce labels such as owner site and refresh month so every unit carries lifecycle metadata. <br><br> **Phase 2 – Tooling:** Auto populate tags from purchase order and HR data so entry is consistent. <br><br> **Phase 3 – Audit:** Run quarterly drift checks to correct missing or stale tags. | - Improves traceability which speeds redeployment and loss investigations. <br><br> - Enables faster refresh planning because cohorts are clearly identified. <br><br> - Strengthens compliance posture because auditors can follow the chain of custody. <br><br> - Reduces manual hunting for details because key context is present in the record. | **Hours saved in audits × Hourly rate.** Scales with **{total_added_int}**. | Stable intake + clean IDs = faster downstream ops. |
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|----------------------|----------|------------------|--------------------------------|
| **Transparent procurement dashboard** | **Phase 1 – Publish:** Show monthly intake estimated arrival dates and allocations so stakeholders can plan their dependencies. <br><br> **Phase 2 – Filter:** Allow departments to view their pipeline and site breakdowns so communication remains targeted. <br><br> **Phase 3 – Alerts:** Notify owners when dates slip so expectations are reset proactively. | - Reduces status emails because users can self serve the latest intake information. <br><br> - Sets clearer expectations which lowers frustration when schedules change. <br><br> - Makes stakeholders feel in control because they can see when their devices are due. <br><br> - Reduces escalations because surprises are replaced with timely updates. | **Inquiries avoided × Handling time.** Peaks (**{peak_month_str}**) typically drive inquiries. | The visual intake curve contextualizes what’s arriving when. |
| **Feedback loop after deployments** | **Phase 1 – Survey:** Sample users after each deployment wave to capture early issues and satisfaction signals. <br><br> **Phase 2 – Correlate:** Link feedback to intake peaks to spot where compressed schedules harmed quality. <br><br> **Phase 3 – Improve:** Adjust golden images and deployment scripts based on the top themes. | - Targets pain points early which prevents repeat issues across later waves. <br><br> - Raises adoption because devices arrive with settings that match user needs. <br><br> - Reduces day two tickets because common setup problems are removed quickly. <br><br> - Builds credibility because users see that feedback results in visible changes. | **Complaint rate drop × Cost per complaint.** Compare pre/post peak **{peak_month_str}**. | Peaks followed by issues highlight where comms and imagery need tuning. |
| **Early comms on supply delays** | **Phase 1 – SLA with Vendors:** Require reliable estimated arrival dates and publish them so everyone sees the same truth. <br><br> **Phase 2 – Broadcast:** Share revised dates to affected departments as soon as exceptions occur. <br><br> **Phase 3 – Mitigate:** Offer loaners or reassignments for critical roles while waiting for delayed stock. | - Avoids surprise for project teams because changes are communicated before deadlines slip. <br><br> - Protects timelines by providing temporary alternatives that keep work moving. <br><br> - Maintains trust with VIP users because their impact is acknowledged and addressed. <br><br> - Reduces escalation volume because stakeholders feel informed and supported. | **Escalations avoided × Delay duration cost.** Uses months with low intake like **{low_month_str}** as signals. | Intake dips + delay notes explain shortfalls to users. |
| **Role-based hardware previews** | **Phase 1 – Catalog:** Present standard builds mapped to role personas so requesters choose fit for purpose options. <br><br> **Phase 2 – Pilot:** Allow selected champions to test devices ahead of waves and provide structured feedback. <br><br> **Phase 3 – Commit:** Freeze configurations before mass rollout to stabilize quality. | - Improves fit for purpose which reduces returns and swap requests. <br><br> - Produces smoother onboarding because users receive devices aligned to their workloads. <br><br> - Reduces training needs because standard builds behave consistently. <br><br> - Increases stakeholder confidence because decisions are tested before scale. | **Return rate reduction × Asset value.** Benchmarked across **{months_span}** months. | Stable intake phases are ideal for controlled pilots. |
| **Go-live readiness comms** | **Phase 1 – Playbooks:** Send pre deployment checklists so users back up data and prepare accessories before handover. <br><br> **Phase 2 – Day-1 Guides:** Provide one page guides per role so first logins and core tasks are clear. <br><br> **Phase 3 – Office Hours:** Offer short support windows after each wave to resolve teething issues quickly. | - Drives higher first week satisfaction because users start strong without confusion. <br><br> - Deflects trivial tickets because common questions are answered upfront. <br><br> - Speeds productivity ramp because users spend less time waiting for help. <br><br> - Reduces perceived downtime because issues are solved in dedicated slots. | **Tickets deflected × Handling cost.** Anchored to waves sized by **{avg_added_float:.1f}/month**. | Where intake spikes, prepared comms cushion user impact. |
"""
        }
        render_cio_tables("Total Number of IT Assets", cio_1a)


    # ---------------------- 1b ----------------------
    with st.expander("📌 Asset Categories (Type / Brand / OS)"):
        possible_cols = [c for c in ["type", "brand", "os"] if c in df_filtered.columns]
        if possible_cols:
            cat = possible_cols[0]
            cat_df = df_filtered.groupby(cat).size().reset_index(name="count").sort_values("count", ascending=False)
            fig2 = px.bar(cat_df, x=cat, y="count", title=f"Assets by {cat}", text="count")
            fig2.update_traces(textposition="outside")
            st.plotly_chart(fig2, use_container_width=True)

            if not cat_df.empty:
                top_cat = cat_df.iloc[0]
                bottom_cat = cat_df.iloc[-1]
                st.markdown("### Analysis of Asset Category Distribution")
                st.write(f"""
**What this graph is:** A bar chart showing **asset inventory distribution by `{cat}`**.  
- **X-axis:** {cat} categories (e.g., device type, brand, or OS).  
- **Y-axis:** Asset count per category.

**What it shows in your data:** The largest category is **{top_cat[cat]}** with **{int(top_cat['count'])} units**,  
while the smallest is **{bottom_cat[cat]}** with **{int(bottom_cat['count'])}** units.

Overall, a tall–short spread indicates **concentration** (standardization leverage and supplier negotiation power),  
whereas a flatter profile indicates **diversity** (greater support complexity).

**How to read it operationally:**  
1) **Peaks:** Negotiate volume pricing; standardize images and spares.  
2) **Plateaus:** Maintain a healthy mix but monitor support overhead.  
3) **Downswings:** Consider retirement/consolidation for fringe categories.  
4) **Mix:** Cross-reference with incidents and uptime to balance cost vs reliability for each category.

**Why this matters:** Category mix drives **TCO and supportability**. Optimizing it reduces unit cost, speeds resolution, and improves user experience.
                """)
                evidence_cat = f"Top {cat}: {top_cat[cat]} ({int(top_cat['count'])} units); lowest: {bottom_cat[cat]} ({int(bottom_cat['count'])} units)."
            else:
                st.info("No data to display for asset categories.")
                evidence_cat = "Empty category dataset."
        else:
            st.warning("No category column found (Type, Brand, or OS).")
            evidence_cat = "No category evidence."

        # 👉 compute concrete category metrics used in formulas/evidence
        if possible_cols and not cat_df.empty:
            total_in_cat = int(cat_df["count"].sum())
            top_name = str(top_cat[cat])
            top_count = int(top_cat["count"])
            top_share = top_count / total_in_cat if total_in_cat else 0.0
            low_name = str(bottom_cat[cat])
            low_count = int(bottom_cat["count"])
            low_share = low_count / total_in_cat if total_in_cat else 0.0
        else:
            total_in_cat = 0
            top_name = "—"
            top_count = 0
            top_share = 0.0
            low_name = "—"
            low_count = 0
            low_share = 0.0

        cio_1b = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|----------------------|----------|------------------|--------------------------------|
| **Focus on high-volume vendors** | **Phase 1 – Identify Leaders:** Target the top `{cat}` by volume such as **{top_name}** and quantify their footprint so the negotiation baseline is transparent. <br><br> **Phase 2 – Negotiate:** Use share **{top_share:.1%}** to secure volume pricing dedicated spares and bundled support with clear service levels. <br><br> **Phase 3 – Track:** Audit realized discount against list price quarterly and publish results so savings are visible and sustained. | - Lowers the unit price because concentrated demand is exchanged for better commercial terms. <br><br> - Reduces lead time risk because suppliers pre position stock for dominant lines. <br><br> - Simplifies support contracts because entitlements are bundled for the largest cohorts. <br><br> - Improves budgeting accuracy because prices and coverage are locked for a longer period. | **(List − Negotiated) × Units for {top_name}.** Units = **{top_count}** out of **{total_in_cat}**. | Bar shows **{top_name} = {top_count}** units (**{top_share:.1%}** of total). |
| **Retire under-used categories** | **Phase 1 – Tag Tails:** Flag categories with a share below five percent such as **{low_name} {low_share:.1%}** so the long tail is explicit. <br><br> **Phase 2 – Plan Exit:** Replace or decommission fringe items during refresh to reduce variety without disrupting users. <br><br> **Phase 3 – Consolidate:** Move workloads to standard platforms and update procurement catalogs to prevent re introduction. | - Cuts spare parts variety which lowers inventory holding costs and simplifies logistics. <br><br> - Lowers training complexity because engineers and helpdesk focus on fewer models. <br><br> - Reduces the number of vendor portals and licenses that operations must maintain. <br><br> - Makes image management easier which improves quality and reduces incidents. | **Obsolete units × Avg repair/license cost.** Tail example: **{low_name} = {low_count}** units. | Long tail at the right of the bar chart signals consolidation targets. |
| **Bundle renewals per category** | **Phase 1 – Align Dates:** Normalize warranty and maintenance renewal windows by brand or type so co terming becomes possible. <br><br> **Phase 2 – Re-bid Bundles:** Seek multi year discounts for the combined base so per unit renewals get cheaper. <br><br> **Phase 3 – Automate Reminders:** Set automated notices to prevent lapses that would expose devices to uncovered risk. | - Produces smoother renewals because paperwork and approvals are handled in a single window. <br><br> - Reduces administrative overhead because finance processes fewer separate transactions. <br><br> - Improves coverage continuity because entitlements do not lapse unnoticed. <br><br> - Increases supplier accountability because performance is tracked across a consolidated contract. | **Renewal overlap × Avg renewal fee.** Scope proportional to **{total_in_cat}** assets. | Concentration in top categories yields leverage for bundled renewals. |
| **Standardize SKUs within top types** | **Phase 1 – Reduce Models:** Limit to one or two SKUs per top category so imaging accessories and spares can be unified. <br><br> **Phase 2 – Golden Image:** Maintain a single hardened image per SKU with documented update cadence and rollback. <br><br> **Phase 3 – Spares Pool:** Create a shared spares pool to support fast swaps and minimize downtime. | - Lowers stocking cost because fewer distinct parts are required to keep service running. <br><br> - Enables faster swap or repair which reduces user downtime. <br><br> - Shortens mean time to resolve because technicians know a small set of configurations well. <br><br> - Reduces configuration errors because every device follows the same blueprint. | **(Models reduced) × (Setup time saved per model).** Heaviest impact where **{top_name}** dominates. | The tall bar for **{top_name}** shows where SKU standardization pays most. |
| **Refresh-by-exception for reliable brands** | **Phase 1 – Reliability Index:** Rank incidents per 100 assets by brand or type so dependable lines are identified with data. <br><br> **Phase 2 – Stretch:** Extend refresh cycles for high performers where risk is low and user experience remains stable. <br><br> **Phase 3 – Reinvest:** Redirect saved budget to weaker categories that create more incidents or poor experience. | - Defers capital expenditure with minimal operational risk because reliable units stay in service longer. <br><br> - Reduces e waste because fewer devices are retired unnecessarily. <br><br> - Aligns spend with outcomes because money is focused on problem areas first. <br><br> - Improves stakeholder confidence because refresh rules are evidence based. | **(Months deferred × Depreciation/month × Units).** Units from top tiers like **{top_name}**. | If top categories also show low incident rates, they’re candidates to stretch. |
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|----------------------|----------|------------------|--------------------------------|
| **Define performance baselines by `{cat}`** | **Phase 1 – Measure:** Calculate metrics such as mean time between failures and uptime per `{cat}` so performance differences are quantified. <br><br> **Phase 2 – Compare:** Focus upgrades and configuration fixes on the bottom quartile to lift the floor quickly. <br><br> **Phase 3 – Iterate:** Recalibrate quarterly so baselines reflect current hardware and software versions. | - Delivers predictable service levels because weak cohorts receive targeted improvements. <br><br> - Enables targeted upgrades which stretch budgets further than blanket replacements. <br><br> - Reduces surprise failures because risky categories are addressed first. <br><br> - Strengthens service level reporting because baselines are transparent and repeatable. | **Avg uptime delta × Volume.** Larger effect in categories like **{top_name} ({top_count})**. | Spread in counts indicates where baselines will cover most users. |
| **Simplify technical support** | **Phase 1 – Reduce Diversity:** Consolidate rarely used categories such as **{low_name}** to keep the supported matrix small. <br><br> **Phase 2 – Standardize Images:** Maintain one hardened image per top SKU so troubleshooting is consistent. <br><br> **Phase 3 – Preload Configs:** Preload required packages and profiles to cut setup time and avoid misconfigurations. | - Accelerates incident resolution because analysts diagnose a familiar stack. <br><br> - Reduces configuration errors because default builds are stable and tested. <br><br> - Makes patch cycles easier because fewer combinations must be validated. <br><br> - Improves first time fix rates which reduces ticket backlog. | **Support time reduced × Tickets/month.** Category volume = **{total_in_cat}**. | Dominance of **{top_name}** implies large payoff from streamlined support. |
| **Golden build governance** | **Phase 1 – Gate Changes:** Use pull requests and peer review for build updates so regressions are caught early. <br><br> **Phase 2 – Canary:** Roll out to a limited group within the top category and monitor stability and user feedback before wider release. <br><br> **Phase 3 – Promote:** Promote to all users only after defined metrics pass thresholds. | - Reduces regression incidents because risky changes are filtered by review and pilot. <br><br> - Creates consistent performance because every device runs a validated image. <br><br> - Makes rollback straightforward because versions and approvals are tracked. <br><br> - Raises change success rate which protects SLA. | **(Incidents avoided × Avg resolution cost).** Heaviest where **{top_name}** concentration exists. | Category concentration means defects propagate widely if ungated. |
| **Telemetry-driven patching** | **Phase 1 – Collect:** Gather health metrics such as crash rates and boot times per category so issues are observable. <br><br> **Phase 2 – Prioritize:** Patch cohorts with the worst signals first to reduce user pain quickly. <br><br> **Phase 3 – Verify:** Check post patch performance to ensure the intervention delivered improvements. | - Reduces stability tickets because problematic versions are fixed proactively. <br><br> - Improves mean time to restore because guidance is based on real telemetry. <br><br> - Creates evidence based maintenance windows which reduce unnecessary restarts. <br><br> - Builds confidence in IT because users see measurable improvements. | **ΔIncidents × Time saved per incident.** Scale by **{total_in_cat}** assets. | High-volume categories amplify benefits of precise patching. |
| **Capacity right-sizing by role** | **Phase 1 – Map Workloads:** Match device specification to role performance needs based on measured demand. <br><br> **Phase 2 – Swap/Upgrade:** Swap devices or upgrade components for under or over specified users to reach the sweet spot. <br><br> **Phase 3 – Monitor:** Track post change KPIs to confirm benefit and prevent drift. | - Improves throughput for power users because devices match workload intensity. <br><br> - Reduces waste for light users because overpowered kits are avoided. <br><br> - Lowers performance tickets because bottlenecks are engineered out. <br><br> - Supports fair allocation because decisions rely on data not anecdotes. | **(Under-spec hours lost − After hours) × Affected units.** | Category mix differences often mirror role misalignment. |
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|-----------------|----------------------|----------|------------------|--------------------------------|
| **Tailor allocation by user profile** | **Phase 1 – Persona Map:** Map roles to device types so the catalog proposes defaults that fit what users actually do. <br><br> **Phase 2 – Deploy:** Prioritize fit within top categories such as **{top_name}** so most users benefit quickly. <br><br> **Phase 3 – Re-validate Annually:** Recheck personas each year so allocations evolve with new tools and work patterns. | - Improves daily experience because users receive hardware that matches their tasks. <br><br> - Reduces performance complaints because underpowered devices are avoided. <br><br> - Increases adoption of standard builds because choices feel appropriate rather than restrictive. <br><br> - Lowers request churn because fewer exceptions are needed. | **Reduced replacement requests × Avg cost.** Inventory base = **{total_in_cat}**. | Heavy skew toward **{top_name}** means many users share similar needs—easy wins. |
| **Publish reliability index** | **Phase 1 – Scoreboard:** Publish incidents per 100 assets by brand or type so differences are visible to requesters. <br><br> **Phase 2 – Share:** Let users select the proven option by showing the score during request submission. <br><br> **Phase 3 – Reward:** Prefer high performers in approvals so the fleet gradually shifts toward reliable lines. | - Encourages rational requests because users see the stability trade offs clearly. <br><br> - Nudges demand to stable platforms which reduces downtime later. <br><br> - Prevents surprises for users because expectations are set with data. <br><br> - Supports transparent decision making which builds trust in IT standards. | **Complaints avoided × Ticket cost.** Impact greatest where top bars dominate. | Category distribution provides the denominator for per-100 calculations. |
| **Onboarding playbooks per category** | **Phase 1 – Quickstart:** Provide a one pager for each top `{cat}` that covers login setup and common tasks. <br><br> **Phase 2 – Videos:** Add short clips for the most frequent how to topics so users can self help. <br><br> **Phase 3 – NPS Pulse:** Run a first week survey to capture gaps and update materials. | - Speeds time to productive because users can complete basics without calling support. <br><br> - Reduces how to tickets because answers are easy to follow. <br><br> - Improves first week satisfaction because friction is removed early. <br><br> - Creates a feedback loop that keeps materials relevant. | **Tickets deflected × Handling cost.** Focus on **{top_name} ({top_count})**. | Concentration in a few categories lets you target materials efficiently. |
| **VIP device lanes** | **Phase 1 – Pre-stock:** Keep ready to ship kits for VIP teams within the top categories so turnaround is rapid. <br><br> **Phase 2 – Concierge Setup:** Assign a named owner for configuration and delivery so the experience feels managed. <br><br> **Phase 3 – SLA Reports:** Provide executive level visibility on fulfillment performance each month. | - Protects key user experience because critical roles receive devices without delay. <br><br> - Reduces downtime for strategic teams because replacement paths are pre arranged. <br><br> - Strengthens stakeholder trust because commitments are met reliably. <br><br> - Clarifies accountability because a single owner shepherds each request. | **(VIP downtime avoided × Revenue at risk).** | High-volume categories are also where VIPs usually sit—lane prevents contention. |
| **Experience telemetry** | **Phase 1 – Collect:** Track metrics such as login time boot duration and app crashes per category to create a clear health picture. <br><br> **Phase 2 – Act:** Swap or patch where scores lag so users feel improvements quickly. <br><br> **Phase 3 – Share:** Publish before and after results so users see progress and understand prioritization. | - Produces measurably better user experience because fixes target real bottlenecks. <br><br> - Reduces tickets that say device feels slow because performance is tuned proactively. <br><br> - Guides refresh priorities so replacements go where they deliver maximum benefit. <br><br> - Builds credibility because improvements are shown with data not anecdotes. | **ΔBad-experience rate × Tickets × Cost.** | Category bars define cohorts for experience scoring. |
"""
        }
        render_cio_tables("Asset Categories", cio_1b)
