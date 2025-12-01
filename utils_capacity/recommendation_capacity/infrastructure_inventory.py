import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- Visual identity: professional blue & white ---
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]  # blues only
px.defaults.color_discrete_sequence = PX_SEQ  # apply globally

def _fmt_currency(v):
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "N/A"

def _fmt_num(v):
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return "N/A"

def infrastructure_inventory(df):

    # ============================
    # Asset Distribution by Component Type
    # ============================
    with st.expander("📌 Asset Distribution by Component Type"):
        if "component_type" in df.columns:

            counts = df["component_type"].value_counts().reset_index()
            counts.columns = ["component_type", "count"]

            have_cost = "cost_per_month_usd" in df.columns
            have_savings = "potential_savings_usd" in df.columns
            have_inc = "incident_count" in df.columns
            have_down = "downtime_minutes" in df.columns

            cost_by_type = (
                df.groupby("component_type")["cost_per_month_usd"].sum().reset_index()
                if have_cost else pd.DataFrame()
            )
            savings_by_type = (
                df.groupby("component_type")["potential_savings_usd"].sum().reset_index()
                if have_savings else pd.DataFrame()
            )
            inc_by_type = (
                df.groupby("component_type")["incident_count"].sum().reset_index()
                if have_inc else pd.DataFrame()
            )
            down_by_type = (
                df.groupby("component_type")["downtime_minutes"].sum().reset_index()
                if have_down else pd.DataFrame()
            )

            # Helper
            def _get_val(df_src, key_col, key, val_col):
                if df_src.empty:
                    return None
                row = df_src[df_src[key_col] == key]
                return None if row.empty else float(row.iloc[0][val_col])

            # ------------------------------------------------
            # Graph 1: Bar Chart - Asset Distribution
            # ------------------------------------------------
            fig_bar = px.bar(
                counts, x="component_type", y="count", text="count",
                title="Asset Distribution by Component Type"
            )
            fig_bar.update_traces(textposition="outside", marker_color=PX_SEQ[0])
            st.plotly_chart(fig_bar, use_container_width=True, key="infra_component_bar")

            top = counts.iloc[0]
            low = counts.iloc[-1]
            total_assets_ct = int(counts["count"].sum()) if not counts.empty else 0
            share_top = (top["count"] / counts["count"].sum() * 100) if counts["count"].sum() else 0.0

            st.write(f"""
**What this graph is:** A bar chart showing **asset distribution by component type**.  
- **X-axis:** Component types.  
- **Y-axis:** Asset count.

**What it shows in your data:** **{str(top['component_type'])}** is the largest cohort with **{int(top['count']):,}** assets (**{share_top:.2f}%** of **{total_assets_ct:,}** total), while **{str(low['component_type'])}** is the smallest with **{int(low['count']):,}**.  
This gap signals where standardization and policy controls will pay off quickest, because the biggest cohorts concentrate both risk and opportunity.

**Overall:** The estate is **concentrated in a few dominant types** with a long tail of minor categories.  
That concentration simplifies prioritization: actions taken on the top one or two types can influence the majority of operational cost, incident exposure, and lifecycle complexity.

**How to read it operationally:**  
1) **Peaks:** Standardize and right-size the top types first for maximum impact; define golden builds, patch baselines, and capacity guardrails here.  
2) **Plateaus:** Maintain provisioning guardrails for steady-growth types; watch for SKU drift and unmanaged variations over time.  
3) **Downswings:** Validate if declines are due to retirement or data gaps; small categories often hide legacy kits that quietly consume support effort.  
4) **Mix:** Align lifecycle and spares to the highest-volume types; stocking to the modal hardware trims MTTR and avoids mismatched parts.

**Why this matters:** Focusing optimization on high-volume types amplifies gains in **cost, performance, and operational simplicity**.  
It also reduces cognitive load for engineers—fewer patterns to maintain means fewer surprises during incidents and changes.
""")

            # ------------------------------------------------
            # Graph 2: Treemap - Share of Assets by Type
            # ------------------------------------------------
            fig_tree = px.treemap(
                counts, path=["component_type"], values="count",
                title="Treemap — Share of Assets by Type",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_tree, use_container_width=True, key="infra_component_treemap")

            st.write(f"""
**What this graph is:** A treemap showing the **proportional share** of total assets by component type.  
- **Tiles:** Component types.  
- **Size:** Share of total assets.

**What it shows in your data:** **{str(top['component_type'])}** occupies the largest area (≈ **{share_top:.2f}%** of assets), while **{str(low['component_type'])}** is a small tile indicating minimal footprint.  
Large tiles imply administrative dominance—most policies, incidents, and spend gravity live there.

**Overall:** A **concentrated estate** where actions on the top few types influence most infrastructure outcomes.  
This helps triage roadmaps: you can deliver measurable results without boiling the ocean.

**How to read it operationally:**  
1) **Peaks:** Prioritize policy control, patch baselines, and monitoring here; coverage here equals coverage for most of the estate.  
2) **Plateaus:** Keep health checks consistent to avoid silent growth; small unchecked expansions can snowball into spend surprises.  
3) **Downswings:** Evaluate for retirement or consolidation opportunities; niche tiles often map to legacy or orphaned services.  
4) **Mix:** Map critical applications onto dominant types to guide resilience; resilient patterns applied to big tiles de-risk the business faster.

**Why this matters:** Knowing **where the estate is concentrated** directs the **fastest path to ROI**.  
It also clarifies reporting: stakeholders can see why the roadmap prioritizes certain hardware families first.
""")

            # ------------------------------------------------
            # Graph 3: Donut Chart - Cost Distribution
            # ------------------------------------------------
            if have_cost and not cost_by_type.empty:
                fig_pie = px.pie(
                    cost_by_type,
                    values="cost_per_month_usd",
                    names="component_type",
                    title="Cost Distribution by Component Type",
                    hole=0.4,
                    color_discrete_sequence=PX_SEQ,
                )
                st.plotly_chart(fig_pie, use_container_width=True, key="infra_component_pie")

                top_cost_row = cost_by_type.loc[cost_by_type["cost_per_month_usd"].idxmax()]
                total_cost_ct = float(cost_by_type["cost_per_month_usd"].sum())
                top_cost_share = (
                    float(top_cost_row["cost_per_month_usd"]) / total_cost_ct * 100
                    if total_cost_ct > 0
                    else 0.0
                )

                # Clean, plain-text analysis (no **, no special symbols)
                st.markdown(
                    f"""
What this graph is: A donut chart showing monthly cost distribution by component type.

Slices: Component types.  
Values: Share of monthly run rate cost.

What it shows in your data: {str(top_cost_row['component_type'])} is the largest cost contributor at { _fmt_currency(top_cost_row['cost_per_month_usd']) } ({top_cost_share:.2f}% of { _fmt_currency(total_cost_ct) }). This cost concentration shows where rightsizing, license cleanup, and tiering will generate visible OPEX savings.

Overall: A small subset of types drives a disproportionate share of cost. These types are ideal targets for rightsizing and consolidation. Because spend is skewed, focused actions such as resize, retire, and re platform can deliver better results than broad, generic quotas.

How to read it operationally:  
1) Peaks: Enforce sizing templates and retire idle capacity for the highest cost types. Combine with automated detection of low utilization nodes.  
2) Plateaus: Track monthly cost variance by type. Sustained variance suggests configuration drift or changes in workload.  
3) Downswings: Confirm whether cost reductions are durable or just one off effects. Make sure cost drops persist across several billing cycles.  
4) Mix: Always pair cost decisions with utilization data. Validate that cost reductions do not push CPU or memory above safe headroom limits.

Why this matters: Targeting the highest cost types accelerates OPEX reduction without wide disruption. Once the largest cost drivers are stable and predictable, it becomes easier to manage and forecast the rest of the estate.
""",
                )

            # ======== Live numbers for CIO tables (component type scope) ========
            total_cost_all = float(df["cost_per_month_usd"].sum()) if have_cost else 0.0
            total_sav_all = float(df["potential_savings_usd"].sum()) if have_savings else 0.0
            avg_sav_pct_all = (total_sav_all / total_cost_all * 100) if total_cost_all > 0 else 0.0

            top_type = str(top["component_type"])
            top_type_cost = _get_val(cost_by_type, "component_type", top_type, "cost_per_month_usd") if have_cost else None
            top_type_sav = _get_val(savings_by_type, "component_type", top_type, "potential_savings_usd") if have_savings else None
            top_type_sav_pct = (
                (top_type_sav / top_type_cost * 100) if (top_type_cost and top_type_cost > 0 and top_type_sav is not None) else None
            )

            # Create per-type breakdown lines for proof (top 5 by cost if available)
            breakdown_lines = []
            if have_cost and have_savings and not cost_by_type.empty:
                merged = pd.merge(cost_by_type, savings_by_type, on="component_type", how="left").fillna(0.0)
                merged["saving_pct"] = merged.apply(
                    lambda r: (r["potential_savings_usd"] / r["cost_per_month_usd"] * 100) if r["cost_per_month_usd"] > 0 else 0.0, axis=1
                )
                merged = merged.sort_values("cost_per_month_usd", ascending=False).head(5)
                for _, r in merged.iterrows():
                    breakdown_lines.append(
                        f"{r['component_type']} → Cost {_fmt_currency(r['cost_per_month_usd'])}, "
                        f"Savings {_fmt_currency(r['potential_savings_usd'])} "
                        f"({r['saving_pct']:.2f}%)"
                    )
            breakdown_text = "<br>".join([f"• {line}" for line in breakdown_lines]) if breakdown_lines else "• Breakdown not available."

            # Evidence strings
            ev_vol = f"{top_type} dominates with {int(top['count']):,} assets ({share_top:.2f}% of total {total_assets_ct:,})."
            ev_cost = ""
            if have_cost and top_type_cost is not None:
                ev_cost = f" Highest cost type in donut = {top_type} with {_fmt_currency(top_type_cost)}."
            ev_inc = ""
            if have_inc:
                top_type_inc = _get_val(inc_by_type, "component_type", top_type, "incident_count")
                if top_type_inc is not None:
                    ev_inc = f" Incidents for {top_type} = {int(top_type_inc):,}."
            ev_down = ""
            if have_down:
                top_type_down = _get_val(down_by_type, "component_type", top_type, "downtime_minutes")
                if top_type_down is not None:
                    ev_down = f" Downtime for {top_type} = {int(top_type_down):,} minutes."

            # =======================================================
            # CIO Tables (each in its own expander) — component type
            # =======================================================
            with st.expander("Cost Reduction Recommendations"):
                # Proof building blocks
                formula_total = "Formula: Savings% = Σ(potential_savings_usd) ÷ Σ(cost_per_month_usd) × 100"
                dataset_total = f"Dataset: ({_fmt_num(total_sav_all)})/({_fmt_num(total_cost_all)})"
                result_total = f"Result: {avg_sav_pct_all:.2f}% potential monthly cost reduction"

                formula_type = "Formula: Type Savings% = Σ(potential_savings_usd for type) ÷ Σ(cost_per_month_usd for type) × 100"
                dataset_type = f"Dataset: ({_fmt_num(top_type_sav) if top_type_sav is not None else 'N/A'})/({_fmt_num(top_type_cost) if top_type_cost is not None else 'N/A'})"
                result_type = f"Result: {top_type_sav_pct:.2f}% for {top_type}" if top_type_sav_pct is not None else "Result: N/A"

                st.markdown(f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate underutilized assets | Phase 1: Identify low use systems in the bottom quartile of utilization and confirm that their workloads can be moved without breaking service level expectations.<br><br>Phase 2: Merge these low use systems onto shared nodes and retire duplicate instances so that capacity is pooled and used more efficiently.<br><br>Phase 3: Reclaim associated licenses, support contracts, and maintenance activities and update the inventory and monitoring records to reflect the new footprint.<br><br> | - Reduces ongoing operating expenditure and day to day support overhead because fewer servers and contracts need to be maintained.<br><br>- Cuts idle capacity across the dominant component types and allows the same business demand to run on a smaller infrastructure base.<br><br>- Shrinks the physical and logical footprint of the environment which makes patching, monitoring, and troubleshooting faster and simpler.<br><br>- Improves hardware and energy utilization which supports sustainability targets while still meeting performance requirements.<br><br> | {formula_total}<br>{dataset_total}<br>{result_total}<br>Breakdown (Top by Cost):<br>{breakdown_text} | {ev_vol}{ev_cost} |
| Standardize hardware models | Phase 1: Define two or three standard hardware templates for each major component type based on real capacity needs, typical workloads, and vendor support commitments.<br><br>Phase 2: Plan and execute migrations from non standard builds onto these templates, coordinating with application owners to avoid disruption and ensuring that performance remains acceptable.<br><br>Phase 3: Enforce the new templates through provisioning guardrails so that future requests default to standardized models rather than one off exceptions.<br><br> | - Reduces oversizing and random variety in hardware which lowers the risk of paying for capacity that is not actually used.<br><br>- Lowers maintenance effort because engineers can rely on a small set of predictable configurations instead of learning many unique builds.<br><br>- Improves lifecycle planning as refresh cycles and support contracts can be aligned to a few standard models rather than scattered across many variants.<br><br>- Strengthens vendor negotiation power because concentrated demand on standard models makes volume discounts easier to secure.<br><br> | {formula_type}<br>{dataset_type}<br>{result_type} | Treemap + bar show skewed distribution; high-variance types are standardization targets. |
| Retire legacy systems | Phase 1: Locate component types with very low counts that are still running and review with business owners whether the underlying applications remain required for current operations.<br><br>Phase 2: Design a safe retirement or replacement plan that covers data migration, interface changes, and user communication so that business processes can move away from the legacy platforms.<br><br>Phase 3: Decommission the legacy hardware and software, clean up related monitoring and backup configurations, and remove them from inventory and security scopes.<br><br> | - Eliminates legacy support cost because old hardware, operating systems, and specialist skills are no longer needed to keep the environment running.<br><br>- Reduces operational and security risk since outdated platforms often have known vulnerabilities and limited vendor support.<br><br>- Simplifies patching and monitoring because there are fewer unique systems and edge cases to maintain in production.<br><br>- Frees up rack space, power, and cooling capacity that can be reused for modern workloads with higher business value.<br><br> | Formula: Savings = Count_retired × Avg cost/asset (by type)<br>Dataset: uses per-type cost averages from uploaded data | Smallest bars/treemap tiles are prime retirement candidates. |
| License optimization | Phase 1: Map software entitlements and license metrics to the active assets for each component type and identify where allocations exceed real usage or where assets have moved but licenses have not.<br><br>Phase 2: Reclaim or reassign unused or underused licenses and adjust license tiers to better match observed consumption patterns for each type.<br><br>Phase 3: Implement a recurring license audit and reconciliation process so that new discrepancies are detected quickly rather than accumulating over time.<br><br> | - Reduces duplicate license spend because entitlements that are not used are either cancelled or reallocated to where they are genuinely needed.<br><br>- Aligns licensing cost more closely to actual usage so the organization pays primarily for value delivered rather than idle entitlements.<br><br>- Improves audit readiness by keeping records accurate and consistent which reduces the risk of surprise compliance findings.<br><br>- Creates clearer visibility of which component types drive license demand which helps shape future technology and procurement choices.<br><br> | Formula: Savings = Σ reclaimed licenses × fee/unit<br>Dataset: derived from top-cost types (see breakdown lines) | Donut shows cost concentration where license focus yields ROI. |
| Predictive scaling | Phase 1: Analyze historical utilization and incident patterns by component type and build simple forecasts for expected growth under normal and peak scenarios.<br><br>Phase 2: Use these forecasts to set minimum and maximum capacity levels so that standard baselines are lower but still allow safe scaling when demand rises.<br><br>Phase 3: Review capacity versus actual demand on a quarterly basis and adjust baselines and scaling rules whenever business volumes or applications change significantly.<br><br> | - Prevents chronic overprovisioning by replacing static, worst case sizing assumptions with data driven projected needs for each component type.<br><br>- Preserves performance during peaks because autoscaling or planned expansions are triggered before saturation is reached.<br><br>- Supports sustained spend control as capacity automatically shrinks when demand falls instead of remaining permanently elevated.<br><br>- Helps avoid emergency capacity purchases because growth and seasonal effects are anticipated early and turned into planned actions.<br><br> | {formula_type}<br>{dataset_type}<br>{result_type} | High-count/high-cost type offers the largest scaling leverage. |
                """, unsafe_allow_html=True)

            with st.expander("Performance Improvement Recommendations"):
                # Build performance proof lines (risk proxy)
                total_inc = int(df["incident_count"].sum()) if have_inc else None
                total_down = int(df["downtime_minutes"].sum()) if have_down else None
                perf_formula = "Formula: Risk Proxy = Σ(incident_count) + Σ(downtime_minutes)"
                perf_dataset = f"Dataset: incidents={total_inc if total_inc is not None else 'N/A'} / downtime_minutes={total_down if total_down is not None else 'N/A'}"
                perf_result = "Result: Higher proxy → higher instability; focus on dominant types first."

                st.markdown(f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Apply CPU/Memory guardrails | Phase 1: Define clear utilization thresholds per component type, such as early warning levels and critical saturation levels, based on observed incident and performance patterns.<br><br>Phase 2: Implement automatic scaling policies or workload shedding rules that react when these thresholds are breached and document how operations teams should respond.<br><br>Phase 3: Review threshold breaches, scaling events, and incident outcomes on a weekly basis and tune the guardrails so that alerts are meaningful and not noisy.<br><br> | - Prevents services from running at unsafe saturation levels which directly reduces the frequency of performance related incidents.<br><br>- Protects formal service level agreements during peak demand because the system reacts early rather than waiting for user complaints.<br><br>- Reduces firefighting for engineers since many capacity issues are addressed by policy rather than last minute manual intervention.<br><br>- Creates a repeatable pattern for managing resource limits which makes future tuning and automation easier to implement.<br><br> | {perf_formula}<br>{perf_dataset}<br>{perf_result} | {ev_vol}{ev_inc}{ev_down} |
| Enforce golden images | Phase 1: Define a small set of base images for each major component type that include tested operating system versions, security hardening, and standard tooling.<br><br>Phase 2: Integrate checks into CI/CD and provisioning pipelines so that deviations from the golden images are detected and corrected before reaching production.<br><br>Phase 3: Run quarterly posture audits to compare real servers against the golden image definitions and remediate any drift that has appeared over time.<br><br> | - Reduces misconfiguration incidents because new assets start from a known good and tested baseline instead of ad hoc builds.<br><br>- Speeds up recoveries and rebuilds since engineers can redeploy from a trusted image rather than assembling systems from scratch.<br><br>- Keeps performance more consistent as tuning and optimizations in the golden image benefit every instance of that type.<br><br>- Simplifies security and compliance reviews because reviewers only need to understand a few standard configurations instead of many custom ones.<br><br> | Formula: Incident Reduction = ΔIncidents × Mean Impact<br>Dataset: computed from incident_count trend by type | Consistent baselines reduce variance across dominant types. |
| Balance workloads | Phase 1: Identify workload hotspots within the top component type by examining utilization skew, queue lengths, and response time differences between nodes.<br><br>Phase 2: Reassign or rebalance jobs, adjust scheduling, or move heavy batch workloads to off peak windows so that resource usage is smoother across instances.<br><br>Phase 3: Validate that latency and error rates improve after rebalancing and confirm that no new hotspot has been created on another node or type.<br><br> | - Creates smoother throughput across infrastructure which improves average and tail response times for users.<br><br>- Avoids localized saturation where one node struggles while others remain lightly loaded which reduces the chance of node specific failures.<br><br>- Makes better use of existing capacity which can postpone or prevent the need for additional hardware or cloud resources.<br><br>- Makes performance more predictable because workloads follow a design rather than accumulating randomly wherever capacity happened to exist.<br><br> | Formula: Downtime Avoided = ΔDowntime (min) × Cost/min<br>Dataset: downtime_minutes by type | Bar/treemap skew implies imbalance within the top type. |
| Patch optimization | Phase 1: Design a staged patch rollout plan per component type that starts with a small canary group of nodes before progressing to the full estate.<br><br>Phase 2: Monitor technical and business metrics after each wave and keep a tested rollback path ready so changes can be reverted quickly if issues appear.<br><br>Phase 3: Capture lessons learned from each patch cycle and update patch windows, validation checks, and rollback criteria to continuously improve outcomes.<br><br> | - Reduces downtime caused by faulty patches because defects are more likely to be caught in early, low risk waves.<br><br>- Shortens mean time to recover when patching problems occur since rollback steps are rehearsed and documented in advance.<br><br>- Increases overall stability because patches are applied in a controlled and observable way rather than rushed under pressure.<br><br>- Improves confidence among stakeholders that regular patching is both safe and beneficial rather than a source of chaos.<br><br> | Formula: ΔIncidents × MTTR Reduction<br>Dataset: incident_count & downtime_minutes trends | Incident/downtime clustering validates priority types. |
| Predictive capacity planning | Phase 1: Use historical growth patterns and project plans to forecast future demand for each component type, including seasonal peaks and expected new workloads.<br><br>Phase 2: Translate these forecasts into resource plans and buffer levels so that the estate grows just ahead of demand without large idle capacity.<br><br>Phase 3: Monitor actual utilization versus forecast every month and adjust the models whenever real traffic diverges from the original assumptions.<br><br> | - Reduces the likelihood of sudden saturation because capacity is added deliberately before known demand increases hit the environment.<br><br>- Reduces reactive escalations and last minute purchases since capacity decisions follow a planned schedule rather than crisis driven timelines.<br><br>- Improves SLA performance because critical services see fewer capacity related slowdowns or outages during busy periods.<br><br>- Gives finance and leadership a clearer view of upcoming investment needs which supports smoother budgeting and approval cycles.<br><br> | {perf_formula}<br>{perf_dataset}<br>{perf_result} | High-volume types are priority for accurate forecasting. |
                """, unsafe_allow_html=True)

            with st.expander("Customer Satisfaction Recommendations"):
                cs_formula = "Formula: Savings Impact = Σ(potential_savings_usd) ÷ Σ(cost_per_month_usd) × 100 (enables reinvestment)"
                cs_dataset = f"Dataset: ({_fmt_num(total_sav_all)})/({_fmt_num(total_cost_all)})"
                cs_result = f"Result: {avg_sav_pct_all:.2f}% optimization headroom to reinvest in service quality"

                st.markdown(f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish service transparency dashboard | Phase 1: Build an internal and external dashboard that shows key indicators by component type such as availability, incident counts, and changes completed.<br><br>Phase 2: Compare these indicators against agreed targets and highlight where performance is on track and where it is drifting below expectations.<br><br>Phase 3: Provide a short executive summary that explains the main trends and actions planned so that non technical stakeholders can understand the story quickly.<br><br> | - Builds trust with users and business stakeholders because they can see clear evidence of how services and infrastructure are performing.<br><br>- Reduces escalations that arise from uncertainty since many questions can be answered directly from the published metrics.<br><br>- Aligns expectations by making it clear which areas are performing well and which are being actively improved.<br><br>- Provides a shared view for technology and business teams which makes prioritisation discussions more objective and data driven.<br><br> | {cs_formula}<br>{cs_dataset}<br>{cs_result} | Dominant type {top_type} ({share_top:.2f}% of assets) most impacts perceived quality. |
| Prioritize critical workloads | Phase 1: Identify which applications and business processes mapped to the top component types are most critical for revenue, operations, or compliance.<br><br>Phase 2: Reserve safeguarded capacity and stricter performance thresholds for these critical workloads so that they are protected even when the estate is under stress.<br><br>Phase 3: Monitor these workloads closely during peak hours and review whether prioritization rules are keeping their experience within agreed levels.<br><br> | - Protects high impact users and business functions from degradation when shared infrastructure becomes busy or constrained.<br><br>- Stabilizes response times and transaction success rates for the services that matter most to customers and leadership.<br><br>- Reduces churn risk by ensuring that key user journeys remain reliable even when less important workloads slow down.<br><br>- Clarifies which services receive preferential treatment which helps manage expectations when resources are tight.<br><br> | Formula: Value = Avoided downtime × impacted users<br>Dataset: uses downtime_minutes and asset mapping | Largest estate share ties to the biggest CSAT upside. |
| Optimize maintenance windows | Phase 1: Use historical utilization and incident data to identify time windows where user activity and risk are naturally lower for each major component type.<br><br>Phase 2: Schedule maintenance and changes into these low impact windows and communicate timings to stakeholders with enough notice for them to plan around it.<br><br>Phase 3: Validate after each window that performance and satisfaction metrics remained stable and refine window selection based on feedback.<br><br> | - Minimizes disruption to users because changes are performed when fewer people depend on the affected systems.<br><br>- Reduces the number of complaints tied to maintenance events since work is both predictable and aligned with low demand periods.<br><br>- Increases satisfaction as users experience fewer unexpected outages in the middle of business critical tasks.<br><br>- Helps technical teams complete work more calmly and accurately because they operate in a controlled, low pressure context.<br><br> | Formula: Complaints Avoided × Handling Cost<br>Dataset: pre/post maintenance incident trends | Concentration suggests timing changes have outsized effect. |
| Implement feedback channels | Phase 1: Set up simple feedback mechanisms, such as short surveys or ticket tags, that capture user experience by component type and key service area.<br><br>Phase 2: Prioritize the most common or severe pain points highlighted in the feedback and schedule them into improvement backlogs with clear owners.<br><br>Phase 3: Communicate back to users about which issues have been addressed so they can see the impact of their input and continue to share insights.<br><br> | - Enables targeted improvements because decisions are based on real user feedback rather than assumptions about what might be painful.<br><br>- Shows users that their comments lead to visible changes which increases their willingness to provide constructive feedback in the future.<br><br>- Improves satisfaction metrics as the most frequently reported issues are systematically reduced over time.<br><br>- Helps align technical effort with business perception so teams work on what users actually care about rather than only backend metrics.<br><br> | Formula: ΔCSAT × Retention Value<br>Dataset: link survey results to type-level KPIs | Charts help pinpoint where to ask and act. |
| Improve SLA communication | Phase 1: Define clear SLA and SLO thresholds for each major component type using realistic targets that reflect current architecture and business needs.<br><br>Phase 2: Publish simple, easy to read SLA views on a monthly basis that show where performance met or missed those thresholds.<br><br>Phase 3: Iterate on targets and remediation plans where gaps persist so that expectations and capability gradually converge.<br><br> | - Sets clear expectations for stakeholders so they understand what levels of performance and availability can be relied upon.<br><br>- Reduces escalations rooted in misunderstanding because service levels are documented and visible rather than implied.<br><br>- Builds trust when SLAs are met consistently and provides context when they are missed along with plans to close the gap.<br><br>- Supports better prioritisation of reliability work since the largest and most persistent SLA gaps can be addressed first.<br><br> | {cs_formula}<br>{cs_dataset}<br>{cs_result} | Visuals show whether type-level targets are realistic. |
                """, unsafe_allow_html=True)

        else:
            st.info("Column 'component_type' not found in dataset.")

    # ============================
    # Asset Count by Location
    # ============================
    with st.expander("📌 Asset Count by Location"):
        if {"location", "asset_id"} <= set(df.columns):

            loc_counts = df.groupby("location")["asset_id"].nunique().reset_index()
            have_cost = "cost_per_month_usd" in df.columns
            have_sav = "potential_savings_usd" in df.columns
            have_inc = "incident_count" in df.columns
            have_down = "downtime_minutes" in df.columns

            cost_by_loc = (
                df.groupby("location")["cost_per_month_usd"].sum().reset_index()
                if have_cost else pd.DataFrame()
            )
            sav_by_loc = (
                df.groupby("location")["potential_savings_usd"].sum().reset_index()
                if have_sav else pd.DataFrame()
            )
            inc_by_loc = (
                df.groupby("location")["incident_count"].sum().reset_index()
                if have_inc else pd.DataFrame()
            )
            down_by_loc = (
                df.groupby("location")["downtime_minutes"].sum().reset_index()
                if have_down else pd.DataFrame()
            )

            # Graph 1: Bar Chart
            fig1 = px.bar(
                loc_counts.sort_values("asset_id", ascending=False),
                x="location", y="asset_id", text="asset_id",
                title="Asset Count by Location"
            )
            fig1.update_traces(textposition="outside", marker_color=PX_SEQ[0])
            st.plotly_chart(fig1, use_container_width=True, key="infra_location_bar")

            top_loc = loc_counts.loc[loc_counts["asset_id"].idxmax()]
            low_loc = loc_counts.loc[loc_counts["asset_id"].idxmin()]
            total_assets_loc = int(loc_counts["asset_id"].sum())
            share_top = (top_loc["asset_id"] / loc_counts["asset_id"].sum() * 100) if loc_counts["asset_id"].sum() else 0.0

            st.write(f"""
**What this graph is:** A bar chart summarizing **unique assets by location**.  
- **X-axis:** Locations.  
- **Y-axis:** Unique asset count.

**What it shows in your data:** **{str(top_loc['location'])}** hosts the largest footprint with **{int(top_loc['asset_id']):,}** assets (**{share_top:.2f}%** of **{total_assets_loc:,}**), while **{str(low_loc['location'])}** is smallest with **{int(low_loc['asset_id']):,}**.  
The distribution tells you where operational risk concentrates geographically and where site practices most affect outcomes.

**Overall:** A **concentrated topology** where a few sites carry a sizeable share of infrastructure.  
Those sites deserve tighter change control, more mature capacity planning, and clearer redundancy patterns.

**How to read it operationally:**  
1) **Peaks:** Prioritize redundancy and failover testing at the top sites; document and rehearse switchover procedures.  
2) **Plateaus:** Maintain capacity and spares proportional to load; avoid reactive logistics for common failures.  
3) **Downswings:** Validate if assets were retired or data is incomplete; reconcile CMDB vs. discovery to remove ghost entries.  
4) **Mix:** Align on-site support hours to volume; high-footprint locations benefit from local runbooks and known-error repositories.

**Why this matters:** Concentration informs **resilience, staffing, and maintenance windows** to protect user experience.  
It also clarifies where executive updates should focus during incidents and planned work.
""")

            # Graph 2: Cost Box Plot (if available)
            if have_cost:
                fig2 = px.box(
                    df.dropna(subset=["location", "cost_per_month_usd"]),

                    x="location", y="cost_per_month_usd",
                    title="Monthly Cost Distribution per Location"
                )
                fig2.update_traces(marker_color=PX_SEQ[1])
                st.plotly_chart(fig2, use_container_width=True, key="infra_location_box")

                # Compute medians and spread for narrative
                med_by_loc = df.groupby("location")["cost_per_month_usd"].median().reset_index(name="median_cost")
                max_med_row = med_by_loc.loc[med_by_loc["median_cost"].idxmax()]
                min_med_row = med_by_loc.loc[med_by_loc["median_cost"].idxmin()]
                overall_min = float(df["cost_per_month_usd"].min())
                overall_max = float(df["cost_per_month_usd"].max())

                st.write(f"""
**What this graph is:** A box plot showing **monthly cost per asset** by location.  
- **X-axis:** Locations.  
- **Y-axis:** Monthly cost per asset.

**What it shows in your data:** Median cost is highest at **{str(max_med_row['location'])}** (**{_fmt_currency(max_med_row['median_cost'])}**) and lowest at **{str(min_med_row['location'])}** (**{_fmt_currency(min_med_row['median_cost'])}**). Across all sites, individual assets range **{_fmt_currency(overall_min)}–{_fmt_currency(overall_max)}**.  
Wide boxes/long whiskers mean inconsistent build patterns or mixed workloads within a site; tight boxes imply standardization and predictable spend.

**Overall:** Cost structures are **non-uniform across regions**, reflecting differences in asset mix, licensing, and efficiency.  
This heterogeneity is a clue: harmonizing builds and contracts at high-median sites should compress variance and pull medians down.

**How to read it operationally:**  
1) **Peaks:** Investigate high-median sites for rightsizing and contract review; renegotiate licenses aligned to actual usage.  
2) **Plateaus:** Guard against drift with monthly variance checks; set alerts when IQR widens beyond a threshold.  
3) **Downswings:** Validate if low costs reflect simpler stacks or missing items; ensure reduced spend isn’t data loss.  
4) **Mix:** Pair with utilization to avoid undercutting SLAs; cheap but saturated sites are false economies.

**Why this matters:** Reducing **spread and medians** at expensive sites drives **predictable OPEX** without sacrificing performance.  
Predictability turns into better budgeting, fewer escalations, and cleaner executive reporting.
""")

            # ======== Live numbers for CIO tables (location scope) ========
            total_cost_all = float(df["cost_per_month_usd"].sum()) if have_cost else 0.0
            total_sav_all = float(df["potential_savings_usd"].sum()) if have_sav else 0.0
            avg_sav_pct_all = (total_sav_all / total_cost_all * 100) if total_cost_all > 0 else 0.0

            def _get_loc_val(xdf, loc, col):
                if xdf.empty:
                    return None
                r = xdf[xdf["location"] == loc]
                return None if r.empty else float(r.iloc[0][col])

            top_loc_name = str(top_loc["location"])
            top_loc_cost = _get_loc_val(cost_by_loc, top_loc_name, "cost_per_month_usd") if have_cost else None
            top_loc_sav = _get_loc_val(sav_by_loc, top_loc_name, "potential_savings_usd") if have_sav else None
            top_loc_inc = _get_loc_val(inc_by_loc, top_loc_name, "incident_count") if have_inc else None
            top_loc_down = _get_loc_val(down_by_loc, top_loc_name, "downtime_minutes") if have_down else None
            top_loc_sav_pct = (
                (top_loc_sav / top_loc_cost * 100) if (top_loc_cost and top_loc_cost > 0 and top_loc_sav is not None) else None
            )

            # Location breakdown lines for proof (top 5 by cost)
            breakdown_loc_lines = []
            if have_cost and have_sav and not cost_by_loc.empty:
                m2 = pd.merge(cost_by_loc, sav_by_loc, on="location", how="left").fillna(0.0)
                m2["saving_pct"] = m2.apply(
                    lambda r: (r["potential_savings_usd"] / r["cost_per_month_usd"] * 100) if r["cost_per_month_usd"] > 0 else 0.0, axis=1
                )
                m2 = m2.sort_values("cost_per_month_usd", ascending=False).head(5)
                for _, r in m2.iterrows():
                    breakdown_loc_lines.append(
                        f"{r['location']} → Cost {_fmt_currency(r['cost_per_month_usd'])}, "
                        f"Savings {_fmt_currency(r['potential_savings_usd'])} "
                        f"({r['saving_pct']:.2f}%)"
                    )
            breakdown_loc_text = "<br>".join([f"• {line}" for line in breakdown_loc_lines]) if breakdown_loc_lines else "• Breakdown not available."

            ev_text_loc = f"{top_loc_name} leads with {int(top_loc['asset_id']):,} assets ({share_top:.2f}% of {total_assets_loc:,})."
            if have_cost and top_loc_cost is not None:
                ev_text_loc += f" Monthly cost at {top_loc_name} = {_fmt_currency(top_loc_cost)}."

            # CIO Tables for Location — strict format
            with st.expander("Cost Reduction Recommendations"):
                formula_total = "Formula: Savings% = Σ(potential_savings_usd) ÷ Σ(cost_per_month_usd) × 100"
                dataset_total = f"Dataset: ({_fmt_num(total_sav_all)})/({_fmt_num(total_cost_all)})"
                result_total = f"Result: {avg_sav_pct_all:.2f}% potential monthly cost reduction"

                formula_loc = "Formula: Location Savings% = Σ(potential_savings_usd at location) ÷ Σ(cost_per_month_usd at location) × 100"
                dataset_loc = f"Dataset: ({_fmt_num(top_loc_sav) if top_loc_sav is not None else 'N/A'})/({_fmt_num(top_loc_cost) if top_loc_cost is not None else 'N/A'})"
                result_loc = f"Result: {top_loc_sav_pct:.2f}% at {top_loc_name}" if top_loc_sav_pct is not None else "Result: N/A"

                st.markdown(f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate toolsets by region | Phase 1: Catalogue all monitoring, backup, security, and management tools used at each location and identify overlap where multiple tools provide similar capabilities.<br><br>Phase 2: Select preferred tools for each function and work with vendors and internal teams to remove duplicated contracts and migrate remaining workloads onto the chosen platforms.<br><br>Phase 3: Negotiate licenses and support based on regional or global volumes and keep an updated register of tools and contracts by site.<br><br> | - Reduces duplicate licensing because the same function is no longer paid for through several tools in the same region.<br><br>- Simplifies vendor management and renewal cycles since fewer suppliers and contracts must be tracked and negotiated.<br><br>- Lowers recurring overhead for operations teams who can focus on mastering a smaller set of tools instead of many fragmented solutions.<br><br>- Improves data consistency and reporting quality because monitoring and management data come from unified sources instead of mismatched systems.<br><br> | {formula_total}<br>{dataset_total}<br>{result_total}<br>Breakdown (Top by Cost):<br>{breakdown_loc_text} | {ev_text_loc} |
| Relocate low-utilization assets | Phase 1: Identify assets at each location that show consistently low utilization and consider whether they can be consolidated into more efficient or cheaper sites.<br><br>Phase 2: Plan and execute the relocation of these workloads, ensuring that network latency, regulatory constraints, and user access patterns remain acceptable after the move.<br><br>Phase 3: Monitor capacity, cost, and performance at both source and target locations to confirm that the relocation delivered the expected improvements.<br><br> | - Lowers hosting and energy cost by moving lightly used assets into locations that operate more efficiently or at lower price points.<br><br>- Optimizes resource placement so that high demand sites host the workloads that truly need local presence while others are centralized.<br><br>- Improves overall density and reduces stranded capacity scattered across many sites that are expensive to maintain.<br><br>- Simplifies operational support by reducing the number of locations where specialist skills or spares must be maintained.<br><br> | {formula_loc}<br>{dataset_loc}<br>{result_loc} | Cost dispersion (box plot) highlights expensive regions for similar workloads. |
| Decommission obsolete nodes | Phase 1: Detect assets at each site that show no meaningful CPU, memory, or network activity over an extended period and flag them as candidates for retirement.<br><br>Phase 2: Confirm with application and business owners that these nodes are no longer supporting critical functions, batch jobs, or emergency fallbacks.<br><br>Phase 3: Retire obsolete nodes in a controlled manner, including wiping data, updating asset records, and stopping related maintenance and monitoring tasks.<br><br> | - Delivers immediate operating expense reduction because powered but unused assets no longer consume energy, cooling, or support effort.<br><br>- Reduces the attack surface since machines that are forgotten are often poorly patched and more vulnerable to security issues.<br><br>- Decreases complexity in the environment which makes troubleshooting, capacity planning, and change testing simpler and faster.<br><br>- Keeps the configuration management database and asset inventories more accurate, which improves trust in reporting and decision making.<br><br> | Formula: Savings = Count_retired × Avg cost/asset (per location)<br>Dataset: uses grouped averages from uploaded data | Bottom quartile costs indicate idle/old assets to retire. |
| Energy optimization by site | Phase 1: Compare energy consumption, cooling efficiency, and power usage effectiveness metrics across locations and identify sites with weaker efficiency or older infrastructure.<br><br>Phase 2: Shift energy intensive workloads to sites with better efficiency where feasible and implement power saving configurations such as dynamic frequency scaling or deeper sleep states.<br><br>Phase 3: Validate measured energy usage and cost reductions and refine placement policies to prioritize the most efficient sites for new workloads.<br><br> | - Lowers power spend by running compute workloads in locations where energy is used more efficiently or costs less per unit.<br><br>- Improves sustainability indicators by reducing the total energy footprint and supporting organizational environmental targets.<br><br>- Often improves hardware longevity because better cooling and power conditions reduce wear and tear on components.<br><br>- Provides clearer data for future consolidation or investment decisions when modernizing or closing older sites.<br><br> | {formula_total}<br>{dataset_total}<br>Result: portion of total savings attributable to energy-heavy sites | High-cost sites likely correlate with higher energy overhead. |
| Tiered storage deployment | Phase 1: Classify data at each location into hot, warm, and cold categories based on access frequency, performance needs, and compliance requirements.<br><br>Phase 2: Move cold and archival data onto cheaper, slower storage tiers while keeping hot transactional data on high performance media close to the applications.<br><br>Phase 3: Review access logs regularly to catch newly cold data and move it into cheaper tiers, ensuring that policies remain up to date.<br><br> | - Reduces storage run rate by ensuring that expensive high performance storage is reserved for data that truly needs fast access.<br><br>- Preserves application performance because critical databases and logs stay on appropriately fast storage tiers.<br><br>- Improves lifecycle control for data, making it easier to comply with retention policies and planned deletion schedules.<br><br>- Helps avoid surprise storage bills because growth in low value data is redirected into cost efficient tiers rather than premium arrays.<br><br> | {formula_loc}<br>{dataset_loc}<br>{result_loc} | Regional disparity indicates uneven storage economics. |
                """, unsafe_allow_html=True)

            with st.expander("Performance Improvement Recommendations"):
                total_inc = int(df["incident_count"].sum()) if have_inc else None
                total_down = int(df["downtime_minutes"].sum()) if have_down else None
                perf_formula = "Formula: Risk Proxy = Σ(incident_count) + Σ(downtime_minutes)"
                perf_dataset = f"Dataset: incidents={total_inc if total_inc is not None else 'N/A'} / downtime_minutes={total_down if total_down is not None else 'N/A'}"
                perf_result = "Result: Higher proxy → higher instability; prioritize top-concentration regions."

                st.markdown(f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Regional change management | Phase 1: Define a clear change management standard for each site, including required approvals, testing evidence, and rollback plans tailored to the risk profile of that location.<br><br>Phase 2: Audit real changes against this standard and coach local teams where deviations occur so that practice aligns with the written process.<br><br>Phase 3: Review change success rates and incident patterns monthly and adjust procedures where necessary to improve stability without blocking useful changes.<br><br> | - Reduces missteps and outages triggered by inconsistent or ad hoc change practices at different locations.<br><br>- Makes releases more predictable because teams follow the same tested pattern when deploying new configurations or hardware.<br><br>- Strengthens operational control by clarifying responsibilities and expectations for local and central teams.<br><br>- Provides traceable evidence of due diligence which supports audits and internal governance requirements.<br><br> | {perf_formula}<br>{perf_dataset}<br>{perf_result} | High-asset sites need stricter control for stability. |
| Capacity alerts by location | Phase 1: Establish capacity thresholds for each site that reflect its size, criticality, and business usage, and configure monitoring to track them.<br><br>Phase 2: Link alerts to automated scaling actions or operator runbooks so that when thresholds are crossed teams know exactly what to do.<br><br>Phase 3: Tune thresholds and responses quarterly based on false alarms, missed events, and evolving demand patterns to keep alerts actionable.<br><br> | - Prevents overloads at busy sites because capacity is adjusted or traffic is reshaped before severe degradation occurs.<br><br>- Protects service levels by ensuring that local capacity constraints are visible and acted on in near real time.<br><br>- Reduces firefighting and emergency calls when predictable peaks hit sites that are already known to be tight on resources.<br><br>- Creates a feedback loop which continuously improves alert quality and reduces noise for on call staff.<br><br> | {perf_formula}<br>{perf_dataset}<br>{perf_result} | Site concentration makes alerts high ROI. |
| Hot–cold workload segregation | Phase 1: Identify which locations and time windows experience the highest contention for compute, storage, or network resources and categorize workloads as hot interactive or cold batch at each site.<br><br>Phase 2: Reschedule or relocate cold, non urgent jobs so they run during off peak times or in less constrained locations where they cause minimal interference.<br><br>Phase 3: Validate throughput, latency, and incident trends to confirm that peak periods are smoother and user facing performance is improved.<br><br> | - Smooths compute and network load over time which makes performance outcomes more stable and predictable for users.<br><br>- Reduces contention between background processing and interactive workloads at busy sites.<br><br>- Improves response times for critical applications during business hours when user expectations are highest.<br><br>- Allows more work to be completed on the same hardware footprint by using quiet periods more effectively.<br><br> | Formula: Downtime Avoided = ΔDowntime × Cost/min<br>Dataset: downtime_minutes aggregated per location | Location bars show where balancing matters most. |
| Patch orchestration per region | Phase 1: Group locations into logical regions and design patch waves that reflect regional differences in working hours, risk appetite, and support coverage.<br><br>Phase 2: Use canary nodes in each region to validate new patches before wider rollout and prepare fallback plans that consider regional dependencies.<br><br>Phase 3: Review patch incidents and near misses by region and refine scheduling, sequencing, and testing to continuously reduce impact.<br><br> | - Reduces downtime from patch failures because each region benefits from controlled testing before full rollout.<br><br>- Speeds recovery when issues do arise since rollback and response plans are tailored to the region and rehearsed in advance.<br><br>- Increases stability as regional patterns of risk and demand are explicitly considered in the patch strategy.<br><br>- Improves collaboration between central teams and regional operations by clarifying how global changes flow through local environments.<br><br> | Formula: ΔIncidents × MTTR Reduction<br>Dataset: incident_count & downtime_minutes trends by site | Incident/downtime clustering validates priority regions. |
| QoS enforcement | Phase 1: Identify critical user flows and services per location and classify them into higher and lower priority traffic classes.<br><br>Phase 2: Implement quality of service rules on networks, load balancers, and application tiers so that high priority traffic is favored during contention.<br><br>Phase 3: Monitor SLA adherence and user experience metrics to check that QoS rules are delivering improvements without starving lower priority workloads unnecessarily.<br><br> | - Stabilizes end user experience by protecting key services from congestion when resources or bandwidth are limited.<br><br>- Lowers latency spikes for the most important transactions which directly improves satisfaction and business outcomes.<br><br>- Reduces escalations during busy events because critical functions remain usable even if less important services slow down.<br><br>- Provides a structured way to make trade offs under resource pressure instead of relying on improvised manual interventions.<br><br> | {perf_formula}<br>{perf_dataset}<br>{perf_result} | Cost dispersion suggests uneven performance conditions. |
                """, unsafe_allow_html=True)

            with st.expander("Customer Satisfaction Recommendations"):
                cs_formula = "Formula: Savings Impact = Σ(potential_savings_usd) ÷ Σ(cost_per_month_usd) × 100 (reinvestment into quality)"
                cs_dataset = f"Dataset: ({_fmt_num(total_sav_all)})/({_fmt_num(total_cost_all)})"
                cs_result = f"Result: {avg_sav_pct_all:.2f}% headroom that can be reinvested into reliability/comms"

                st.markdown(f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish regional uptime | Phase 1: Measure uptime and key reliability metrics for each location separately so that variations in user experience are visible rather than averaged away.<br><br>Phase 2: Publish these regional figures on a regular cadence in a format that business and customers can easily understand.<br><br>Phase 3: Track trends over time and call out regions that are improving or degrading along with the actions being taken.<br><br> | - Increases trust because users can see honest visibility into the quality of service they receive at their primary location.<br><br>- Reduces complaints that are based on perception rather than data since uptime and performance are clearly reported.<br><br>- Clarifies expectations by showing which regions are more resilient and which are still being improved.<br><br>- Supports targeted investment discussions because underperforming regions become obvious focal points for improvement budgets.<br><br> | {cs_formula}<br>{cs_dataset}<br>{cs_result} | {top_loc_name} hosts {int(top_loc['asset_id']):,} assets ({share_top:.2f}%); visibility here impacts most users. |
| Site-based SLA tiers | Phase 1: Define SLA tiers that reflect the criticality of services and locations, such as core data centers versus smaller branch sites.<br><br>Phase 2: Map services and customers to these tiers so that response times and support models are aligned with business value and risk tolerance.<br><br>Phase 3: Report against these tiered SLAs each month and adjust mappings when business priorities change.<br><br> | - Aligns service commitments to business importance rather than treating all locations and workloads as equal.<br><br>- Enables faster response for critical users and services that generate the most impact and revenue.<br><br>- Reduces escalations from lower tier sites because expectations are set realistically and communicated clearly.<br><br>- Gives operations teams a framework to triage incidents when multiple locations compete for attention.<br><br> | {cs_formula}<br>{cs_dataset}<br>{cs_result} | Concentration justifies differentiated SLAs. |
| Maintenance notifications | Phase 1: Plan location specific maintenance schedules and publish user friendly notifications that explain what will happen, when, and what impact is expected.<br><br>Phase 2: Provide progress updates during the maintenance window through agreed channels so users are not left guessing about status.<br><br>Phase 3: Share short post event summaries that confirm completion and highlight any user facing changes or improvements.<br><br> | - Reduces perceived disruption because users can plan work around maintenance windows they know about in advance.<br><br>- Improves satisfaction by replacing surprise outages with predictable and well communicated events.<br><br>- Manages expectations by explaining the purpose and benefits of maintenance activities instead of leaving them opaque.<br><br>- Helps support teams handle fewer inbound tickets asking whether the system is down because status is already visible and explained.<br><br> | Formula: Complaints Avoided × Handling Cost<br>Dataset: compare pre/post maintenance incident trends at location | Cost/variance suggests timing matters by site. |
| Feedback loop by region | Phase 1: Collect regular feedback from key user groups in each location using surveys, workshops, or targeted interviews that focus on infrastructure related experience.<br><br>Phase 2: Prioritize the most common or severe issues raised in each region and create remediation tasks with clear owners and timelines.<br><br>Phase 3: Close the loop by informing users which actions were taken and how their feedback influenced the roadmap.<br><br> | - Enables targeted improvements that reflect the specific needs of each region rather than applying generic fixes everywhere.<br><br>- Accelerates customer satisfaction gains because work is focused on the pain points users mention most often.<br><br>- Strengthens relationships with local stakeholders as they see that their input leads to concrete outcomes.<br><br>- Creates a virtuous cycle of feedback and improvement where data about user experience directly shapes operations priorities.<br><br> | {cs_formula}<br>{cs_dataset}<br>{cs_result} | Regional view pinpoints weak spots to engage. |
| Redundancy communication plan | Phase 1: Document the redundancy and failover design for key locations and services in language that business stakeholders can understand.<br><br>Phase 2: Test these failovers on a regular schedule and capture results, including what users experienced and how long transitions took.<br><br>Phase 3: Share the outcomes of these tests with stakeholders along with follow up actions to improve any weak points that were discovered.<br><br> | - Builds confidence that resilience is not just a design on paper but a capability that is exercised and verified in practice.<br><br>- Reduces escalations during real incidents because users already understand how failovers are expected to behave.<br><br>- Increases loyalty by showing that the organization invests in continuity and is transparent about resilience posture.<br><br>- Informs future design and investment decisions by highlighting where redundant paths perform well and where they need strengthening.<br><br> | Formula: Outage Cost Avoided = historical downtime × business impact<br>Dataset: downtime_minutes by location | High concentration raises stakes; redundancy is critical. |
                """, unsafe_allow_html=True)

        else:
            st.info("Required columns 'location' and 'asset_id' not found in dataset.")
