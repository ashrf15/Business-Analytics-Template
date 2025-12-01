import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# 🔹 Helper to render CIO tables with 3 nested expanders (Option A format)
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def _to_num(s):
    return pd.to_numeric(s, errors="coerce")

def _fmt_cur(v):
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "N/A"

def _safe_sum(series):
    try:
        return float(_to_num(series).fillna(0).sum())
    except Exception:
        return 0.0

def _safe_mean(series):
    try:
        return float(_to_num(series).dropna().mean())
    except Exception:
        return float("nan")

def _safe_min(series):
    try:
        return float(_to_num(series).dropna().min())
    except Exception:
        return float("nan")

def _safe_max(series):
    try:
        return float(_to_num(series).dropna().max())
    except Exception:
        return float("nan")

def storage_capacity(df):

    # Prepare storage fields with graceful fallback to existing dataset columns
    df_sc = df.copy()

    # Derive capacity/used if not explicitly provided
    if "storage_capacity_tb" not in df_sc.columns and "storage_tb" in df_sc.columns:
        df_sc["storage_capacity_tb"] = _to_num(df_sc["storage_tb"])
    if "storage_used_tb" not in df_sc.columns and {"avg_storage_utilization", "storage_capacity_tb"} <= set(df_sc.columns):
        df_sc["storage_used_tb"] = (_to_num(df_sc["avg_storage_utilization"]) / 100.0) * _to_num(df_sc["storage_capacity_tb"])

    # Compute utilization pct when possible
    if {"storage_used_tb", "storage_capacity_tb"} <= set(df_sc.columns):
        df_sc["storage_utilization_pct"] = (_to_num(df_sc["storage_used_tb"]) / _to_num(df_sc["storage_capacity_tb"]).replace(0, np.nan)) * 100

    # ================
    # Subtarget 1: Storage Utilization by Asset (multiple graphs)
    # ================
    with st.expander("📌 Storage Utilization by Asset"):
        if {"asset_id", "storage_utilization_pct"} <= set(df_sc.columns):

            # Graph 1: Bar – utilization by asset
            fig_bar = px.bar(
                df_sc.sort_values("storage_utilization_pct", ascending=False),
                x="asset_id",
                y="storage_utilization_pct",
                title="Storage Utilization by Asset (%)",
                text="storage_utilization_pct",
                labels={"asset_id": "Asset", "storage_utilization_pct": "Utilization (%)"}
            )
            fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True, key="stor_asset_bar")

            # Dynamic analysis for Graph 1
            util_mean = _safe_mean(df_sc["storage_utilization_pct"])
            util_min = _safe_min(df_sc["storage_utilization_pct"])
            util_max = _safe_max(df_sc["storage_utilization_pct"])
            max_row = df_sc.loc[df_sc["storage_utilization_pct"].idxmax()]
            min_row = df_sc.loc[df_sc["storage_utilization_pct"].idxmin()]
            n_assets = int(df_sc["asset_id"].nunique())
            st.write(f"""
**What this graph is:** A ranked bar chart showing **storage utilization by asset**.  
- **X-axis:** Asset ID.  
- **Y-axis:** Utilization of provisioned capacity (%).

**What it shows in your data:** Among **{n_assets}** assets, peak utilization is **{util_max:.2f}%** on **'{max_row['asset_id']}'**, while the lowest is **{util_min:.2f}%** on **'{min_row['asset_id']}'**. The average across assets is **{util_mean:.2f}%**.

**Overall:** Taller bars signal **capacity pressure** (risk of I/O contention), while shorter bars reveal **headroom** suitable for consolidation or right-sizing.

**How to read it operationally:**  
1) **Peaks:** For top bars, plan **expansion/tiering** or redistribute hot datasets.  
2) **Plateaus:** If many bars sit high, maintain **outflow ≥ inflow** with quotas & alerts.  
3) **Downswings:** After cleanup (archival/deletion), bars should flatten—**verify impact**.  
4) **Mix:** Pair with **cost / business criticality** so hot & high-value assets get priority.

**Why this matters:** Skewed utilization is **debt**—it drives outages on hot assets and waste on cold ones. Keeping assets in a healthy band preserves **cost**, **performance**, and **satisfaction**.
""")

            # Graph 2: Histogram – utilization distribution
            fig_hist = px.histogram(
                df_sc,
                x="storage_utilization_pct",
                nbins=20,
                title="Distribution of Storage Utilization (%)",
                labels={"storage_utilization_pct": "Utilization (%)"}
            )
            st.plotly_chart(fig_hist, use_container_width=True, key="stor_asset_hist")

            # Dynamic analysis for Graph 2
            lt_30 = int((_to_num(df_sc["storage_utilization_pct"]) < 30).sum())
            gt_85 = int((_to_num(df_sc["storage_utilization_pct"]) >= 85).sum())
            st.write(f"""
**What this graph is:** A histogram of **how storage utilization is distributed** across assets.  
- **X-axis:** Utilization (%).  
- **Y-axis:** Asset count per band.

**What it shows in your data:** **{lt_30}** assets operate **<30%** (oversizing risk) and **{gt_85}** assets run **≥85%** (saturation risk). Center of mass sits near **{util_mean:.2f}%**.

**Overall:** A right-heavy tail implies **demand exceeding capacity**; a left-heavy tail highlights **excess headroom** and immediate cost opportunities.

**How to read it operationally:**  
1) **Peaks:** Bins ≥85% ⇒ trigger **tiering, rebalancing, or adds**.  
2) **Plateaus:** Stable mid-bands ⇒ keep guardrails; watch for drift.  
3) **Downswings:** After clean-ups, the right tail should shrink—**confirm**.  
4) **Mix:** Cross-tab by **asset/BU/region** to ensure critical services aren’t in the hot tail.

**Why this matters:** Extreme tails are **debt**—they inflate outage probability and wasted spend. Keeping a compact distribution protects **budget**, **throughput**, and **user confidence**.
""")

            # Graph 3: Scatter – capacity vs utilization
            if "storage_capacity_tb" in df_sc.columns:
                fig_scatter = px.scatter(
                    df_sc,
                    x="storage_capacity_tb",
                    y="storage_utilization_pct",
                    title="Provisioned Capacity (TB) vs Utilization (%)",
                    labels={"storage_capacity_tb": "Capacity (TB)", "storage_utilization_pct": "Utilization (%)"},
                    trendline="ols"
                )
                st.plotly_chart(fig_scatter, use_container_width=True, key="stor_asset_scatter")

                cap_min = _safe_min(df_sc["storage_capacity_tb"])
                cap_max = _safe_max(df_sc["storage_capacity_tb"])
                st.write(f"""
**What this graph is:** A scatter relating **provisioned capacity (TB)** to **utilization (%)**.  
- **X-axis:** Capacity (TB).  
- **Y-axis:** Utilization (%).

**What it shows in your data:** Capacity spans **{cap_min:.2f}–{cap_max:.2f} TB**. Points at **high TB/low %** reveal **oversizing**; **low TB/high %** indicates **tight headroom** needing close monitoring or incremental expansion.

**Overall:** The farther points sit from a healthy band, the greater the mismatch between **what’s provisioned** and **what’s actually used**.

**How to read it operationally:**  
1) **Peaks:** High-capacity & low-use ⇒ **shrink/tier** volumes.  
2) **Plateaus:** Consistent bands ⇒ maintain policy; validate quota efficacy.  
3) **Downswings:** After right-sizing, expect a drift toward balanced zone—**verify**.  
4) **Mix:** Overlay **I/O latency** to confirm business impact before action.

**Why this matters:** Misaligned capacity is **debt**. You pay for TBs that don’t deliver value or risk running hot where it matters. Alignment preserves **cost**, **performance**, and **resilience**.
""")

            # CIO tables for this subtarget
            total_cost = _safe_sum(df_sc["cost_per_month_usd"]) if "cost_per_month_usd" in df_sc.columns else 0.0
            total_sav = _safe_sum(df_sc["potential_savings_usd"]) if "potential_savings_usd" in df_sc.columns else 0.0
            low_cost_sum = _safe_sum(df_sc.loc[_to_num(df_sc["storage_utilization_pct"]) < 30, "cost_per_month_usd"]) if "cost_per_month_usd" in df_sc.columns else 0.0
            low_sav_sum = _safe_sum(df_sc.loc[_to_num(df_sc["storage_utilization_pct"]) < 30, "potential_savings_usd"]) if "potential_savings_usd" in df_sc.columns else 0.0

            cio_util = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Tier cold data to lower-cost storage | Phase 1: Identify assets that consistently operate below 30% utilization by using the histogram and asset level utilization values so that you have a clear list of low-use storage candidates. Validate with application owners that the data on these assets is genuinely cold or infrequently accessed and confirm that retention and compliance rules allow tiering or archival. <br><br>**Phase 2 :** Move appropriately classified cold datasets to lower-cost archival or nearline tiers while keeping catalog entries and metadata so that restores are still possible if business needs change. Coordinate moves in controlled batches and monitor for unexpected access patterns that might indicate misclassification. <br><br>**Phase 3 :** Review access logs, growth patterns and cost reports monthly to ensure that data remains in the correct tier and adjust policies if access behaviour, regulations or business priorities change. | - Delivers direct monthly storage cost reduction because low-use and cold datasets are relocated from expensive primary tiers to cheaper archival or nearline tiers.<br><br>- Reduces pressure on high performance arrays so that expensive capacity can be reserved for active transactional and analytical workloads that truly require fast I/O.<br><br>- Improves the sustainability and efficiency of the storage estate because energy, cooling and backup resources are not wasted on rarely used data sitting on premium media.<br><br> | Formula: Savings Ratio = Σ potential_savings_usd ÷ Σ cost_per_month_usd for <30%. Dataset: {_fmt_cur(low_sav_sum)} ÷ {_fmt_cur(low_cost_sum)} = {(low_sav_sum/low_cost_sum if low_cost_sum else 0):.2f}. | Histogram shows {lt_30} assets under 30% and bar chart highlights low-use assets by ID. |
| Right-size oversized volumes | Phase 1: Compare used storage against provisioned capacity for each asset to identify volumes where a large portion of allocated space is consistently unused. Confirm with workload and database owners that there are no upcoming projects or growth events that would justify keeping the current size. <br><br>**Phase 2 :** For safe candidates, shrink or re provision volumes according to platform capabilities so that logical and physical capacity are better aligned with actual demand. Implement quotas or size templates to prevent rapid re expansion without proper review. <br><br>**Phase 3 :** Enforce quotas for users and applications and periodically reassess usage to ensure that right sized volumes stay within expected ranges over time. | - Reduces spend on storage that is allocated but never genuinely used because oversized volumes are brought down closer to real consumption levels.<br><br>- Lowers backup and replication overhead since smaller volumes generate fewer bytes to protect and transfer during routine protection cycles.<br><br>- Simplifies future capacity planning because the estate reflects realistic working sets instead of inflated allocations that mask true growth trends.<br><br> | Formula: Over-provisioned TB × $/TB per month. Dataset: scatter exhibits low utilization at higher TB sizes. | Capacity–utilization scatter identifies oversizing clusters. |
| Consolidate storage on denser arrays | Phase 1: Use utilization and capacity data to build a pool of low-use or modest-use assets that can be migrated onto newer, denser or more efficient storage arrays without compromising performance or resilience. Engage platform and application teams to agree which workloads can move together. <br><br>**Phase 2 :** Execute migrations in planned waves so that selected workloads are consolidated onto fewer arrays, and freed devices are placed into a decommission or repurpose queue. Ensure that data protection, monitoring and performance baselines are validated after each wave. <br><br>**Phase 3 :** After consolidation, power down or reassign freed devices and update inventory, support contracts and monitoring systems so that retired hardware no longer consumes effort or budget. Validate backup and recovery processes on the new consolidated platforms. | - Cuts hardware and maintenance costs because old or inefficient arrays can be retired, reused for non production workloads or removed from support altogether.<br><br>- Lowers power and cooling consumption by reducing the number of active devices needed to deliver the same logical capacity and performance levels.<br><br>- Streamlines operational support as teams manage a smaller, more standardised set of platforms with consistent firmware, tooling and runbooks.<br><br> | Formula: Devices avoided × Cost/device per month. Dataset: {lt_30} sub-30% assets represent consolidation candidates. | Histogram left tail and bar ranks quantify consolidation pool. |
| Policy-driven lifecycle management | Phase 1: Classify datasets by age, business value and access frequency so that data is clearly labelled as hot, warm, cold or regulatory and suitable retention periods are defined. Document these policies and agree them with legal, risk and business stakeholders. <br><br>**Phase 2 :** Implement retention, archival and deletion rules within storage, backup and application platforms so that stale or obsolete data is automatically transitioned or removed according to policy. Ensure that audit trails are available for compliance checks. <br><br>**Phase 3 :** Automate lifecycle enforcement through scheduled jobs and regular reviews and refine rules based on observed growth patterns, exceptions and new regulatory requirements. | - Slows uncontrolled storage growth because obsolete and low value data is systematically archived or removed instead of being kept indefinitely on expensive primary tiers.<br><br>- Reduces legal and compliance risk by ensuring that records are retained for the correct duration and that sensitive data is not stored longer than necessary.<br><br>- Improves storage hygiene and transparency since teams have a clear understanding of what data is stored where and why, enabling faster impact analysis and problem resolution.<br><br> | Formula: TB archived × $/TB per month. Dataset: low-use assets indicate stale data presence. | Utilization distribution evidences cold datasets. |
| Deduplication and compression | Phase 1: Identify workloads and storage pools containing large amounts of duplicate or highly compressible data and confirm platform support for deduplication and compression features. Engage application and backup owners to agree on enablement plans. <br><br>**Phase 2 :** Enable appropriate data reduction technologies on selected volumes or arrays and track reduction ratios to understand the effectiveness of each policy. Adjust scope based on performance impact and achieved savings. <br><br>**Phase 3 :** Re tune data reduction settings and extend or narrow coverage on a quarterly basis according to observed patterns so that benefits are maximised without impacting application behaviour. | - Lowers effective capacity requirements because the same logical data footprint consumes fewer physical terabytes once duplicates and redundant patterns are removed or compressed.<br><br>- Delays or avoids future hardware purchases as improved data reduction ratios free up existing capacity and stretch the useful life of current arrays.<br><br>- Reduces backup and replication bandwidth requirements because smaller data sets generate fewer bytes to move across networks and into secondary locations.<br><br> | Formula: Δ effective TB × $/TB per month. Dataset: wide dispersion of utilization suggests compressible datasets. | Spread across bands supports reduction opportunity. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Expand capacity for high-risk assets | Phase 1: Use the utilization metrics to flag assets that operate at or above 85% and confirm which of these host performance sensitive or business critical workloads. Document this list as a high-risk queue. <br><br>**Phase 2 :** For these assets, add physical capacity, move data to faster tiers or split workloads so that utilization is brought back into a healthy band before saturation leads to incidents. Coordinate changes with change management and application owners. <br><br>**Phase 3 :** After expansion, measure latency, I/O wait times and incident rates to confirm that user experience has improved and that utilisation now remains within agreed thresholds. | - Reduces the likelihood of I/O bottlenecks and storage related outages by giving the most heavily loaded assets enough headroom to handle demand peaks.<br><br>- Improves end user response times for applications that rely on these high-risk assets because read and write operations are no longer constrained by full or fragmented volumes.<br><br>- Supports more predictable service levels for critical workloads since storage saturation is addressed proactively rather than after performance incidents occur.<br><br> | Formula: Δ latency × I/O volume. Dataset: {gt_85} assets at or above 85% utilization. | Bar ranking exposes peak asset '{max_row['asset_id']}' at {util_max:.2f}%. |
| I/O workload balancing | Phase 1: Analyse utilization, I/O patterns and latency across arrays and volumes to identify where hot workloads are concentrated together and causing localised contention. Document which applications or services are responsible. <br><br>**Phase 2 :** Rebalance workloads by redistributing hot paths across multiple arrays or storage pools and separating noisy neighbours so that no single asset is overloaded. Validate that application dependencies and failover paths remain intact. <br><br>**Phase 3 :** Monitor queue depth, latency and throughput after changes to confirm that I/O has become more evenly distributed and adjust placement rules or templates based on the results. | - Improves overall throughput by spreading I/O intensive workloads across multiple arrays instead of allowing a small number of devices to become choke points.<br><br>- Reduces performance variability for users because storage latency spikes are less frequent when busy workloads are separated and balanced properly.<br><br>- Gives operations teams better resilience against unexpected spikes in individual applications since I/O load can be shifted away from stressed assets more easily.<br><br> | Formula: Δ queue depth × business impact. Dataset: scatter highlights high-utilization pockets on specific capacities. | Scatter trendline reveals imbalance signs. |
| Proactive threshold alerts | Phase 1: Define utilisation and latency thresholds such as 75, 85 and 90 percent that represent warning and critical levels for storage health and configure alerts accordingly. Align thresholds with vendor guidance and internal risk appetite. <br><br>**Phase 2 :** Link these alerts to concrete actions such as tiering data, rebalancing workloads or provisioning more capacity so that every alert leads to a structured response rather than noise. Ensure on call teams know the runbooks. <br><br>**Phase 3 :** Review alert history and follow up actions monthly to fine tune thresholds, remove redundant rules and ensure that alerts correlate with real risk rather than generating unnecessary noise. | - Reduces unexpected storage incidents by surfacing capacity and performance problems early while there is still time to remediate them calmly.<br><br>- Lowers operational stress and improves response quality because teams can follow predefined steps instead of improvising under pressure when volumes suddenly run full.<br><br>- Enhances observability and governance as capacity, utilisation and performance metrics are tied directly to alerts and documented mitigation actions.<br><br> | Formula: Outage cost avoided via preemption. Dataset: right-tail assets emphasize alert need. | Histogram tail validates threshold placement. |
| Golden storage policies | Phase 1: Define clear gold, silver and bronze storage classes that specify performance, resilience and cost characteristics and ensure all stakeholders understand when each class should be used. Document these standards in design guidelines. <br><br>**Phase 2 :** Map existing workloads to the appropriate classes and gradually realign mis placed datasets so that critical workloads run on gold or silver and less sensitive ones on bronze. Capture exceptions explicitly. <br><br>**Phase 3 :** Audit policies regularly to detect drift where workloads have moved or grown without policy updates and correct these gaps before they lead to performance or cost problems. | - Creates predictable performance and availability for different categories of workloads because each class has well understood characteristics and commitments.<br><br>- Prevents over engineering by ensuring that non critical workloads do not consume premium gold tier capacity that should be reserved for high impact services.<br><br>- Simplifies communication with business units as storage offerings can be described in standard classes rather than in many ad hoc configurations and exceptions.<br><br> | Formula: SLA gain × transaction volume. Dataset: dispersion across utilization bands suggests policy inconsistency. | Distribution spread supports standardization. |
| Snapshot and replication optimization | Phase 1: Review snapshot and replication schedules for each dataset and align frequency and retention with data change rates and business requirements so that protection matches actual risk. Document recommended schedules by data class. <br><br>**Phase 2 :** Prune stale or redundant snapshots that are no longer needed for operational or compliance purposes and adjust replication targets where copies exceed realistic recovery needs. <br><br>**Phase 3 :** Automate retention enforcement and reassess schedules on a regular basis to ensure they remain optimal as workloads evolve and new regulations or risk appetites emerge. | - Reduces consumed capacity by deleting snapshots and replicas that no longer have business or compliance value which immediately frees storage space.<br><br>- Lowers replication bandwidth and backup windows because fewer redundant copies need to be transferred and processed during protection cycles.<br><br>- Improves recovery efficiency since backup sets and replicas are cleaner, smaller and better aligned with current restore objectives and testing practices.<br><br> | Formula: Δ snapshot TB × $/TB per month. Dataset: low-use volumes accumulate excess snapshots. | Low-utilization assets prone to redundant copies. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate capacity posture to stakeholders | Phase 1: Publish simple monthly storage utilization scorecards that highlight overall usage, growth and risk areas so that non technical stakeholders can see the storage status at a glance. Include key messages on risk and planned actions. <br><br>**Phase 2 :** Explicitly flag assets and services that sit above agreed utilisation thresholds and explain what remediation steps and timelines are in place for each of them. <br><br>**Phase 3 :** Track how these actions reduce risk over time and update the scorecards so that stakeholders can see progress and understand when issues have been resolved. | - Builds trust with business and leadership teams because storage risks and remediation plans are clearly communicated rather than hidden in technical tools.<br><br>- Reduces the number of escalations and urgent queries as stakeholders already understand which areas are under control and which are being actively managed.<br><br>- Helps align expectations about capacity upgrades and maintenance windows since stakeholders can see why changes are needed and when they are likely to occur.<br><br> | Formula: Complaints avoided × handling cost. Dataset: {gt_85} assets above 85% presented as risk list. | Bar and histogram clearly illustrate risk distribution. |
| Prioritize critical services during growth | Phase 1: Tag datasets and volumes that underpin critical business services and customer facing applications so that they can be easily distinguished in reports and dashboards. Validate tags with business owners. <br><br>**Phase 2 :** Reserve additional capacity headroom and apply stricter monitoring and alerting for these tagged resources so that they are less likely to experience storage related performance problems during growth periods. <br><br>**Phase 3 :** Monitor SLOs and user experience metrics for these critical services and adjust capacity or policies whenever early signs of degradation appear. | - Protects the performance and stability of services that have the greatest impact on customers and revenue when storage contention occurs.<br><br>- Gives business stakeholders confidence that their most important systems are explicitly prioritised in storage plans instead of competing silently with less critical workloads.<br><br>- Improves customer satisfaction and retention because key user journeys remain smooth even when overall storage demand is increasing across the estate.<br><br> | Formula: Δ SLA adherence × value per service. Dataset: peak asset '{max_row['asset_id']}' at {util_max:.2f}% warrants priority. | Peak identification links to business impact. |
| Post-change transparency | Phase 1: After significant storage optimisation or capacity changes, share before and after utilisation and performance metrics with stakeholders in plain language so that the impact of the work is obvious. Include key graphs from the dashboards. <br><br>**Phase 2 :** Collect feedback from users and business owners about perceived performance changes and link their comments to specific technical actions taken on storage. <br><br>**Phase 3 :** Use this feedback loop to refine future optimisation priorities and communication styles so that stakeholders continue to see value and feel informed. | - Improves perception of reliability because stakeholders can see that changes to storage are producing visible, measurable improvements rather than introducing new problems.<br><br>- Encourages constructive collaboration between technical teams and business users since both groups share the same view of before and after conditions.<br><br>- Supports ongoing investment in storage optimisation by providing clear evidence of benefits delivered in terms that non technical decision makers can understand.<br><br> | Formula: CSAT uplift × user base. Dataset: distribution shift after right-sizing visible in histogram. | Visuals validate measurable improvements. |
"""
            }
            render_cio_tables("Storage Utilization by Asset — CIO Recommendations", cio_util)

        else:
            st.info("Required columns for utilization by asset not found. Provide 'asset_id', 'storage_capacity_tb' and either 'storage_used_tb' or 'avg_storage_utilization' with 'storage_capacity_tb'.")

    # ================
    # Subtarget 2: Storage Growth Trend (multiple graphs)
    # ================
    with st.expander("📌 Storage Growth Trend"):
        # Build a date field for trend: prefer 'date', else 'data_timestamp' at daily, then roll up monthly
        df_tr = df_sc.copy()
        date_col = None
        if "date" in df_tr.columns:
            df_tr["date"] = pd.to_datetime(df_tr["date"], errors="coerce")
            date_col = "date"
        elif "data_timestamp" in df_tr.columns:
            df_tr["date"] = pd.to_datetime(df_tr["data_timestamp"], errors="coerce")
            date_col = "date"

        if date_col and "storage_used_tb" in df_tr.columns:
            # Graph 1: Monthly total used TB
            monthly = (
                df_tr.dropna(subset=[date_col, "storage_used_tb"])
                .assign(month=lambda x: x[date_col].dt.to_period("M"))
                .groupby("month", as_index=False)["storage_used_tb"].sum()
            )
            monthly["month"] = monthly["month"].astype(str)
            fig_trend = px.line(
                monthly,
                x="month",
                y="storage_used_tb",
                title="Monthly Storage Consumption (TB)",
                labels={"month": "Month", "storage_used_tb": "Total Used (TB)"}
            )
            fig_trend.update_traces(mode="lines+markers")
            st.plotly_chart(fig_trend, use_container_width=True, key="stor_growth_monthly")

            # Dynamic analysis for Graph 1
            total_tb = float(monthly["storage_used_tb"].sum()) if not monthly.empty else 0.0
            avg_tb = float(monthly["storage_used_tb"].mean()) if not monthly.empty else 0.0
            max_row = monthly.loc[monthly["storage_used_tb"].idxmax()] if not monthly.empty else {"month": "-", "storage_used_tb": 0}
            min_row = monthly.loc[monthly["storage_used_tb"].idxmin()] if not monthly.empty else {"month": "-", "storage_used_tb": 0}
            st.write(f"""
**What this graph is:** A line chart of **storage consumption over time** (monthly).  
- **X-axis:** Calendar month.  
- **Y-axis:** Total used storage (TB).

**What it shows in your data:** Peak month **{max_row['month']}** at **{float(max_row['storage_used_tb']):.2f} TB**; lowest month **{min_row['month']}** at **{float(min_row['storage_used_tb']):.2f} TB**. Across the period, consumption totals **{total_tb:.2f} TB** (avg **{avg_tb:.2f} TB/month**).

**Overall:** A rising curve indicates **demand outpacing cleanup** (growth pressure), while a flat or falling curve signals **effective lifecycle management** (archival/tiering/deletion).

**How to read it operationally:**  
1) **Peaks:** Schedule **capacity adds/tiering** ahead of peak windows.  
2) **Plateaus:** Maintain retention & quota controls; monitor drift.  
3) **Downswings:** Validate which policies (archival, snapshot pruning) worked.  
4) **Mix:** Pair with **business events** to explain inflections (releases, onboarding).

**Why this matters:** Unchecked growth is **debt**. The higher the curve, the costlier each month becomes—capacity rush, latency, and unhappy users. Keeping growth in control preserves **budget**, **performance**, and **trust**.
""")

            # Graph 2: Monthly growth (first difference)
            growth_neg = 0
            growth_pos = 0
            growth_max = 0.0
            growth_min = 0.0

            if len(monthly) >= 2:
                monthly["growth_tb"] = monthly["storage_used_tb"].diff()
                fig_growth = px.bar(
                    monthly,
                    x="month",
                    y="growth_tb",
                    title="Month-over-Month Storage Growth (TB)",
                    labels={"month": "Month", "growth_tb": "Δ Used (TB)"}
                )
                st.plotly_chart(fig_growth, use_container_width=True, key="stor_growth_mom")

                # Dynamic analysis for Graph 2
                growth_max = float(monthly["growth_tb"].max(skipna=True))
                growth_min = float(monthly["growth_tb"].min(skipna=True))
                growth_pos = int((monthly["growth_tb"] > 0).sum())
                growth_neg = int((monthly["growth_tb"] < 0).sum())
                st.write(f"""
**What this graph is:** A bar chart of **month-over-month (MoM) change** in storage used.  
- **X-axis:** Calendar month.  
- **Y-axis:** Change in used storage (Δ TB).

**What it shows in your data:** Largest MoM **increase** **{growth_max:.2f} TB**, largest **decrease** **{growth_min:.2f} TB**. Count of growth months: **{growth_pos}**; reduction months: **{growth_neg}**.

**Overall:** Positive bars indicate **net accumulation** (pressure building), while negative bars show **effective cleanup** (policy impact).

**How to read it operationally:**  
1) **Peaks:** Investigate spikes—enable **tiering, dedupe, compression**.  
2) **Plateaus:** If changes hover near zero, keep policies steady and track seasonality.  
3) **Downswings:** After interventions, expect more negative/neutral bars—**confirm success**.  
4) **Mix:** Correlate with **snapshot/backup schedules** and ingestion events.

**Why this matters:** Volatile growth is **debt**—it triggers emergency adds and user pain. Smoothing MoM change safeguards **cost**, **resilience**, and **experience**.
""")
            else:
                st.info("Insufficient data points (<2 months) to compute month-over-month growth trend.")


            # CIO tables for this subtarget
            gt85_now = int((_to_num(df_sc.get("storage_utilization_pct", pd.Series([]))) >= 85).sum()) if "storage_utilization_pct" in df_sc.columns else 0
            util_mean_all = _safe_mean(df_sc.get("storage_utilization_pct", pd.Series([]))) if "storage_utilization_pct" in df_sc.columns else float("nan")

            cio_growth = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Archive and delete stale data | Phase 1: Use last access timestamps, business ownership and application logs to identify datasets that have not been read or updated for a long period and can be considered cold or obsolete. Validate with data owners that these datasets are safe to move or remove based on retention and regulatory requirements. <br><br>**Phase 2 :** Move cold but required data into archival tiers and delete obsolete data that no longer has business, legal or operational value while keeping appropriate audit trails. Execute this work in controlled batches and monitor for unexpected access spikes. <br><br>**Phase 3 :** Review archival and deletion activity monthly so that you can confirm which months show reduced growth and refine the criteria if too much or too little data is being archived or removed. | - Slows down the rate of storage consumption by ensuring that obsolete and low value data does not continue to accumulate on primary or high cost tiers.<br><br>- Reduces recurring storage costs because archived data sits on cheaper media and deleted data no longer consumes any capacity at all.<br><br>- Lowers risk and complexity for compliance and discovery exercises since the overall volume of retained data is smaller and more relevant to current business needs.<br><br> | Formula: TB archived × $/TB per month. Dataset: months with negative growth ({growth_neg}) confirm archival effectiveness windows. | Month-over-month chart shows reductions alongside growth bursts. |
| Optimize backup and snapshot schedules | Phase 1: Map current backup and snapshot schedules for key systems and compare their frequency and retention to data change rates and business recovery requirements. Identify where protection is significantly more aggressive than necessary. <br><br>**Phase 2 :** Right size backup frequency, retention periods and snapshot schedules for each dataset so that protection is adequate without generating unnecessary data growth. Remove or shorten schedules that no longer match real risk or regulatory needs. <br><br>**Phase 3 :** Monitor backup sizes, snapshot counts and restoration test results to ensure that optimised schedules still meet recovery objectives and adjust configurations as workloads and regulations evolve. | - Cuts capacity used by backups and snapshots because redundant or overly frequent copies are reduced to what is actually required for recovery and compliance.<br><br>- Shortens backup windows and replication times since there is less data to process during each protection cycle which reduces operational impact on production workloads.<br><br>- Simplifies recovery testing and incident response because protection sets are leaner, more current and easier to navigate when restores are needed.<br><br> | Formula: Δ snapshot TB × $/TB per month. Dataset: spikes of {float(max_row['storage_used_tb']):.2f} TB indicate periods to tune protection policies. | Monthly total trend highlights peak accumulation periods. |
| Implement cost-aware tiering | Phase 1: Define clear thresholds and rules that determine when data should move from hot to warm and from warm to cold tiers based on age, frequency of access and performance requirements. Document these rules and validate them with business and risk teams. <br><br>**Phase 2 :** Automate tier movements using storage or data management tools so that data is moved according to policy without heavy manual intervention. Monitor initial runs closely to catch misclassifications early. <br><br>**Phase 3 :** Track realised cost savings and performance outcomes over time and adjust tier rules if some data types are moved too aggressively or not aggressively enough. | - Places data on the lowest cost tier that can still meet its access and performance needs which reduces overall spend on storage capacity.<br><br>- Prevents premium storage from being filled by warm and cold data because automatic tiering regularly frees space on higher tiers for genuinely hot workloads.<br><br>- Makes cost dynamics easier to explain to stakeholders since tiering rules directly link data behaviour to spend and can be shown using trend and growth charts.<br><br> | Formula: (Hot→Warm TB × Δ $/TB) + (Warm→Cold TB × Δ $/TB). Dataset: sustained growth months require tiering to control spend. | Growth curve evidences steady expansion requiring tier controls. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Capacity headroom planning | Phase 1: Use historical monthly consumption and projected business initiatives to forecast storage demand for the next three to six months so that you understand how close you are to current capacity limits. Share these forecasts with both technical and financial stakeholders. <br><br>**Phase 2 :** Plan and stage capacity expansions in smaller, incremental steps aligned to forecast needs rather than waiting for thresholds to be breached. Coordinate these additions with maintenance windows and vendor lead times. <br><br>**Phase 3 :** After expansions, validate that latency and performance remain within acceptable limits and that headroom is sufficient for seasonal peaks and unplanned demand. Update forecasts with actuals. | - Prevents storage pools from suddenly running out of space which would otherwise cause outages, emergency changes and user disruption.<br><br>- Smooths hardware or service procurement by turning unpredictable emergency purchases into planned, budgeted increments that align with growth trends.<br><br>- Improves service quality because storage performance remains stable and predictable even as data volumes increase over time.<br><br> | Formula: Peak month TB × safety factor. Dataset: peak month {max_row['month']} at {float(max_row['storage_used_tb']):.2f} TB informs headroom. | Trend clearly identifies peak demand level. |
| Balance hot datasets to fast tiers | Phase 1: Identify services and datasets that show sustained positive growth and are sensitive to performance by combining MoM growth charts with application SLOs and incident histories. <br><br>**Phase 2 :** Move these hot datasets to faster storage tiers such as SSD or NVMe pools so that access latency and throughput are aligned with business needs. Coordinate migrations to avoid impact during busy periods. <br><br>**Phase 3 :** Monitor I/O latency, throughput and user experience after the move and fine tune tier placement or caching strategies if performance targets are still not met. | - Improves response times for key applications because hot and frequently accessed data is hosted on storage that can handle high I/O volumes efficiently.<br><br>- Reduces performance incident rates for growth heavy workloads as they are less likely to be constrained by slower spinning media or overloaded tiers.<br><br>- Supports business growth and new feature rollout by ensuring that rapidly expanding datasets do not degrade the performance of critical customer journeys.<br><br> | Formula: Δ latency × I/O volume. Dataset: sequential positive growth months ({growth_pos}) suggest persistent pressure. | MoM bars show sustained increases. |
| Threshold-based early warnings | Phase 1: Establish storage utilisation thresholds for pools and arrays and configure forward looking alerts based on projected growth so that you know when capacity will be breached if current trends continue. Incorporate thresholds such as 75, 85 and 90 percent. <br><br>**Phase 2 :** Connect these alerts to predefined actions such as triggering tiering jobs, scheduling expansions or running cleanup campaigns so that responses are consistent and timely. Ensure runbooks are available to operations staff. <br><br>**Phase 3 :** Review alert patterns, false positives and missed events on a regular basis and adjust thresholds and actions to achieve a balance between early warning and alert fatigue. | - Reduces the risk of sudden storage outages due to capacity spikes because teams are notified while there is still enough time to intervene with tiering, cleanup or expansion.<br><br>- Improves operational discipline as every warning is linked to a clear response plan rather than ad hoc decisions taken under pressure at the last minute.<br><br>- Increases visibility of storage risk across the organisation which helps prioritise investments and technical work on the areas with the highest projected impact.<br><br> | Formula: Outage cost avoided via preemption. Dataset: {gt85_now} assets ≥85% utilization today. | Current right-tail risk justifies proactive alerts. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate capacity roadmap | Phase 1: Share simple monthly views of storage growth and forecast against available capacity with business stakeholders so that they understand when and why expansions are needed. Highlight any upcoming risk points. <br><br>**Phase 2 :** Publish estimated timelines for capacity additions, optimisations and risk mitigation actions and keep these dates updated as plans evolve. <br><br>**Phase 3 :** Report on outcomes after work is completed by showing updated growth curves and headroom so that stakeholders can see tangible progress against the roadmap. | - Builds confidence in service continuity because stakeholders can see that storage growth and capacity are being actively monitored and planned rather than ignored until problems occur.<br><br>- Reduces reactive escalations and urgent questions about capacity status since there is a shared, visible roadmap that explains what will happen next.<br><br>- Helps align project and release planning with infrastructure readiness so that business initiatives do not collide with unexpected capacity constraints.<br><br> | Formula: Escalations avoided × handling cost. Dataset: growth trend visualizes forward demand. | Charts provide transparent capacity posture. |
| Prioritize critical workloads during peak growth | Phase 1: Tag workloads and datasets that support critical services and map when their demand peaks relative to overall storage growth so that risk windows are clearly understood. <br><br>**Phase 2 :** Reserve explicit capacity headroom for these workloads and apply stronger growth controls to less critical areas during peak periods. Ensure governance reflects these priorities. <br><br>**Phase 3 :** Track SLOs, performance and incident patterns for the critical workloads through growth spikes and adjust capacity allocations if early signs of strain appear. | - Preserves performance and reliability for the services that are most important to customers and revenue generation during periods of rapid storage growth.<br><br>- Provides business leaders with assurance that critical workloads will not be starved of storage capacity because of background growth from lower priority systems.<br><br>- Reduces the likelihood of reputational damage and contract penalties by keeping high priority services stable even when the rest of the environment is under capacity pressure.<br><br> | Formula: Δ SLA × revenue at risk. Dataset: peaks up to {float(max_row['storage_used_tb']):.2f} TB highlight contention risk windows. | Peak months align with highest risk to SLAs. |
| Post-optimization reporting | Phase 1: After storage optimisation campaigns such as archival, tiering or snapshot tuning, publish clear before and after metrics that show changes in growth rate, total consumption and headroom. Use the same charts that stakeholders are familiar with. <br><br>**Phase 2 :** Gather feedback from stakeholders on whether performance, availability and visibility have improved and log this feedback alongside technical metrics. <br><br>**Phase 3 :** Use both quantitative and qualitative results to refine policies and plan future optimisation waves, focusing effort on actions that delivered the most value. | - Demonstrates tangible improvements from storage optimisation work which helps justify the time, effort and investment spent on these initiatives.<br><br>- Strengthens relationships with business stakeholders because they can see that their concerns about growth and performance are being addressed with measurable outcomes.<br><br>- Encourages continuous improvement by creating a cycle where optimisation actions, results and stakeholder perceptions feed into the next round of planning and prioritisation.<br><br> | Formula: Growth rate reduction × $/TB per month. Dataset: months with negative Δ corroborate impact. | MoM bar reductions evidence success. |
"""
            }
            render_cio_tables("Storage Growth Trend — CIO Recommendations", cio_growth)

        else:
            st.info("Trend analysis requires 'date' or 'data_timestamp' and 'storage_used_tb'. Provide either explicit used TB values, or include 'avg_storage_utilization' with 'storage_capacity_tb' so used TB can be derived.")
